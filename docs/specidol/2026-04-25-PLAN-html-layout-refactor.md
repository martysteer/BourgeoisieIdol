# Plan: HTML Layout Refactor — Consistent Page Structure

## Context

All four SpecIdol pages (index, controller, judge, audience) have evolved independently with inconsistent layout structures. Headers, content areas, and footers use different markup patterns, different flex/grid approaches, and different responsive breakpoints. This refactor establishes a common layout skeleton so pages share structural CSS, behave consistently on mobile, and individual zones (e.g., "controller header", "judge content") can be worked on independently.

## Current State (Problems)

| Issue | Details |
|-------|---------|
| **Body layout varies** | index: flex centered, control: block, judge: flex column 100vh, audience: flex column 100vh via `.container` |
| **No shared layout classes** | Each page redefines `* { margin:0; padding:0; box-sizing }` and body styles |
| **Header markup differs** | judge: `.header` div, audience: `.header` div, control: bare `<h1>`, index: bare `<h1>` |
| **Footer markup differs** | judge: `.footer` div, audience: `.footer` flex, control: none (sections scroll), index: none |
| **Breakpoints inconsistent** | index: 768px, control: 900px, judge: 600px, audience: 900px |
| **Typography override duplication** | Each page's media query re-overrides `:root` vars independently |

## Design: Common Layout Shell

### Shared HTML pattern (all pages adopt):

```html
<body class="page-[name]">
  <header class="page-header">
    <!-- page-specific -->
  </header>
  <main class="page-content">
    <!-- page-specific -->
  </main>
  <footer class="page-footer">
    <!-- page-specific, optional -->
  </footer>
</body>
```

### Layout modes (via body class):

| Class | Behavior | Used By |
|-------|----------|---------|
| `.page-centered` | flex column, centered, min-height: 100vh, scrolls | index |
| `.page-scrollable` | flex column, min-height: 100vh, content scrolls naturally | control |
| `.page-locked` | flex column, height: 100vh, overflow: hidden | judge, audience |

### Shared layout CSS (added to `style.css`):

```css
/* Layout shell */
body {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.page-centered {
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.page-scrollable {
  padding: 2rem;
}

.page-locked {
  height: 100vh;
  overflow: hidden;
}

.page-header {
  padding: 1rem;
  text-align: center;
  flex-shrink: 0;
}

.page-content {
  flex: 1;
  min-height: 0;  /* allows flex children to shrink below content size */
}

.page-footer {
  padding: 1rem;
  flex-shrink: 0;
}
```

### Unified responsive breakpoints:

```css
/* Mobile: ≤600px — stacked, compact */
/* Tablet: ≤900px — reduced grid columns, smaller type */
/* Desktop: >900px — full layout */
```

Single media query block in `style.css` for typography scaling (remove per-page duplication):

```css
@media (max-width: 900px) {
  :root {
    --text-display: 1.5rem;
    --text-heading: 1.125rem;
    --text-subheading: 1rem;
    --text-body: 0.875rem;
    --text-caption: 0.75rem;
  }
}
```

## Implementation Steps

### Step 1: Update `style.css` with layout shell
- Add `.page-centered`, `.page-scrollable`, `.page-locked` layout modes
- Add `.page-header`, `.page-content`, `.page-footer` structural classes
- Add unified responsive breakpoint for typography (900px)
- Remove `* { margin: 0; ... }` duplication — it's already in style.css `:root`

### Step 2: Refactor `index.html`
- `<body class="page-centered">`
- Wrap `<h1>` in `<header class="page-header">`
- Wrap `.container` in `<main class="page-content">`
- Remove duplicated body flex/centering styles from inline `<style>`
- Remove duplicated `* { margin:0 }` reset
- Remove inline media query for typography (now in style.css)

### Step 3: Refactor `judge.html`
- `<body class="page-locked">`
- `.header` → `<header class="page-header">`
- `.main` → `<main class="page-content">` (keep flex centering for buzz button as page-specific)
- `.footer` → `<footer class="page-footer">`
- Remove duplicated body flex/height styles from inline `<style>`
- Remove duplicated `* { margin:0 }` reset
- Remove inline media query for typography

### Step 4: Refactor `audience.html`
- `<body class="page-locked">`
- Remove `.container` wrapper (body is now the flex column)
- `.header` → `<header class="page-header">`
- `.content` → `<main class="page-content">`
- `.footer` → `<footer class="page-footer">` (keep flex space-between as page-specific)
- Remove duplicated body flex/height styles from inline `<style>`
- Remove duplicated `* { margin:0 }` reset
- Remove inline media query for typography
- CRT `body::before` effect stays (page-specific)

### Step 5: Refactor `control.html`
- `<body class="page-scrollable">`
- Wrap title + session-info in `<header class="page-header">`
- Wrap main content sections in `<main class="page-content">`
- Wrap session-management in `<footer class="page-footer">` (destructive actions at bottom)
- Remove duplicated body styles from inline `<style>`
- Remove duplicated `* { margin:0 }` reset
- Remove inline media query for typography

### Step 6: Verify and test
- All four pages render correctly at desktop (>900px)
- All four pages render correctly at mobile (≤600px)
- judge.html: buzz button fills screen, no scroll
- audience.html: CRT effect works, text scrolls in content area only
- control.html: page scrolls naturally, all sections accessible
- index.html: centered layout, session grid works
- Modals still work on all pages (z-index above layout)

## Files Modified

| File | Changes |
|------|---------|
| `www/style.css` | Add layout shell classes, unified responsive breakpoint |
| `www/index.html` | Adopt common structure, remove inline layout CSS |
| `www/judge.html` | Adopt common structure, remove inline layout CSS |
| `www/audience.html` | Adopt common structure, remove inline layout CSS |
| `www/control.html` | Adopt common structure, remove inline layout CSS |

## What This Does NOT Change

- Page-specific visual styles (CRT effects, buzz button, neon colors)
- JavaScript behavior
- WebSocket protocol
- Content within zones — only the structural wrappers change
- Page-specific layout within zones (e.g., audience footer's flex space-between stays inline)
