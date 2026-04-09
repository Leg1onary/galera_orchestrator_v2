# =============================================================================
# Stage 1 — Frontend build
# Node Alpine: builds Vue 3 + Vite SPA into /frontend/dist/
# Output lands in backend/static/ via vite.config.js build.outDir
# =============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

# Copy only manifests first — layer cache is preserved if deps don't change
COPY frontend/package.json frontend/package-lock.json* ./

RUN npm ci --silent

# Copy source and build
COPY frontend/ ./

RUN npm run build
# Vite outputs to ../backend/static (per vite.config.js build.outDir)
# The built files land at /frontend/../backend/static = /backend/static


# =============================================================================
# Stage 2 — Python runtime
# Slim Bookworm: FastAPI + Uvicorn + all backend deps
# =============================================================================
FROM python:3.11-slim-bookworm AS runtime

# Non-interactive, no .pyc files, unbuffered stdout for Docker logs
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps: libmariadb for pymysql SSL, openssh-client for paramiko host key
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

# Install Python deps first (layer cache)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend from Stage 1 into backend/static/
# (Vite already placed files here during Stage 1 build, so this just
#  confirms the directory is present in the runtime image)
COPY --from=frontend-builder /backend/static ./static

# Per ТЗ раздел 2: SQLite lives on a Docker volume at /data/
# Create the mount point so Docker doesn't create it as root-owned dir
RUN mkdir -p /data

# Per ТЗ раздел 3.2: SSH key is mounted read-only by docker-compose.
# Create the directory so the bind mount has a proper target.
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Expose the single port the container serves (API + static)
EXPOSE 8000

# Healthcheck — polls /api/auth/me which requires no auth and returns 401
# A 401 means FastAPI is up; we accept codes 200 and 401 as healthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c \
        "import urllib.request, sys; \
         r = urllib.request.urlopen('http://localhost:8000/api/auth/me', timeout=4); \
         sys.exit(0)" \
    || python -c \
        "import urllib.error, urllib.request, sys; \
         try: urllib.request.urlopen('http://localhost:8000/api/auth/me', timeout=4) \
         except urllib.error.HTTPError as e: sys.exit(0 if e.code == 401 else 1) \
         except Exception: sys.exit(1)"

# Start Uvicorn — main:app is the FastAPI instance in /backend/main.py
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]