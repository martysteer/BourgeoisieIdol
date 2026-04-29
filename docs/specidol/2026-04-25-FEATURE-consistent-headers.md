# Consistent Headers & Full-width Lines

**Date:** 2026-04-25
**Status:** Complete

## Changes

### 1. Full-width Horizontal Lines

Replaced box borders (all four sides) with top/bottom-only horizontal rules across all content sections, matching the judge screen's clean `border-top`/`border-bottom` pattern.

| Element | Before | After |
|---------|--------|-------|
| `audience.html` `.story-text-container` | `border: 2px solid #0f0` | `border-bottom: 2px solid #0f0` (top removed — sits below header border) |
| `control.html` `.selected-story-display` | `border: 3px solid #ff0` | `border-top/bottom: 3px solid #ff0` |
| `control.html` `.section` | `border: 1px solid #0f0` | `border-top/bottom: 2px solid #0f0` |
| `control.html` `.story-management` | `border: 1px solid #0f0` | `border-top/bottom: 2px solid #0f0` |
| `control.html` `.session-management` | `border: 2px solid #f00` | `border-top/bottom: 2px solid #f00` |

### 2. Consistent Header Layout

All three session pages (judge, audience, controller) share the same header pattern:

```
┌──────────────────────────────────────────────┐
│ PAGE LABEL (green)     CONTEXTUAL INFO (yellow)│
│ stats / session info                           │
├──────────────────────────────────────────────┤
```

**Left side** — `.header-left` column:
- `.page-label`: Page role in green Press Start 2P ("WATCHING", "JUDGING", "CONTROLLING")
- `.header-info`: Session stats (code, stories, judges, audience count)

**Right side** — `.header-context`:
- Big yellow text showing the main contextual info for each page
- `.waiting` state: muted `#997700`, no glow (before data arrives)
- Active state: bright `#ff0` with text-shadow glow

| Page | Label | Context (right side) |
|------|-------|---------------------|
| Audience | WATCHING | Story title (or "Waiting for story...") |
| Judge | JUDGING | Judge name (clickable to edit) |
| Controller | CONTROLLING | Selected story title (or "No story selected") |

Mobile (≤900px): header stacks vertically, context text left-aligned.

### 3. Live Session Stats

Judge and audience pages now display live session stats (code, story count, judge count, audience count) via WebSocket event listeners:
- `session_state`: initial population
- `audience_joined`/`audience_left`: audience count
- `story_added`/`story_removed`: story count
- `judge_joined`/`judge_left`: judge count (audience page)

### 4. Controller Style Alignment

Refactored controller CSS to align with other pages:
- Removed `padding: 2rem` from `.page-scrollable` body class — section borders now go edge-to-edge
- All sections use `padding: 1rem 2rem` (horizontal matches header)
- Footer padding zeroed so session-management borders touch edges
- Removed redundant form element overrides — core `style.css` handles inputs/buttons
- Controller buttons override to ghost style only (`black bg, green text`)
- Scoped `.management-content` declarations to parent selectors

## Shared CSS Classes (in style.css)

```css
.header-left    /* flex column for label + stats */
.page-label     /* green Press Start 2P, body size, with glow */
.header-info    /* monospace, caption size, 0.7 opacity */
.header-context /* yellow Press Start 2P, heading size, with glow */
.header-context.waiting  /* muted #997700, no glow */
```

## Files Modified

| File | Changes |
|------|---------|
| `www/style.css` | `.page-header` flex layout, `.header-left`, `.page-label`, `.header-context`, `.page-scrollable` no padding, mobile stacking |
| `www/control.html` | Header restructured, section borders → top/bottom, redundant CSS removed, footer padding zeroed |
| `www/judge.html` | Header restructured, old CSS removed, stats + audience/story listeners added |
| `www/audience.html` | Header restructured, story title → header context, stats listeners, `.story-text-container` border-top removed |
