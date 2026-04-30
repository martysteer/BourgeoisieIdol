# IIIF Viewer Post-Testing Fixes

## Context
After implementing OSD integration (8 tasks, 7 commits), user tested and found 6 issues: broken OSD button icons, non-working canvas nav, no manifest auto-fill, duplicate title display, viewer not filling space, and text displaying below viewer instead of overlaid on it.

## Fix 1: OSD Button Icons — Custom Soviet SVGs
**Files:** `www/audience.html`, `www/judge.html`, `www/control.html`

**Problem:** `prefixUrl: ''` means OSD looks for button PNGs at root — no images vendored. Buttons render as broken `<img>` tags.

**Fix:** Add `navImages` config to all `initOsdViewer()` calls with inline SVG data URIs. Soviet-themed geometric icons using `--soviet-red` (#b71c1c) and `--soviet-gold`/ochre colors. Four buttons: zoomIn (+), zoomOut (-), home (star), fullpage (expand arrows).

Each button has 4 states (REST, GROUP, HOVER, DOWN) — use same SVG per button, just change opacity/color for hover/down states.

Define SVG data URIs once per file in a `const OSD_NAV_IMAGES = {...}` object, pass to `OpenSeadragon()` config as `navImages: OSD_NAV_IMAGES`.

## Fix 2: Canvas Navigation Buttons
**Files:** `www/control.html`

**Problem:** User reports next/prev canvas buttons don't work. Server handler confirmed correct (relay.py:418-445). Code path looks correct on paper: `advanceCanvas()` → `client.canvasAdvance(direction)` → server broadcasts `canvas_advanced` → handler updates OSD.

**Likely issue:** The `updateCanvasControls()` guard checks `sessionState.current_round.status !== 'running'` and disables buttons. If `sessionState.current_round.status` isn't properly updated, buttons stay disabled. Also possible: manifest only had 1 canvas during test (buttons correctly disabled for single canvas).

**Fix:** Verify the state flow. Add console.log debugging if needed during manual test. The code looks correct — may need to verify with multi-canvas manifest. If bug found during implementation, fix it.

## Fix 3: Manifest Auto-Fill Title/Text
**Files:** `server/relay.py`, `www/control.html`

**Problem:** Fetch Manifest button fetches canvases but doesn't extract manifest-level metadata (label, description, metadata pairs). User wants auto-fill of title and text fields.

**Server changes (`relay.py`):**
- Add `extract_manifest_metadata(manifest)` function that extracts:
  - `label`: from `manifest.label` (v3 language map) or `manifest.label` (v2 string)
  - `description`: from `manifest.summary` (v3) or `manifest.description` (v2)
  - `metadata`: from `manifest.metadata[]` — array of {label, value} pairs
- Update `fetch_manifest()` to return `(canvases, metadata, error)` — metadata is `{label, description, metadata_text}`
  - `metadata_text`: format metadata pairs as readable paragraphs: `"Label: Value\n\nLabel2: Value2"`
- Update `fetch_manifest` message handler to include metadata in response

**Client changes (`control.html`):**
- Update `manifest_fetched` handler to auto-fill:
  - If `data.metadata.label` exists and title field empty → set title field
  - If `data.metadata.metadata_text` exists and text field empty → set text field
  - Don't overwrite if user already typed something

## Fix 4: Remove Duplicate Round Question
**Files:** `www/audience.html`

**Problem:** `#roundQuestion` div at line 160 shows same title that's already in header `#itemTitle`. Redundant.

**Fix:**
- Remove `<div id="roundQuestion" ...>` from HTML (line 160)
- Remove `questionEl` references from `startRound()` function (lines 394-396)
- Remove `roundQuestion` hide from `resetView()` (line 473)

## Fix 5: Viewer Fills Available Space
**Files:** `www/audience.html`

**Problem:** OSD viewer has fixed `height: 60vh` and container has `margin: 0 auto 2rem`. Doesn't fill available viewport.

**Fix:**
- Change `#osdViewerContainer` to `flex: 1; display: flex; flex-direction: column;` when visible
- Change `#osdViewer` to `flex: 1` instead of `height: 60vh`
- Remove `margin-bottom: 2rem` from container
- Structure: header + viewer fills remaining space, text overlays on viewer

## Fix 6: Text Overlay on Viewer
**Files:** `www/audience.html`, `www/control.html`

**Problem:** Text paragraphs display below the OSD viewer in a separate container. User wants text overlaid on the viewer, without blocking pinch/zoom.

**Audience fix:**
- Move `#metadataParagraphs` inside `#osdViewerContainer`, positioned absolutely over the viewer
- Add overlay container: `position: absolute; bottom: 0; left: 0; right: 0; pointer-events: none; z-index: 10;`
- Text blocks get semi-transparent dark background (`rgba(0, 0, 0, 0.75)`) for readability
- Remove the separate `.story-text-container` div
- `pointer-events: none` on overlay so OSD zoom/pan works through text

**Controller fix:**
- Same pattern: move `#liveStoryText` into `#osdViewerContainer` as absolute overlay
- Smaller text (already `var(--text-body)`)
- When no OSD viewer (text-only items), text displays normally in story-text-column

## Implementation Order
1. Fix 4 (remove roundQuestion) — simplest, no deps
2. Fix 5 (viewer fills space) — layout change needed before overlay
3. Fix 1 (OSD button icons) — visual fix, independent
4. Fix 6 (text overlay) — depends on Fix 5 layout
5. Fix 3 (manifest auto-fill) — server + client, independent
6. Fix 2 (canvas nav debug) — verify during manual test after other fixes

## Verification
- `make dev` — start servers
- Open controller, create session
- Add item with multi-canvas IIIF manifest (e.g. https://iiif.bodleian.ox.ac.uk/iiif/manifest/e32a277e-91e2-4a6d-8ba6-cc4bad230410.json)
- Verify: Fetch Manifest auto-fills title and text
- Verify: OSD buttons show Soviet-styled SVG icons (not broken images)
- Start round, verify viewer fills audience viewport
- Verify text paragraphs overlay on viewer without blocking zoom
- Verify canvas next/prev buttons work with multi-canvas manifest
- Verify roundQuestion div no longer appears in audience view
- Check judge view OSD buttons also show custom icons
