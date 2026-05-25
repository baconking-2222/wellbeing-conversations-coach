# Deploying the Wellbeing Conversations Coach (free path)

This app has two services. They have to live on different free hosts because Streamlit Community Cloud doesn't run WebSockets (which the voice bridge needs).

| Service | What it does | Host |
|---|---|---|
| Streamlit hub | The pretty UI: pick scenarios, see history, view scorecards | **Streamlit Community Cloud** (free) |
| FastAPI bridge | Proxies the Gemini Live voice session + runs the Claude scorer + serves the voice page | **Hugging Face Spaces** (free, Docker) |

Total time: about 30 minutes of clicks. No coding.

You'll need accounts on three services (all free, all no card required):
- GitHub: <https://github.com/signup>
- Hugging Face: <https://huggingface.co/join>
- Streamlit Community Cloud: <https://share.streamlit.io> (signs in with GitHub)

---

## Step 1: Push the code to GitHub

Run this in the project folder. Replace `YOUR-GH-USERNAME` with your actual GitHub username.

```bash
cd ~/Claude\ Projects/komodo-ai-trainer
git init
git add -A
git commit -m "Initial Wellbeing Conversations Coach deploy"

# Create the repo on GitHub first (private is fine):
# https://github.com/new   →  name it "wellbeing-conversations-coach"

git branch -M main
git remote add origin https://github.com/YOUR-GH-USERNAME/wellbeing-conversations-coach.git
git push -u origin main
```

GitHub will ask for a Personal Access Token instead of your password. Make one here: <https://github.com/settings/tokens/new> → tick "repo" → generate. Paste it as the password.

---

## Step 2: Deploy the voice bridge to Hugging Face Spaces

1. Go to <https://huggingface.co/new-space>
2. Fill in:
   - **Owner**: your account
   - **Space name**: `wellbeing-coach-bridge`
   - **Short description**: "Voice bridge"
   - **Space SDK**: pick **Docker** (not Gradio/Streamlit)
   - **Visibility**: Public (free) or Private (also free)
3. Click **Create Space**
4. On the Space page, click **Files**, then **Upload files**. Drag in:
   - `Dockerfile`
   - `requirements-bridge.txt`
   - `README-hf-spaces.md` → **rename to `README.md`** when uploading (replaces the auto-generated one)
   - `server.py`
   - `db.py`
   - the whole `catalog/` folder
   - the whole `scoring/` folder
   - the whole `prompts/` folder
   - the whole `voice_page/` folder
5. Commit the upload.
6. Click **Settings** → **Variables and secrets** → **New secret**. Add:
   - `GOOGLE_API_KEY` = your `AIzaSy...` key from <https://aistudio.google.com/apikey>
   - `ANTHROPIC_API_KEY` = your `sk-ant-...` key from <https://console.anthropic.com/settings/keys>
7. Go back to the Space, watch it build (~3-5 min). You'll see logs.
8. When status is "Running", the URL will be like `https://YOUR-USERNAME-wellbeing-coach-bridge.hf.space`. **Copy this URL** - you need it for Step 3.

**Sanity check**: open `https://YOUR-USERNAME-wellbeing-coach-bridge.hf.space/api/health` in a browser. You should see `{"ok": true, "google_key_set": true, "anthropic_key_set": true, ...}`.

---

## Step 3: Deploy the Streamlit hub to Streamlit Community Cloud

1. Go to <https://share.streamlit.io>
2. Sign in with GitHub (the same account from Step 1)
3. Click **Create app** → **Deploy a public app from GitHub**
4. Fill in:
   - **Repository**: `YOUR-GH-USERNAME/wellbeing-conversations-coach`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **App URL**: pick a slug, e.g. `wellbeing-coach`
5. Click **Advanced settings** → **Python version**: 3.11
6. Still in Advanced settings, **Secrets** (TOML format) - paste this, swapping in your real values:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   KOMODO_BRIDGE_URL = "https://YOUR-USERNAME-wellbeing-coach-bridge.hf.space"
   ```
7. Streamlit Cloud uses `requirements.txt` by default. Rename `requirements-streamlit.txt` to `requirements.txt` on the repo (or just rely on the full one - both work, just slower install).
   - Easier: in Streamlit Cloud's advanced settings, set **Requirements file**: `requirements-streamlit.txt`.
8. Click **Deploy**. Takes ~3-5 min.
9. When it's up, your team gets a URL like `https://wellbeing-coach.streamlit.app`.

---

## Step 4: Test it works end-to-end

1. Open `https://wellbeing-coach.streamlit.app`
2. Pick a scenario → click **Start ▶**
3. Click **🎤 Open voice session ▶** - this opens the HF Spaces voice page in a new tab
4. Allow mic permission
5. Have a 1-minute conversation
6. Click **End session and score ▶**
7. Scorecard appears

If anything breaks, the most likely causes:
- HF Spaces Space is sleeping (free tier sleeps after inactivity - first request wakes it up in ~30s)
- API keys not set in Space secrets
- `KOMODO_BRIDGE_URL` in Streamlit secrets doesn't match the actual HF Spaces URL

---

## Sharing with the team

Just send them the Streamlit URL: `https://wellbeing-coach.streamlit.app`.

They don't need any accounts. They just open the link, pick a scenario, allow mic, talk.

Each voice session costs ~$1-3 in Gemini API fees (charged to your Google Cloud account if you used a paid project, or against your free-tier daily quota if you used a free project). Monitor at <https://aistudio.google.com/app/billing> if you start to worry about cost.

---

## Updating the deployed app

After making code changes locally:

```bash
git add -A
git commit -m "what changed"
git push
```

- **Streamlit Cloud** auto-redeploys on every push. Takes ~2-3 min.
- **Hugging Face Spaces**: it does NOT auto-redeploy from GitHub (we uploaded files manually). To update, re-upload the changed files via the Space's web UI. Or, set up a GitHub action to sync (more setup, ask me if you want this later).

---

## Known quirks

- **Iframe-embedded voice doesn't work on Streamlit Cloud.** That's why we use the "Open voice session" button. On localhost the iframe still works.
- **HF Spaces free tier sleeps** after 15-30 minutes of no traffic. The first hit after sleep takes ~30s to wake up.
- **Sessions are stored in SQLite** inside the HF Spaces container. HF Spaces' free Docker storage isn't persistent across restarts, so practice history will reset whenever the Space restarts or sleeps. For persistent history you'd need a managed database (separate task).
