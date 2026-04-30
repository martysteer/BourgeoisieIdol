# IIIF Viewer Integration Design

**Date:** 2026-04-30
**Status:** Draft

## Summary

Replace static `<img>` display with OpenSeadragon viewer across all three views (audience, judge, controller). Adds deep zoom and multi-canvas navigation to IIIF-sourced items. Canvas navigation is controller-driven and synced to all clients.

## Goals

Two capabilities the current `<img>` display lacks:

1. **Deep zoom** — high-res images with pan/zoom into details
2. **Multi-canvas navigation** — browse through multiple canvases in a IIIF manifest (pages, views, etc.)

## Design Decisions

### Viewer Choice: OpenSeadragon

**Chosen:** OpenSeadragon — pure JS, zero dependencies, single vendored file (~100KB).

**Alternatives considered:**

| Viewer | Pros | Cons | Why rejected |
|--------|------|------|--------------|
| **OpenSeadragon** | Pure JS, zero deps, gold standard for deep zoom, IIIF Image API native | Multi-canvas UI needs custom buttons | Best fit for no-framework stack |
| **Tify** | Slim, fast, built-in multi-canvas nav | Requires Vue.js dependency | Framework dependency violates project constraints |
| **Universal Viewer** | Full-featured, zoom + multi-canvas out of box | Heavy, many dependencies | Too heavy, too many deps |
| **Diva.js** | Document-optimized, page nav built in | Moderate weight | Heavier than needed |

OpenSeadragon wins: purest fit for vanilla JS / no-build-step / no-framework stack. Multi-canvas nav is just a few buttons wired to canvas switching — trivial custom UI.

### Viewer Placement: All Three Views

**Chosen:** Replace `<img>` tag with OpenSeadragon in audience, judge, and controller views.

**Alternatives considered:**
- **Audience only** (judges keep simple `<img>`) — rejected for inconsistency
- **Expandable overlay** (click image to open viewer in modal/fullscreen) — rejected, adds complexity
- **Separate viewer page** (link out to dedicated URL) — rejected, breaks flow

Consistency across all views won. Same viewer everywhere, sized appropriately per view.

### Canvas Navigation: Controller-Driven

**Chosen:** Controller has prev/next canvas buttons, broadcasts canvas changes to all clients. Same pattern as existing `text_advance`.

**Alternatives considered:**
- **Free browsing** (each view navigates independently, no sync) — rejected, breaks shared experience
- **Hybrid** (controller can advance, but audience/judges can also browse freely) — rejected, adds complexity and potential confusion

Controller-driven matches existing architecture. All synchronized state changes flow through controller → server → all clients.

### Canvas vs Text: Independent Controls

**Chosen:** Controller has separate buttons for "next canvas" and "next paragraph". Canvas and text are independent streams the controller can trigger in any order.

**Alternatives considered:**
- **Canvas per paragraph** (advancing text also advances canvas) — rejected, too rigid, assumes 1:1 mapping
- **Canvas first, then paragraphs** (show all canvases, then reveal text) — rejected, too rigid, assumes fixed ordering

Independent controls give controller full flexibility. Some items may have many canvases and little text, or vice versa. No assumptions about relationship between images and text.

### Image Mode: Dual with Fallback (Approach B)

**Chosen:** Always use OpenSeadragon. When manifest provides IIIF Image API service endpoint → tiled deep zoom. When only static image URL available → OpenSeadragon simple image mode (still pan/zoom, loads full image).

**Alternatives considered:**
- **Approach A: IIIF Image API only** — OSD only uses tiled mode. Static images fall back to simple image mode but without explicit design for it. Risk of inconsistent behavior.
- **Approach C: Minimal** — keep `<img>` as default, only use OSD when IIIF Image API detected. Smallest change but inconsistent UX — sometimes viewer, sometimes static image, users won't understand why.

Approach B gives consistent UX regardless of image source. One viewer, always zoomable, graceful degradation for non-tiled images.

### Canvas Controls: Disabled Not Hidden

**Chosen:** Canvas navigation buttons always visible in controller, disabled when not applicable (0 or 1 canvases, or at bounds).

**Alternative:** Hide buttons when not needed — rejected, causes layout shift.

### Backward Compatibility: None

This is a brand new prototype. No migration of old import/export formats. `canvases` array is the only format.

## Data Model Changes

### Canvas Structure

`extract_image_url()` replaced by `extract_canvas_info()`. Returns list:

```python
[
    {
        "label": "Canvas 1",          # from canvas label (nullable)
        "image_url": "https://...",   # static image URL
        "service_url": "https://..."  # IIIF Image API base URL (nullable)
    },
    ...
]
```

`service_url` extracted from IIIF `service` property on image resources:
- v2: `@id` on service object
- v3: `id` on service object

### Item Data Model

```
title:        string
text:         string
manifest_url: string (nullable)
canvases:     list (can be empty)
```

Legacy `image_url` field on items removed. Image data lives in `canvases` array.

### Server State

`current_round` gains:
- `canvases`: list from item
- `canvas_index`: integer, starts at 0

## WebSocket Messages

### New: `canvas_advance`

Controller-only command. Added to `CONTROLLER_ONLY` set.

```
Controller sends:  {type: "canvas_advance", data: {direction: "next"|"prev"}}
Server broadcasts: {type: "canvas_advanced", data: {canvas_index: N, canvas: {label, image_url, service_url}}}
```

Server increments/decrements `canvas_index`, clamps to 0..len-1. No wrap, no goto. Server ignores `canvas_advance` if item has no canvases.

### Modified: `round_started`

Broadcast adds:
- `canvases`: full canvas list
- `canvas_index`: 0

Removes: `image_url`, `manifest_url` (data now in canvases)

### Modified: `round_reset`

Resets `canvas_index` to 0.

### Modified: `fetch_manifest`

Response changes from `{image_url, error}` to `{canvases, error}`.

### Modified: `add_item`

Accepts `canvases` list instead of `image_url`.

### Controller manifest fetch flow

1. Controller enters manifest URL, clicks "Fetch Manifest"
2. Server fetches manifest, runs `extract_canvas_info()`, returns `{canvases, error}`
3. Controller stores canvases in form state
4. On "Add Item" submit, controller sends `add_item` with `{title, text, manifest_url, canvases}`

## OpenSeadragon Integration

### Vendored File

`www/openseadragon.min.js` — single file, checked into repo.

### Initialization

Replace `<img>` with `<div id="osdViewer">` in all three views.

On `round_started`:
- If canvases non-empty → initialize OSD with first canvas tile source
- If canvases empty → hide viewer container, text-only round

Tile source selection per canvas:
- `service_url` present → pass `service_url + '/info.json'` directly (OSD auto-detects IIIF Image API, enables tiled deep zoom)
- `image_url` only → `{type: 'image', url: image_url}` (simple pan/zoom)

On `canvas_advanced` → `viewer.open(newTileSource)`.

On `round_reset` → destroy viewer, hide container.

### Viewer Config

```javascript
{
    showNavigator: false,
    showNavigationControl: true,
    gestureSettingsMouse: {scrollToZoom: true}
}
```

Respect `prefers-reduced-motion` — disable OSD animations when active.

## View-Specific Details

### Audience View

- Viewer fills item content area, mobile responsive (no fixed max-width)
- Canvas label shown above viewer when provided
- No canvas navigation controls — controller drives all canvas changes
- `geometric-frame` container retained
- OSD zoom/pan controls available locally (built-in toolbar)

### Judge View

- Max-width 300px maintained (mobile-optimized)
- Same message handlers as audience
- No canvas navigation controls — controller drives all canvas changes
- OSD zoom/pan controls available locally

### Controller View

- Small OSD preview in round info area, syncs with same `canvas_advanced` messages
- Canvas navigation controls in round controls area (near existing text advance button):
  - "Prev Canvas" and "Next Canvas" buttons
  - Canvas indicator: "Canvas 2 / 5"
  - Buttons disabled at bounds (prev disabled on first canvas, next disabled on last)
  - Buttons disabled when item has 0 or 1 canvases
- Controls always visible, disabled when not applicable (layout stability)
- Item queue display shows canvas count: `🖼️ 5` instead of just `🖼️`

### All Views — Graceful States

- Item has canvases → show viewer
- Item has no canvases → hide viewer container, text-only round works as before

## Import/Export

No backward compatibility. Prototype only.

- Export: items include `canvases` array
- Import: expects `canvases` array

## Files Changed

| File | Changes |
|------|---------|
| `server/relay.py` | `extract_canvas_info()`, canvas state, `canvas_advance` handler, modified item/round handlers |
| `www/app.js` | `canvasAdvance()` method, updated `addItem()` |
| `www/audience.html` | OSD viewer init, `canvas_advanced` handler, responsive sizing |
| `www/judge.html` | OSD viewer init, `canvas_advanced` handler |
| `www/control.html` | OSD viewer init, canvas nav buttons, updated item form |
| `www/openseadragon.min.js` | New vendored file |
