"""FastAPI bridge between the Streamlit hub and the Gemini-powered voice page.

Architecture
------------
The browser does NOT talk to Gemini directly. Instead:

    Browser  <--WS-->  this bridge  <--Live API-->  Gemini

This keeps the Google API key server-side and works around the @google/genai
JS SDK losing the apiVersion when constructing the Live WebSocket URL.
The Python SDK has no such issue.

Endpoints:
  GET  /                                  redirect to the voice page
  GET  /voice/...                         static voice page
  GET  /api/session/{id}                  scenario + persona summary (no secrets)
  WS   /ws/voice/{id}                     proxied Gemini Live session
  POST /api/session/{id}/transcript       saves transcript, runs Claude scorer
  GET  /api/session/{id}/scorecard        fetches scorecard
  GET  /api/health
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(override=True)

from google import genai
from google.genai import types as gtypes

import catalog
import db
from catalog.realtime import build_realtime_config
from scoring.score import score_transcript

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("komodo.bridge")

ROOT = Path(__file__).parent
VOICE_DIR = ROOT / "voice_page"

GEMINI_MODEL = os.environ.get(
    "KOMODO_GEMINI_MODEL",
    # Current native-audio Live model on the Gemini Developer API (v1beta).
    # The older `gemini-2.5-flash-preview-native-audio-dialog` name has been
    # retired and is no longer routable.
    "gemini-2.5-flash-native-audio-preview-09-2025",
)
GEMINI_API_VERSION = os.environ.get("KOMODO_GEMINI_API_VERSION", "v1beta")
# Models that accept the `enable_affective_dialog` flag. The Sep-2025 native
# audio preview model rejects it (`Unknown name enableAffectiveDialog`).
AFFECTIVE_DIALOG_MODELS: set[str] = set()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")

db.init_db()

app = FastAPI(title="Komodo AI Trainer bridge")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Static + simple GET endpoints
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    return RedirectResponse("/voice/")


@app.get("/voice/")
def voice_index():
    return FileResponse(VOICE_DIR / "index.html")


app.mount("/voice", StaticFiles(directory=VOICE_DIR, html=True), name="voice")


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    row = db.get_session(session_id)
    if not row:
        raise HTTPException(404, "Session not found")
    cfg = build_realtime_config(row["scenario_id"])
    return {
        "session_id": session_id,
        "mode": cfg["mode"],
        "scenario": {
            "id": cfg["scenario"]["id"],
            "title": cfg["scenario"]["title"],
            "brief": cfg["scenario"]["brief"],
            "watch_for": cfg["scenario"].get("watch_for", []),
            "duration_minutes": cfg["scenario"].get("duration_minutes", 10),
            "is_red_flag": cfg["is_red_flag"],
            "consent_required": cfg["scenario"].get("consent_required", False) or cfg["is_red_flag"],
        },
        "persona": {
            "id": cfg["persona"]["id"],
            "display_name": cfg["persona"]["display_name"],
            "year": cfg["persona"].get("year"),
            "profile": cfg["persona"].get("profile"),
        },
        "activity": cfg["activity"],
        "voice": cfg["voice"],
        "model": GEMINI_MODEL,
        "status": row["status"],
    }


# ---------------------------------------------------------------------------
# WebSocket proxy: browser <-> bridge <-> Gemini Live
# ---------------------------------------------------------------------------


_LANGUAGE_LABELS = {
    "en-NZ": "English (New Zealand)",
    "en-AU": "English (Australia)",
    "en-GB": "English (British)",
    "en-US": "English (US)",
    "es-ES": "Spanish",
    "es-US": "Spanish (US)",
    "fr-FR": "French",
    "de-DE": "German",
    "it-IT": "Italian",
    "pt-BR": "Portuguese (Brazilian)",
    "nl-NL": "Dutch",
    "pl-PL": "Polish",
    "ru-RU": "Russian",
    "tr-TR": "Turkish",
    "ar-XA": "Arabic",
    "hi-IN": "Hindi",
    "zh-CN": "Chinese (Simplified)",
    "ja-JP": "Japanese",
    "ko-KR": "Korean",
    "th-TH": "Thai",
    "vi-VN": "Vietnamese",
    "id-ID": "Indonesian",
}


def _language_instruction(lang_code: str) -> str:
    label = _LANGUAGE_LABELS.get(lang_code, lang_code)
    return (
        f"\n\n## Language (strict)\n"
        f"Conduct the ENTIRE session in {label} ({lang_code}). "
        f"The teacher is speaking {label}. Speak only in {label}, even if you "
        f"hear another language or accent. Do not mix languages. Do not "
        f"translate things back into other languages unless the teacher "
        f"explicitly asks you to.\n"
    )


def _build_live_config(cfg: dict, lang_code: str) -> gtypes.LiveConnectConfig:
    kwargs = dict(
        response_modalities=["AUDIO"],
        system_instruction=cfg["instructions"] + _language_instruction(lang_code),
        speech_config=gtypes.SpeechConfig(
            language_code=lang_code,
            voice_config=gtypes.VoiceConfig(
                prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(voice_name=cfg["voice"])
            ),
        ),
        input_audio_transcription=gtypes.AudioTranscriptionConfig(),
        output_audio_transcription=gtypes.AudioTranscriptionConfig(),
        # Tune server-side VAD for snappier response after the teacher finishes.
        realtime_input_config=gtypes.RealtimeInputConfig(
            automatic_activity_detection=gtypes.AutomaticActivityDetection(
                disabled=False,
                # Wait 600ms of silence (instead of the default ~1s) before
                # deciding the teacher has finished their turn.
                silence_duration_ms=600,
                # Include a bit of audio before VAD triggers so we don't clip
                # the start of words.
                prefix_padding_ms=200,
            )
        ),
    )
    if GEMINI_MODEL in AFFECTIVE_DIALOG_MODELS:
        kwargs["enable_affective_dialog"] = True
    return gtypes.LiveConnectConfig(**kwargs)


@app.websocket("/ws/voice/{session_id}")
async def voice_ws(ws: WebSocket, session_id: str, lang: str = "en-US"):
    """Proxy a Gemini Live session between the browser and Google.

    `lang` is a BCP-47 code (e.g. en-US, en-NZ, th-TH). Used to set the
    Gemini SpeechConfig language AND injected into the system instruction
    so the AI doesn't accidentally drift based on the user's geolocation.
    """
    await ws.accept()

    if not GOOGLE_API_KEY:
        await ws.send_json({"type": "fatal", "error": "GOOGLE_API_KEY not set on server"})
        await ws.close()
        return

    row = db.get_session(session_id)
    if not row:
        await ws.send_json({"type": "fatal", "error": f"Unknown session {session_id}"})
        await ws.close()
        return

    cfg = build_realtime_config(row["scenario_id"])
    live_config = _build_live_config(cfg, lang)

    client = genai.Client(
        api_key=GOOGLE_API_KEY,
        http_options={"api_version": GEMINI_API_VERSION},
    )

    log.info("WS open: session=%s scenario=%s voice=%s model=%s lang=%s",
             session_id, cfg["scenario"]["id"], cfg["voice"], GEMINI_MODEL, lang)

    try:
        async with client.aio.live.connect(model=GEMINI_MODEL, config=live_config) as live:
            await ws.send_json({
                "type": "ready",
                "voice": cfg["voice"],
                "model": GEMINI_MODEL,
                "mode": cfg["mode"],
                "lang": lang,
            })

            stop = asyncio.Event()

            async def browser_to_gemini():
                try:
                    while not stop.is_set():
                        msg = await ws.receive_json()
                        t = msg.get("type")
                        if t == "audio":
                            data = base64.b64decode(msg["data"])
                            await live.send_realtime_input(
                                audio=gtypes.Blob(data=data, mime_type="audio/pcm;rate=16000")
                            )
                        elif t == "audio_stream_end":
                            await live.send_realtime_input(audio_stream_end=True)
                        elif t == "end":
                            break
                        else:
                            log.warning("unknown browser msg type: %s", t)
                except WebSocketDisconnect:
                    log.info("Browser disconnected (session=%s)", session_id)
                except Exception:
                    log.exception("browser_to_gemini crashed")
                finally:
                    stop.set()

            async def gemini_to_browser():
                # `live.receive()` is a per-turn async iterator: it yields all
                # chunks for one model turn, then returns. We have to call it
                # again to keep listening across the rest of the conversation.
                try:
                    while not stop.is_set():
                        turn_count = 0
                        async for resp in live.receive():
                            if stop.is_set():
                                break
                            turn_count += 1
                            if getattr(resp, "data", None):
                                await ws.send_json({
                                    "type": "audio",
                                    "data": base64.b64encode(resp.data).decode("ascii"),
                                })
                            sc = getattr(resp, "server_content", None)
                            if sc is not None:
                                in_tr = getattr(sc, "input_transcription", None)
                                if in_tr and (in_tr.text or in_tr.finished):
                                    await ws.send_json({
                                        "type": "input_transcript",
                                        "text": in_tr.text or "",
                                        "finished": bool(getattr(in_tr, "finished", False)),
                                    })
                                out_tr = getattr(sc, "output_transcription", None)
                                if out_tr and (out_tr.text or out_tr.finished):
                                    await ws.send_json({
                                        "type": "output_transcript",
                                        "text": out_tr.text or "",
                                        "finished": bool(getattr(out_tr, "finished", False)),
                                    })
                                if getattr(sc, "interrupted", False):
                                    await ws.send_json({"type": "interrupted"})
                                if getattr(sc, "turn_complete", False):
                                    await ws.send_json({"type": "turn_complete"})
                        # Inner iterator ended - turn finished. Loop back and
                        # call receive() again for the next turn.
                        log.info("session %s: turn ended (%d chunks), waiting for next",
                                 session_id, turn_count)
                except Exception:
                    log.exception("gemini_to_browser crashed")
                finally:
                    stop.set()

            await asyncio.gather(browser_to_gemini(), gemini_to_browser())
    except Exception as e:
        log.exception("voice_ws fatal")
        try:
            await ws.send_json({"type": "fatal", "error": f"{type(e).__name__}: {e}"})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
        log.info("WS close: session=%s", session_id)


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------


class TranscriptRequest(BaseModel):
    transcript: str


@app.post("/api/session/{session_id}/transcript")
def submit_transcript(session_id: str, req: TranscriptRequest):
    row = db.get_session(session_id)
    if not row:
        raise HTTPException(404, "Session not found")
    transcript = req.transcript.strip()
    if not transcript:
        raise HTTPException(400, "Empty transcript")

    db.save_transcript(session_id, transcript)
    cfg = build_realtime_config(row["scenario_id"])
    activity = None
    if cfg["scenario"].get("activity_id"):
        activity = catalog.activity_as_dict(
            catalog.get_activity(cfg["scenario"]["activity_id"])
        )
    sc = score_transcript(
        mode=cfg["mode"],
        scenario=cfg["scenario"],
        persona=cfg["persona"],
        activity=activity,
        transcript=transcript,
    )
    db.save_scorecard(session_id, sc)
    import json
    return JSONResponse(json.loads(sc.to_json()))


@app.get("/api/session/{session_id}/scorecard")
def get_scorecard(session_id: str):
    row = db.get_session(session_id)
    if not row:
        raise HTTPException(404, "Session not found")
    if not row.get("scorecard"):
        return JSONResponse({"status": row["status"]})
    return JSONResponse(row["scorecard"])


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "google_key_set": bool(GOOGLE_API_KEY),
        "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "model": GEMINI_MODEL,
    }
