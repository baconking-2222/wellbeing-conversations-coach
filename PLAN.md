# Komodo AI Trainer — Build Plan

A staff-only voice training tool for school teachers and pastoral staff. Built around the 23 wellbeing activities in Komodo's Classroom Wellbeing Flash Cards. Inspired by Gong's AI Trainer.

---

## 1. Guiding principles

1. **Staff only, never students.** No AI chatbot a student ever talks to. This product trains the adults who care for them.
2. **Voice-first.** The whole point is rehearsal that feels real. Text mode is a debugging tool, not the experience.
3. **Safeguarding is not optional.** If a teacher tries to "flash-card their way out of" something that needs escalation, the scorecard tells them so.
4. **Local first.** Runs on Chris's Mac for the trial. No hosting, no auth, no database service. Same operational shape as `komodo-dashboard` and `komodo-flashcards`.
5. **The flash-card deck is the source of truth.** The product never invents activities. It teaches the 23 that exist.

---

## 2. Modes

### Mode 1 — Teacher delivers an activity
- AI plays a small composite class (e.g. Yr 4: one keen, one wriggly, one shy, one cynic).
- Teacher chooses an activity from the deck and runs it.
- Scored on delivery quality.

### Mode 2 — Teacher responds to a distressed student
- AI plays a single student in some level of distress (anxious / shutdown / defiant / dysregulated / tearful / overloaded).
- Teacher reads the situation, validates, chooses an appropriate activity, guides them through it.
- Scored on attunement, choice, delivery, closure, and safeguarding judgement.

Both modes ship in v1. Home screen is a mode picker.

---

## 3. Architecture

```
~/Claude Projects/komodo-ai-trainer/
├── streamlit_app.py            # Hub: mode + scenario picker, scorecards, history
├── voice_page/                 # Static voice client (opened in new tab)
│   ├── index.html
│   ├── voice.js                # OpenAI Realtime via WebRTC
│   └── style.css               # Komodo brand
├── catalog/
│   ├── activities.json         # The 23 flash-card activities, structured
│   ├── personas.json           # Student + class personas
│   └── scenarios.json          # Pre-built scenario briefs (Mode 1 + Mode 2)
├── prompts/
│   ├── persona_system.md       # System prompt template for AI student/class
│   ├── scorer_mode1.md         # Claude prompt for Mode 1 scoring
│   └── scorer_mode2.md         # Claude prompt for Mode 2 scoring
├── scoring/
│   ├── rubrics.py              # Mode 1 + Mode 2 rubrics as Python objects
│   └── score.py                # Calls Claude, returns structured score
├── data/
│   └── sessions.sqlite         # Local SQLite — transcripts, scores, history
├── server.py                   # Tiny FastAPI bridge: receives transcripts from voice page, runs scorer
├── requirements.txt
├── .env.example                # OPENAI_API_KEY, ANTHROPIC_API_KEY
└── README.md
```

**Why a tiny FastAPI bridge?** Streamlit can't receive HTTP POSTs from the voice page directly. A separate FastAPI process on localhost:8765 takes the transcript when the session ends, writes it to SQLite with status `scored`, and Streamlit polls/refreshes to display it.

**Flow:**
1. Teacher opens Streamlit, picks mode, picks scenario, hits **Start practice**.
2. Streamlit writes a `pending` session row to SQLite with the scenario brief and persona config, then opens the voice page in a new tab with `?session=<id>`.
3. Voice page fetches the scenario config from the bridge, opens an OpenAI Realtime connection with the persona as the system prompt, runs the conversation.
4. When teacher hits **End session** (or time runs out), voice page POSTs the transcript to the bridge.
5. Bridge calls `scoring/score.py` (Claude sonnet-4-6 with the right rubric), writes scores to SQLite.
6. Teacher returns to Streamlit tab, sees the scorecard.

---

## 4. Activity catalog

Extracted from the PDF once and frozen as `activities.json`. Each entry:

```json
{
  "id": "five-senses-check-in",
  "title": "Five senses check-in",
  "age": "all",
  "objective": "Mindfulness and emotional regulation through engaging the senses...",
  "instructions": "Name 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, 1 thing you can taste.",
  "props_needed": false,
  "best_for": ["grounding", "anxiety", "transitions"],
  "fit_notes": "Works for almost everything. Easy entry-level activity."
}
```

23 activities total. I'll generate this in Phase 0 from the PDF text I've already extracted.

---

## 5. Personas

### Mode 2 (single student)

| Code | Year | Profile | State at session start |
|---|---|---|---|
| `jr-mia` | Yr 3 | Anxious, fidgety | Worried about a spelling test in 10 min |
| `jr-leo` | Yr 2 | Dysregulated, post-PE | Bouncing, laughing loudly, can't sit |
| `jr-sam` | Yr 5 | Withdrawn | Head down after a lunchtime friend incident |
| `sr-tahlia` | Yr 9 | Shutdown, snapped at peer | Arms folded, "leave me alone" |
| `sr-marcus` | Yr 10 | Cynical / defiant | "This wellbeing stuff is cringe" |
| `sr-aroha` | Yr 12 | Tearful, exam stress | "I haven't slept, I can't do this" |
| `sr-ethan` | Yr 8 | Neurodivergent, sensory overload | Hands over ears in noisy corridor |
| `sr-redflag-jaya` | Yr 10 | **Red-flag** | Hints at self-harm — escalation, not flash-card |
| `sr-redflag-eli` | Yr 11 | **Red-flag** | Discloses something happening at home — safeguarding |

### Mode 1 (composite class)

| Code | Year | Mix |
|---|---|---|
| `class-jr-yr4` | Yr 4 | One keen, one wriggly, one shy, one cynic |
| `class-jr-yr2` | Yr 2 | Two enthusiastic, one tearful, one wanderer |
| `class-sr-yr9` | Yr 9 | Two engaged, one phone-scrolling, one quiet |
| `class-sr-yr11` | Yr 11 | Tired, mostly polite, one openly cynical, one anxious about upcoming exams |

Personas are stored as system-prompt templates with behavioural guardrails. AI student stays in character; AI class voices 3–4 distinct voices when speaking back.

---

## 6. Scenario examples

**Mode 1**
- *Monday morning settle* — Yr 4 class came in chatty after wet-weather break. Run **Five senses check-in**. Target: 4 min.
- *Friday end-of-day landing* — Yr 10 maths class is fizzing before the bell. Run **Sensory stomp & shake**.
- *Pre-test calm* — Yr 9 class about to sit a science test. Run **Five finger breathing**.
- *Post-assembly reset* — Yr 2 class came back overstimulated. Run **Tense & release**.

**Mode 2**
- *The wobbly chin* — Mia, Yr 3, came in from lunch crying. You've got 5 min before maths.
- *The shutdown* — Tahlia, Yr 9, snapped at a peer and is now silent at her desk. Class is settling around her.
- *The cynic* — Marcus, Yr 10, "this is so dumb". You've been asked to do a one-on-one check-in.
- *The overload* — Ethan, Yr 8, hands over ears in the corridor between bells.
- **Red-flag — *Jaya, Yr 10*** — comes to chat after class, mentions she sometimes "doesn't want to be around". Test: do you escalate?
- **Red-flag — *Eli, Yr 11*** — discloses something happening at home that meets safeguarding threshold. Test: do you stop, listen, and refer?

---

## 7. Scorecard (final draft for Chris's edit)

### Mode 1 — Delivering an activity (each criterion 0–3, weighted equally)

| # | Criterion | 0 (Not yet) | 1 (Emerging) | 2 (Solid) | 3 (Strong) |
|---|---|---|---|---|---|
| 1 | **Setup & framing** | Jumps in cold | Names activity but no why | Names activity + brief why | Settles room, names, gives a one-line purpose students can hold onto |
| 2 | **Clarity of instructions** | Confusing or missing steps | Most steps clear, one gap | All steps clear and ordered | Crystal clear, anticipates likely confusions |
| 3 | **Age-appropriate language** | Wrong register for the year | Mostly right with slips | Right register throughout | Right register + relatable examples for that age |
| 4 | **Pacing & tone** | Rushed or flat | Some pauses, mostly okay | Calm, unhurried, breathing space | Calm, unhurried, *and* sensitive to the room's energy |
| 5 | **Modelling & check-ins** | Doesn't model or check | Models OR checks, not both | Models and checks once | Models, checks, names what they notice |
| 6 | **Handling wobbles** | Ignores or escalates | Addresses but loses room | Addresses calmly, regains focus | Uses the wobble — names it, brings it back warmly |
| 7 | **Closure & integration** | Just stops | Closes activity | Closes + brief reflection | Closes, reflects, points to when *they* could use this themselves |

### Mode 2 — Responding to a distressed student

| # | Criterion | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| 1 | **Attunement** | Misreads or ignores | Notices something | Reads emotion + intensity | Reads emotion, intensity, and what's *under* it |
| 2 | **Validation** | Goes straight to fixing | Acknowledges briefly | Names + normalises the feeling | Names, normalises, makes the student feel *seen* before any tool |
| 3 | **Activity selection** | Wrong fit (e.g. imagery for dysregulated kid) | Okay fit | Good fit for student + state | Excellent fit — explains *why* this one to the student |
| 4 | **Activity delivery** | Confused or rushed | Gets through it | Clear, calm delivery | Same bar as Mode 1 level 3 |
| 5 | **Pacing & patience** | Pushes through resistance | Notices resistance, doesn't adapt | Adapts, slows down | Stays alongside without agenda; lets the student lead the tempo |
| 6 | **Closure & next step** | Ends abruptly | Checks in | Checks in + names what helped | Checks in, names what helped, plans what to do if it returns |
| 7 | **Safeguarding awareness** | Misses red flags | Notices but flash-cards through it | Notices and pauses | Stops the activity, listens, escalates to right person — no improvising |

**Red-flag override:** in scenarios marked `is_red_flag: true`, criterion 7 acts as a gate. A score of 0 or 1 on safeguarding caps the overall score at 1, regardless of other criteria. Coaching note explicitly says: "This scenario was a safeguarding moment, not a flash-card moment."

**Output shape from scorer:**
```json
{
  "criteria": [{ "id": 1, "score": 2, "evidence": "...", "to_try": "..." }, ...],
  "overall_score": 17,
  "overall_max": 21,
  "headline": "Strong delivery — work on closure",
  "what_worked": ["...", "..."],
  "what_to_try": ["...", "..."],
  "safeguarding_flag": false
}
```

---

## 8. Build phases

**Phase 0 — Catalog (half a day)**
- **Reuse** `~/Claude Projects/komodo-flashcards/activities.py` — the 23 activities are already structured there. Either import as a sibling package or copy to `catalog/activities.json` (decide at build time based on whether the schemas match).
- Add `best_for` tags and `fit_notes` for trainer-specific use (these may not exist in the flashcards version)
- Write `personas.json` and `scenarios.json` (≥4 scenarios per mode, plus 2 red-flag)

**Phase 1 — Streamlit shell + scorer (1–2 days)**
- Streamlit app: home → mode picker → scenario picker → scenario brief
- Manual transcript paste-in for testing the scorer
- `scoring/score.py` against Claude sonnet-4-6 with structured output
- SQLite for history
- This is testable *without any voice yet* — proves the scorer works before we touch Realtime API

**Phase 2 — Voice page POC (1–2 days)**
- Static `voice_page/index.html` + `voice.js`
- Single hardcoded scenario, OpenAI Realtime API via WebRTC
- Push-to-talk + end-session buttons
- Saves transcript to a local JSON file
- Confirms voice UX feels right before integrating

**Phase 3 — Wire it together (1 day)**
- FastAPI bridge: serves scenario config to voice page, receives transcript on session end, triggers scorer
- Streamlit launches voice page with `?session=<id>`
- Auto-refresh score view when session completes

**Phase 4 — Polish (1–2 days)**
- Komodo brand applied to voice page
- All scenarios + personas wired in
- History view in Streamlit (sessions over time, score trends per criterion)
- Transcript replay
- README with how to run + demo script

**Phase 5 (later) — Manager view**
- Only if/when this graduates beyond Chris's trial demos
- Aggregate scores across staff, weak-area heatmap
- Requires real auth + hosting — separate plan

Total to v1 (Phase 0–4): roughly **5–7 working days** of focused build, depending on how much Realtime API fights us.

---

## 9. Tech dependencies

```
streamlit>=1.36
anthropic>=0.40           # scorer (Claude sonnet-4-6)
openai>=1.50              # not used directly; voice page uses Realtime via JS
fastapi
uvicorn
python-dotenv
pypdf                     # one-off PDF parse for Phase 0
```

Voice page is plain HTML + JS — no build step, no npm. Loads OpenAI's Realtime WebRTC client from their docs example.

---

## 10. Cost estimate (per session)

- OpenAI Realtime (gpt-4o-realtime): ~$0.06/min audio in + ~$0.24/min audio out → ~**$1.50–3** per 10-min session
- Claude sonnet-4-6 scorer: ~5k input + 1k output tokens → ~**$0.02** per session
- Total: **~$1.50–3 per practice session.** Fine for trial demos. Worth re-architecting before any volume rollout.

---

## 11. Open questions

1. **PDF voice character** — should the AI student "voice" sound like a child? OpenAI Realtime has limited voice options (alloy, echo, fable, shimmer, etc.) — none are convincingly child-like. We may need to accept that the *script* is the realism, not the voice. Worth a 10-min test before committing.
2. **Komodo brand on voice page** — pick a colour + logo to apply (likely from your existing `komodo-flashcards` styling).
3. **Session length cap** — 10 min default per session? Hard cap at 15?
4. **Disclaimer screen** — first run should show an "this is staff-only, AI is not a substitute for…" intro. Worth wording carefully with your psychologist.

---

## 12. Risks

- **Realtime API latency / glitches.** Mitigated by de-risking in Phase 2 before integration.
- **Scorer drift.** Claude scoring open-ended transcripts can be inconsistent. Mitigated by tight rubric prompts, structured output, and a "show evidence" requirement on each criterion (model must quote the transcript).
- **Personas feeling like caricatures.** Mitigated by your psychologist reviewing persona prompts before they ship.
- **Red-flag scenarios feeling exploitative.** Mitigated by consent gate at session start ("the following scenario contains discussion of self-harm…") and psychologist sign-off.
