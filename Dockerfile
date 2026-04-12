# =============================================================================
# Stage 1 — Frontend build
# =============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build
# Vite outDir = ../backend/static → файлы попадают в /backend/static/


# =============================================================================
# Stage 2 — Python runtime
# =============================================================================
FROM python:3.11-slim-bookworm AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_ACCESS_LOG=1

# openssh-client нужен paramiko для known_hosts и host-key проверок
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-client \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

# Зависимости отдельным слоем — кэшируются если requirements.txt не менялся
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend source
COPY backend/ ./

# Статика из Stage 1
COPY --from=frontend-builder /backend/static ./static

# Volume mount-point для SQLite
RUN mkdir -p /data && chmod 755 /data

# SSH-ключ монтируется bind-mount'ом read-only — директория должна существовать
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

EXPOSE 8000

# Healthcheck принимает 200 И 401 как "живой"
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/me \
        | grep -qE "^(200|401)$"

CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info", \
     "--no-access-log"]
