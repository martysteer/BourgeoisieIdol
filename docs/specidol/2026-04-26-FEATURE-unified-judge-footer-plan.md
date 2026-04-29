# Unified Judge Panel Footer

## Status: COMPLETE

Both judge and audience pages now share identical footer layout with judge initials.

## Layout

### Footer (both pages)

```
────────────────────────────────────────── (green border-top)
 │AS│BJ│CK│          │DL│EF│
  green/unbuzzed       red/buzzed (right)
```

- Judge cells with left/right borders only (horizontal ladder pattern)
- Adjacent borders collapse via negative margin
- Green text + green borders for unbuzzed, red for buzzed
- `overflow-x: auto` for horizontal scroll with many judges
- CSS `order` pushes buzzed cells right: `order: 0` unbuzzed, `order: 1` buzzed

### Judge page content area (during round)

```
        [BUZZ BUTTON]
      2 of 5 buzzed
         1:23.4
─────────────────────── (footer)
 │AS│BJ│    │CK│DL│
```

Timer + buzz-count moved from old footer into content area below buzz button.

### Audience page footer

Timer removed entirely. Just judge cell panels.

## Changes

### `www/style.css`
- `.page-footer`: `border-top: 2px solid var(--neon-green)`, compact padding
- `.judge-panels`: flex row, `overflow-x: auto`
- `.judge-cell`: green text, left/right borders, `order: 0`, negative margin to collapse adjacent borders
- `.judge-cell:first-child`: no negative margin
- `.judge-cell.buzzed`: red text, red borders, `order: 1`

### `www/judge.html`
- Footer: timer replaced with `#judgePanels` container
- Content: timer + buzz-count created inside `startRound()` below buzz button
- Scoped `.buzzed` CSS to `.buzz-button .buzzed` (prevents bleeding into judge cells)
- Removed `.judge-indicators`, `.judge-indicator`, `@keyframes buzzPulse`
- JS: `renderJudgeStatus()` renamed to `renderJudgePanels()`, targets `.judge-cell`
- `renderJudgePanels()` called from `session_state`, `judge_joined`, `judge_left`, `judge_name_changed`

### `www/audience.html`
- Footer: timer removed entirely
- Removed `.judge-panel`, `.judge-panel.buzzed`, `.x`, `@keyframes xSlam`, `.judge-panel.buzzed .label`
- Removed local `.page-footer` override
- Removed responsive `.judge-panel` media query
- `renderJudgePanels()` simplified to `.judge-cell` divs (no X overlay)
- `markJudgeBuzzed()` and `resetView()` target `.judge-cell`

## Verification

- Both footers identical: green border-top, horizontal ladder of bordered cells
- Horizontal scroll when many judges connected
- Buzzed judges move right (CSS order), turn red with red borders
- Non-buzzed judges stay left/visible in green
- Judge page: timer + buzz-count visible in content during round
- Audience page: no timer anywhere
- Judge joins/leaves/name changes re-render correctly, preserving buzz state
- Buzz button X animation still fires (scoped to `.buzz-button .buzzed`)
