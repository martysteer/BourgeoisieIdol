# Changelog

All notable changes to BourgeoisieIdol will be documented in this file.

## [2.0.0] - 2026-04-29

### Changed
- **Forked from SpecIdol** — BourgeoisieIdol adaptation begins
- **Project rebranding** — all references updated to BourgeoisieIdol
- **Conceptual framework** — integrated influences from class analysis, democratic assemblies, typographic systems, Soviet aesthetics, IIIF standards, and socialist critique
- **Documentation structure** — added `docs/sources/` with reference materials for each conceptual influence
- **README** — updated to reflect conference context and thematic framework
- **BOOTSTRAP** — updated to include thematic considerations in working style
- **CLAUDE.md** — expanded with detailed thematic framework and design questions

### Added
- **Reference materials** in `docs/sources/`:
  - `bourgeoisie.md` — class systems, social dynamics
  - `popular-assembly.md` — collective decision-making
  - `citizens-assembly.md` — direct democracy
  - `point-typography.md` — measurement, precision
  - `brief-visual-exploration-typography.md` — historical semantics
  - `socialist-voting.md` — sociocultural values
  - `soviet-mosaics.md` — visual aesthetic
  - `iiif.md` — technology, open standards
  - `historical-materialism-conference.md` — conference context

---

# SpecIdol Changelog (pre-fork)

## [Unreleased]

### Added
- **Consistent headers** across judge, audience, and controller pages:
  - Left side: page label (WATCHING/JUDGING/CONTROLLING) in green + session stats
  - Right side: contextual info in yellow (story title, judge name, selected story)
  - Waiting/active color states (muted brown-yellow → bright yellow with glow)
  - Mobile stacking at ≤900px
- **Live session stats** on judge and audience pages (code, stories, judges, audience count via WebSocket)
- **Full-width horizontal lines** replacing box borders on all content sections
- **Design improvements** from comprehensive design critique:
  - Systematic typography scale (5 levels: 3rem → 0.75rem)
  - Controller layout restructured with clear primary/secondary/tertiary hierarchy
  - Empty states with progressive onboarding (story management auto-expands when queue empty)
  - Judge social awareness (connected count, buzz status indicators with animations)
  - Session list 2-column responsive grid layout for better scalability
- **History enhancements**:
  - Copy JSON button to export round history to clipboard
  - Story titles now included in history entries
- **Round controls improvements**:
  - Story selection blocked during active rounds (running/paused)
  - Round controls merged into selected-story-display box (unified yellow container)
  - Visual feedback when story selection disabled
- **Join as Controller button** on session join page - rejoin existing sessions as controller
- **Session control panel** in controller interface:
  - Eject Judges button - disconnects all judges with confirmation
  - Shutdown Audience button - disconnects all audience screens with confirmation
  - Delete Session button - removes session and ejects all clients with confirmation
  - Judge count and audience count display
- **Makefile improvements**:
  - `make help` - show all available commands (default target)
  - `make docker` - build Docker image (renamed from `make build`)
  - `make clean` - stop and remove container and image
- **GitHub Actions workflow** - manual deployment to DigitalOcean Droplet
- **Deployment documentation** - complete guide in `docs/docker-deployment-plan.md`
- **Para-critique essay** - `docs/para-critique-acsl-specidol.md` discussing ACSL licensing and AI co-authorship

### Changed
- **Controller CSS refactored** — removed body padding so borders go edge-to-edge, removed redundant form element overrides, scoped management-content selectors
- **`.page-scrollable`** no longer adds body padding — sections handle their own horizontal padding
- **Port standardization**:
  - Production (Docker): Port 80 for web, 8765 for WebSocket
  - Development (`make dev`): Port 8000 for web, 8765 for WebSocket (no sudo required)
- **WebSocket connection fix**: Production mode now correctly connects to port 8765
- **Docker architecture**: Single Dockerfile with nginx + relay via supervisord (no docker-compose)
- **Session info layout**: Redesigned controller header with three-column grid layout
- **Session stats**: Unified display across join page and controller (stories | judges | audience)

### Fixed
- Port 8765 already in use handling in `make dev-stop`
- WebSocket connection in production (was trying to connect to HTTP port instead of 8765)
- Dockerfile EXPOSE declarations now match actual ports
- All deployment documentation updated with correct ports
- `updateStory` text loss bug
- Story update in place without changing queue order

### Security
- Firewall configuration documented for ports 22, 80, 8765
- Controller-only authentication for session deletion commands

## [1.0.0] - 2026-04-18

Initial release of SpecIdol - Pop Idol for speculative fiction writers at conventions.

### Features
- Real-time WebSocket coordination between controller, judges, and audience
- Multiple concurrent sessions with 4-letter session codes
- Auto-assign judge IDs (sequential: 1, 2, 3...)
- Auto-scrolling story text synchronized across all clients
- Judge buzzer system with big red buttons
- Audience projector view with CRT effects and animations
- Controller interface with story queue management
- Import/Export session functionality
- Dynamic judge indicators (panels generated from connected judges)
- UI refinements: two-column controller layout, session list grid, collapsible sections
- Retro/campy game show aesthetic
- No build step, no framework - pure HTML/CSS/JS + Python WebSocket server

### License
Licensed under Anti-Capitalist Software License v1.4
