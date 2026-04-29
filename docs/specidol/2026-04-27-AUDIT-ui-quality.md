# UI Audit: SPECULATIVE IDOL

## Anti-Patterns Verdict: PASS

Intentional retro terminal/arcade aesthetic. No AI-slop indicators. Constrained palette, consistent theming, handcrafted personality.

## Executive Summary

Solid foundation with strong thematic identity. Primary concerns: accessibility gaps (contrast ratios, missing ARIA, no focus management), inline styles obstructing maintainability, missing responsive breakpoint on controller two-column layout, and no keyboard shortcut for the critical Advance Text action. Server has minor input validation gaps.

---

## Critical

### C1. No ARIA roles or live regions anywhere
- **Files**: All HTML pages
- **What**: No `role`, `aria-label`, `aria-live`, or `aria-pressed` attributes. Judge buzz button has no accessible label. Buzz count changes silently. Round start/end outcomes invisible to screen readers.
- **Impact**: Entire app unusable with assistive technology.
- **Fix**: Add `aria-live="polite"` to status/buzz-count regions. Add `aria-label` to buzz button. Add `role="status"` to timer. Add `role="alert"` to outcome display.

### C2. Contrast ratio failures on disabled elements
- **Files**: `style.css:77`, all pages
- **What**: `button:disabled { opacity: 0.3 }` — green text at 0.3 opacity on black = ~1.3:1 contrast. WCAG AA requires 4.5:1.
- **Impact**: Disabled buttons invisible to low-vision users.
- **Fix**: Use `opacity: 0.5` minimum, or switch to explicit dim color (`#060`) instead of opacity.

### C3. `.header-context.waiting` color fails contrast
- **Files**: `style.css:150-152`
- **What**: `color: #997700` on `#000` background = ~4.0:1. Below WCAG AA (4.5:1 for normal text).
- **Fix**: Lighten to `#aa8800` (~5.0:1) or `#bb9900`.

---

## High

### H1. No keyboard shortcut for Advance Text
- **Files**: `control.html:359`
- **What**: During live performance, controller clicks "Advance Text" button repeatedly. No keyboard binding.
- **Impact**: Clunky live operation. Keyboard-only users blocked.
- **Fix**: Bind spacebar or right arrow to `advanceText()` when round running. One `keydown` listener, gated on round status.

### H2. Advance Text button uses inline styles
- **Files**: `control.html:359`
- **What**: `style="background: #ff0; color: #000; border-color: #ff0;"` — can't be overridden for state changes via CSS classes, breaks consistency.
- **Fix**: Extract to `.btn-advance` class.

### H3. `textProgress` div uses inline styles
- **Files**: `control.html:362`
- **What**: `style="font-family: 'Courier New', monospace; font-size: var(--text-caption); opacity: 0.7;"` — same issue.
- **Fix**: Extract to `.text-progress` class.

### H4. Controller two-column layout has no responsive breakpoint
- **Files**: `control.html:93-115`
- **What**: `.selected-story-display` is `display: flex` with 33%/67% columns. No `@media` breakpoint. Press Start 2P at `--text-body` in 33% width on mobile won't fit.
- **Fix**: Add `@media (max-width: 900px)` to stack columns vertically.

### H5. No pause/resume button on controller
- **Files**: `control.html:356-361`
- **What**: Server supports `pause`/`resume` messages. Controller has no button for them.
- **Impact**: Controller can't pause for technical issues or judge questions during live performance.
- **Fix**: Add Pause/Resume toggle in controls area.

### H6. Focus trap missing in modals
- **Files**: `modal.js`, `judge.html:140-151`
- **What**: Modals show via `.active` class but don't trap focus. Tab key moves to elements behind modal overlay.
- **Fix**: On modal open, focus first button. On Tab from last element, wrap to first. On Shift+Tab from first, wrap to last.

---

## Medium

### M1. Story text column empty state is weak
- **Files**: `control.html:365-368`
- **What**: Italic gray placeholder text in 67% of the UI. Dead space when no round running.
- **Fix**: Show full story text as dimmed preview when story selected but round not started. Clear and switch to line-by-line on round start.

### M2. `story_added` broadcast missing `story_count`
- **Files**: `relay.py:175-178`
- **What**: `story_added` event data contains `index` and `title` but no `story_count`. Judge/audience handlers (`judge.html:338`, `audience.html:275`) read `data.story_count` — gets `undefined`, displayed as empty string.
- **Fix**: Add `"story_count": len(session["stories"])` to broadcast data. Same for `story_removed` at line 184.

### M3. `updateStory()` only updates client state, never sends to server
- **Files**: `control.html:774-793`
- **What**: Editing a story modifies `sessionState.stories[i]` locally but never calls `client.send()`. Other clients and server keep old text. Next `session_state` sync or page reload reverts edits.
- **Fix**: Add `update_story` message type to server, or remove/re-add story on edit.

### M4. CRT scanline overlay blocks pointer events on z-index edge cases
- **Files**: `audience.html:19-35`
- **What**: `body::before` has `z-index: 1000` and `pointer-events: none`. Currently safe, but any future element above z-index 1000 (modal is 9999, fine) could interact oddly. The scanline covers the entire viewport permanently.
- **Impact**: Performance cost of rendering full-viewport pseudo-element with repeating gradient.
- **Note**: Low risk currently, but worth documenting.

### M5. `AudioContext` created eagerly on audience page
- **Files**: `audience.html:378`
- **What**: `new AudioContext()` runs on page load before user gesture. Chrome/Safari may suspend it and log console warnings.
- **Fix**: Already mitigated by `audioContext.resume()` in `enableAudio()` overlay click. Acceptable pattern, but creating context lazily on first click would be cleaner.

### M6. Copy JSON button inside `<h2>` is semantically odd
- **Files**: `control.html:417`
- **What**: `<button>` nested inside `<h2>` heading. Screen readers announce heading content including button text.
- **Fix**: Move button to `.section-content` or place outside `<h2>` but visually adjacent.

### M7. No server-side rate limiting on messages
- **Files**: `relay.py:62-65`
- **What**: Any client can flood `text_advance`, `buzz`, etc. No throttle. Single malicious client can spam broadcasts to all connected clients.
- **Fix**: Add per-client rate limit (e.g., max 10 msg/sec). Drop excess messages silently.

### M8. Session code injection in index.html `renderSessions()`
- **Files**: `index.html:198-205`
- **What**: `session.code` inserted directly into HTML template string and `onclick="selectSession('${session.code}')"`. Code is server-generated (4 uppercase letters), so safe in practice, but pattern is XSS-prone if code format ever changes.
- **Fix**: Use `escapeHtml()` (available in control.html but not in index.html) or build elements with DOM API.

---

## Low

### L1. `.page-footer` border-top stacks with session-management border
- **Files**: `style.css:162`, `control.html:57`
- **What**: `.page-footer` has `border-top: 2px solid var(--neon-green)`. Controller footer contains `.session-management` which has `border-top-color: #f00`. Double border when session management is first child.
- **Fix**: Remove `border-top` from `.page-footer` in controller local styles, or set `padding: 0; border: none` on controller's `.page-footer`.

### L2. Audience page `paused`/`resumed` handlers missing
- **Files**: `audience.html`
- **What**: No `client.on('paused')` or `client.on('resumed')` handlers. If controller pauses during a round, audience timer keeps running (no timer shown, so invisible) and auto-scroller isn't paused.
- **Impact**: Minimal since audience timer was removed. But `scroller` reference exists and could be active if re-enabled.
- **Note**: Actually, `scroller` is declared but never `start()`ed in current code — dead code from earlier auto-scroll feature. Harmless.

### L3. `cancelEditBtn` has inline styles
- **Files**: `control.html:400`
- **What**: `style="display: none; margin-left: 0.5rem; background: #800; color: #f00; border-color: #f00;"` — should be CSS class.

### L4. History item outcome class not escaped
- **Files**: `control.html:642`
- **What**: `class="history-item ${entry.outcome}"` — outcome comes from server (`"victory"` or `"defeat"`). Safe in practice but pattern doesn't validate.

### L5. `joinControllerBtn` inline styles on index.html
- **Files**: `index.html:146`
- **What**: `style="background: #440; color: #ff0; border-color: #ff0; margin-top: 1rem;"` — should be a CSS class.

### L6. Dead `scroller` variable in audience.html
- **Files**: `audience.html:162`
- **What**: `let scroller = null;` declared, referenced in `session_state` handler (`scroller.pause()`, `scroller.stop()`) but never instantiated. All paths guarded by `if (scroller)` so no crash, but dead code.

### L7. WebSocket reconnect doesn't re-join session
- **Files**: `app.js:66-74`
- **What**: On disconnect, client reconnects after 2s but only calls `this.onConnect()`. Each page's `onConnect` calls `joinSession()` which works. But if the server restarted, the session is gone — client silently reconnects to a server that doesn't know its session.
- **Fix**: Handle `error` response from `join` message with redirect to index.

### L8. No `<label>` associations on index.html inputs
- **Files**: `index.html`
- **What**: Session code input field has no associated `<label>`. (Actually no input on index.html currently — session buttons replaced text input. Moot.)

---

## Patterns & Systemic Issues

### Inline styles pervasive
17+ elements use inline `style=""` attributes across controller, index, and audience pages. Makes state-based styling impossible via CSS, hurts maintainability, and prevents clean overrides.

### Color tokens underused
`style.css` defines `--neon-green`, `--neon-yellow`, `--neon-red`, `--black` but pages frequently hard-code `#0f0`, `#ff0`, `#f00`, `#000`. Token usage is ~40%. Switching themes or adjusting colors requires find-replace across all files.

### No shared `renderJudgePanels()`
Judge and audience have identical `renderJudgePanels()` implementations. Both build the same HTML, preserve buzzed state the same way, use `calculateInitials()`. Candidate for shared function in `app.js`.

### `innerHTML` for dynamic rendering
All dynamic lists (story queue, history, judge panels, sessions) use `innerHTML` with template strings. Works but: no event delegation (inline `onclick`), XSS surface if data escaping missed, DOM thrash on re-render. Not critical for this app's scale.

---

## Positive Findings

1. **Font loading strategy** — `media="print" onload="this.media='all'"` with `<noscript>` fallback. Best practice for non-blocking web font loading.
2. **`prefers-reduced-motion` respected** — Global media query disables all animations. Excellent accessibility practice.
3. **`escapeHtml()` in controller** — Story titles properly escaped in `renderStoryQueue()` and `renderHistory()`. XSS protection where it matters most (user-supplied story text).
4. **Clock synchronization** — `updateClockOffset()` / `serverToLocal()` pattern handles client-server time drift for accurate timer display.
5. **Buzz authentication** — Server verifies `judge_id` matches websocket's registered identity before accepting buzz. Prevents spoofing.
6. **Controller-only action gating** — `CONTROLLER_ONLY` set in server ensures only controllers can modify rounds/stories.
7. **Reconnect with backoff** — Client auto-reconnects up to 5 times with 2s delay.
8. **Judge name persistence** — localStorage with 2hr TTL is a thoughtful UX touch.
9. **Buzzed state preservation** — `buzzedIds` Set pattern in `renderJudgePanels()` survives re-renders from judge join/leave/name-change.
10. **Modal system** — Promise-based `customConfirm()`/`customAlert()` replaces browser dialogs cleanly. Keyboard support (Escape to cancel/dismiss).

---

## Recommendations by Priority

### Immediate (before next live use)
1. Add keyboard shortcut for Advance Text (H1)
2. Add Pause/Resume button to controller (H5)
3. Fix `story_added`/`story_removed` missing `story_count` in server broadcasts (M2)
4. Fix `updateStory()` not syncing to server (M3)

### Next sprint
5. Extract inline styles to CSS classes (H2, H3, L3, L5)
6. Add responsive breakpoint for controller two-column layout (H4)
7. Add focus trap to modals (H6)
8. Add `aria-live` regions for status/buzz-count/timer (C1)
9. Fix contrast on disabled buttons and `.waiting` text (C2, C3)

### Backlog
10. Consolidate `renderJudgePanels()` into shared `app.js`
11. Replace hard-coded hex with CSS custom properties
12. Add server-side rate limiting (M7)
13. Clean up dead `scroller` code in audience.html (L6)
14. Handle reconnect to dead session gracefully (L7)
