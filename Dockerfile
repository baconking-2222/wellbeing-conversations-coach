# Dockerfile for the FastAPI voice bridge on Hugging Face Spaces.
# HF Spaces routes external traffic to whatever port the container
# listens on (defaults to 7860).
FROM python:3.11-slim

WORKDIR /app

# Install bridge deps (cached if requirements unchanged)
COPY requirements-bridge.txt ./
RUN pip install --no-cache-dir -r requirements-bridge.txt

# Copy the bridge code + everything it imports
COPY server.py db.py ./
COPY catalog/ ./catalog/
COPY scoring/ ./scoring/
COPY prompts/ ./prompts/
COPY voice_page/ ./voice_page/

# HF Spaces conventions
ENV PORT=7860
EXPOSE 7860

# data/ holds the SQLite DB; HF Spaces gives us a writable /tmp by default
RUN mkdir -p /app/data

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
