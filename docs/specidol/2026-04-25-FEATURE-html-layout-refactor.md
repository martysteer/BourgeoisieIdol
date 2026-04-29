# HTML Layout Refactor — Consistent Page Structure

**Date:** 2026-04-25
**Status:** Complete (extended by `2026-04-25-FEATURE-consistent-headers.md`)

## Problem

All four SpecIdol pages (index, controller, judge, audience) evolved independently with inconsistent layout structures:

- Body layout varies: flex centered / block / flex column 100vh / flex column via `.container`
- No shared layout classes — each page redefines `* { margin:0 }` and body styles
- Header/footer markup differs across pages (`.header` divs, bare `<h1>`, `.footer` divs)
- Breakpoints inconsistent: 768px, 900px, 600px across pages
- Typography override duplication in per-page media queries

## Solution

### Common HTML Shell

All pages adopt:

```html
<body class="page-[name]">
  <header class="page-header">...</header>
  <main class="page-content">...</main>
  <footer class="page-footer">...</footer>
</body>
```

### Layout Modes

| Class | Behavior | Used By |
|-------|----------|---------|
| `.page-centered` | flex column, centered, min-height: 100vh, scrolls | index |
| `.page-scrollable` | flex column, min-height: 100vh, content scrolls | control |
| `.page-locked` | flex column, height: 100vh, overflow: hidden | judge, audience |

### Unified Breakpoint

Single 900px breakpoint in `style.css` for typography scaling. Per-page media queries for typography removed.

## Files Modified

| File | Changes |
|------|---------|
| `www/style.css` | Layout shell classes, unified responsive breakpoint |
| `www/index.html` | Adopt common structure, remove inline layout CSS |
| `www/judge.html` | Adopt common structure, remove inline layout CSS |
| `www/audience.html` | Adopt common structure, remove inline layout CSS |
| `www/control.html` | Adopt common structure, remove inline layout CSS |

## What Stays Unchanged

- Page-specific visual styles (CRT effects, buzz button, neon colors)
- JavaScript behavior
- WebSocket protocol
- Content within zones
- Page-specific layout within zones (e.g., audience footer's flex space-between)
