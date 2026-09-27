# IIIF Viewer Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up canvas display toggle, paragraph overlay on OSD viewer, and redesign judge view for full IIIF interaction.

**Architecture:** Add `canvas_visible` session state + `toggle_canvas` broadcast message (mirrors `toggle_audience_qr`). Audience and judge views gain a `canvasMode` boolean that routes `text_advanced` paragraphs to either `#storyText` (text mode) or `#metadataParagraphs` overlay on the OSD viewer (canvas mode). Judge view restructured with persistent buzz button outside `innerHTML` rewriting.

**Tech Stack:** Python WebSocket server (relay.py), vanilla HTML/CSS/JS, OpenSeadragon 5.0.0

**Spec:** `docs/superpowers/specs/2026-09-27-iiif-viewer-design.md`

---

## File Structure

| File | Role |
|------|------|
| `server/relay.py` | Add `canvas_visible` to session init + `session_state` response, add `toggle_canvas` handler, add to `CONTROLLER_ONLY` |
| `www/app.js` | Add `toggleCanvas(visible)` method to `SpecIdolClient` |
| `www/control.html` | Add canvas toggle checkbox + JS function + handler for initial state |
| `www/audience.html` | Add `canvasMode` state, `appendOverlayParagraph()`, update `text_advanced` routing, add `toggle_canvas` handler, add `.overlay-paragraph` CSS |
| `www/judge.html` | Restructure DOM (persistent buzz button outside innerHTML), add `canvas-mode` CSS, add `canvasMode` state, paragraph routing, `toggle_canvas` handler |

---

### Task 1: Server — `canvas_visible` state + `toggle_canvas` handler

**Files:**
- Modify: `server/relay.py:138-168` (session init)
- Modify: `server/relay.py:170-174` (CONTROLLER_ONLY set)
- Modify: `server/relay.py:270-286` (session_state response)
- Modify: `server/relay.py:747-763` (after toggle_audience_qr, add toggle_canvas)

- [ ] **Step 1: Add `canvas_visible` to session initialization**

In `create_new_session()` (line 138), add `"canvas_visible": False` after `"timer_visible": True` (line 166):

```python
        "timer_visible": True,
        "canvas_visible": False,
        "buzz_history": []  # [{judge_id, judge_name, time, timestamp}, ...]
```

- [ ] **Step 2: Add `canvas_visible` to `session_state` response**

In the `session_state` response dict (line 270-286), add `canvas_visible` after `timer_visible` (line 283):

```python
                "timer_visible": session["timer_visible"],
                "canvas_visible": session["canvas_visible"],
                "server_time": time.time()
```

- [ ] **Step 3: Add `toggle_canvas` to `CONTROLLER_ONLY` set**

In the `CONTROLLER_ONLY` set (lines 170-174), add `"toggle_canvas"`:

```python
CONTROLLER_ONLY = {"add_item", "remove_item", "update_item", "round_start",
                    "speed_change", "pause", "resume", "reset_round", "text_advance",
                    "canvas_advance", "import_session", "eject_judges", "shutdown_audience",
                    "delete_session", "countdown_start", "toggle_audience_qr",
                    "toggle_timer_visibility", "fetch_manifest", "toggle_canvas"}
```

- [ ] **Step 4: Add `toggle_canvas` handler**

After the `toggle_timer_visibility` handler (ends at line 781), add:

```python
    elif msg_type == "toggle_canvas":
        visible = data.get("visible", True)
        session["canvas_visible"] = visible
        await broadcast_to_session(session_code, {
            "type": "toggle_canvas",
            "data": {"visible": visible}
        })
```

Note: This broadcasts to ALL clients (not filtered to audience/judge), unlike `toggle_audience_qr` which only goes to audience. The controller needs to receive it back for state tracking, and judges need it too. Simpler than filtering.

- [ ] **Step 5: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('server/relay.py', doraise=True)"`
Expected: No output (success)

- [ ] **Step 6: Commit**

```bash
git add server/relay.py
git commit -m "feat: add canvas_visible session state and toggle_canvas handler"
```

---

### Task 2: app.js — `toggleCanvas()` method

**Files:**
- Modify: `www/app.js:142-144` (after `canvasAdvance` method)

- [ ] **Step 1: Add `toggleCanvas` method to SpecIdolClient**

After the `canvasAdvance(direction)` method (line 142-144), add:

```javascript
    toggleCanvas(visible) {
        this.send('toggle_canvas', { visible });
    }
```

- [ ] **Step 2: Verify syntax**

Run: `node -c www/app.js`
Expected: No output (success)

- [ ] **Step 3: Commit**

```bash
git add www/app.js
git commit -m "feat: add toggleCanvas method to SpecIdolClient"
```

---

### Task 3: Controller — canvas toggle checkbox

**Files:**
- Modify: `www/control.html:580-586` (Judge/Audience Config details section)
- Modify: `www/control.html:836-842` (session_state handler — set initial checkbox state)
- Modify: `www/control.html:1444-1451` (after toggleAudienceQR function)

- [ ] **Step 1: Add checkbox HTML**

In the Judge/Audience Config `<details>` (lines 578-587), add a canvas toggle checkbox after the timer checkbox (line 584):

```html
                <label class="config-checkbox">
                    <input type="checkbox" id="toggleTimerCheckbox" checked onchange="toggleTimerVisibility(this.checked)"> Display timer to audience/judges
                </label>
                <label class="config-checkbox">
                    <input type="checkbox" id="toggleCanvasCheckbox" onchange="toggleCanvas(this.checked)"> Display canvas to audience/judges
                </label>
                <div id="judgeQRContainer"></div>
```

- [ ] **Step 2: Set initial checkbox state from session_state**

In the `session_state` handler (around line 841-842), after setting timer visibility toggle state, add:

```javascript
            // Set canvas visibility toggle state
            const canvasVisible = data.canvas_visible === true;
            document.getElementById('toggleCanvasCheckbox').checked = canvasVisible;
```

- [ ] **Step 3: Add `toggleCanvas()` function**

After the `toggleTimerVisibility` function (line 1449-1451), add:

```javascript
        function toggleCanvas(visible) {
            client.toggleCanvas(visible);
        }
```

- [ ] **Step 4: Verify — open control.html in browser**

Manual check: open `http://localhost:8000/control.html?code=TEST`, confirm "Display canvas to audience/judges" checkbox appears in Judge/Audience Config section. Check browser console for no JS errors.

- [ ] **Step 5: Commit**

```bash
git add www/control.html
git commit -m "feat: add canvas toggle checkbox to controller"
```

---

### Task 4: Audience — canvas mode + paragraph overlay

**Files:**
- Modify: `www/audience.html:16-190` (CSS styles)
- Modify: `www/audience.html:246` (add canvasMode variable)
- Modify: `www/audience.html:469-471` (text_advanced handler)
- Modify: `www/audience.html:583-601` (startRound function)
- Modify: `www/audience.html:603-623` (after appendTextLine, add appendOverlayParagraph)
- Modify: `www/audience.html:649-672` (resetView function)
- Add new `toggle_canvas` handler after existing handlers

This is the largest task. Multiple edits to audience.html.

- [ ] **Step 1: Add `.overlay-paragraph` CSS**

After the `#metadataParagraphs` CSS rule (ends at line 189), add:

```css
        .overlay-paragraph {
            background: rgba(0, 0, 0, 0.8);
            padding: 0.75rem 1rem;
            font-size: 1.4rem;
            line-height: 1.6;
            color: #fff;
        }
```

- [ ] **Step 2: Add `canvasMode` variable**

After `let osdViewer = null;` (line 247), add:

```javascript
        let canvasMode = false;
```

- [ ] **Step 3: Update `text_advanced` handler for routing**

Replace the `text_advanced` handler (lines 469-471):

```javascript
        client.on('text_advanced', (data) => {
            appendTextLine(data.paragraph || data.line);
        });
```

With:

```javascript
        client.on('text_advanced', (data) => {
            const text = data.paragraph || data.line;
            if (canvasMode) {
                appendOverlayParagraph(text);
            } else {
                appendTextLine(text);
            }
        });
```

- [ ] **Step 4: Add `appendOverlayParagraph()` function**

After the `appendTextLine()` function (ends at line 623), add:

```javascript
        function appendOverlayParagraph(text) {
            const container = document.getElementById('metadataParagraphs');
            const div = document.createElement('div');
            div.className = 'overlay-paragraph text-line';
            div.textContent = text;
            container.appendChild(div);

            // Auto-scroll overlay to bottom
            const overlay = document.getElementById('textOverlay');
            setTimeout(() => {
                overlay.scrollTop = overlay.scrollHeight;
            }, 100);
        }
```

- [ ] **Step 5: Update `startRound()` — init OSD + apply canvas mode**

In `startRound()` (lines 583-601), replace the OSD block (lines 592-600):

```javascript
            // Show OSD viewer if canvases present
            if (roundData.canvases && roundData.canvases.length > 0) {
                const osdContainer = document.getElementById('osdViewerContainer');
                osdContainer.style.display = 'flex';
                const canvas = roundData.canvases[roundData.canvas_index || 0];
                if (canvas) {
                    initOsdViewer(canvas);
                    showCanvasLabel(canvas.label);
                }
            }
```

With:

```javascript
            // Init OSD viewer if canvases present
            const hasCanvases = roundData.canvases && roundData.canvases.length > 0;
            if (hasCanvases) {
                const canvas = roundData.canvases[roundData.canvas_index || 0];
                if (canvas) {
                    initOsdViewer(canvas);
                    showCanvasLabel(canvas.label);
                }
            }
            applyCanvasMode();
```

- [ ] **Step 6: Add `applyCanvasMode()` helper**

After `appendOverlayParagraph()`, add:

```javascript
        function applyCanvasMode() {
            const osdContainer = document.getElementById('osdViewerContainer');
            const textContainer = document.querySelector('.story-text-container');
            const hasOsd = osdViewer !== null;

            if (canvasMode && hasOsd) {
                osdContainer.style.display = 'flex';
                textContainer.style.display = 'none';
            } else {
                osdContainer.style.display = 'none';
                textContainer.style.display = '';
            }
        }
```

`canvasMode` is the toggle state (set by `toggle_canvas` handler). `hasOsd` checks whether an OSD viewer was initialized (i.e., item has canvases). Both must be true for canvas layout. `canvasMode` persists across rounds — it's the global toggle, not reset when an item lacks canvases.

- [ ] **Step 7: Add `toggle_canvas` handler**

After the `toggle_timer_visibility` handler (lines 428-435), add:

```javascript
        client.on('toggle_canvas', (data) => {
            canvasMode = data.visible;
            applyCanvasMode();
        });
```

- [ ] **Step 8: Update `countdown_start` handler for canvas mode**

In the `countdown_start` handler (lines 385-417), the first paragraph is appended via `appendTextLine`. Update to route based on canvasMode. Find line 393-394:

```javascript
            if (data.first_paragraph || data.first_line) {
                appendTextLine(data.first_paragraph || data.first_line);
            }
```

Replace with:

```javascript
            // Init OSD if canvases present
            const hasCanvases = data.canvases && data.canvases.length > 0;
            if (hasCanvases) {
                const canvas = data.canvases[0];
                if (canvas) {
                    initOsdViewer(canvas);
                    showCanvasLabel(canvas.label);
                }
            }
            applyCanvasMode();

            // Show first paragraph in correct container
            if (data.first_paragraph || data.first_line) {
                const text = data.first_paragraph || data.first_line;
                if (canvasMode && osdViewer) {
                    appendOverlayParagraph(text);
                } else {
                    appendTextLine(text);
                }
            }
```

- [ ] **Step 9: Update `resetView()` to reset `canvasMode`**

In `resetView()` (lines 649-672), after `document.getElementById('metadataParagraphs').innerHTML = '';` (line 660), add:

```javascript
            canvasMode = false;
```

This is already implied by the spec. Also make sure `applyCanvasMode()` is called or text container is shown. The existing code already sets `osdViewerContainer` display to none and doesn't hide `storyText`, so this is fine — but add the variable reset.

- [ ] **Step 10: Update `session_state` handler for initial `canvas_visible`**

In the `session_state` handler (lines 328-383), after the timer visibility check (lines 350-352), add:

```javascript
            // Set initial canvas mode
            if (data.canvas_visible === true) {
                canvasMode = true;
            }
```

- [ ] **Step 11: Verify — open audience.html in browser**

Manual check:
1. Open controller, create session, add item with IIIF manifest
2. Open audience view
3. Toggle "Display canvas to audience/judges" on
4. Start round → verify OSD viewer fills content area, text hidden
5. Click "Reveal Paragraph" → verify overlay paragraph appears on OSD
6. Toggle canvas off → verify OSD hidden, text area shown
7. Click "Reveal Paragraph" → verify text appears in text area

- [ ] **Step 12: Commit**

```bash
git add www/audience.html
git commit -m "feat: add canvas mode and paragraph overlay to audience view"
```

---

### Task 5: Judge — DOM restructure + canvas mode

**Files:**
- Modify: `www/judge.html:16-112` (CSS styles)
- Modify: `www/judge.html:131-139` (main element HTML)
- Modify: `www/judge.html:193` (add canvasMode variable)
- Modify: `www/judge.html:338-392` (countdown_start handler)
- Modify: `www/judge.html:436-438` (text_advanced handler)
- Modify: `www/judge.html:561-598` (startRound function)
- Modify: `www/judge.html:645-655` (resetView function)

This is the most complex task — DOM restructure to keep buzz button persistent.

- [ ] **Step 1: Add canvas-mode CSS**

After the existing `.header-timer.timer-force-hidden` rule (line 109-111), add the new CSS:

```css
        /* Canvas mode layout */
        #osdViewerContainer {
            display: none;
            width: 100%;
            flex: 1;
            flex-direction: column;
            position: relative;
        }

        #canvasLabel {
            font-size: var(--text-caption);
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

        .overlay-paragraph {
            background: rgba(0, 0, 0, 0.8);
            padding: 0.75rem 1rem;
            font-size: 1rem;
            line-height: 1.5;
            color: #fff;
        }

        /* Buzz button container — always in DOM */
        #buzzContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
        }

        /* Canvas mode: floating compact buzz */
        main.canvas-mode #buzzContainer {
            position: fixed;
            top: 5rem;
            right: 1rem;
            z-index: 500;
            gap: 0.25rem;
        }

        main.canvas-mode .buzz-button {
            width: 80px;
            height: 80px;
            max-width: 80px;
            max-height: 80px;
            font-size: var(--text-caption);
        }

        main.canvas-mode .buzz-button .buzzed {
            font-size: 2rem;
        }

        main.canvas-mode .buzz-count {
            font-size: 0.5rem;
        }

        main.canvas-mode .story-title {
            display: none;
        }

        /* Canvas mode: OSD fills main */
        main.canvas-mode {
            padding: 0;
        }

        main.canvas-mode #osdViewerContainer {
            display: flex;
            flex: 1;
        }

        main.canvas-mode .waiting {
            display: none;
        }

        /* Text mode: hide OSD, show centered buzz */
        main:not(.canvas-mode) #osdViewerContainer {
            display: none !important;
        }
```

- [ ] **Step 2: Restructure `<main>` HTML**

Replace the current `<main>` element (lines 131-139):

```html
    <main class="page-content" id="main" role="main">
        <div class="story-title" id="itemTitle" aria-live="polite"></div>
        <div id="osdViewerContainer" style="margin: 0 auto 1rem; max-width: 300px; display: none; background: var(--black); padding: 0.5rem;">
            <div id="canvasLabel" style="font-size: var(--text-caption); color: var(--neon-yellow); text-align: center; margin-bottom: 0.25rem; display: none;"></div>
            <div id="osdViewer" style="width: 100%; height: 250px;"></div>
        </div>
        <div id="metadataParagraphs" style="max-width: 400px; margin: 0 auto; text-align: left;"></div>
        <div class="waiting">Waiting for round to start...</div>
    </main>
```

With:

```html
    <main class="page-content" id="main" role="main">
        <div class="story-title" id="itemTitle" aria-live="polite"></div>
        <div id="osdViewerContainer">
            <div id="canvasLabel"></div>
            <div id="osdViewer"></div>
            <div id="textOverlay">
                <div id="metadataParagraphs" aria-live="polite" aria-relevant="additions"></div>
            </div>
        </div>
        <div id="buzzContainer">
            <button class="buzz-button" id="buzzButton" onclick="buzz()" aria-label="Buzz out the reader" disabled>BUZZ</button>
            <div class="buzz-count" id="buzzCountDisplay" aria-live="polite">0 of 0 buzzed</div>
        </div>
        <div class="judge-status" id="judgeStatus"></div>
        <div class="waiting" id="waitingMessage">Waiting for round to start...</div>
    </main>
```

Key changes: buzz button is now always in DOM (not created by innerHTML). OSD container uses CSS classes instead of inline styles. `#textOverlay` added for paragraph overlay.

- [ ] **Step 3: Add `canvasMode` variable**

After `let osdViewer = null;` (line 193), add:

```javascript
        let canvasMode = false;
```

- [ ] **Step 4: Add `applyCanvasMode()` and `appendOverlayParagraph()` functions**

After `showCanvasLabel()` (line 253-258), add:

```javascript
        function applyCanvasMode() {
            const main = document.getElementById('main');
            if (canvasMode && osdViewer) {
                main.classList.add('canvas-mode');
            } else {
                main.classList.remove('canvas-mode');
            }
        }

        function appendOverlayParagraph(text) {
            const container = document.getElementById('metadataParagraphs');
            const div = document.createElement('div');
            div.className = 'overlay-paragraph text-line';
            div.textContent = text;
            container.appendChild(div);

            const overlay = document.getElementById('textOverlay');
            setTimeout(() => {
                overlay.scrollTop = overlay.scrollHeight;
            }, 100);
        }
```

- [ ] **Step 5: Rewrite `countdown_start` handler**

Replace the entire `countdown_start` handler (lines 338-392). The old one does `main.innerHTML = ...` which creates all elements. New one uses persistent DOM:

```javascript
        client.on('countdown_start', (data) => {
            // Reset judge state fully
            buzzed = false;
            if (timer) timer.stop();
            if (countdown) countdown.cancel();

            // Show title
            document.getElementById('itemTitle').textContent = data.item_title || '';

            // Hide waiting message
            document.getElementById('waitingMessage').style.display = 'none';

            // Reset buzz button
            const buzzButton = document.getElementById('buzzButton');
            buzzButton.disabled = true;
            buzzButton.innerHTML = 'BUZZ';

            // Update buzz count
            const buzzCountEl = document.getElementById('buzzCountDisplay');
            buzzCountEl.textContent = `0 of ${connectedJudges.length} buzzed`;

            // Init OSD if canvases present
            const hasCanvases = data.canvases && data.canvases.length > 0;
            if (hasCanvases) {
                const canvas = data.canvases[0];
                initOsdViewer(canvas);
                showCanvasLabel(canvas.label);
            }
            applyCanvasMode();

            renderJudgePanels(false);

            // Show header timer (reset to 0)
            const headerTimer = document.getElementById('headerTimer');
            headerTimer.textContent = '0:00.0';
            headerTimer.style.display = 'flex';

            // Start countdown, then activate
            countdown = new Countdown('countdown-container', () => {
                // Countdown complete — activate buzz button
                if (!buzzed) buzzButton.disabled = false;

                if (!timer || !timer.intervalId) {
                    timer = new Timer(
                        Infinity,
                        (elapsed) => {
                            document.getElementById('headerTimer').textContent = formatTime(elapsed);
                        }
                    );
                    timer.startTime = Date.now() / 1000;
                    timer.tick();
                    timer.intervalId = setInterval(() => timer.tick(), 100);
                }
            });
            countdown.start();
        });
```

- [ ] **Step 6: Update `text_advanced` handler**

Replace the text_advanced handler (lines 436-438):

```javascript
        client.on('text_advanced', (data) => {
            // Judges don't display text, but handle event to suppress console warning
        });
```

With:

```javascript
        client.on('text_advanced', (data) => {
            if (canvasMode && osdViewer) {
                appendOverlayParagraph(data.paragraph || data.line);
            }
            // In text mode, judges don't display text paragraphs
        });
```

- [ ] **Step 7: Add `toggle_canvas` handler**

After the `toggle_timer_visibility` handler (lines 329-336), add:

```javascript
        client.on('toggle_canvas', (data) => {
            canvasMode = data.visible;
            applyCanvasMode();
        });
```

- [ ] **Step 8: Rewrite `startRound()` function**

Replace the existing `startRound()` function (lines 561-598). The old one does `main.innerHTML = ...`. New one uses persistent DOM:

```javascript
        function startRound(roundData) {
            buzzed = false;

            // Show title
            document.getElementById('itemTitle').textContent = roundData.title || '';

            // Hide waiting message
            document.getElementById('waitingMessage').style.display = 'none';

            // Reset and enable buzz button
            const buzzButton = document.getElementById('buzzButton');
            buzzButton.disabled = false;
            buzzButton.innerHTML = 'BUZZ';

            // Update buzz count
            const buzzCountEl = document.getElementById('buzzCountDisplay');
            buzzCountEl.textContent = `0 of ${connectedJudges.length} buzzed`;

            // Init OSD if canvases present
            const hasCanvases = roundData.canvases && roundData.canvases.length > 0;
            if (hasCanvases) {
                const canvas = roundData.canvases[roundData.canvas_index || 0];
                if (canvas) {
                    initOsdViewer(canvas);
                    showCanvasLabel(canvas.label);
                }
            }
            applyCanvasMode();

            renderJudgePanels(false);

            // Show header timer
            const headerTimer = document.getElementById('headerTimer');
            headerTimer.style.display = 'flex';

            if (timer) timer.stop();
            timer = new Timer(
                Infinity,
                (elapsed) => {
                    document.getElementById('headerTimer').textContent = formatTime(elapsed);
                }
            );
            timer.start(roundData.start_time);
        }
```

- [ ] **Step 9: Rewrite `resetView()` function**

Replace the existing `resetView()` (lines 645-655):

```javascript
        function resetView() {
            if (timer) timer.stop();
            if (countdown) countdown.cancel();
            destroyOsdViewer();
            buzzed = false;
            document.getElementById('main').innerHTML = '<div class="story-title" id="itemTitle" aria-live="polite"></div><div class="waiting">Waiting for round to start...</div>';
            document.getElementById('headerTimer').style.display = 'none';
            document.querySelectorAll('.judge-cell').forEach(cell => {
                cell.classList.remove('buzzed');
            });
        }
```

With:

```javascript
        function resetView() {
            if (timer) timer.stop();
            if (countdown) countdown.cancel();
            destroyOsdViewer();
            buzzed = false;
            canvasMode = false;

            // Reset title
            document.getElementById('itemTitle').textContent = '';

            // Show waiting message
            document.getElementById('waitingMessage').style.display = '';

            // Reset buzz button
            const buzzButton = document.getElementById('buzzButton');
            buzzButton.disabled = true;
            buzzButton.innerHTML = 'BUZZ';

            // Clear overlay paragraphs
            document.getElementById('metadataParagraphs').innerHTML = '';

            // Remove canvas mode
            document.getElementById('main').classList.remove('canvas-mode');

            // Hide timer
            document.getElementById('headerTimer').style.display = 'none';

            // Clear buzzed state on judge panels
            document.querySelectorAll('.judge-cell').forEach(cell => {
                cell.classList.remove('buzzed');
            });
        }
```

- [ ] **Step 10: Update `session_state` handler for initial `canvas_visible`**

In the `session_state` handler (lines 266-327), after the timer visibility check (lines 280-282), add:

```javascript
            // Set initial canvas mode
            if (data.canvas_visible === true) {
                canvasMode = true;
            }
```

- [ ] **Step 11: Fix `round_started` handler**

The `round_started` handler (lines 394-418) currently checks for `existingBtn` (from the old innerHTML approach). Since buzz button is now always in DOM, simplify. Replace lines 394-418:

```javascript
        client.on('round_started', (data) => {
            if (data.server_time) updateClockOffset(data.server_time);

            // Enable button if not already buzzed
            const buzzButton = document.getElementById('buzzButton');
            if (buzzButton && !buzzed) buzzButton.disabled = false;

            // Start server-synced timer (supersedes countdown timer)
            if (timer) timer.stop();
            timer = new Timer(
                timerDuration,
                (elapsed) => {
                    document.getElementById('headerTimer').textContent = formatTime(elapsed);
                },
                () => {
                    if (typeof playVictoryFanfare === 'function') playVictoryFanfare();
                }
            );
            timer.start(data.start_time || (Date.now() / 1000));
        });
```

Wait — the old `round_started` also has a fallback that calls `startRound(data)` if no existing button (late join). With persistent DOM, buzz button always exists, so we always just sync the timer. But what about late joins that missed `countdown_start`? The title and OSD won't be set up. Need to handle that.

Check the flow: if a judge late-joins during a running round, they get `session_state` with `current_round.status === 'running'`, which calls `startRound(round)` in the session_state handler (line 298). So the `round_started` handler only fires for judges who were present during countdown. The persistent button approach means we just enable the button and start timer. Late joins are handled via `session_state` → `startRound()`.

But we should also handle: judge was present but OSD/title wasn't set up (e.g., countdown was skipped, direct `round_start` without countdown). In that case `round_started` fires without prior `countdown_start`. We need to init OSD + set title.

Update the `round_started` handler:

```javascript
        client.on('round_started', (data) => {
            if (data.server_time) updateClockOffset(data.server_time);

            // Set up title and OSD if not already done by countdown_start
            const titleEl = document.getElementById('itemTitle');
            if (!titleEl.textContent) {
                titleEl.textContent = data.title || '';
                document.getElementById('waitingMessage').style.display = 'none';

                const hasCanvases = data.canvases && data.canvases.length > 0;
                if (hasCanvases) {
                    const canvas = data.canvases[data.canvas_index || 0];
                    if (canvas) {
                        initOsdViewer(canvas);
                        showCanvasLabel(canvas.label);
                    }
                }
                applyCanvasMode();
                renderJudgePanels(false);
            }

            // Enable button if not already buzzed
            const buzzButton = document.getElementById('buzzButton');
            if (buzzButton && !buzzed) buzzButton.disabled = false;

            // Update buzz count
            const buzzCountEl = document.getElementById('buzzCountDisplay');
            if (buzzCountEl) {
                buzzCountEl.textContent = `0 of ${connectedJudges.length} buzzed`;
            }

            // Start server-synced timer (supersedes countdown timer)
            const headerTimer = document.getElementById('headerTimer');
            headerTimer.style.display = 'flex';
            if (timer) timer.stop();
            timer = new Timer(
                Infinity,
                (elapsed) => {
                    headerTimer.textContent = formatTime(elapsed);
                }
            );
            timer.start(data.start_time || (Date.now() / 1000));
        });
```

- [ ] **Step 12: Fix `session_state` handler buzz replay**

In the `session_state` handler (lines 296-326), the buzz replay code references `button` from the old innerHTML. The persistent button is always `document.getElementById('buzzButton')`. Lines 300-309 need updating:

Find:
```javascript
                if (round.buzzes) {
                    round.buzzes.forEach(b => {
                        updateJudgeStatus(b.judge_id);
                        if (b.judge_id === myJudgeId) {
                            buzzed = true;
                            const button = document.getElementById('buzzButton');
                            if (button) {
                                button.disabled = true;
                                button.innerHTML = '<div class="buzzed">✕</div>';
                            }
                        }
                    });
                }
```

This code already uses `document.getElementById('buzzButton')` and checks for null. With the persistent DOM, button always exists. No change needed — it works as-is.

- [ ] **Step 13: Fix `round_ended` handler**

The `round_ended` handler (lines 479-487) disables the button. This still works with persistent DOM — no change needed.

- [ ] **Step 14: Fix `paused` and `resumed` handlers**

The `paused` handler (lines 420-426) and `resumed` handler (lines 428-434) reference `document.getElementById('buzzButton')`. These work with persistent DOM. No change needed.

- [ ] **Step 15: Verify — open judge.html in browser**

Manual check:
1. Open controller, create session, add item with IIIF manifest
2. Open judge view, connect
3. Toggle "Display canvas to audience/judges" on
4. Start round → verify OSD viewer fills judge content area, buzz button is compact floating top-right
5. Verify buzz button works (click it, shows ✕)
6. Toggle canvas off → verify big centered buzz button layout returns
7. Check: paragraph overlay appears when text advanced in canvas mode

- [ ] **Step 16: Commit**

```bash
git add www/judge.html
git commit -m "feat: restructure judge view with persistent buzz button and canvas mode"
```

---

### Task 6: Cross-file verification

**Files:**
- All modified files

- [ ] **Step 1: Verify Python syntax**

Run: `python3 -c "import py_compile; py_compile.compile('server/relay.py', doraise=True)"`
Expected: No output (success)

- [ ] **Step 2: Verify JS syntax**

Run: `node -c www/app.js`
Expected: No output (success)

- [ ] **Step 3: Check message type consistency**

Verify all files agree on message type name `toggle_canvas`:
- `server/relay.py`: handler for `toggle_canvas`, broadcasts `toggle_canvas`
- `www/app.js`: `toggleCanvas()` sends `toggle_canvas`
- `www/control.html`: calls `client.toggleCanvas()`, has handler for `toggle_canvas` (via session_state initial state)
- `www/audience.html`: handler for `toggle_canvas`
- `www/judge.html`: handler for `toggle_canvas`

Run: `grep -rn "toggle_canvas" server/relay.py www/app.js www/control.html www/audience.html www/judge.html`
Expected: matches in all 5 files

- [ ] **Step 4: Check `canvas_visible` consistency**

Run: `grep -rn "canvas_visible" server/relay.py www/control.html www/audience.html www/judge.html`
Expected: matches in relay.py (session init + session_state), control.html (initial state), audience.html (initial state), judge.html (initial state)

- [ ] **Step 5: Integration test**

Manual browser test — full flow:
1. `make dev` to start servers
2. Open controller → create session → add item with IIIF manifest URL
3. Open audience + judge in separate tabs
4. Check "Display canvas to audience/judges" checkbox in controller
5. Start round → all 3 views should show OSD, audience + judge have overlay paragraphs when text advanced
6. Uncheck canvas → audience + judge switch to text mode
7. Re-check canvas → back to canvas mode
8. Close round → reset works cleanly
9. Start round with item that has NO canvases → text mode regardless of toggle

- [ ] **Step 6: Commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: resolve cross-file issues from canvas mode integration"
```

Only if fixes were needed. Skip if clean.
