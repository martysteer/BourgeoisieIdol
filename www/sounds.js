// Web Audio API sound generators for SpecIdol

let audioContext = null;

function getAudioContext() {
    if (!audioContext) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) {
            console.warn('Web Audio API not supported, sounds disabled');
            return null;
        }
        audioContext = new AudioContextClass();
    }
    // Resume if suspended (autoplay policy)
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
    return audioContext;
}

// iOS Safari requires playing a sound during a user gesture to fully unlock audio.
// Call this from a click/touchend handler.
async function unlockAudio() {
    const ctx = getAudioContext();
    if (!ctx) return;
    // Await resume — iOS won't unlock until this resolves
    if (ctx.state === 'suspended') {
        await ctx.resume();
    }
    const buf = ctx.createBuffer(1, 1, ctx.sampleRate);
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(ctx.destination);
    src.start(0);
}

function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// --- Synth engine (ported from buzz-tester) ---

function makeDistortionCurve(amount) {
    var samples = 44100;
    var curve = new Float32Array(samples);
    var deg = Math.PI / 180;
    for (var i = 0; i < samples; i++) {
        var x = (i * 2) / samples - 1;
        curve[i] = ((3 + amount) * x * 20 * deg) / (Math.PI + amount * Math.abs(x));
    }
    return curve;
}

function playSynthSound(params, delay) {
    var ctx = getAudioContext();
    if (!ctx) return;

    var startTime = ctx.currentTime + (delay || 0);
    var dur = params.duration;

    // Gain envelope: 5ms attack, sustain at 80%, exponential decay
    var masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.001, startTime);
    masterGain.gain.exponentialRampToValueAtTime(params.volume, startTime + 0.005);
    masterGain.gain.setValueAtTime(params.volume, startTime + dur * 0.8);
    masterGain.gain.exponentialRampToValueAtTime(0.001, startTime + dur);
    masterGain.connect(ctx.destination);

    // Optional bandpass filter
    var outputNode = masterGain;
    if (params.filterQ > 0.5) {
        var filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = params.filterFreq;
        filter.Q.value = params.filterQ;
        filter.connect(masterGain);
        outputNode = filter;
    }

    // Optional distortion
    var distortionNode = outputNode;
    if (params.distortion > 0) {
        var waveshaper = ctx.createWaveShaper();
        waveshaper.curve = makeDistortionCurve(params.distortion);
        waveshaper.oversample = '4x';
        waveshaper.connect(outputNode);
        distortionNode = waveshaper;
    }

    // Oscillator 1
    var osc1 = ctx.createOscillator();
    osc1.type = params.osc1Type;
    osc1.frequency.value = params.osc1Freq;
    osc1.connect(distortionNode);
    osc1.start(startTime);
    osc1.stop(startTime + dur);

    // Oscillator 2
    if (params.osc2Type && params.osc2Type !== 'off') {
        var osc2 = ctx.createOscillator();
        osc2.type = params.osc2Type;
        osc2.frequency.value = params.osc2Freq + (params.detune || 0);
        osc2.connect(distortionNode);
        osc2.start(startTime);
        osc2.stop(startTime + dur);
    }
}

// --- Buzz: EAS dual-tone, beep count from server buzz_count (cycles 1→2→3) ---

var BUZZ_TONE = {
    osc1Type: 'sine', osc1Freq: 880,
    osc2Type: 'off', osc2Freq: 0,
    volume: 0.3, duration: 0.15,
    distortion: 0, filterFreq: 1000, filterQ: 0, detune: 0
};

function playBuzz(soundIndex, repeatCount) {
    if (prefersReducedMotion()) return;

    // repeatCount = server buzz_count (1st, 2nd, 3rd judge to buzz), cycles 1→2→3
    var beepCount = ((repeatCount - 1) % 3) + 1;

    var gap = 0.12;
    for (var i = 0; i < beepCount; i++) {
        playSynthSound(BUZZ_TONE, i * (BUZZ_TONE.duration + gap));
    }
}

// --- Victory fanfare: ascending C major arpeggio with shimmer ---

var FANFARE_SEQUENCE = [
    // C4
    {
        delay: 0,
        osc1Type: 'square', osc1Freq: 261.63,
        osc2Type: 'off', osc2Freq: 0,
        volume: 0.35, duration: 0.25,
        distortion: 30, filterFreq: 1000, filterQ: 0, detune: 0
    },
    // E4
    {
        delay: 0.28,
        osc1Type: 'square', osc1Freq: 329.63,
        osc2Type: 'off', osc2Freq: 0,
        volume: 0.35, duration: 0.25,
        distortion: 30, filterFreq: 1000, filterQ: 0, detune: 0
    },
    // G4
    {
        delay: 0.56,
        osc1Type: 'square', osc1Freq: 392.00,
        osc2Type: 'off', osc2Freq: 0,
        volume: 0.35, duration: 0.25,
        distortion: 30, filterFreq: 1000, filterQ: 0, detune: 0
    },
    // C5 — clean hit
    {
        delay: 0.84,
        osc1Type: 'square', osc1Freq: 523.25,
        osc2Type: 'off', osc2Freq: 0,
        volume: 0.4, duration: 0.3,
        distortion: 30, filterFreq: 1000, filterQ: 0, detune: 0
    },
    // C5 shimmer — starts same time as clean C5, rings longer
    {
        delay: 0.84,
        osc1Type: 'square', osc1Freq: 523.25,
        osc2Type: 'square', osc2Freq: 524.25,
        volume: 0.35, duration: 0.5,
        distortion: 20, filterFreq: 1000, filterQ: 0, detune: 0
    }
];

function playVictoryFanfare() {
    if (prefersReducedMotion()) return;

    for (var i = 0; i < FANFARE_SEQUENCE.length; i++) {
        playSynthSound(FANFARE_SEQUENCE[i], FANFARE_SEQUENCE[i].delay);
    }
}

// --- Ahooga: two-tone car horn ---

var AHOOGA_SEQUENCE = [
    // High tone
    {
        osc1Type: 'sawtooth', osc1Freq: 400,
        osc2Type: 'off', osc2Freq: 0,
        volume: 0.4, duration: 0.35,
        distortion: 50, filterFreq: 1000, filterQ: 0, detune: 0
    },
    // Low tone
    {
        osc1Type: 'sawtooth', osc1Freq: 220,
        osc2Type: 'off', osc2Freq: 0,
        volume: 0.4, duration: 0.45,
        distortion: 50, filterFreq: 1000, filterQ: 0, detune: 0
    }
];

function playAhooga() {
    if (prefersReducedMotion()) return;

    playSynthSound(AHOOGA_SEQUENCE[0], 0);
    playSynthSound(AHOOGA_SEQUENCE[1], 0.4);
}

// --- Final combo: rapid EAS burst + AHOOGA ---

function playFinalCombo(judgeSounds) {
    if (prefersReducedMotion()) return;

    // 3 rapid EAS beeps overlapping slightly
    for (var i = 0; i < 3; i++) {
        playSynthSound(BUZZ_TONE, i * 0.08);
    }

    // Ahooga after the burst
    playSynthSound(AHOOGA_SEQUENCE[0], 0.4);
    playSynthSound(AHOOGA_SEQUENCE[1], 0.8);
}

// --- Countdown beep: 1 beep per call (0.5s long), called each second by Countdown ---

var COUNTDOWN_BEEP = {
    osc1Type: 'sine', osc1Freq: 880,
    osc2Type: 'off', osc2Freq: 0,
    volume: 0.3, duration: 0.5,
    distortion: 0, filterFreq: 1000, filterQ: 0, detune: 0
};

// "GO" beep: major third chord, higher, brighter
var COUNTDOWN_GO = {
    osc1Type: 'square', osc1Freq: 1046.5,
    osc2Type: 'square', osc2Freq: 1318.5,
    volume: 0.35, duration: 0.4,
    distortion: 20, filterFreq: 1000, filterQ: 0, detune: 0
};

function playCountdownBeep() {
    if (prefersReducedMotion()) return;

    playSynthSound(COUNTDOWN_BEEP, 0);
}

function playCountdownGo() {
    if (prefersReducedMotion()) return;

    playSynthSound(COUNTDOWN_GO, 0);
}
