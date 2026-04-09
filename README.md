# Galera Orchestrator v2

Self-hosted management panel for **MariaDB Galera** clusters.  
Monitors node state in real-time, runs recovery/maintenance operations,
and provides diagnostics — all from a single Docker container.

---

## Requirements

| Dependency        | Version   |
|-------------------|-----------|
| Docker            | 24+       |
| Docker Compose    | v2 plugin |
| SSH key           | RSA / Ed25519, passwordless, access to all nodes |

---

## Quick Start

### 1 — Clone and configure

```bash
git clone https://github.com/your-org/galera-orchestrator-v2.git
cd galera-orchestrator-v2
cp .env.example .env
```

Edit `.env`:

```env
ADMIN_PASSWORD=your-strong-password

# openssl rand -hex 32
JWT_SECRET_KEY=<random 32+ chars>

# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_SECRET_KEY=<fernet key>

SSH_KEY_HOST_PATH=~/.ssh/id_rsa
```

### 2 — Start

```bash
docker compose up -d
```

Panel: **http://localhost:8000**  
Default login: `admin` / password from `.env`.

### 3 — Stop (data preserved)

```bash
docker compose down
```

---

## Configuration Reference

| Variable              | Default                              | Required | Description |
|-----------------------|--------------------------------------|----------|-------------|
| `ADMIN_USERNAME`      | `admin`                              | —        | Admin login |
| `ADMIN_PASSWORD`      | `changeme`                           | ✅ change | Admin password |
| `JWT_SECRET_KEY`      | `change-me-jwt-secret-min-32-chars`  | ✅ change | JWT signing secret (min 32 chars) |
| `FERNET_SECRET_KEY`   | `change-me-fernet-key`               | ✅ change | Fernet key for node password encryption |
| `DATABASE_URL`        | `sqlite:////data/orchestrator.db`    | —        | SQLite path inside container |
| `SSH_KEY_HOST_PATH`   | `~/.ssh/id_rsa`                      | ✅        | Host path to SSH private key |
| `HOST_PORT`           | `8000`                               | —        | Host port to expose |
| `SSH_CONNECT_TIMEOUT` | `5`                                  | —        | SSH connect timeout (sec) |
| `SSH_COMMAND_TIMEOUT` | `10`                                 | —        | SSH command timeout (sec) |
| `DB_CONNECT_TIMEOUT`  | `3`                                  | —        | MariaDB connect timeout (sec) |

---

## SSH Key

One global SSH key is used for all nodes and arbitrators.  
It is **bind-mounted read-only** into the container — never stored in the database.

```bash
# Verify the key reaches a node
ssh -i ~/.ssh/id_rsa -p 22 root@<node-host> "hostname"
```

The key must be passwordless. If your key is at a non-standard path:

```env
# .env
SSH_KEY_HOST_PATH=/home/user/.ssh/galera_key
```

---

## Data Persistence

SQLite lives at `/data/orchestrator.db` inside the container, backed by the
`orchestrator-data` Docker named volume. Data survives container restarts
and image upgrades.

### Backup

```bash
docker run --rm \
  -v orchestrator-data:/data \
  -v "$(pwd)":/backup \
  alpine \
  tar czf /backup/orchestrator-db-$(date +%Y%m%d-%H%M%S).tar.gz /data
```

### Restore

```bash
docker compose down
docker run --rm \
  -v orchestrator-data:/data \
  -v "$(pwd)":/backup \
  alpine \
  sh -c "cd / && tar xzf /backup/orchestrator-db-YYYYMMDD-HHMMSS.tar.gz"
docker compose up -d
```

### Upgrade image (data preserved)

```bash
docker compose pull        # or: docker compose build
docker compose up -d       # recreates container, volume untouched
```

---

## Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 8000 | HTTP     | Web panel + REST API + WebSocket |

To expose on port 80: set `HOST_PORT=80` in `.env`.

---

## Running E2E Tests

```bash
# Install test deps
pip install pytest httpx pytest-asyncio websockets

# Run against local container
E2E_BASE_URL=http://localhost:8000 \
ADMIN_USERNAME=admin \
ADMIN_PASSWORD=your-password \
pytest tests/e2e/ -v

# Run specific path group
pytest tests/e2e/ -v -k "TestAuth"
pytest tests/e2e/ -v -k "TestWebSocket"
```

Tests cover (without real Galera nodes):
- SPA fallback + OpenAPI schema
- Auth: login, logout, httpOnly cookie, wrong password
- All cluster-scoped endpoint contracts + status structure
- Settings CRUD (cluster, datacenter, node validation)
- Node action schema + cluster lock 409
- Recovery / Maintenance endpoint contracts
- Diagnostics endpoint contracts
- WebSocket auth + event structure
- Security headers + CORS

---

## Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # Vite dev server on :5173, proxies /api → :8000
```

### Full stack (Docker)

```bash
docker compose up --build
```

---

## Project Structure

```
galera-orchestrator-v2/
├── backend/
│ ├── main.py # FastAPI app, SPA fallback, lifespan
│ ├── config.py # Settings (pydantic-settings from env)
│ ├── database.py # SQLAlchemy Core engine, init_db
│ ├── models.py # Table definitions (8 tables)
│ ├── auth.py # JWT helpers, Fernet encrypt/decrypt
│ ├── ssh_client.py # paramiko wrapper, global key
│ ├── db_client.py # pymysql wrapper, Fernet decrypt
│ ├── polling.py # asyncio background polling loop
│ ├── websocket.py # WS manager, broadcast, auth
│ ├── dependencies.py # FastAPI Depends (get_current_user, etc.)
│ ├── requirements.txt
│ └── routers/
│ ├── auth.py # POST /login, /logout, GET /me
│ ├── clusters.py # GET /clusters, /contours, /status, /log
│ ├── nodes.py # GET/PATCH nodes, actions, test-connection
│ ├── arbitrators.py # GET arbitrators, test-connection, log
│ ├── recovery.py # GET/POST recovery/*
│ ├── maintenance.py # GET/POST maintenance/*
│ ├── diagnostics.py # GET/POST diagnostics/*
│ └── settings.py # CRUD clusters/nodes/arbitrators/dc/system
├── frontend/
│ ├── src/
│ │ ├── main.ts
│ │ ├── App.vue
│ │ ├── router/index.ts
│ │ ├── stores/ # auth, ws, cluster
│ │ ├── api/ # axios client + typed API modules
│ │ ├── data/docs.ts # static docs content (no API)
│ │ ├── pages/ # 9 page components
│ │ ├── layouts/
│ │ └── components/ # feature components by page
│ ├── index.html
│ ├── vite.config.ts
│ └── package.json
├── tests/
│ └── e2e/
│ └── test_critical_paths.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```


---

## Security Notes

| Concern | Mitigation |
|---------|-----------|
| Admin password | Change `ADMIN_PASSWORD` before first deploy |
| JWT secret | Generate random 32+ char string, store in `.env` only |
| Fernet key rotation | Changing `FERNET_SECRET_KEY` invalidates all stored node passwords — re-enter them in Settings |
| SSH key | Mounted `:ro` — container cannot modify or exfiltrate |
| Credentials in JS | JWT lives only in httpOnly cookie — inaccessible to JavaScript |
| No mock mode | All SSH/SQL actions are real — use a test cluster for experiments |

---

## Troubleshooting

**Panel unreachable after start**
```bash
docker compose logs orchestrator
docker compose ps
```

**`401` after login (cookie not sent)**  
Check that you access the panel on the same host/port as configured.
httpOnly cookies are not sent cross-origin.

**Node shows `OFFLINE` immediately**  
Verify SSH key access:
```bash
ssh -i ~/.ssh/id_rsa -p <ssh_port> <ssh_user>@<node_host> "hostname"
```

**`FERNET_SECRET_KEY` changed — node passwords broken**  
Go to Settings → Nodes → re-enter `db_password` for affected nodes.

**WebSocket `Disconnected` in footer**  
Check container is running, no firewall blocks port 8000 for WS upgrade.