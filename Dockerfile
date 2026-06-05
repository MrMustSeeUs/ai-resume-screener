# =============================================================================
# AI Resume Screener — Dockerfile
# Packages the entire app into a container so it runs identically everywhere:
# your laptop, CI/CD, and Render's cloud servers.
#
# Docker concept: a container is a lightweight, isolated box that includes
# your code, Python, and all dependencies — nothing extra, nothing missing.
# =============================================================================

# ── Base image ────────────────────────────────────────────────────────────────
# We start FROM an official Python 3.11 image (slim = smaller, faster builds)
# "slim" removes documentation and test files we don't need in production
FROM python:3.12-slim

# ── Working directory ─────────────────────────────────────────────────────────
# All subsequent commands run inside /app inside the container
WORKDIR /app

# ── Install dependencies first (layer caching trick) ─────────────────────────
# Docker builds in layers. By copying requirements.txt BEFORE copying
# the rest of the code, Docker can reuse the cached pip install layer
# if only our code changed (not dependencies). This speeds up rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ─────────────────────────────────────────────────────
# Now copy everything else (app/, tests/, etc.)
COPY . .

# ── Expose port ────────────────────────────────────────────────────────────────
# Streamlit runs on port 8501 by default
# EXPOSE tells Docker (and Render) which port to listen on
EXPOSE 8501

# ── Health check ──────────────────────────────────────────────────────────────
# Docker will ping this URL every 30s to confirm the app is alive
# If it fails 3 times, Docker marks the container as unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── Start command ─────────────────────────────────────────────────────────────
# This runs when the container starts.
# --server.address=0.0.0.0 → accept connections from outside the container
# --server.port=8501        → match the EXPOSE above
# --server.headless=true    → no browser auto-open in production
# --server.fileWatcherType=none → disable file watcher (not needed in production)
CMD ["streamlit", "run", "app/main.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--server.fileWatcherType=none"]
