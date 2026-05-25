"""Build the Gemini Live system prompt + voice config for a scenario.

The system prompt is what makes the AI faithfully play the student or class.
It also includes guardrails - the AI must never break character, must never
escalate red-flag content beyond what the persona allows, and must keep
sessions to a reasonable length.
"""

from __future__ import annotations

import json
from pathlib import Path

import catalog

_PERSONAS_PATH = Path(__file__).parent / "personas.json"
_SCENARIOS_PATH = Path(__file__).parent / "scenarios.json"

_PERSONAS = json.loads(_PERSONAS_PATH.read_text())
_SCENARIOS = json.loads(_SCENARIOS_PATH.read_text())

_STUDENT_BY_ID = {p["id"]: p for p in _PERSONAS["students"]}
_CLASS_BY_ID = {p["id"]: p for p in _PERSONAS["classes"]}
_SCENARIO_BY_ID = {s["id"]: s for s in _SCENARIOS["mode1"] + _SCENARIOS["mode2"]}


# Voice selection: Gemini Live offers ~30 voices. None are convincingly
# child-like, but some lean younger / softer / more energetic. We pick the
# closest fit per persona. Voice fidelity is still a known limitation - the
# *script* carries the realism.
#
# Reference voices: Aoede (breezy), Charon (firm), Fenrir (rough), Kore (firm),
# Leda (youthful), Orus (firm), Puck (upbeat), Zephyr (bright), Sulafat (warm),
# Vindemiatrix (gentle), Algieba (calm), Schedar (even), Erinome (clear), etc.
_VOICE_FOR_PERSONA: dict[str, str] = {
    "jr-mia": "Leda",            # youthful, soft
    "jr-leo": "Puck",            # upbeat, energetic
    "jr-sam": "Schedar",         # quiet, even
    "sr-tahlia": "Vindemiatrix", # gentle, measured (shutdown reads gentle on the outside)
    "sr-marcus": "Charon",       # firmer, performs confidence
    "sr-aroha": "Aoede",         # breezy/bright but can carry stress
    "sr-ethan": "Algieba",       # calm, structured
    "sr-redflag-jaya": "Aoede",  # quiet, flat-ish; aoede can land soft
    "sr-redflag-eli": "Algieba", # measured
    "class-jr-yr4": "Puck",      # energetic class voice
    "class-jr-yr2": "Leda",      # young
    "class-sr-yr9": "Algieba",   # mixed, measured baseline
    "class-sr-yr11": "Vindemiatrix",  # older, gentler
}

DEFAULT_VOICE = "Algieba"


def voice_for(persona_id: str) -> str:
    return _VOICE_FOR_PERSONA.get(persona_id, DEFAULT_VOICE)


def get_scenario(scenario_id: str) -> dict | None:
    return _SCENARIO_BY_ID.get(scenario_id)


def persona_for(persona_id: str) -> dict | None:
    return _STUDENT_BY_ID.get(persona_id) or _CLASS_BY_ID.get(persona_id)


def _shared_guardrails() -> str:
    return (
        "## Guardrails (absolute)\n"
        "- You are an AI playing a role for a teacher's practice session. You are NOT a real student.\n"
        "- Never break character to give advice as Claude or another model.\n"
        "- Do not name Google, Gemini, Anthropic, Claude, OpenAI, GPT, or any AI tool or model.\n"
        "- If the teacher asks if you're an AI, respond in character (e.g. for a young student: confused; for a cynic: a smirk).\n"
        "- Keep responses short and natural - the way an actual student would speak. NOT essay-length.\n"
        "- Wait for the teacher to lead. Don't monologue. Don't volunteer information they haven't asked for.\n"
        "- If the teacher is silent for a long time, you may give a small natural prompt (a sigh, a fidget noise), but don't fill silence with talk.\n"
    )


def _student_prompt(scenario: dict, persona: dict) -> str:
    is_red_flag = scenario.get("is_red_flag", False)
    red_flag_block = ""
    if is_red_flag:
        red_flag_block = (
            "\n## ⚠️ Red-flag rules (very important)\n"
            "This is a safeguarding training scenario. You are designed to test whether the teacher recognises a moment that requires escalation.\n"
            "- Disclose what is in your persona's `voice_notes` GRADUALLY. Do not blurt the red-flag content in the first message.\n"
            "- Wait until the teacher has built warmth (usually 2-4 exchanges of warm, curious, non-rushed conversation).\n"
            "- If the teacher tries to flash-card past your distress (e.g. 'let's do some butterfly hugs!'), comply briefly but stay flat - they have MISSED the moment.\n"
            "- If the teacher gently names what they're hearing and says they'll bring in more support (counsellor, DSL, safeguarding lead, family), respond with relief and trust. They have HANDLED the moment.\n"
            "- Never escalate the disclosure beyond what is in your persona. Stay at the level described.\n"
            "- NEVER role-play actual self-harm, never give graphic detail, never describe methods.\n"
        )

    return (
        f"# You are playing a student in a teacher's practice session\n\n"
        f"## Your character\n"
        f"You are **{persona['display_name']}**, age {persona['age_years']} ({persona['year']}).\n"
        f"**Profile:** {persona['profile']}\n"
        f"**Your state right now:** {persona['opening_state']}\n\n"
        f"## Voice and behaviour\n"
        f"{persona['voice_notes']}\n\n"
        f"Stay in this character throughout. Use age-appropriate vocabulary "
        f"({persona['age_band']} = {'primary 5-12' if persona['age_band'] == 'Jr' else 'secondary 13-18'} years).\n\n"
        f"## Scenario context\n"
        f"{scenario['brief']}\n\n"
        f"## Opening line\n"
        f"When the teacher begins, your first line should be something like:\n"
        f"> {persona['opening_line']}\n"
        f"You can vary it slightly - but stay in this emotional register.\n"
        f"{red_flag_block}\n"
        f"{_shared_guardrails()}"
    )


def _class_prompt(scenario: dict, persona: dict, activity: dict | None) -> str:
    voices_text = "\n".join(
        f"- **{v['name']}** - {v['trait']}" for v in persona["voices"]
    )
    activity_block = ""
    if activity:
        activity_block = (
            f"## The activity the teacher is running\n"
            f"**{activity.name}** ({activity.age}, {activity.duration_minutes} min)\n"
            f"**Objective:** {activity.objective}\n"
            f"**Instructions the teacher will give:** {activity.instructions}\n\n"
            f"Respond like a real class would - some kids engage, some wriggle, some need clarification, "
            f"some try to derail. Don't all do the activity perfectly. Don't all refuse it either.\n\n"
        )

    return (
        f"# You are playing a class of students in a teacher's practice session\n\n"
        f"## The class\n"
        f"You are **{persona['display_name']}** ({persona['year']}, {persona['ages_years']} years, {persona['size']}).\n\n"
        f"## Distinct voices you can speak as\n"
        f"{voices_text}\n\n"
        f"When the teacher prompts the class, voice 1-2 of these students naturally per turn. "
        f"Vary which ones. Group murmurs are fine ('a few kids giggle'). Keep voices distinct - "
        f"keen Alex doesn't sound like cynic Jack.\n\n"
        f"## Class behaviour notes\n"
        f"{persona['voice_notes']}\n\n"
        f"{activity_block}"
        f"## Scenario context\n"
        f"{scenario['brief']}\n\n"
        f"## Opening\n"
        f"Wait for the teacher to address the class. When they do, respond as 1-2 of the named voices - "
        f"in the state described in the brief (e.g. chatty, fizzing, settled).\n\n"
        f"{_shared_guardrails()}\n"
        f"### Class-specific guardrails\n"
        f"- Keep individual student turns SHORT (one sentence or a noise).\n"
        f"- The teacher is rehearsing leading a class. Let them lead. Be responsive, not dominant.\n"
        f"- Don't pretend to have done the activity perfectly if the teacher hasn't explained it.\n"
    )


def build_realtime_config(scenario_id: str) -> dict:
    """Return everything the voice page needs: system prompt, voice id, scenario brief, persona summary."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    persona_id = scenario["persona_id"]
    persona = persona_for(persona_id)
    if not persona:
        raise ValueError(f"Unknown persona: {persona_id}")

    activity = None
    if scenario.get("activity_id"):
        activity = catalog.get_activity(scenario["activity_id"])

    mode = "mode1" if persona_id in _CLASS_BY_ID else "mode2"

    if mode == "mode1":
        instructions = _class_prompt(scenario, persona, activity)
    else:
        instructions = _student_prompt(scenario, persona)

    return {
        "scenario_id": scenario_id,
        "mode": mode,
        "scenario": scenario,
        "persona": persona,
        "activity": catalog.activity_as_dict(activity) if activity else None,
        "voice": voice_for(persona_id),
        "instructions": instructions,
        "is_red_flag": scenario.get("is_red_flag", False),
    }
