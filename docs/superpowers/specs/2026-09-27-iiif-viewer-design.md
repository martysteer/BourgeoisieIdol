# IIIF Viewer Experience Design

**Goal:** Wire up canvas display toggle, paragraph overlay on OSD viewer, and redesign judge view for full IIIF interaction.

**Context:** The OSD viewer infrastructure and paragraph advance server logic exist but are disconnected. Text always routes to the main text area regardless of canvas presence. Judges see a tiny OSD viewer that prevents interaction.

---

## 1. Server & Message Protocol

### Session State

Add `canvas_visible: false` to session dict initialization. Include in `session_state` response so late-joining clients get current layout.

### New Message: `toggle_canvas`

Controller-only command. Mirrors the `toggle_audience_qr` pattern exactly.

- **Client sends:** `{type: "toggle_canvas", data: {visible: true/false}}`
- **Server:** updates `session["canvas_visible"]`, broadcasts to all clients
- **Broadcast:** `{type: "toggle_canvas", data: {visible: true/false}}`
- Add `"toggle_canvas"` to `CONTROLLER_ONLY` set

### Controller UI

New checkbox in Judge/Audience Config details section: "Display canvas to audience/judges". Mirrors QR toggle: `onchange="toggleCanvas(this.checked)"`. Initial state from `session_state.canvas_visible`.

### No Changes To

`text_advance`, `canvas_advance`, `round_start`, `countdown_start` — text and canvas remain independent operations with independent controller buttons.

---

## 2. Audience View — Canvas Mode & Paragraph Overlay

### Two Display Modes

Controlled by local `canvasMode` boolean, set from `toggle_canvas` handler and `startRound`.

**Canvas mode** (`canvas_visible: true` AND current item has canvases):
- OSD viewer container visible, fills content area
- `#storyText` container hidden
- `text_advanced` paragraphs append to `#metadataParagraphs` inside `#textOverlay`
- `#textOverlay` is positioned absolute, bottom-pinned on OSD viewer, max-height 50%, overflow-y auto, pointer-events none

**Text mode** (default / `canvas_visible: false` / item has no canvases):
- OSD viewer container hidden
- `#storyText` container visible
- `text_advanced` paragraphs append to `#storyText` via existing `appendTextLine()`

### `appendOverlayParagraph(text)`

- Creates `<div class="overlay-paragraph text-line">` with text content
- Appends to `#metadataParagraphs`
- Auto-scrolls `#textOverlay` to bottom after 100ms delay
- Styling via `.overlay-paragraph` CSS class (not inline):
  - Semi-transparent black background (`rgba(0, 0, 0, 0.8)`)
  - Padding, readable font size
  - Uses existing `.text-line` animation (fade-in + translate)
  - All styling in CSS class for easy restyling later

### `text_advanced` Handler (Updated)

```
if canvasMode:
    appendOverlayParagraph(data.paragraph || data.line)
else:
    appendTextLine(data.paragraph || data.line)
```

### Toggle Mid-Round

If controller toggles canvas off during a running round:
- Hide OSD viewer, show `#storyText`
- Future paragraphs route to `#storyText`
- Already-revealed overlay paragraphs are lost (acceptable — simpler than migrating DOM nodes)

If controller toggles canvas on during a running round:
- Show OSD viewer (init if canvases available), hide `#storyText`
- Future paragraphs route to overlay
- Already-revealed text paragraphs remain in `#storyText` but hidden

### Reset

`resetView()` destroys OSD, clears both `#metadataParagraphs` and `#storyText`, sets `canvasMode = false`.

---

## 3. Judge View — Full OSD + Floating Buzz Button

### Layout Redesign

Two modes switched by CSS class on `<main>`:

**Canvas mode** (`<main class="canvas-mode">`):
- OSD viewer full-width, full-height of content area (same as audience)
- Paragraph overlay: bottom-pinned on OSD, semi-transparent, same as audience
- Buzz button: compact floating circle, top-right corner, ~80px diameter, fixed position, high z-index
- Buzz count ("0 of 3 buzzed"): small text positioned near the floating buzz button
- Shows `✕` when buzzed, button disabled

**Text mode** (default):
- Current layout: big centered buzz button, no OSD
- Identical to current judge.html behavior

### DOM Structure Change

Currently `countdown_start` handler does `main.innerHTML = ...` which destroys all elements. Change to:
- Pre-build layout with both modes' elements in HTML
- Toggle visibility via CSS class (`canvas-mode`) on `<main>`
- Buzz button lives in a fixed-position container that's never destroyed by innerHTML
- `countdown_start` and `startRound` toggle the CSS class based on `canvasMode`

Buzz button container (always in DOM):
```html
<div id="buzzContainer" class="buzz-floating">
    <button id="buzzButton" class="buzz-button" onclick="buzz()">BUZZ</button>
    <div id="buzzCountDisplay" class="buzz-count">0 of 0 buzzed</div>
</div>
```

In text mode: `.buzz-floating` is centered, button is large (current sizing).
In canvas mode: `.buzz-floating` is fixed top-right, button is compact (80px circle).

### Paragraph Routing

Same as audience: `canvasMode` boolean, `text_advanced` routes to `#metadataParagraphs` overlay when in canvas mode.

### Canvas Mode Toggle

`toggle_canvas` handler sets `canvasMode`, adds/removes `canvas-mode` class on `<main>`, shows/hides OSD viewer, same logic as audience.

---

## 4. What Stays The Same

- Controller OSD viewer and canvas navigation buttons — unchanged
- `canvas_advance` message type and handler — unchanged
- Server paragraph chunking (`\n\n` split) — unchanged
- `text_advance` server logic — unchanged
- Countdown 3-2-1 sequence — unchanged
- Sounds, QR overlay, timer visibility — unchanged
- `appendTextLine()` function — unchanged, still used in text mode

---

## 5. File Changes Summary

| File | Changes |
|------|---------|
| `server/relay.py` | Add `canvas_visible` to session state, add `toggle_canvas` handler, add to `CONTROLLER_ONLY` |
| `www/control.html` | Add canvas toggle checkbox, `toggleCanvas()` function, `toggle_canvas` handler for initial state |
| `www/audience.html` | Add `canvasMode` state, update `text_advanced` handler routing, add `appendOverlayParagraph()`, add `toggle_canvas` handler, add `.overlay-paragraph` CSS |
| `www/judge.html` | Restructure DOM (persistent buzz button, OSD container), add `canvas-mode` CSS, add `canvasMode` state, same paragraph routing as audience, add `toggle_canvas` handler |
| `www/app.js` | Add `toggleCanvas(visible)` method to SpecIdolClient |
