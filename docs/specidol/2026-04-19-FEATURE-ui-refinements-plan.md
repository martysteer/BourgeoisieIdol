# UI Refinements Plan

## Status: COMPLETE ✓

All changes implemented and committed.

Additional features added:
- Session list buttons (replace code input)
- Multiple concurrent sessions support

## Changes

### 1. Auto-assign Judge IDs
- Remove judge dropdown requirement
- Server auto-assigns next available judge ID incrementally
- Supports >3 judges
- Judge URL: `?code=XXXX` (no judge param needed)

**Files:**
- `server/relay.py`: Add next_judge_id tracking, auto-assign on join
- `www/judge.html`: Remove judge param requirement

### 2. Judge Screen Updates
- Text changes: "session code:" and "you are judge XXX" (lowercase)
- Move timer to bottom left position (match audience layout)

**Files:**
- `www/judge.html`: Update header text, reposition timer

### 3. Audience Dynamic Judge Panels
- Dynamically create judge panels based on connected judges
- Update as judges join/disconnect

**Files:**
- `www/audience.html`: Generate panels from session state

### 4. Controller Layout Redesign
- Two 50% columns
- Left: "Add Story" (collapsible) + Import/Export
- Right: "Story Queue"
- Disclosure arrow on Add Story
- When collapsed: Queue 90%, Add Story vertical slice

**Files:**
- `www/control.html`: Restructure layout, add disclosure behavior

### 5. Controller Story Row
- Entire row clickable for selection (not just button)

**Files:**
- `www/control.html`: onclick on row instead of button

## Implementation Order
1. Server judge auto-assignment
2. Judge screen updates
3. Audience dynamic panels
4. Controller layout + interactions
