// Wellbeing Conversations Coach - voice page client.
//
// Talks to our FastAPI bridge over a single WebSocket. The bridge talks to
// Gemini Live on our behalf using the server-side API key. This avoids the
// @google/genai JS SDK's apiVersion routing bug and keeps the Google key
// off the browser.
//
// Wire protocol (JSON, both directions):
//   browser -> bridge   { type: 'audio',           data: <base64 PCM 16kHz mono> }
//                       { type: 'audio_stream_end' }
//                       { type: 'end' }
//   bridge  -> browser  { type: 'ready', voice, model, mode }
//                       { type: 'audio',           data: <base64 PCM 24kHz mono> }
//                       { type: 'input_transcript',  text, finished }
//                       { type: 'output_transcript', text, finished }
//                       { type: 'interrupted' }
//                       { type: 'turn_complete' }
//                       { type: 'fatal', error }

const params = new URLSearchParams(location.search);
const sessionId = params.get("session");

const views = {
  loading: document.getElementById("view-loading"),
  error:   document.getElementById("view-error"),
  brief:   document.getElementById("view-brief"),
  live:    document.getElementById("view-live"),
  scoring: document.getElementById("view-scoring"),
  results: document.getElementById("view-results"),
};
function show(name) {
  Object.values(views).forEach(v => v.classList.remove("active"));
  views[name].classList.add("active");
}
function $ (id) { return document.getElementById(id); }
function failWith(msg) {
  console.error("[komodo-trainer]", msg);
  $("error-message").textContent = msg;
  show("error");
}

window.addEventListener("error", (e) => {
  console.error("[komodo-trainer] uncaught:", e.error || e.message);
  if (e.message) failWith(`Uncaught error: ${e.message}`);
});
window.addEventListener("unhandledrejection", (e) => {
  console.error("[komodo-trainer] promise rejection:", e.reason);
  failWith(`Promise rejected: ${e.reason?.message || String(e.reason)}`);
});

if (!sessionId) {
  failWith("No session id in the URL. Open the voice page from the Streamlit hub.");
}

// ----- State -----
let sessionCfg = null;
let ws = null;
let micStream = null;
let inputCtx = null;
let outputCtx = null;
let workletNode = null;
let sourceNode = null;
let playbackDest = null;     // MediaStreamAudioDestinationNode for AI audio
let playbackAudioEl = null;  // <audio> element that plays AI audio via the OS audio path
let muted = false;
let timerInterval = null;
let timerStart = 0;
let endingNow = false;
let connected = false;
let micChunkCount = 0;       // running count for debug

const userBuf = { text: "", el: null, complete: false };
const assistantBuf = { text: "", el: null, complete: false };
const finishedTurns = [];

let nextPlayTime = 0;
let speakingTimeout = null;
let aiSpeaking = false;          // half-duplex: true while AI is talking, mic gated off

// ----- Audio helpers -----
function base64ToInt16(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Int16Array(bytes.buffer);
}

function int16ToBase64(int16) {
  const bytes = new Uint8Array(int16.buffer);
  let bin = "";
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  }
  return btoa(bin);
}

function playPCM24k(int16) {
  if (!outputCtx) return;
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7FFF);
  }
  const buf = outputCtx.createBuffer(1, float32.length, 24000);
  buf.getChannelData(0).set(float32);
  const src = outputCtx.createBufferSource();
  src.buffer = buf;
  // Route through a MediaStreamDestination + <audio> element so the browser's
  // echo canceller knows about this audio and subtracts it from the mic.
  // Without this, the AI's voice leaks into the mic, Gemini hears itself, and
  // user speech stops being recognised after the first AI turn.
  src.connect(playbackDest);
  const startAt = Math.max(outputCtx.currentTime, nextPlayTime);
  src.start(startAt);
  nextPlayTime = startAt + buf.duration;
}

const WORKLET_SRC = `
class PCMRecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetRate = 16000;
    this.ratio = sampleRate / this.targetRate;
    this.accum = [];
  }
  process(inputs) {
    const input = inputs[0]?.[0];
    if (!input) return true;
    for (let i = 0; i < input.length; i += this.ratio) {
      this.accum.push(input[Math.floor(i)]);
    }
    if (this.accum.length >= 320) {
      const int16 = new Int16Array(this.accum.length);
      for (let j = 0; j < this.accum.length; j++) {
        const s = Math.max(-1, Math.min(1, this.accum[j]));
        int16[j] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      this.port.postMessage(int16.buffer, [int16.buffer]);
      this.accum = [];
    }
    return true;
  }
}
registerProcessor('pcm-recorder', PCMRecorderProcessor);
`;
function workletURL() {
  return URL.createObjectURL(new Blob([WORKLET_SRC], { type: "application/javascript" }));
}

// ----- UI helpers -----
function setOrb(state, label) {
  const orb = $("orb");
  orb.classList.remove("state-idle", "state-listening", "state-speaking");
  orb.classList.add(`state-${state}`);
  $("orb-label").textContent = label;
}
function fmtTime(s) {
  const m = Math.floor(s / 60).toString().padStart(2, "0");
  const ss = Math.floor(s % 60).toString().padStart(2, "0");
  return `${m}:${ss}`;
}
function startTimer() {
  timerStart = Date.now();
  timerInterval = setInterval(() => {
    $("session-timer").textContent = fmtTime((Date.now() - timerStart) / 1000);
  }, 250);
}
function stopTimer() { if (timerInterval) clearInterval(timerInterval); timerInterval = null; }
function appendTurnEl(role) {
  const div = document.createElement("div");
  div.className = `turn ${role}`;
  const speaker = role === "user" ? "You" : (sessionCfg.persona.display_name || "AI");
  div.innerHTML = `<span class="speaker">${speaker}:</span> <span class="text"></span>`;
  const t = $("live-transcript");
  if (t.querySelector("p.muted")) t.innerHTML = "";
  t.appendChild(div);
  t.scrollTop = t.scrollHeight;
  return div.querySelector(".text");
}
function flushTurn(buf, role) {
  if (!buf.text.trim()) return;
  finishedTurns.push({ role, text: buf.text.trim() });
  buf.text = ""; buf.el = null; buf.complete = false;
}
function buildFinalTranscript() {
  flushTurn(userBuf, "user");
  flushTurn(assistantBuf, "assistant");
  return finishedTurns
    .map(t => {
      const speaker = t.role === "user" ? "Teacher" : (sessionCfg.persona.display_name || "Student");
      return `${speaker}: ${t.text}`;
    })
    .join("\n\n");
}

// ----- Step 1: load session config -----
async function loadSession() {
  try {
    const r = await fetch(`/api/session/${sessionId}`);
    if (!r.ok) throw new Error(`Bridge: ${r.status} ${await r.text()}`);
    sessionCfg = await r.json();
  } catch (e) {
    failWith(`Couldn't load session: ${e.message}`);
    return;
  }
  renderBrief();
  show("brief");
}

function renderBrief() {
  const s = sessionCfg.scenario, p = sessionCfg.persona;
  $("brief-title").textContent = s.title;
  $("brief-text").textContent = s.brief;

  const friendlyMode = sessionCfg.mode === "mode1" ? "🎴 Lead a class" : "💛 Support a student";
  const modePill = $("brief-mode-pill");
  modePill.textContent = friendlyMode;
  modePill.className = `mode-pill ${sessionCfg.mode}`;
  if (s.is_red_flag) { modePill.textContent = "⚠ Safeguarding"; modePill.classList.add("redflag"); }

  $("brief-persona").textContent = `${p.display_name}${p.year ? ` • ${p.year}` : ""}`;
  $("brief-duration").textContent = `~${s.duration_minutes} min`;
  $("brief-voice").textContent = `voice: ${sessionCfg.voice}`;

  const watch = $("brief-watchfor");
  watch.innerHTML = "";
  (s.watch_for || []).forEach(w => {
    const li = document.createElement("li");
    li.textContent = w;
    watch.appendChild(li);
  });

  if (sessionCfg.activity) {
    const a = sessionCfg.activity;
    $("brief-activity-card").style.display = "";
    $("brief-activity-title").textContent = `🎴 Activity: ${a.name}`;
    $("brief-activity-objective").textContent = a.objective;
    $("brief-activity-instructions").textContent = a.instructions;
  }

  if (s.is_red_flag) {
    $("brief-redflag").style.display = "";
    $("start-button").disabled = true;
    $("consent-check").addEventListener("change", e => {
      $("start-button").disabled = !e.target.checked;
    });
  }

  // Restore language preference + persist on change
  const langSel = $("lang-select");
  const savedLang = localStorage.getItem("komodo-trainer.lang");
  if (savedLang) {
    const opt = langSel.querySelector(`option[value="${savedLang}"]`);
    if (opt) langSel.value = savedLang;
  }
  langSel.addEventListener("change", () => {
    localStorage.setItem("komodo-trainer.lang", langSel.value);
  });

  $("start-button").addEventListener("click", startSession);
  $("mute-button").addEventListener("click", toggleMute);
  $("end-button").addEventListener("click", endSession);

  $("live-title").textContent = s.title;
  $("live-persona").textContent = `${p.display_name}${p.year ? ` • ${p.year}` : ""} • voice: ${sessionCfg.voice}`;

  const resultsPill = $("results-mode-pill");
  resultsPill.textContent = friendlyMode;
  resultsPill.className = `mode-pill ${sessionCfg.mode}`;
}

// ----- Step 2: start the voice session -----
async function startSession() {
  $("start-button").disabled = true;
  $("start-button").textContent = "Connecting…";
  setOrb("idle", "Connecting…");
  show("live");

  try {
    // Mic + audio contexts (need user gesture; we're inside a click handler)
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    inputCtx = new (window.AudioContext || window.webkitAudioContext)({
      latencyHint: "interactive",
    });
    outputCtx = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: 24000,
      latencyHint: "interactive",
    });
    if (inputCtx.state === "suspended") await inputCtx.resume();
    if (outputCtx.state === "suspended") await outputCtx.resume();

    // Build the playback path: AudioContext → MediaStreamDestination → <audio>
    // element. Routing through an <audio> tag is what enables the browser's
    // built-in echo cancellation to suppress AI voice from our mic.
    playbackDest = outputCtx.createMediaStreamDestination();
    playbackAudioEl = new Audio();
    playbackAudioEl.srcObject = playbackDest.stream;
    playbackAudioEl.autoplay = true;
    // Some browsers want the element in the DOM before they'll play it.
    playbackAudioEl.style.display = "none";
    document.body.appendChild(playbackAudioEl);
    try {
      await playbackAudioEl.play();
    } catch (e) {
      console.warn("[komodo-trainer] audio element autoplay blocked:", e);
    }

    // Open WebSocket to our bridge
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const lang = $("lang-select")?.value || "en-US";
    const wsUrl = `${proto}//${location.host}/ws/voice/${encodeURIComponent(sessionId)}?lang=${encodeURIComponent(lang)}`;
    console.log("[komodo-trainer] connecting to", wsUrl);
    ws = new WebSocket(wsUrl);

    ws.addEventListener("open", () => {
      console.log("[komodo-trainer] WS open");
    });

    ws.addEventListener("message", (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        handleMessage(msg);
      } catch (e) {
        console.error("[komodo-trainer] bad WS message", evt.data, e);
      }
    });

    ws.addEventListener("error", (e) => {
      console.error("[komodo-trainer] WS error", e);
    });

    ws.addEventListener("close", (ev) => {
      console.log("[komodo-trainer] WS closed", ev.code, ev.reason);
      connected = false;
      if (!endingNow && ev.code !== 1000) {
        failWith(`Voice session closed (code ${ev.code}): ${ev.reason || "no reason"}`);
      }
    });
  } catch (e) {
    failWith(`Couldn't start the session: ${e.message}`);
  }
}

async function startMicPipeline() {
  try {
    await inputCtx.audioWorklet.addModule(workletURL());
  } catch (e) {
    failWith(`AudioWorklet failed to load: ${e.message}`);
    return;
  }
  workletNode = new AudioWorkletNode(inputCtx, "pcm-recorder");
  workletNode.port.onmessage = (evt) => {
    if (muted || aiSpeaking || !ws || ws.readyState !== WebSocket.OPEN) return;
    const int16 = new Int16Array(evt.data);
    const b64 = int16ToBase64(int16);
    ws.send(JSON.stringify({ type: "audio", data: b64 }));
    micChunkCount += 1;
    if (micChunkCount % 50 === 0) {
      console.log(`[komodo-trainer] mic chunks sent: ${micChunkCount}`);
    }
  };
  sourceNode = inputCtx.createMediaStreamSource(micStream);
  sourceNode.connect(workletNode);
}

// ----- Step 3: route bridge messages -----
function handleMessage(msg) {
  switch (msg.type) {
    case "ready":
      console.log("[komodo-trainer] bridge ready", msg);
      connected = true;
      setOrb("listening", "Listening, go ahead");
      startTimer();
      startMicPipeline().catch(e => failWith(`Mic pipeline failed: ${e.message}`));
      break;

    case "audio": {
      const int16 = base64ToInt16(msg.data);
      playPCM24k(int16);
      aiSpeaking = true;
      setOrb("speaking", `${sessionCfg.persona.display_name} is speaking`);
      if (speakingTimeout) clearTimeout(speakingTimeout);
      speakingTimeout = setTimeout(() => {
        aiSpeaking = false;
        setOrb("listening", "Go ahead");
      }, 800);
      break;
    }

    case "input_transcript": {
      if (userBuf.complete) flushTurn(userBuf, "user");
      if (!userBuf.el) userBuf.el = appendTurnEl("user");
      userBuf.text += msg.text || "";
      userBuf.el.textContent = userBuf.text;
      if (msg.finished) {
        userBuf.complete = true;
        // User finished speaking; AI is now processing. Show that explicitly.
        if (!aiSpeaking) setOrb("idle", "Thinking…");
      }
      break;
    }

    case "output_transcript": {
      if (assistantBuf.complete) flushTurn(assistantBuf, "assistant");
      if (!assistantBuf.el) assistantBuf.el = appendTurnEl("assistant");
      assistantBuf.text += msg.text || "";
      assistantBuf.el.textContent = assistantBuf.text;
      if (msg.finished) assistantBuf.complete = true;
      break;
    }

    case "interrupted":
      nextPlayTime = outputCtx?.currentTime || 0;
      aiSpeaking = false;
      if (speakingTimeout) { clearTimeout(speakingTimeout); speakingTimeout = null; }
      setOrb("listening", "Listening");
      flushTurn(assistantBuf, "assistant");
      break;

    case "turn_complete":
      aiSpeaking = false;
      if (speakingTimeout) { clearTimeout(speakingTimeout); speakingTimeout = null; }
      flushTurn(assistantBuf, "assistant");
      flushTurn(userBuf, "user");
      setOrb("listening", "Go ahead");
      console.log("[komodo-trainer] turn complete, mic re-enabled");
      break;

    case "fatal":
      failWith(`Bridge error: ${msg.error}`);
      break;

    default:
      console.log("[komodo-trainer] unknown msg type:", msg.type, msg);
  }
}

// ----- Mute -----
function toggleMute() {
  if (!micStream) return;
  muted = !muted;
  micStream.getAudioTracks().forEach(t => (t.enabled = !muted));
  $("mute-button").textContent = muted ? "🔇 Unmute" : "🎤 Mute";
}

// ----- Step 4: end session -----
async function endSession() {
  if (endingNow) return;
  endingNow = true;
  stopTimer();

  try { if (workletNode) workletNode.disconnect(); } catch {}
  try { if (sourceNode) sourceNode.disconnect(); } catch {}
  try { if (micStream) micStream.getTracks().forEach(t => t.stop()); } catch {}
  try { if (playbackAudioEl) { playbackAudioEl.pause(); playbackAudioEl.remove(); } } catch {}
  try {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "end" }));
      ws.close(1000, "client ended");
    }
  } catch {}
  try { if (inputCtx) await inputCtx.close(); } catch {}
  try { if (outputCtx) await outputCtx.close(); } catch {}

  show("scoring");

  const transcript = buildFinalTranscript();
  if (!transcript) {
    failWith("No transcript was captured. The session ended before any speech was transcribed. Try again.");
    return;
  }

  try {
    const resp = await fetch(`/api/session/${sessionId}/transcript`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript }),
    });
    if (!resp.ok) throw new Error(`Scorer: ${resp.status} ${await resp.text()}`);
    const sc = await resp.json();
    renderScorecard(sc, transcript);
  } catch (e) {
    failWith(`Scoring failed: ${e.message}`);
  }
}

// ----- Step 5: render scorecard -----
function toTen(score, max) {
  if (!max) return 0;
  return Math.round((score / max) * 10);
}

function renderScorecard(sc, transcript) {
  const overall10 = toTen(sc.overall_score, sc.overall_max);
  const pct = overall10 * 10;
  const flagged = !!sc.safeguarding_flag;

  const scoreEl = $("overall-score");
  scoreEl.innerHTML = `${overall10}<span style="font-size:1.2rem; color:#2a4458; margin-left:2px;">/10</span>`;
  scoreEl.classList.toggle("flagged", flagged);

  const fillEl = $("overall-fill");
  fillEl.style.width = `${pct}%`;
  fillEl.classList.toggle("flagged", flagged);

  const headlineEl = $("results-headline");
  headlineEl.textContent = sc.headline;
  headlineEl.classList.toggle("flagged", flagged);

  if (flagged) {
    $("results-safeguarding").style.display = "";
    $("safeguarding-note").textContent = sc.safeguarding_note || "";
  }

  const worked = $("what-worked");
  worked.innerHTML = "";
  (sc.what_worked || []).forEach(w => {
    const li = document.createElement("li");
    li.textContent = w;
    worked.appendChild(li);
  });

  const totry = $("what-to-try");
  totry.innerHTML = "";
  (sc.what_to_try || []).forEach(w => {
    const li = document.createElement("li");
    li.textContent = w;
    totry.appendChild(li);
  });

  const critList = $("criteria-list");
  critList.innerHTML = "";
  (sc.criteria || []).forEach(c => {
    const crit10 = toTen(c.score, 3);
    const cpct = crit10 * 10;
    const div = document.createElement("div");
    div.className = "criterion";
    div.innerHTML = `
      <div class="criterion-head">
        <h4>${c.id}. ${escapeHtml(c.name)}</h4>
        <div class="criterion-score">${crit10}<span style="font-size:0.78rem; color:#2a4458;">/10</span></div>
      </div>
      <div class="criterion-bar"><div class="criterion-fill" style="width:${cpct}%"></div></div>
      <div class="criterion-evidence"><em>Evidence:</em> ${escapeHtml(c.evidence)}</div>
      <div class="criterion-totry"><strong>Try next:</strong> ${escapeHtml(c.to_try)}</div>
    `;
    critList.appendChild(div);
  });

  $("results-transcript").textContent = transcript;
  show("results");
}

function escapeHtml(s) {
  if (!s) return "";
  return String(s).replace(/[&<>"']/g, m => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]
  ));
}

loadSession();
