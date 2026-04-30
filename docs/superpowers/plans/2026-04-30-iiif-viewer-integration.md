# IIIF Viewer Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace static `<img>` display with OpenSeadragon viewer across audience, judge, and controller views — adding deep zoom and controller-driven multi-canvas navigation.

**Architecture:** OpenSeadragon vendored as single JS file. Server extracts all canvases from IIIF manifests (not just first image). New `canvas_advance` WebSocket message follows same pattern as `text_advance`. Dual-mode tile sources: IIIF Image API `info.json` for tiled zoom, plain image URL fallback.

**Tech Stack:** Python (server/relay.py), vanilla JS/HTML/CSS, OpenSeadragon 5.0

**Testing:** No test framework — manual browser testing with `make dev`. Each task includes manual verification steps.

**Spec:** `docs/superpowers/specs/2026-04-30-iiif-viewer-integration-design.md`

---

### Task 1: Vendor OpenSeadragon

**Files:**
- Create: `www/openseadragon.min.js`

- [ ] **Step 1: Download OpenSeadragon**

```bash
curl -L -o /tmp/openseadragon.zip https://github.com/openseadragon/openseadragon/releases/download/v5.0.0/openseadragon-bin-5.0.0.zip
unzip -o /tmp/openseadragon.zip -d /tmp/openseadragon
cp /tmp/openseadragon/openseadragon-bin-5.0.0/openseadragon.min.js www/openseadragon.min.js
rm -rf /tmp/openseadragon /tmp/openseadragon.zip
```

If v5.0.0 is not available, check https://github.com/openseadragon/openseadragon/releases for latest and adjust URL accordingly.

- [ ] **Step 2: Verify file exists and is reasonable size**

```bash
ls -la www/openseadragon.min.js
# Expected: ~100-200KB file
```

- [ ] **Step 3: Commit**

```bash
git add www/openseadragon.min.js
git commit -m "chore: vendor OpenSeadragon 5.0.0"
```

---

### Task 2: Server — replace `extract_image_url` with `extract_canvas_info`

**Files:**
- Modify: `server/relay.py:12-37`

This task replaces the two functions `extract_image_url()` and `fetch_manifest()` with `extract_canvas_info()` and an updated `fetch_manifest()` that returns a canvases list.

- [ ] **Step 1: Replace `extract_image_url` with `extract_canvas_info`**

Replace lines 12-26 of `server/relay.py` (the `extract_image_url` function) with:

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
                # v3 labels are language maps: {"en": ["Label"]}
                label = None
                if isinstance(label_obj, dict):
                    for lang_values in label_obj.values():
                        if isinstance(lang_values, list) and lang_values:
                            label = lang_values[0]
                            break
                elif isinstance(label_obj, str):
                    label = label_obj
                # Extract service URL for IIIF Image API
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
                    # v2 can have {"@value": "Label"}
                    label = label.get('@value', str(label))
                elif isinstance(label, list) and label:
                    label = label[0] if isinstance(label[0], str) else label[0].get('@value', str(label[0]))
                # Extract service URL for IIIF Image API
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
```

- [ ] **Step 2: Update `fetch_manifest` to return canvases**

Replace lines 28-37 of `server/relay.py` (the `fetch_manifest` function) with:

```python
def fetch_manifest(manifest_url):
    """Fetch IIIF manifest and extract canvas info"""
    try:
        with urllib.request.urlopen(manifest_url, timeout=10) as response:
            manifest = json.loads(response.read())

        canvases = extract_canvas_info(manifest)
        return canvases, None
    except Exception as e:
        return [], str(e)
```

- [ ] **Step 3: Verify server starts without syntax errors**

```bash
cd /Users/marty/Projects/BourgeoisieIdol && make dev-stop; make dev
# Check terminal output for any Python errors
# Then: make dev-stop
```

- [ ] **Step 4: Commit**

```bash
git add server/relay.py
git commit -m "refactor: replace extract_image_url with extract_canvas_info

Extracts all canvases from IIIF manifests (v2 and v3) instead of
just first image. Each canvas includes label, image_url, and
service_url for IIIF Image API tiled zoom."
```

---

### Task 3: Server — update item data model and message handlers

**Files:**
- Modify: `server/relay.py:50-77` (create_new_session)
- Modify: `server/relay.py:202-226` (add_item handler)
- Modify: `server/relay.py:237-288` (round_start handler)
- Modify: `server/relay.py:368-389` (fetch_manifest handler)
- Modify: `server/relay.py:474-492` (reset_round handler)
- Modify: `server/relay.py:494-522` (import_session handler)

- [ ] **Step 1: Update `create_new_session` — replace `image_url` with canvas fields**

In `create_new_session()`, replace the `current_round` dict (lines 60-73). Change `manifest_url` and `image_url` fields to `canvases` and `canvas_index`:

```python
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
```

- [ ] **Step 2: Add `canvas_advance` to `CONTROLLER_ONLY` set**

In the `CONTROLLER_ONLY` set (lines 79-82), add `"canvas_advance"`:

```python
CONTROLLER_ONLY = {"add_item", "remove_item", "round_start", "speed_change",
                    "pause", "resume", "reset_round", "text_advance", "canvas_advance",
                    "import_session", "eject_judges", "shutdown_audience", "delete_session",
                    "fetch_manifest"}
```

- [ ] **Step 3: Update `add_item` handler — use canvases instead of image_url**

Replace the `add_item` handler (lines 202-226) with:

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

- [ ] **Step 4: Update `round_start` handler — broadcast canvases**

Replace the `round_start` handler (lines 237-288) with:

```python
    elif msg_type == "round_start":
        item_index = data.get("item_index")
        if item_index is None or item_index < 0 or item_index >= len(session["items"]):
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

- [ ] **Step 5: Update `fetch_manifest` handler — return canvases**

Replace the `fetch_manifest` handler (lines 368-389) with:

```python
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

        canvases, error = fetch_manifest(manifest_url)

        await websocket.send(json.dumps({
            "type": "manifest_fetched",
            "data": {
                "canvases": canvases,
                "error": error
            }
        }))
```

- [ ] **Step 6: Add `canvas_advance` handler**

Add new handler **after** the `text_advance` handler block (after line 366, before the `fetch_manifest` handler). Insert:

```python
    elif msg_type == "canvas_advance":
        # Only advance during running round
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
```

- [ ] **Step 7: Update `reset_round` handler — use canvas fields**

Replace the `reset_round` handler (lines 474-492) with:

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

- [ ] **Step 8: Update `import_session` handler — use canvases**

Replace the item validation loop in the `import_session` handler (lines 494-522). Change `image_url` references to `canvases`:

```python
    elif msg_type == "import_session":
        imported_items = data.get("items", [])
        imported_config = data.get("config", {})

        # Validate items
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

        # Update config if provided
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

- [ ] **Step 9: Verify server starts clean**

```bash
cd /Users/marty/Projects/BourgeoisieIdol && make dev-stop; make dev
# Check for Python errors in output
# Then: make dev-stop
```

- [ ] **Step 10: Commit**

```bash
git add server/relay.py
git commit -m "feat: update server for canvas-based items and canvas_advance

- Item data model uses canvases[] instead of image_url
- round_start broadcasts canvases array
- New canvas_advance message (controller-only)
- fetch_manifest returns canvases list
- reset_round/import_session use new model"
```

---

### Task 4: Client shared code — update app.js

**Files:**
- Modify: `www/app.js:119-138`

- [ ] **Step 1: Update `addItem` method to use canvases**

Replace the `addItem` method (lines 119-126) with:

```javascript
    addItem(title, text, manifestUrl = null, canvases = []) {
        this.send('add_item', {
            title,
            text,
            manifest_url: manifestUrl,
            canvases: canvases
        });
    }
```

- [ ] **Step 2: Replace `fetchManifest` method and add `canvasAdvance`**

Replace the `fetchManifest` method (lines 136-138) with:

```javascript
    fetchManifest(manifestUrl) {
        this.send('fetch_manifest', { manifest_url: manifestUrl });
    }

    canvasAdvance(direction) {
        this.send('canvas_advance', { direction });
    }
```

- [ ] **Step 3: Commit**

```bash
git add www/app.js
git commit -m "feat: update SpecIdolClient for canvases and canvas_advance"
```

---

### Task 5: Audience view — OpenSeadragon integration

**Files:**
- Modify: `www/audience.html:13` (add script tag)
- Modify: `www/audience.html:139-149` (replace image HTML)
- Modify: `www/audience.html:315-340` (startRound function)
- Modify: `www/audience.html:384-402` (resetView function)
- Add handler for `canvas_advanced` message

- [ ] **Step 1: Add OpenSeadragon script tag**

In `www/audience.html`, add this line after line 12 (`<link rel="stylesheet" href="modal.css">`), before the `<style>` tag on line 14:

```html
    <script src="openseadragon.min.js"></script>
```

- [ ] **Step 2: Add OSD viewer styles**

In the `<style>` block (after the `.page-content` rule around line 43), add:

```css
        #osdViewerContainer {
            display: none;
            width: 100%;
            margin: 0 auto 2rem;
        }

        #canvasLabel {
            font-size: var(--text-body);
            color: var(--soviet-gold);
            text-align: center;
            margin-bottom: 0.5rem;
            display: none;
        }

        #osdViewer {
            width: 100%;
            height: 60vh;
            background: var(--black);
        }
```

- [ ] **Step 3: Replace image HTML with OSD viewer container**

Replace lines 141-143 (the imageContainer div with img tag) with:

```html
        <div id="osdViewerContainer" class="geometric-frame" style="padding: 1rem;">
            <div id="canvasLabel"></div>
            <div id="osdViewer"></div>
        </div>
```

- [ ] **Step 4: Add OSD viewer state variable and helper functions**

In the `<script>` block, after the existing variable declarations (after line 172 `let connectedJudges = [];`), add:

```javascript
        let osdViewer = null;

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
                prefixUrl: ''
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

- [ ] **Step 5: Update `startRound` function**

Replace the `startRound` function (lines 315-340) with:

```javascript
        function startRound(roundData) {
            resetView();

            // Show round question
            const questionEl = document.getElementById('roundQuestion');
            questionEl.textContent = roundData.title || 'Untitled';
            questionEl.style.display = 'block';

            // Header title
            const titleEl = document.getElementById('itemTitle');
            titleEl.textContent = roundData.title || 'Untitled';
            titleEl.classList.remove('waiting');

            // Show OSD viewer if canvases available
            const canvases = roundData.canvases || [];
            const container = document.getElementById('osdViewerContainer');
            if (canvases.length > 0) {
                container.style.display = 'block';
                const canvasIndex = roundData.canvas_index || 0;
                showCanvasLabel(canvases[canvasIndex].label);
                initOsdViewer(canvases[canvasIndex]);
            } else {
                container.style.display = 'none';
            }

            // Clear metadata paragraphs
            document.getElementById('metadataParagraphs').innerHTML = '';
        }
```

- [ ] **Step 6: Add `canvas_advanced` handler**

After the `round_reset` handler (after line 247), add:

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

- [ ] **Step 7: Update `resetView` function**

Replace the `resetView` function (lines 384-402) with:

```javascript
        function resetView() {
            stopTensionTicks();
            tensionMode = false;

            if (timer) timer.stop();
            destroyOsdViewer();

            document.getElementById('outcome').style.display = 'none';
            const titleEl = document.getElementById('itemTitle');
            titleEl.textContent = 'Waiting for item...';
            titleEl.classList.add('waiting');

            document.getElementById('roundQuestion').style.display = 'none';
            document.getElementById('osdViewerContainer').style.display = 'none';
            document.getElementById('canvasLabel').style.display = 'none';
            document.getElementById('metadataParagraphs').innerHTML = '';

            document.querySelectorAll('.judge-cell').forEach(cell => {
                cell.classList.remove('buzzed');
            });
        }
```

- [ ] **Step 8: Manual test**

```bash
make dev
```

1. Open `http://localhost:8000` in browser
2. Create session, open audience view
3. Add an item with a IIIF manifest URL (e.g. `https://iiif.bodleian.ox.ac.uk/iiif/manifest/e32a277e-91e2-4a6d-8ba6-cc4bad230410.json`)
4. Start round — verify OSD viewer appears with zoomable image
5. Add an item without manifest — verify no viewer shown, text-only works
6. Reset round — verify viewer cleaned up

- [ ] **Step 9: Commit**

```bash
git add www/audience.html
git commit -m "feat: add OpenSeadragon viewer to audience view

Replaces static <img> with OSD deep zoom viewer. Handles
canvas_advanced messages, canvas labels, and reduced motion.
Responsive sizing fills content area."
```

---

### Task 6: Judge view — OpenSeadragon integration

**Files:**
- Modify: `www/judge.html:13` (add script tag)
- Modify: `www/judge.html:133-136` (replace image HTML)
- Modify: `www/judge.html:375-430` (startRound function)
- Modify: `www/judge.html:477-494` (resetView function)
- Add handler for `canvas_advanced` message

- [ ] **Step 1: Add OpenSeadragon script tag**

In `www/judge.html`, add this line after line 12 (`<link rel="stylesheet" href="modal.css">`), before the `<style>` tag on line 14:

```html
    <script src="openseadragon.min.js"></script>
```

- [ ] **Step 2: Replace image HTML with OSD viewer container**

Replace lines 133-135 (the imageContainer div with img tag) with:

```html
        <div id="osdViewerContainer" class="geometric-frame" style="margin: 0 auto 1rem; max-width: 300px; display: none; background: var(--black); padding: 0.5rem;">
            <div id="canvasLabel" style="font-size: var(--text-caption); color: var(--soviet-gold); text-align: center; margin-bottom: 0.25rem; display: none;"></div>
            <div id="osdViewer" style="width: 100%; height: 250px;"></div>
        </div>
```

- [ ] **Step 3: Add OSD helper functions**

In the `<script>` block, after the variable declarations (after line 167 `let connectedJudges = [];`), add:

```javascript
        let osdViewer = null;

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
                prefixUrl: ''
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

- [ ] **Step 4: Update `startRound` function**

Replace the `startRound` function (lines 375-430). The key change is replacing `image_url` display with OSD viewer init. The buzz button area construction stays the same:

```javascript
        function startRound(roundData) {
            buzzed = false;
            document.getElementById('itemTitle').textContent = roundData.title || '';

            // Show OSD viewer if canvases available
            const canvases = roundData.canvases || [];
            const container = document.getElementById('osdViewerContainer');
            if (canvases.length > 0) {
                container.style.display = 'block';
                const canvasIndex = roundData.canvas_index || 0;
                showCanvasLabel(canvases[canvasIndex].label);
                initOsdViewer(canvases[canvasIndex]);
            } else {
                container.style.display = 'none';
                destroyOsdViewer();
            }

            // Clear metadata
            const metaContainer = document.getElementById('metadataParagraphs');
            if (metaContainer) metaContainer.innerHTML = '';

            const main = document.getElementById('main');
            // Keep the persistent elements, replace only the interactive area
            const existingTitle = document.getElementById('itemTitle');
            const existingViewer = document.getElementById('osdViewerContainer');
            const existingMeta = document.getElementById('metadataParagraphs');

            main.innerHTML = '';
            main.appendChild(existingTitle);
            main.appendChild(existingViewer);
            main.appendChild(existingMeta);

            const buzzArea = document.createElement('div');
            buzzArea.innerHTML = `
                <button class="buzz-button" id="buzzButton" onclick="buzz()" aria-label="Buzz out the reader">
                    BUZZ
                </button>
                <div class="judge-status" id="judgeStatus">
                    <div class="buzz-count" id="buzzCountDisplay" aria-live="polite">0 of ${connectedJudges.length} buzzed</div>
                    <div class="timer" id="timer" role="timer" aria-live="off">0:00.0</div>
                </div>
            `;
            main.appendChild(buzzArea);

            renderJudgePanels();

            if (timer) timer.stop();
            timer = new Timer(
                timerDuration,
                (elapsed) => {
                    const timerEl = document.getElementById('timer');
                    if (timerEl) timerEl.textContent = formatTime(elapsed);
                },
                () => {
                    // Timer complete (victory)
                }
            );
            timer.start(roundData.start_time);
        }
```

- [ ] **Step 5: Add `canvas_advanced` handler**

After the `round_reset` handler (after line 305), add:

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

- [ ] **Step 6: Update `resetView` function**

Replace the `resetView` function (lines 477-494) with:

```javascript
        function resetView() {
            if (timer) timer.stop();
            buzzed = false;
            destroyOsdViewer();

            const main = document.getElementById('main');
            main.innerHTML = `
                <div class="story-title" id="itemTitle" aria-live="polite"></div>
                <div id="osdViewerContainer" class="geometric-frame" style="margin: 0 auto 1rem; max-width: 300px; display: none; background: var(--black); padding: 0.5rem;">
                    <div id="canvasLabel" style="font-size: var(--text-caption); color: var(--soviet-gold); text-align: center; margin-bottom: 0.25rem; display: none;"></div>
                    <div id="osdViewer" style="width: 100%; height: 250px;"></div>
                </div>
                <div id="metadataParagraphs" style="max-width: 400px; margin: 0 auto; text-align: left;"></div>
                <div class="waiting">Waiting for round to start...</div>
            `;

            document.querySelectorAll('.judge-cell').forEach(cell => {
                cell.classList.remove('buzzed');
            });
        }
```

- [ ] **Step 7: Manual test**

```bash
make dev
```

1. Open judge view in browser (mobile-size viewport preferred)
2. Start a round with IIIF manifest item — verify small OSD viewer appears (max-width 300px)
3. Verify buzz button still works
4. Reset round — verify viewer cleaned up
5. Start text-only item — verify no viewer, text paragraphs work normally

- [ ] **Step 8: Commit**

```bash
git add www/judge.html
git commit -m "feat: add OpenSeadragon viewer to judge view

Replaces static <img> with OSD viewer, max-width 300px for mobile.
Handles canvas_advanced, canvas labels, reduced motion."
```

---

### Task 7: Controller view — OpenSeadragon + canvas navigation

**Files:**
- Modify: `www/control.html:13` (add script tag)
- Modify: `www/control.html:460-466` (add canvas nav buttons to controls)
- Modify: `www/control.html:499-506` (update item form)
- Modify: `www/control.html:632-650` (manifest_fetched handler)
- Modify: `www/control.html:652-662` (round_started handler)
- Modify: `www/control.html:698-708` (round_reset handler)
- Modify: `www/control.html:754-768` (renderItemQueue)
- Modify: `www/control.html:863-877` (fetchManifest function)
- Modify: `www/control.html:879-915` (addItem function)
- Modify: `www/control.html:917-930` (loadItemForEditing function)
- Modify: `www/control.html:956-979` (updateItem function)
- Modify: `www/control.html:981-989` (cancelEdit function)
- Modify: `www/control.html:1098-1107` (exportSession function)

This is the largest task because controller has the most UI: canvas nav buttons, form changes, preview viewer.

- [ ] **Step 1: Add OpenSeadragon script tag**

In `www/control.html`, add this line after line 12 (`<link rel="stylesheet" href="modal.css">`), before the `<style>` tag on line 14:

```html
    <script src="openseadragon.min.js"></script>
```

- [ ] **Step 2: Add canvas nav buttons to round controls area**

In the round controls column (after line 462, the advanceBtn), add canvas navigation buttons:

```html
                <div id="canvasControls" style="display: flex; align-items: center; gap: 0.5rem;">
                    <button onclick="advanceCanvas('prev')" id="prevCanvasBtn" disabled>◀ Prev Canvas</button>
                    <span id="canvasProgress" class="text-progress" style="white-space: nowrap;">Canvas 0 / 0</span>
                    <button onclick="advanceCanvas('next')" id="nextCanvasBtn" disabled>Next Canvas ▶</button>
                </div>
```

- [ ] **Step 3: Add OSD preview to the story text column**

In the story text column (line 468-472), add an OSD viewer container before the story text div. Replace lines 468-472 with:

```html
        <div class="story-text-column">
            <div id="osdViewerContainer" style="display: none; margin-bottom: 1rem;">
                <div id="canvasLabel" style="font-size: var(--text-caption); color: var(--soviet-gold); margin-bottom: 0.25rem; display: none;"></div>
                <div id="osdViewer" style="width: 100%; height: 200px; background: var(--black);"></div>
            </div>
            <div class="story-text" id="liveStoryText">
                <span class="empty-text">Metadata paragraphs appear here during round...</span>
            </div>
        </div>
```

- [ ] **Step 4: Update item form — replace hidden imageUrl with canvases state**

Replace lines 499-506 (the manifest URL form group) with:

```html
                <div class="form-group">
                    <label>IIIF Manifest URL (optional):</label>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" id="manifestUrl" placeholder="https://example.org/manifest.json" style="flex: 1;">
                        <button type="button" id="fetchManifestBtn" onclick="fetchManifest()">Fetch Manifest</button>
                    </div>
                    <span id="manifestStatus" style="font-size: var(--text-caption); display: block; margin-top: 0.25rem;"></span>
                </div>
```

- [ ] **Step 5: Add OSD and canvas state variables**

In the `<script>` block, after the existing variable declarations (after line 561 `let currentParagraphProgress = { position: 0, total: 0 };`), add:

```javascript
        let osdViewer = null;
        let formCanvases = []; // canvases stored from manifest fetch, used when adding item
        let currentCanvases = []; // canvases for current round
        let currentCanvasIndex = 0;

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
                prefixUrl: ''
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

        function updateCanvasControls() {
            const prevBtn = document.getElementById('prevCanvasBtn');
            const nextBtn = document.getElementById('nextCanvasBtn');
            const progress = document.getElementById('canvasProgress');

            const total = currentCanvases.length;

            if (total <= 1) {
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                progress.textContent = total === 0 ? 'No canvases' : 'Canvas 1 / 1';
            } else {
                prevBtn.disabled = currentCanvasIndex <= 0;
                nextBtn.disabled = currentCanvasIndex >= total - 1;
                progress.textContent = `Canvas ${currentCanvasIndex + 1} / ${total}`;
            }

            // Also disable if round not running
            if (!sessionState || sessionState.current_round.status !== 'running') {
                prevBtn.disabled = true;
                nextBtn.disabled = true;
            }
        }
```

- [ ] **Step 6: Update `manifest_fetched` handler**

Replace the `manifest_fetched` handler (lines 632-650) with:

```javascript
        client.on('manifest_fetched', (data) => {
            const btn = document.getElementById('fetchManifestBtn');
            const status = document.getElementById('manifestStatus');
            btn.disabled = false;

            if (data.error) {
                status.textContent = `Could not fetch manifest: ${data.error}`;
                status.style.color = 'var(--soviet-red)';
                formCanvases = [];
            } else if (data.canvases && data.canvases.length > 0) {
                status.textContent = `Manifest fetched: ${data.canvases.length} canvas${data.canvases.length !== 1 ? 'es' : ''} found`;
                status.style.color = 'var(--soviet-gold)';
                formCanvases = data.canvases;
            } else {
                status.textContent = 'Manifest fetched but no canvases found';
                status.style.color = 'var(--soviet-gold)';
                formCanvases = [];
            }
        });
```

- [ ] **Step 7: Update `round_started` handler**

Replace the `round_started` handler (lines 652-662) with:

```javascript
        client.on('round_started', (data) => {
            updateStatus('running');
            document.getElementById('liveStoryText').innerHTML = '';

            // Set up canvases
            currentCanvases = data.canvases || [];
            currentCanvasIndex = data.canvas_index || 0;

            const container = document.getElementById('osdViewerContainer');
            if (currentCanvases.length > 0) {
                container.style.display = 'block';
                showCanvasLabel(currentCanvases[currentCanvasIndex].label);
                initOsdViewer(currentCanvases[currentCanvasIndex]);
            } else {
                container.style.display = 'none';
                destroyOsdViewer();
            }

            updateCanvasControls();

            if (sessionState) {
                sessionState.current_round.status = 'running';
                sessionState.current_round.text_paragraph_count = data.text_paragraph_count || 0;
                renderItemQueue();
            }
            updateSelectedItemDisplay();
            updateParagraphProgress(0, data.text_paragraph_count || 0);
        });
```

- [ ] **Step 8: Add `canvas_advanced` handler**

After the `round_started` handler, add:

```javascript
        client.on('canvas_advanced', (data) => {
            currentCanvasIndex = data.canvas_index;

            if (data.canvas) {
                showCanvasLabel(data.canvas.label);
                if (osdViewer) {
                    osdViewer.open(getTileSource(data.canvas));
                } else {
                    initOsdViewer(data.canvas);
                }
            }

            updateCanvasControls();
        });
```

- [ ] **Step 9: Update `round_reset` handler**

Replace the `round_reset` handler (lines 698-708) with:

```javascript
        client.on('round_reset', () => {
            updateStatus('waiting');
            clearItemText();
            currentParagraphProgress = { position: 0, total: 0 };
            currentCanvases = [];
            currentCanvasIndex = 0;
            destroyOsdViewer();
            document.getElementById('osdViewerContainer').style.display = 'none';
            document.getElementById('canvasLabel').style.display = 'none';
            updateCanvasControls();

            if (sessionState) {
                sessionState.current_round.status = 'waiting';
                sessionState.current_round.item_index = null;
                updateSelectedItemDisplay();
                renderItemQueue();
            }
        });
```

- [ ] **Step 10: Update `renderItemQueue` — show canvas count**

In the `renderItemQueue` function (around line 754-768), replace the `hasImage` line:

Change:
```javascript
                const hasImage = item.image_url ? '\u{1F5BC}\uFE0F' : '\u{1F4C4}';
```

To:
```javascript
                const canvasCount = (item.canvases || []).length;
                const hasImage = canvasCount > 0 ? `\u{1F5BC}\uFE0F ${canvasCount}` : '\u{1F4C4}';
```

- [ ] **Step 11: Add `advanceCanvas` function**

Add this function in the `<script>` block (after the `advanceText` function around line 1074):

```javascript
        function advanceCanvas(direction) {
            if (!sessionState || sessionState.current_round.status !== 'running') return;
            client.canvasAdvance(direction);
        }
```

- [ ] **Step 12: Add keyboard shortcut for canvas navigation**

In the `keydown` handler (lines 1076-1086), add canvas navigation keys. Replace the handler:

```javascript
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            const modalOverlay = document.getElementById('modalOverlay');
            if (modalOverlay && modalOverlay.classList.contains('active')) return;

            if (e.code === 'Space' || e.code === 'ArrowRight') {
                e.preventDefault();
                advanceText();
            } else if (e.code === 'ArrowUp') {
                e.preventDefault();
                advanceCanvas('prev');
            } else if (e.code === 'ArrowDown') {
                e.preventDefault();
                advanceCanvas('next');
            }
        });
```

- [ ] **Step 13: Update `addItem` function — send canvases**

In the `addItem` function (around line 879-915), replace the variables and `client.addItem` call. Change:

```javascript
            const imageUrl = document.getElementById('imageUrl').value.trim() || null;
```
to:
```javascript
            const canvases = formCanvases;
```

And change:
```javascript
            client.addItem(title, text, manifestUrl, imageUrl);
```
to:
```javascript
            client.addItem(title, text, manifestUrl, canvases);
```

And in the form reset section at the end, change:
```javascript
            document.getElementById('imageUrl').value = '';
```
to:
```javascript
            formCanvases = [];
```

- [ ] **Step 14: Update `loadItemForEditing` function**

In `loadItemForEditing` (around line 917-930), replace:
```javascript
            document.getElementById('imageUrl').value = item.image_url || '';
```
with:
```javascript
            formCanvases = item.canvases || [];
```

Also update the manifest status to show canvas count:
After setting `formCanvases`, add:
```javascript
            const status = document.getElementById('manifestStatus');
            if (formCanvases.length > 0) {
                status.textContent = `${formCanvases.length} canvas${formCanvases.length !== 1 ? 'es' : ''} loaded`;
                status.style.color = 'var(--soviet-gold)';
            } else {
                status.textContent = '';
            }
```

- [ ] **Step 15: Update `updateItem` function**

In `updateItem` (around line 956-979), replace:
```javascript
            const imageUrl = document.getElementById('imageUrl').value.trim() || null;
```
with:
```javascript
            const canvases = formCanvases;
```

And change:
```javascript
            sessionState.items[editingItemIndex] = {title, text, manifest_url: manifestUrl, image_url: imageUrl};
```
to:
```javascript
            sessionState.items[editingItemIndex] = {title, text, manifest_url: manifestUrl, canvases: canvases};
```

And in the form reset section, change:
```javascript
            document.getElementById('imageUrl').value = '';
```
to:
```javascript
            formCanvases = [];
```

- [ ] **Step 16: Update `cancelEdit` function**

In `cancelEdit` (around line 981-989), replace:
```javascript
            document.getElementById('imageUrl').value = '';
```
with:
```javascript
            formCanvases = [];
```

- [ ] **Step 17: Update `paused` and `resumed` handlers for canvas controls**

After the existing `paused` handler (around line 669-675), add canvas control updates. In the `paused` handler, add at the end:
```javascript
            updateCanvasControls();
```

In the `resumed` handler (around line 677-683), add at the end:
```javascript
            updateCanvasControls();
```

- [ ] **Step 18: Manual test**

```bash
make dev
```

1. Open `http://localhost:8000` → create session → open controller
2. Add item with IIIF manifest URL — verify "N canvases found" message
3. Verify item queue shows `🖼️ N` with count
4. Start round — verify OSD preview appears in text column
5. Click "Next Canvas ▶" / "◀ Prev Canvas" — verify canvas changes
6. Verify buttons disabled at bounds
7. Open audience and judge views — verify they sync on canvas changes
8. Arrow keys: Space/Right advances text, Up/Down navigates canvases
9. Reset round — verify all canvas state cleaned up
10. Add text-only item — verify canvas buttons disabled, no viewer
11. Export session — verify canvases in JSON
12. Import session — verify canvases loaded

- [ ] **Step 19: Commit**

```bash
git add www/control.html
git commit -m "feat: add OpenSeadragon viewer and canvas navigation to controller

- OSD preview in round text area
- Prev/Next Canvas buttons with progress indicator
- Canvas buttons disabled at bounds and when inactive
- Arrow Up/Down keyboard shortcuts for canvas nav
- Item form stores canvases from manifest fetch
- Item queue shows canvas count
- Export/import uses canvases array"
```

---

### Task 8: Final integration test and cleanup

- [ ] **Step 1: Full end-to-end test**

```bash
make dev
```

Test flow:
1. Create session from index page
2. Open controller, audience, and judge views in separate tabs
3. Add item with multi-canvas IIIF manifest
4. Start round
5. Navigate canvases from controller — all views sync
6. Reveal paragraphs — independent from canvas nav
7. Buzz from judge — verify buzz works during canvas browsing
8. Reset round, start new text-only item — verify clean state
9. Import/export a session with canvas items
10. Test with IIIF manifest that has a service endpoint (tiled zoom) if available

Test manifests to try:
- Bodleian: `https://iiif.bodleian.ox.ac.uk/iiif/manifest/e32a277e-91e2-4a6d-8ba6-cc4bad230410.json`
- Wellcome: `https://iiif.wellcomecollection.org/presentation/b18035723`
- A v3 manifest if available from the sources used in the project

- [ ] **Step 2: Verify no stale references to `image_url` in client code**

Search all HTML and JS files for remaining `image_url` references. If any exist in active code paths (not comments), update them:

```bash
grep -rn "image_url" www/
```

Expected: no active references in audience.html, judge.html, control.html, or app.js. (Some may remain in comments or data structures for manifests where canvases have `image_url` as a field — that's correct.)

- [ ] **Step 3: Commit any cleanup**

If any fixes were needed:
```bash
git add -A
git commit -m "fix: remove stale image_url references from client code"
```

- [ ] **Step 4: Stop dev servers**

```bash
make dev-stop
```
