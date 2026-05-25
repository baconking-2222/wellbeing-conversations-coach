---
title: Wellbeing Conversations Coach - Voice Bridge
emoji: 💛
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Voice bridge for the Wellbeing Conversations Coach

FastAPI service that:
- Proxies Gemini Live voice sessions between the browser and Google
- Scores transcripts with Claude after each session
- Serves the voice page (HTML + JS)

Talks to:
- A Streamlit hub (deployed separately on Streamlit Community Cloud)
- Google Gemini Live API (set `GOOGLE_API_KEY` in Space secrets)
- Anthropic Claude API (set `ANTHROPIC_API_KEY` in Space secrets)
