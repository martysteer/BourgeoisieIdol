# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BourgeoisieIdol — fork of [SpecIdol](https://github.com/martysteer/SpecIdol), adapted with influences from:
- [Bourgeoisie](https://en.wikipedia.org/wiki/Bourgeoisie) (class systems, social dynamics)
- [Popular assembly](https://en.wikipedia.org/wiki/Popular_assembly) (collective decision-making)
- [Citizen's Assembly](https://en.wikipedia.org/wiki/Citizens%27_assembly) (direct democracy)
- [Point (typography)](https://en.wikipedia.org/wiki/Point_(typography)) (measurement, precision)
- [Making of A Brief Visual Exploration of A Dictionary of Typography](https://www.c82.net/blog/?id=86) (an historical semantic)
- [Socialist voting discussion](https://www.reddit.com/r/Socialism_101/comments/1omyrfh/what_do_socialists_think_about_voting/) (sociocultural values)
- [Soviet mosaics, A lot of them made in the 80’s](https://www.reddit.com/r/RetroFuturism/comments/j0904z/soviet_mosaics_a_lot_of_them_made_in_the_80s/) (visual aesthetic)
- [International Image Interoperability Framework](https://iiif.io/api/index.html) (technology)

**For the [Twenty-third Annual Historical Materialism Conference: Planetary Warscapes Ablaze: Imperial Mutations in Infernal Times](https://www.historicalmaterialism.org/event/twenty-third-annual-conference/#newtechnologies)**, **[Marxism, Culture and the Arts Stream](https://www.historicalmaterialism.org/event/twenty-third-annual-conference/#marxismculture)** and **[New Technologies and Capital Accumulation](https://www.historicalmaterialism.org/event/twenty-third-annual-conference/#newtechnologies)**

*Original: live "Pop Idol for writers" web app for writers conventions. Readers read aloud with auto-scrolling text, three judges buzz them out. Survive 2 min without all judges buzzing = win.*

## Development Commands

**Local development (no Docker):**
```bash
make dev         # Start servers (port 8000 + WebSocket 8765)
make dev-stop    # Stop local servers
```

**Docker (production):**
```bash
make docker      # Build Docker image
make servers     # Run container (port 80 + 8765)
make stop        # Stop container
make clean       # Remove container and image
```

**Python setup (if running locally):**
```bash
cd server
pip3 install -r requirements.txt  # Only dependency: websockets==12.0
```

Access at `http://localhost:8000` (dev) or `http://localhost` (Docker).

## Architecture

### Tech Stack
- **No frameworks, no build step** — vanilla HTML/CSS/JS frontend, Python backend
- **No database** — ephemeral in-memory state (sessions lost on server restart)
- **Single transport** — WebSocket only (no REST, no fetch, no HTTP APIs)
- **Single server file** — all backend logic in `server/relay.py`

### Message-Based Design

All communication is WebSocket messages: `{type: "...", data: {...}}`.

**Server → Clients:** broadcast session state changes
**Controller → Server:** commands (`round_start`, `add_story`, `speed_change`, etc.)
**Judges → Server:** `buzz` only
**Audience → Server:** read-only (no commands)

Clock sync: server sends timestamps, clients compute `clockOffset` for local timer/scroll coordination.

### Multi-Session Architecture

- `sessions = {}` — in-memory dict of all active sessions
- `websocket_sessions = {}` — maps each client WebSocket to their session code
- Session codes: 4 random uppercase letters (e.g., "ABCD")
- Judges auto-assigned sequential IDs (1, 2, 3...) on join

### Client Types

Four views in `www/`:

1. **`index.html`** — landing page, session list, join interface
2. **`control.html`** — controller (story queue, round controls, import/export)
3. **`judge.html`** — judge view (big red buzzer button, mobile-optimized)
4. **`audience.html`** — projector view (CRT effects, judge panels, animations)

All share `app.js` (SpecIdolClient class, Timer, AutoScroller utilities) and `modal.js`/`modal.css` (custom modal system).

### State Management

**Server (`relay.py`) holds authoritative state:**
- `sessions[code].stories` — list of stories
- `sessions[code].current_round` — active round state (story_index, start_time, speed, paused, buzzes, status)
- `sessions[code].judge_slots` — dynamic judge roster
- `sessions[code].clients` — all connected WebSockets and their roles

**Clients compute display locally:**
- Timer: calculate elapsed from server `start_time` + local clock
- AutoScroller: track scroll position, advance based on `speed` and `dt`
- State updates: server broadcasts state changes, clients re-render

### Controller-Only Commands

Only the controller can send these message types (enforced server-side):
`add_story`, `remove_story`, `round_start`, `speed_change`, `pause`, `resume`, `reset_round`, `text_advance`, `import_session`, `eject_judges`, `shutdown_audience`, `delete_session`

## Code Patterns

**Shared JavaScript:**
- `SpecIdolClient` class — WS connection, message routing, clock sync (in `app.js`)
- `Timer` class — client-side timer with pause/resume, server timestamp sync
- `AutoScroller` class — position-tracking auto-scroll (avoids speed^2 bugs)
- Custom modals — use `showModal()`/`showConfirmModal()` from `modal.js`, not `alert()`/`confirm()`

**Inline code strategy:**
- Shared logic: `app.js`, `modal.js`
- Page-specific JS: inline `<script>` in HTML (don't extract unless reused across pages)
- Initial styles: inline `<style>` during prototyping
- Production styles: page-specific CSS extracted to separate files, shared base in `style.css`

**CSS custom properties (defined in `style.css :root`):**
- Typography scale: `--text-display` through `--text-caption` (1.5x ratio)
- Color palette: `--neon-green`, `--neon-yellow`, `--neon-magenta`, `--neon-red`, `--black`
- Use these variables for consistency

**Accessibility:**
- `prefers-reduced-motion` respected globally — keep it

## Visual Style

Retro/campy game show aesthetic:
- Black backgrounds, neon green (`#0f0`) primary, yellow headings
- `Press Start 2P` pixel font (headings/buttons), `Courier New` (body)
- `degheest/` directory has libre/open fonts (FT88, Director, etc.)
- CRT scanline effects on audience view
- Glow/box-shadow on interactive elements
- Audience view: full viewport, high contrast, projector-optimized
- Judge view: mobile-optimized, big touch targets

## Documentation

All docs in `docs/`. Naming: `YYYY-MM-DD-TYPE-shortname.md`

Types: `FEATURE`, `PLAN`, `SPEC`, `CRITIQUE`, `NOTES`

Changelog: `docs/CHANGELOG.md` (Keep-a-Changelog format, not top-level)

When adding features: create doc *before* or *alongside* implementation.

## Hard Constraints

**Do not suggest:**
- React, Vue, Svelte, or any frontend framework
- TypeScript, Vite, webpack, or build tooling
- Database (Postgres, SQLite, etc.)
- REST APIs or HTTP endpoints (WebSocket only)
- Test frameworks (manual browser testing)

**These are intentional design choices, not technical debt.**

## License

Anti-Capitalist Software License v1.4 — see LICENSE file.

## Thematic Framework

BourgeoisieIdol critically engages with competitive cultural production by layering multiple conceptual frames:

**Class Analysis** — Examine power dynamics between judges (gatekeepers), readers (cultural workers), and audience (consumers). How does the format reproduce or challenge bourgeois cultural hierarchies?

**Democratic Alternatives** — Popular assemblies and citizens' assemblies suggest alternative models to competitive elimination. Could collective deliberation replace individual judgment? What would non-hierarchical evaluation look like?

**Measurement & Standardization** — Typographic points represent precision and shared standards. The app uses timers, scores, and structured formats. Question: what gets measured, what gets valued, and who decides?

**Visual Language** — Soviet mosaics and retro-futurist aesthetics provide visual alternatives to capitalist slickness. Bold geometry, public scale, collective themes.

**Technical Infrastructure** — IIIF demonstrates open standards and federated access. Apply these principles to cultural platforms and creative tools.

**Conference Context** — Developed for Historical Materialism Conference (Marxism, Culture & Arts / New Technologies & Capital Accumulation streams). The app itself is an intervention in how we structure creative competition.

### Design Questions to Explore

- Can a game show format be repurposed for non-competitive ends?
- What alternatives exist to winner/loser dynamics?
- How do technological affordances shape cultural participation?
- What happens when we make infrastructure choices visible and political?

See `docs/sources/` for detailed reference materials on each conceptual influence.
