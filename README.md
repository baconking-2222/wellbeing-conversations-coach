# Wellbeing Conversations Coach

Staff-only voice training tool built around the 23 activities in Komodo's Classroom Wellbeing Flash Cards. Two friendly modes:

- **🎴 Lead a class** - the AI plays a composite class of students; you rehearse running a flash-card activity.
- **💛 Support a student** - the AI plays a single student in distress; you read the moment, validate, pick an activity, and guide them through it.

After each session, Claude scores the transcript against a 7-criterion rubric (displayed out of 10) and returns specific feedback. Red-flag safeguarding scenarios cap the score if you try to flash-card past a moment that needs escalation.

## How it's built

Two services:

| Service | What | How to run |
|---|---|---|
| **Streamlit hub** | Pretty UI: scenarios, filters, history | `streamlit run streamlit_app.py` |
| **FastAPI bridge** | Proxies Gemini Live voice + serves the voice page + runs Claude scorer | `uvicorn server:app --port 8000` |

**Voice provider:** Google Gemini Live (native audio model). **Scoring:** Anthropic Claude.

## Run locally

```bash
cd ~/Claude\ Projects/komodo-ai-trainer
cp .env.example .env   # then fill in ANTHROPIC_API_KEY and GOOGLE_API_KEY
./run.sh
```

Streamlit opens at <http://localhost:8511>, bridge at <http://localhost:8000>.

## Deploy

See [DEPLOY.md](DEPLOY.md) for the step-by-step (Streamlit Community Cloud + Hugging Face Spaces, both free).

## Project layout

```
wellbeing-conversations-coach/
├── streamlit_app.py          # main hub UI
├── server.py                 # FastAPI bridge (voice + scorer endpoints)
├── db.py                     # SQLite session store
├── Dockerfile                # for the bridge on HF Spaces
├── catalog/
│   ├── _activities.py        # 23 wellbeing activities (self-contained copy)
│   ├── augmentations.json    # trainer tags per activity
│   ├── personas.json         # 9 students + 4 classes
│   ├── scenarios.json        # 5 Mode-1 + 7 Mode-2 scenarios
│   └── realtime.py           # builds the Gemini Live system prompt per scenario
├── scoring/
│   ├── rubrics.py            # 7-criterion rubric per mode
│   └── score.py              # Claude scorer
├── voice_page/               # static HTML+JS+CSS voice client
└── prompts/                  # Claude scorer prompts
```
