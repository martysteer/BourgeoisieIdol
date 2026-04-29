# BOOTSTRAP — Claude Behaviour for BourgeoisieIdol

## Project Context

BourgeoisieIdol: live web application examining competitive cultural production. Forked from SpecIdol, adapted for Historical Materialism Conference. Readers present work, judges evaluate real-time, audience observes. Format interrogates cultural gatekeeping, collective decision-making, alternatives to competitive hierarchies.

## Hard Rules

- **No frameworks, no build step.** Vanilla HTML/CSS/JS frontend. Python + `websockets` backend. This is intentional. Don't suggest React, Vite, TypeScript, etc.
- **No database.** In-memory state only. Ephemeral event app — state loss on restart is acceptable.
- **Inline `<style>` for initial building.** Start with inline `<style>` blocks when prototyping/building features. Once working, refactor page-specific styles into separate CSS files. Shared base stays in `style.css`.
- **Inline `<script>` per page.** Shared logic in `app.js`/`modal.js`, page-specific JS stays inline in the HTML. Don't extract to separate JS files unless there's clear reuse across multiple pages.
- **CSS custom properties** defined in `style.css :root`. Use them. Typography scale uses 1.5x ratio (`--text-display` through `--text-caption`). Colour palette: `--neon-green`, `--neon-yellow`, `--neon-magenta`, `--neon-red`, `--black`.
- **All game logic lives in `server/relay.py`.** Single file. Frontend is display + input only.
- **WebSocket is the only transport.** No REST, no fetch, no HTTP APIs. Everything goes through the WS relay.

## Code Patterns

- `SpecIdolClient` class in `app.js` — all pages use it for WS connection, message routing, clock sync
- Message-based architecture: `{type: "...", ...payload}` over WebSocket
- Controller is authoritative — only controller sends game commands (`round_start`, `add_story`, `speed_change`, etc.)
- Judges send `buzz` only. Audience is read-only (listen only).
- Custom modal system (`modal.js`/`modal.css`) — no `alert()`/`confirm()`. Use `showModal()`/`showConfirmModal()`.
- `prefers-reduced-motion` respected globally. Keep it.

## Visual Style

- Retro/campy game show. Black backgrounds, neon green (`#0f0`) primary, yellow headings.
- `Press Start 2P` pixel font for headings/buttons. `Courier New` monospace for body.
- `degheest/` fonts available (FT88, Director, etc.) — libre/open fonts for display use.
- CRT scanline effect on audience view. Glow/box-shadow effects on interactive elements.
- Audience view is designed for projector — full viewport, high contrast, large text.
- Judge view is mobile-optimised — big touch targets, minimal chrome.

## File Layout

```
server/relay.py          — all backend logic (single file)
www/app.js               — shared WS client
www/modal.js, modal.css  — shared modal system
www/style.css            — shared base styles + CSS vars
www/index.html           — landing/join page
www/control.html         — controller interface
www/judge.html           — judge interface
www/audience.html        — audience/projector view
docs/                    — all documentation
Makefile                 — dev and docker commands
```

## Docs

All docs in `docs/`. Filename: `YYYY-MM-DD-TYPE-shortname.md`

| Type | Use |
|------|-----|
| `FEATURE` | New feature design/spec |
| `PLAN` | Implementation plan |
| `SPEC` | Original design specification |
| `CRITIQUE` | Design review |
| `NOTES` | General notes, research |

Changelog: `docs/CHANGELOG.md` — Keep-a-Changelog format. Not top-level.

When adding a feature, create a doc *before* or *alongside* implementation.

## Git

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `style:`, `chore:`
- Short subjects, imperative mood
- Commit related changes together
- Don't batch unrelated changes into one commit
- Don't commit credentials or `.env`

## Dev

```
make dev       — local servers (port 8000 + 8765)
make dev-stop  — stop local servers
make docker    — build image
make servers   — run container (port 80 + 8765)
```

## Working Style

- Features arrive as conversation. Discuss before building. Plans/specs in docs.
- Small, incremental changes. Don't rewrite working code to add a feature.
- Test in browser — no test framework. This is a live event app, not a SaaS product.
- If changing WS protocol (new message types), update both `relay.py` and the relevant HTML page(s) together. Keep them in sync.
- Consider thematic implications. See `docs/sources/` for conceptual framework. How do design choices reinforce or challenge cultural hierarchies?
- Keep it fun. This is a game show app interrogating game show formats.
