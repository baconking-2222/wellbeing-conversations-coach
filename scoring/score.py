"""Claude-powered transcript scorer. Returns structured Scorecard objects."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from scoring.rubrics import Criterion, max_score, rubric_as_markdown, rubric_for

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_MODEL = os.environ.get("KOMODO_SCORER_MODEL", "claude-sonnet-4-6")


@dataclass
class CriterionScore:
    id: int
    name: str
    score: int
    evidence: str
    to_try: str


@dataclass
class Scorecard:
    mode: str
    scenario_id: str
    headline: str
    what_worked: list[str]
    what_to_try: list[str]
    criteria: list[CriterionScore]
    overall_score: int
    overall_max: int
    safeguarding_flag: bool
    safeguarding_note: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "mode": self.mode,
                "scenario_id": self.scenario_id,
                "headline": self.headline,
                "what_worked": self.what_worked,
                "what_to_try": self.what_to_try,
                "criteria": [c.__dict__ for c in self.criteria],
                "overall_score": self.overall_score,
                "overall_max": self.overall_max,
                "safeguarding_flag": self.safeguarding_flag,
                "safeguarding_note": self.safeguarding_note,
            },
            indent=2,
        )


def _scorecard_tool(rubric: list[Criterion]) -> dict:
    """Tool schema forcing Claude to emit the right shape."""
    return {
        "name": "report_scorecard",
        "description": "Submit the completed scorecard for the teacher's practice session.",
        "input_schema": {
            "type": "object",
            "required": ["criteria", "headline", "what_worked", "what_to_try", "safeguarding_flag"],
            "properties": {
                "headline": {
                    "type": "string",
                    "description": "One sentence summary — the single biggest takeaway.",
                },
                "what_worked": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-3 specific things the teacher did well, with brief evidence.",
                    "minItems": 1,
                    "maxItems": 4,
                },
                "what_to_try": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-3 concrete things to try next time, in order of priority.",
                    "minItems": 1,
                    "maxItems": 4,
                },
                "criteria": {
                    "type": "array",
                    "minItems": len(rubric),
                    "maxItems": len(rubric),
                    "items": {
                        "type": "object",
                        "required": ["id", "score", "evidence", "to_try"],
                        "properties": {
                            "id": {
                                "type": "integer",
                                "enum": [c.id for c in rubric],
                            },
                            "score": {
                                "type": "integer",
                                "enum": [0, 1, 2, 3],
                            },
                            "evidence": {
                                "type": "string",
                                "description": "≤20-word quote or paraphrase from the transcript justifying this score.",
                            },
                            "to_try": {
                                "type": "string",
                                "description": "One concrete sentence the teacher could try next time.",
                            },
                        },
                    },
                },
                "safeguarding_flag": {
                    "type": "boolean",
                    "description": "True if this session contained a safeguarding moment the teacher should have escalated.",
                },
                "safeguarding_note": {
                    "type": "string",
                    "description": "If safeguarding_flag is true, one sentence on what the safeguarding moment was and whether the teacher handled it.",
                },
            },
        },
    }


def _build_prompt(
    mode: str,
    scenario: dict,
    persona: dict,
    activity: dict | None,
) -> str:
    template_path = _PROMPTS_DIR / f"scorer_{mode}.md"
    template = template_path.read_text()

    rubric_md = rubric_as_markdown(mode)
    watch_for = "\n".join(f"- {w}" for w in scenario.get("watch_for", []))

    if mode == "mode1":
        class_summary = (
            f"{persona['display_name']} ({persona['year']}, ages {persona['ages_years']}). "
            + "Voices in the class: "
            + "; ".join(f"{v['name']} — {v['trait']}" for v in persona["voices"])
        )
        return template.format(
            scenario_title=scenario["title"],
            class_summary=class_summary,
            activity_name=activity["name"],
            activity_age=activity["age"],
            activity_objective=activity["objective"],
            activity_instructions=activity["instructions"],
            scenario_brief=scenario["brief"],
            watch_for=watch_for,
            rubric=rubric_md,
        )

    student_summary = (
        f"{persona['display_name']} ({persona['year']}, age {persona['age_years']}). "
        f"Profile: {persona['profile']}. Opening state: {persona['opening_state']}"
    )
    is_red_flag = scenario.get("is_red_flag", False)
    if is_red_flag:
        red_flag_block = (
            "## ⚠️ Red-flag scenario\n"
            f"This is a safeguarding training scenario (type: {scenario.get('red_flag_type', 'unspecified')}). "
            "The right response involves recognising what's being disclosed and escalating to the appropriate "
            "professional — NOT using a flash-card activity as a substitute."
        )
        safeguarding_rule = (
            "This scenario is flagged `is_red_flag: true`. If the teacher scored 0 or 1 on Criterion 7 "
            "(Safeguarding awareness) — i.e. they missed the disclosure or tried to flash-card past it — "
            "cap the overall score at 1/21 in `criteria`, set `safeguarding_flag: true`, and write a "
            "`safeguarding_note` naming what was missed. The headline must lead with the safeguarding miss."
        )
    else:
        red_flag_block = ""
        safeguarding_rule = (
            "This scenario is not flagged as red-flag, but if anything in the transcript suggests a "
            "real safeguarding concern that the teacher should have escalated, set `safeguarding_flag: true` "
            "and explain in `safeguarding_note`."
        )

    return template.format(
        scenario_title=scenario["title"],
        student_summary=student_summary,
        scenario_brief=scenario["brief"],
        red_flag_block=red_flag_block,
        watch_for=watch_for,
        rubric=rubric_md,
        safeguarding_rule=safeguarding_rule,
    )


def score_transcript(
    *,
    mode: str,
    scenario: dict,
    persona: dict,
    activity: dict | None,
    transcript: str,
) -> Scorecard:
    """Score a practice-session transcript. Returns a structured Scorecard."""
    if mode not in ("mode1", "mode2"):
        raise ValueError(f"Unknown mode: {mode}")

    rubric = rubric_for(mode)
    prompt = _build_prompt(mode, scenario, persona, activity)

    client = Anthropic()
    resp = client.messages.create(
        model=_MODEL,
        max_tokens=2000,
        tools=[_scorecard_tool(rubric)],
        tool_choice={"type": "tool", "name": "report_scorecard"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"{prompt}\n\n"
                    "## Transcript of the practice session\n"
                    "```\n"
                    f"{transcript.strip()}\n"
                    "```"
                ),
            }
        ],
    )

    payload = None
    for block in resp.content:
        if block.type == "tool_use" and block.name == "report_scorecard":
            payload = block.input
            break
    if payload is None:
        raise RuntimeError("Claude did not return a report_scorecard tool call")

    name_lookup = {c.id: c.name for c in rubric}
    criteria = [
        CriterionScore(
            id=c["id"],
            name=name_lookup.get(c["id"], f"Criterion {c['id']}"),
            score=c["score"],
            evidence=c["evidence"],
            to_try=c["to_try"],
        )
        for c in payload["criteria"]
    ]
    criteria.sort(key=lambda c: c.id)

    overall = sum(c.score for c in criteria)
    safeguarding_flag = bool(payload.get("safeguarding_flag", False))

    if scenario.get("is_red_flag") and any(c.id == 7 and c.score <= 1 for c in criteria):
        overall = min(overall, 1)
        safeguarding_flag = True

    return Scorecard(
        mode=mode,
        scenario_id=scenario["id"],
        headline=payload["headline"],
        what_worked=list(payload["what_worked"]),
        what_to_try=list(payload["what_to_try"]),
        criteria=criteria,
        overall_score=overall,
        overall_max=max_score(mode),
        safeguarding_flag=safeguarding_flag,
        safeguarding_note=payload.get("safeguarding_note", ""),
        raw=dict(payload),
    )
