# Controller Redesign Plan

## Status: COMPLETE

## Changes

### 1. Story Queue + History → disclosure triangles

Both sections become collapsible like Story Management / Session Management:
- Wrap in `.section.collapsed` div with `onclick` toggle
- Arrow `▼` that rotates `-90deg` when collapsed
- `.management-content` hidden when collapsed
- Story Queue starts expanded, History starts collapsed

### 2. Tight borders between sections

All collapsible sections share `border-top: 2px solid #0f0`. No `border-bottom` — each section's top border acts as separator from the one above. Session Management keeps red borders. Remove `.section` class `border-bottom` and `margin-bottom`. Stack sections flush.

### 3. Remove bottom border from h2 titles

The global `h2` style has `border-bottom: 2px solid #0f0`. Remove it (set `border: none` on collapsible h2s — already done for Story Management pattern, apply to all).

### 4. Story Queue redesign

- Remove story summary text (the `substring(0,80)` preview)
- Keep title + remove button only
- Simpler items: no border box, just bottom divider line

### 5. History list redesign

- Simpler items: no border box, just text with bottom divider
- Format: "Title — OUTCOME (duration, N buzzes)"
- No `.history-item` border

### 6. Selected story display → two-column layout

- Drop the title from this section (already in header-context)
- Drop the "NOW PERFORMING" label
- Left column (1/3): controls (Start/Advance/Reset buttons, status, text progress)
- Right column (2/3): story text display that mirrors audience view
  - `story-text-container` with scrollable text
  - Lines appear as controller advances text (listen to `text_advanced` events)
  - Same `.text-line` animation as audience
- On reset/new round: clear text display

### 7. Remove "Open Audience View" button from header

Delete the button from `.header-info`. The story text is now visible directly in the controller.

## Files Modified

| File | Changes |
|------|---------|
| `www/control.html` | All changes above — CSS, HTML structure, JS functions |
