# Judge Customization Design

**Date:** 2026-04-25
**Status:** Approved

## Overview

Allow judges to set custom names that persist across page refreshes and display as initials on audience and judge screens.

## Requirements

1. **Custom names:** Judges can set their own name via modal dialog
2. **Persistence:** Names stored server-side (session scope) and client-side (localStorage, 2hr expiry)
3. **Refresh behavior:** Page refresh assigns new judge slot, but name carries over from localStorage
4. **Display:** Show initials with collision numbering across all views
5. **Privacy:** localStorage expires after 2 hours

## Data Model

### Server (relay.py)

**Modified judge slots:**
```python
session["judge_slots"] = {
    1: {"websocket": ws, "name": "Alice Smith"},
    2: {"websocket": ws, "name": "Judge 2"},  # default
}
```

**Default name:** `f"Judge {judge_id}"` when slot created

### Client (localStorage)

**Storage format:**
```javascript
{
  "name": "Alice Smith",
  "timestamp": 1714089600000
}
```

**Key:** `specidol_judge_name`
**Expiry:** 2 hours (7200000ms)
**Privacy:** Auto-cleared on expiry

## WebSocket Protocol

### Modified Messages

**`join` (client → server):**
```json
{
  "type": "join",
  "data": {
    "code": "ABCD",
    "role": "judge",
    "name": "Alice Smith"  // optional, from localStorage
  }
}
```

**`session_state` (server → client):**
```json
{
  "type": "session_state",
  "data": {
    "connected_judges": [
      {"id": 1, "name": "Alice Smith"},
      {"id": 2, "name": "Judge 2"}
    ],
    ...
  }
}
```

**`judge_joined` / `judge_left` (server → all):**
```json
{
  "type": "judge_joined",
  "data": {
    "judge_id": 1,
    "connected_judges": [{"id": 1, "name": "Alice Smith"}, ...]
  }
}
```

### New Messages

**`set_judge_name` (client → server):**
```json
{
  "type": "set_judge_name",
  "data": {
    "name": "Alice Smith"  // max 20 chars
  }
}
```

**`judge_name_changed` (server → all):**
```json
{
  "type": "judge_name_changed",
  "data": {
    "judge_id": 1,
    "name": "New Name"
  }
}
```

## UI/UX

### Judge View (judge.html)

**Header:**
- Display: `"You are judge 'Alice Smith'"`
- Default: `"You are judge 'Judge 2'"`
- Clickable to open name editor modal

**Name Editor Modal:**
- Title: **"Who do you think you are?"**
- Input field (max 20 characters)
- Pre-filled with current name
- Save button

**Judge Indicators:**
- Below buzz button
- Show all judges as initials (same format as audience)
- Include yourself in list

### Audience View (audience.html)

**Judge Panels:**
- Remove "JUDGE" label
- Display just initials: `"AS"`, `"BJ2"`, etc.
- Same collision numbering as judge view

## Initials Algorithm

**Function:** `calculateInitials(judges)` → returns `{judge_id: "AS2"}`

**Steps:**

1. **Extract initials:** First letter of each word, uppercase
   - `"Alice Smith"` → `"AS"`
   - `"bob jones"` → `"BJ"`
   - `"Judge 2"` → `"J2"`

2. **Group by initials:** Detect collisions
   ```javascript
   {
     "AS": [1, 3, 5],
     "BJ": [2]
   }
   ```

3. **Number collisions:** First occurrence no number, subsequent get 2, 3, 4...
   - Judge 1: `"AS"`
   - Judge 3: `"AS2"`
   - Judge 5: `"AS3"`

4. **Return map:** `{1: "AS", 2: "BJ", 3: "AS2", 5: "AS3"}`

**Example:**
```javascript
judges = [
  {id: 1, name: "Alice Smith"},
  {id: 2, name: "Bob Jones"},
  {id: 3, name: "Alice Sanders"}
]
// Output: {1: "AS", 2: "BJ", 3: "AS2"}
```

## Implementation Notes

### Server Changes (relay.py)

1. Modify `judge_slots` structure to store `{websocket, name}` dict
2. Update `create_new_session()` to use new structure
3. Modify `join` handler to accept optional `name` in data
4. Add `set_judge_name` handler
5. Update all broadcasts to include judge names
6. Fix websocket cleanup to handle new structure

### Client Changes (judge.html)

1. Add localStorage get/set with expiry check
2. Send name in `join` message if available
3. Add click handler to header text (and style it slightly similar to the other clickable buttons)
4. Add modal HTML/CSS for name editor
5. Add `set_judge_name` send on save
6. Add `judge_name_changed` handler
7. Add initials calculation function
8. Render judge indicators below button

### Client Changes (audience.html)

1. Update `renderJudgePanels()` to use initials
2. Add initials calculation function (shared logic)
3. Add `judge_name_changed` handler
4. Update CSS for new panel format

## Edge Cases

1. **Expired localStorage:** Clear and use default "Judge X"
2. **Empty name input:** Reject, keep current name
3. **Name > 20 chars:** Truncate or reject in UI (limit typing)
4. **All same initials:** Number all after first (AS, AS2, AS3, AS4...)
5. **Special characters in name:** Allow, extract letters only for initials
6. **Single-word name:** Use first letter only (e.g., "Alice" → "A")
7. **Session deleted:** localStorage persists but won't apply (different session)

## Testing Checklist

- [ ] Judge sets name, refreshes → name persists
- [ ] Judge sets name, other judges see initials update
- [ ] Audience view shows initials in real-time
- [ ] Collision numbering works (AS, AS2, AS3)
- [ ] localStorage expires after 2 hours
- [ ] Default "Judge X" works when no localStorage
- [ ] Modal opens/closes correctly
- [ ] 20-char limit enforced
- [ ] Name displays correctly in all views
- [ ] Judge leaves → initials update everywhere
