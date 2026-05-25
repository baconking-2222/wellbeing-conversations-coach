"""Wellbeing Conversations Coach - Streamlit hub.

Two friendly modes for staff:
  🎴 Lead a class through an activity   (was mode1)
  💛 Support a student one-on-one        (was mode2)

Internal `mode1` / `mode2` strings still live in scenarios.json and the rubrics
so we keep them as keys. Only the UI says warmer things.
"""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

import catalog
from catalog import realtime as catalog_realtime
import db
from scoring.score import score_transcript

load_dotenv(override=True)
db.init_db()

BRIDGE_URL = os.environ.get("KOMODO_BRIDGE_URL", "http://localhost:8000")

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
LOGO_PATH = ASSETS / "logo-primary.png"
ICON_PATH = ASSETS / "icon-blue.png"

PERSONAS = json.loads((ROOT / "catalog" / "personas.json").read_text())
SCENARIOS = json.loads((ROOT / "catalog" / "scenarios.json").read_text())

STUDENT_BY_ID = {p["id"]: p for p in PERSONAS["students"]}
CLASS_BY_ID = {p["id"]: p for p in PERSONAS["classes"]}
SCENARIO_BY_ID = {s["id"]: s for s in (SCENARIOS["mode1"] + SCENARIOS["mode2"])}

# Warm labels for the two modes
MODE_LABELS = {
    "mode1": "🎴 Lead a class",
    "mode2": "💛 Support a student",
}
MODE_SUBTITLES = {
    "mode1": "Practise delivering a flash-card activity to a class of students. The AI plays the room.",
    "mode2": "Practise responding to a single student in distress. The AI plays the student.",
}

MODE1_THEMES = [
    ("any",           "All themes"),
    ("Breathing",     "🌬️  Breathing"),
    ("Grounding",     "🌳 Grounding"),
    ("Calming",       "🌊 Calming"),
    ("Energy release","⚡ Energy release"),
    ("Mindfulness",   "🧘 Mindfulness"),
    ("Gratitude",     "💛 Gratitude"),
    ("Self-reflection","✨ Self-reflection"),
]

STUDENT_STATE_BY_PERSONA: dict[str, str] = {
    "jr-mia":          "Anxious",
    "jr-leo":          "Dysregulated",
    "jr-sam":          "Withdrawn",
    "sr-tahlia":       "Shutdown",
    "sr-marcus":       "Cynical",
    "sr-aroha":        "Tearful",
    "sr-ethan":        "Overloaded",
    "sr-redflag-jaya": "Safeguarding",
    "sr-redflag-eli":  "Safeguarding",
}
MODE2_STATES = [
    ("any",          "Any state"),
    ("Anxious",      "😟 Anxious"),
    ("Withdrawn",    "🌧️ Withdrawn"),
    ("Shutdown",     "🧱 Shutdown"),
    ("Dysregulated", "⚡ Dysregulated"),
    ("Tearful",      "💧 Tearful"),
    ("Cynical",      "😏 Cynical"),
    ("Overloaded",   "🌪️ Sensory overload"),
    ("Safeguarding", "⚠️ Safeguarding"),
]

AGE_FILTERS = [
    ("any", "All ages"),
    ("Jr",  "🧒 Primary (5 to 12)"),
    ("Sr",  "🧑 Secondary (13 to 18)"),
]
LENGTH_FILTERS = [
    ("any",    "Any length"),
    ("quick",  "⚡ Quick (under 5 min)"),
    ("medium", "⏱️ Medium (5 to 10 min)"),
    ("longer", "🪴 Longer (over 10 min)"),
]


# ----------------------------------------------------------------------------
# Page config + brand
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Wellbeing Conversations Coach",
    page_icon=str(ICON_PATH) if ICON_PATH.exists() else "💛",
    layout="wide",
    initial_sidebar_state="expanded",
)

if LOGO_PATH.exists():
    try:
        st.logo(
            str(LOGO_PATH),
            icon_image=str(ICON_PATH) if ICON_PATH.exists() else None,
            size="large",
        )
    except TypeError:
        st.logo(str(LOGO_PATH))


_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Epilogue:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
    --pale-blue: #ebf9ff;
    --pastel-blue: #a5daff;
    --komodo-blue: #55b5f2;
    --vibrant-blue: #3d92e6;
    --komodo-navy: #064471;
    --light-green: #77eed6;
    --pastel-green: #d2ffe6;
    --black-blue: #001f34;
    --danger: #b00020;
    --danger-bg: #ffd9d9;
}

html, body, .stApp { font-family: 'Epilogue', 'Inter', sans-serif !important; }
.stApp, .stApp * { color: var(--black-blue); }
.stApp .stCaption, .stApp small { color: #2a4458 !important; }

.stApp {
    background:
      radial-gradient(circle at 8% 10%, rgba(165,218,255,0.55) 0%, transparent 32%),
      radial-gradient(circle at 92% 88%, rgba(119,238,214,0.45) 0%, transparent 30%),
      radial-gradient(circle at 60% 60%, rgba(85,181,242,0.18) 0%, transparent 40%),
      var(--pale-blue);
}

h1, h2, h3, h4 { color: var(--komodo-navy); font-weight: 700; font-family: 'Epilogue', sans-serif !important; }

/* ---- Hide Streamlit auto-generated multipage nav (we render our own) ---- */
[data-testid="stSidebarNav"] { display: none !important; }

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: white;
    border-right: 2px solid var(--black-blue);
}
[data-testid="stSidebarHeader"] img, [data-testid="stLogo"] {
    max-height: 56px !important;
    height: auto !important;
    image-rendering: -webkit-optimize-contrast;
}
.kb-nav-label {
    color: var(--komodo-navy);
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 14px 4px 8px;
}

/* ---- Hero ---- */
.kb-hero {
    background: white;
    border: 3px solid var(--black-blue);
    border-radius: 22px;
    padding: 26px 30px;
    margin: 0 0 22px;
    box-shadow: 0 4px 0 rgba(0,31,52,0.10), 0 8px 18px rgba(0,31,52,0.10);
    position: relative;
    overflow: hidden;
}
.kb-hero::before {
    content: ''; position: absolute; top: -50px; right: -50px;
    width: 180px; height: 180px; border-radius: 50%;
    background: var(--pastel-blue); opacity: 0.55; z-index: 0;
}
.kb-hero::after {
    content: ''; position: absolute; bottom: -60px; left: -60px;
    width: 200px; height: 200px; border-radius: 50%;
    background: var(--light-green); opacity: 0.40; z-index: 0;
}
.kb-hero > * { position: relative; z-index: 1; }
.kb-hero h1 { margin: 0 0 8px; font-size: 2.15rem; }
.kb-hero p { margin: 0; color: #2a4458; font-size: 1.05rem; }

/* ---- Mode picker: target the two pick_m* buttons via the column layout
   that contains them. The .kb-modepicker DIV ends up as a sibling rather
   than a parent of the buttons in Streamlit's DOM, so we scope to the
   immediate-following columns block instead. ---- */
.kb-modepick-anchor + div[data-testid="stHorizontalBlock"] .stButton > button {
    min-height: 110px !important;
    border-radius: 24px !important;
    border: 3px solid var(--black-blue) !important;
    font-size: 1.32rem !important;
    font-weight: 700 !important;
    padding: 22px !important;
    box-shadow: 0 6px 0 rgba(0,31,52,0.16), 0 10px 22px rgba(0,31,52,0.10) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
    white-space: normal !important;
    line-height: 1.3 !important;
}
.kb-modepick-anchor + div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 9px 0 rgba(0,31,52,0.18), 0 14px 26px rgba(0,31,52,0.14) !important;
}

/* ---- Filter row ---- */
.kb-filterlabel {
    color: var(--komodo-navy);
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin: 10px 0 4px;
}
.stApp .stSelectbox > div > div {
    background: white !important;
    border: 2px solid var(--black-blue) !important;
    border-radius: 14px !important;
    min-height: 44px;
}

/* ---- Scenario cards ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(170deg, #ffffff 0%, #f4fbff 65%, var(--pale-blue) 100%);
    border: 3px solid var(--black-blue) !important;
    border-radius: 22px !important;
    padding: 22px 24px !important;
    box-shadow: 0 6px 0 rgba(0,31,52,0.14), 0 10px 22px rgba(0,31,52,0.10);
    height: 100%;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 0 rgba(0,31,52,0.16), 0 16px 28px rgba(0,31,52,0.14);
}
[data-testid="stHorizontalBlock"] { align-items: stretch; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    display: flex; flex-direction: column;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
    flex: 1;
}

/* ---- Inside-card Start buttons: green tealy pill, full width ---- */
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
    background: var(--light-green) !important;
    color: var(--black-blue) !important;
    border: 3px solid var(--black-blue) !important;
    border-radius: 30px !important;
    padding: 12px 20px !important;
    font-size: 1.02rem !important;
    font-weight: 700 !important;
    width: 100% !important;
    box-shadow: 0 4px 0 rgba(0,31,52,0.16);
    transition: background 0.15s ease, transform 0.1s ease;
}
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {
    background: var(--pastel-green) !important;
    transform: translateY(-1px);
    box-shadow: 0 5px 0 rgba(0,31,52,0.18);
}

/* ---- Outside-card buttons: scoped to the main content block so card
   buttons (inside stVerticalBlockBorderWrapper) keep their own rules. ---- */
.stApp [data-testid="stMainBlockContainer"] .stButton > button[kind="secondary"] {
    background: white !important;
    color: var(--komodo-navy) !important;
    border: 3px solid var(--black-blue) !important;
    border-radius: 30px !important;
    font-weight: 700 !important;
    padding: 10px 22px !important;
    box-shadow: 0 3px 0 rgba(0,31,52,0.12);
}
.stApp [data-testid="stMainBlockContainer"] .stButton > button[kind="secondary"]:hover {
    background: var(--pale-blue) !important;
    color: var(--komodo-navy) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 0 rgba(0,31,52,0.14);
}
.stApp [data-testid="stMainBlockContainer"] .stButton > button[kind="primary"],
.stApp [data-testid="stMainBlockContainer"] [data-testid="stBaseLinkButton-primary"],
.stApp [data-testid="stMainBlockContainer"] a[data-testid="stBaseLinkButton-primary"] {
    background: var(--light-green) !important;
    color: var(--black-blue) !important;
    border: 3px solid var(--black-blue) !important;
    border-radius: 30px !important;
    font-weight: 700 !important;
    padding: 10px 22px !important;
    text-decoration: none !important;
    box-shadow: 0 3px 0 rgba(0,31,52,0.16);
    transition: background 0.15s ease, transform 0.1s ease;
}
.stApp [data-testid="stMainBlockContainer"] .stButton > button[kind="primary"]:hover,
.stApp [data-testid="stMainBlockContainer"] a[data-testid="stBaseLinkButton-primary"]:hover {
    background: var(--pastel-green) !important;
    color: var(--black-blue) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 0 rgba(0,31,52,0.18);
}
/* When the mode picker primary button is active, show a ✓ in the corner */
.kb-modepick-anchor + div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"]::after {
    content: ' ✓';
    font-size: 1.2rem;
    margin-left: 6px;
}

/* ---- Strong subtitle under the mode picker ---- */
.kb-mode-subtitle {
    background: white;
    border: 2.5px solid var(--black-blue);
    border-left: 8px solid var(--komodo-blue);
    border-radius: 14px;
    padding: 14px 20px;
    margin: 14px 0 18px;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--komodo-navy);
    box-shadow: 0 3px 0 rgba(0,31,52,0.10);
}

/* Pills */
.kb-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.75rem;
    margin: 0 5px 5px 0;
    border: 2px solid var(--black-blue);
    color: var(--black-blue);
    line-height: 1.4;
    background: white;
}
.kb-pill.persona  { background: var(--pastel-blue); }
.kb-pill.activity { background: var(--light-green); }
.kb-pill.state    { background: var(--pastel-green); }
.kb-pill.age      { background: var(--pale-blue); }
.kb-pill.duration { background: white; }
.kb-pill.redflag  { background: var(--danger-bg); border-color: var(--danger); color: var(--danger); }

/* Card body */
.kb-card-head {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 10px;
}
.kb-card-emoji {
    font-size: 2.3rem; line-height: 1; flex-shrink: 0;
    width: 60px; height: 60px;
    background: linear-gradient(135deg, var(--pale-blue) 0%, var(--pastel-green) 100%);
    border: 2.5px solid var(--black-blue);
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 0 rgba(0,31,52,0.12);
}
.kb-card-title {
    color: var(--komodo-navy);
    font-size: 1.32rem;
    font-weight: 700;
    line-height: 1.2;
    margin: 0;
}
.kb-card-pills { margin-top: 4px; }
.kb-card-brief {
    color: #2a4458;
    font-size: 0.95rem;
    line-height: 1.55;
    margin: 12px 0 16px;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* Score bar */
.kb-score-bar {
    display: inline-block; width: 100%; height: 18px;
    background: #e9eef2;
    border-radius: 9px; overflow: hidden;
    border: 2px solid var(--black-blue);
}
.kb-score-fill { height: 100%; background: var(--vibrant-blue); }
.kb-score-fill.flagged { background: var(--danger); }

/* History row */
.kb-history-row {
    background: white;
    border: 3px solid var(--black-blue);
    border-radius: 18px;
    padding: 16px 22px;
    margin-bottom: 14px;
    box-shadow: 0 4px 0 rgba(0,31,52,0.12);
}
.kb-history-row:hover {
    box-shadow: 0 6px 0 rgba(0,31,52,0.16), 0 8px 16px rgba(0,31,52,0.10);
}

footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none !important; }
</style>
"""
st.html(_CSS)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _hero(title: str, subtitle: str) -> None:
    st.html(
        f"<div class='kb-hero'><h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(subtitle)}</p></div>"
    )


def _persona_for(scenario: dict) -> dict:
    pid = scenario["persona_id"]
    return STUDENT_BY_ID.get(pid) or CLASS_BY_ID[pid]


def _scenario_emoji(scenario: dict, mode: str) -> str:
    if mode == "mode1":
        if scenario.get("activity_id"):
            act = catalog.get_activity(scenario["activity_id"])
            if act and act.emoji:
                return act.emoji
        return "🎴"
    pid = scenario["persona_id"]
    if scenario.get("is_red_flag"):
        return "⚠️"
    return {
        "jr-mia": "😟",
        "jr-leo": "⚡",
        "jr-sam": "🌧️",
        "sr-tahlia": "🧱",
        "sr-marcus": "😏",
        "sr-aroha": "💧",
        "sr-ethan": "🌪️",
    }.get(pid, "💛")


def _length_bucket(minutes: int) -> str:
    if minutes < 5: return "quick"
    if minutes <= 10: return "medium"
    return "longer"


def _scenario_matches_filters(scenario: dict, mode: str, filters: dict) -> bool:
    persona = _persona_for(scenario)
    age_f = filters.get("age", "any")
    if age_f != "any":
        age_band = persona.get("age_band", "")
        if age_band not in (age_f, "All"):
            return False
    length_f = filters.get("length", "any")
    if length_f != "any":
        if _length_bucket(scenario.get("duration_minutes", 5)) != length_f:
            return False
    if mode == "mode1":
        theme = filters.get("theme", "any")
        if theme != "any":
            if not scenario.get("activity_id"):
                return False
            act = catalog.get_activity(scenario["activity_id"])
            if not act or theme not in act.purposes:
                return False
    else:
        state = filters.get("state", "any")
        if state == "Safeguarding":
            if not scenario.get("is_red_flag"):
                return False
        elif state != "any":
            tag = STUDENT_STATE_BY_PERSONA.get(scenario["persona_id"])
            if tag != state:
                return False
        if not filters.get("show_safeguarding", False) and state != "Safeguarding":
            if scenario.get("is_red_flag"):
                return False
    return True


def _to_ten(score: float, max_score: float) -> int:
    if not max_score:
        return 0
    return round((score / max_score) * 10)


def _render_scenario_card(scenario: dict, mode: str) -> None:
    persona = _persona_for(scenario)
    activity = catalog.get_activity(scenario["activity_id"]) if scenario.get("activity_id") else None
    emoji = _scenario_emoji(scenario, mode)
    dur = scenario.get("duration_minutes", 5)

    pills = []
    if scenario.get("is_red_flag"):
        pills.append("<span class='kb-pill redflag'>⚠ SAFEGUARDING</span>")
    pills.append(f"<span class='kb-pill persona'>{html.escape(persona['display_name'])}</span>")
    if persona.get("year"):
        pills.append(f"<span class='kb-pill age'>{html.escape(persona['year'])}</span>")
    if mode == "mode1" and activity:
        pills.append(f"<span class='kb-pill activity'>{html.escape(activity.name)}</span>")
    if mode == "mode2":
        state_tag = STUDENT_STATE_BY_PERSONA.get(scenario["persona_id"])
        if state_tag and not scenario.get("is_red_flag"):
            pills.append(f"<span class='kb-pill state'>{html.escape(state_tag)}</span>")
    pills.append(f"<span class='kb-pill duration'>⏱ {dur} min</span>")

    with st.container(border=True):
        st.html(
            f"<div class='kb-card-head'>"
            f"<div class='kb-card-emoji'>{emoji}</div>"
            f"<h3 class='kb-card-title' style='flex:1; min-width:0;'>{html.escape(scenario['title'])}</h3>"
            f"</div>"
            f"<div class='kb-card-pills'>{' '.join(pills)}</div>"
            f"<div class='kb-card-brief'>{html.escape(scenario['brief'])}</div>"
        )
        if st.button("Start ▶", key=f"start-{scenario['id']}", use_container_width=True):
            sid = db.create_session(
                mode=mode,
                scenario=scenario,
                persona_id=scenario["persona_id"],
                activity_id=scenario.get("activity_id"),
            )
            st.session_state.active_session = {
                "session_id": sid,
                "scenario_id": scenario["id"],
                "mode": mode,
            }
            st.rerun()


def _render_scorecard(sc: dict) -> None:
    overall_10 = _to_ten(sc["overall_score"], sc["overall_max"])
    pct = overall_10 * 10
    flagged = sc.get("safeguarding_flag", False)
    fill_class = "kb-score-fill flagged" if flagged else "kb-score-fill"
    headline_color = "#b00020" if flagged else "var(--komodo-navy)"

    st.html(
        f"""
        <div style='background:white; border:2.5px solid var(--black-blue);
                    border-radius:18px; padding:18px 22px; margin:10px 0 14px;
                    box-shadow: 0 4px 0 rgba(0,31,52,0.12);'>
          <div style='font-size:0.78rem; color:#2a4458;
                      letter-spacing:0.08em; text-transform:uppercase;
                      font-weight:700;'>Overall</div>
          <div style='display:flex; align-items:baseline; gap:16px; margin: 6px 0 12px;'>
            <div style='font-size:2.8rem; font-weight:700; color:{headline_color};'>
              {overall_10}<span style='font-size:1.4rem; color:#2a4458;'>/10</span>
            </div>
            <div style='flex:1;'>
              <div class='kb-score-bar'><div class='{fill_class}'
                style='width:{pct:.0f}%'></div></div>
            </div>
          </div>
          <div style='font-size:1.15rem; font-weight:600; color:{headline_color};'>
            {html.escape(sc['headline'])}
          </div>
        </div>
        """
    )

    if flagged:
        st.error(f"⚠️ Safeguarding moment. {sc.get('safeguarding_note', '')}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### ✅ What worked")
        for item in sc["what_worked"]:
            st.markdown(f"- {item}")
    with col2:
        st.markdown("##### 🎯 What to try next")
        for item in sc["what_to_try"]:
            st.markdown(f"- {item}")

    st.markdown("##### 📋 Criterion-by-criterion")
    for c in sc["criteria"]:
        crit_10 = _to_ten(c["score"], 3)
        cpct = crit_10 * 10
        st.html(
            f"""
            <div style='background:white; border:2px solid var(--black-blue);
                        border-radius:12px; padding:14px 18px; margin-bottom: 10px;
                        box-shadow: 0 3px 0 rgba(0,31,52,0.10);'>
              <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h4 style='margin:0;'>{c['id']}. {html.escape(c['name'])}</h4>
                <div style='font-weight:700; color: var(--komodo-navy);'>
                  {crit_10}<span style='font-size:0.85rem; color:#2a4458;'>/10</span>
                </div>
              </div>
              <div style='margin: 6px 0;'>
                <div class='kb-score-bar'><div class='kb-score-fill'
                  style='width:{cpct:.0f}%'></div></div>
              </div>
              <div style='margin-top:8px;'><em>Evidence:</em> {html.escape(c['evidence'])}</div>
              <div style='margin-top:4px;'><strong>Try next:</strong> {html.escape(c['to_try'])}</div>
            </div>
            """
        )


# ----------------------------------------------------------------------------
# Sidebar nav
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='kb-nav-label'>Navigate</div>", unsafe_allow_html=True)
    page = st.radio(
        "Page",
        ["🎤 Practise", "📜 History"],
        label_visibility="collapsed",
    )
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.85rem; color:#2a4458; padding:0 4px; line-height:1.5;'>"
        "<strong>Wellbeing Conversations Coach</strong><br>"
        "Voice-based rehearsal for the Komodo Wellbeing flash cards. Have real "
        "conversations with AI-played students and get Claude-powered feedback "
        "after each session."
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================================
# PRACTISE PAGE
# ============================================================================
if page.startswith("🎤"):
    if "active_session" not in st.session_state:
        st.session_state.active_session = None
    if "mode_choice" not in st.session_state:
        st.session_state.mode_choice = "mode1"

    # ----- Scenario list view -----
    if st.session_state.active_session is None:
        _hero(
            "Pick a scenario to practise",
            "Voice rehearsal with AI-played students. Claude scores how you went, "
            "and you can come back any time to refine.",
        )

        # ----- Mode picker as two giant buttons -----
        # The anchor div is used as a sibling selector hook in CSS so we can
        # style only the modepicker's columns block without affecting other
        # st.columns elements lower on the page.
        st.html("<div class='kb-modepick-anchor'></div>")
        mc1, mc2 = st.columns(2, gap="medium")
        with mc1:
            active = st.session_state.mode_choice == "mode1"
            if st.button(
                "🎴   Lead a class",
                key="pick_m1",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.mode_choice = "mode1"
                st.rerun()
        with mc2:
            active = st.session_state.mode_choice == "mode2"
            if st.button(
                "💛   Support a student",
                key="pick_m2",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.mode_choice = "mode2"
                st.rerun()
        mode = st.session_state.mode_choice
        st.html(
            f"<div class='kb-mode-subtitle'>{html.escape(MODE_SUBTITLES[mode])}</div>"
        )

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # Filters
        st.markdown("<div class='kb-filterlabel'>Filter scenarios</div>", unsafe_allow_html=True)
        if mode == "mode1":
            fcols = st.columns([1.2, 1.4, 1.2, 1.2])
            with fcols[0]:
                age_choice = st.selectbox("Age group", AGE_FILTERS, format_func=lambda x: x[1], key="m1_age")
            with fcols[1]:
                theme_choice = st.selectbox("Theme", MODE1_THEMES, format_func=lambda x: x[1], key="m1_theme")
            with fcols[2]:
                len_choice = st.selectbox("Length", LENGTH_FILTERS, format_func=lambda x: x[1], key="m1_len")
            with fcols[3]:
                st.write("")
            filters = {"age": age_choice[0], "theme": theme_choice[0], "length": len_choice[0]}
        else:
            fcols = st.columns([1.2, 1.4, 1.2, 1.2])
            with fcols[0]:
                age_choice = st.selectbox("Age group", AGE_FILTERS, format_func=lambda x: x[1], key="m2_age")
            with fcols[1]:
                state_choice = st.selectbox("Student state", MODE2_STATES, format_func=lambda x: x[1], key="m2_state")
            with fcols[2]:
                len_choice = st.selectbox("Length", LENGTH_FILTERS, format_func=lambda x: x[1], key="m2_len")
            with fcols[3]:
                show_sg = st.toggle("⚠️ Include safeguarding", key="m2_sg", value=False)
            filters = {
                "age": age_choice[0],
                "state": state_choice[0],
                "length": len_choice[0],
                "show_safeguarding": show_sg or state_choice[0] == "Safeguarding",
            }

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        scenarios = [
            s for s in SCENARIOS[mode]
            if _scenario_matches_filters(s, mode, filters)
        ]

        if not scenarios:
            st.info("No scenarios match those filters. Try widening them.")
        else:
            for i in range(0, len(scenarios), 2):
                row = scenarios[i:i+2]
                cols = st.columns(2, gap="medium")
                for j, scen in enumerate(row):
                    with cols[j]:
                        _render_scenario_card(scen, mode)

    # ----- Detail view: just embed the voice page -----
    else:
        active = st.session_state.active_session
        voice_url = f"{BRIDGE_URL}/voice/?session={active['session_id']}"
        # On Streamlit Cloud the embedded iframe usually can't get mic
        # permission across origins, so we offer the new-tab path as the
        # reliable fallback. Locally, the embed works fine.
        is_cloud = "streamlit.app" in (os.environ.get("HOSTNAME", "") + os.environ.get("STREAMLIT_SERVER_HEADLESS", ""))

        col_back, col_open = st.columns([1.6, 2.2])
        with col_back:
            if st.button("← Back to scenarios", use_container_width=True, type="secondary"):
                st.session_state.active_session = None
                st.rerun()
        with col_open:
            st.link_button(
                "🎤 Open voice session ▶",
                voice_url,
                use_container_width=True,
                type="primary",
            )

        st.caption(
            "The voice page opens in a new tab. If you'd rather try it "
            "embedded below (only works on localhost), scroll down."
        )

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        with st.expander("Embedded voice (localhost only)", expanded=False):
            components.iframe(voice_url, height=1100, scrolling=True)


# ============================================================================
# HISTORY PAGE
# ============================================================================
else:
    _hero(
        "Practice history",
        "Past sessions you have scored. Click any to revisit the scorecard and transcript.",
    )

    all_rows = db.list_sessions()
    # Only show fully scored sessions
    rows = [r for r in all_rows if r["status"] == "scored" and r["overall_score"] is not None]

    top_cols = st.columns([4, 1.4])
    with top_cols[1]:
        if rows and st.button("🗑️ Clear all history", use_container_width=True, type="secondary"):
            st.session_state._confirm_clear = True

    if st.session_state.get("_confirm_clear"):
        st.warning(
            "This will permanently delete all scored sessions. "
            "There is no undo."
        )
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Yes, delete everything", use_container_width=True):
                db.delete_all_sessions()
                st.session_state._confirm_clear = False
                st.session_state.pop("_view_session", None)
                st.rerun()
        with c2:
            if st.button("Cancel", use_container_width=True, type="secondary"):
                st.session_state._confirm_clear = False
                st.rerun()

    if not rows:
        st.info("No scored sessions yet. Head to **Practise** and run one.")
    else:
        for r in rows:
            score_10 = _to_ten(r["overall_score"], r["overall_max"])
            flag_emoji = " ⚠️" if r["safeguarding_flag"] else ""
            mode_label = MODE_LABELS.get(r["mode"], r["mode"])

            with st.container(border=False):
                cols = st.columns([5, 1.4, 1.2, 1])
                with cols[0]:
                    st.html(
                        f"<div class='kb-history-row'>"
                        f"<h3 style='margin:0 0 6px;'>{html.escape(r['scenario_title'])}{flag_emoji}</h3>"
                        f"<span class='kb-pill activity'>{html.escape(mode_label)}</span>"
                        f"<div style='color:#2a4458; font-size:0.88rem; margin-top:8px;'>{r['created_at']}</div>"
                        f"</div>"
                    )
                with cols[1]:
                    st.html(
                        f"<div style='text-align:center; padding:18px 0;'>"
                        f"<div style='font-size:2rem; font-weight:700; color:var(--komodo-navy);'>"
                        f"{score_10}<span style='font-size:1rem; color:#2a4458;'>/10</span></div>"
                        f"</div>"
                    )
                with cols[2]:
                    if st.button("View ▶", key=f"view-{r['id']}", use_container_width=True):
                        st.session_state._view_session = r["id"]
                        st.rerun()
                with cols[3]:
                    if st.button("🗑️", key=f"del-{r['id']}", use_container_width=True, type="secondary"):
                        db.delete_session(r["id"])
                        if st.session_state.get("_view_session") == r["id"]:
                            st.session_state.pop("_view_session", None)
                        st.rerun()

        if st.session_state.get("_view_session"):
            row = db.get_session(st.session_state._view_session)
            if row and row.get("scorecard"):
                st.markdown("---")
                st.markdown(f"### {row['scenario_title']}")
                _render_scorecard(row["scorecard"])
                if row.get("transcript"):
                    with st.expander("📜 Transcript"):
                        st.text(row["transcript"])
                if st.button("Close", type="secondary"):
                    del st.session_state._view_session
                    st.rerun()
