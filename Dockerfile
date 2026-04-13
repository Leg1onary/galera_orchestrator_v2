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
# curl нужен для healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-client \
        curl \
    && rm -rf /var/lib/apt/lists/*

# SEC-004: Create non-root user (uid=1001) to run the application
# Using a static UID avoids conflicts with host user IDs
RUN groupadd --gid 1001 nonroot \
    && useradd --uid 1001 --gid 1001 --no-create-home --shell /bin/false nonroot

WORKDIR /backend

# Зависимости отдельным слоем — кэшируются если requirements.txt не менялся
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend source
COPY backend/ ./

# Статика из Stage 1
COPY --from=frontend-builder /backend/static ./static

# Volume mount-point для SQLite — владелец: nonroot
RUN mkdir -p /data && chown nonroot:nonroot /data && chmod 755 /data

# SSH-ключ монтируется bind-mount'ом read-only — директория должна существовать
RUN mkdir -p /home/nonroot/.ssh && chown nonroot:nonroot /home/nonroot/.ssh && chmod 700 /home/nonroot/.ssh

# Права на /backend
RUN chown -R nonroot:nonroot /backend

# SEC-004: Switch to non-root user
USER nonroot

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
