"""Scorecard rubrics for both modes. 0-3 per criterion with anchor descriptors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Criterion:
    id: int
    name: str
    short: str
    descriptors: dict[int, str]


MODE1_RUBRIC: list[Criterion] = [
    Criterion(
        id=1,
        name="Setup & framing",
        short="Did the teacher set the activity up well - naming it, giving a brief purpose, settling the room?",
        descriptors={
            0: "Jumped in cold with no setup",
            1: "Named the activity but gave no reason for it",
            2: "Named the activity and gave a brief one-line purpose",
            3: "Settled the room, named the activity, gave a purpose students could hold onto",
        },
    ),
    Criterion(
        id=2,
        name="Clarity of instructions",
        short="Could a student follow each step without confusion?",
        descriptors={
            0: "Steps confusing or missing - students wouldn't be able to follow",
            1: "Most steps clear but at least one was unclear or out of order",
            2: "All steps clear, ordered, and well-described",
            3: "Crystal clear AND anticipated likely confusions or questions before they arose",
        },
    ),
    Criterion(
        id=3,
        name="Age-appropriate language",
        short="Did the vocabulary, tone, and examples match the age band of the class?",
        descriptors={
            0: "Wrong register - language for the wrong age group",
            1: "Mostly right register with some misjudged moments",
            2: "Right register throughout",
            3: "Right register AND used examples or framing that landed specifically for this age group",
        },
    ),
    Criterion(
        id=4,
        name="Pacing & tone",
        short="Was the delivery calm and unhurried, leaving breathing space for students to actually do the activity?",
        descriptors={
            0: "Rushed or flat - students had no space to engage",
            1: "Some pauses but mostly hurried OR mostly slow but lifeless",
            2: "Calm, unhurried delivery with proper breathing space",
            3: "Calm, unhurried AND visibly sensitive to the room's energy - adapting tempo to what they needed",
        },
    ),
    Criterion(
        id=5,
        name="Modelling & check-ins",
        short="Did the teacher demonstrate where helpful, check students were with them, and notice what they were doing?",
        descriptors={
            0: "Did not model and did not check understanding",
            1: "Either modelled OR checked once, not both",
            2: "Modelled where useful and checked understanding at least once",
            3: "Modelled, checked in, and named what they noticed in students - making them feel seen",
        },
    ),
    Criterion(
        id=6,
        name="Handling wobbles",
        short="When students went off-task, giggled, or pushed back, did the teacher hold the room without escalating?",
        descriptors={
            0: "Ignored or escalated - lost the room",
            1: "Addressed the wobble but lost focus in the process",
            2: "Addressed calmly and brought focus back",
            3: "Used the wobble - named it warmly, used it to deepen the activity, or gently brought a specific student back",
        },
    ),
    Criterion(
        id=7,
        name="Closure & integration",
        short="Did the teacher bring the activity to a meaningful close - not just stopping, but reflecting and pointing forward?",
        descriptors={
            0: "Activity just stopped with no closure",
            1: "Closed the activity (e.g. 'okay, well done') but no reflection",
            2: "Closed and offered a brief reflection on what they noticed",
            3: "Closed, reflected, AND pointed students to when they could use this themselves outside of class",
        },
    ),
]


MODE2_RUBRIC: list[Criterion] = [
    Criterion(
        id=1,
        name="Attunement",
        short="Did the teacher read the student before reacting - noticing body language, tone, what they say and don't say?",
        descriptors={
            0: "Misread or ignored the student's actual state",
            1: "Noticed something but didn't act on it",
            2: "Read the emotion and intensity accurately",
            3: "Read the emotion, intensity, AND what was underneath - and the student felt understood without having to spell it out",
        },
    ),
    Criterion(
        id=2,
        name="Validation",
        short="Did the teacher name and normalise the feeling before suggesting any tool or fix?",
        descriptors={
            0: "Went straight to fixing or problem-solving",
            1: "Briefly acknowledged the feeling but pivoted to a tool too fast",
            2: "Named and normalised the feeling before offering anything",
            3: "Named, normalised, AND made the student feel genuinely seen - building trust before any activity was even mentioned",
        },
    ),
    Criterion(
        id=3,
        name="Activity selection",
        short="Did the teacher pick an activity that genuinely fits this student, their age, and their current state?",
        descriptors={
            0: "Chose an activity that was a poor fit (e.g. guided imagery for a dysregulated child, stomping for a shutdown teen)",
            1: "Okay fit but not great - could have chosen something better",
            2: "Good fit for the student, age, and state",
            3: "Excellent fit AND explained to the student why this one - making the choice feel collaborative",
        },
    ),
    Criterion(
        id=4,
        name="Activity delivery",
        short="When the activity ran, was it delivered with the same clarity, pacing, and warmth we'd expect from a Mode 1 lesson?",
        descriptors={
            0: "Confused, rushed, or didn't actually deliver the activity",
            1: "Got through it but the delivery was flat or unclear",
            2: "Clear, calm delivery",
            3: "Clear, calm, warm delivery - same bar as a strong Mode 1 lesson",
        },
    ),
    Criterion(
        id=5,
        name="Pacing & patience",
        short="If the student resisted or went slowly, did the teacher adapt rather than push through?",
        descriptors={
            0: "Pushed through resistance and made things worse",
            1: "Noticed resistance but didn't adapt",
            2: "Adapted, slowed down, gave space",
            3: "Stayed alongside without agenda - let the student set the tempo, no rushing",
        },
    ),
    Criterion(
        id=6,
        name="Closure & next step",
        short="Did the conversation end with the student feeling safer, with a sense of what to do if it returns?",
        descriptors={
            0: "Ended abruptly - student left without resolution",
            1: "Checked in briefly at the end",
            2: "Checked in AND named what helped",
            3: "Checked in, named what helped, AND planned with the student what to do if it returns",
        },
    ),
    Criterion(
        id=7,
        name="Safeguarding awareness",
        short="Did the teacher recognise when this needed to be escalated beyond a flash card - and act appropriately?",
        descriptors={
            0: "Missed clear safeguarding red flags entirely",
            1: "Noticed something concerning but tried to flash-card it away",
            2: "Noticed concerning content and paused appropriately",
            3: "Stopped the activity, listened, and escalated to the right person (counsellor, DSL, safeguarding lead) - no improvising, no false promises of confidentiality",
        },
    ),
]


def rubric_for(mode: str) -> list[Criterion]:
    if mode == "mode1":
        return MODE1_RUBRIC
    if mode == "mode2":
        return MODE2_RUBRIC
    raise ValueError(f"Unknown mode: {mode}")


def max_score(mode: str) -> int:
    return len(rubric_for(mode)) * 3


def rubric_as_markdown(mode: str) -> str:
    """Render the rubric as a markdown block for inclusion in scorer prompts."""
    lines = []
    for c in rubric_for(mode):
        lines.append(f"**{c.id}. {c.name}** - {c.short}")
        for score, desc in c.descriptors.items():
            lines.append(f"  - **{score}**: {desc}")
        lines.append("")
    return "\n".join(lines)
