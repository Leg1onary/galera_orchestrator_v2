<div align="center">

<br/>

```
 ██████╗  █████╗ ██╗     ███████╗██████╗  █████╗
██╔════╝ ██╔══██╗██║     ██╔════╝██╔══██╗██╔══██╗
██║  ███╗███████║██║     █████╗  ██████╔╝███████║
██║   ██║██╔══██║██║     ██╔══╝  ██╔══██╗██╔══██║
╚██████╔╝██║  ██║███████╗███████╗██║  ██║██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝

 ██████╗ ██████╗  ██████╗██╗  ██╗███████╗███████╗████████╗██████╗  █████╗ ████████╗ ██████╗ ██████╗
██╔═══██╗██╔══██╗██╔════╝██║  ██║██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
██║   ██║██████╔╝██║     ███████║█████╗  ███████╗   ██║   ██████╔╝███████║   ██║   ██║   ██║██████╔╝
██║   ██║██╔══██╗██║     ██╔══██║██╔══╝  ╚════██║   ██║   ██╔══██╗██╔══██║   ██║   ██║   ██║██╔══██╗
╚██████╔╝██║  ██║╚██████╗██║  ██║███████╗███████║   ██║   ██║  ██║██║  ██║   ██║   ╚██████╔╝██║  ██║
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
```

### v2 — Self-hosted control panel for MariaDB Galera clusters

*Real-time monitoring · Recovery wizard · Rolling restart · SSH diagnostics*
*— all from a **single Docker container.***

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![MariaDB Galera](https://img.shields.io/badge/MariaDB-Galera-003545?style=flat-square&logo=mariadb&logoColor=white)](https://mariadb.com/kb/en/galera-cluster/)
[![WebSocket](https://img.shields.io/badge/Realtime-WebSocket-8A2BE2?style=flat-square)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![JWT httpOnly](https://img.shields.io/badge/Auth-JWT%20httpOnly-black?style=flat-square&logo=jsonwebtokens&logoColor=white)](https://jwt.io)
[![SSH](https://img.shields.io/badge/SSH-paramiko-4E9A06?style=flat-square&logo=gnubash&logoColor=white)](https://www.paramiko.org)

</div>

<br/>

---

## ⚡ What is this?

**Galera Orchestrator v2** is a production-grade ops panel for teams running **MariaDB Galera** clusters.
No agents on nodes. No complex setup. Just a Docker container, your SSH key, and full control.

```
  Your Browser  ──────────────►  Docker Container (port 8000)
                                  │
                                  ├─ Vue 3 SPA          (served as static)
                                  ├─ FastAPI REST API    /api/...
                                  ├─ WebSocket           /ws/clusters/{id}
                                  └─ Background Poller   (asyncio, every 5s)
                                           │
                          ┌────────────────┼────────────────┐
                          ▼                ▼                ▼
                       node-1           node-2           node-3
                    SSH + MariaDB    SSH + MariaDB    SSH + MariaDB
```

> **No agents. No plugins. No magic.**
> The orchestrator connects to your nodes via **SSH** and **MariaDB** directly.

---

## 🗒️ Contents

| | Section |
|---|---|
| 🚀 | [Quick Start](#-quick-start) |
| ⚙️ | [Configuration Reference](#%EF%B8%8F-configuration-reference) |
| 🔑 | [SSH Key Setup](#-ssh-key-setup) |
| 🖥️ | [Pages & Features](#%EF%B8%8F-pages--features) |
| 🔄 | [Real-time & WebSocket](#-real-time--websocket) |
| 🏗️ | [Architecture](#%EF%B8%8F-architecture) |
| 📁 | [Project Structure](#-project-structure) |
| 💾 | [Data Persistence & Backup](#-data-persistence--backup) |
| 👨‍💻 | [Development](#-development) |
| 🧪 | [E2E Tests](#-e2e-tests) |
| 🔒 | [Security Notes](#-security-notes) |
| 🔧 | [Troubleshooting](#-troubleshooting) |

---

## 🚀 Quick Start

### Prerequisites

| Dependency | Version |
|---|---|
| 🐳 Docker | 24+ |
| 🐳 Docker Compose | v2 plugin |
| 🔑 SSH private key | RSA / Ed25519, passwordless, access to all Galera nodes |

### 1. Clone & configure

```bash
git clone https://github.com/Leg1onary/galera_orchestrator_v2.git
cd galera_orchestrator_v2
cp .env.example .env
```

Open `.env` and **change all three secrets before first start**:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password        # ← change this

# Generate: openssl rand -hex 32
JWT_SECRET_KEY=<random-32+-chars>           # ← change this

# Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_SECRET_KEY=<fernet-key>             # ← change this

SSH_KEY_HOST_PATH=/root/.ssh/id_rsa        # path to your SSH key on the host
```

> ⚠️ `JWT_SECRET_KEY` and `FERNET_SECRET_KEY` must be **different** values.

### 2. Start

```bash
docker compose up -d
```

| | |
|---|---|
| 🌍 **Panel** | http://localhost:8000 |
| 👤 **Login** | `admin` / password from `.env` |
| 📖 **API Docs** | http://localhost:8000/docs |

### 3. Add your first cluster

1. Go to **Settings → Clusters** → create cluster
2. **Settings → Datacenters** → create datacenter(s)
3. **Settings → Nodes** → add nodes (host, SSH port, DB credentials)
4. Select cluster in the top bar → watch **Overview** come alive 🎉

### 4. Stop (data preserved)

```bash
docker compose down
```

---

## ⚙️ Configuration Reference

All configuration via `.env` file. Sensible defaults for everything except secrets.

| Variable | Default | Required | Description |
|---|---|---|---|
| `ADMIN_USERNAME` | `admin` | — | Admin login username |
| `ADMIN_PASSWORD` | `changeme` | **✅ change** | Admin password |
| `JWT_SECRET_KEY` | `change-me-jwt-secret` | **✅ change** | JWT signing secret (min 32 chars) |
| `FERNET_SECRET_KEY` | `change-me-fernet-secret` | **✅ change** | Fernet key — encrypts node DB passwords in SQLite |
| `SSH_KEY_HOST_PATH` | `/root/.ssh/id_rsa` | **✅** | Host path to SSH private key (bind-mounted `:ro`) |
| `DATABASE_URL` | `sqlite:////data/orchestrator.db` | — | SQLite path inside container |
| `HOST_PORT` | `8000` | — | Host port to expose |
| `SSH_CONNECT_TIMEOUT` | `5` | — | SSH connect timeout, seconds |
| `SSH_COMMAND_TIMEOUT` | `10` | — | SSH command timeout, seconds |
| `DB_CONNECT_TIMEOUT` | `3` | — | MariaDB connect timeout, seconds |

---

## 🔑 SSH Key Setup

The orchestrator uses **one global SSH key** for all node/arbitrator connections.
The key is **bind-mounted read-only** into the container — never stored in the database.

```yaml
# docker-compose.yml (already set up)
volumes:
  - ${SSH_KEY_HOST_PATH}:/root/.ssh/id_rsa:ro
```

✅ Verify access before starting:

```bash
ssh -i ~/.ssh/id_rsa -p 22 root@<node-host> "hostname && mysql -e 'SELECT 1'"
```

Using a non-standard path? Just set it in `.env`:

```env
SSH_KEY_HOST_PATH=/home/ops/.ssh/galera_ed25519
```

> The key must be **passwordless**. `ssh-keygen -t ed25519 -N ""` creates one in seconds.

---

## 🖥️ Pages & Features

### 🏠 Overview

The command center. Everything important at a glance.

- **Cluster summary bar** — status, node count, primary component health
- **NodeCards** — per-node state, wsrep metrics, read_only flag, maintenance badge
- **Sparklines** — 30-point ring buffer for `flow_control_paused` and `recv_queue`
- **Event Log** — real-time stream of cluster events with severity badges
- **WebSocket indicator** — live connection status in footer

### 🗊 Nodes

Full node table with everything you need for day-to-day ops.

- Sort/filter by name, state, datacenter, contour
- **NodeDetailDrawer** — expand any node for full wsrep variable dump
- Per-node actions: toggle read_only, enter/exit maintenance, restart MariaDB
- **Connection test** — on-demand SSH + DB reachability check
- State badges: `SYNCED` · `JOINED` · `DONOR` · `DESYNCED` · `OFFLINE`

### 🗺️ Topology

SVG canvas — visual representation of your cluster layout.

- Nodes and arbitrators grouped by **datacenter zones**
- **Contour** groupings (prod / staging / etc.)
- Connection lines with state color coding
- Zoom, pan, drag — full interactive canvas
- Real-time state updates via WebSocket

### 🚑 Recovery

Step-by-step wizard for full cluster recovery when **all nodes are down**.

```
Step 1 — Scan nodes
  └─ SSH into each node, read cluster status & wsrep state
  └─ Detects which nodes are offline / non-primary

Step 2 — Select bootstrap node
  └─ Shows seqno from grastate.dat for each node
  └─ Highlights the safe-to-bootstrap candidate
  └─ Manual override with explicit confirmation

Step 3 — Bootstrap & rejoin
  └─ Executes bootstrap on selected node
  └─ Monitors SYNCED state before rejoining next node
  └─ Real-time progress log via WebSocket

Step 4 — Done
  └─ Cluster health confirmation
  └─ Link back to Overview
```

> 🛡️ **Cluster lock**: only one recovery operation at a time. Concurrent attempts → `409 Conflict`.

### 🔧 Maintenance

Controlled maintenance operations without cluster downtime.

- **Enter / Exit Maintenance** — sets `read_only = ON/OFF` per node via SSH + MariaDB
- **Rolling Restart Wizard** — restarts MariaDB node-by-node:
  1. Choose restart order (drag to reorder)
  2. Each node: enter maintenance → `systemctl restart mariadb` → wait for `SYNCED` → next
  3. Zero downtime for the cluster as a whole
- Live progress log, abort at any step

> ⚠️ Never put **all nodes** into maintenance simultaneously — the cluster will lose quorum.

### 🔍 Diagnostics

SSH-powered cluster health inspection without leaving the browser.

- **Config diff** — compare `my.cnf` / `galera.cnf` across all nodes, highlight differences
- **Variable check** — verify critical Galera variables match across the cluster
- **Resource probe** — disk usage, memory, open file handles via SSH
- Per-node execution — run diagnostics on selected subset of nodes

### ⚙️ Settings

Full CRUD management of all cluster entities.

| Entity | Fields |
|---|---|
| **Clusters** | Name, description, contour |
| **Datacenters** | Name, cluster association |
| **Nodes** | Host, ports, SSH user, DB credentials (Fernet-encrypted), datacenter |
| **Arbitrators** | Host, SSH port, datacenter |
| **System** | Polling interval, SSH/DB timeouts |

---

## 🔄 Real-time & WebSocket

All live data flows through a single WebSocket per cluster:

```
WS /ws/clusters/{cluster_id}
```

Authentication via the same `httpOnly` JWT cookie — no separate WS token needed.

| Event | Payload | Triggered by |
|---|---|---|
| `node_state_changed` | Updated node live-fields | Poller detects state change |
| `arbitrator_state_changed` | Updated arbitrator state | Poller detects arb change |
| `operation_started` | Operation id, type, target | Recovery / Maintenance start |
| `operation_progress` | Step log line, timestamp | Mid-operation execution |
| `operation_finished` | Final status, duration | Operation completes or fails |
| `log_entry` | New event_log record | Any cluster event |

**Poller** runs as an asyncio background task, polling every `polling_interval_sec` seconds (default: 5s, configurable in Settings). Interval is read from DB on every cycle — Settings changes take effect on next tick without restart.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  🐳 Docker Container                                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ⚡ FastAPI + Uvicorn                                     │    │
│  │   ├─ REST API         /api/clusters/{id}/...             │    │
│  │   ├─ Auth             /api/auth/...  (JWT httpOnly)      │    │
│  │   ├─ WebSocket        /ws/clusters/{id}                  │    │
│  │   ├─ SPA fallback     /* → /backend/static/index.html    │    │
│  │   └─ Background       asyncio Poller (5s interval)       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  🗄️ SQLite  /data/orchestrator.db  ──── Docker named volume    │
│  🔑 SSH key /root/.ssh/id_rsa      ──── bind-mount :ro         │
└──────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technologies |
|---|---|
| 🐍 **Backend** | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy Core, paramiko, pymysql, PyJWT, cryptography (Fernet) |
| 💻 **Frontend** | Vue 3, Vite 5, Pinia, Vue Router 4, TanStack Query (Vue Query), PrimeVue, VueUse |
| 🗄️ **Database** | SQLite (via named Docker volume — survives upgrades) |
| 🐳 **Deploy** | Docker multi-stage build, Docker Compose, single container |

### Node Status Color Model

| Color | State | Meaning |
|---|---|---|
| 🟢 **Green** | `SYNCED` | Fully operational, R/W |
| 🟡 **Yellow** | `SYNCED` + read_only | Synced but in maintenance / read-only mode |
| 🔵 **Blue** | `DONOR` / `JOINER` / `DESYNCED` | Sync in progress — temporary |
| 🟠 **Orange** | `wsrep_ready = OFF` | Node degraded, cluster unstable |
| 🔴 **Red** | `OFFLINE` | No SSH / MariaDB down / unreachable |

---

## 📁 Project Structure

```
galera_orchestrator_v2/
│
├── 🐍 backend/
│   ├── main.py                  FastAPI app, SPA fallback, lifespan hooks
│   ├── config.py                pydantic-settings — all env vars in one place
│   ├── database.py              SQLAlchemy Core engine + init_db()
│   ├── models.py                8 table definitions (clusters, nodes, arbs, ops…)
│   ├── auth.py                  JWT helpers, Fernet encrypt/decrypt
│   ├── ssh_client.py            paramiko wrapper, global key, timeouts
│   ├── db_client.py             pymysql wrapper, Fernet-decrypt passwords
│   ├── dependencies.py          FastAPI Depends (get_current_user, get_cluster…)
│   ├── requirements.txt
│   │
│   ├── services/
│   │   ├── poller.py            asyncio background polling loop
│   │   └── ws_manager.py        WebSocket connection manager + broadcast
│   │
│   └── routers/
│       ├── auth.py              POST /login, /logout · GET /me
│       ├── clusters.py          GET clusters, status, event log
│       ├── nodes.py             GET/PATCH nodes, actions, test-connection
│       ├── contours.py          GET contours for cluster
│       ├── recovery.py          GET/POST recovery wizard steps
│       ├── maintenance.py       GET/POST maintenance + rolling restart
│       ├── diagnostics.py       GET/POST SSH diagnostics
│       └── settings.py          CRUD: clusters / nodes / arbs / DC / system
│
├── 💻 frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/index.ts
│   │   │
│   │   ├── stores/              Pinia stores: auth, cluster, ws, recovery
│   │   ├── api/                 Axios client + typed API modules per domain
│   │   ├── data/docs.ts         Static built-in docs content
│   │   │
│   │   ├── pages/               9 page components
│   │   │   ├── OverviewPage.vue
│   │   │   ├── NodesPage.vue
│   │   │   ├── TopologyPage.vue
│   │   │   ├── RecoveryPage.vue
│   │   │   ├── MaintenancePage.vue
│   │   │   ├── DiagnosticsPage.vue
│   │   │   ├── SettingsPage.vue
│   │   │   ├── DocsPage.vue
│   │   │   └── LoginPage.vue
│   │   │
│   │   ├── layouts/             AppLayout (sidebar, topbar, ws-footer)
│   │   └── components/          Feature components grouped by page
│   │
│   ├── index.html
│   ├── vite.config.ts           Vite + proxy /api & /ws → :8000
│   └── package.json
│
├── 🧪 tests/
│   └── e2e/
│       └── test_critical_paths.py   Full E2E coverage (no real Galera needed)
│
├── 🐳 Dockerfile                Multi-stage: Node (build) → Python (runtime)
├── 🐳 docker-compose.yml
├── 📝 .env.example
├── 🚫 .gitignore
└── 📚 README.md
```

---

## 💾 Data Persistence & Backup

SQLite lives at `/data/orchestrator.db` inside the container, backed by the `orchestrator-data` named Docker volume. **Data survives container restarts and image upgrades.**

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

### Upgrade (data preserved)

```bash
git pull
docker compose build --no-cache
docker compose up -d   # volume untouched, container recreated
```

---

## 👨‍💻 Development

### Backend (hot-reload)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Vite dev server)

```bash
cd frontend
npm install
npm run dev   # :5173, proxies /api and /ws → :8000
```

Vite proxy is pre-configured in `vite.config.ts` — backend on `:8000`, frontend on `:5173`, cookies work cross-port in dev.

### Full stack via Docker

```bash
docker compose up --build
```

---

## 🧪 E2E Tests

Tests run against a live container. **No real Galera cluster required** — all checks are API-contract level.

```bash
# Install
pip install pytest httpx pytest-asyncio websockets

# Run all
E2E_BASE_URL=http://localhost:8000 \
ADMIN_USERNAME=admin \
ADMIN_PASSWORD=your-password \
pytest tests/e2e/ -v

# Run a specific group
pytest tests/e2e/ -v -k "TestAuth"
pytest tests/e2e/ -v -k "TestWebSocket"
pytest tests/e2e/ -v -k "TestRecovery"
```

### Coverage

| Group | What's tested |
|---|---|
| ✅ **Auth** | Login, logout, httpOnly cookie, wrong credentials, `/me` |
| ✅ **Clusters** | CRUD, status structure, event log pagination |
| ✅ **Nodes** | Schema, test-connection, actions, state validation |
| ✅ **Recovery** | Endpoint contracts, wizard step sequence |
| ✅ **Maintenance** | Enter/exit, rolling restart contracts |
| ✅ **Diagnostics** | Config diff, variable check, resource probe |
| ✅ **Settings** | Full CRUD: cluster / datacenter / node / arb / system |
| ✅ **Cluster Lock** | `409 Conflict` on concurrent operations |
| ✅ **WebSocket** | Auth, connection, event structure |
| ✅ **Security** | CORS headers, SPA fallback, OpenAPI schema |

---

## 🔒 Security Notes

| Concern | Mitigation |
|---|---|
| 🔑 **Admin password** | Change `ADMIN_PASSWORD` before first deploy — default is `changeme` |
| 🎫 **JWT secret** | Generate with `openssl rand -hex 32`; `.env` only, never commit |
| 🔐 **Node DB passwords** | Encrypted at rest with Fernet — changing `FERNET_SECRET_KEY` invalidates all stored passwords |
| 💻 **SSH key** | Mounted `:ro` — container cannot modify or exfiltrate it |
| 🍪 **JWT in browser** | Lives only in `httpOnly` cookie — inaccessible to JavaScript, XSS-safe |
| 🔇 **Dual secrets** | `JWT_SECRET_KEY` and `FERNET_SECRET_KEY` **must** be different values |
| ⚠️ **No mock mode** | All SSH / SQL operations are **real** — use a test cluster for experiments |
| 🌐 **CORS** | In production, SPA and API are on the same origin — CORS middleware active in dev only |

---

## 🔧 Troubleshooting

<details>
<summary>🚫 Panel unreachable after <code>docker compose up</code></summary>

```bash
docker compose logs orchestrator    # check startup errors
docker compose ps                   # verify container is running
```
</details>

<details>
<summary>🔐 <code>401 Unauthorized</code> after login</summary>

Make sure you access the panel on the **same host and port** configured in `HOST_PORT`.
`httpOnly` cookies are not sent cross-origin — accessing via IP when configured for hostname (or vice versa) will break auth.
</details>

<details>
<summary>🔴 Node immediately shows <code>OFFLINE</code></summary>

```bash
# Test SSH from the host
ssh -i ~/.ssh/id_rsa -p <ssh_port> <ssh_user>@<node_host> "hostname"

# Test DB
mysql -h <node_host> -P <db_port> -u <db_user> -p -e "SELECT 1"
```
</details>

<details>
<summary>🔐 Node DB passwords broken after config change</summary>

If you changed `FERNET_SECRET_KEY`, all encrypted passwords are now unreadable.
Go to **Settings → Nodes** and re-enter `db_password` for every affected node.
</details>

<details>
<summary>📴 WebSocket shows <code>Disconnected</code> in footer</summary>

```bash
docker compose ps    # confirm container is up

# Manual WS upgrade test
curl -i -N \
  -H "Upgrade: websocket" \
  -H "Connection: Upgrade" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/ws/clusters/1
```
</details>

<details>
<summary>🔄 Rolling Restart stuck mid-way</summary>

If a rolling restart is interrupted, the affected node stays in maintenance (`read_only = ON`).
Go to **Maintenance → Node Maintenance State** → find the node → click **Exit**.
This releases `read_only` without requiring a full restart.
</details>

<details>
<summary>⚙️ Settings changes not reflected in polling</summary>

Polling interval and SSH/DB timeouts are read from the database on every poll cycle.
No restart needed — changes take effect on the next tick (within `polling_interval_sec` seconds).
</details>

---

<div align="center">

<br/>

```
Built for ops teams who need real control, not pretty dashboards.
```

<br/>

[![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red?style=flat-square)](https://github.com/Leg1onary/galera_orchestrator_v2)
[![FastAPI](https://img.shields.io/badge/Powered%20by-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/UI-Vue%203-42b883?style=flat-square&logo=vue.js)](https://vuejs.org)
[![Docker](https://img.shields.io/badge/Ships%20as-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)

<br/>

**[⬆ Back to top](#)**

</div>
