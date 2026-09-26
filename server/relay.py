import asyncio
import json
import os
import random
import string
import time
from datetime import datetime
import websockets
from websockets.server import serve

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
        "stories": [],
        "current_round": {
            "story_index": None,
            "title": None,
            "text": None,
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
        "buzz_history": []  # [{judge_id, judge_name, time, timestamp}, ...]
    }

CONTROLLER_ONLY = {"add_story", "remove_story", "update_story", "round_start",
                    "speed_change", "pause", "resume", "reset_round", "text_advance",
                    "import_session", "eject_judges", "shutdown_audience", "delete_session",
                    "countdown_start", "toggle_audience_qr", "toggle_timer_visibility"}

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
                "story_count": len(sess["stories"]),
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
                "stories": session["stories"],
                "current_round": session["current_round"],
                "history": session["history"],
                "client_info": session["clients"][websocket],
                "connected_judges": connected_judges,
                "judge_sounds": session["judge_sounds"],
                "audience_count": sum(1 for c in session["clients"].values() if c.get("role") == "audience"),
                "audience_qr_visible": session["audience_qr_visible"],
                "timer_visible": session["timer_visible"],
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

    elif msg_type == "add_story":
        title = data.get("title", "Untitled")
        text = data.get("text", "")
        session["stories"].append({"title": title, "text": text})
        await broadcast_to_session(session_code, {
            "type": "story_added",
            "data": {"index": len(session["stories"]) - 1, "title": title}
        })

    elif msg_type == "remove_story":
        story_index = data.get("story_index")
        if story_index is not None and 0 <= story_index < len(session["stories"]):
            session["stories"].pop(story_index)
            await broadcast_to_session(session_code, {
                "type": "story_removed",
                "data": {"index": story_index}
            })

    elif msg_type == "update_story":
        story_index = data.get("story_index")
        if story_index is None or story_index >= len(session["stories"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid story index"}
            }))
            return
        session["stories"][story_index] = {
            "title": data.get("title", ""),
            "text": data.get("text", "")
        }
        await broadcast_to_session(session_code, {
            "type": "stories_update",
            "data": {"stories": session["stories"]}
        })

    elif msg_type == "countdown_start":
        story_index = data.get("story_index")
        if story_index is None or story_index >= len(session["stories"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid story index"}
            }))
            return

        story = session["stories"][story_index]

        # Split text into sentence chunks (reuse round_start logic)
        import re
        text = story.get("text", "").strip()
        if not text:
            text_lines = ["[Empty story]"]
        else:
            sentences = re.split(r'([.!?]+\s+)', text)
            sentences = [''.join(sentences[i:i+2]).strip() for i in range(0, len(sentences)-1, 2) if sentences[i].strip()]
            if not sentences:
                sentences = [text]
            text_lines = []
            chunk = []
            for sent in sentences:
                chunk.append(sent)
                if len(chunk) >= 3:
                    text_lines.append(' '.join(chunk))
                    chunk = []
            if chunk:
                text_lines.append(' '.join(chunk))
            if not text_lines:
                text_lines = [text]

        # Reset round state (countdown phase — start_time set later)
        session["current_round"] = {
            "story_index": story_index,
            "title": story["title"],
            "text": story["text"],
            "text_lines": text_lines,
            "text_position": 0,
            "start_time": None,
            "speed": 1,
            "paused": False,
            "pause_time": None,
            "elapsed_at_pause": 0,
            "buzzes": [],
            "status": "countdown"
        }
        # Clear buzz history for new round
        session["buzz_history"] = []

        await broadcast_to_session(session_code, {
            "type": "countdown_start",
            "data": {
                "story_index": story_index,
                "story_title": story["title"],
                "story_text": story["text"],
                "text_line_count": len(text_lines),
                "first_line": text_lines[0] if text_lines else ""
            }
        })

    elif msg_type == "round_start":
        story_index = data.get("story_index", 0)
        if story_index >= len(session["stories"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid story index"}
            }))
            return

        story = session["stories"][story_index]

        # If countdown already set up this round, just transition to running
        current = session["current_round"]
        if (current.get("status") == "countdown"
                and current.get("story_index") == story_index
                and current.get("text_lines")):
            now = time.time()
            current["start_time"] = now
            current["status"] = "running"
            # Position 1: first line was already shown during countdown
            current["text_position"] = 1

            text_lines = current["text_lines"]
            await broadcast_to_session(session_code, {
                "type": "round_started",
                "data": {
                    "title": story["title"],
                    "text": story["text"],
                    "text_line_count": len(text_lines),
                    "start_time": now,
                    "server_time": now
                }
            })
            return

        # Full setup (no countdown preceded this)
        import re
        text = story.get("text", "").strip()
        if not text:
            text_lines = ["[Empty story]"]
        else:
            sentences = re.split(r'([.!?]+\s+)', text)
            sentences = [''.join(sentences[i:i+2]).strip() for i in range(0, len(sentences)-1, 2) if sentences[i].strip()]
            if not sentences:
                sentences = [text]
            text_lines = []
            chunk = []
            for sent in sentences:
                chunk.append(sent)
                if len(chunk) >= 3:
                    text_lines.append(' '.join(chunk))
                    chunk = []
            if chunk:
                text_lines.append(' '.join(chunk))
            if not text_lines:
                text_lines = [text]

        session["current_round"] = {
            "story_index": story_index,
            "title": story["title"],
            "text": story["text"],
            "text_lines": text_lines,
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
                "title": story["title"],
                "text": story["text"],
                "text_line_count": len(text_lines),
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
        # Only advance during running round
        if session["current_round"]["status"] != "running":
            return

        text_position = session["current_round"]["text_position"]
        text_lines = session["current_round"]["text_lines"]

        # Check if text exhausted
        if text_position >= len(text_lines):
            # Victory - reader finished without all judges buzzing
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
            # Advance to next line
            current_line = text_lines[text_position]
            session["current_round"]["text_position"] += 1

            await broadcast_to_session(session_code, {
                "type": "text_advanced",
                "data": {
                    "line": current_line,
                    "position": text_position,
                    "total": len(text_lines)
                }
            })

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
            "story_index": None,
            "title": None,
            "text": None,
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
        stories = data.get("stories", [])
        config = data.get("config", {})

        # Validate stories format
        if not isinstance(stories, list):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid stories format"}
            }))
            return

        for story in stories:
            if not isinstance(story, dict) or "title" not in story or "text" not in story:
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid story format"}
                }))
                return

        # Merge config (only allowed keys)
        if "timer_duration" in config:
            session["config"]["timer_duration"] = int(config["timer_duration"])
        if "judge_count" in config:
            session["config"]["judge_count"] = int(config["judge_count"])

        # Replace stories
        session["stories"] = stories

        await broadcast_to_session(session_code, {
            "type": "session_imported",
            "data": {"story_count": len(stories)}
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
