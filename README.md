# BOURGEOISIE IDOL

A live web application examining competitive cultural production through a game show format. Originally forked from [SpecIdol](https://github.com/martysteer/SpecIdol) and adapted for the [Twenty-third Annual Historical Materialism Conference](https://www.historicalmaterialism.org/event/twenty-third-annual-conference/).

**Concept:** Readers present creative work, judges evaluate in real-time, audience observes. The format itself becomes a site for interrogating cultural gatekeeping, collective decision-making, and alternatives to competitive hierarchies.

**Mechanics:** Auto-scrolling text, multi-device coordination, WebSocket-based real-time state sync. Readers read aloud, judges buzz with big red buttons. Survive 2 minutes without all judges buzzing = win.

## Features

- **Multiple concurrent sessions** - run many games simultaneously
- **Auto-assign judge IDs** - judges join, get sequential numbers (1, 2, 3...)
- **Session list interface** - click to select session, no typing codes
- **Real-time WebSocket coordination** between multiple clients
- **Auto-scrolling story text** synchronized across all views
- **Judge buzzer system** with big red buttons (mobile-optimized)
- **Audience projector view** with CRT effects, judge panels, animations, sound
- **Controller interface** with story queue, round controls, import/export
- **Retro/campy aesthetic** with pixel fonts, neon colors, game show vibe
- **No build step, no framework** - pure HTML/CSS/JS + Python WebSocket server

## Quick Start

### Option 1: Docker (Recommended)

```bash
make docker   # Build Docker image
make servers  # Run container
```

**Production ports:**
- Web interface: `http://localhost` (port 80)
- WebSocket relay: `ws://localhost:8765`

To stop: `make stop`

### Option 2: Local Development (No Docker)

```bash
# Install dependencies
cd server
pip3 install -r requirements.txt
cd ..

# Start servers
make dev
```

**Development ports:**
- Web interface: `http://localhost:8000` (port 8000 - no sudo needed)
- WebSocket relay: `ws://localhost:8765`

To stop: `make dev-stop`

**Note:** Dev mode uses port 8000 to avoid requiring sudo. Docker/production uses standard port 80.

### Using the App

**1. Create a Session**
1. Open `http://localhost` in a browser
2. Click **"Create Session"** → redirects to controller
3. Note the 4-letter session code displayed

**2. Join as Judge**
1. Open `http://localhost` on mobile devices (or browser tabs)
2. Select the session from the list
3. Click **"Join as Judge"**
4. Auto-assigned sequential ID (1, 2, 3...)

**3. Join as Audience**
1. Open `http://localhost` on projector laptop
2. Select the session from the list
3. Click **"Join as Audience"**

**4. Run the Event**
In the Controller view:
1. Add stories (title + text)
2. Click story row to select
3. Click **"Start Round"**
4. Speed controls: 1x/2x/3x, play/pause
5. Judges buzz when done
6. All judges buzz → "BUZZED OUT"
7. Timer reaches limit → "SURVIVOR!"

## Architecture

- **Server**: Python WebSocket relay (`server/relay.py`) holds session state in memory
- **Clients**: Static HTML/CSS/JS (`www/`) connect via WebSocket, compute timer/scroll locally
- **No database**: Session lost on server restart (ephemeral event app)

## Import/Export Sessions

In the Controller, use the **Import/Export** panel to:
- **Export**: Copy session JSON (stories + config) to clipboard
- **Import**: Paste session JSON to pre-load stories

Example JSON:
```json
{
  "stories": [
    {"title": "Story One", "text": "Once upon a time..."},
    {"title": "Story Two", "text": "In a galaxy far away..."}
  ],
  "config": {
    "timer_duration": 120,
    "judge_count": 3
  }
}
```

## Configuration

Edit `server/relay.py` to change defaults:
- `timer_duration`: seconds (default 120 = 2:00)

Judge count is unlimited - as many judges as connect will participate.

## Deployment

See [docs/docker-deployment-plan.md](docs/docker-deployment-plan.md) for complete deployment guide.

### Quick Deploy to DigitalOcean

1. **Create Droplet** (Ubuntu 22.04, $4-6/mo)
2. **Install Docker** and clone repo
3. **Configure firewall** (ports 22, 80, 8765)
4. **Build and run**: `docker build -t specidol . && docker run -d --name specidol --restart unless-stopped -p 80:80 -p 8765:8765 specidol`
5. **Setup GitHub Actions** (optional): Add secrets, deploy with one click

Access at `http://YOUR_DROPLET_IP`

### Local Network Deployment

Run Docker on laptop connected to venue WiFi. Devices on same network access via laptop's IP.

## Browser Compatibility

- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Full support (Web Audio API works)
- **Mobile Safari/Chrome**: Optimized for portrait (judge view)

## License

Anti-Capitalist Software License v1.4

See [LICENSE](LICENSE) file for full text.

https://anticapitalist.software/

## Conceptual Framework

See `docs/sources/` for reference materials. Key influences:
- **Bourgeoisie** — class systems, social dynamics
- **Popular assembly / Citizens' assembly** — collective decision-making, direct democracy
- **Point (typography)** — measurement, precision, standardization
- **Soviet mosaics** — visual aesthetic, socialist public art
- **IIIF** — open standards, federated infrastructure
- **Socialist voting** — critique of competitive/hierarchical systems

## Credits

Forked from [SpecIdol](https://github.com/martysteer/SpecIdol) by Marty Steer.

Developed for presentation at the Twenty-third Annual Historical Materialism Conference (Marxism, Culture and the Arts / New Technologies and Capital Accumulation streams).