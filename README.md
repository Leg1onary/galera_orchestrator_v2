<div align="center">

<img src="https://raw.githubusercontent.com/mariadb-corporation/mariadb-community-columnstore-engine/main/docs/images/mariadb-logo.png" width="72" alt="MariaDB" />

# 🕷️ Galera Orchestrator v2

**Self-hosted web panel for monitoring and managing MariaDB Galera clusters.**

> Real-time node state · Recovery wizard · Rolling restart · SSH diagnostics
> — all from a **single Docker container**.

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![MariaDB](https://img.shields.io/badge/MariaDB-Galera-003545?style=flat-square&logo=mariadb&logoColor=white)](https://mariadb.com/kb/en/galera-cluster/)
[![WebSocket](https://img.shields.io/badge/Realtime-WebSocket-8A2BE2?style=flat-square)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![JWT](https://img.shields.io/badge/Auth-JWT%20httpOnly-black?style=flat-square&logo=jsonwebtokens&logoColor=white)](https://jwt.io)
[![SSH](https://img.shields.io/badge/SSH-paramiko-4E9A06?style=flat-square&logo=gnubash&logoColor=white)](https://www.paramiko.org)

</div>

<br/>

---

## 🗒️ Contents

| | Section |
|---|---|
| 📌 | [Overview](#-overview) |
| ⚡ | [Quick Start](#-quick-start) |
| ⚙️ | [Configuration Reference](#%EF%B8%8F-configuration-reference) |
| 🔑 | [SSH Key Setup](#-ssh-key-setup) |
| 💾 | [Data Persistence](#-data-persistence) |
| 🖥️ | [Pages & Features](#%EF%B8%8F-pages--features) |
| 📁 | [Project Structure](#-project-structure) |
| 👨‍💻 | [Development](#-development) |
| 🧪 | [Running E2E Tests](#-running-e2e-tests) |
| 🔒 | [Security Notes](#-security-notes) |
| 🔧 | [Troubleshooting](#-troubleshooting) |

---

## 📌 Overview

Galera Orchestrator v2 is a **greenfield** SPA built on FastAPI + Vue 3, deployed as a single Docker container.
Backend serves both the REST API and the compiled frontend static files from one process.

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  🐳 Docker Container                                     │
│                                                         │
│  ⚡ FastAPI (Uvicorn)                                    │
│   ├── 📡 REST API      /api/...                          │
│   ├── 🔄 WebSocket    /ws/clusters/{cluster_id}         │
│   └── 🌐 SPA static   /* → /backend/static/             │
│                                                         │
│  🗄️ SQLite          /data/orchestrator.db  [volume]   │
│  🔑 SSH key          /root/.ssh/id_rsa      [ro mount] │
└─────────────────────────────────────────────────────────┘
```

### 🧩 Tech Stack

| Layer | Technologies |
|-------|--------------|
| 🐍 Backend | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy Core, SQLite, paramiko, pymysql, PyJWT, Fernet |
| 💻 Frontend | Vue 3, Vite, Pinia, Vue Router, VueUse, Vue Query, Vue3-Charts |
| 🐳 Deploy | Docker, Docker Compose, single container |

---

## ⚡ Quick Start

### 📋 Requirements

| Dependency | Version |
|---|---|
| 🐳 Docker | 24+ |
| 🐳 Docker Compose | v2 plugin |
| 🔑 SSH key | RSA / Ed25519, passwordless, access to all nodes and arbitrators |

### 1️⃣ Clone and configure

```bash
git clone https://github.com/Leg1onary/galera_orchestrator_v2.git
cd galera_orchestrator_v2
cp .env.example .env
```

Edit `.env` — **change all three secrets before first start**:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password

# openssl rand -hex 32
JWT_SECRET_KEY=<random-32+-chars>

# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_SECRET_KEY=<fernet-key>

SSH_KEY_HOST_PATH=/root/.ssh/id_rsa
```

> ⚠️ **Important:** `JWT_SECRET_KEY` and `FERNET_SECRET_KEY` must be **different** values.

### 2️⃣ Start

```bash
docker compose up -d
```

🌍 Panel: **http://localhost:8000**
👤 Login: `admin` / password from `.env`

### 3️⃣ Stop (data preserved)

```bash
docker compose down
```

---

## ⚙️ Configuration Reference

| Variable | Default | Required | Description |
|---|---|---|---|
| `ADMIN_USERNAME` | `admin` | — | 👤 Admin login |
| `ADMIN_PASSWORD` | `changeme` | ✅ change | 🔒 Admin password |
| `JWT_SECRET_KEY` | `change-me-jwt-secret` | ✅ change | 🎫 JWT signing secret (min 32 chars) |
| `FERNET_SECRET_KEY` | `change-me-fernet-secret` | ✅ change | 🔐 Fernet key for encrypting node DB passwords |
| `SSH_KEY_HOST_PATH` | `/root/.ssh/id_rsa` | ✅ | 🔑 Host path to SSH private key |
| `DATABASE_URL` | `sqlite:////data/orchestrator.db` | — | 🗄️ SQLite path inside container |
| `HOST_PORT` | `8000` | — | 🌐 Host port to expose |
| `SSH_CONNECT_TIMEOUT` | `5` | — | ⏱️ SSH connect timeout, seconds |
| `SSH_COMMAND_TIMEOUT` | `10` | — | ⏱️ SSH command timeout, seconds |
| `DB_CONNECT_TIMEOUT` | `3` | — | ⏱️ MariaDB connect timeout, seconds |

---

## 🔑 SSH Key Setup

The application uses **one global SSH key** for all connections to nodes and arbitrators.
The key is bind-mounted **read-only** into the container — never stored in the database.

```yaml
# docker-compose.yml (already configured)
volumes:
  - ${SSH_KEY_HOST_PATH}:/root/.ssh/id_rsa:ro
```

✅ Verify the key reaches your nodes before first start:

```bash
ssh -i ~/.ssh/id_rsa -p 22 root@<node-host> "hostname"
```

The key must be **passwordless**. Non-standard path? Set in `.env`:

```env
SSH_KEY_HOST_PATH=/home/user/.ssh/galera_key
```

---

## 💾 Data Persistence

SQLite lives at `/data/orchestrator.db` inside the container, backed by the `orchestrator-data` Docker named volume.
Data survives container restarts and image upgrades.

### 📦 Backup

```bash
docker run --rm \
  -v orchestrator-data:/data \
  -v "$(pwd)":/backup \
  alpine \
  tar czf /backup/orchestrator-db-$(date +%Y%m%d-%H%M%S).tar.gz /data
```

### ♻️ Restore

```bash
docker compose down
docker run --rm \
  -v orchestrator-data:/data \
  -v "$(pwd)":/backup \
  alpine \
  sh -c "cd / && tar xzf /backup/orchestrator-db-YYYYMMDD-HHMMSS.tar.gz"
docker compose up -d
```

### ⬆️ Upgrade image (data preserved)

```bash
docker compose pull      # or: docker compose build
docker compose up -d     # recreates container, volume untouched
```

---

## 🖥️ Pages & Features

| Route | Page | Description |
|---|---|---|
| 🏠 `/` | Overview | Cluster summary bar, NodeCards with sparklines, EventLog |
| 🗊 `/nodes` | Nodes | Full node table, NodeDetailDrawer, per-node actions |
| 🗺️ `/topology` | Topology | SVG canvas — DC zones, nodes, arbitrators, connection lines |
| 🚑 `/recovery` | Recovery | Wizard: diagnose → select bootstrap node → confirm → execute |
| 🔧 `/maintenance` | Maintenance | Per-node R/O·R/W, Enter/Exit Maintenance, rolling restart wizard |
| 🔍 `/diagnostics` | Diagnostics | Config diff, variable check, resource probe via SSH |
| ⚙️ `/settings` | Settings | CRUD for clusters, nodes, arbitrators, datacenters, system settings |
| 📖 `/docs` | Docs | Built-in reference documentation |
| 🔐 `/login` | Login | JWT auth via httpOnly cookie |

### 🎨 Node Status Colors

| Indicator | State | Meaning |
|---|---|---|
| 🟢 Green | `SYNCED` | Node is synced, R/W — fully operational |
| 🟡 Yellow | `SYNCED` + R/O | Node is synced but in read-only mode |
| 🔵 Blue | `DONOR` / `JOINER` / `DESYNCED` | Sync in progress |
| 🟠 Orange | `wsrep_ready = OFF` | Node degraded, cluster unstable |
| 🔴 Red | `OFFLINE` | No SSH / MariaDB down / unreachable |

### 🔄 WebSocket Events

Real-time updates via `WS /ws/clusters/{cluster_id}`:

| Event | 📨 Payload |
|---|---|
| `node_state_changed` | Updated node live-fields |
| `arbitrator_state_changed` | Updated arbitrator state |
| `operation_started` | New cluster operation created |
| `operation_progress` | Step-by-step log line |
| `operation_finished` | Final operation status |
| `log_entry` | New event_log record |

### 🛡️ Cluster Lock

> Only **one active operation** (`pending` / `running` / `cancel_requested`) is allowed per cluster at a time.
> A second attempt returns **`409 Conflict`**. This applies to recovery, maintenance, and node actions.

---

## 📁 Project Structure

```
galera_orchestrator_v2/
├── 🐍 backend/
│   ├── main.py              # ⚡ FastAPI app, SPA fallback, lifespan
│   ├── config.py            # ⚙️ Settings via pydantic-settings
│   ├── database.py          # 🗄️ SQLAlchemy Core engine, init_db
│   ├── models.py            # 📊 8 table definitions
│   ├── auth.py              # 🔒 JWT helpers, Fernet encrypt/decrypt
│   ├── ssh_client.py        # 💻 paramiko wrapper, global key
│   ├── db_client.py         # 🔄 pymysql wrapper, Fernet decrypt
│   ├── polling.py           # ⏱️ asyncio background polling loop
│   ├── websocket.py         # 📡 WS manager, broadcast, auth
│   ├── dependencies.py      # 🧲 FastAPI Depends (get_current_user, …)
│   ├── requirements.txt
│   └── routers/
│       ├── auth.py            # 🔐 POST /login, /logout, GET /me
│       ├── clusters.py        # 🏛️ GET /clusters, /contours, /status, /log
│       ├── nodes.py           # 🖥️ GET/PATCH nodes, actions, test-connection
│       ├── arbitrators.py     # ⚖️ GET arbitrators, test-connection, log
│       ├── recovery.py        # 🚑 GET/POST recovery/*
│       ├── maintenance.py     # 🔧 GET/POST maintenance/*
│       ├── diagnostics.py     # 🔍 GET/POST diagnostics/*
│       └── settings.py        # ⚙️ CRUD clusters/nodes/arbitrators/dc/system
├── 💻 frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/index.ts
│   │   ├── stores/            # 🎨 auth, ws, cluster
│   │   ├── api/               # 📡 axios client + typed API modules
│   │   ├── data/docs.ts       # 📖 static docs content (no API)
│   │   ├── pages/             # 🗺️ 9 page components
│   │   ├── layouts/
│   │   └── components/        # 🧩 feature components grouped by page
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── 🧪 tests/
│   └── e2e/
│       └── test_critical_paths.py
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── 📝 .env.example
├── 🚫 .gitignore
└── 📚 README.md
```

---

## 👨‍💻 Development

### 🐍 Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 💻 Frontend

```bash
cd frontend
npm install
npm run dev        # Vite dev server on :5173, proxies /api and /ws → :8000
```

### 🐳 Full stack via Docker

```bash
docker compose up --build
```

---

## 🧪 Running E2E Tests

Tests run against a live container — **no real Galera nodes required**.

```bash
# 📦 Install deps
pip install pytest httpx pytest-asyncio websockets

# ▶️ Run all
E2E_BASE_URL=http://localhost:8000 \
ADMIN_USERNAME=admin \
ADMIN_PASSWORD=your-password \
pytest tests/e2e/ -v

# 🎯 Run specific group
pytest tests/e2e/ -v -k "TestAuth"
pytest tests/e2e/ -v -k "TestWebSocket"
```

**📋 Coverage:**

- ✅ SPA fallback + OpenAPI schema
- ✅ Auth: login, logout, httpOnly cookie, wrong credentials
- ✅ All cluster-scoped endpoint contracts + status structure
- ✅ Settings CRUD: cluster, datacenter, node validation
- ✅ Node action schema + cluster lock `409 Conflict`
- ✅ Recovery / Maintenance endpoint contracts
- ✅ Diagnostics endpoint contracts
- ✅ WebSocket auth + event structure
- ✅ Security headers + CORS

---

## 🔒 Security Notes

| 🛡️ Concern | Mitigation |
|---|---|
| 🔑 Admin password | Change `ADMIN_PASSWORD` before first deploy — default is `changeme` |
| 🎫 JWT secret | Generate a random 32+ char string; store in `.env` only |
| 🔄 Fernet key rotation | Changing `FERNET_SECRET_KEY` **invalidates all stored node passwords** — re-enter them in Settings |
| 💾 SSH key | Mounted `:ro` — container cannot modify or exfiltrate it |
| 🍪 JWT in JS | Token lives only in `httpOnly` cookie — inaccessible to JavaScript |
| ⚠️ No mock mode | All SSH / SQL actions are **real** — use a test cluster for experiments |
| 🔇 Dual secrets | `JWT_SECRET_KEY` and `FERNET_SECRET_KEY` **must** be different values |

---

## 🔧 Troubleshooting

<details>
<summary>🚫 Panel unreachable after start</summary>

```bash
docker compose logs orchestrator
docker compose ps
```
</details>

<details>
<summary>🔐 <code>401</code> after login (cookie not sent)</summary>

Make sure you access the panel on the **same host and port** as configured.
`httpOnly` cookies are not sent cross-origin.
</details>

<details>
<summary>🔴 Node shows <code>OFFLINE</code> immediately</summary>

Verify SSH key access from the host:
```bash
ssh -i ~/.ssh/id_rsa -p <ssh_port> <ssh_user>@<node_host> "hostname"
```
</details>

<details>
<summary>🔐 <code>FERNET_SECRET_KEY</code> changed — node passwords broken</summary>

Go to **Settings → Nodes** and re-enter `db_password` for every affected node.
</details>

<details>
<summary>📴 WebSocket shows <code>Disconnected</code> in footer</summary>

Check the container is running and no firewall blocks port 8000 for WebSocket upgrade:
```bash
docker compose ps
curl -i -N \
  -H "Upgrade: websocket" \
  -H "Connection: Upgrade" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/ws/clusters/1
```
</details>

---

<div align="center">

**🕷️ Galera Orchestrator v2**

<sub>Built for ops teams who need real control, not pretty dashboards.</sub>

<br/>

[![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red?style=flat-square)](https://github.com/Leg1onary/galera_orchestrator_v2)
[![FastAPI](https://img.shields.io/badge/Powered%20by-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/UI-Vue%203-42b883?style=flat-square&logo=vue.js)](https://vuejs.org)

</div>
