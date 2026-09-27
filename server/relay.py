import asyncio
import json
import os
import random
import string
import time
import urllib.request
from datetime import datetime
import websockets
from websockets.server import serve


def extract_canvas_info(manifest):
    """Extract canvas info (label, image_url, service_url) from all canvases in IIIF manifest (v2 or v3)"""
    canvases = []

    # IIIF Presentation API 3.0
    if 'items' in manifest:
        for canvas in manifest.get('items', []):
            try:
                body = canvas['items'][0]['items'][0]['body']
                image_url = body.get('id')
                label_obj = canvas.get('label', {})
                label = None
                if isinstance(label_obj, dict):
                    for lang_values in label_obj.values():
                        if isinstance(lang_values, list) and lang_values:
                            label = lang_values[0]
                            break
                elif isinstance(label_obj, str):
                    label = label_obj
                service_url = None
                service = body.get('service', [])
                if isinstance(service, list) and service:
                    service_url = service[0].get('id') or service[0].get('@id')
                elif isinstance(service, dict):
                    service_url = service.get('id') or service.get('@id')
                canvases.append({
                    "label": label,
                    "image_url": image_url,
                    "service_url": service_url
                })
            except (KeyError, IndexError, TypeError):
                continue
        if canvases:
            return canvases

    # IIIF Presentation API 2.1
    for sequence in manifest.get('sequences', []):
        for canvas in sequence.get('canvases', []):
            try:
                image_resource = canvas['images'][0]['resource']
                image_url = image_resource.get('@id')
                label = canvas.get('label')
                if isinstance(label, dict):
                    label = label.get('@value', str(label))
                elif isinstance(label, list) and label:
                    label = label[0] if isinstance(label[0], str) else label[0].get('@value', str(label[0]))
                service_url = None
                service = image_resource.get('service')
                if isinstance(service, list) and service:
                    service_url = service[0].get('@id') or service[0].get('id')
                elif isinstance(service, dict):
                    service_url = service.get('@id') or service.get('id')
                canvases.append({
                    "label": label,
                    "image_url": image_url,
                    "service_url": service_url
                })
            except (KeyError, IndexError, TypeError):
                continue

    return canvases

def extract_localized_value(value):
    """Extract string from IIIF v2/v3 localized values"""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if '@value' in value:
            return value['@value']
        for lang_values in value.values():
            if isinstance(lang_values, list) and lang_values:
                return str(lang_values[0])
            if isinstance(lang_values, str):
                return lang_values
    if isinstance(value, list) and value:
        return extract_localized_value(value[0])
    return None

def extract_manifest_metadata(manifest):
    """Extract manifest-level metadata (label, description, metadata pairs)"""
    label = extract_localized_value(manifest.get('label'))
    description = extract_localized_value(
        manifest.get('summary') or manifest.get('description')
    )
    metadata_pairs = []
    for entry in manifest.get('metadata', []):
        entry_label = extract_localized_value(entry.get('label'))
        entry_value = extract_localized_value(entry.get('value'))
        if entry_label and entry_value:
            metadata_pairs.append(f"{entry_label}: {entry_value}")
    parts = []
    if description:
        parts.append(description)
    parts.extend(metadata_pairs)
    metadata_text = '\n\n'.join(parts) if parts else None
    return {
        "label": label,
        "description": description,
        "metadata_text": metadata_text
    }

def fetch_manifest_data(manifest_url):
    """Fetch IIIF manifest and extract canvas info and metadata"""
    try:
        with urllib.request.urlopen(manifest_url, timeout=10) as response:
            manifest = json.loads(response.read())
        canvases = extract_canvas_info(manifest)
        metadata = extract_manifest_metadata(manifest)
        return canvases, metadata, None
    except Exception as e:
        return [], {}, str(e)


# Multiple sessions (in memory)
sessions = {}  # {code: session_data}
websocket_sessions = {}  # {websocket: code} - track which session each client is in

def generate_code():
    """Generate 4 uppercase letter code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in sessions:
            return code

def create_new_session(code):
    """Create a new session with the given code"""
    return {
        "code": code,
        "config": {
            "timer_duration": 120,
            "speed_options": [1, 2, 3]
        },
        "clients": {},  # {websocket: {"role": "judge", "judge_id": 1}}
        "items": [],
        "current_round": {
            "item_index": None,
            "title": None,
            "text": None,
            "canvases": [],
            "canvas_index": 0,
            "start_time": None,
            "speed": 1,
            "paused": False,
            "pause_time": None,
            "elapsed_at_pause": 0,
            "buzzes": [],
            "status": "waiting"
        },
        "history": [],
        "judge_slots": {},  # {judge_id: {"websocket": ws, "name": str}} - dynamic
        "next_judge_id": 1,
        "judge_sounds": {},  # {judge_id: sound_index (0-4)}
        "audience_qr_visible": False,
        "timer_visible": True,
        "canvas_visible": False,
        "buzz_history": []  # [{judge_id, judge_name, time, timestamp}, ...]
    }

CONTROLLER_ONLY = {"add_item", "remove_item", "update_item", "round_start",
                    "speed_change", "pause", "resume", "reset_round", "text_advance",
                    "canvas_advance", "import_session", "eject_judges", "shutdown_audience",
                    "delete_session", "countdown_start", "toggle_audience_qr",
                    "toggle_timer_visibility", "fetch_manifest", "toggle_canvas"}

def get_connected_judges(session):
    """Return sorted list of {id, name} for connected judges"""
    return sorted(
        [{"id": jid, "name": slot["name"]}
         for jid, slot in session["judge_slots"].items()
         if slot["websocket"] is not None],
        key=lambda j: j["id"]
    )

async def handle_message(websocket, message_data):
    """Process incoming message and broadcast responses"""
    msg_type = message_data.get("type")
    data = message_data.get("data", {})

    # Get current session for this websocket (if any)
    session_code = websocket_sessions.get(websocket)
    session = sessions.get(session_code) if session_code else None

    # Auth check for controller-only actions
    if msg_type in CONTROLLER_ONLY:
        if not session:
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Not in a session"}
            }))
            return
        client_info = session["clients"].get(websocket, {})
        if client_info.get("role") != "controller":
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Only controller can perform this action"}
            }))
            return

    if msg_type == "list_sessions":
        # Return all active sessions
        session_list = []
        for code, sess in sessions.items():
            judge_count = len([j for j in sess["judge_slots"].values() if j["websocket"] is not None])
            audience_count = sum(1 for c in sess["clients"].values() if c.get("role") == "audience")
            session_list.append({
                "code": code,
                "item_count": len(sess["items"]),
                "judge_count": judge_count,
                "audience_count": audience_count
            })
        await websocket.send(json.dumps({
            "type": "sessions_list",
            "data": {"sessions": session_list}
        }))

    elif msg_type == "create_session":
        code = generate_code()
        session = create_new_session(code)
        sessions[code] = session
        session["clients"][websocket] = {"role": "controller"}
        websocket_sessions[websocket] = code
        await websocket.send(json.dumps({
            "type": "session_created",
            "data": {"code": code}
        }))

    elif msg_type == "join":
        code = data.get("code")
        role = data.get("role")
        judge_id = data.get("judge_id")

        # Look up session by code
        if code not in sessions:
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid session code"}
            }))
            return

        session = sessions[code]
        websocket_sessions[websocket] = code

        if role == "judge":
            # Auto-assign next judge ID
            judge_id = session["next_judge_id"]
            session["next_judge_id"] += 1
            judge_name = data.get("name") or f"Judge {judge_id}"
            judge_name = judge_name[:20]  # max 20 chars
            session["judge_slots"][judge_id] = {"websocket": websocket, "name": judge_name}
            session["clients"][websocket] = {"role": "judge", "judge_id": judge_id}
            # Assign random buzz sound if not already assigned (reconnection case)
            if judge_id not in session["judge_sounds"]:
                session["judge_sounds"][judge_id] = random.randint(0, 4)
        else:
            session["clients"][websocket] = {"role": role}

        # Send full session state to joining client
        connected_judges = get_connected_judges(session)
        await websocket.send(json.dumps({
            "type": "session_state",
            "data": {
                "code": session["code"],
                "config": session["config"],
                "items": session["items"],
                "current_round": session["current_round"],
                "history": session["history"],
                "client_info": session["clients"][websocket],
                "connected_judges": connected_judges,
                "judge_sounds": session["judge_sounds"],
                "audience_count": sum(1 for c in session["clients"].values() if c.get("role") == "audience"),
                "audience_qr_visible": session["audience_qr_visible"],
                "timer_visible": session["timer_visible"],
                "canvas_visible": session["canvas_visible"],
                "server_time": time.time()
            }
        }))

        # Broadcast join to other clients in this session
        if role == "judge":
            await broadcast_to_session(code, {
                "type": "judge_joined",
                "data": {
                    "judge_id": judge_id,
                    "connected_judges": connected_judges,
                    "judge_sounds": session["judge_sounds"]
                }
            }, exclude=websocket)
        elif role == "audience":
            audience_count = sum(1 for c in session["clients"].values() if c.get("role") == "audience")
            await broadcast_to_session(code, {
                "type": "audience_joined",
                "data": {"audience_count": audience_count}
            }, exclude=websocket)

    elif msg_type == "add_item":
        title = data.get("title", "").strip()
        text = data.get("text", "").strip()
        manifest_url = data.get("manifest_url", "").strip() or None
        canvases = data.get("canvases", [])

        if not title or not text:
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Title and text required"}
            }))
            return

        item = {
            "title": title,
            "text": text,
            "manifest_url": manifest_url,
            "canvases": canvases
        }
        session["items"].append(item)

        await broadcast_to_session(session_code, {
            "type": "item_added",
            "data": item
        })

    elif msg_type == "remove_item":
        item_index = data.get("item_index")
        if item_index is not None and 0 <= item_index < len(session["items"]):
            session["items"].pop(item_index)
            await broadcast_to_session(session_code, {
                "type": "item_removed",
                "data": {"item_index": item_index}
            })

    elif msg_type == "update_item":
        item_index = data.get("item_index")
        if item_index is None or item_index >= len(session["items"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid item index"}
            }))
            return
        session["items"][item_index] = {
            "title": data.get("title", ""),
            "text": data.get("text", ""),
            "manifest_url": data.get("manifest_url"),
            "canvases": data.get("canvases", [])
        }
        await broadcast_to_session(session_code, {
            "type": "items_update",
            "data": {"items": session["items"]}
        })

    elif msg_type == "countdown_start":
        item_index = data.get("item_index")
        if item_index is None or item_index >= len(session["items"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid item index"}
            }))
            return

        item = session["items"][item_index]

        # Split text into paragraphs (double newline)
        text = item.get("text", "").strip()
        if not text:
            text_paragraphs = ["[Empty metadata]"]
        else:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if not paragraphs:
                text_paragraphs = [text]
            else:
                text_paragraphs = paragraphs

        session["current_round"] = {
            "item_index": item_index,
            "title": item["title"],
            "text": item["text"],
            "canvases": item.get("canvases", []),
            "canvas_index": 0,
            "text_paragraphs": text_paragraphs,
            "text_position": 0,
            "start_time": None,
            "speed": 1,
            "paused": False,
            "pause_time": None,
            "elapsed_at_pause": 0,
            "buzzes": [],
            "status": "countdown"
        }
        session["buzz_history"] = []

        await broadcast_to_session(session_code, {
            "type": "countdown_start",
            "data": {
                "item_index": item_index,
                "item_title": item["title"],
                "item_text": item["text"],
                "canvases": item.get("canvases", []),
                "text_paragraph_count": len(text_paragraphs),
                "first_paragraph": text_paragraphs[0] if text_paragraphs else ""
            }
        })

    elif msg_type == "round_start":
        item_index = data.get("item_index", 0)
        if item_index >= len(session["items"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid item index"}
            }))
            return

        item = session["items"][item_index]

        # If countdown already set up this round, just transition to running
        current = session["current_round"]
        if (current.get("status") == "countdown"
                and current.get("item_index") == item_index
                and current.get("text_paragraphs")):
            now = time.time()
            current["start_time"] = now
            current["status"] = "running"
            current["text_position"] = 1

            text_paragraphs = current["text_paragraphs"]
            await broadcast_to_session(session_code, {
                "type": "round_started",
                "data": {
                    "title": item["title"],
                    "text": item["text"],
                    "canvases": item.get("canvases", []),
                    "canvas_index": 0,
                    "text_paragraph_count": len(text_paragraphs),
                    "start_time": now,
                    "server_time": now
                }
            })
            return

        # Full setup (no countdown preceded this)
        text = item.get("text", "").strip()
        if not text:
            text_paragraphs = ["[Empty metadata]"]
        else:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if not paragraphs:
                text_paragraphs = [text]
            else:
                text_paragraphs = paragraphs

        session["current_round"] = {
            "item_index": item_index,
            "title": item["title"],
            "text": item["text"],
            "canvases": item.get("canvases", []),
            "canvas_index": 0,
            "text_paragraphs": text_paragraphs,
            "text_position": 0,
            "start_time": time.time(),
            "speed": 1,
            "paused": False,
            "pause_time": None,
            "elapsed_at_pause": 0,
            "buzzes": [],
            "status": "running"
        }

        now = session["current_round"]["start_time"]
        await broadcast_to_session(session_code, {
            "type": "round_started",
            "data": {
                "title": item["title"],
                "text": item["text"],
                "canvases": item.get("canvases", []),
                "canvas_index": 0,
                "text_paragraph_count": len(text_paragraphs),
                "start_time": now,
                "server_time": now
            }
        })

    elif msg_type == "speed_change":
        speed = data.get("speed", 1)
        if speed not in session["config"]["speed_options"]:
            return
        session["current_round"]["speed"] = speed
        await broadcast_to_session(session_code, {
            "type": "speed_changed",
            "data": {"speed": speed, "timestamp": time.time()}
        })

    elif msg_type == "pause":
        if session["current_round"]["status"] == "running":
            now = time.time()
            elapsed = now - session["current_round"]["start_time"]
            session["current_round"]["paused"] = True
            session["current_round"]["pause_time"] = now
            session["current_round"]["elapsed_at_pause"] = elapsed
            session["current_round"]["status"] = "paused"
            await broadcast_to_session(session_code, {
                "type": "paused",
                "data": {"timestamp": now, "elapsed": elapsed}
            })

    elif msg_type == "resume":
        if session["current_round"]["status"] == "paused":
            now = time.time()
            session["current_round"]["start_time"] = now - session["current_round"]["elapsed_at_pause"]
            session["current_round"]["paused"] = False
            session["current_round"]["status"] = "running"
            await broadcast_to_session(session_code, {
                "type": "resumed",
                "data": {
                    "timestamp": now,
                    "elapsed": session["current_round"]["elapsed_at_pause"]
                }
            })

    elif msg_type == "text_advance":
        if session["current_round"]["status"] != "running":
            return

        text_position = session["current_round"]["text_position"]
        text_paragraphs = session["current_round"]["text_paragraphs"]

        if text_position >= len(text_paragraphs):
            now = time.time()
            elapsed = now - session["current_round"]["start_time"]
            session["current_round"]["status"] = "victory"
            outcome_data = {
                "outcome": "victory",
                "buzzes": session["current_round"]["buzzes"],
                "duration": round(elapsed, 1)
            }
            session["history"].append({
                "title": session["current_round"]["title"],
                **outcome_data
            })
            await broadcast_to_session(session_code, {
                "type": "round_ended",
                "data": outcome_data
            })
        else:
            current_paragraph = text_paragraphs[text_position]
            session["current_round"]["text_position"] += 1

            await broadcast_to_session(session_code, {
                "type": "text_advanced",
                "data": {
                    "paragraph": current_paragraph,
                    "position": text_position,
                    "total": len(text_paragraphs)
                }
            })

    elif msg_type == "canvas_advance":
        if session["current_round"]["status"] != "running":
            return

        canvases = session["current_round"].get("canvases", [])
        if not canvases:
            return

        direction = data.get("direction")
        canvas_index = session["current_round"]["canvas_index"]

        if direction == "next":
            canvas_index = min(canvas_index + 1, len(canvases) - 1)
        elif direction == "prev":
            canvas_index = max(canvas_index - 1, 0)
        else:
            return

        session["current_round"]["canvas_index"] = canvas_index

        await broadcast_to_session(session_code, {
            "type": "canvas_advanced",
            "data": {
                "canvas_index": canvas_index,
                "total_canvases": len(canvases),
                "canvas": canvases[canvas_index]
            }
        })

    elif msg_type == "fetch_manifest":
        manifest_url = data.get("manifest_url", "").strip()

        if not manifest_url:
            await websocket.send(json.dumps({
                "type": "manifest_fetched",
                "data": {
                    "canvases": [],
                    "error": "No manifest URL provided"
                }
            }))
            return

        canvases, metadata, error = fetch_manifest_data(manifest_url)

        await websocket.send(json.dumps({
            "type": "manifest_fetched",
            "data": {
                "canvases": canvases,
                "metadata": metadata,
                "error": error
            }
        }))

    elif msg_type == "buzz":
        # Only accept buzzes during a running round
        if session["current_round"]["status"] != "running":
            return

        client_info = session["clients"].get(websocket, {})
        if client_info.get("role") != "judge":
            return
        judge_id = client_info.get("judge_id")
        if not judge_id:
            return

        # Check if already buzzed
        if any(b["judge_id"] == judge_id for b in session["current_round"]["buzzes"]):
            return

        now = time.time()
        start_time = session["current_round"].get("start_time")
        elapsed = round(now - start_time, 1) if start_time else 0

        buzz_entry = {"judge_id": judge_id, "time": elapsed}
        session["current_round"]["buzzes"].append(buzz_entry)
        buzz_count = len(session["current_round"]["buzzes"])

        # Record in buzz_history
        judge_name = session["judge_slots"].get(judge_id, {}).get("name", f"Judge {judge_id}")
        timestamp = datetime.utcnow().isoformat() + "Z"
        session["buzz_history"].append({
            "judge_id": judge_id,
            "judge_name": judge_name,
            "time": elapsed,
            "timestamp": timestamp
        })

        await broadcast_to_session(session_code, {
            "type": "buzzed",
            "data": {
                "judge_id": judge_id,
                "time": elapsed,
                "buzz_count": buzz_count,
                "timestamp": timestamp
            }
        })

        # Check if all connected judges have buzzed
        connected_judge_count = sum(1 for slot in session["judge_slots"].values() if slot["websocket"] is not None)
        if buzz_count >= connected_judge_count:
            session["current_round"]["status"] = "defeat"
            outcome_data = {
                "outcome": "defeat",
                "buzzes": session["current_round"]["buzzes"],
                "buzz_history": session["buzz_history"],
                "duration": elapsed
            }
            session["history"].append({
                "title": session["current_round"]["title"],
                **outcome_data
            })
            await broadcast_to_session(session_code, {
                "type": "round_ended",
                "data": outcome_data
            })

    elif msg_type == "set_judge_name":
        client_info = session["clients"].get(websocket, {})
        if client_info.get("role") != "judge":
            return
        judge_id = client_info.get("judge_id")
        name = data.get("name", "").strip()[:20]
        if not name:
            return
        slot = session["judge_slots"].get(judge_id)
        if slot:
            slot["name"] = name
            connected_judges = get_connected_judges(session)
            await broadcast_to_session(session_code, {
                "type": "judge_name_changed",
                "data": {
                    "judge_id": judge_id,
                    "name": name,
                    "connected_judges": connected_judges
                }
            })

    elif msg_type == "reset_round":
        session["current_round"] = {
            "item_index": None,
            "title": None,
            "text": None,
            "canvases": [],
            "canvas_index": 0,
            "start_time": None,
            "speed": 1,
            "paused": False,
            "pause_time": None,
            "elapsed_at_pause": 0,
            "buzzes": [],
            "status": "waiting"
        }
        await broadcast_to_session(session_code, {
            "type": "round_reset",
            "data": {}
        })

    elif msg_type == "import_session":
        imported_items = data.get("items", [])
        imported_config = data.get("config", {})

        valid_items = []
        for item in imported_items:
            if isinstance(item, dict) and "title" in item and "text" in item:
                valid_item = {
                    "title": item["title"],
                    "text": item["text"],
                    "manifest_url": item.get("manifest_url"),
                    "canvases": item.get("canvases", [])
                }
                valid_items.append(valid_item)

        session["items"] = valid_items

        if "timer_duration" in imported_config:
            session["config"]["timer_duration"] = int(imported_config["timer_duration"])

        await broadcast_to_session(session_code, {
            "type": "session_imported",
            "data": {
                "items": valid_items,
                "config": session["config"]
            }
        })

    elif msg_type == "toggle_audience_qr":
        visible = data.get("visible", True)
        session["audience_qr_visible"] = visible
        # Broadcast only to audience clients
        audience_clients = [
            ws for ws, info in session["clients"].items()
            if info.get("role") == "audience" and ws.open
        ]
        message = json.dumps({
            "type": "toggle_audience_qr",
            "data": {"visible": visible}
        })
        if audience_clients:
            await asyncio.gather(
                *[ws.send(message) for ws in audience_clients],
                return_exceptions=True
            )

    elif msg_type == "toggle_timer_visibility":
        visible = data.get("visible", True)
        session["timer_visible"] = visible
        # Broadcast to audience and judge clients
        target_clients = [
            ws for ws, info in session["clients"].items()
            if info.get("role") in ("audience", "judge") and ws.open
        ]
        message = json.dumps({
            "type": "toggle_timer_visibility",
            "data": {"visible": visible}
        })
        if target_clients:
            await asyncio.gather(
                *[ws.send(message) for ws in target_clients],
                return_exceptions=True
            )

    elif msg_type == "toggle_canvas":
        visible = data.get("visible", True)
        session["canvas_visible"] = visible
        await broadcast_to_session(session_code, {
            "type": "toggle_canvas",
            "data": {"visible": visible}
        })

    elif msg_type == "eject_judges":
        # Close all judge websockets with message
        judge_sockets = [
            ws for ws, info in session["clients"].items()
            if info.get("role") == "judge"
        ]
        for judge_ws in judge_sockets:
            if judge_ws.open:
                await judge_ws.send(json.dumps({
                    "type": "ejected",
                    "data": {"message": "You have been ejected by the controller"}
                }))
                await judge_ws.close()

    elif msg_type == "shutdown_audience":
        # Close all audience websockets with message
        audience_sockets = [
            ws for ws, info in session["clients"].items()
            if info.get("role") == "audience"
        ]
        for audience_ws in audience_sockets:
            if audience_ws.open:
                await audience_ws.send(json.dumps({
                    "type": "shutdown",
                    "data": {"message": "Audience view has been shutdown"}
                }))
                await audience_ws.close()

    elif msg_type == "delete_session":
        # Eject all clients
        all_clients = list(session["clients"].keys())
        for client_ws in all_clients:
            if client_ws.open and client_ws != websocket:  # Don't close controller yet
                client_info = session["clients"].get(client_ws, {})
                role = client_info.get("role", "client")
                await client_ws.send(json.dumps({
                    "type": "session_deleted",
                    "data": {"message": f"Session has been deleted by controller"}
                }))
                await client_ws.close()

        # Remove session from sessions dict
        if session_code in sessions:
            del sessions[session_code]

        # Notify controller
        await websocket.send(json.dumps({
            "type": "session_deleted",
            "data": {"message": "Session deleted successfully"}
        }))

async def broadcast_to_session(session_code, message, exclude=None):
    """Send message to all clients in a specific session except exclude"""
    if session_code not in sessions:
        return
    session = sessions[session_code]
    websockets_to_send = [
        ws for ws in session["clients"].keys()
        if ws != exclude and ws.open
    ]
    if websockets_to_send:
        await asyncio.gather(
            *[ws.send(json.dumps(message)) for ws in websockets_to_send],
            return_exceptions=True
        )

async def handler(websocket):
    """Handle WebSocket connection"""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_message(websocket, data)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON"}
                }))
    finally:
        # Clean up on disconnect
        session_code = websocket_sessions.pop(websocket, None)
        if session_code and session_code in sessions:
            session = sessions[session_code]
            client_info = session["clients"].pop(websocket, None)
            if client_info:
                role = client_info.get("role")
                if role == "judge":
                    judge_id = client_info.get("judge_id")
                    slot = session["judge_slots"].get(judge_id)
                    if slot and slot["websocket"] == websocket:
                        del session["judge_slots"][judge_id]
                        # Broadcast judge left
                        connected_judges = get_connected_judges(session)
                        await broadcast_to_session(session_code, {
                            "type": "judge_left",
                            "data": {"judge_id": judge_id, "connected_judges": connected_judges}
                        })
                elif role == "audience":
                    # Broadcast audience left
                    audience_count = sum(1 for c in session["clients"].values() if c.get("role") == "audience")
                    await broadcast_to_session(session_code, {
                        "type": "audience_left",
                        "data": {"audience_count": audience_count}
                    })

async def main():
    port = int(os.getenv('WEBSOCKET_PORT', 8765))
    async with serve(handler, "0.0.0.0", port):
        print(f"WebSocket server running on ws://0.0.0.0:{port}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
