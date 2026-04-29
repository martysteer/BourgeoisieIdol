## Design Context

### Users
Convention-goers at speculative fiction writers' events. Four distinct roles use the app simultaneously:
- **Controller** (event organizer): Manages sessions, loads stories, controls pacing from a laptop
- **Judges** (3 editors): Buzz out readers via mobile phones with big red buttons
- **Audience**: Watches projected view on a big screen in the room
- **Readers**: Perform their stories live while auto-scrolling text plays

Context is a live event — noisy room, varying lighting, phones in hands, projector on a wall. Stakes feel real in the moment but the whole thing is tongue-in-cheek fun.

### Brand Personality
**Campy, Dramatic, Fun**

Evokes both camp game show energy AND genuine competitive tension. Think a retro TV game show host who takes everything deadly seriously while the audience laughs. The drama is real but the frame is playful. Writers should feel excited and nervous, audience should feel entertained, judges should feel powerful.

### Aesthetic Direction
**Retro terminal meets 80s game show meets arcade cabinet.**

All three references layer together:
- **80s/90s game shows**: Dramatic reveals, countdown timers, spotlight moments, over-the-top reactions
- **Arcade/retro gaming**: Pixel fonts, CRT scanlines, neon-on-black, high score energy
- **Hacker terminal**: Green-on-black, monospace, blinking cursors, raw text aesthetic

**Anti-references**: Modern SaaS (no rounded corners, no glassmorphism, no pastel gradients), corporate dashboards, anything "clean and minimal." This should feel like a found object from an alternate timeline where game shows ran on terminals.

**Theme**: Dark only. Pure black backgrounds. Neon color palette (green primary, yellow highlight, red danger, magenta accent).

### Design Principles

1. **Drama over decoration** — Every visual choice should heighten tension or payoff. If it doesn't serve the drama, cut it. Animations exist for dramatic moments (buzz, victory, defeat), not for polish.

2. **Readable at distance** — Audience view lives on a projector in a lit room. Text must be large, high-contrast, and legible from the back row. CRT effects enhance atmosphere but never compromise readability.

3. **Zero learning curve** — Judges pick up phones and buzz. Controller runs the show. No onboarding, no tooltips, no help text. The interface IS the instruction.

4. **Commit to the bit** — The retro terminal aesthetic is not a skin — it's the identity. No "tasteful" compromises. Pixel fonts, hard edges, neon glow, scanlines. If it feels too much, it's probably right.

5. **Accessible within the aesthetic** — WCAG AA contrast as baseline. Respect prefers-reduced-motion. Keyboard navigable. But accessibility serves the aesthetic, not the other way around — find solutions that maintain the retro terminal feel.

### Color Tokens
| Token | Hex | Usage |
|-------|-----|-------|
| `--neon-green` | `#0f0` | Primary, safe, active |
| `--neon-yellow` | `#ff0` | Selected, highlighted |
| `--neon-red` | `#f00` | Danger, buzzed |
| `--neon-magenta` | `#f0f` | Accent |
| `--black` | `#000` | Background |

### Typography
| Role | Font | Variable |
|------|------|----------|
| Headings/UI | Press Start 2P | `--text-display` through `--text-caption` |
| Body/Story text | Courier New, monospace | Same scale |
| Available local fonts | Degheest collection (FT88, Director, etc.) | Not yet integrated |

### Spacing & Borders
- No border-radius anywhere (hard edges intentional)
- Border widths: 2px standard, 3px emphasis
- Glow effects via box-shadow and text-shadow with neon colors
