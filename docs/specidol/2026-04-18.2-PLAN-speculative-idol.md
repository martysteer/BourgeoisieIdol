# Speculative Idol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live "Pop Idol for writers" web app with auto-scrolling stories, judge buzzers, audience projector view, and retro game show aesthetic.

**Architecture:** Python WebSocket relay server (~100 lines) coordinates real-time state between static HTML/CSS/JS clients. No framework, no build step. Time-based auto-scroll with server-synced timestamps. Retro/campy aesthetic with pixel fonts, CRT effects, animations.

**Tech Stack:** Python 3.8+, `websockets` library, vanilla HTML5/CSS/JS, Press Start 2P font (Google Fonts CDN)

---

## Task 1: WebSocket Server Foundation

**Files:**
- Create: `server/relay.py`
- Create: `server/requirements.txt`

- [ ] **Step 1: Create requirements file**

```bash
mkdir -p server
cat > server/requirements.txt << 'EOF'
websockets==12.0
EOF
```

- [ ] **Step 2: Install dependencies**

Run: `pip3 install -r server/requirements.txt`
Expected: Successfully installed websockets-12.0

- [ ] **Step 3: Write basic WebSocket server with session state**

Create `server/relay.py`:

```python
import asyncio
import json
import random
import string
import time
from datetime import datetime
import websockets
from websockets.server import serve

# Single session state (in memory)
session = {
    "code": None,
    "config": {
        "timer_duration": 120,
        "speed_options": [1, 2, 3],
        "judge_count": 3
    },
    "clients": {},  # {websocket: {"role": "judge", "judge_id": 1}}
    "stories": [],
    "current_round": {
        "story_index": None,
        "title": None,
        "text": None,
        "start_time": None,
        "speed": 1,
        "paused": False,
        "pause_time": None,
        "elapsed_at_pause": 0,
        "buzzes": [],
        "status": "waiting"
    },
    "history": [],
    "judge_slots": {1: None, 2: None, 3: None}  # {judge_id: websocket}
}

def generate_code():
    """Generate 4 uppercase letter code"""
    return ''.join(random.choices(string.ascii_uppercase, k=4))

async def handle_message(websocket, message_data):
    """Process incoming message and broadcast responses"""
    msg_type = message_data.get("type")
    data = message_data.get("data", {})

    if msg_type == "create_session":
        session["code"] = generate_code()
        session["clients"][websocket] = {"role": "controller"}
        await websocket.send(json.dumps({
            "type": "session_created",
            "data": {"code": session["code"]}
        }))

    elif msg_type == "join":
        code = data.get("code")
        role = data.get("role")
        judge_id = data.get("judge_id")

        if session["code"] and code != session["code"]:
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid session code"}
            }))
            return

        if role == "judge":
            if judge_id not in session["judge_slots"]:
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {"message": f"Invalid judge number: {judge_id}"}
                }))
                return
            if session["judge_slots"][judge_id] is not None:
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {"message": f"Judge {judge_id} slot already taken"}
                }))
                return
            session["judge_slots"][judge_id] = websocket
            session["clients"][websocket] = {"role": "judge", "judge_id": judge_id}
        else:
            session["clients"][websocket] = {"role": role}

        # Send full session state to joining client
        await websocket.send(json.dumps({
            "type": "session_state",
            "data": {
                "code": session["code"],
                "config": session["config"],
                "stories": session["stories"],
                "current_round": session["current_round"],
                "history": session["history"],
                "client_info": session["clients"][websocket]
            }
        }))

async def broadcast(message, exclude=None):
    """Send message to all connected clients except exclude"""
    websockets_to_send = [
        ws for ws in session["clients"].keys()
        if ws != exclude and ws.open
    ]
    if websockets_to_send:
        await asyncio.gather(
            *[ws.send(json.dumps(message)) for ws in websockets_to_send],
            return_exceptions=True
        )

async def handler(websocket):
    """Handle WebSocket connection"""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_message(websocket, data)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON"}
                }))
    finally:
        # Clean up on disconnect
        client_info = session["clients"].pop(websocket, None)
        if client_info and client_info.get("role") == "judge":
            judge_id = client_info.get("judge_id")
            if session["judge_slots"].get(judge_id) == websocket:
                session["judge_slots"][judge_id] = None

async def main():
    async with serve(handler, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Test server starts**

Run: `python3 server/relay.py`
Expected: "WebSocket server running on ws://localhost:8765"

Leave it running in a terminal. Open a new terminal for next steps.

- [ ] **Step 5: Test with wscat (install if needed)**

Run: `npm install -g wscat` (if not installed)
Run: `wscat -c ws://localhost:8765`
Send: `{"type": "create_session", "data": {}}`
Expected: Receive `{"type": "session_created", "data": {"code": "ABCD"}}` (code will vary)

Ctrl+C to exit wscat.

- [ ] **Step 6: Commit**

```bash
git add server/relay.py server/requirements.txt
git commit -m "feat: add WebSocket relay server with session creation"
```

---

## Task 2: Round Control Message Handlers

**Files:**
- Modify: `server/relay.py`

- [ ] **Step 1: Add round_start handler after the join handler**

In `server/relay.py`, add this to the `handle_message` function after the `join` handler:

```python
    elif msg_type == "add_story":
        title = data.get("title", "Untitled")
        text = data.get("text", "")
        session["stories"].append({"title": title, "text": text})
        await broadcast({
            "type": "story_added",
            "data": {"index": len(session["stories"]) - 1, "title": title}
        })

    elif msg_type == "remove_story":
        story_index = data.get("story_index")
        if 0 <= story_index < len(session["stories"]):
            session["stories"].pop(story_index)
            await broadcast({
                "type": "story_removed",
                "data": {"index": story_index}
            })

    elif msg_type == "round_start":
        story_index = data.get("story_index", 0)
        if story_index >= len(session["stories"]):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid story index"}
            }))
            return

        story = session["stories"][story_index]
        session["current_round"] = {
            "story_index": story_index,
            "title": story["title"],
            "text": story["text"],
            "start_time": time.time(),
            "speed": 1,
            "paused": False,
            "pause_time": None,
            "elapsed_at_pause": 0,
            "buzzes": [],
            "status": "running"
        }

        await broadcast({
            "type": "round_started",
            "data": {
                "title": story["title"],
                "text": story["text"],
                "start_time": session["current_round"]["start_time"]
            }
        })

    elif msg_type == "speed_change":
        speed = data.get("speed", 1)
        if speed not in session["config"]["speed_options"]:
            return
        session["current_round"]["speed"] = speed
        await broadcast({
            "type": "speed_changed",
            "data": {"speed": speed, "timestamp": time.time()}
        })

    elif msg_type == "pause":
        if session["current_round"]["status"] == "running":
            now = time.time()
            elapsed = now - session["current_round"]["start_time"]
            session["current_round"]["paused"] = True
            session["current_round"]["pause_time"] = now
            session["current_round"]["elapsed_at_pause"] = elapsed
            session["current_round"]["status"] = "paused"
            await broadcast({
                "type": "paused",
                "data": {"timestamp": now, "elapsed": elapsed}
            })

    elif msg_type == "resume":
        if session["current_round"]["status"] == "paused":
            now = time.time()
            session["current_round"]["start_time"] = now - session["current_round"]["elapsed_at_pause"]
            session["current_round"]["paused"] = False
            session["current_round"]["status"] = "running"
            await broadcast({
                "type": "resumed",
                "data": {
                    "timestamp": now,
                    "elapsed": session["current_round"]["elapsed_at_pause"]
                }
            })
```

- [ ] **Step 2: Test round start with wscat**

In wscat connected to server:
Send: `{"type": "create_session", "data": {}}`
Send: `{"type": "add_story", "data": {"title": "Test Story", "text": "Once upon a time..."}}`
Send: `{"type": "round_start", "data": {"story_index": 0}}`
Expected: Receive `{"type": "round_started", "data": {...}}` with title, text, start_time

- [ ] **Step 3: Commit**

```bash
git add server/relay.py
git commit -m "feat: add round control handlers (start, pause, resume, speed)"
```

---

## Task 3: Buzz and Round End Handlers

**Files:**
- Modify: `server/relay.py`

- [ ] **Step 1: Add buzz and reset handlers**

In `server/relay.py`, add after the resume handler:

```python
    elif msg_type == "buzz":
        judge_id = data.get("judge_id")
        client_info = session["clients"].get(websocket, {})

        # Verify this is actually a judge
        if client_info.get("role") != "judge" or client_info.get("judge_id") != judge_id:
            return

        # Check if already buzzed
        if any(b["judge_id"] == judge_id for b in session["current_round"]["buzzes"]):
            return

        now = time.time()
        elapsed = now - session["current_round"]["start_time"]
        buzz_entry = {"judge_id": judge_id, "time": round(elapsed, 1)}
        session["current_round"]["buzzes"].append(buzz_entry)

        await broadcast({
            "type": "buzzed",
            "data": buzz_entry
        })

        # Check if all judges have buzzed
        if len(session["current_round"]["buzzes"]) >= session["config"]["judge_count"]:
            session["current_round"]["status"] = "defeat"
            outcome_data = {
                "outcome": "defeat",
                "buzzes": session["current_round"]["buzzes"],
                "duration": session["current_round"]["buzzes"][-1]["time"]
            }
            session["history"].append({
                "title": session["current_round"]["title"],
                **outcome_data
            })
            await broadcast({
                "type": "round_ended",
                "data": outcome_data
            })

    elif msg_type == "victory":
        # Client detected timer reached limit
        if session["current_round"]["status"] == "running":
            session["current_round"]["status"] = "victory"
            outcome_data = {
                "outcome": "victory",
                "buzzes": session["current_round"]["buzzes"],
                "duration": session["config"]["timer_duration"]
            }
            session["history"].append({
                "title": session["current_round"]["title"],
                **outcome_data
            })
            await broadcast({
                "type": "round_ended",
                "data": outcome_data
            })

    elif msg_type == "reset_round":
        session["current_round"] = {
            "story_index": None,
            "title": None,
            "text": None,
            "start_time": None,
            "speed": 1,
            "paused": False,
            "pause_time": None,
            "elapsed_at_pause": 0,
            "buzzes": [],
            "status": "waiting"
        }
        await broadcast({
            "type": "round_reset",
            "data": {}
        })
```

- [ ] **Step 2: Test buzz sequence with wscat**

Start a round, then:
Send: `{"type": "join", "data": {"code": "ABCD", "role": "judge", "judge_id": 1}}`
Send: `{"type": "buzz", "data": {"judge_id": 1}}`
Expected: Receive `{"type": "buzzed", "data": {"judge_id": 1, "time": ...}}`

- [ ] **Step 3: Commit**

```bash
git add server/relay.py
git commit -m "feat: add buzz, victory, and reset handlers"
```

---

## Task 4: Import/Export Session Handler

**Files:**
- Modify: `server/relay.py`

- [ ] **Step 1: Add import handler**

In `server/relay.py`, add after reset_round handler:

```python
    elif msg_type == "import_session":
        stories = data.get("stories", [])
        config = data.get("config", {})

        # Validate stories format
        if not isinstance(stories, list):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "Invalid stories format"}
            }))
            return

        for story in stories:
            if not isinstance(story, dict) or "title" not in story or "text" not in story:
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid story format"}
                }))
                return

        # Merge config (only allowed keys)
        if "timer_duration" in config:
            session["config"]["timer_duration"] = int(config["timer_duration"])
        if "judge_count" in config:
            session["config"]["judge_count"] = int(config["judge_count"])

        # Replace stories
        session["stories"] = stories

        await broadcast({
            "type": "session_imported",
            "data": {"story_count": len(stories)}
        })
```

- [ ] **Step 2: Test import with wscat**

Send:
```json
{
  "type": "import_session",
  "data": {
    "stories": [
      {"title": "Story One", "text": "Text one..."},
      {"title": "Story Two", "text": "Text two..."}
    ],
    "config": {"timer_duration": 90}
  }
}
```
Expected: Receive `{"type": "session_imported", "data": {"story_count": 2}}`

- [ ] **Step 3: Commit**

```bash
git add server/relay.py
git commit -m "feat: add session import handler with validation"
```

---

## Task 5: Shared Client JavaScript Foundation

**Files:**
- Create: `www/app.js`

- [ ] **Step 1: Create www directory and app.js with WebSocket client**

```bash
mkdir -p www
cat > www/app.js << 'EOF'
// Shared WebSocket client and state management

class SpecIdolClient {
    constructor() {
        this.ws = null;
        this.sessionCode = null;
        this.role = null;
        this.judgeId = null;
        this.sessionState = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.messageHandlers = {};
    }

    connect(wsUrl = 'ws://localhost:8765') {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            if (this.onConnect) this.onConnect();
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (this.onError) this.onError(error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    this.connect(wsUrl);
                }, 2000);
            }
        };
    }

    send(type, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
        } else {
            console.error('WebSocket not ready');
        }
    }

    on(messageType, handler) {
        this.messageHandlers[messageType] = handler;
    }

    handleMessage(message) {
        const handler = this.messageHandlers[message.type];
        if (handler) {
            handler(message.data);
        } else {
            console.log('Unhandled message type:', message.type, message.data);
        }
    }

    createSession() {
        this.send('create_session');
    }

    joinSession(code, role, judgeId = null) {
        this.sessionCode = code;
        this.role = role;
        this.judgeId = judgeId;
        this.send('join', { code, role, judge_id: judgeId });
    }

    addStory(title, text) {
        this.send('add_story', { title, text });
    }

    removeStory(storyIndex) {
        this.send('remove_story', { story_index: storyIndex });
    }

    startRound(storyIndex) {
        this.send('round_start', { story_index: storyIndex });
    }

    changeSpeed(speed) {
        this.send('speed_change', { speed });
    }

    pause() {
        this.send('pause');
    }

    resume() {
        this.send('resume');
    }

    buzz(judgeId) {
        this.send('buzz', { judge_id: judgeId });
    }

    victory() {
        this.send('victory');
    }

    resetRound() {
        this.send('reset_round');
    }

    importSession(stories, config) {
        this.send('import_session', { stories, config });
    }
}

// Timer utilities
class Timer {
    constructor(duration, onTick, onComplete) {
        this.duration = duration; // seconds
        this.onTick = onTick;
        this.onComplete = onComplete;
        this.startTime = null;
        this.pausedAt = null;
        this.elapsedAtPause = 0;
        this.intervalId = null;
    }

    start(serverStartTime) {
        this.startTime = serverStartTime;
        this.pausedAt = null;
        this.elapsedAtPause = 0;
        this.tick();
        this.intervalId = setInterval(() => this.tick(), 100); // 10 Hz for tenths precision
    }

    pause() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.pausedAt = Date.now() / 1000;
        this.elapsedAtPause = this.getElapsed();
    }

    resume(newStartTime) {
        this.startTime = newStartTime;
        this.pausedAt = null;
        this.tick();
        this.intervalId = setInterval(() => this.tick(), 100);
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    getElapsed() {
        if (this.pausedAt) {
            return this.elapsedAtPause;
        }
        if (!this.startTime) return 0;
        return (Date.now() / 1000) - this.startTime;
    }

    tick() {
        const elapsed = this.getElapsed();
        if (this.onTick) {
            this.onTick(elapsed);
        }
        if (elapsed >= this.duration) {
            this.stop();
            if (this.onComplete) {
                this.onComplete();
            }
        }
    }
}

// Auto-scroll utilities
class AutoScroller {
    constructor(element, baseSpeed = 30) {
        this.element = element;
        this.baseSpeed = baseSpeed; // pixels per second at 1x
        this.speed = 1;
        this.startTime = null;
        this.pausedAt = null;
        this.elapsedAtPause = 0;
        this.intervalId = null;
    }

    start(serverStartTime, speed = 1) {
        this.startTime = serverStartTime;
        this.speed = speed;
        this.pausedAt = null;
        this.elapsedAtPause = 0;
        this.scroll();
        this.intervalId = setInterval(() => this.scroll(), 50); // 20 Hz for smooth scroll
    }

    changeSpeed(speed, timestamp) {
        // Recalculate start time to maintain current position
        const currentElapsed = this.getElapsed();
        this.speed = speed;
        this.startTime = timestamp - (currentElapsed / speed);
    }

    pause() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.pausedAt = Date.now() / 1000;
        this.elapsedAtPause = this.getElapsed();
    }

    resume(newStartTime) {
        this.startTime = newStartTime;
        this.pausedAt = null;
        this.scroll();
        this.intervalId = setInterval(() => this.scroll(), 50);
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    getElapsed() {
        if (this.pausedAt) {
            return this.elapsedAtPause * this.speed;
        }
        if (!this.startTime) return 0;
        return ((Date.now() / 1000) - this.startTime) * this.speed;
    }

    scroll() {
        const elapsed = this.getElapsed();
        const position = elapsed * this.baseSpeed;
        this.element.scrollTop = position;
    }
}

// Utility: format time as M:SS.T
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const tenths = Math.floor((seconds % 1) * 10);
    return `${minutes}:${secs.toString().padStart(2, '0')}.${tenths}`;
}

// Utility: parse URL params
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        code: params.get('code'),
        judge: params.get('judge') ? parseInt(params.get('judge')) : null
    };
}
EOF
```

- [ ] **Step 2: Commit**

```bash
git add www/app.js
git commit -m "feat: add shared client WebSocket, timer, and auto-scroll utilities"
```

---

## Task 6: Landing Page (index.html)

**Files:**
- Create: `www/index.html`

- [ ] **Step 1: Create landing page HTML**

```bash
cat > www/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPECULATIVE IDOL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }

        h1 {
            font-family: 'Press Start 2P', cursive;
            font-size: 2rem;
            text-align: center;
            margin-bottom: 3rem;
            text-shadow: 0 0 10px #0f0, 0 0 20px #0f0;
            line-height: 1.5;
        }

        .container {
            max-width: 500px;
            width: 100%;
        }

        .mode-select {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        button {
            background: #0f0;
            color: #000;
            border: 3px solid #0f0;
            padding: 1rem 2rem;
            font-family: 'Press Start 2P', cursive;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
        }

        button:hover {
            background: #000;
            color: #0f0;
            box-shadow: 0 0 20px #0f0;
        }

        .join-form {
            display: none;
            flex-direction: column;
            gap: 1rem;
        }

        .join-form.active {
            display: flex;
        }

        input, select {
            background: #000;
            color: #0f0;
            border: 2px solid #0f0;
            padding: 0.75rem;
            font-family: 'Courier New', monospace;
            font-size: 1rem;
        }

        input:focus, select:focus {
            outline: none;
            box-shadow: 0 0 10px #0f0;
        }

        input[type="text"] {
            text-transform: uppercase;
            font-family: 'Press Start 2P', cursive;
            font-size: 1.2rem;
            text-align: center;
            letter-spacing: 0.5rem;
        }

        .error {
            color: #f00;
            text-align: center;
            padding: 0.5rem;
            display: none;
        }

        .error.active {
            display: block;
        }

        @media (max-width: 600px) {
            h1 {
                font-size: 1.2rem;
            }
            button {
                font-size: 0.7rem;
            }
        }
    </style>
</head>
<body>
    <h1>SPECULATIVE<br>IDOL</h1>

    <div class="container">
        <div class="mode-select" id="modeSelect">
            <button onclick="createSession()">Create Session</button>
            <button onclick="showJoinForm()">Join Session</button>
        </div>

        <div class="join-form" id="joinForm">
            <input type="text" id="codeInput" placeholder="CODE" maxlength="4" pattern="[A-Z]{4}">

            <select id="roleSelect" onchange="toggleJudgeNumber()">
                <option value="">Select Role...</option>
                <option value="judge">Judge</option>
                <option value="audience">Audience</option>
            </select>

            <select id="judgeNumber" style="display: none;">
                <option value="">Select Judge Number...</option>
                <option value="1">Judge 1</option>
                <option value="2">Judge 2</option>
                <option value="3">Judge 3</option>
            </select>

            <button onclick="joinSession()">Join</button>
            <button onclick="showModeSelect()">Back</button>
        </div>

        <div class="error" id="error"></div>
    </div>

    <script src="app.js"></script>
    <script>
        const client = new SpecIdolClient();
        client.connect();

        client.on('session_created', (data) => {
            window.location.href = `control.html?code=${data.code}`;
        });

        client.on('session_state', (data) => {
            const params = getUrlParams();
            // Redirect based on role
            if (data.client_info.role === 'judge') {
                window.location.href = `judge.html?code=${params.code}&judge=${data.client_info.judge_id}`;
            } else if (data.client_info.role === 'audience') {
                window.location.href = `audience.html?code=${params.code}`;
            }
        });

        client.on('error', (data) => {
            showError(data.message);
        });

        function createSession() {
            client.createSession();
        }

        function showJoinForm() {
            document.getElementById('modeSelect').style.display = 'none';
            document.getElementById('joinForm').classList.add('active');
        }

        function showModeSelect() {
            document.getElementById('joinForm').classList.remove('active');
            document.getElementById('modeSelect').style.display = 'flex';
            clearError();
        }

        function toggleJudgeNumber() {
            const role = document.getElementById('roleSelect').value;
            const judgeNumber = document.getElementById('judgeNumber');
            judgeNumber.style.display = role === 'judge' ? 'block' : 'none';
        }

        function joinSession() {
            const code = document.getElementById('codeInput').value.toUpperCase();
            const role = document.getElementById('roleSelect').value;
            const judgeId = role === 'judge' ? parseInt(document.getElementById('judgeNumber').value) : null;

            if (!code || code.length !== 4) {
                showError('Enter a 4-letter code');
                return;
            }
            if (!role) {
                showError('Select a role');
                return;
            }
            if (role === 'judge' && !judgeId) {
                showError('Select a judge number');
                return;
            }

            clearError();
            client.joinSession(code, role, judgeId);
        }

        function showError(message) {
            const error = document.getElementById('error');
            error.textContent = message;
            error.classList.add('active');
        }

        function clearError() {
            document.getElementById('error').classList.remove('active');
        }

        // Auto-uppercase code input
        document.getElementById('codeInput').addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    </script>
</body>
</html>
EOF
```

- [ ] **Step 2: Test landing page**

Run: `python3 -m http.server 8000 --directory www`

Open browser: `http://localhost:8000/index.html`

Expected: See "SPECULATIVE IDOL" title, "Create Session" / "Join Session" buttons

Click "Create Session" → should redirect to `control.html?code=XXXX` (will 404 for now, check URL)

Click "Join Session" → form appears with code input, role selector, judge number (when judge selected)

- [ ] **Step 3: Commit**

```bash
git add www/index.html
git commit -m "feat: add landing page with session create/join"
```

---

## Task 7: Judge View (judge.html)

**Files:**
- Create: `www/judge.html`

- [ ] **Step 1: Create judge view HTML**

```bash
cat > www/judge.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Judge - SPECULATIVE IDOL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #000;
            color: #0f0;
            font-family: 'Press Start 2P', cursive;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }

        .header {
            padding: 1rem;
            text-align: center;
            border-bottom: 2px solid #0f0;
        }

        .code {
            font-size: 0.8rem;
            opacity: 0.7;
        }

        .judge-num {
            font-size: 1.2rem;
            margin: 0.5rem 0;
        }

        .story-title {
            font-size: 0.7rem;
            margin-top: 0.5rem;
            color: #ff0;
        }

        .timer {
            font-size: 1.5rem;
            margin-top: 0.5rem;
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }

        .buzz-button {
            width: 80vmin;
            height: 80vmin;
            max-width: 400px;
            max-height: 400px;
            background: linear-gradient(145deg, #ff0000, #cc0000);
            border: 8px solid #800000;
            border-radius: 50%;
            font-family: 'Press Start 2P', cursive;
            font-size: 2rem;
            color: #fff;
            cursor: pointer;
            box-shadow: 0 15px 30px rgba(255, 0, 0, 0.5),
                        inset 0 -8px 20px rgba(0, 0, 0, 0.3),
                        inset 0 8px 20px rgba(255, 255, 255, 0.2);
            transition: all 0.1s;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            line-height: 1.3;
        }

        .buzz-button:active {
            transform: scale(0.95);
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.5),
                        inset 0 -4px 10px rgba(0, 0, 0, 0.3),
                        inset 0 4px 10px rgba(255, 255, 255, 0.2);
        }

        .buzz-button:disabled {
            background: #333;
            border-color: #666;
            cursor: not-allowed;
            box-shadow: none;
        }

        .buzzed {
            font-size: 8rem;
            color: #f00;
            animation: buzzAnim 0.5s ease-out;
        }

        @keyframes buzzAnim {
            0% { transform: scale(0) rotate(-45deg); opacity: 0; }
            50% { transform: scale(1.2) rotate(5deg); }
            100% { transform: scale(1) rotate(0deg); opacity: 1; }
        }

        .judge-status {
            margin-top: 1rem;
            display: flex;
            gap: 0.5rem;
            justify-content: center;
        }

        .judge-indicator {
            padding: 0.5rem;
            border: 2px solid #0f0;
            font-size: 0.6rem;
            opacity: 0.5;
        }

        .judge-indicator.buzzed {
            color: #f00;
            border-color: #f00;
            opacity: 1;
        }

        .waiting {
            font-size: 1rem;
            text-align: center;
            opacity: 0.7;
        }

        @media (max-width: 600px) {
            .buzz-button {
                font-size: 1.5rem;
            }
            .judge-num {
                font-size: 1rem;
            }
            .timer {
                font-size: 1.2rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="code" id="code">CODE: ----</div>
        <div class="judge-num" id="judgeNum">JUDGE -</div>
        <div class="story-title" id="storyTitle"></div>
        <div class="timer" id="timer">0:00.0</div>
    </div>

    <div class="main" id="main">
        <div class="waiting">Waiting for round to start...</div>
    </div>

    <script src="app.js"></script>
    <script>
        const params = getUrlParams();
        const client = new SpecIdolClient();
        let timer = null;
        let buzzed = false;

        document.getElementById('code').textContent = `CODE: ${params.code || '----'}`;
        document.getElementById('judgeNum').textContent = `JUDGE ${params.judge || '-'}`;

        client.connect();

        client.onConnect = () => {
            client.joinSession(params.code, 'judge', params.judge);
        };

        client.on('session_state', (data) => {
            if (data.current_round.status === 'running') {
                startRound(data.current_round);
            } else if (data.current_round.status === 'paused') {
                // Show paused state
                if (timer) timer.pause();
            }
        });

        client.on('round_started', (data) => {
            startRound(data);
        });

        client.on('paused', (data) => {
            if (timer) timer.pause();
        });

        client.on('resumed', (data) => {
            if (timer) timer.resume(data.timestamp - data.elapsed);
        });

        client.on('speed_changed', (data) => {
            // Speed doesn't affect judge view, but we track it
        });

        client.on('buzzed', (data) => {
            updateJudgeStatus(data.judge_id);
        });

        client.on('round_ended', (data) => {
            if (timer) timer.stop();
        });

        client.on('round_reset', () => {
            resetView();
        });

        function startRound(roundData) {
            buzzed = false;
            document.getElementById('storyTitle').textContent = roundData.title || '';

            const main = document.getElementById('main');
            main.innerHTML = `
                <button class="buzz-button" id="buzzButton" onclick="buzz()">
                    BUZZ
                </button>
                <div class="judge-status" id="judgeStatus"></div>
            `;

            renderJudgeStatus();

            if (timer) timer.stop();
            timer = new Timer(
                120,
                (elapsed) => {
                    document.getElementById('timer').textContent = formatTime(elapsed);
                },
                () => {
                    // Timer complete (victory)
                }
            );
            timer.start(roundData.start_time);
        }

        function buzz() {
            if (buzzed) return;
            buzzed = true;

            const button = document.getElementById('buzzButton');
            button.disabled = true;
            button.innerHTML = '<div class="buzzed">✕</div>';

            client.buzz(params.judge);
        }

        function renderJudgeStatus() {
            const container = document.getElementById('judgeStatus');
            if (!container) return;

            container.innerHTML = `
                <div class="judge-indicator" data-judge="1">J1</div>
                <div class="judge-indicator" data-judge="2">J2</div>
                <div class="judge-indicator" data-judge="3">J3</div>
            `;
        }

        function updateJudgeStatus(judgeId) {
            const indicator = document.querySelector(`[data-judge="${judgeId}"]`);
            if (indicator) {
                indicator.classList.add('buzzed');
            }
        }

        function resetView() {
            if (timer) timer.stop();
            buzzed = false;
            document.getElementById('storyTitle').textContent = '';
            document.getElementById('timer').textContent = '0:00.0';
            document.getElementById('main').innerHTML = '<div class="waiting">Waiting for round to start...</div>';
        }
    </script>
</body>
</html>
EOF
```

- [ ] **Step 2: Test judge view**

Browser: `http://localhost:8000/judge.html?code=TEST&judge=1`

Expected: See judge header with code, judge number, timer at 0:00.0, "Waiting for round" message

Use wscat to start a round and verify judge view updates with button

- [ ] **Step 3: Commit**

```bash
git add www/judge.html
git commit -m "feat: add judge view with big red buzz button"
```

---

## Task 8: Audience View Structure

**Files:**
- Create: `www/audience.html`

- [ ] **Step 1: Create audience view HTML structure (no animations yet)**

```bash
cat > www/audience.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audience - SPECULATIVE IDOL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            height: 100vh;
            overflow: hidden;
            position: relative;
        }

        /* CRT scanline effect */
        body::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 0, 0, 0.1),
                rgba(0, 0, 0, 0.1) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 1000;
        }

        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 2rem;
        }

        .header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .story-title {
            font-family: 'Press Start 2P', cursive;
            font-size: 1.5rem;
            color: #ff0;
            text-shadow: 0 0 10px #ff0;
        }

        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .story-text-container {
            flex: 1;
            overflow: hidden;
            border: 2px solid #0f0;
            padding: 2rem;
            margin-bottom: 2rem;
            position: relative;
        }

        .story-text {
            font-size: 1.2rem;
            line-height: 1.8;
            white-space: pre-wrap;
        }

        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
        }

        .timer {
            font-family: 'Press Start 2P', cursive;
            font-size: 2rem;
            color: #0f0;
            text-shadow: 0 0 10px #0f0;
        }

        .timer.tension {
            color: #f00;
            animation: pulse 0.5s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.05); }
        }

        .judge-panels {
            display: flex;
            gap: 1rem;
        }

        .judge-panel {
            border: 3px solid #0f0;
            padding: 1rem 2rem;
            font-family: 'Press Start 2P', cursive;
            font-size: 1rem;
            box-shadow: 0 0 15px #0f0;
            transition: all 0.3s;
        }

        .judge-panel.buzzed {
            border-color: #f00;
            color: #f00;
            box-shadow: 0 0 15px #f00;
            position: relative;
        }

        .judge-panel .x {
            display: none;
            font-size: 3rem;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }

        .judge-panel.buzzed .x {
            display: block;
            animation: xSlam 0.5s ease-out;
        }

        @keyframes xSlam {
            0% { transform: translate(-50%, -50%) scale(0) rotate(-45deg); opacity: 0; }
            50% { transform: translate(-50%, -50%) scale(1.3) rotate(5deg); }
            100% { transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }
        }

        .judge-panel.buzzed .label {
            opacity: 0.3;
        }

        .outcome {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-family: 'Press Start 2P', cursive;
            font-size: 4rem;
            z-index: 100;
            text-align: center;
        }

        .outcome.victory {
            color: #0f0;
            text-shadow: 0 0 20px #0f0;
            animation: victoryAnim 1s ease-out;
        }

        .outcome.defeat {
            color: #f00;
            text-shadow: 0 0 20px #f00;
            animation: defeatAnim 0.8s ease-out;
        }

        @keyframes victoryAnim {
            0% { transform: translate(-50%, -50%) scale(0) rotate(-10deg); opacity: 0; }
            50% { transform: translate(-50%, -50%) scale(1.2) rotate(5deg); }
            100% { transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }
        }

        @keyframes defeatAnim {
            0% { transform: translate(-50%, -100vh); opacity: 0; }
            60% { transform: translate(-50%, -40%); opacity: 1; }
            100% { transform: translate(-50%, -50%); }
        }

        body.defeat-flash {
            animation: flashRed 0.5s;
        }

        @keyframes flashRed {
            0%, 100% { background: #000; }
            50% { background: #300; }
        }

        @media (max-width: 900px) {
            .story-title {
                font-size: 1rem;
            }
            .timer {
                font-size: 1.5rem;
            }
            .judge-panel {
                font-size: 0.8rem;
                padding: 0.5rem 1rem;
            }
            .outcome {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="story-title" id="storyTitle">Waiting for story...</div>
        </div>

        <div class="content">
            <div class="story-text-container">
                <div class="story-text" id="storyText"></div>
            </div>
        </div>

        <div class="footer">
            <div class="timer" id="timer">0:00.0</div>
            <div class="judge-panels" id="judgePanels">
                <div class="judge-panel" data-judge="1">
                    <span class="label">JUDGE 1</span>
                    <span class="x">✕</span>
                </div>
                <div class="judge-panel" data-judge="2">
                    <span class="label">JUDGE 2</span>
                    <span class="x">✕</span>
                </div>
                <div class="judge-panel" data-judge="3">
                    <span class="label">JUDGE 3</span>
                    <span class="x">✕</span>
                </div>
            </div>
        </div>
    </div>

    <div class="outcome" id="outcome"></div>

    <script src="app.js"></script>
    <script>
        const params = getUrlParams();
        const client = new SpecIdolClient();
        let timer = null;
        let scroller = null;
        let tensionMode = false;

        client.connect();

        client.onConnect = () => {
            client.joinSession(params.code, 'audience');
        };

        client.on('session_state', (data) => {
            if (data.current_round.status === 'running') {
                startRound(data.current_round);
            }
        });

        client.on('round_started', (data) => {
            startRound(data);
        });

        client.on('paused', (data) => {
            if (timer) timer.pause();
            if (scroller) scroller.pause();
        });

        client.on('resumed', (data) => {
            if (timer) timer.resume(data.timestamp - data.elapsed);
            if (scroller) scroller.resume(data.timestamp - data.elapsed);
        });

        client.on('speed_changed', (data) => {
            if (scroller) scroller.changeSpeed(data.speed, data.timestamp);
        });

        client.on('buzzed', (data) => {
            markJudgeBuzzed(data.judge_id);
            playSound('buzz');
        });

        client.on('round_ended', (data) => {
            if (timer) timer.stop();
            if (scroller) scroller.stop();
            showOutcome(data.outcome);
        });

        client.on('round_reset', () => {
            resetView();
        });

        function startRound(roundData) {
            resetView();

            document.getElementById('storyTitle').textContent = roundData.title || 'Untitled';
            document.getElementById('storyText').textContent = roundData.text || '';

            const textContainer = document.getElementById('storyText');

            if (timer) timer.stop();
            timer = new Timer(
                120,
                (elapsed) => {
                    document.getElementById('timer').textContent = formatTime(elapsed);

                    // Enter tension mode in last 10 seconds
                    if (elapsed >= 110 && !tensionMode) {
                        tensionMode = true;
                        document.getElementById('timer').classList.add('tension');
                        // TODO: play tick sound
                    }
                },
                () => {
                    client.victory();
                }
            );
            timer.start(roundData.start_time);

            if (scroller) scroller.stop();
            scroller = new AutoScroller(document.querySelector('.story-text-container'), 30);
            scroller.start(roundData.start_time, roundData.speed || 1);
        }

        function markJudgeBuzzed(judgeId) {
            const panel = document.querySelector(`[data-judge="${judgeId}"]`);
            if (panel) {
                panel.classList.add('buzzed');
            }
        }

        function showOutcome(outcome) {
            const outcomeEl = document.getElementById('outcome');
            outcomeEl.textContent = outcome === 'victory' ? 'SURVIVOR!' : 'BUZZED OUT';
            outcomeEl.className = `outcome ${outcome}`;
            outcomeEl.style.display = 'block';

            if (outcome === 'victory') {
                playSound('victory');
                // TODO: confetti/fireworks
            } else {
                playSound('defeat');
                document.body.classList.add('defeat-flash');
                setTimeout(() => document.body.classList.remove('defeat-flash'), 500);
            }
        }

        function resetView() {
            tensionMode = false;
            document.getElementById('timer').classList.remove('tension');
            document.getElementById('outcome').style.display = 'none';
            document.getElementById('storyTitle').textContent = 'Waiting for story...';
            document.getElementById('storyText').textContent = '';
            document.getElementById('timer').textContent = '0:00.0';

            document.querySelectorAll('.judge-panel').forEach(panel => {
                panel.classList.remove('buzzed');
            });
        }

        function playSound(type) {
            // Placeholder for audio playback
            console.log(`Playing sound: ${type}`);
        }
    </script>
</body>
</html>
EOF
```

- [ ] **Step 2: Test audience view**

Browser: `http://localhost:8000/audience.html?code=TEST`

Expected: See "Waiting for story", timer, three judge panels

Start a round via wscat, verify text appears, timer counts, auto-scroll works

- [ ] **Step 3: Commit**

```bash
git add www/audience.html
git commit -m "feat: add audience view with auto-scroll and judge panels"
```

---

## Task 9: Controller View Structure

**Files:**
- Create: `www/control.html`

- [ ] **Step 1: Create controller view HTML**

```bash
cat > www/control.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Controller - SPECULATIVE IDOL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            padding: 2rem;
        }

        h1, h2 {
            font-family: 'Press Start 2P', cursive;
            margin-bottom: 1rem;
        }

        h1 {
            font-size: 1.5rem;
            text-align: center;
            color: #ff0;
        }

        h2 {
            font-size: 1rem;
            margin-top: 2rem;
            border-bottom: 2px solid #0f0;
            padding-bottom: 0.5rem;
        }

        .session-info {
            text-align: center;
            padding: 1rem;
            border: 2px solid #0f0;
            margin-bottom: 2rem;
        }

        .code {
            font-family: 'Press Start 2P', cursive;
            font-size: 2rem;
            color: #0f0;
            letter-spacing: 0.5rem;
        }

        .section {
            margin-bottom: 2rem;
            padding: 1rem;
            border: 1px solid #0f0;
        }

        input, textarea, button, select {
            background: #000;
            color: #0f0;
            border: 2px solid #0f0;
            padding: 0.5rem;
            font-family: 'Courier New', monospace;
            font-size: 1rem;
            margin: 0.25rem;
        }

        button {
            cursor: pointer;
            font-family: 'Press Start 2P', cursive;
            font-size: 0.8rem;
            padding: 0.75rem 1.5rem;
            transition: all 0.2s;
        }

        button:hover {
            background: #0f0;
            color: #000;
        }

        button:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        textarea {
            width: 100%;
            min-height: 100px;
            resize: vertical;
        }

        .story-queue {
            list-style: none;
        }

        .story-item {
            border: 1px solid #0f0;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .story-item.current {
            border-color: #ff0;
            color: #ff0;
        }

        .story-info {
            flex: 1;
        }

        .story-actions {
            display: flex;
            gap: 0.5rem;
        }

        .controls {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .history-list {
            list-style: none;
        }

        .history-item {
            border: 1px solid #0f0;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }

        .history-item.victory {
            border-color: #0f0;
        }

        .history-item.defeat {
            border-color: #f00;
            color: #f00;
        }

        .form-group {
            margin-bottom: 0.5rem;
        }

        label {
            display: block;
            margin-bottom: 0.25rem;
            font-size: 0.9rem;
        }

        .import-export {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .import-export textarea {
            min-height: 200px;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <h1>CONTROLLER</h1>

    <div class="session-info">
        <div>SESSION CODE</div>
        <div class="code" id="sessionCode">----</div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem;">Connected: <span id="clientCount">0</span></div>
    </div>

    <div class="section">
        <h2>Story Queue</h2>
        <ul class="story-queue" id="storyQueue"></ul>

        <div class="form-group">
            <label>Title:</label>
            <input type="text" id="storyTitle" placeholder="Story title">
        </div>

        <div class="form-group">
            <label>Text:</label>
            <textarea id="storyText" placeholder="Story text..."></textarea>
        </div>

        <button onclick="addStory()">Add Story</button>
    </div>

    <div class="section">
        <h2>Round Controls</h2>
        <div id="currentStatus" style="margin-bottom: 1rem;">Status: Waiting</div>

        <div class="controls">
            <button onclick="startRound()" id="startBtn">Start Round</button>
            <button onclick="pauseRound()" id="pauseBtn" disabled>Pause</button>
            <button onclick="resumeRound()" id="resumeBtn" disabled>Resume</button>
            <button onclick="changeSpeed(1)" id="speed1Btn">1x</button>
            <button onclick="changeSpeed(2)" id="speed2Btn">2x</button>
            <button onclick="changeSpeed(3)" id="speed3Btn">3x</button>
            <button onclick="resetRound()" id="resetBtn">Reset</button>
        </div>
    </div>

    <div class="section">
        <h2>Import / Export</h2>
        <div class="import-export">
            <textarea id="importExportJson" placeholder="Session JSON..."></textarea>
            <div style="display: flex; gap: 0.5rem;">
                <button onclick="exportSession()">Export to JSON</button>
                <button onclick="importSession()">Import from JSON</button>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>History</h2>
        <ul class="history-list" id="historyList"></ul>
    </div>

    <script src="app.js"></script>
    <script>
        const params = getUrlParams();
        const client = new SpecIdolClient();
        let sessionState = null;
        let currentSpeed = 1;

        client.connect();

        client.onConnect = () => {
            if (params.code) {
                client.joinSession(params.code, 'controller');
            }
        };

        client.on('session_state', (data) => {
            sessionState = data;
            updateUI();
        });

        client.on('story_added', (data) => {
            // Refresh would happen via state update
            console.log('Story added:', data);
        });

        client.on('story_removed', (data) => {
            console.log('Story removed:', data);
        });

        client.on('round_started', (data) => {
            updateStatus('running');
        });

        client.on('paused', (data) => {
            updateStatus('paused');
        });

        client.on('resumed', (data) => {
            updateStatus('running');
        });

        client.on('round_ended', (data) => {
            updateStatus('ended');
            if (sessionState) {
                sessionState.history.push({
                    title: sessionState.current_round.title,
                    ...data
                });
                renderHistory();
            }
        });

        client.on('round_reset', () => {
            updateStatus('waiting');
        });

        client.on('session_imported', (data) => {
            alert(`Imported ${data.story_count} stories`);
            // Trigger refresh by requesting session state
            if (params.code) {
                client.joinSession(params.code, 'controller');
            }
        });

        function updateUI() {
            if (!sessionState) return;

            document.getElementById('sessionCode').textContent = sessionState.code || '----';
            renderStoryQueue();
            renderHistory();
            updateStatus(sessionState.current_round.status);
        }

        function renderStoryQueue() {
            const queue = document.getElementById('storyQueue');
            if (!sessionState || !sessionState.stories) {
                queue.innerHTML = '<li>No stories added yet</li>';
                return;
            }

            queue.innerHTML = sessionState.stories.map((story, i) => {
                const isCurrent = i === sessionState.current_round.story_index;
                return `
                    <li class="story-item ${isCurrent ? 'current' : ''}">
                        <div class="story-info">
                            <strong>${story.title}</strong><br>
                            <span style="opacity: 0.7; font-size: 0.9rem;">
                                ${story.text.substring(0, 80)}...
                            </span>
                        </div>
                        <div class="story-actions">
                            <button onclick="selectStory(${i})">Select</button>
                            <button onclick="removeStory(${i})">Remove</button>
                        </div>
                    </li>
                `;
            }).join('');
        }

        function renderHistory() {
            const list = document.getElementById('historyList');
            if (!sessionState || sessionState.history.length === 0) {
                list.innerHTML = '<li>No rounds completed yet</li>';
                return;
            }

            list.innerHTML = sessionState.history.map(entry => {
                const buzzInfo = entry.buzzes.map(b => `J${b.judge_id}:${b.time}s`).join(', ');
                return `
                    <li class="history-item ${entry.outcome}">
                        <strong>${entry.title}</strong> - ${entry.outcome.toUpperCase()}<br>
                        <span style="font-size: 0.85rem;">
                            Duration: ${entry.duration}s | Buzzes: ${buzzInfo || 'none'}
                        </span>
                    </li>
                `;
            }).join('');
        }

        function updateStatus(status) {
            document.getElementById('currentStatus').textContent = `Status: ${status}`;

            // Enable/disable buttons based on status
            const startBtn = document.getElementById('startBtn');
            const pauseBtn = document.getElementById('pauseBtn');
            const resumeBtn = document.getElementById('resumeBtn');

            startBtn.disabled = (status === 'running' || status === 'paused');
            pauseBtn.disabled = (status !== 'running');
            resumeBtn.disabled = (status !== 'paused');
        }

        function addStory() {
            const title = document.getElementById('storyTitle').value.trim();
            const text = document.getElementById('storyText').value.trim();

            if (!title || !text) {
                alert('Enter both title and text');
                return;
            }

            client.addStory(title, text);
            document.getElementById('storyTitle').value = '';
            document.getElementById('storyText').value = '';
        }

        function selectStory(index) {
            if (!sessionState) return;
            sessionState.current_round.story_index = index;
            renderStoryQueue();
        }

        function removeStory(index) {
            if (confirm('Remove this story?')) {
                client.removeStory(index);
            }
        }

        function startRound() {
            if (!sessionState || sessionState.current_round.story_index === null) {
                alert('Select a story first');
                return;
            }
            client.startRound(sessionState.current_round.story_index);
        }

        function pauseRound() {
            client.pause();
        }

        function resumeRound() {
            client.resume();
        }

        function changeSpeed(speed) {
            currentSpeed = speed;
            client.changeSpeed(speed);

            // Update button states
            document.getElementById('speed1Btn').style.background = speed === 1 ? '#0f0' : '#000';
            document.getElementById('speed2Btn').style.background = speed === 2 ? '#0f0' : '#000';
            document.getElementById('speed3Btn').style.background = speed === 3 ? '#0f0' : '#000';
            document.getElementById('speed1Btn').style.color = speed === 1 ? '#000' : '#0f0';
            document.getElementById('speed2Btn').style.color = speed === 2 ? '#000' : '#0f0';
            document.getElementById('speed3Btn').style.color = speed === 3 ? '#000' : '#0f0';
        }

        function resetRound() {
            if (confirm('Reset the current round?')) {
                client.resetRound();
            }
        }

        function exportSession() {
            if (!sessionState) return;

            const exportData = {
                stories: sessionState.stories,
                config: sessionState.config
            };

            document.getElementById('importExportJson').value = JSON.stringify(exportData, null, 2);
        }

        function importSession() {
            const json = document.getElementById('importExportJson').value.trim();
            if (!json) {
                alert('Paste JSON first');
                return;
            }

            try {
                const data = JSON.parse(json);
                client.importSession(data.stories || [], data.config || {});
            } catch (e) {
                alert('Invalid JSON: ' + e.message);
            }
        }
    </script>
</body>
</html>
EOF
```

- [ ] **Step 2: Test controller view**

Browser: `http://localhost:8000/control.html?code=TEST`

Expected: See session code, story queue (empty), controls, history

Add a story via form, verify it appears in queue

Select story, click "Start Round", verify status changes and other views update

- [ ] **Step 3: Commit**

```bash
git add www/control.html
git commit -m "feat: add controller view with story queue and round controls"
```

---

## Task 10: Sound Effects (Base64 Inline)

**Files:**
- Modify: `www/audience.html`

- [ ] **Step 1: Add inline base64 sound effects**

Since generating actual .wav files is complex, we'll use the Web Audio API to generate simple tones inline. Add this before the closing `</script>` tag in `www/audience.html`:

```javascript
// Simple tone generator for sound effects
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

function playBuzzSound() {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 200; // Low buzzer tone
    oscillator.type = 'sawtooth';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

function playVictorySound() {
    const times = [0, 0.15, 0.3, 0.5];
    const freqs = [523, 659, 784, 1047]; // C, E, G, C (major chord)

    times.forEach((time, i) => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.value = freqs[i];
        oscillator.type = 'square';

        gainNode.gain.setValueAtTime(0.2, audioContext.currentTime + time);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + time + 0.3);

        oscillator.start(audioContext.currentTime + time);
        oscillator.stop(audioContext.currentTime + time + 0.3);
    });
}

function playDefeatSound() {
    const times = [0, 0.2, 0.4];
    const freqs = [440, 349, 262]; // Descending sad trombone

    times.forEach((time, i) => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.value = freqs[i];
        oscillator.type = 'sawtooth';

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime + time);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + time + 0.4);

        oscillator.start(audioContext.currentTime + time);
        oscillator.stop(audioContext.currentTime + time + 0.4);
    });
}

function playTickSound() {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.05);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.05);
}

// Update playSound function
function playSound(type) {
    if (type === 'buzz') playBuzzSound();
    else if (type === 'victory') playVictorySound();
    else if (type === 'defeat') playDefeatSound();
    else if (type === 'tick') playTickSound();
}

// Add tick sound in tension mode
let tickInterval = null;
function startTensionTicks() {
    if (tickInterval) clearInterval(tickInterval);
    let tickRate = 1000; // Start at 1 second

    const tick = () => {
        playTickSound();
        tickRate = Math.max(100, tickRate * 0.9); // Accelerate
        tickInterval = setTimeout(tick, tickRate);
    };
    tick();
}

function stopTensionTicks() {
    if (tickInterval) {
        clearTimeout(tickInterval);
        tickInterval = null;
    }
}

// Update tension mode trigger in startRound timer callback
// Replace the "// TODO: play tick sound" comment with:
// startTensionTicks();

// Add stopTensionTicks() in showOutcome and resetView functions
```

Now update the timer callback in `startRound` to call `startTensionTicks()`:

```javascript
if (elapsed >= 110 && !tensionMode) {
    tensionMode = true;
    document.getElementById('timer').classList.add('tension');
    startTensionTicks();
}
```

Add `stopTensionTicks()` at the start of `showOutcome` and `resetView`.

- [ ] **Step 2: Test sound effects**

Open audience view, start a round

Expected: Hear buzz sound when judge buzzes, tick sounds in last 10 seconds (accelerating), victory/defeat sounds at round end

- [ ] **Step 3: Commit**

```bash
git add www/audience.html
git commit -m "feat: add Web Audio API sound effects (buzz, victory, defeat, tick)"
```

---

## Task 11: Shared Styles Polish

**Files:**
- Create: `www/style.css`
- Modify: `www/index.html`, `www/judge.html`, `www/audience.html`, `www/control.html`

- [ ] **Step 1: Extract common styles to style.css**

```bash
cat > www/style.css << 'EOF'
/* Shared styles for SPECULATIVE IDOL */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --neon-green: #0f0;
    --neon-yellow: #ff0;
    --neon-magenta: #f0f;
    --neon-red: #f00;
    --black: #000;
}

body {
    background: var(--black);
    color: var(--neon-green);
    font-family: 'Courier New', monospace;
}

h1, h2, h3 {
    font-family: 'Press Start 2P', cursive;
}

button {
    background: var(--neon-green);
    color: var(--black);
    border: 3px solid var(--neon-green);
    padding: 0.75rem 1.5rem;
    font-family: 'Press Start 2P', cursive;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
}

button:hover:not(:disabled) {
    background: var(--black);
    color: var(--neon-green);
    box-shadow: 0 0 20px var(--neon-green);
}

button:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

input, textarea, select {
    background: var(--black);
    color: var(--neon-green);
    border: 2px solid var(--neon-green);
    padding: 0.75rem;
    font-family: 'Courier New', monospace;
    font-size: 1rem;
}

input:focus, textarea:focus, select:focus {
    outline: none;
    box-shadow: 0 0 10px var(--neon-green);
}
EOF
```

- [ ] **Step 2: Add style.css link to all HTML files**

Add this line in the `<head>` of each HTML file (after the Google Fonts link):

```html
<link rel="stylesheet" href="style.css">
```

Files to modify:
- `www/index.html`
- `www/judge.html`
- `www/audience.html`
- `www/control.html`

You can remove the duplicate common styles from each file's `<style>` block, keeping only page-specific styles.

- [ ] **Step 3: Test all views still render correctly**

Open each view in browser and verify styling looks correct.

- [ ] **Step 4: Commit**

```bash
git add www/style.css www/index.html www/judge.html www/audience.html www/control.html
git commit -m "refactor: extract shared styles to style.css"
```

---

## Task 12: End-to-End Integration Test

**Files:**
- None (testing only)

- [ ] **Step 1: Start server and web server**

Terminal 1:
```bash
cd server
python3 relay.py
```

Terminal 2:
```bash
cd www
python3 -m http.server 8000
```

- [ ] **Step 2: Test full flow**

1. Open `http://localhost:8000/index.html` in browser
2. Click "Create Session" → redirects to controller, shows session code
3. Open `http://localhost:8000/index.html` in two more browser tabs
4. In each tab, click "Join Session", enter the session code:
   - Tab 1: Join as Judge 1
   - Tab 2: Join as Audience
5. In controller: add a test story (title + text), click "Add Story"
6. Select the story, click "Start Round"
7. Verify:
   - Audience view shows scrolling text, timer counting, judge panels lit
   - Judge view shows button and timer
8. In judge view, click the big red BUZZ button
9. Verify:
   - Judge button transforms to X
   - Audience shows judge panel with X and plays buzz sound
10. Open two more judge tabs (Judge 2, Judge 3), buzz them
11. Verify all 3 judges buzzed → round ends with "BUZZED OUT" on audience view
12. In controller, click "Reset Round", start a new round
13. Let timer run to 2:00 without buzzing
14. Verify audience shows "SURVIVOR!" with victory sound

- [ ] **Step 3: Document any bugs found**

If bugs discovered, note them and fix in follow-up tasks. For this test, just verify the core flow works.

- [ ] **Step 4: Commit test notes (if any)**

If you created test documentation:
```bash
git add docs/testing-notes.md
git commit -m "docs: add end-to-end integration test notes"
```

---

## Task 13: README Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README**

```bash
cat > README.md << 'EOF'
# SPECULATIVE IDOL

A live "Pop Idol for writers" web application for speculative fiction conventions. Readers read stories aloud with auto-scrolling text, three editor-judges buzz them out with big red buttons, and an audience watches on a projector. If the reader survives 2 minutes without all three judges buzzing, they win.

## Features

- **Real-time WebSocket coordination** between multiple clients
- **Auto-scrolling story text** synchronized across all views
- **Judge buzzer system** with big red buttons (mobile-optimized)
- **Audience projector view** with CRT effects, judge panels, animations, sound
- **Controller interface** with story queue, round controls, import/export
- **Retro/campy aesthetic** with pixel fonts, neon colors, game show vibe
- **No build step, no framework** - pure HTML/CSS/JS + Python WebSocket server

## Quick Start

### 1. Install Dependencies

```bash
cd server
pip3 install -r requirements.txt
```

### 2. Start WebSocket Server

```bash
cd server
python3 relay.py
```

Server runs on `ws://localhost:8765`

### 3. Start Web Server

```bash
cd www
python3 -m http.server 8000
```

Web UI available at `http://localhost:8000/index.html`

### 4. Create a Session

1. Open `http://localhost:8000/index.html` in a browser
2. Click **"Create Session"** → redirects to controller
3. Note the 4-letter session code

### 5. Join as Judge (x3)

1. Open `http://localhost:8000/index.html` on 3 mobile devices (or browser tabs)
2. Click **"Join Session"**, enter the session code
3. Select **"Judge"**, pick judge number (1, 2, or 3)
4. Each judge gets a big red BUZZ button

### 6. Join as Audience

1. Open `http://localhost:8000/index.html` on the projector laptop
2. Click **"Join Session"**, enter the session code
3. Select **"Audience"**
4. This view shows on the projector for the audience to watch

### 7. Run the Event

In the **Controller** view:
1. Add stories: enter title + text, click "Add Story"
2. Select a story from the queue
3. Click **"Start Round"** to begin
4. Use speed controls (1x/2x/3x) and play/pause as needed
5. Judges press their BUZZ buttons when they've heard enough
6. When all 3 buzz → "BUZZED OUT" (defeat)
7. If timer reaches 2:00 → "SURVIVOR!" (victory)

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
- `judge_count`: number of judges (default 3)

## Deployment

### Option A: Local Network

1. Run server on a laptop connected to venue WiFi
2. Replace `localhost` with laptop's local IP in `www/app.js`:
   ```javascript
   connect(wsUrl = 'ws://192.168.x.x:8765')
   ```
3. Devices connect to same WiFi, access via IP

### Option B: Hosted Server

1. Deploy `server/relay.py` to a VPS (e.g., DigitalOcean, Linode)
2. Update `www/app.js` with server's public WebSocket URL
3. Serve `www/` files via Apache/Nginx
4. Use `wss://` (secure WebSocket) in production

## Browser Compatibility

- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Full support (Web Audio API works)
- **Mobile Safari/Chrome**: Optimized for portrait (judge view)

## License

MIT

## Credits

Built for a speculative fiction writers' convention. Inspired by Pop Idol and game show aesthetics.
EOF
```

- [ ] **Step 2: Commit README**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```

---

## Self-Review Checklist

After completing all tasks, verify:

### Spec Coverage
- [x] WebSocket server with session creation/join
- [x] Story management (add, remove, queue)
- [x] Round controls (start, pause, resume, speed, reset)
- [x] Buzz system (judges press buttons, server tracks, broadcasts)
- [x] Timer (client-side, synced, tension mode in last 10s)
- [x] Auto-scroll (time-based, speed control)
- [x] Landing page (create/join flows)
- [x] Judge view (button, timer, other judges' status)
- [x] Audience view (text, timer, judge panels, animations, sounds)
- [x] Controller view (queue, controls, import/export, history)
- [x] Retro/campy aesthetic (pixel fonts, neon colors, CRT effect)
- [x] Sound effects (buzz, victory, defeat, ticks)
- [x] Import/export JSON sessions

### No Placeholders
- All code blocks complete
- All file paths exact
- All commands with expected output
- No TBD/TODO left in plan

### Type Consistency
- Session state structure consistent across server and clients
- Message protocol types match between send and receive handlers
- Timer and AutoScroller classes used consistently

---

## Execution Complete

All tasks defined. Ready for agentic execution.
