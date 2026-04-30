// Shared WebSocket client and state management

// Clock offset: difference between server and client clocks.
// serverTime = clientTime + clockOffset
let clockOffset = 0;

function updateClockOffset(serverTime) {
    const clientNow = Date.now() / 1000;
    clockOffset = serverTime - clientNow;
}

// Convert server timestamp to client-local timestamp
function serverToLocal(serverTimestamp) {
    return serverTimestamp - clockOffset;
}

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

    connect(wsUrl) {
        // Auto-detect WebSocket URL if not provided
        if (!wsUrl) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = window.location.port;

            // Always connect to WebSocket on port 8765
            if (host === 'localhost' || host === '127.0.0.1') {
                wsUrl = 'ws://localhost:8765';
            } else {
                wsUrl = `${protocol}//${host}:8765`;
            }
        }

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

    listSessions() {
        this.send('list_sessions');
    }

    createSession() {
        this.send('create_session');
    }

    joinSession(code, role, judgeId = null, name = null) {
        this.sessionCode = code;
        this.role = role;
        this.judgeId = judgeId;
        const data = { code, role, judge_id: judgeId };
        if (name) data.name = name;
        this.send('join', data);
    }

    setJudgeName(name) {
        this.send('set_judge_name', { name });
    }

    addItem(title, text, manifestUrl = null, canvases = []) {
        this.send('add_item', {
            title,
            text,
            manifest_url: manifestUrl,
            canvases: canvases
        });
    }

    removeItem(itemIndex) {
        this.send('remove_item', { item_index: itemIndex });
    }

    startRound(itemIndex) {
        this.send('round_start', { item_index: itemIndex });
    }

    fetchManifest(manifestUrl) {
        this.send('fetch_manifest', { manifest_url: manifestUrl });
    }

    canvasAdvance(direction) {
        this.send('canvas_advance', { direction });
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

    advanceText() {
        this.send('text_advance');
    }

    importSession(items, config) {
        this.send('import_session', { items, config });
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
        this.startTime = serverToLocal(serverStartTime);
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

    resume(serverStartTime) {
        this.startTime = serverToLocal(serverStartTime);
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
// Tracks scroll position directly to avoid speed^2 bugs on pause/resume.
class AutoScroller {
    constructor(element, baseSpeed = 30) {
        this.element = element;
        this.baseSpeed = baseSpeed; // pixels per second at 1x
        this.speed = 1;
        this.position = 0;         // accumulated scroll position in pixels
        this.lastTickTime = null;   // last tick timestamp (seconds)
        this.running = false;
        this.intervalId = null;
    }

    start(serverStartTime, speed = 1) {
        this.speed = speed;
        this.position = 0;
        this.lastTickTime = Date.now() / 1000;
        this.running = true;
        this.intervalId = setInterval(() => this.scroll(), 50); // 20 Hz
    }

    changeSpeed(speed, timestamp) {
        // Flush position at old speed before switching
        this._advance();
        this.speed = speed;
    }

    pause() {
        this._advance();
        this.running = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    resume(newStartTime) {
        this.lastTickTime = Date.now() / 1000;
        this.running = true;
        this.intervalId = setInterval(() => this.scroll(), 50);
    }

    stop() {
        this.running = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    _advance() {
        const now = Date.now() / 1000;
        if (this.lastTickTime && this.running) {
            const dt = now - this.lastTickTime;
            this.position += dt * this.speed * this.baseSpeed;
        }
        this.lastTickTime = now;
    }

    scroll() {
        this._advance();
        this.element.scrollTop = this.position;
    }
}

// Utility: format time as M:SS.T
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const tenths = Math.floor((seconds % 1) * 10);
    return `${minutes}:${secs.toString().padStart(2, '0')}.${tenths}`;
}

// Calculate initials from judge names with collision numbering
function calculateInitials(judges) {
    // judges: [{id, name}, ...]
    // returns: {id: "AS", id2: "AS2", ...}
    const initialsMap = {};
    const groups = {};

    // Extract initials for each judge
    judges.forEach(j => {
        const initials = j.name
            .split(/\s+/)
            .map(w => w.charAt(0))
            .join('')
            .toUpperCase();
        initialsMap[j.id] = initials;
        if (!groups[initials]) groups[initials] = [];
        groups[initials].push(j.id);
    });

    // Number collisions
    const result = {};
    for (const [initials, ids] of Object.entries(groups)) {
        ids.forEach((id, index) => {
            result[id] = index === 0 ? initials : initials + (index + 1);
        });
    }
    return result;
}

function renderJudgePanelCells(containerId, judges) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Preserve buzzed state across re-renders
    const buzzedIds = new Set(
        [...container.querySelectorAll('.judge-cell.buzzed')]
            .map(el => parseInt(el.dataset.judge))
    );

    const initials = calculateInitials(judges);
    container.innerHTML = judges.map(j =>
        `<div class="judge-cell${buzzedIds.has(j.id) ? ' buzzed' : ''}" data-judge="${j.id}"><span class="x-mark">✕</span><span class="initials">${initials[j.id]}</span></div>`
    ).join('');
}

// Utility: parse URL params
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        code: params.get('code'),
        judge: params.get('judge') ? parseInt(params.get('judge')) : null
    };
}

// Utility: escape HTML special characters
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
