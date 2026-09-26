# BourgeoisieIdol: Rebase onto SpecIdol

**Date:** 2026-09-26
**Status:** Draft

## Goal

Rebase BourgeoisieIdol on top of SpecIdol's current HEAD (`35dfafb`), bringing all SpecIdol UX improvements into BourgeoisieIdol while preserving BourgeoisieIdol's IIIF item/canvas domain model and OpenSeadragon viewer. Keep SpecIdol's existing retro game-show visual style — do not apply the Soviet mosaic reskin.

## Context

Both repos forked from commit `aeeebca` (2026-04-18). Since then:

- **SpecIdol** added 43 commits: QR code overlays, 3-2-1 countdown, `sounds.js` synth engine, buzz-tester page, judge-test page, mobile bug fixes, audio unlock improvements, story editing, timer/QR visibility toggles.
- **BourgeoisieIdol** added 24 commits: IIIF manifest integration (stories → items with canvases), OpenSeadragon viewer on all views, canvas navigation, paragraph-based text chunking, Soviet mosaic reskin (excluded from this rebase), libre typography fonts, branding.

A git merge is not viable — both forks modified the same 6 core files in incompatible ways. Instead: start from SpecIdol HEAD, reimplement BourgeoisieIdol's IIIF layer on top.

## What Stays from SpecIdol (Unchanged)

These SpecIdol features carry over as-is:

- **QR code overlays** — controller toggles QR on audience view; session cards show QR on index page; `lib/qrcode-generator.js` vendored library
- **3-2-1 countdown** — `countdown_start` message type, `Countdown` class in `app.js`, countdown handlers on audience/judge/controller
- **`sounds.js` synth engine** — external module with buzz presets, victory fanfare, countdown beeps, tension ticks, ahooga
- **`buzz-tester.html`** — sound design sandbox page with 71 presets, auto-stack toggle, edit-in-place
- **`judge-test.html`** — judge testing dashboard
- **Timer/QR visibility toggles** — `toggle_audience_qr`, `toggle_timer_visibility` message types and handlers
- **Mobile fixes** — iOS audio unlock, mobile timer toggle, outcome text clipping, judge page round-start fix, audience count fix
- **Story editing** — `update_story` handler (will become `update_item`)
- **Visual style** — neon green/yellow/magenta palette, Press Start 2P headings, Courier New body, CRT scanlines, glow effects. All retained.

## Changes: Layer by Layer

### Layer 1: Domain Model (stories → IIIF items)

**Server (`relay.py`):**

| SpecIdol | BourgeoisieIdol |
|----------|-----------------|
| `stories` list of `{title, text}` | `items` list of `{title, text, manifestUrl, canvases}` |
| `add_story` / `story_added` | `add_item` / `item_added` |
| `remove_story` / `story_removed` | `remove_item` / `item_removed` |
| `update_story` / `stories_update` | `update_item` / `items_update` |
| `round_start` with `story_index` | `round_start` with `item_index` |
| Text split: sentences (regex `.!?`) | Text split: paragraphs (double newline) |
| No canvas state | `canvases`, `canvas_index` in `current_round` |

New server handlers:
- `fetch_manifest` — HTTP GET a IIIF manifest URL, parse JSON, return canvas info + metadata
- `canvas_advance` — increment/decrement `canvas_index`, broadcast new canvas state

New server helper functions:
- `extract_canvas_info(manifest)` — parse IIIF v2/v3 manifest into `[{id, label, imageUrl, width, height}]`
- `extract_localized_value(value)` — handle IIIF language maps (`{"en": ["..."]}}` etc.)
- `extract_manifest_metadata(manifest)` — pull label, description, metadata fields

Round state additions:
```python
current_round = {
    ...existing fields...,
    "canvases": [],       # from item's canvases array
    "canvas_index": 0,    # current canvas position
}
```

Broadcast additions — `session_state` and `round_update` messages include `canvases` and `canvas_index`.

**Client (`app.js`):**

| SpecIdol method | BourgeoisieIdol method |
|----------------|----------------------|
| `addStory(title, text)` | `addItem(title, text, manifestUrl, canvases)` |
| `removeStory(storyIndex)` | `removeItem(itemIndex)` |
| `startRound(storyIndex)` | `startRound(itemIndex)` |
| `advanceText()` | `advanceText()` (unchanged name) |
| — | `fetchManifest(manifestUrl)` (new) |
| — | `canvasAdvance(direction)` (new — sends `{type: "canvas_advance", data: {direction: 1|-1}}`) |

### Layer 2: OpenSeadragon Viewer

**Vendor:** `www/openseadragon.min.js` (v5.0.0)

**Integration on all three display views:**

**audience.html:**
- OSD viewer div in main content area (replaces/augments text-only display)
- Canvas label above viewer
- Metadata paragraphs below viewer (revealed progressively like text lines)
- OSD initialized on `round_update` when canvases present
- `canvas_advance` handler updates OSD `tileSources`
- Navigation buttons: zoom in/out, home, fullscreen
- Falls back to text-only display when item has no canvases

**judge.html:**
- Smaller OSD viewer (250px height, 300px max-width) — judge needs the buzz button prominent
- Canvas label + metadata paragraphs below viewer
- Same `canvas_advance` handler
- Falls back to text-only when no canvases

**control.html:**
- OSD viewer in live display column (right side)
- Canvas navigation controls: "Prev Canvas" / "Next Canvas" buttons
- Canvas progress indicator: "Canvas N / Total"
- Controller sends `canvas_advance` messages (only controller has this authority)
- Keyboard: up/down arrows for canvas navigation (in addition to existing space/right for text advance)

**Conditional rendering:** When an item has no `manifestUrl` or empty `canvases`, all views fall back to the existing text-only display mode. OSD viewer div hidden, text display shown. This preserves compatibility with plain text items.

### Layer 3: Controller IIIF UI

Changes to the item management section of `control.html`:

- **Add Item form:**
  - Title input (same as story title)
  - Manifest URL input (new text field)
  - "Fetch Manifest" button — calls `client.fetchManifest(url)`, populates canvases list and auto-fills metadata text
  - Metadata text textarea (replaces story text — pre-filled from manifest description if fetched)
  - Canvas list preview (read-only, shows fetched canvas labels)

- **Item queue display:**
  - Each item shows: title, canvas count (if any), text preview
  - Inline "Remove" button per item

- **Live display column:**
  - "Reveal Next Paragraph" label on advance button (replaces "Advance Text")
  - Canvas navigation controls when active item has canvases

### Layer 4: Branding

Files replaced wholesale from BourgeoisieIdol:
- `CLAUDE.md` — BourgeoisieIdol project instructions, thematic framework, conference context
- `README.md` — BourgeoisieIdol readme with IIIF references, thematic framing
- `LICENSE` — Anti-Capitalist Software License v1.4

Files modified:
- `index.html` — page title and heading: "BourgeoisieIdol" instead of "SpecIdol". Thematic subtitle. Rest of UX (session cards, QR codes, join flow) stays as SpecIdol has it.

Docs directory:
- Copy BourgeoisieIdol's `docs/sources/` (thematic reference materials)
- Copy BourgeoisieIdol's `docs/CHANGELOG.md` (will need updating post-rebase)
- Existing SpecIdol docs (design specs, implementation plans) stay — they document the feature history

### Layer 5: Assets

- `www/degheest/` — libre/open font directory (FT88, Director, etc.). Copied from BourgeoisieIdol. Available for use but not force-applied — SpecIdol's Press Start 2P + Courier New remain the active typography.
- `www/openseadragon.min.js` — vendored OpenSeadragon v5.0.0

### Layer 6: Excluded

These BourgeoisieIdol changes are deliberately NOT applied:

- `7f8616a` "Soviet mosaic color palette and geometric framing" — the CSS custom property overrides, geometric border treatments, mosaic-inspired color values
- Any changes to `style.css` `:root` variables that alter the neon green/yellow/magenta/red palette
- Any font-family changes from Press Start 2P / Courier New to degheest fonts
- The BourgeoisieIdol `style.css` as a whole is NOT copied — SpecIdol's `style.css` stays, only additions needed for OSD viewer styling are added

## Implementation Strategy

**Working copy:** BourgeoisieIdol repo, new branch `feat/specidol-rebase`

**Method:** Copy SpecIdol's current source files as the new base, then apply BourgeoisieIdol layers as a series of commits.

**Commit sequence:**

1. **Replace source with SpecIdol HEAD** — copy `server/`, `www/`, `Makefile`, `Dockerfile`, `.gitignore` from SpecIdol. Commit as "chore: rebase onto SpecIdol HEAD (35dfafb)".

2. **Domain model: stories → items** — modify `relay.py` and `app.js`. Rename all story references to item references. Add IIIF manifest fetching, canvas state, paragraph-based text chunking. Commit as "feat: transform domain model from stories to IIIF items".

3. **Vendor OpenSeadragon** — add `www/openseadragon.min.js`. Commit as "chore: vendor OpenSeadragon 5.0.0".

4. **Add OSD viewer to all views** — modify `audience.html`, `judge.html`, `control.html` with OSD viewer integration, canvas navigation, conditional rendering. Commit as "feat: add OpenSeadragon IIIF viewer to all views".

5. **Controller IIIF UI** — update item management form with manifest URL, fetch button, canvas controls. Commit as "feat: add IIIF manifest fetching and canvas controls to controller".

6. **Branding** — replace `CLAUDE.md`, `README.md`, `LICENSE`. Update `index.html` title/heading. Copy `docs/sources/`, update changelog. Commit as "feat: rebrand to BourgeoisieIdol with thematic framework".

7. **Assets** — copy `www/degheest/` fonts directory. Commit as "chore: add degheest libre typography fonts".

**Validation after each commit:** Manual browser testing — start servers, create session, verify each role view works.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| SpecIdol's countdown/sounds reference "story" terminology in UI strings | Search-and-replace in commit 2, verify all user-facing strings say "item" |
| `sounds.js` may reference story-specific events | Review `sounds.js` — it's event-driven (buzz, victory, countdown), not domain-coupled. Should work unchanged. |
| OSD viewer CSS may conflict with SpecIdol's existing styles | Scope OSD styles with `.osd-viewer-container` class prefix |
| Buzz-tester and judge-test pages reference stories | These are standalone test pages — update terminology if needed, or leave as-is since they test sounds/buzzing, not domain model |
| `qrcode-generator.js` and `openseadragon.min.js` both vendored in `www/` | Move both to `www/lib/` for cleanliness, or leave flat — low risk either way |

## Success Criteria

- All SpecIdol features work: QR overlays, countdown, synth sounds, buzz-tester, judge-test, timer/QR toggles
- IIIF manifest fetching works: paste URL, get canvases + metadata
- OpenSeadragon viewer renders IIIF images on audience, judge, and controller
- Canvas navigation works from controller (prev/next, keyboard arrows)
- Text reveal works with paragraph chunking
- Items without manifests fall back to text-only display
- Mobile: iOS audio unlock, responsive layouts all functional
- Visual style: SpecIdol's neon retro game-show aesthetic throughout (no Soviet palette)
