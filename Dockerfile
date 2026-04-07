# ================================================================
# Galera Orchestrator v2 — Multi-stage Dockerfile
#
# Stage 1: Build Vue 3 frontend
# Stage 2: Production Python image with built frontend
#
# Usage:
#   docker build -t galera-orchestrator-v2 .
#   docker run -p 8000:8000 -v $(pwd)/config:/app/config galera-orchestrator-v2
# ================================================================

# ── Stage 1: Frontend build ──────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --quiet

COPY frontend/ ./
RUN npm run build
# Output: /build/frontend/../backend/static (per vite.config.js outDir)

# ── Stage 2: Production image ────────────────────────────────────
FROM python:3.11-slim AS production

# System deps for paramiko / cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY backend/ ./backend/
COPY config/   ./config/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /build/backend/static ./backend/static

# Create config from example if not mounted
RUN if [ ! -f /app/config/nodes.yaml ]; then \
      cp /app/config/nodes.example.yaml /app/config/nodes.yaml; \
    fi

# Logs directory
RUN mkdir -p /app/logs

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
