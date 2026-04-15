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

*Real-time monitoring · Recovery wizard · Rolling restart · SSH diagnostics · Smart Advisor*  
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
                                  ├─ FastAPI REST API    /api/clusters/{id}/...
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
| 🔬 | [Diagnostics Suite](#-diagnostics-suite) |
| 🤖 | [Smart Advisor](#-smart-advisor) |
| 🔄 | [Real-time & WebSocket](#-real-time--websocket) |
| 🔃 | [Version & Updates](#-version--updates) |
| 🏗️ | [Architecture](#%EF%B8%8F-architecture) |
| 📁 | [Project Structure](#-project-structure) |
| 💾 | [Data Persistence & Backup](#-data-persistence--backup) |
| 👨‍💻 | [Development](#-development) |
| 🔒 | [Security Notes](#-security-notes) |
| 🔧 | [Troubleshooting](#-troubleshooting) |

---

## 🚀 Quick Start

### Prerequisites

| Dependency | Version |
|---|---|
| 🐳 Docker | 24+ |
| 🐳 Docker Compose | v2 plugin |
| 🐍 Python 3 | 3.8+ (for installer — bcrypt hash + Fernet key generation) |
| 🔑 SSH private key | RSA / Ed25519, passwordless, access to all Galera nodes |

---

### 🧩 Option A — One-line installer *(recommended)*

One command on your server — the script downloads everything, asks for credentials and SSH key,
generates secrets, and starts the container:

```bash
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/install.sh | bash
```

What happens inside:
1. Checks for Docker, Docker Compose, and Python 3
2. Installs `bcrypt` via pip if needed
3. Creates `~/galera-orchestrator/` directory
4. Downloads `docker-compose.ghcr.yml`
5. Interactively asks for: login, password, SSH key, port, COOKIE_SECURE
6. **Hashes password via bcrypt** — `ADMIN_PASSWORD_HASH` written to `.env`, plaintext never stored
7. **Auto-generates** `JWT_SECRET_KEY` (hex 32 bytes) and `FERNET_SECRET_KEY` (Fernet)
8. Writes `.env` with `chmod 600` and `DOCS_ENABLED=false`
9. Pulls image from GHCR and starts

After startup, the script shows:
```
  🌍 Panel:   http://<server-ip>:8000
  👤 Login:   admin
  📁 Dir:     ~/galera-orchestrator
```

> ⚠️ If you chose `COOKIE_SECURE=true` — the panel is accessible **only over HTTPS**.
> For HTTP access (dev/test), answer `n` to the COOKIE_SECURE prompt.

---

### 🔄 Update

```bash
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/update.sh | bash
```

Or if the script is already local:

```bash
bash ~/galera-orchestrator/update.sh
```

What it does:
- Reminds you to backup the DB (and shows the command)
- Asks for confirmation
- Pulls the new image from GHCR
- Restarts the container without data loss
- Updates `docker-compose.ghcr.yml` to the latest version

---

### 🐳 Option B — Docker Compose manually *(no git, Docker only)*

```bash
# 1. Download two files
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/docker-compose.ghcr.yml -o docker-compose.ghcr.yml
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/.env.example -o .env

# 2. Fill in .env (see Configuration Reference below)
nano .env

# 3. Start (image pulled automatically from GHCR)
docker compose -f docker-compose.ghcr.yml up -d
```

---

### 🛠️ Option C — Build from source *(for development)*

```bash
git clone https://github.com/Leg1onary/galera_orchestrator_v2.git
cd galera_orchestrator_v2
cp .env.example .env && nano .env
docker compose up -d
```

---

### First-run setup — add your first cluster

1. Open **Settings → Clusters** → create a cluster
2. **Settings → Datacenters** → create datacenter(s)
3. **Settings → Contours** → create contours if needed (prod / staging / etc.)
4. **Settings → Nodes** → add nodes (host, SSH port, DB credentials)
5. Select the cluster in the top bar → watch **Overview** come alive 🎉

---

## ⚙️ Configuration Reference

All configuration via `.env` file. Sensible defaults for everything except secrets.

| Variable | Default | Required | Description |
|---|---|---|---|
| `ADMIN_USERNAME` | `admin` | — | Admin login username |
| `ADMIN_PASSWORD_HASH` | — | **✅** | bcrypt hash of admin password. Auto-generated by installer. Manual: `python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpass', bcrypt.gensalt(12)).decode())"` |
| `JWT_SECRET_KEY` | — | **✅** | JWT signing secret, minimum 32 chars. Generate: `openssl rand -hex 32` |
| `FERNET_SECRET_KEY` | — | **✅** | Fernet key — encrypts node passwords in SQLite. Generate: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `SSH_KEY_PATH` | `~/.ssh/id_rsa` | **✅** | Host path to SSH key (bind-mounted `:ro` into container) |
| `DATABASE_URL` | `sqlite:////data/orchestrator.db` | — | Do not change — `/data` is mounted as a named volume |
| `HOST_PORT` | `8000` | — | Host port for the panel |
| `COOKIE_SECURE` | `true` | — | `true` — JWT cookie sent only over HTTPS (recommended). `false` — dev/test without TLS only |
| `DOCS_ENABLED` | `false` | — | `true` — enables `/docs`, `/redoc`, `/openapi.json`. **Dev only**, keep `false` in production |
| `SSH_CONNECT_TIMEOUT` | `5` | — | SSH connect timeout in seconds |
| `SSH_COMMAND_TIMEOUT` | `10` | — | SSH command timeout in seconds |
| `DB_CONNECT_TIMEOUT` | `3` | — | MariaDB connect timeout in seconds |

> ⚠️ **`JWT_SECRET_KEY` and `FERNET_SECRET_KEY` must be different values.**
> The server refuses to start if they match or contain default `change-me-*` values.

---

## 🔒 Production Security Defaults

Before deploying to production, verify:

| # | Action | How to check |
|---|---|---|
| 1 | `ADMIN_PASSWORD_HASH` is a bcrypt hash, not plaintext | `grep ADMIN_PASSWORD .env` — no `ADMIN_PASSWORD=` line |
| 2 | `JWT_SECRET_KEY` ≥ 32 chars, unique | `wc -c <<< "$JWT_SECRET_KEY"` → 65+ (with \n) |
| 3 | `FERNET_SECRET_KEY` is a valid Fernet key, different from JWT | starts with base64url prefix |
| 4 | `COOKIE_SECURE=true` | panel is behind TLS / reverse-proxy |
| 5 | `DOCS_ENABLED=false` | `/docs` → `404` |
| 6 | `.env` is `chmod 600` | `ls -la .env` → `-rw-------` |
| 7 | SSH key has no passphrase, accessible only from container | `ls -la $SSH_KEY_PATH` → `600` |

---

## 🔑 SSH Key Setup

The orchestrator uses **one global SSH key** for all node and arbitrator connections.
The key is **bind-mounted read-only** into the container — never stored in the database.

```yaml
# docker-compose.ghcr.yml (already configured)
volumes:
  - ${SSH_KEY_PATH}:/root/.ssh/id_rsa:ro
```

Test access before starting:

```bash
ssh -i ~/.ssh/id_rsa -p 22 root@<node-host> "hostname && mysql -e 'SELECT 1'"
```

Generate a new key if needed:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/galera_key
ssh-copy-id -i ~/.ssh/galera_key.pub user@node-host
```

> Key must have **no passphrase**.

---

## 🖥️ Pages & Features

### 🏠 Overview

The command center. Everything important at a glance.

- **Cluster summary bar** — status, node count, primary component health, wsrep overview
- **NodeCards** — per-node state, wsrep metrics, `read_only` flag, maintenance badge
- **Sparklines** — 30-point ring buffer for `flow_control_paused` and `recv_queue`
- **Replication lag alert** — automatic banner when `wsrep_local_recv_queue_avg > 0` on any node, with per-node detail and wsrep_slave_threads recommendation
- **Advisor widget** — critical/warn issue count from Smart Advisor, click-through to Diagnostics
- **Event log** — real-time stream of cluster events with severity badges
- **WebSocket indicator** — live connection status in the footer

### 🗊 Nodes

Full node table for day-to-day ops.

- Sort/filter by name, state, datacenter, contour
- **NodeDetailDrawer** — expand any node for full wsrep variable dump, SSH/DB latency, InnoDB status
- Per-node actions: toggle `read_only`, enter/exit maintenance, restart MariaDB, **Rejoin** (one-click re-join for offline nodes)
- **Clone node** — duplicate node config with optional credential override
- **Connection test** — on-demand SSH + DB reachability check with latency
- State badges: `SYNCED` · `JOINED` · `DONOR` · `DESYNCED` · `OFFLINE` · `DEGRADED`

### 🗺️ Topology

SVG canvas — visual representation of cluster layout.

- Nodes and arbitrators grouped by **datacenter zones**
- Connection lines with state color coding (synced / active / offline)
- Hover tooltip with full node status
- Click node → opens NodeDetailDrawer
- Real-time updates via WebSocket

### 🚑 Recovery

Step-by-step wizard for full cluster recovery when **all nodes are down**.

```
Step 1 — Scan nodes
  └─ SSH into each node, read cluster status & wsrep state
  └─ Detects non-primary / offline / joining nodes

Step 2 — Select bootstrap node
  └─ Shows seqno from grastate.dat for each node
  └─ Highlights the safe-to-bootstrap candidate
  └─ Manual override with explicit confirmation

Step 3 — Bootstrap
  └─ Runs bootstrap sequence on selected node
  └─ Monitors join progress on remaining nodes
  └─ Cluster lock held for duration (409 on concurrent ops)

Step 4 — Rejoin remaining nodes
  └─ Sequential rejoin with per-node progress tracking
  └─ SST/IST detection, stuck SST alert
```

### 🔄 Maintenance

- **Rolling Restart** — restarts nodes one-by-one, waiting for SYNCED state before proceeding
- **Desync / Resync** — toggle `wsrep_desync ON/OFF` without restart (for safe DDL/dumps)
- **Node maintenance state** — toggle `read_only` cluster-wide or per-node
- **Purge binary logs** — one-click `PURGE BINARY LOGS BEFORE ...` per node
- **Flush operations** — `FLUSH LOGS`, `FLUSH TABLES WITH READ LOCK / UNLOCK TABLES`
- **SST status panel** — detect stuck SST donor/joiner, one-click restart-SST
- All destructive ops require explicit confirmation dialog
- Cluster-level lock prevents concurrent recovery + maintenance

### ⚙️ Settings

- **Clusters** — CRUD, polling interval per cluster
- **Datacenters** — logical groupings for Topology view
- **Contours** — environment tags (prod / staging / etc.)
- **Nodes** — SSH + DB credentials per node (passwords encrypted at rest via Fernet)
- **Arbitrators** — garbd nodes with SSH connectivity monitoring
- **System** — SSH/DB timeouts, global settings

---

## 🔬 Diagnostics Suite

Full diagnostics panel accessible from the **Diagnostics** page, organized in tabs.

### Connection Check
- SSH reachability + latency for every node and arbitrator
- MariaDB reachability + latency
- Galera wsrep status validation
- Color-coded pass / warn / fail per node

### Config Diff
- Side-by-side comparison of key `SHOW GLOBAL VARIABLES` across all nodes
- Highlights diverging values (e.g. different `wsrep_slave_threads` or `max_connections`)
- Filter by variable name

### Variables
- Full `SHOW GLOBAL VARIABLES` dump per node
- Quick search / filter
- Export to CSV

### System Resources
- CPU, RAM, disk usage per node via SSH
- Progress bars with warn (80%) / critical (90%) thresholds
- **Disk Details** panel — top-10 tables by size (`information_schema.TABLES`), binary log sizes (`SHOW BINARY LOGS`), `ibdata1` size via SSH
- Adaptive status dots (ok / warn / critical)

### Process List
- Live `information_schema.PROCESSLIST` per node
- **Kill process** — per-PID kill with confirm dialog
- **Kill ALL** — bulk-kill by state (Sleep, Lock wait, etc.) or by user
- Auto-refresh with configurable interval

### Active Transactions
- `information_schema.INNODB_TRX` — transactions older than N seconds
- Columns: TRX ID, started, age, state, thread ID, query snippet, tables/rows locked
- Per-node grouping

### InnoDB Status
- `SHOW ENGINE INNODB STATUS` raw output with syntax highlighting
- **Deadlock parser** — structured card view of `LATEST DETECTED DEADLOCK`:
  - Transaction A vs B side-by-side
  - Victim badge, lock type / mode, tables, query snippets
  - Falls back to raw `pre` if parsing fails
- Copy to clipboard

### Config Health Check
- Automated best-practice rules against `SHOW GLOBAL VARIABLES`:

| Rule | Check | Severity |
|---|---|---|
| `innodb_buffer_pool_size` | Must be 60–70% of RAM | warn / error |
| `max_connections` | > 1000 risks OOM | warn / error |
| `wsrep_slave_threads` | Should match CPU core count | warn / error |
| `innodb_flush_log_at_trx_commit` | Must be 1 for durability | warn |
| `wsrep_sync_wait` | Info if disabled (stale reads risk) | info |

### Error Log
- Tail of MariaDB error log via SSH
- Color-coded lines: ERROR / WARNING / NOTE
- Auto-scroll with pause-on-hover

### Slow Query Log
- Live slow query list from `information_schema` / slow query log
- **Enable / Disable** slow query log per node at runtime (`SET GLOBAL slow_query_log`)
- Columns: query time, db, user, query text

### Arbitrator Log
- Tail of garbd log via SSH
- Color-coded severity lines

### Flush Panel
- `FLUSH LOGS` — rotate binary/error logs
- `FLUSH TABLES WITH READ LOCK` + `UNLOCK TABLES` with safety confirmation

### Purge Binary Logs
- Select cutoff date or log file name
- Preview size to be freed
- Executes `PURGE BINARY LOGS BEFORE ...`

---

## 🤖 Smart Advisor

`GET /api/clusters/{cluster_id}/advisor`

The Advisor aggregates data from all diagnostics sources and returns a prioritized list of actionable recommendations. Visible as:
- Full panel in **Diagnostics → Advisor** tab
- Summary widget on **Overview** dashboard

### Advisor Categories

| Category | Source | Example finding |
|---|---|---|
| `config` | Config Health Check | InnoDB buffer pool underprovisioned (25% of RAM, recommended 60–70%) |
| `performance` | Config Health, Replication lag | `wsrep_slave_threads` mismatch vs CPU cores — causing replication lag |
| `replication` | Live node state | `wsrep_local_recv_queue_avg > 0` — replication lagging on 2 nodes |
| `availability` | SST status | Node stuck in JOINING state for > 5 min — SST restart recommended |
| `storage` | Disk usage | Disk usage at 87% on node-2 — top tables: `db.orders` 4.2 GB |
| `locking` | Active transactions | 3 transactions running > 5 min, oldest 14 min — review and consider KILL |
| `locking` | InnoDB status | Recent deadlock detected — victim query and tables identified |
| `security` | Config | `innodb_flush_log_at_trx_commit ≠ 1` — durability risk in production |

### Severity Levels

| Level | Color | When |
|---|---|---|
| `critical` | 🔴 | Immediate action required (stuck SST, split-brain risk, disk > 90%) |
| `warn` | 🟡 | Degraded performance or configuration risk |
| `info` | 🔵 | Suboptimal configuration, low-priority recommendations |

### Recommended Actions

Each advisor card carries an `action` that maps to a direct UI interaction:

- `open_panel` — jump to the relevant diagnostics tab
- `node_action` — pre-fills a node action (restart SST, rejoin)
- `config_change` — links to the variable with documentation
- `recovery_action` — opens Recovery wizard

---

## 🔄 Real-time & WebSocket

```
WS /ws/clusters/{cluster_id}
```

- One WebSocket per cluster per browser tab
- Auth via `httpOnly` JWT cookie — same cookie as REST API
- Emits events: `node_state`, `cluster_state`, `event_log`, `operation_progress`
- Frontend reconnects automatically with exponential backoff
- Connection status indicator in the SPA footer

**Polling fallback:** If WebSocket is unavailable, the frontend falls back to HTTP polling every 5s.

---

## 🔃 Version & Updates

### How version is determined

The app version is **not set manually in `.env`** — it is determined automatically at container startup:

| Source | When used |
|---|---|
| `git rev-parse --short HEAD` | Build from source (Option C) — shows short commit SHA |
| `APP_VERSION` env (set by `Dockerfile`) | Image built via CI/CD — SHA passed as `ARG GIT_SHA` at build time |
| `unknown` | Fallback if git and env are unavailable |

The current version is always visible in the **bottom-left footer** in `abc1234` format.

### Check for updates

Next to the version in the footer is a **🔃** button (Check updates).
It performs a check **on demand** — no automatic background requests
(important for air-gapped networks).

| Status | Meaning |
|---|---|
| `↑ new version available` | Running image digest differs from `:latest` in registry |
| `✓ up to date` | Image is current |
| `⚠ registry unavailable` | Registry unreachable (air-gapped network, no Docker CLI, timeout) |

> Check uses `docker manifest inspect ghcr.io/leg1onary/galera_orchestrator_v2:latest`
> without pulling the image. Requires access to `ghcr.io` from the host.

### How to update

```bash
# If you used install.sh
bash ~/galera-orchestrator/update.sh

# Manual
docker compose -f ~/galera-orchestrator/docker-compose.ghcr.yml pull
docker compose -f ~/galera-orchestrator/docker-compose.ghcr.yml up -d
```

> ⚠️ Back up the database before updating — see [Data Persistence & Backup](#-data-persistence--backup).

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────┐
│           Docker Container                 │
│                                            │
│  ┌─────────────┐    ┌──────────────────┐   │
│  │  Vue 3 SPA  │    │   FastAPI App    │   │
│  │  (static)   │◄───│                  │   │
│  └─────────────┘    │  /api/clusters/  │   │
│                     │  /ws/clusters/   │   │
│                     │                  │   │
│                     │  Background      │   │
│                     │  Poller (asyncio)│   │
│                     └──────┬───────────┘   │
│                            │               │
│                     ┌──────▼───────────┐   │
│                     │   SQLite /data   │   │
│                     └──────────────────┘   │
│                                            │
│  /root/.ssh/id_rsa  (bind :ro)             │
└────────────────────────────────────────────┘
         │ SSH + MariaDB
         ▼
   Galera Nodes
```

**Stack:**

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.110+, SQLAlchemy 2.0 (async), Pydantic v2 |
| SSH | paramiko |
| DB driver | PyMySQL |
| Auth | python-jose (JWT RS256), bcrypt, cryptography (Fernet) |
| Frontend | Vue 3, Vite 5, Pinia, Vue Router, TanStack Vue Query, TypeScript |
| UI | PrimeVue 4, custom dark-only design system |
| DB | SQLite (single file, named Docker volume) |
| Auth flow | JWT in `httpOnly` cookie, validated via `GET /api/auth/me` |
| Realtime | WebSocket `/ws/clusters/{cluster_id}` + 5s polling fallback |

---

## 📁 Project Structure

```
galera_orchestrator_v2/
├── backend/
│   ├── main.py                # FastAPI app, middleware, lifespan
│   ├── auth.py                # JWT + bcrypt login, cookie management
│   ├── models.py              # SQLAlchemy models (clusters, nodes, etc.)
│   ├── schemas.py             # Pydantic schemas
│   ├── poller.py              # Background polling loop (asyncio, per cluster)
│   ├── services/
│   │   ├── ssh_client.py      # paramiko wrapper (SSHClient)
│   │   └── db_client.py       # PyMySQL wrapper (DBClient)
│   └── routers/
│       ├── auth.py            # /api/auth/login, /api/auth/me, /api/auth/logout
│       ├── clusters.py        # /api/clusters CRUD
│       ├── nodes.py           # nodes, node actions, rejoin, desync/resync, flush, purge
│       ├── recovery.py        # recovery wizard (bootstrap, rejoin, cancel)
│       ├── maintenance.py     # rolling restart, maintenance state
│       ├── diagnostics.py     # all diagnostics endpoints (15+ panels)
│       ├── advisor.py         # Smart Advisor GET /api/clusters/{id}/advisor
│       ├── ws.py              # WebSocket /ws/clusters/{id}
│       ├── settings.py        # global settings
│       ├── contours.py        # contour CRUD
│       └── version.py         # /api/version, update check
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── OverviewPage.vue
│   │   │   ├── NodesPage.vue
│   │   │   ├── TopologyPage.vue
│   │   │   ├── DiagnosticsPage.vue
│   │   │   ├── RecoveryPage.vue
│   │   │   ├── MaintenancePage.vue
│   │   │   ├── SettingsPage.vue
│   │   │   ├── DocsPage.vue
│   │   │   └── LoginPage.vue
│   │   ├── components/
│   │   │   ├── overview/      # NodeCard, Sparkline, EventLog, AdvisorWidget, ReplicationLagAlert
│   │   │   ├── nodes/         # NodeTable, NodeDetailDrawer, NodeStatusBadge, StatRow
│   │   │   └── diagnostics/   # 15+ panel components (AdvisorPanel, ProcessListPanel, etc.)
│   │   ├── stores/            # Pinia — cluster, nodes, ws, version, maintenance, recovery
│   │   ├── api/               # Typed API clients (nodes.ts, diagnostics.ts, advisor.ts, ...)
│   │   ├── composables/       # useClusterStatus, usePoller, etc.
│   │   └── assets/main.css    # Global design tokens + dark theme
│   └── vite.config.ts
├── Dockerfile
├── docker-compose.yml          # Dev (build from source)
├── docker-compose.ghcr.yml     # Prod (pull from GHCR)
├── .env.example
├── install.sh
└── update.sh
```

---

## 💾 Data Persistence & Backup

All persistent data lives in a single SQLite file inside a named Docker volume:

```bash
# Backup
docker exec galera-orchestrator sqlite3 /data/orchestrator.db ".backup /data/backup.db"
docker cp galera-orchestrator:/data/backup.db ./orchestrator-backup-$(date +%Y%m%d).db

# Restore
docker cp ./orchestrator-backup-YYYYMMDD.db galera-orchestrator:/data/orchestrator.db
docker compose restart orchestrator
```

> ⚠️ After changing `FERNET_SECRET_KEY`, all encrypted node passwords become unreadable.
> Always back up before rotating keys.

---

## 👨‍💻 Development

```bash
git clone https://github.com/Leg1onary/galera_orchestrator_v2.git
cd galera_orchestrator_v2
cp .env.example .env

# In .env for dev:
#   COOKIE_SECURE=false
#   DOCS_ENABLED=true
#   ADMIN_PASSWORD_HASH=<bcrypt-hash>

docker compose up -d
# Frontend: http://localhost:5173  (Vite dev server, HMR)
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs  (only if DOCS_ENABLED=true)
```

Generate a bcrypt hash for dev `.env`:
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'admin', bcrypt.gensalt(12)).decode())"
```

---

## 🔒 Security Notes

| Concern | Mitigation |
|---|---|
| 🔑 **Admin password** | Stored as `bcrypt` hash (`ADMIN_PASSWORD_HASH`). Plaintext never written to `.env`. |
| 🎫 **JWT secret** | Minimum 32 chars. Generate: `openssl rand -hex 32`. Server refuses to start with default value. |
| 🔐 **Node DB passwords** | Encrypted in SQLite via Fernet. Changing `FERNET_SECRET_KEY` invalidates all passwords. |
| 💻 **SSH key** | Mounted `:ro` — container cannot modify or exfiltrate the key. |
| 🍪 **JWT in browser** | `httpOnly` cookie only — inaccessible to JavaScript, XSS-safe. |
| 🔇 **Dual secrets** | `JWT_SECRET_KEY` and `FERNET_SECRET_KEY` **must** be different values. |
| 🌐 **Security headers** | Every response includes: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`. |
| 📄 **OpenAPI schema** | `/docs`, `/redoc`, `/openapi.json` disabled by default (`DOCS_ENABLED=false`). |
| 🔒 **Secure cookie** | `COOKIE_SECURE=true` by default — cookie not sent over HTTP. |
| ⚠️ **No mock mode** | All SSH / SQL operations are **real** — use a test cluster for experiments. |
| 🌐 **CORS** | In production, SPA and API are on the same origin — CORS middleware active in dev only. |

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

Make sure you access the panel on the **same host and port** as `HOST_PORT`.
`httpOnly` cookies are not sent cross-origin.

Also ensure `COOKIE_SECURE=false` if accessing over plain HTTP (no TLS).
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

If you changed `FERNET_SECRET_KEY`, all encrypted passwords are unreadable.
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

If interrupted, the affected node stays in maintenance (`read_only = ON`).
Go to **Maintenance → Node Maintenance State** → find the node → click **Exit**.
This releases `read_only` without requiring a full restart.
</details>

<details>
<summary>⚙️ Settings changes not reflected immediately</summary>

Polling interval and SSH/DB timeouts are read from the database on every poll cycle.
No restart needed — changes take effect on the next tick (within `polling_interval_sec` seconds).
</details>

<details>
<summary>🔑 How to change the admin password</summary>

```bash
# Generate new bcrypt hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'newpassword', bcrypt.gensalt(12)).decode())"

# Update .env
sed -i "s|^ADMIN_PASSWORD_HASH=.*|ADMIN_PASSWORD_HASH=<new_hash>|" ~/galera-orchestrator/.env

# Restart container
docker compose -f ~/galera-orchestrator/docker-compose.ghcr.yml restart
```
</details>

<details>
<summary>🔃 "Check updates" shows "registry unavailable"</summary>

Possible reasons:
- Server has no internet access (air-gapped network) — expected behavior
- `ghcr.io` is blocked by firewall

To update in an air-gapped network, use `update.sh` from the host:
```bash
bash ~/galera-orchestrator/update.sh
```
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
