# BourgeoisieIdol SpecIdol Rebase — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebase BourgeoisieIdol onto SpecIdol HEAD (`35dfafb`), bringing all SpecIdol UX improvements while preserving BourgeoisieIdol's IIIF item/canvas model and OpenSeadragon viewer.

**Architecture:** Copy SpecIdol's source files as new base, then layer BourgeoisieIdol's IIIF integration on top in discrete commits. SpecIdol's visual style (neon game-show) stays — no Soviet mosaic reskin.

**Tech Stack:** Vanilla HTML/CSS/JS, Python WebSocket server (`websockets==12.0`), OpenSeadragon 5.0.0, no frameworks/build tools.

**Spec:** `docs/superpowers/specs/2026-09-26-specidol-rebase-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Copy from SpecIdol | `server/relay.py` | WebSocket server — will be modified for IIIF |
| Copy from SpecIdol | `www/app.js` | Shared client — will be modified for items |
| Copy from SpecIdol | `www/audience.html` | Audience view — will add OSD viewer |
| Copy from SpecIdol | `www/judge.html` | Judge view — will add OSD viewer |
| Copy from SpecIdol | `www/control.html` | Controller — will add OSD + IIIF form |
| Copy from SpecIdol | `www/index.html` | Landing page — branding change only |
| Copy from SpecIdol | `www/style.css` | Base styles — minor OSD CSS additions |
| Copy from SpecIdol | `www/sounds.js` | Synth engine — unchanged |
| Copy from SpecIdol | `www/modal.js`, `www/modal.css` | Modal system — unchanged |
| Copy from SpecIdol | `www/service-worker.js`, `www/favicon.svg` | Unchanged |
| Copy from SpecIdol | `www/lib/qrcode-generator.js` | QR library — unchanged |
| Copy from SpecIdol | `www/buzz-tester.html` | Sound sandbox — unchanged |
| Copy from SpecIdol | `www/judge-test.html` | Judge test page — unchanged |
| Copy from SpecIdol | `server/requirements.txt` | Dependencies — unchanged |
| Copy from SpecIdol | `Makefile`, `Dockerfile`, `.gitignore` | Build/deploy — unchanged |
| Copy from BourgeoisieIdol | `www/openseadragon.min.js` | Vendored OSD library |
| Keep from BourgeoisieIdol | `CLAUDE.md` | Project instructions |
| Keep from BourgeoisieIdol | `README.md` | Project readme |
| Keep from BourgeoisieIdol | `LICENSE` | Anti-Capitalist License |
| Keep from BourgeoisieIdol | `BOOTSTRAP.md` | Bootstrap docs |
| Keep from BourgeoisieIdol | `docs/sources/` | Thematic reference materials |
| Copy from BourgeoisieIdol | `www/degheest/` | Libre typography fonts |

---

### Task 1: Create rebase branch and copy SpecIdol source

**Files:**
- Replace: `server/relay.py`, `server/requirements.txt`
- Replace: `www/app.js`, `www/style.css`, `www/sounds.js`, `www/modal.js`, `www/modal.css`
- Replace: `www/index.html`, `www/audience.html`, `www/judge.html`, `www/control.html`
- Replace: `www/service-worker.js`, `www/favicon.svg`
- Replace: `Makefile`, `Dockerfile`, `.gitignore`
- Add: `www/lib/qrcode-generator.js`, `www/buzz-tester.html`, `www/judge-test.html`

- [ ] **Step 1: Create feature branch**

```bash
cd /Users/marty/Projects/BourgeoisieIdol
git checkout -b feat/specidol-rebase
```

- [ ] **Step 2: Copy SpecIdol server files**

```bash
cp /Users/marty/Projects/SpecIdol/server/relay.py /Users/marty/Projects/BourgeoisieIdol/server/relay.py
cp /Users/marty/Projects/SpecIdol/server/requirements.txt /Users/marty/Projects/BourgeoisieIdol/server/requirements.txt
```

- [ ] **Step 3: Copy SpecIdol www files**

```bash
# Core shared files
cp /Users/marty/Projects/SpecIdol/www/app.js /Users/marty/Projects/BourgeoisieIdol/www/app.js
cp /Users/marty/Projects/SpecIdol/www/style.css /Users/marty/Projects/BourgeoisieIdol/www/style.css
cp /Users/marty/Projects/SpecIdol/www/sounds.js /Users/marty/Projects/BourgeoisieIdol/www/sounds.js
cp /Users/marty/Projects/SpecIdol/www/modal.js /Users/marty/Projects/BourgeoisieIdol/www/modal.js
cp /Users/marty/Projects/SpecIdol/www/modal.css /Users/marty/Projects/BourgeoisieIdol/www/modal.css
cp /Users/marty/Projects/SpecIdol/www/service-worker.js /Users/marty/Projects/BourgeoisieIdol/www/service-worker.js
cp /Users/marty/Projects/SpecIdol/www/favicon.svg /Users/marty/Projects/BourgeoisieIdol/www/favicon.svg

# HTML views
cp /Users/marty/Projects/SpecIdol/www/index.html /Users/marty/Projects/BourgeoisieIdol/www/index.html
cp /Users/marty/Projects/SpecIdol/www/audience.html /Users/marty/Projects/BourgeoisieIdol/www/audience.html
cp /Users/marty/Projects/SpecIdol/www/judge.html /Users/marty/Projects/BourgeoisieIdol/www/judge.html
cp /Users/marty/Projects/SpecIdol/www/control.html /Users/marty/Projects/BourgeoisieIdol/www/control.html

# Extra pages
cp /Users/marty/Projects/SpecIdol/www/buzz-tester.html /Users/marty/Projects/BourgeoisieIdol/www/buzz-tester.html
cp /Users/marty/Projects/SpecIdol/www/judge-test.html /Users/marty/Projects/BourgeoisieIdol/www/judge-test.html

# Vendored library
mkdir -p /Users/marty/Projects/BourgeoisieIdol/www/lib
cp /Users/marty/Projects/SpecIdol/www/lib/qrcode-generator.js /Users/marty/Projects/BourgeoisieIdol/www/lib/qrcode-generator.js
```

- [ ] **Step 4: Copy SpecIdol build files**

```bash
cp /Users/marty/Projects/SpecIdol/Makefile /Users/marty/Projects/BourgeoisieIdol/Makefile
cp /Users/marty/Projects/SpecIdol/Dockerfile /Users/marty/Projects/BourgeoisieIdol/Dockerfile
cp /Users/marty/Projects/SpecIdol/.gitignore /Users/marty/Projects/BourgeoisieIdol/.gitignore
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: rebase onto SpecIdol HEAD (35dfafb)

Replace all source files with SpecIdol's current main branch.
This brings in QR codes, countdown, sounds.js synth engine,
buzz-tester, judge-test, and all mobile/UX fixes.
BourgeoisieIdol IIIF layer will be re-applied in subsequent commits."
```

---

### Task 2: Transform domain model — stories to IIIF items (server)

**Files:**
- Modify: `server/relay.py`

This task converts SpecIdol's story-based backend to BourgeoisieIdol's IIIF item-based model. The final `relay.py` should match BourgeoisieIdol's existing version (766 lines) in structure and behavior.

- [ ] **Step 1: Add IIIF helper functions and urllib import**

Add `import urllib.request` to the imports at line 7, and insert the three IIIF helper functions + `fetch_manifest` function after the imports (before the `sessions = {}` line). Insert the following after line 9 (`from websockets.server import serve`):

```python

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

def fetch_manifest(manifest_url):
    """Fetch IIIF manifest and extract canvas info and metadata"""
    try:
        with urllib.request.urlopen(manifest_url, timeout=10) as response:
            manifest = json.loads(response.read())
        canvases = extract_canvas_info(manifest)
        metadata = extract_manifest_metadata(manifest)
        return canvases, metadata, None
    except Exception as e:
        return [], {}, str(e)
```

- [ ] **Step 2: Update session structure — stories → items**

In `create_new_session()`, change `"stories": []` to `"items": []`. Add canvas fields to `current_round`:

```python
def create_new_session(code):
    return {
        "code": code,
        "config": {
            "timer_duration": 120,
            "speed_options": [1, 2, 3]
        },
        "clients": {},
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
        "judge_slots": {},
        "next_judge_id": 1,
        "judge_sounds": {},
        "audience_qr_visible": False,
        "timer_visible": True,
        "buzz_history": []
    }
```

Note: `judge_sounds`, `audience_qr_visible`, `timer_visible`, `buzz_history` are kept from SpecIdol.

- [ ] **Step 3: Update CONTROLLER_ONLY set**

Replace the `CONTROLLER_ONLY` set:

```python
CONTROLLER_ONLY = {"add_item", "remove_item", "update_item", "round_start",
                    "speed_change", "pause", "resume", "reset_round", "text_advance",
                    "canvas_advance", "import_session", "eject_judges", "shutdown_audience",
                    "delete_session", "countdown_start", "toggle_audience_qr",
                    "toggle_timer_visibility", "fetch_manifest"}
```

- [ ] **Step 4: Update list_sessions — story_count → item_count**

In the `list_sessions` handler, change:
```python
"story_count": len(sess["stories"]),
```
to:
```python
"item_count": len(sess["items"]),
```

- [ ] **Step 5: Update join handler — stories → items in session_state**

In the `join` handler's `session_state` response, change:
```python
"stories": session["stories"],
```
to:
```python
"items": session["items"],
```

- [ ] **Step 6: Replace add_story/remove_story/update_story with item equivalents**

Replace the `add_story` handler (lines 187-194) with:

```python
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
```

Replace the `remove_story` handler (lines 196-203) with:

```python
    elif msg_type == "remove_item":
        item_index = data.get("item_index")
        if item_index is not None and 0 <= item_index < len(session["items"]):
            session["items"].pop(item_index)
            await broadcast_to_session(session_code, {
                "type": "item_removed",
                "data": {"item_index": item_index}
            })
```

Replace the `update_story` handler (lines 205-220) with:

```python
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
```

- [ ] **Step 7: Update countdown_start — stories → items, sentences → paragraphs**

In the `countdown_start` handler, replace all `story`/`stories` references with `item`/`items`, and replace sentence-based text chunking with paragraph-based:

```python
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
```

- [ ] **Step 8: Update round_start — stories → items, sentences → paragraphs**

Replace the entire `round_start` handler with:

```python
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
```

- [ ] **Step 9: Update text_advance — text_lines → text_paragraphs**

Replace the `text_advance` handler:

```python
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
```

- [ ] **Step 10: Add canvas_advance and fetch_manifest handlers**

Insert after the `text_advance` handler (before the `buzz` handler):

```python
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

        canvases, metadata, error = fetch_manifest(manifest_url)

        await websocket.send(json.dumps({
            "type": "manifest_fetched",
            "data": {
                "canvases": canvases,
                "metadata": metadata,
                "error": error
            }
        }))
```

- [ ] **Step 11: Update reset_round — add canvas fields**

Replace the `reset_round` handler:

```python
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
```

- [ ] **Step 12: Update import_session — stories → items**

Replace the `import_session` handler:

```python
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
```

- [ ] **Step 13: Remove the inline `import re` statements**

The SpecIdol `relay.py` has `import re` inside the `countdown_start` and `round_start` handlers (lines 234 and 320). Since we're now using `text.split('\n\n')` instead of regex sentence splitting, these inline imports are no longer needed. Remove them if they still exist after the edits.

- [ ] **Step 14: Verify server starts**

```bash
cd /Users/marty/Projects/BourgeoisieIdol
python3 -c "import server.relay; print('relay.py parses OK')"
```

Expected: `relay.py parses OK`

- [ ] **Step 15: Commit**

```bash
git add server/relay.py
git commit -m "feat: transform server domain model from stories to IIIF items

- Add IIIF manifest fetching (extract_canvas_info, extract_manifest_metadata)
- Replace stories with items (add_item, remove_item, update_item)
- Add canvas_advance and fetch_manifest handlers
- Switch text chunking from sentence regex to paragraph split
- Add canvases/canvas_index to round state
- Keep all SpecIdol features (countdown, QR toggles, timer toggles, sounds)"
```

---

### Task 3: Transform client library — stories to items (app.js)

**Files:**
- Modify: `www/app.js`

- [ ] **Step 1: Replace addStory/removeStory/startRound methods**

In `www/app.js`, replace lines 126-136:

```javascript
    addStory(title, text) {
        this.send('add_story', { title, text });
    }

    removeStory(storyIndex) {
        this.send('remove_story', { story_index: storyIndex });
    }

    startRound(storyIndex) {
        this.send('round_start', { story_index: storyIndex });
    }
```

with:

```javascript
    addItem(title, text, manifestUrl = null, canvases = []) {
        this.send('add_item', { title, text, manifest_url: manifestUrl, canvases });
    }

    removeItem(itemIndex) {
        this.send('remove_item', { item_index: itemIndex });
    }

    startRound(itemIndex) {
        this.send('round_start', { item_index: itemIndex });
    }

    fetchManifest(manifestUrl) {
        this.send('fetch_manifest', { manifest_url: manifestUrl });
    }

    canvasAdvance(direction) {
        this.send('canvas_advance', { direction });
    }
```

- [ ] **Step 2: Update importSession method**

Replace line 162-164:

```javascript
    importSession(stories, config) {
        this.send('import_session', { stories, config });
    }
```

with:

```javascript
    importSession(items, config) {
        this.send('import_session', { items, config });
    }
```

- [ ] **Step 3: Verify syntax**

```bash
node -c /Users/marty/Projects/BourgeoisieIdol/www/app.js
```

Expected: no output (success)

- [ ] **Step 4: Commit**

```bash
git add www/app.js
git commit -m "feat: transform client API from stories to IIIF items

- addStory → addItem (with manifestUrl, canvases params)
- removeStory → removeItem
- Add fetchManifest() and canvasAdvance() methods
- Update importSession to use items"
```

---

### Task 4: Vendor OpenSeadragon

**Files:**
- Add: `www/openseadragon.min.js`

- [ ] **Step 1: Copy OpenSeadragon from BourgeoisieIdol**

```bash
cp /Users/marty/Projects/BourgeoisieIdol/www/openseadragon.min.js /Users/marty/Projects/BourgeoisieIdol/www/openseadragon.min.js
```

Note: The file already exists in BourgeoisieIdol's working tree from before the rebase. If it was overwritten by SpecIdol copy (it wouldn't be — SpecIdol doesn't have it), re-copy from git:

```bash
git show main:www/openseadragon.min.js > /Users/marty/Projects/BourgeoisieIdol/www/openseadragon.min.js
```

- [ ] **Step 2: Verify file exists and is non-empty**

```bash
ls -la /Users/marty/Projects/BourgeoisieIdol/www/openseadragon.min.js
```

Expected: File exists, ~500KB

- [ ] **Step 3: Commit**

```bash
git add www/openseadragon.min.js
git commit -m "chore: vendor OpenSeadragon 5.0.0"
```

---

### Task 5: Add OSD viewer to audience view

**Files:**
- Modify: `www/audience.html`

The SpecIdol audience.html uses `sounds.js`, countdown, QR overlay, and sentence-based `text_line` display. We need to add OSD viewer support while keeping all of those features intact.

- [ ] **Step 1: Add OpenSeadragon script tag**

In `www/audience.html`, add after the `modal.css` link (line 13-ish):

```html
    <script src="openseadragon.min.js"></script>
```

- [ ] **Step 2: Add OSD CSS styles**

Add to the `<style>` block, before the closing `</style>`:

```css
        #osdViewerContainer {
            display: none;
            width: 100%;
            flex: 1;
            flex-direction: column;
            position: relative;
        }

        #canvasLabel {
            font-size: var(--text-body);
            color: var(--neon-yellow);
            text-align: center;
            padding: 0.5rem 0;
            display: none;
        }

        #osdViewer {
            width: 100%;
            flex: 1;
            min-height: 200px;
            background: var(--black);
        }

        #textOverlay {
            position: absolute;
            bottom: 1rem;
            left: 1rem;
            right: 1rem;
            max-height: 50%;
            overflow-y: auto;
            pointer-events: none;
            z-index: 10;
        }

        #metadataParagraphs {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
```

- [ ] **Step 3: Add OSD container to page content**

In the `<main class="page-content">` section, add the OSD container. It should sit alongside the existing text display area. Add before/after the existing story text container:

```html
        <div id="osdViewerContainer" style="padding: 1rem;">
            <div id="canvasLabel"></div>
            <div id="osdViewer"></div>
            <div id="textOverlay">
                <div id="metadataParagraphs" aria-live="polite" aria-relevant="additions"></div>
            </div>
        </div>
```

- [ ] **Step 4: Add OSD JavaScript functions**

Add to the inline `<script>` block, after the variable declarations and before `client.connect()`:

```javascript
        let osdViewer = null;

        function osdIcon(svg, color = '#0f0') {
            return 'data:image/svg+xml,' + encodeURIComponent(
                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36">${svg}</svg>`
            ).replace(/%23/g, '#');
        }

        const OSD_NAV_IMAGES = {
            zoomIn: {
                REST:  osdIcon('<rect rx="4" width="36" height="36" fill="#1a1a1a" stroke="#0f0" stroke-width="2"/><line x1="18" y1="10" x2="18" y2="26" stroke="#0f0" stroke-width="3"/><line x1="10" y1="18" x2="26" y2="18" stroke="#0f0" stroke-width="3"/>'),
                GROUP: osdIcon('<rect rx="4" width="36" height="36" fill="#2a2a2a" stroke="#0f0" stroke-width="2"/><line x1="18" y1="10" x2="18" y2="26" stroke="#0f0" stroke-width="3"/><line x1="10" y1="18" x2="26" y2="18" stroke="#0f0" stroke-width="3"/>'),
                HOVER: osdIcon('<rect rx="4" width="36" height="36" fill="#0f0" stroke="#0f0" stroke-width="2"/><line x1="18" y1="10" x2="18" y2="26" stroke="#1a1a1a" stroke-width="3"/><line x1="10" y1="18" x2="26" y2="18" stroke="#1a1a1a" stroke-width="3"/>'),
                DOWN:  osdIcon('<rect rx="4" width="36" height="36" fill="#f00" stroke="#0f0" stroke-width="2"/><line x1="18" y1="10" x2="18" y2="26" stroke="#fff" stroke-width="3"/><line x1="10" y1="18" x2="26" y2="18" stroke="#fff" stroke-width="3"/>')
            },
            zoomOut: {
                REST:  osdIcon('<rect rx="4" width="36" height="36" fill="#1a1a1a" stroke="#0f0" stroke-width="2"/><line x1="10" y1="18" x2="26" y2="18" stroke="#0f0" stroke-width="3"/>'),
                GROUP: osdIcon('<rect rx="4" width="36" height="36" fill="#2a2a2a" stroke="#0f0" stroke-width="2"/><line x1="10" y1="18" x2="26" y2="18" stroke="#0f0" stroke-width="3"/>'),
                HOVER: osdIcon('<rect rx="4" width="36" height="36" fill="#0f0" stroke="#0f0" stroke-width="2"/><line x1="10" y1="18" x2="26" y2="18" stroke="#1a1a1a" stroke-width="3"/>'),
                DOWN:  osdIcon('<rect rx="4" width="36" height="36" fill="#f00" stroke="#0f0" stroke-width="2"/><line x1="10" y1="18" x2="26" y2="18" stroke="#fff" stroke-width="3"/>')
            },
            home: {
                REST:  osdIcon('<rect rx="4" width="36" height="36" fill="#1a1a1a" stroke="#0f0" stroke-width="2"/><polygon points="18,6 30,18 24,18 24,30 12,30 12,18 6,18" fill="none" stroke="#0f0" stroke-width="2"/>'),
                GROUP: osdIcon('<rect rx="4" width="36" height="36" fill="#2a2a2a" stroke="#0f0" stroke-width="2"/><polygon points="18,6 30,18 24,18 24,30 12,30 12,18 6,18" fill="none" stroke="#0f0" stroke-width="2"/>'),
                HOVER: osdIcon('<rect rx="4" width="36" height="36" fill="#0f0" stroke="#0f0" stroke-width="2"/><polygon points="18,6 30,18 24,18 24,30 12,30 12,18 6,18" fill="none" stroke="#1a1a1a" stroke-width="2"/>'),
                DOWN:  osdIcon('<rect rx="4" width="36" height="36" fill="#f00" stroke="#0f0" stroke-width="2"/><polygon points="18,6 30,18 24,18 24,30 12,30 12,18 6,18" fill="none" stroke="#fff" stroke-width="2"/>')
            },
            fullpage: {
                REST:  osdIcon('<rect rx="4" width="36" height="36" fill="#1a1a1a" stroke="#0f0" stroke-width="2"/><polyline points="10,14 10,10 14,10" fill="none" stroke="#0f0" stroke-width="2"/><polyline points="22,10 26,10 26,14" fill="none" stroke="#0f0" stroke-width="2"/><polyline points="26,22 26,26 22,26" fill="none" stroke="#0f0" stroke-width="2"/><polyline points="14,26 10,26 10,22" fill="none" stroke="#0f0" stroke-width="2"/>'),
                GROUP: osdIcon('<rect rx="4" width="36" height="36" fill="#2a2a2a" stroke="#0f0" stroke-width="2"/><polyline points="10,14 10,10 14,10" fill="none" stroke="#0f0" stroke-width="2"/><polyline points="22,10 26,10 26,14" fill="none" stroke="#0f0" stroke-width="2"/><polyline points="26,22 26,26 22,26" fill="none" stroke="#0f0" stroke-width="2"/><polyline points="14,26 10,26 10,22" fill="none" stroke="#0f0" stroke-width="2"/>'),
                HOVER: osdIcon('<rect rx="4" width="36" height="36" fill="#0f0" stroke="#0f0" stroke-width="2"/><polyline points="10,14 10,10 14,10" fill="none" stroke="#1a1a1a" stroke-width="2"/><polyline points="22,10 26,10 26,14" fill="none" stroke="#1a1a1a" stroke-width="2"/><polyline points="26,22 26,26 22,26" fill="none" stroke="#1a1a1a" stroke-width="2"/><polyline points="14,26 10,26 10,22" fill="none" stroke="#1a1a1a" stroke-width="2"/>'),
                DOWN:  osdIcon('<rect rx="4" width="36" height="36" fill="#f00" stroke="#0f0" stroke-width="2"/><polyline points="10,14 10,10 14,10" fill="none" stroke="#fff" stroke-width="2"/><polyline points="22,10 26,10 26,14" fill="none" stroke="#fff" stroke-width="2"/><polyline points="26,22 26,26 22,26" fill="none" stroke="#fff" stroke-width="2"/><polyline points="14,26 10,26 10,22" fill="none" stroke="#fff" stroke-width="2"/>')
            }
        };

        function getTileSource(canvas) {
            if (canvas.service_url) {
                return canvas.service_url + '/info.json';
            }
            return { type: 'image', url: canvas.image_url };
        }

        function initOsdViewer(canvas) {
            destroyOsdViewer();
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            osdViewer = OpenSeadragon({
                element: document.getElementById('osdViewer'),
                tileSources: getTileSource(canvas),
                showNavigator: false,
                showNavigationControl: true,
                gestureSettingsMouse: { scrollToZoom: true },
                animationTime: prefersReducedMotion ? 0 : 1.2,
                springStiffness: prefersReducedMotion ? 100 : 6.5,
                prefixUrl: '',
                navImages: OSD_NAV_IMAGES
            });
        }

        function destroyOsdViewer() {
            if (osdViewer) {
                osdViewer.destroy();
                osdViewer = null;
            }
        }

        function showCanvasLabel(label) {
            const labelEl = document.getElementById('canvasLabel');
            if (label) {
                labelEl.textContent = label;
                labelEl.style.display = 'block';
            } else {
                labelEl.style.display = 'none';
            }
        }
```

- [ ] **Step 5: Update message handlers for items + canvas**

Replace `story_count` → `item_count` in session_state handler. Rename `story_added`/`story_removed` handlers to `item_added`/`item_removed`. Update `storyCount` element ID references to `itemCount`. Change `storyTitle` to `itemTitle`.

Add `canvas_advanced` handler:

```javascript
        client.on('canvas_advanced', (data) => {
            if (data.canvas) {
                showCanvasLabel(data.canvas.label);
                if (osdViewer) {
                    osdViewer.open(getTileSource(data.canvas));
                } else {
                    initOsdViewer(data.canvas);
                }
            }
        });
```

Update the `text_advanced` handler to use `data.paragraph` instead of `data.line`.

Update `startRound()` function to show OSD viewer when canvases are present, and fall back to text-only when not.

Update `resetView()` to call `destroyOsdViewer()` and hide OSD container.

- [ ] **Step 6: Update all "story" terminology in HTML and JS**

Search and replace in the file:
- `storyCount` → `itemCount` (element IDs)
- `storyTitle` → `itemTitle` (element IDs)
- `story_count` → `item_count` (data fields)
- `story_added` → `item_added` (message types)
- `story_removed` → `item_removed` (message types)
- `Waiting for story...` → `Waiting for item...` (UI text)
- `stories` → `items` (data access in session_state)

- [ ] **Step 7: Commit**

```bash
git add www/audience.html
git commit -m "feat: add OpenSeadragon IIIF viewer to audience view

- OSD viewer displays IIIF canvases with zoom/pan controls
- Metadata paragraphs overlay on OSD viewer
- canvas_advanced handler updates viewer
- Falls back to text-only when item has no canvases
- Keeps all SpecIdol features (countdown, sounds, QR overlay)
- OSD nav icons use neon green to match SpecIdol palette"
```

---

### Task 6: Add OSD viewer to judge view

**Files:**
- Modify: `www/judge.html`

Same pattern as audience but with smaller viewer (250px height, 300px max-width).

- [ ] **Step 1: Add OpenSeadragon script tag**

Add after `modal.css` link:
```html
    <script src="openseadragon.min.js"></script>
```

- [ ] **Step 2: Add OSD container to page content**

In `<main>`, add after the story title div and before the waiting message:

```html
        <div id="osdViewerContainer" style="margin: 0 auto 1rem; max-width: 300px; display: none; background: var(--black); padding: 0.5rem;">
            <div id="canvasLabel" style="font-size: var(--text-caption); color: var(--neon-yellow); text-align: center; margin-bottom: 0.25rem; display: none;"></div>
            <div id="osdViewer" style="width: 100%; height: 250px;"></div>
        </div>
        <div id="metadataParagraphs" style="max-width: 400px; margin: 0 auto; text-align: left;"></div>
```

- [ ] **Step 3: Add OSD JavaScript functions**

Same `osdIcon`, `OSD_NAV_IMAGES`, `getTileSource`, `initOsdViewer`, `destroyOsdViewer`, `showCanvasLabel` functions as audience view (use neon green `#0f0` for icon color).

- [ ] **Step 4: Update message handlers**

Add `canvas_advanced` handler. Update `text_advanced` to use `data.paragraph`. Update `startRound()` to show OSD when canvases present. Update `resetView()` to destroy OSD.

Rename all story → item terminology in element IDs and data fields.

- [ ] **Step 5: Commit**

```bash
git add www/judge.html
git commit -m "feat: add OpenSeadragon IIIF viewer to judge view

- Compact OSD viewer (250px height, 300px max-width)
- Canvas label and metadata paragraphs display
- Falls back to buzz-only when no canvases
- Story → item terminology throughout"
```

---

### Task 7: Add OSD viewer and IIIF UI to controller

**Files:**
- Modify: `www/control.html`

The controller is the most complex view — it needs manifest fetching UI, canvas navigation controls, and OSD viewer alongside all existing SpecIdol features (countdown, QR, sounds, collapsible sections).

- [ ] **Step 1: Add OpenSeadragon script tag**

Add after `modal.css` link:
```html
    <script src="openseadragon.min.js"></script>
```

- [ ] **Step 2: Add manifest URL field to item form**

In the story/item add form section, add between the title input and the text textarea:

```html
                <label>IIIF Manifest URL (optional):</label>
                <div style="display: flex; gap: 0.5rem;">
                    <input type="text" id="manifestUrl" placeholder="https://example.org/manifest.json" style="flex: 1;">
                    <button type="button" id="fetchManifestBtn" onclick="fetchManifestUrl()">Fetch</button>
                </div>
                <span id="manifestStatus" style="font-size: var(--text-caption); display: block; margin-top: 0.25rem;"></span>
```

- [ ] **Step 3: Add canvas navigation controls to live display**

In the live display column (right side), add canvas controls:

```html
                <div id="canvasControls" style="display: none; align-items: center; gap: 0.5rem;">
                    <button onclick="advanceCanvas('prev')" id="prevCanvasBtn" disabled>◀ Prev</button>
                    <span id="canvasProgress" style="white-space: nowrap;">Canvas 0 / 0</span>
                    <button onclick="advanceCanvas('next')" id="nextCanvasBtn" disabled>Next ▶</button>
                </div>
```

- [ ] **Step 4: Add OSD viewer container to live display**

```html
                <div id="osdViewerContainer" style="display: none; position: relative;">
                    <div id="canvasLabel" style="font-size: var(--text-caption); color: var(--neon-yellow); text-align: center; margin-bottom: 0.25rem;"></div>
                    <div id="osdViewer" style="width: 100%; height: 200px; background: var(--black);"></div>
                </div>
```

- [ ] **Step 5: Add OSD JavaScript and manifest fetching**

Add the same OSD functions (osdIcon, OSD_NAV_IMAGES, getTileSource, initOsdViewer, destroyOsdViewer, showCanvasLabel). Plus:

```javascript
        let formCanvases = []; // canvases from manifest fetch, stored for addItem

        function fetchManifestUrl() {
            const url = document.getElementById('manifestUrl').value.trim();
            if (!url) return;
            document.getElementById('manifestStatus').textContent = 'Fetching...';
            client.fetchManifest(url);
        }

        client.on('manifest_fetched', (data) => {
            const status = document.getElementById('manifestStatus');
            if (data.error) {
                status.textContent = 'Error: ' + data.error;
                formCanvases = [];
                return;
            }
            formCanvases = data.canvases || [];
            status.textContent = formCanvases.length + ' canvas(es) found';

            // Auto-fill title and text from metadata if empty
            if (data.metadata) {
                const titleInput = document.getElementById('itemTitle');
                const textInput = document.getElementById('itemText');
                if (titleInput && !titleInput.value && data.metadata.label) {
                    titleInput.value = data.metadata.label;
                }
                if (textInput && !textInput.value && data.metadata.metadata_text) {
                    textInput.value = data.metadata.metadata_text;
                }
            }
        });

        function advanceCanvas(direction) {
            client.canvasAdvance(direction);
        }

        function updateCanvasControls(canvasIndex, totalCanvases) {
            const controls = document.getElementById('canvasControls');
            if (totalCanvases > 1) {
                controls.style.display = 'flex';
                document.getElementById('canvasProgress').textContent =
                    `Canvas ${canvasIndex + 1} / ${totalCanvases}`;
                document.getElementById('prevCanvasBtn').disabled = (canvasIndex <= 0);
                document.getElementById('nextCanvasBtn').disabled = (canvasIndex >= totalCanvases - 1);
            } else {
                controls.style.display = 'none';
            }
        }
```

- [ ] **Step 6: Update addStory → addItem function**

The controller's inline `addStory()` function becomes `addItem()`:

```javascript
        function addItem() {
            const title = document.getElementById('itemTitleInput').value.trim();
            const text = document.getElementById('itemText').value.trim();
            const manifestUrl = document.getElementById('manifestUrl').value.trim() || null;
            if (!title || !text) return;
            client.addItem(title, text, manifestUrl, formCanvases);
            // Clear form
            document.getElementById('itemTitleInput').value = '';
            document.getElementById('itemText').value = '';
            document.getElementById('manifestUrl').value = '';
            document.getElementById('manifestStatus').textContent = '';
            formCanvases = [];
        }
```

- [ ] **Step 7: Update keyboard shortcuts — add arrow keys for canvas**

Add to the existing keyboard handler:

```javascript
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                advanceCanvas('prev');
            }
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                advanceCanvas('next');
            }
```

- [ ] **Step 8: Update all message handlers and terminology**

- `story_added` → `item_added`
- `story_removed` → `item_removed`
- `stories_update` → `items_update`
- `countdown_start` data: `story_index` → `item_index`, `story_title` → `item_title`
- `round_start` sends `item_index` instead of `story_index`
- Update `startRound()` to show OSD viewer + canvas controls when canvases present
- Update `resetView()` to destroy OSD and hide canvas controls
- Add `canvas_advanced` handler that updates OSD viewer and canvas controls
- Text advance label: "Advance Text" → "Reveal Paragraph"

- [ ] **Step 9: Update import/export to use items**

The export/import JSON functions reference `stories` — change to `items`.

- [ ] **Step 10: Commit**

```bash
git add www/control.html
git commit -m "feat: add IIIF manifest fetching and OSD viewer to controller

- Manifest URL input with Fetch button
- Auto-populate title/text from manifest metadata
- Canvas navigation controls (prev/next + keyboard arrows)
- OSD viewer in live display column
- Story → item terminology throughout
- Import/export uses items format"
```

---

### Task 8: Branding — BourgeoisieIdol identity

**Files:**
- Keep: `CLAUDE.md`, `README.md`, `LICENSE`, `BOOTSTRAP.md`
- Modify: `www/index.html`
- Copy: `docs/sources/`

- [ ] **Step 1: Update index.html title and heading**

In `www/index.html`, change:
- `<title>` tag: `SpecIdol` → `BourgeoisieIdol`
- Main heading `<h1>`: `SPECULATIVE<br>IDOL` → `BOURGEOISIE<br>IDOL`
- Any audio overlay text referencing "SpecIdol" → "BourgeoisieIdol"
- `story_count` → `item_count` in session card rendering
- `stories` → `items` in any UI text

- [ ] **Step 2: Update index.html session_state handler**

The `sessions_list` handler renders session cards. Update `story_count` references to `item_count` and change "stories" label to "items".

- [ ] **Step 3: Copy BourgeoisieIdol docs/sources if not present**

```bash
# docs/sources/ should still be in the working tree from BourgeoisieIdol
# Verify it exists:
ls /Users/marty/Projects/BourgeoisieIdol/docs/sources/
```

If missing (shouldn't be — Task 1 only copied server/www/Makefile/Dockerfile):
```bash
git checkout main -- docs/sources/
```

- [ ] **Step 4: Commit**

```bash
git add www/index.html docs/sources/
git commit -m "feat: rebrand to BourgeoisieIdol with thematic framework

- Update index page title, heading, and terminology
- story_count → item_count in session cards
- Keep docs/sources/ thematic reference materials"
```

---

### Task 9: Add degheest libre typography fonts

**Files:**
- Add/keep: `www/degheest/`

- [ ] **Step 1: Verify degheest directory exists**

```bash
ls /Users/marty/Projects/BourgeoisieIdol/www/degheest/
```

Should show: `COPYRIGHT.md`, `License SIL OFL.txt`, `README.md`, `webfonts/`

If missing:
```bash
git checkout main -- www/degheest/
```

- [ ] **Step 2: Commit**

```bash
git add www/degheest/
git commit -m "chore: add degheest libre typography fonts

Available for use but not applied — SpecIdol's Press Start 2P
and Courier New remain the active typography."
```

---

### Task 10: Smoke test and fix integration issues

**Files:**
- Potentially any file modified above

- [ ] **Step 1: Start servers**

```bash
cd /Users/marty/Projects/BourgeoisieIdol
make dev
```

Expected: HTTP server on port 8000, WebSocket on 8765

- [ ] **Step 2: Test basic flow**

Open `http://localhost:8000` in browser. Verify:
1. Landing page shows "BOURGEOISIE IDOL"
2. Create session works
3. Controller loads with all SpecIdol features (collapsible sections, countdown, QR toggles)
4. Can add an item with title + text (no manifest)
5. Round start, countdown, text advance work
6. Judge view: buzz button works
7. Audience view: text lines appear, sounds play

- [ ] **Step 3: Test IIIF flow**

1. In controller, paste a IIIF manifest URL (e.g. `https://iiif.bodleian.ox.ac.uk/iiif/manifest/e32a277e-91e2-4a6d-8ba6-cc4bad230410.json`)
2. Click Fetch — verify canvases and metadata populate
3. Add item with manifest data
4. Start round — verify OSD viewer appears on controller, audience, judge
5. Canvas prev/next navigation works
6. Paragraph reveal works over the OSD viewer

- [ ] **Step 4: Test SpecIdol-only features preserved**

1. QR overlay toggle on audience view
2. Timer visibility toggle
3. Buzz-tester page loads (`/buzz-tester.html`)
4. Judge-test page loads (`/judge-test.html`)
5. Sounds work: buzz, victory, defeat, countdown beeps
6. Mobile: test on phone if possible

- [ ] **Step 5: Fix any issues found, commit**

```bash
git add -A
git commit -m "fix: resolve integration issues from rebase"
```

- [ ] **Step 6: Stop servers**

```bash
make dev-stop
```

---

### Task 11: Update CHANGELOG and docs

**Files:**
- Modify: `docs/CHANGELOG.md`

- [ ] **Step 1: Add rebase entry to CHANGELOG**

Add entry at the top of the Unreleased section:

```markdown
## [Unreleased]

### Changed
- Rebased onto SpecIdol HEAD (35dfafb) — brings all UX improvements
- Added QR code overlays (controller toggles QR on audience view)
- Added 3-2-1 countdown before rounds
- Added sounds.js synth engine (buzz presets, victory fanfare, countdown beeps)
- Added buzz-tester sound design sandbox page
- Added judge testing dashboard page
- Added timer/QR visibility toggles
- Mobile improvements: iOS audio unlock, timer toggle, layout fixes
- OSD viewer nav icons use neon green palette (matching SpecIdol visual style)

### Fixed
- Audience count on join
- Mobile timer toggle and outcome text clipping
- Judge page breaking on second round start
- Audio unlock on iOS Safari
```

- [ ] **Step 2: Commit**

```bash
git add docs/CHANGELOG.md
git commit -m "docs: update CHANGELOG for SpecIdol rebase"
```
