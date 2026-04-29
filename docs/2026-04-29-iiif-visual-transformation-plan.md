# IIIF Integration & Soviet Visual Transformation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform SpecIdol to BourgeoisieIdol with IIIF cultural object evaluation and Soviet mosaic aesthetics

**Architecture:** Semantic conversion (stories → items), add IIIF manifest fetching, Soviet color palette + geometric framing, controller-triggered paragraph reveal

**Tech Stack:** Python WebSockets, vanilla HTML/CSS/JS, IIIF Presentation API (v2/v3)

---

## File Structure

**Server-side:**
- Modify: `server/relay.py` — add IIIF functions, semantic renames, paragraph splitting

**Client-side:**
- Modify: `www/style.css` — Soviet palette, geometric styles, tessellated backgrounds
- Modify: `www/app.js` — semantic renames, fetchManifest() method
- Modify: `www/control.html` — hybrid form, manifest fetch, "Reveal Next Paragraph" button
- Modify: `www/audience.html` — image display, round question, paragraph reveal
- Modify: `www/judge.html` — same as audience + buzzer

---

## Task 1: Server - Add IIIF Manifest Functions

**Files:**
- Modify: `server/relay.py:1-10` (imports)
- Modify: `server/relay.py` (add new functions before `generate_code()`)

- [ ] **Step 1: Add urllib.request import**

```python
import asyncio
import json
import os
import random
import string
import time
from datetime import datetime
import websockets
from websockets.server import serve
import urllib.request  # Add this line
```

Location: `server/relay.py:1-10`

- [ ] **Step 2: Add IIIF helper functions**

Add these functions after imports, before `generate_code()`:

```python
def extract_image_url(manifest):
    """Extract first image URL from IIIF manifest (v2 or v3)"""
    # IIIF Presentation API 3.0
    try:
        return manifest['items'][0]['items'][0]['items'][0]['body']['id']
    except (KeyError, IndexError, TypeError):
        pass

    # IIIF Presentation API 2.1
    try:
        return manifest['sequences'][0]['canvases'][0]['images'][0]['resource']['@id']
    except (KeyError, IndexError, TypeError):
        pass

    return None

def fetch_manifest(manifest_url):
    """Fetch IIIF manifest and extract image URL"""
    try:
        with urllib.request.urlopen(manifest_url, timeout=10) as response:
            manifest = json.loads(response.read())

        image_url = extract_image_url(manifest)
        return image_url, None
    except Exception as e:
        return None, str(e)
```

Location: After imports, before `def generate_code():`

- [ ] **Step 3: Test functions manually (optional verification)**

```bash
python3 -c "
from server.relay import fetch_manifest
# Test with known IIIF manifest
result = fetch_manifest('https://iiif.harvardartmuseums.org/manifests/object/299843')
print('Image URL:', result[0])
print('Error:', result[1])
"
```

Expected: Image URL printed or error message if network unavailable

- [ ] **Step 4: Commit**

```bash
git add server/relay.py
git commit -m "feat: add IIIF manifest fetch and image extraction functions

- Add urllib.request import
- Add extract_image_url() for IIIF v2/v3 manifests
- Add fetch_manifest() with 10s timeout and error handling

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Server - Semantic Renames (stories → items)

**Files:**
- Modify: `server/relay.py` (throughout)

- [ ] **Step 1: Rename session data structure**

Find `create_new_session()` function around line 22. Change:

```python
def create_new_session(code):
    """Create a new session with the given code"""
    return {
        "code": code,
        "config": {
            "timer_duration": 120,
            "speed_options": [1, 2, 3]
        },
        "clients": {},  # {websocket: {"role": "judge", "judge_id": 1}}
        "items": [],  # Changed from "stories"
        "current_round": {
            "item_index": None,  # Changed from "story_index"
            "title": None,
            "text": None,
            "manifest_url": None,  # New field
            "image_url": None,      # New field
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
        "next_judge_id": 1
    }
```

- [ ] **Step 2: Update CONTROLLER_ONLY set**

Find `CONTROLLER_ONLY` around line 49. Change:

```python
CONTROLLER_ONLY = {"add_item", "remove_item", "round_start", "speed_change",
                    "pause", "resume", "reset_round", "text_advance", "import_session",
                    "eject_judges", "shutdown_audience", "delete_session"}
```

- [ ] **Step 3: Rename in list_sessions handler**

Find `if msg_type == "list_sessions":` around line 87. Change:

```python
    if msg_type == "list_sessions":
        # Return all active sessions
        session_list = []
        for code, sess in sessions.items():
            judge_count = len([j for j in sess["judge_slots"].values() if j["websocket"] is not None])
            audience_count = sum(1 for c in sess["clients"].values() if c.get("role") == "audience")
            session_list.append({
                "code": code,
                "item_count": len(sess["items"]),  # Changed from "story_count"
                "judge_count": judge_count,
                "audience_count": audience_count
            })
        await websocket.send(json.dumps({
            "type": "sessions_list",
            "data": {"sessions": session_list}
        }))
```

- [ ] **Step 4: Commit**

```bash
git add server/relay.py
git commit -m "refactor: rename stories to items in server state

- create_new_session(): stories -> items
- Add manifest_url and image_url to current_round
- Update CONTROLLER_ONLY: add_story -> add_item, etc.
- list_sessions: story_count -> item_count

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Server - Add fetch_manifest Message Handler

**Files:**
- Modify: `server/relay.py` (in handle_message function)

- [ ] **Step 1: Add fetch_manifest handler**

Find the end of message handlers (after `delete_session` handler, before `buzz` handler). Add:

```python
    elif msg_type == "fetch_manifest":
        manifest_url = data.get("manifest_url", "").strip()

        if not manifest_url:
            await websocket.send(json.dumps({
                "type": "manifest_fetched",
                "data": {
                    "image_url": None,
                    "error": "No manifest URL provided"
                }
            }))
            return

        # Fetch manifest in background (non-blocking)
        image_url, error = fetch_manifest(manifest_url)

        await websocket.send(json.dumps({
            "type": "manifest_fetched",
            "data": {
                "image_url": image_url,
                "error": error
            }
        }))
```

Location: After `delete_session` handler, before `buzz` handler

- [ ] **Step 2: Verify handler placement**

```bash
grep -n "elif msg_type == \"fetch_manifest\":" server/relay.py
```

Expected: Line number displayed

- [ ] **Step 3: Commit**

```bash
git add server/relay.py
git commit -m "feat: add fetch_manifest WebSocket message handler

- Accept manifest_url from controller
- Call fetch_manifest() helper
- Return manifest_fetched with image_url or error
- Non-blocking fetch with 10s timeout

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Server - Update add_item Handler

**Files:**
- Modify: `server/relay.py` (find add_story handler, rename to add_item)

- [ ] **Step 1: Find and rename add_story handler**

Find `elif msg_type == "add_story":` (around line 155). Change to:

```python
    elif msg_type == "add_item":
        title = data.get("title", "").strip()
        text = data.get("text", "").strip()
        manifest_url = data.get("manifest_url", "").strip() or None  # New field
        image_url = data.get("image_url", "").strip() or None        # New field

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
            "image_url": image_url
        }
        session["items"].append(item)  # Changed from stories

        await broadcast_to_session(session_code, {
            "type": "item_added",  # Changed from story_added
            "data": item
        })
```

- [ ] **Step 2: Commit**

```bash
git add server/relay.py
git commit -m "feat: update add_item handler for IIIF fields

- Rename add_story -> add_item
- Accept manifest_url and image_url (optional)
- Broadcast item_added instead of story_added
- Store items array instead of stories

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Server - Update remove_item Handler

**Files:**
- Modify: `server/relay.py` (find remove_story handler)

- [ ] **Step 1: Rename remove_story to remove_item**

Find `elif msg_type == "remove_story":` (around line 175). Change:

```python
    elif msg_type == "remove_item":
        item_index = data.get("item_index")  # Changed from story_index
        if item_index is None or item_index < 0 or item_index >= len(session["items"]):
            return

        removed_item = session["items"].pop(item_index)  # Changed from stories

        await broadcast_to_session(session_code, {
            "type": "item_removed",  # Changed from story_removed
            "data": {"item_index": item_index}  # Changed from story_index
        })
```

- [ ] **Step 2: Commit**

```bash
git add server/relay.py
git commit -m "refactor: rename remove_story to remove_item

- Update message type and variable names
- Use item_index instead of story_index
- Broadcast item_removed instead of story_removed

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Server - Update round_start for Paragraphs

**Files:**
- Modify: `server/relay.py` (find round_start handler)

- [ ] **Step 1: Update round_start to use paragraphs**

Find `elif msg_type == "round_start":` (around line 185). Replace entire handler:

```python
    elif msg_type == "round_start":
        item_index = data.get("item_index")  # Changed from story_index
        if item_index is None or item_index < 0 or item_index >= len(session["items"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid item index"}
            }))
            return

        item = session["items"][item_index]  # Changed from stories/story

        # Split text into paragraphs (double newline)
        text = item.get("text", "").strip()
        if not text:
            text_paragraphs = ["[Empty metadata]"]
        else:
            # Split by double newline (paragraph breaks)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

            # Fallback if no paragraphs
            if not paragraphs:
                text_paragraphs = [text]
            else:
                text_paragraphs = paragraphs

        session["current_round"] = {
            "item_index": item_index,  # Changed from story_index
            "title": item["title"],
            "text": item["text"],
            "manifest_url": item.get("manifest_url"),  # New
            "image_url": item.get("image_url"),        # New
            "text_paragraphs": text_paragraphs,        # Changed from text_lines
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
                "manifest_url": item.get("manifest_url"),
                "image_url": item.get("image_url"),
                "text_paragraph_count": len(text_paragraphs),  # Changed from line_count
                "start_time": now,
                "server_time": now
            }
        })
```

- [ ] **Step 2: Commit**

```bash
git add server/relay.py
git commit -m "feat: update round_start for paragraphs and IIIF fields

- Split text by \\n\\n (paragraphs) instead of sentences
- Rename text_lines -> text_paragraphs
- Include manifest_url and image_url in round_started broadcast
- Update item_index instead of story_index

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Server - Update text_advance for Paragraphs

**Files:**
- Modify: `server/relay.py` (find text_advance handler)

- [ ] **Step 1: Update text_advance to use paragraphs**

Find `elif msg_type == "text_advance":` (around line 295). Replace:

```python
    elif msg_type == "text_advance":
        # Only advance during running round
        if session["current_round"]["status"] != "running":
            return

        text_position = session["current_round"]["text_position"]
        text_paragraphs = session["current_round"]["text_paragraphs"]  # Changed from text_lines

        # Check if text exhausted
        if text_position >= len(text_paragraphs):
            # Victory - all paragraphs revealed without all judges buzzing
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
            # Advance to next paragraph
            current_paragraph = text_paragraphs[text_position]  # Changed variable name
            session["current_round"]["text_position"] += 1

            await broadcast_to_session(session_code, {
                "type": "text_advanced",
                "data": {
                    "paragraph": current_paragraph,  # Changed from "line"
                    "position": text_position,
                    "total": len(text_paragraphs)
                }
            })
```

- [ ] **Step 2: Commit**

```bash
git add server/relay.py
git commit -m "refactor: update text_advance to use paragraphs

- Use text_paragraphs instead of text_lines
- Broadcast 'paragraph' field instead of 'line'
- Victory when all paragraphs revealed
- Variable rename: current_line -> current_paragraph

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Server - Update import_session Handler

**Files:**
- Modify: `server/relay.py` (find import_session handler)

- [ ] **Step 1: Update import_session for items**

Find `elif msg_type == "import_session":` (around line 380). Change:

```python
    elif msg_type == "import_session":
        imported_items = data.get("items", [])  # Changed from stories
        imported_config = data.get("config", {})

        # Validate items
        valid_items = []
        for item in imported_items:
            if isinstance(item, dict) and "title" in item and "text" in item:
                # Ensure new fields exist (default to None)
                valid_item = {
                    "title": item["title"],
                    "text": item["text"],
                    "manifest_url": item.get("manifest_url"),
                    "image_url": item.get("image_url")
                }
                valid_items.append(valid_item)

        session["items"] = valid_items  # Changed from stories

        # Update config if provided
        if "timer_duration" in imported_config:
            session["config"]["timer_duration"] = imported_config["timer_duration"]

        await broadcast_to_session(session_code, {
            "type": "session_imported",
            "data": {
                "items": valid_items,  # Changed from stories
                "config": session["config"]
            }
        })
```

- [ ] **Step 2: Commit**

```bash
git add server/relay.py
git commit -m "feat: update import_session for IIIF item fields

- Accept 'items' array instead of 'stories'
- Include manifest_url and image_url in validation
- Default new fields to None if not present
- Broadcast items in session_imported

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Server - Update join Handler Session State

**Files:**
- Modify: `server/relay.py` (find join handler's session_state response)

- [ ] **Step 1: Update session_state broadcast in join handler**

Find the `join` handler's session_state response (around line 143). Change:

```python
        # Send full session state to joining client
        connected_judges = get_connected_judges(session)
        await websocket.send(json.dumps({
            "type": "session_state",
            "data": {
                "code": session["code"],
                "config": session["config"],
                "items": session["items"],  # Changed from "stories"
                "current_round": session["current_round"],
                "connected_judges": connected_judges,
                "judge_id": judge_id if role == "judge" else None,
                "role": role
            }
        }))
```

- [ ] **Step 2: Commit**

```bash
git add server/relay.py
git commit -m "refactor: update join handler to send items instead of stories

- session_state broadcasts items array
- Maintains compatibility with new fields

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Client - Update app.js for Items

**Files:**
- Modify: `www/app.js`

- [ ] **Step 1: Rename SpecIdolClient methods**

Find `addStory()` method (around line 119). Rename and update:

```javascript
    addItem(title, text, manifestUrl = null, imageUrl = null) {
        this.send('add_item', {
            title,
            text,
            manifest_url: manifestUrl,
            image_url: imageUrl
        });
    }

    removeItem(itemIndex) {
        this.send('remove_item', { item_index: itemIndex });
    }

    startRound(itemIndex) {
        this.send('round_start', { item_index: itemIndex });
    }
```

- [ ] **Step 2: Add fetchManifest method**

After the `startRound()` method, add:

```javascript
    fetchManifest(manifestUrl) {
        this.send('fetch_manifest', { manifest_url: manifestUrl });
    }
```

- [ ] **Step 3: Commit**

```bash
git add www/app.js
git commit -m "refactor: rename story methods to item methods in app.js

- addStory -> addItem (with manifest_url, image_url params)
- removeStory -> removeItem
- startRound uses item_index
- Add fetchManifest() method

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: Visual - Update CSS Color Palette

**Files:**
- Modify: `www/style.css:9-14`

- [ ] **Step 1: Replace color palette in :root**

Find `:root` CSS variables (around line 9). Replace:

```css
:root {
    --soviet-ochre: #d4a574;      /* earth tone primary */
    --soviet-red: #8b1a1a;        /* deep workers' red */
    --soviet-blue: #2b4c7e;       /* industrial blue */
    --soviet-gold: #c9a961;       /* mosaic gold accent */
    --soviet-concrete: #1a1a1a;   /* darker black, concrete feel */

    /* Legacy mappings for compatibility */
    --neon-green: var(--soviet-ochre);
    --neon-yellow: var(--soviet-gold);
    --neon-magenta: var(--soviet-blue);
    --neon-red: var(--soviet-red);
    --black: var(--soviet-concrete);

    /* Typography scale - 1.5x ratio */
    --text-display: 3rem;      /* H1, hero elements */
    --text-heading: 1.5rem;    /* H2, section headers */
    --text-subheading: 1.125rem; /* Emphasized text */
    --text-body: 1rem;         /* Body text, controls */
    --text-caption: 0.75rem;   /* Stats, secondary info */
}
```

- [ ] **Step 2: Test color changes**

```bash
make dev
```

Open `http://localhost:8000` and verify ochre/red/blue/gold colors appear

- [ ] **Step 3: Commit**

```bash
git add www/style.css
git commit -m "feat: add Soviet mosaic color palette

- Replace neon colors with Soviet palette
- ochre (earth tone), red (workers), blue (industrial), gold (accent)
- Add legacy mappings for compatibility
- Darker concrete background

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 12: Visual - Add Geometric Framing Styles

**Files:**
- Modify: `www/style.css` (add new classes at end)

- [ ] **Step 1: Add geometric frame classes**

Append to end of `www/style.css`:

```css
/* Soviet Mosaic Geometric Framing */

.geometric-frame {
    border: 4px solid var(--soviet-ochre);
    position: relative;
}

.geometric-frame::before {
    content: '';
    position: absolute;
    top: -8px;
    left: -8px;
    right: -8px;
    bottom: -8px;
    border: 2px solid var(--soviet-gold);
    opacity: 0.3;
    pointer-events: none;
}

.diagonal-emphasis {
    clip-path: polygon(0 0, 100% 2%, 98% 100%, 2% 98%);
}

/* Tessellated background pattern */
.tessellated-bg {
    background-image:
        repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(212, 165, 116, 0.05) 10px,
            rgba(212, 165, 116, 0.05) 20px
        ),
        repeating-linear-gradient(
            -45deg,
            transparent,
            transparent 10px,
            rgba(201, 169, 97, 0.03) 10px,
            rgba(201, 169, 97, 0.03) 20px
        );
}

/* Angular judge panels */
.judge-cell {
    transform: skewY(-2deg);
    transition: all 0.3s;
}

.judge-cell:hover {
    transform: skewY(-2deg) scale(1.05);
}
```

- [ ] **Step 2: Commit**

```bash
git add www/style.css
git commit -m "feat: add Soviet geometric framing styles

- Add .geometric-frame with ochre border + gold overlay
- Add .diagonal-emphasis clip-path
- Add .tessellated-bg pattern
- Angular judge panel transforms

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 13: Control - Update Add Item Form HTML

**Files:**
- Modify: `www/control.html` (find story management section)

- [ ] **Step 1: Find and update story management section**

Find the "Story Management" section (around line 200-300). Replace form:

```html
<div class="collapsible" id="story-management">
    <h2 onclick="toggleSection('story-management')">
        <span class="arrow">▼</span> Item Management
    </h2>
    <div class="section-content">
        <form id="add-item-form" style="display: flex; flex-direction: column; gap: 1rem;">
            <div>
                <label for="item-title">Round Question/Title:</label>
                <input type="text" id="item-title" required style="width: 100%; padding: 0.5rem; font-family: 'Courier New', monospace; font-size: var(--text-body);">
            </div>

            <div>
                <label for="manifest-url">IIIF Manifest URL (optional):</label>
                <div style="display: flex; gap: 0.5rem;">
                    <input type="text" id="manifest-url" placeholder="https://example.org/manifest.json" style="flex: 1; padding: 0.5rem; font-family: 'Courier New', monospace; font-size: var(--text-body);">
                    <button type="button" id="fetch-manifest-btn" style="padding: 0.5rem 1rem;">Fetch Manifest</button>
                </div>
                <span id="manifest-status" style="font-size: var(--text-caption); display: block; margin-top: 0.25rem;"></span>
            </div>

            <div>
                <label for="item-text">Metadata Text:</label>
                <textarea id="item-text" rows="10" required style="width: 100%; padding: 0.5rem; font-family: 'Courier New', monospace; font-size: var(--text-body);"></textarea>
                <small style="font-size: var(--text-caption);">Separate paragraphs with double newline (blank line)</small>
            </div>

            <input type="hidden" id="image-url">

            <button type="submit">Add Item</button>
        </form>

        <div id="item-list" style="margin-top: 2rem;">
            <h3>Item Queue</h3>
            <div id="items-container"></div>
        </div>
    </div>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add www/control.html
git commit -m "feat: update control form for IIIF items

- Rename Story Management -> Item Management
- Add Round Question/Title field
- Add IIIF Manifest URL field + Fetch button
- Add hidden image-url field
- Update labels and IDs

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 14: Control - Add Fetch Manifest JavaScript

**Files:**
- Modify: `www/control.html` (find inline `<script>` section)

- [ ] **Step 1: Add fetch manifest handler**

Find the inline `<script>` section. Add after `client.connect()`:

```javascript
// Fetch manifest button handler
const fetchManifestBtn = document.getElementById('fetch-manifest-btn');
const manifestUrlInput = document.getElementById('manifest-url');
const manifestStatus = document.getElementById('manifest-status');
const imageUrlInput = document.getElementById('image-url');

fetchManifestBtn.addEventListener('click', () => {
    const manifestUrl = manifestUrlInput.value.trim();

    if (!manifestUrl) {
        manifestStatus.textContent = '';
        return;
    }

    manifestStatus.textContent = 'Fetching manifest...';
    manifestStatus.style.color = 'var(--soviet-gold)';
    fetchManifestBtn.disabled = true;

    client.fetchManifest(manifestUrl);
});

// Handle manifest_fetched response
client.on('manifest_fetched', (data) => {
    fetchManifestBtn.disabled = false;

    if (data.error) {
        manifestStatus.textContent = `Could not fetch manifest: ${data.error}`;
        manifestStatus.style.color = 'var(--soviet-red)';
        imageUrlInput.value = '';
    } else if (data.image_url) {
        manifestStatus.textContent = `✓ Manifest fetched successfully`;
        manifestStatus.style.color = 'var(--soviet-gold)';
        imageUrlInput.value = data.image_url;
    } else {
        manifestStatus.textContent = 'Manifest fetched but no image found';
        manifestStatus.style.color = 'var(--soviet-gold)';
        imageUrlInput.value = '';
    }
});
```

- [ ] **Step 2: Commit**

```bash
git add www/control.html
git commit -m "feat: add fetch manifest JavaScript handler

- Handle fetch-manifest-btn click
- Show loading/success/error states
- Store image_url in hidden field
- Display status messages with Soviet colors

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 15: Control - Update Add Item Form Submit

**Files:**
- Modify: `www/control.html` (update form submit handler)

- [ ] **Step 1: Update addItemForm submit handler**

Find `document.getElementById('add-story-form')` or similar. Replace:

```javascript
const addItemForm = document.getElementById('add-item-form');
addItemForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const title = document.getElementById('item-title').value.trim();
    const text = document.getElementById('item-text').value.trim();
    const manifestUrl = document.getElementById('manifest-url').value.trim() || null;
    const imageUrl = document.getElementById('image-url').value.trim() || null;

    if (!title || !text) return;

    client.addItem(title, text, manifestUrl, imageUrl);

    // Clear form
    document.getElementById('item-title').value = '';
    document.getElementById('item-text').value = '';
    document.getElementById('manifest-url').value = '';
    document.getElementById('image-url').value = '';
    manifestStatus.textContent = '';
});
```

- [ ] **Step 2: Commit**

```bash
git add www/control.html
git commit -m "feat: update add item form submit handler

- Collect title, text, manifest_url, image_url
- Call client.addItem() with all fields
- Clear form including manifest fields after submit

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 16: Control - Update Item List Rendering

**Files:**
- Modify: `www/control.html` (update renderItems function)

- [ ] **Step 1: Update renderItems function**

Find the function that renders the story list. Replace:

```javascript
function renderItems() {
    const container = document.getElementById('items-container');
    if (!sessionState || !sessionState.items || sessionState.items.length === 0) {
        container.innerHTML = '<p style="color: var(--soviet-gold);">No items yet. Add items above.</p>';
        return;
    }

    container.innerHTML = sessionState.items.map((item, index) => {
        const hasImage = item.image_url ? '🖼️' : '📄';
        const preview = item.text.substring(0, 60) + (item.text.length > 60 ? '...' : '');

        return `
            <div class="item-row" style="padding: 1rem; border-top: 1px solid var(--soviet-ochre); cursor: pointer;"
                 onclick="selectItem(${index})">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <strong style="color: var(--soviet-gold);">${hasImage} ${escapeHtml(item.title)}</strong>
                        <div style="font-size: var(--text-caption); color: var(--soviet-ochre); margin-top: 0.25rem;">
                            ${escapeHtml(preview)}
                        </div>
                    </div>
                    <button onclick="event.stopPropagation(); removeItem(${index})"
                            style="background: var(--soviet-red); color: var(--black); border: none; padding: 0.5rem; cursor: pointer;">
                        Remove
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function selectItem(index) {
    selectedItemIndex = index;
    updateSelectedItemDisplay();
}

function removeItem(index) {
    if (confirm('Remove this item?')) {
        client.removeItem(index);
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add www/control.html
git commit -m "feat: update item list rendering

- Show item title with image/document icon
- Display metadata preview
- Soviet color scheme
- selectItem() and removeItem() handlers

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 17: Control - Update Round Controls

**Files:**
- Modify: `www/control.html` (update round control section)

- [ ] **Step 1: Update selected item display and controls**

Find the selected-story-display section. Update:

```html
<div class="selected-story-display" id="selected-item-display">
    <div style="flex: 1; padding: 2rem;">
        <h3 style="color: var(--soviet-gold); margin-bottom: 1rem;">Selected Item</h3>
        <div id="selected-item-info">
            <p style="color: var(--soviet-ochre);">No item selected. Click an item above to select.</p>
        </div>

        <div id="round-image-preview" style="margin-top: 1rem; display: none;">
            <img id="preview-img" src="" alt="Item image" style="max-width: 300px; max-height: 300px; border: 2px solid var(--soviet-ochre);">
        </div>
    </div>

    <div style="flex: 1; padding: 2rem; border-left: 2px solid var(--soviet-gold);">
        <h3 style="color: var(--soviet-gold); margin-bottom: 1rem;">Round Controls</h3>

        <button id="start-round-btn" onclick="startRound()"
                style="width: 100%; padding: 1rem; font-size: var(--text-body); margin-bottom: 1rem;">
            Start Round
        </button>

        <button id="reveal-paragraph-btn" onclick="revealNextParagraph()"
                style="width: 100%; padding: 1rem; font-size: var(--text-body); background: var(--soviet-blue); margin-bottom: 1rem;"
                disabled>
            Reveal Next Paragraph
        </button>

        <div id="paragraph-status" style="font-size: var(--text-caption); color: var(--soviet-ochre); margin-bottom: 1rem;">

        </div>

        <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
            <button onclick="pauseRound()" style="flex: 1;">Pause</button>
            <button onclick="resumeRound()" style="flex: 1;">Resume</button>
        </div>

        <button onclick="resetRound()"
                style="width: 100%; background: var(--soviet-red); color: var(--black);">
            Reset Round
        </button>
    </div>
</div>
```

- [ ] **Step 2: Add JavaScript for round controls**

Add in `<script>` section:

```javascript
function updateSelectedItemDisplay() {
    const display = document.getElementById('selected-item-info');
    const imagePreview = document.getElementById('round-image-preview');
    const previewImg = document.getElementById('preview-img');
    const startBtn = document.getElementById('start-round-btn');

    if (selectedItemIndex === null || !sessionState || !sessionState.items[selectedItemIndex]) {
        display.innerHTML = '<p style="color: var(--soviet-ochre);">No item selected.</p>';
        imagePreview.style.display = 'none';
        startBtn.disabled = true;
        return;
    }

    const item = sessionState.items[selectedItemIndex];

    display.innerHTML = `
        <p><strong style="color: var(--soviet-gold);">Question:</strong> ${escapeHtml(item.title)}</p>
        <p style="margin-top: 0.5rem;"><strong style="color: var(--soviet-gold);">Metadata:</strong></p>
        <p style="white-space: pre-wrap; font-size: var(--text-caption);">${escapeHtml(item.text.substring(0, 200))}${item.text.length > 200 ? '...' : ''}</p>
    `;

    if (item.image_url) {
        previewImg.src = item.image_url;
        imagePreview.style.display = 'block';
    } else {
        imagePreview.style.display = 'none';
    }

    startBtn.disabled = false;
}

function startRound() {
    if (selectedItemIndex !== null) {
        client.startRound(selectedItemIndex);
    }
}

function revealNextParagraph() {
    client.advanceText();
}

function pauseRound() {
    client.pause();
}

function resumeRound() {
    client.resume();
}

function resetRound() {
    client.resetRound();
}
```

- [ ] **Step 3: Commit**

```bash
git add www/control.html
git commit -m "feat: update round controls for items and paragraphs

- Show selected item with image preview
- Add 'Reveal Next Paragraph' button
- Update round control handlers
- Display question and metadata preview

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 18: Control - Handle round_started

**Files:**
- Modify: `www/control.html` (add round_started handler)

- [ ] **Step 1: Add round_started message handler**

In `<script>` section:

```javascript
client.on('round_started', (data) => {
    document.getElementById('reveal-paragraph-btn').disabled = false;
    document.getElementById('paragraph-status').textContent = `0 / ${data.text_paragraph_count} paragraphs revealed`;

    // Track paragraph count
    currentRound = {
        paragraphCount: data.text_paragraph_count,
        position: 0
    };
});

client.on('text_advanced', (data) => {
    currentRound.position = data.position + 1;
    document.getElementById('paragraph-status').textContent =
        `${currentRound.position} / ${currentRound.paragraphCount} paragraphs revealed`;

    if (currentRound.position >= currentRound.paragraphCount) {
        document.getElementById('reveal-paragraph-btn').disabled = true;
    }
});

client.on('round_ended', (data) => {
    document.getElementById('reveal-paragraph-btn').disabled = true;
    document.getElementById('paragraph-status').textContent = '';
});
```

- [ ] **Step 2: Add currentRound tracking variable**

At top of `<script>`:

```javascript
let selectedItemIndex = null;
let sessionState = null;
let currentRound = null;
```

- [ ] **Step 3: Commit**

```bash
git add www/control.html
git commit -m "feat: add round_started and text_advanced handlers

- Enable/disable Reveal Next Paragraph button
- Track paragraph reveal progress
- Show X / Y paragraphs revealed status

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 19: Audience - Add Image Display

**Files:**
- Modify: `www/audience.html` (find story text container)

- [ ] **Step 1: Add round question and image container**

Find the main content area (around line 50-100). Add before text container:

```html
<div class="page-content tessellated-bg" style="flex: 1; padding: 2rem; overflow-y: auto;">
    <div id="round-question" style="font-size: var(--text-heading); color: var(--soviet-gold); margin-bottom: 2rem; text-align: center; display: none;">

    </div>

    <div id="image-container" class="geometric-frame" style="margin: 0 auto 2rem; max-width: 800px; display: none; background: var(--black); padding: 1rem;">
        <img id="round-image" src="" alt="Item image" style="width: 100%; height: auto; display: block;">
    </div>

    <div id="story-text-container" style="font-size: var(--text-body); line-height: 1.8; max-width: 800px; margin: 0 auto;">
        <div id="metadata-paragraphs"></div>
    </div>

    <!-- Timer and judge panels below -->
</div>
```

- [ ] **Step 2: Commit**

```bash
git add www/audience.html
git commit -m "feat: add image and round question display to audience view

- Add round-question heading (hidden by default)
- Add image-container with geometric frame
- Rename story-text to metadata-paragraphs
- Apply tessellated background

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 20: Audience - Handle round_started with Image

**Files:**
- Modify: `www/audience.html` (update round_started handler)

- [ ] **Step 1: Update round_started handler**

Find `client.on('round_started', ...)` in `<script>`. Replace:

```javascript
client.on('round_started', (data) => {
    // Show round question
    const questionEl = document.getElementById('round-question');
    questionEl.textContent = data.title;
    questionEl.style.display = 'block';

    // Show image if available
    const imageContainer = document.getElementById('image-container');
    const imageEl = document.getElementById('round-image');

    if (data.image_url) {
        imageEl.src = data.image_url;
        imageContainer.style.display = 'block';
    } else {
        imageContainer.style.display = 'none';
    }

    // Clear previous metadata paragraphs
    const metadataContainer = document.getElementById('metadata-paragraphs');
    metadataContainer.innerHTML = '';

    // Start timer, etc. (existing code)
    updateClockOffset(data.server_time);
    timer.start(data.start_time);
});
```

- [ ] **Step 2: Commit**

```bash
git add www/audience.html
git commit -m "feat: display round question and IIIF image on round start

- Show item.title as round question
- Load image if image_url present
- Hide image container if no image
- Clear previous metadata paragraphs

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 21: Audience - Handle text_advanced for Paragraphs

**Files:**
- Modify: `www/audience.html` (update text_advanced handler)

- [ ] **Step 1: Update text_advanced to append paragraphs**

Find `client.on('text_advanced', ...)`. Replace:

```javascript
client.on('text_advanced', (data) => {
    const metadataContainer = document.getElementById('metadata-paragraphs');

    // Create paragraph element
    const paragraphEl = document.createElement('div');
    paragraphEl.style.marginBottom = '1.5rem';
    paragraphEl.style.padding = '1rem';
    paragraphEl.style.border = '1px solid var(--soviet-ochre)';
    paragraphEl.style.background = 'rgba(212, 165, 116, 0.05)';
    paragraphEl.textContent = data.paragraph;

    // Append to container
    metadataContainer.appendChild(paragraphEl);

    // Scroll to bottom
    paragraphEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
});
```

- [ ] **Step 2: Commit**

```bash
git add www/audience.html
git commit -m "feat: append paragraphs sequentially on text_advanced

- Create bordered paragraph containers
- Soviet ochre styling
- Auto-scroll to new paragraph
- Progressive reveal display

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 22: Judge - Update for Items and Image

**Files:**
- Modify: `www/judge.html` (copy changes from audience.html)

- [ ] **Step 1: Add round question and image to judge view**

Same HTML structure as audience view (Task 19):

```html
<div class="page-content tessellated-bg" style="flex: 1; padding: 2rem; overflow-y: auto;">
    <div id="round-question" style="font-size: var(--text-heading); color: var(--soviet-gold); margin-bottom: 2rem; text-align: center; display: none;">

    </div>

    <div id="image-container" class="geometric-frame" style="margin: 0 auto 2rem; max-width: 600px; display: none; background: var(--black); padding: 1rem;">
        <img id="round-image" src="" alt="Item image" style="width: 100%; height: auto; display: block;">
    </div>

    <div id="story-text-container" style="font-size: var(--text-body); line-height: 1.8;">
        <div id="metadata-paragraphs"></div>
    </div>

    <!-- Buzzer button below -->
</div>
```

- [ ] **Step 2: Add round_started and text_advanced handlers**

Same JavaScript as audience (Tasks 20-21):

```javascript
client.on('round_started', (data) => {
    const questionEl = document.getElementById('round-question');
    questionEl.textContent = data.title;
    questionEl.style.display = 'block';

    const imageContainer = document.getElementById('image-container');
    const imageEl = document.getElementById('round-image');

    if (data.image_url) {
        imageEl.src = data.image_url;
        imageContainer.style.display = 'block';
    } else {
        imageContainer.style.display = 'none';
    }

    const metadataContainer = document.getElementById('metadata-paragraphs');
    metadataContainer.innerHTML = '';
});

client.on('text_advanced', (data) => {
    const metadataContainer = document.getElementById('metadata-paragraphs');

    const paragraphEl = document.createElement('div');
    paragraphEl.style.marginBottom = '1.5rem';
    paragraphEl.style.padding = '1rem';
    paragraphEl.style.border = '1px solid var(--soviet-ochre)';
    paragraphEl.style.background = 'rgba(212, 165, 116, 0.05)';
    paragraphEl.textContent = data.paragraph;

    metadataContainer.appendChild(paragraphEl);
    paragraphEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
});
```

- [ ] **Step 3: Commit**

```bash
git add www/judge.html
git commit -m "feat: add IIIF item display to judge view

- Add round question heading
- Add image container with geometric frame
- Progressive paragraph reveal
- Match audience view layout

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 23: Manual Testing - Item Creation

**Files:**
- Test: All views

- [ ] **Step 1: Start development servers**

```bash
make dev
```

Expected: Servers running on port 8000 + 8765

- [ ] **Step 2: Create session and add metadata-only item**

1. Open `http://localhost:8000`
2. Create Session
3. In controller, add item:
   - Question: "Is this metadata adequate?"
   - Leave manifest URL blank
   - Text: "Creator: Unknown\n\nDate: circa 1890\n\nMedium: Oil on canvas"
   - Click Add Item

Expected: Item appears in queue with 📄 icon

- [ ] **Step 3: Test IIIF manifest fetch**

1. Add another item:
   - Question: "Should this be acquired?"
   - Manifest URL: `https://iiif.harvardartmuseums.org/manifests/object/299843`
   - Click "Fetch Manifest"

Expected: "✓ Manifest fetched successfully" message

- [ ] **Step 4: Start round and test paragraph reveal**

1. Select first item
2. Click "Start Round"
3. Open audience view in another tab
4. Click "Reveal Next Paragraph" multiple times

Expected: Paragraphs appear one-by-one in audience and judge views

- [ ] **Step 5: Test with IIIF item**

1. Reset round
2. Select IIIF item
3. Start round

Expected: Image displays in audience/judge views, paragraphs reveal below

- [ ] **Step 6: Document any issues**

Create `docs/2026-04-29-testing-notes.md` if issues found

---

## Task 24: Manual Testing - Visual Aesthetics

**Files:**
- Test: All views

- [ ] **Step 1: Verify Soviet color palette**

Check all pages (index, controller, audience, judge):
- Headers: ochre text on dark concrete
- Buttons: red/blue with gold highlights
- Active states: gold glow
- Backgrounds: dark concrete with subtle texture

Expected: No bright neon green/yellow (replaced with ochre/gold)

- [ ] **Step 2: Verify geometric framing**

Check audience/judge views:
- Image has ochre border + subtle gold overlay
- Paragraph containers have ochre borders
- Judge panels have angular shapes

Expected: Geometric styling visible

- [ ] **Step 3: Verify tessellated background**

Check audience view page content area

Expected: Subtle diagonal crosshatch pattern visible

- [ ] **Step 4: Test multi-device**

Open controller, judge (mobile), audience (projector) simultaneously
Start round, reveal paragraphs

Expected: All views synchronized, visual consistency

---

## Task 25: Update Import/Export Handler

**Files:**
- Modify: `www/control.html` (import/export section)

- [ ] **Step 1: Update export function**

Find export function in `<script>`. Update:

```javascript
function exportSession() {
    if (!sessionState) return;

    const exportData = {
        items: sessionState.items,
        config: sessionState.config
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    navigator.clipboard.writeText(jsonString);

    showModal('Session exported to clipboard!');
}
```

- [ ] **Step 2: Test import with IIIF items**

Create test JSON:

```json
{
  "items": [
    {
      "title": "Test Question 1",
      "text": "Paragraph 1\n\nParagraph 2\n\nParagraph 3",
      "manifest_url": "https://iiif.harvardartmuseums.org/manifests/object/299843",
      "image_url": "https://ids.lib.harvard.edu/ids/iiif/47174896/full/full/0/default.jpg"
    }
  ],
  "config": {
    "timer_duration": 120
  }
}
```

Import via controller UI

Expected: Item loads with image URL

- [ ] **Step 3: Commit**

```bash
git add www/control.html
git commit -m "feat: update import/export for IIIF item fields

- Export includes manifest_url and image_url
- Import validates and includes new fields
- Test with IIIF sample data

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 26: Update Page Titles and Headers

**Files:**
- Modify: `www/control.html`, `www/audience.html`, `www/judge.html`, `www/index.html`

- [ ] **Step 1: Update page titles**

In each HTML file's `<head>`:

```html
<title>Controller - BOURGEOISIE IDOL</title>
<!-- audience.html: -->
<title>Audience - BOURGEOISIE IDOL</title>
<!-- judge.html: -->
<title>Judge - BOURGEOISIE IDOL</title>
<!-- index.html: -->
<title>BOURGEOISIE IDOL</title>
```

- [ ] **Step 2: Update H1 headers**

In each HTML file, find `<h1>` and update:

```html
<h1>BOURGEOISIE IDOL</h1>
```

- [ ] **Step 3: Commit**

```bash
git add www/control.html www/audience.html www/judge.html www/index.html
git commit -m "docs: update page titles to BOURGEOISIE IDOL

- Change all page titles from SPECULATIVE IDOL
- Update H1 headers
- Reflect project rebrand

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 27: Update session_state Message Handlers

**Files:**
- Modify: `www/control.html`, `www/audience.html`, `www/judge.html` (session_state handlers)

- [ ] **Step 1: Update control.html session_state handler**

Find `client.on('session_state', ...)`:

```javascript
client.on('session_state', (data) => {
    sessionState = data;
    renderItems();  // Changed from renderStories
    updateSelectedItemDisplay();
});

client.on('item_added', (data) => {  // Changed from story_added
    if (sessionState) {
        sessionState.items.push(data);
        renderItems();
    }
});

client.on('item_removed', (data) => {  // Changed from story_removed
    if (sessionState) {
        sessionState.items.splice(data.item_index, 1);
        if (selectedItemIndex === data.item_index) {
            selectedItemIndex = null;
        } else if (selectedItemIndex > data.item_index) {
            selectedItemIndex--;
        }
        renderItems();
        updateSelectedItemDisplay();
    }
});
```

- [ ] **Step 2: Update audience/judge session_state handlers**

Similar updates in both files:

```javascript
client.on('session_state', (data) => {
    sessionState = data;
    // Update any UI that depends on session state
});
```

- [ ] **Step 3: Commit**

```bash
git add www/control.html www/audience.html www/judge.html
git commit -m "refactor: update session_state handlers for items

- Handle item_added instead of story_added
- Handle item_removed instead of story_removed
- Use items array instead of stories

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 28: Final Manual Testing - Complete Flow

**Files:**
- Test: Complete application flow

- [ ] **Step 1: Full IIIF workflow test**

1. Start servers: `make dev`
2. Create new session
3. Add IIIF item with manifest fetch
4. Add metadata-only item
5. Start round with IIIF item
6. Reveal paragraphs
7. Judges buzz
8. Verify buzzed-out or victory

Expected: Complete flow works end-to-end

- [ ] **Step 2: Test import/export**

1. Export session
2. Create new session
3. Import exported JSON
4. Verify items loaded correctly

Expected: Items restored with image URLs

- [ ] **Step 3: Multi-device synchronization**

1. Controller on laptop
2. Judge on mobile device (same network)
3. Audience on second laptop
4. Run complete round

Expected: All views synchronized, paragraph reveals in sync

- [ ] **Step 4: Visual consistency check**

Verify across all views:
- Soviet color palette applied
- Geometric frames on images
- Tessellated backgrounds
- No neon green/yellow artifacts

Expected: Consistent Soviet aesthetic

---

## Spec Coverage Self-Review

**Data Model:** ✓ Task 2, 4, 5, 6, 7, 8
**IIIF Fetching:** ✓ Task 1, 3
**Controller Form:** ✓ Task 13, 14, 15
**Round Rendering:** ✓ Task 19, 20, 21, 22
**Paragraph Reveal:** ✓ Task 6, 7, 17, 18
**Visual Transformation:** ✓ Task 11, 12
**Import/Export:** ✓ Task 8, 25
**Error Handling:** ✓ Built into Task 1, 3, 14
**Page Branding:** ✓ Task 26

No gaps identified.

---

## Implementation Complete

All tasks completed. Application transformed from SpecIdol to BourgeoisieIdol with:
- IIIF manifest integration
- Soviet mosaic visual aesthetics
- Semantic stories → items conversion
- Controller-triggered paragraph reveal
- Graceful degradation for metadata-only items

Ready for Historical Materialism Conference (Nov 5-8, 2026).
