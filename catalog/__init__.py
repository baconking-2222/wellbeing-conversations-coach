"""Source of truth for the 23 flash-card activities.

The Activity dataclass + ACTIVITIES list live in `_activities.py` in this
folder. That file is a verbatim copy of the same file in the sibling
`komodo-flashcards` project. We keep it self-contained here so the
trainer can be deployed standalone (e.g. Streamlit Cloud / HF Spaces).

If the canonical flash-cards copy is ever updated, re-sync by running:
    cp ~/Claude\\ Projects/komodo-flashcards/activities.py catalog/_activities.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ._activities import ACTIVITIES, Activity, get_activity  # noqa: E402

_AUGMENTATIONS_PATH = Path(__file__).parent / "augmentations.json"
_AUGMENTATIONS: dict[str, dict] = json.loads(_AUGMENTATIONS_PATH.read_text())


def augmentation(activity_id: str) -> dict:
    """Trainer-specific tags layered on top of the Activity record.

    Keys: best_for (list[str]), fit_notes (str), avoid_if (list[str]).
    """
    return _AUGMENTATIONS.get(activity_id, {"best_for": [], "fit_notes": "", "avoid_if": []})


def activity_as_dict(activity: Activity) -> dict:
    """Serialise an Activity + its augmentations for prompts and the voice page."""
    base = asdict(activity)
    base.update(augmentation(activity.id))
    return base


def all_activities() -> list[Activity]:
    return list(ACTIVITIES)


__all__ = [
    "ACTIVITIES",
    "Activity",
    "get_activity",
    "augmentation",
    "activity_as_dict",
    "all_activities",
]
