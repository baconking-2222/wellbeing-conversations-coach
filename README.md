# Komodo AI Trainer

Staff-only voice training tool built around the 23 activities in Komodo's Classroom Wellbeing Flash Cards. Two modes:

- **Mode 1 - Deliver an activity to a class.** AI plays a composite class of students. Teacher rehearses running a flash-card activity.
- **Mode 2 - Respond to a distressed student.** AI plays a single student in distress. Teacher reads the moment, validates, picks an appropriate activity, and guides them through it.

After each session, Claude scores the transcript against a 7-criterion rubric and returns specific feedback. Red-flag safeguarding scenarios cap the score if the teacher tries to flash-card past a moment that requires escalation.

See [PLAN.md](PLAN.md) for the full design.

## Build status

| Phase | What it covers | Status |
|---|---|---|
| 0 | Activity catalog, personas, scenarios | ✅ Done |
| 1 | Streamlit shell + Claude scorer (paste-transcript test mode) | ✅ Done |
| 2 | Voice page (OpenAI Realtime API) | ⏳ Next |
| 3 | Wire voice page → bridge → scorer | ⏳ |
| 4 | Polish + history view + Komodo brand | ⏳ |

## Run it

```bash
cd ~/Claude\ Projects/komodo-ai-trainer
cp .env.example .env       # then fill in ANTHROPIC_API_KEY
pip3 install --user -r requirements.txt
./run.sh
```

The app opens at <http://localhost:8501>.

## Phase 1 (right now): paste-transcript mode

Voice isn't wired in yet, so you test the scorer by pasting a transcript of what was (or could have been) said. This lets us tune the rubric and personas before we deal with WebRTC latency.

Flow: **Practice → Mode → Scenario → Start → Paste transcript → Score it**. Past sessions live in **History**.

## Activity catalog

The 23 activities come from `~/Claude Projects/komodo-flashcards/activities.py` - that's the single source of truth across both Komodo apps. The trainer adds `best_for`, `fit_notes`, and `avoid_if` tags in `catalog/augmentations.json`.

## Project layout

```
komodo-ai-trainer/
├── streamlit_app.py          # main hub
├── db.py                     # SQLite session store
├── catalog/
│   ├── __init__.py           # imports activities from sibling flashcards project
│   ├── augmentations.json    # trainer-specific tags per activity
│   ├── personas.json         # 9 students (incl. 2 red-flag) + 4 classes
│   └── scenarios.json        # 5 Mode-1 + 7 Mode-2 scenarios (2 red-flag)
├── scoring/
│   ├── rubrics.py            # 7-criterion rubric per mode with anchors
│   └── score.py              # Claude scorer (sonnet-4-6 via tool_use)
├── prompts/
│   ├── scorer_mode1.md
│   └── scorer_mode2.md
├── data/
│   └── sessions.sqlite       # local session history (created on first run)
├── voice_page/               # Phase 2 (not yet built)
└── PLAN.md
```
