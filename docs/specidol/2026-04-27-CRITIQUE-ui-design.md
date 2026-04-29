# Design Critique: SPECULATIVE IDOL

## Anti-Patterns Verdict: PASS

Not AI slop. This is a deliberate retro terminal/arcade aesthetic — black background, neon green monochrome, Press Start 2P pixel font, CRT scanlines on audience view. The design language is *intentional* and *thematic*: a literary performance game show styled like an 80s arcade cabinet. No gradients-on-cards, no glassmorphism, no Tailwind-template smell. The color palette (green/yellow/red on black) is constrained and meaningful. This looks handcrafted with personality.

## Overall Impression

Strong thematic identity. The arcade/terminal vibe works perfectly for a competitive performance game. The judge buzz button is visceral and fun. The new controller two-column layout is a big upgrade — seeing text live while controlling is the right call.

**Single biggest opportunity:** The controller is information-dense but lacks *state awareness*. It looks the same whether idle, mid-round, or post-round. The primary action area (controls column) should dramatically shift appearance based on round state.

## What's Working

1. **Judge page is perfect.** Giant red buzz button, centered, nothing else competing. Timer + buzz count below. Footer shows who's buzzed. Zero learning curve — a judge opens this and knows exactly what to do.

2. **Color-as-meaning is consistent.** Green = safe/active, yellow = selected/highlighted, red = danger/buzzed. This holds across all four pages. The judge footer red/green reordering is clever UX — non-buzzed judges stay visible on the left.

3. **Collapsible section hierarchy.** The controller now has clear primary/secondary/tertiary zones. The yellow-bordered control area sits above green-bordered collapsibles. Visual weight matches importance.

## Priority Issues

### 1. Controller controls column has no state differentiation
- **What**: "Status: Waiting", "Status: running", "Status: ended" is just text. The controls column looks identical in every state.
- **Why**: During a live round, the controller is under time pressure. They need to instantly see "round is live, advance is the thing to press." Currently three buttons sit there equally regardless of state.
- **Fix**: When round is running, make the Advance Text button larger/dominant. When waiting, make Start Round dominant. When ended, show outcome prominently. Consider dimming or hiding irrelevant buttons rather than just disabling them.

### 2. No pause/resume button on controller
- **What**: Server supports pause/resume. Controller has no button for it.
- **Why**: During a live performance, the controller may need to pause (technical issue, judge question). Having to rely on server-side or missing this entirely breaks the live show flow.
- **Fix**: Add Pause/Resume toggle button next to Advance Text, styled distinctly (maybe yellow outline to match the control area theme).

### 3. Story text column empty state is weak
- **What**: "Story text appears here during round..." is just italic gray text in a big empty space.
- **Why**: 2/3 of the primary UI is dead space most of the time. When no round is running, this area does nothing.
- **Fix**: When a story is selected but round hasn't started, show the full story text as a preview (dimmed). This lets the controller review what they're about to perform. Clear it and switch to line-by-line mode when round starts.

### 4. Controller mobile breakpoint missing for two-column layout
- **What**: `.selected-story-display` is `display: flex` with 33%/67% columns. No responsive breakpoint.
- **Why**: On narrow screens, the controls column will be crushed. Press Start 2P at `--text-body` in a 33%-width column on a phone won't fit "Advance Text" buttons.
- **Fix**: Add `@media (max-width: 900px)` to stack columns vertically — controls on top, text below.

### 5. `.page-footer` shared padding/border breaks controller footer
- **What**: `style.css` sets `.page-footer { padding: 0; border-top }` globally. This works for judge/audience but the controller footer's session management section has its own border — double border (green from `.page-footer`, red from `.session-management`).
- **Why**: Two borders stack visually.
- **Fix**: Remove `border-top` from `.page-footer` in controller's local styles, or remove it from the shared style and let each page add it locally.

## Minor Observations

- **Advance Text button has inline styles** (`style="background: #ff0; color: #000; border-color: #ff0;"`) — should be a CSS class for maintainability and state management.
- **`textProgress` div uses inline styles** — same issue. Extract to class.
- **History "Copy JSON" button inside h2** is semantically odd and could confuse screen readers. Consider moving it to the section content.
- **Story queue Remove button** appears even during active round (just greyed out via parent `.disabled` opacity). Could hide entirely during rounds to reduce visual noise.
- **No keyboard shortcut for Advance Text** — during a live performance, clicking a button repeatedly is clunky. Spacebar or arrow key binding would be a big UX win for the controller.

## Questions to Consider

- What if Advance Text was triggered by spacebar, making the controller feel like a presentation clicker?
- What if the story text column showed a subtle line count / progress bar at the top so the controller can pace themselves?
- What if the controller footer showed the judge panel too (matching judge/audience), so all three views share the same footer?
