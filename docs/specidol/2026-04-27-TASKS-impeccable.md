# SpecIdol UI Quality Pass — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Resolve all issues from the 2026-04-27 design critique and UI audit — accessibility, inline style extraction, controller UX, responsive breakpoints, and code cleanup.

**Architecture:** All changes are frontend-only (HTML/CSS/JS). No server (relay.py) changes. No new files — all edits to existing files. No frameworks, no build step. CSS custom properties in style.css, page-specific styles inline in each HTML file.

**Tech Stack:** Vanilla HTML/CSS/JS, Python WebSocket server (read-only), no test framework (browser testing).

**Source docs:**
- `docs/2026-04-27-CRITIQUE-ui-design.md` (critique)
- `docs/2026-04-27-AUDIT-ui-quality.md` (audit)

---

## File Map

| File | Changes |
|------|---------|
| `www/style.css` | Fix contrast (disabled buttons, `.waiting`), add new utility classes |
| `www/control.html` | Keyboard shortcut, pause/resume button, state-aware controls, inline style extraction, responsive breakpoint, story preview, Copy JSON button relocation, dead code cleanup |
| `www/index.html` | Extract joinControllerBtn inline style, add escapeHtml, fix session code XSS pattern |
| `www/judge.html` | ARIA attributes, extract inline styles from name modal |
| `www/audience.html` | ARIA attributes, lazy AudioContext, dead scroller cleanup |
| `www/modal.js` | Focus trap |
| `www/app.js` | Shared `renderJudgePanels()` extraction, `escapeHtml()` shared util |

---

## Task 1: Fix contrast failures (C2, C3)

**Files:**
- Modify: `www/style.css:76-78` (disabled button opacity)
- Modify: `www/style.css:149-152` (`.header-context.waiting` color)

- [x] **Step 1: Fix disabled button contrast**

In `www/style.css`, change `button:disabled` from `opacity: 0.3` to `opacity: 0.5`:

```css
button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

- [x] **Step 2: Fix `.header-context.waiting` contrast**

In `www/style.css`, change `#997700` to `#aa8800` (~5.0:1 on black):

```css
.header-context.waiting {
    color: #aa8800;
    text-shadow: none;
}
```

- [x] **Step 3: Browser-verify both changes**

Open controller page. Check disabled buttons are visible but clearly inactive. Check "No story selected" header text is readable.

- [x] **Step 4: Commit**

```bash
git add www/style.css
git commit -m "fix: contrast ratios on disabled buttons and waiting text (C2, C3)"
```

---

## Task 2: Add ARIA roles and live regions (C1)

**Files:**
- Modify: `www/judge.html` (buzz button, timer, buzz count, story title)
- Modify: `www/audience.html` (story text, outcome, judge panels)
- Modify: `www/control.html` (status, text progress)

- [x] **Step 1: Add ARIA to judge.html**

On the buzz button template in `startRound()` (judge.html ~line 352):
```html
<button class="buzz-button" id="buzzButton" onclick="buzz()" aria-label="Buzz out the reader">
    BUZZ
</button>
```

On timer display:
```html
<div class="timer" id="timer" role="timer" aria-live="off">0:00.0</div>
```

On buzz count display:
```html
<div class="buzz-count" id="buzzCountDisplay" aria-live="polite">0 of ${connectedJudges.length} buzzed</div>
```

On story title (line 131):
```html
<div class="story-title" id="storyTitle" aria-live="polite"></div>
```

On main waiting area (line 130):
```html
<main class="page-content" id="main" role="main">
```

- [x] **Step 2: Add ARIA to audience.html**

On story title (line 135):
```html
<div class="header-context waiting" id="storyTitle" aria-live="polite">Waiting for story...</div>
```

On outcome overlay (line 148):
```html
<div class="outcome" id="outcome" role="alert" aria-live="assertive"></div>
```

On story text container (line 140):
```html
<div class="story-text" id="storyText" aria-live="polite" aria-relevant="additions"></div>
```

- [x] **Step 3: Add ARIA to control.html**

On status text (line 356):
```html
<div id="currentStatus" class="status-text" role="status" aria-live="polite">Status: Waiting</div>
```

On text progress (line 362 — will become a class in Task 5):
```html
<div id="textProgress" class="text-progress" role="status" aria-live="polite"></div>
```

- [x] **Step 4: Browser-verify with screen reader or accessibility inspector**

- [x] **Step 5: Commit**

```bash
git add www/judge.html www/audience.html www/control.html
git commit -m "fix: add ARIA roles and live regions for screen readers (C1)"
```

---

## Task 3: Keyboard shortcut for Advance Text (H1)

**Files:**
- Modify: `www/control.html` (add keydown listener, ~after line 883)

- [x] **Step 1: Add keyboard listener**

Add after the `advanceText()` function in control.html (after line 883):

```javascript
// Keyboard shortcut: spacebar or right arrow to advance text
document.addEventListener('keydown', (e) => {
    // Don't capture if typing in an input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    if (e.code === 'Space' || e.code === 'ArrowRight') {
        e.preventDefault();
        advanceText();
    }
});
```

- [x] **Step 2: Browser-verify**

Start round. Press spacebar — should advance text. Press right arrow — should advance text. Click into story title input, press spacebar — should type space, NOT advance. When round not running, spacebar should do nothing (advanceText checks status).

- [x] **Step 3: Commit**

```bash
git add www/control.html
git commit -m "feat: keyboard shortcut for advance text — spacebar and right arrow (H1)"
```

---

## Task 4: Pause/Resume button on controller (H5)

**Files:**
- Modify: `www/control.html:357-361` (controls div)
- Modify: `www/control.html` inline styles (add `.btn-pause` class)
- Modify: `www/control.html` JS `updateStatus()` function (~line 650)

- [x] **Step 1: Add btn-pause CSS class**

In control.html `<style>` block, add after the `.controls` rule (~line 273):

```css
.btn-pause {
    background: var(--black);
    color: var(--neon-yellow);
    border-color: var(--neon-yellow);
}

.btn-pause:hover:not(:disabled) {
    background: var(--neon-yellow);
    color: var(--black);
    box-shadow: 0 0 20px var(--neon-yellow);
}
```

- [x] **Step 2: Add pause/resume button to HTML**

In the controls div (line 357-361), add the pause button after advanceBtn:

```html
<div class="controls">
    <button onclick="startRound()" id="startBtn">Start Round</button>
    <button onclick="advanceText()" id="advanceBtn" class="btn-advance" disabled>Advance Text</button>
    <button onclick="togglePause()" id="pauseBtn" class="btn-pause" disabled>Pause</button>
    <button onclick="resetRound()" id="resetBtn">Reset</button>
</div>
```

Note: this also extracts the advanceBtn inline style (Task 5) — use the `.btn-advance` class instead of `style="..."`.

- [x] **Step 3: Add togglePause function and update updateStatus**

Add `togglePause()` after `advanceText()`:

```javascript
function togglePause() {
    if (!sessionState) return;
    const status = sessionState.current_round.status;
    if (status === 'running') {
        client.pause();
    } else if (status === 'paused') {
        client.resume();
    }
}
```

Update `updateStatus()` to manage the pause button:

```javascript
function updateStatus(status) {
    document.getElementById('currentStatus').textContent = `Status: ${status}`;

    const startBtn = document.getElementById('startBtn');
    const advanceBtn = document.getElementById('advanceBtn');
    const pauseBtn = document.getElementById('pauseBtn');

    startBtn.disabled = (status === 'running' || status === 'paused');
    advanceBtn.disabled = (status !== 'running');
    pauseBtn.disabled = (status !== 'running' && status !== 'paused');
    pauseBtn.textContent = (status === 'paused') ? 'Resume' : 'Pause';
}
```

- [x] **Step 4: Browser-verify**

Start round. Pause button active. Click pause — status shows "paused", advance disabled, pause becomes "Resume". Click Resume — back to running. When waiting or ended, pause disabled.

- [x] **Step 5: Commit**

```bash
git add www/control.html
git commit -m "feat: pause/resume button on controller (H5)"
```

---

## Task 5: Extract inline styles to CSS classes (H2, H3, L3, L5)

**Files:**
- Modify: `www/control.html` (advanceBtn, textProgress, cancelEditBtn, Copy JSON button)
- Modify: `www/index.html` (joinControllerBtn)

- [x] **Step 1: Add CSS classes in control.html style block**

Add to control.html `<style>`:

```css
.btn-advance {
    background: var(--neon-yellow);
    color: var(--black);
    border-color: var(--neon-yellow);
}

.btn-advance:hover:not(:disabled) {
    box-shadow: 0 0 20px var(--neon-yellow);
}

.text-progress {
    font-family: 'Courier New', monospace;
    font-size: var(--text-caption);
    opacity: 0.7;
}

.btn-copy-json {
    font-size: var(--text-caption);
    padding: 0.5rem 1rem;
    margin-left: 1rem;
    vertical-align: middle;
}
```

Update `#cancelEditBtn` rules to handle display toggle via class:
```css
#cancelEditBtn {
    display: none;
}

#cancelEditBtn.visible {
    display: inline-block;
}
```

Remove existing `#cancelEditBtn` color rules since they're already defined at lines 308-318.

- [x] **Step 2: Replace inline styles in control.html HTML**

Replace advanceBtn (line 359):
```html
<button onclick="advanceText()" id="advanceBtn" class="btn-advance" disabled>Advance Text</button>
```

Replace textProgress (line 362):
```html
<div id="textProgress" class="text-progress" role="status" aria-live="polite"></div>
```

Replace cancelEditBtn (line 400) — remove `style` attribute:
```html
<button onclick="cancelEdit()" id="cancelEditBtn">Cancel</button>
```

Replace Copy JSON button (line 417):
```html
<button onclick="event.stopPropagation(); copyHistory()" class="btn-copy-json">Copy JSON</button>
```

- [x] **Step 3: Update updateFormUI() to use class toggle**

```javascript
if (editingStoryIndex !== null) {
    formTitle.textContent = 'Edit Story';
    saveBtn.textContent = 'Update Story';
    cancelBtn.classList.add('visible');
} else {
    formTitle.textContent = 'Add Story';
    saveBtn.textContent = 'Add Story';
    cancelBtn.classList.remove('visible');
}
```

- [x] **Step 4: Add CSS class in index.html and remove inline style**

Add to index.html `<style>`:

```css
.btn-controller {
    background: #440;
    color: var(--neon-yellow);
    border-color: var(--neon-yellow);
    margin-top: 1rem;
}

.btn-controller:hover:not(:disabled) {
    background: var(--neon-yellow);
    color: var(--black);
    box-shadow: 0 0 20px var(--neon-yellow);
}
```

Replace joinControllerBtn (line 146):
```html
<button onclick="joinAsController()" id="joinControllerBtn" disabled class="btn-controller">Join as Controller</button>
```

- [x] **Step 5: Browser-verify all affected buttons render identically**

- [x] **Step 6: Commit**

```bash
git add www/control.html www/index.html
git commit -m "refactor: extract inline styles to CSS classes (H2, H3, L3, L5)"
```

---

## Task 6: Controller responsive breakpoint for two-column layout (H4)

**Files:**
- Modify: `www/control.html` inline styles (~after line 115)

- [x] **Step 1: Add responsive breakpoint**

Add to the existing `@media (max-width: 900px)` block in control.html (line 164-168):

```css
@media (max-width: 900px) {
    .story-management .section-content {
        grid-template-columns: 1fr;
    }

    .selected-story-display {
        flex-direction: column;
    }

    .round-controls-column {
        flex: none;
        border-right: none;
        border-bottom: 2px solid var(--neon-yellow);
    }

    .story-text-column {
        max-height: 30vh;
    }
}
```

- [x] **Step 2: Browser-verify**

Resize browser to < 900px. Controls column stacks above story text. Border switches from right to bottom.

- [x] **Step 3: Commit**

```bash
git add www/control.html
git commit -m "fix: responsive breakpoint for controller two-column layout (H4)"
```

---

## Task 7: Focus trap in modals (H6)

**Files:**
- Modify: `www/modal.js`

- [x] **Step 1: Add focus trap logic**

Replace `modal.js` with focus-trap-aware version. Key changes:
- `okBtn.focus()` on modal open
- Tab key cycles between visible buttons only
- Shift+Tab wraps backwards

```javascript
// Custom modal dialog system

function customConfirm(message) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('modalOverlay');
        const messageEl = document.getElementById('modalMessage');
        const okBtn = document.getElementById('modalOk');
        const cancelBtn = document.getElementById('modalCancel');

        messageEl.textContent = message;
        if (cancelBtn) cancelBtn.style.display = 'block';
        overlay.classList.add('active');
        okBtn.focus();

        const focusableEls = [okBtn, cancelBtn].filter(el => el && el.style.display !== 'none');

        const cleanup = () => {
            overlay.classList.remove('active');
            okBtn.removeEventListener('click', handleOk);
            if (cancelBtn) cancelBtn.removeEventListener('click', handleCancel);
            document.removeEventListener('keydown', handleKey);
        };

        const handleOk = () => { cleanup(); resolve(true); };
        const handleCancel = () => { cleanup(); resolve(false); };
        const handleKey = (e) => {
            if (e.key === 'Escape') { handleCancel(); return; }
            if (e.key === 'Tab') {
                const first = focusableEls[0];
                const last = focusableEls[focusableEls.length - 1];
                if (e.shiftKey) {
                    if (document.activeElement === first) { e.preventDefault(); last.focus(); }
                } else {
                    if (document.activeElement === last) { e.preventDefault(); first.focus(); }
                }
            }
        };

        okBtn.addEventListener('click', handleOk);
        if (cancelBtn) cancelBtn.addEventListener('click', handleCancel);
        document.addEventListener('keydown', handleKey);
    });
}

function customAlert(message) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('modalOverlay');
        const messageEl = document.getElementById('modalMessage');
        const okBtn = document.getElementById('modalOk');
        const cancelBtn = document.getElementById('modalCancel');

        messageEl.textContent = message;
        if (cancelBtn) cancelBtn.style.display = 'none';
        overlay.classList.add('active');
        okBtn.focus();

        const cleanup = () => {
            overlay.classList.remove('active');
            okBtn.removeEventListener('click', handleOk);
            document.removeEventListener('keydown', handleKey);
        };

        const handleOk = () => { cleanup(); resolve(); };
        const handleKey = (e) => {
            if (e.key === 'Escape') { handleOk(); return; }
            if (e.key === 'Tab') { e.preventDefault(); okBtn.focus(); }
        };

        okBtn.addEventListener('click', handleOk);
        document.addEventListener('keydown', handleKey);
    });
}
```

- [x] **Step 2: Browser-verify**

Trigger confirm dialog. Tab cycles between OK/Cancel. Shift+Tab wraps. Focus doesn't escape to background.

- [x] **Step 3: Commit**

```bash
git add www/modal.js
git commit -m "fix: focus trap in modal dialogs (H6)"
```

---

## Task 8: Controller state-aware controls (Critique #1)

**Files:**
- Modify: `www/control.html` inline styles + JS `updateStatus()`

- [x] **Step 1: Add state-based CSS classes**

Add to control.html `<style>`:

```css
.round-controls-column[data-status="running"] {
    border-color: var(--neon-green);
    background: rgba(0, 255, 0, 0.05);
}

.round-controls-column[data-status="paused"] {
    border-color: var(--neon-yellow);
    background: rgba(255, 255, 0, 0.05);
}

.round-controls-column[data-status="ended"] {
    border-color: var(--neon-red);
    background: rgba(255, 0, 0, 0.05);
}

.status-text[data-status="running"] {
    color: var(--neon-green);
    text-shadow: 0 0 10px var(--neon-green);
}

.status-text[data-status="paused"] {
    color: var(--neon-yellow);
    text-shadow: 0 0 10px var(--neon-yellow);
}

.status-text[data-status="ended"] {
    color: var(--neon-red);
}
```

- [x] **Step 2: Update updateStatus() to set data attributes**

```javascript
function updateStatus(status) {
    const statusEl = document.getElementById('currentStatus');
    statusEl.textContent = `Status: ${status}`;
    statusEl.dataset.status = status;

    const controlsCol = document.querySelector('.round-controls-column');
    if (controlsCol) controlsCol.dataset.status = status;

    const startBtn = document.getElementById('startBtn');
    const advanceBtn = document.getElementById('advanceBtn');
    const pauseBtn = document.getElementById('pauseBtn');

    startBtn.disabled = (status === 'running' || status === 'paused');
    advanceBtn.disabled = (status !== 'running');
    pauseBtn.disabled = (status !== 'running' && status !== 'paused');
    pauseBtn.textContent = (status === 'paused') ? 'Resume' : 'Pause';
}
```

- [x] **Step 3: Browser-verify**

Start round — controls column glows green. Pause — yellow. End — red.

- [x] **Step 4: Commit**

```bash
git add www/control.html
git commit -m "feat: controller state-aware controls with visual differentiation (Critique #1)"
```

---

## Task 9: Story text preview in empty state (Critique #3, M1)

**Files:**
- Modify: `www/control.html` JS

- [x] **Step 1: Update clearStoryText to show preview**

Replace `clearStoryText()`:

```javascript
function clearStoryText() {
    const textEl = document.getElementById('liveStoryText');
    const index = sessionState ? sessionState.current_round.story_index : null;

    if (index !== null && sessionState.stories[index]) {
        textEl.innerHTML = '';
        const preview = document.createElement('div');
        preview.style.opacity = '0.3';
        preview.style.whiteSpace = 'pre-wrap';
        preview.style.lineHeight = '1.7';
        preview.textContent = sessionState.stories[index].text;
        textEl.appendChild(preview);
    } else {
        textEl.innerHTML = '<span class="empty-text">Story text appears here during round...</span>';
    }
}
```

- [x] **Step 2: Update round_started handler**

In the `round_started` handler, replace `clearStoryText()` with a hard clear:
```javascript
document.getElementById('liveStoryText').innerHTML = '';
```

- [x] **Step 3: Add clearStoryText call to selectStory**

Add at end of `selectStory()` after `loadStoryForEditing(index)`:
```javascript
clearStoryText();
```

- [x] **Step 4: Browser-verify**

Select story — dimmed preview appears. Start round — preview clears, live text populates. Reset — preview returns.

- [x] **Step 5: Commit**

```bash
git add www/control.html
git commit -m "feat: story text preview when story selected but round not started (Critique #3)"
```

---

## Task 10: Fix story_added/story_removed missing story_count (M2)

**Files:**
- Modify: `www/judge.html:338-344`
- Modify: `www/audience.html:275-281`

- [x] **Step 1: Fix judge.html handlers**

Replace story_added handler:
```javascript
client.on('story_added', (data) => {
    const el = document.getElementById('storyCount');
    el.textContent = (parseInt(el.textContent) || 0) + 1;
});
```

Replace story_removed handler:
```javascript
client.on('story_removed', (data) => {
    const el = document.getElementById('storyCount');
    el.textContent = Math.max(0, (parseInt(el.textContent) || 0) - 1);
});
```

- [x] **Step 2: Fix audience.html handlers — same pattern**

- [x] **Step 3: Browser-verify**

Add/remove stories from controller. Judge and audience pages show correct counts.

- [x] **Step 4: Commit**

```bash
git add www/judge.html www/audience.html
git commit -m "fix: story count display — increment/decrement instead of reading missing field (M2)"
```

---

## Task 11: Move Copy JSON button out of h2 (M6)

**Files:**
- Modify: `www/control.html:413-421`

- [x] **Step 1: Move button to section-content**

```html
<div class="collapsible collapsed" id="historySection">
    <h2 onclick="toggleSection('historySection')">
        <span class="arrow">▼</span>
        History
    </h2>
    <div class="section-content">
        <button onclick="copyHistory()" class="btn-copy-json">Copy JSON</button>
        <ul class="history-list" id="historyList"></ul>
    </div>
</div>
```

- [x] **Step 2: Commit**

```bash
git add www/control.html
git commit -m "fix: move Copy JSON button out of h2 for semantic correctness (M6)"
```

---

## Task 12: Fix page-footer double border (L1)

**Files:**
- Modify: `www/control.html:19-21`

- [x] **Step 1: Remove border-top from controller's page-footer**

```css
.page-footer {
    padding: 0;
    border-top: none;
}
```

- [x] **Step 2: Commit**

```bash
git add www/control.html
git commit -m "fix: remove double border on controller footer (L1)"
```

---

## Task 13: Fix XSS pattern in index.html renderSessions (M8)

**Files:**
- Modify: `www/index.html` JS

- [x] **Step 1: Add escapeHtml to index.html**

```javascript
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
```

- [x] **Step 2: Rewrite renderSessions with DOM API**

```javascript
function renderSessions(sessions) {
    const container = document.getElementById('sessionButtons');
    if (sessions.length === 0) {
        container.innerHTML = '<div style="text-align: center; opacity: 0.7; padding: 2rem;">No active sessions</div>';
        return;
    }

    container.innerHTML = '';
    sessions.forEach(session => {
        const btn = document.createElement('button');
        btn.addEventListener('click', () => selectSession(session.code));
        btn.innerHTML = `
            <div class="session-code">${escapeHtml(session.code)}</div>
            <div class="session-stats">
                ${session.story_count} stories | ${session.judge_count} judges | ${session.audience_count} audience
            </div>
        `;
        container.appendChild(btn);
    });
}
```

- [x] **Step 3: Update selectSession to not rely on textContent matching**

```javascript
function selectSession(code) {
    selectedCode = code;
    document.getElementById('joinControllerBtn').disabled = false;
    document.getElementById('joinAudienceBtn').disabled = false;
    document.getElementById('joinJudgeBtn').disabled = false;
    document.querySelectorAll('#sessionButtons button').forEach(btn => {
        const isSelected = btn.querySelector('.session-code').textContent === code;
        btn.style.background = isSelected ? '#0f0' : '#000';
        btn.style.color = isSelected ? '#000' : '#0f0';
    });
}
```

- [x] **Step 4: Commit**

```bash
git add www/index.html
git commit -m "fix: XSS-safe session rendering with DOM API (M8)"
```

---

## Task 14: Consolidate renderJudgePanels into shared app.js (Systemic)

**Files:**
- Modify: `www/app.js`
- Modify: `www/judge.html`
- Modify: `www/audience.html`

- [x] **Step 1: Add shared renderJudgePanelCells to app.js**

```javascript
function renderJudgePanelCells(containerId, judges) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const buzzedIds = new Set(
        [...container.querySelectorAll('.judge-cell.buzzed')]
            .map(el => parseInt(el.dataset.judge))
    );

    const initials = calculateInitials(judges);
    container.innerHTML = judges.map(j =>
        `<div class="judge-cell${buzzedIds.has(j.id) ? ' buzzed' : ''}" data-judge="${j.id}"><span class="x-mark">✕</span><span class="initials">${initials[j.id]}</span></div>`
    ).join('');
}
```

- [x] **Step 2: Update judge.html renderJudgePanels to call shared function**

```javascript
function renderJudgePanels() {
    renderJudgePanelCells('judgePanels', connectedJudges);
    updateBuzzCount();
}
```

- [x] **Step 3: Update audience.html renderJudgePanels to call shared function**

```javascript
function renderJudgePanels() {
    renderJudgePanelCells('judgePanels', connectedJudges);
}
```

- [x] **Step 4: Commit**

```bash
git add www/app.js www/judge.html www/audience.html
git commit -m "refactor: consolidate renderJudgePanels into shared app.js (Systemic)"
```

---

## Task 15: Replace hard-coded hex with CSS custom properties (Systemic)

**Files:**
- Modify: `www/control.html`, `www/judge.html`, `www/audience.html`, `www/index.html`

- [x] **Step 1: Replace in control.html**

All `#0f0` → `var(--neon-green)`, `#ff0` → `var(--neon-yellow)`, `#f00` → `var(--neon-red)`, `#000` → `var(--black)` in the `<style>` block.

Key locations: `.collapsible` border, `.session-management`, `.danger-btn`, `.selected-story-display`, `.round-controls-column`, `.story-item`, `.story-actions button`, `.history-item.defeat`, `.management-section h3`, `.status-text`, `.empty-state .cta`.

- [x] **Step 2: Replace in index.html**

`h1` text-shadow, `.column-header`, `.error`.

- [x] **Step 3: Replace in judge.html**

`.story-title`, `.timer`, `.buzz-count`, `.buzz-count.active`. Leave buzz button gradient stops hard-coded.

- [x] **Step 4: Replace in audience.html**

`.story-text-container` border, `.outcome.victory`, `.outcome.defeat`. Leave CRT scanline rgba values and dark variant `#300`.

- [x] **Step 5: Commit**

```bash
git add www/control.html www/index.html www/judge.html www/audience.html
git commit -m "refactor: replace hard-coded hex colors with CSS custom properties (Systemic)"
```

---

## Task 16: Clean up dead scroller code in audience.html (L6)

**Files:**
- Modify: `www/audience.html`

- [x] **Step 1: Remove dead scroller references**

Remove `let scroller = null;` and all `if (scroller)` guards.

- [x] **Step 2: Commit**

```bash
git add www/audience.html
git commit -m "refactor: remove dead scroller code from audience.html (L6)"
```

---

## Task 17: Lazy AudioContext on audience page (M5)

**Files:**
- Modify: `www/audience.html:378-383`

- [x] **Step 1: Make AudioContext lazy**

```javascript
let audioContext = null;

function getAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContext;
}

function enableAudio() {
    getAudioContext().resume();
    document.getElementById('audioOverlay').style.display = 'none';
}
```

Replace all `audioContext.` references in `play*Sound()` functions with `getAudioContext().`.

- [x] **Step 2: Commit**

```bash
git add www/audience.html
git commit -m "refactor: lazy AudioContext creation on audience page (M5)"
```

---

## Task 18: Handle reconnect to dead session (L7)

**Files:**
- Modify: `www/control.html`, `www/judge.html`, `www/audience.html`

- [x] **Step 1: Add error handler to each page**

```javascript
client.on('error', async (data) => {
    if (data.message === 'Invalid session code') {
        await customAlert('Session no longer exists. Returning to home.');
        window.location.href = 'index.html';
    }
});
```

- [x] **Step 2: Commit**

```bash
git add www/control.html www/judge.html www/audience.html
git commit -m "fix: handle reconnect to dead session with redirect to index (L7)"
```

---

## Task 19: Move escapeHtml to shared app.js (Systemic)

**Files:**
- Modify: `www/app.js`
- Modify: `www/control.html` (remove local copy)

- [x] **Step 1: Add escapeHtml to app.js**

```javascript
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
```

- [x] **Step 2: Remove local escapeHtml from control.html (lines 448-452)**

- [x] **Step 3: Commit**

```bash
git add www/app.js www/control.html
git commit -m "refactor: move escapeHtml to shared app.js (Systemic)"
```

---

## Verification

After all tasks:

1. **Controller**: Start/pause/resume/advance/reset cycle works. Keyboard shortcuts work. State colors change. Story preview shows. Responsive layout stacks on narrow screens.
2. **Judge**: Buzz button has aria-label. Timer has role. Panels render via shared function. Story count updates correctly.
3. **Audience**: No console AudioContext warning. Dead scroller gone. ARIA on outcome and story text. Panels via shared function.
4. **Index**: Sessions render XSS-safe. Controller button styled via class.
5. **All pages**: Disabled buttons at 0.5 opacity. Waiting text at `#aa8800`. Modal focus traps work. No hard-coded hex in CSS (except gradient stops).
6. **Accessibility**: Browser accessibility inspector — no critical warnings.

## Execution Order

Tasks 1-19 in sequence. Key dependencies:
- Task 4 before Task 5 (pause button introduces `.btn-advance` class)
- Task 15 after Tasks 5, 8 (which add new CSS with hex to convert)
- Task 19 after Task 13 (index.html adds local escapeHtml first)
