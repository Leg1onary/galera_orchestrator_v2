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
| 🔃 | [Version & Updates](#-version--updates) |
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
| 🐍 Python 3 | 3.8+ (для installer — генерация Fernet-ключа и bcrypt-хэша) |
| 🔑 SSH private key | RSA / Ed25519, passwordless, access to all Galera nodes |

---

### 🧩 Option A — One-line installer *(recommended)*

Одна команда на сервере — скрипт сам скачает файлы, спросит пароль и SSH-ключ,
сгенерирует секреты и запустит контейнер:

```bash
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/install.sh | bash
```

Что происходит внутри:
1. Проверяет наличие Docker, Docker Compose и Python 3
2. Устанавливает `bcrypt` через pip (если не установлен)
3. Создаёт папку `~/galera-orchestrator`
4. Скачивает `docker-compose.ghcr.yml`
5. Интерактивно спрашивает: логин, пароль, SSH-ключ, порт, COOKIE_SECURE
6. **Хэширует пароль через bcrypt** — в `.env` пишется `ADMIN_PASSWORD_HASH`, plaintext не сохраняется
7. **Автоматически генерирует** `JWT_SECRET_KEY` (hex 32 байта) и `FERNET_SECRET_KEY` (Fernet)
8. Пишет `.env` с `chmod 600` и `DOCS_ENABLED=false`
9. Тянет образ с GHCR и запускает

После запуска скрипт покажет:
```
  🌍 Panel:   http://<server-ip>:8000
  👤 Login:   admin
  📁 Dir:     ~/galera-orchestrator
```

> ⚠️ Если выбрал `COOKIE_SECURE=true` — панель доступна **только через HTTPS**.
> Для HTTP-доступа (dev/тест) ответь `n` на вопрос о COOKIE_SECURE.

---

### 🔄 Обновление

```bash
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/update.sh | bash
```

Или если скрипт уже скачан локально:

```bash
bash ~/galera-orchestrator/update.sh
```

Что делает:
- Напоминает про бэкап БД (и показывает команду)
- Спрашивает подтверждение
- Тянет новый образ с GHCR
- Перезапускает контейнер без downtime данных
- Обновляет `docker-compose.ghcr.yml` до актуальной версии

---

### 🐳 Option B — Docker Compose вручную *(без git, только Docker)*

```bash
# 1. Скачать два файла
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/docker-compose.ghcr.yml -o docker-compose.ghcr.yml
curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/.env.example -o .env

# 2. Заполнить .env (см. Configuration Reference ниже)
nano .env

# 3. Запустить (образ скачается автоматически с GHCR)
docker compose -f docker-compose.ghcr.yml up -d
```

---

### 🛠️ Option C — Собрать из исходников *(для разработки)*

```bash
git clone https://github.com/Leg1onary/galera_orchestrator_v2.git
cd galera_orchestrator_v2
cp .env.example .env && nano .env
docker compose up -d
```

---

### После запуска — добавить первый кластер

1. Открой **Settings → Clusters** → создай кластер
2. **Settings → Datacenters** → создай датацентр(ы)
3. **Settings → Contours** → создай контуры (если нужно)
4. **Settings → Nodes** → добавь узлы (host, SSH-порт, DB-credentials)
5. Выбери кластер в топбаре → наблюдай как **Overview** оживает 🎉

---

## ⚙️ Configuration Reference

All configuration via `.env` file. Sensible defaults for everything except secrets.

| Variable | Default | Required | Description |
|---|---|---|---|
| `ADMIN_USERNAME` | `admin` | — | Admin login username |
| `ADMIN_PASSWORD_HASH` | — | **✅ обязательно** | bcrypt-хэш пароля. Генерируется installer'ом автоматически. Вручную: `python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpass', bcrypt.gensalt(12)).decode())"` |
| `JWT_SECRET_KEY` | — | **✅ обязательно** | JWT signing secret, минимум 32 символа. Генерировать: `openssl rand -hex 32` |
| `FERNET_SECRET_KEY` | — | **✅ обязательно** | Fernet key — шифрует пароли узлов в SQLite. Генерировать: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `SSH_KEY_PATH` | `~/.ssh/id_rsa` | **✅** | Host path к SSH-ключу (bind-mounted `:ro` в контейнер) |
| `DATABASE_URL` | `sqlite:////data/orchestrator.db` | — | Не менять — `/data` монтируется как named volume |
| `HOST_PORT` | `8000` | — | Host port для панели |
| `COOKIE_SECURE` | `true` | — | `true` — JWT-cookie отправляется только по HTTPS (recommended). `false` — только для dev/тест без TLS |
| `DOCS_ENABLED` | `false` | — | `true` — включает `/docs`, `/redoc`, `/openapi.json`. **Только для dev**, в проде держать `false` |
| `SSH_CONNECT_TIMEOUT` | `5` | — | SSH connect timeout, секунды |
| `SSH_COMMAND_TIMEOUT` | `10` | — | SSH command timeout, секунды |
| `DB_CONNECT_TIMEOUT` | `3` | — | MariaDB connect timeout, секунды |

> ⚠️ **`JWT_SECRET_KEY` и `FERNET_SECRET_KEY` должны быть разными значениями.**
> Сервер откажется стартовать если они совпадают или содержат дефолтные `change-me-*` значения.

---

## 🔒 Production Security Defaults

При деплое на прод убедись что выполнено:

| # | Что сделать | Как проверить |
|---|---|---|
| 1 | `ADMIN_PASSWORD_HASH` — bcrypt-хэш, не plaintext | `grep ADMIN_PASSWORD .env` — не должно быть `ADMIN_PASSWORD=` |
| 2 | `JWT_SECRET_KEY` ≥ 32 символов, уникальный | `wc -c <<< "$JWT_SECRET_KEY"` → 65+ (с \n) |
| 3 | `FERNET_SECRET_KEY` — валидный Fernet-ключ, отличается от JWT | начинается с `gASV` или аналогичного base64url |
| 4 | `COOKIE_SECURE=true` | панель за TLS/reverse-proxy |
| 5 | `DOCS_ENABLED=false` | `/docs` → `404` |
| 6 | `.env` — `chmod 600` | `ls -la .env` → `-rw-------` |
| 7 | SSH-ключ без passphrase, доступен только из контейнера | `ls -la $SSH_KEY_PATH` → `600` |

---

## 🔑 SSH Key Setup

The orchestrator uses **one global SSH key** for all node/arbitrator connections.
The key is **bind-mounted read-only** into the container — never stored in the database.

```yaml
# docker-compose.ghcr.yml (already configured)
volumes:
  - ${SSH_KEY_PATH}:/home/nonroot/.ssh/id_rsa:ro
```

✅ Проверь доступ перед запуском:

```bash
ssh -i ~/.ssh/id_rsa -p 22 root@<node-host> "hostname && mysql -e 'SELECT 1'"
```

Если ключа нет — создай:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/galera_key
ssh-copy-id -i ~/.ssh/galera_key.pub user@node-host
```

> Ключ должен быть **без passphrase**.

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

Step 3 — Bootstrap
  └─ Runs bootstrap sequence on selected node
  └─ Monitors join progress on remaining nodes
  └─ Cluster lock held for duration (409 on concurrent ops)
```

### 🔄 Maintenance

- **Rolling Restart** — restarts nodes one-by-one, waiting for sync before proceeding
- **Node Maintenance State** — toggle `read_only` without restart
- All destructive ops require explicit confirmation
- Cluster-level lock prevents concurrent recovery + maintenance

### ⚙️ Settings

- **Clusters** — CRUD, polling interval per cluster
- **Datacenters** — logical groupings for Topology view
- **Contours** — environment tags (prod/staging/etc.)
- **Nodes** — SSH + DB credentials per node (passwords encrypted at rest via Fernet)
- **Global settings** — SSH/DB timeouts

---

## 🔄 Real-time & WebSocket

```
WS /ws/clusters/{cluster_id}
```

- One WebSocket per cluster, per browser tab
- Auth via `httpOnly` JWT cookie — same cookie as REST API
- Emits events: `node_state`, `cluster_state`, `event_log`, `operation_progress`
- Frontend reconnects automatically with exponential backoff
- Connection status indicator in the SPA footer

---

## 🔃 Version & Updates

### Как определяется версия

Версия приложения **не задаётся вручную в `.env`** — она определяется автоматически при старте контейнера:

| Источник | Когда используется |
|---|---|
| `git rev-parse --short HEAD` | Сборка из исходников (`Option C`) — показывает короткий SHA коммита |
| `APP_VERSION` (env, задаётся `Dockerfile`) | Образ собран через CI/CD — SHA коммита передаётся как `ARG GIT_SHA` при сборке |
| `unknown` | Fallback, если git и env недоступны |

Текущая версия всегда видна в **левом нижнем углу** футера панели в формате `abc1234`.

### Проверка наличия обновлений

Рядом с версией в футере находится кнопка **🔃** (Check updates).
Она выполняет проверку **вручную по запросу** — автоматических фоновых запросов нет
(важно для изолированных сетей).

После нажатия рядом с кнопкой появляется один из трёх статусов:

| Статус | Значение |
|---|---|
| `↑ new version available` | Digest запущенного образа отличается от `:latest` в реестре — доступно обновление |
| `✓ up to date` | Образ актуален |
| `⚠ registry unavailable` | Реестр недоступен (изолированная сеть, нет `docker` CLI, timeout) |

> Проверка использует `docker manifest inspect ghcr.io/leg1onary/galera_orchestrator_v2:latest`
> без скачивания образа. Требует доступа к `ghcr.io` с хоста, где запущен контейнер.

### Как обновить

```bash
# Если использовал install.sh
bash ~/galera-orchestrator/update.sh

# Вручную
docker compose -f ~/galera-orchestrator/docker-compose.ghcr.yml pull
docker compose -f ~/galera-orchestrator/docker-compose.ghcr.yml up -d
```

> ⚠️ Перед обновлением сделай бэкап БД — см. [Data Persistence & Backup](#-data-persistence--backup).

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────┐
│           Docker Container                 │
│                                            │
│  ┌─────────────┐    ┌──────────────────┐   │
│  │  Vue 3 SPA  │    │   FastAPI App    │   │
│  │  (static)   │◄───│                  │   │
│  └─────────────┘    │  /api/...        │   │
│                     │  /ws/...         │   │
│                     │                  │   │
│                     │  Background      │   │
│                     │  Poller (asyncio)│   │
│                     └──────┬───────────┘   │
│                            │               │
│                     ┌──────▼───────────┐   │
│                     │   SQLite /data   │   │
│                     └──────────────────┘   │
│                                            │
│  /home/nonroot/.ssh/id_rsa  (bind :ro)     │
└────────────────────────────────────────────┘
         │ SSH + MariaDB
         ▼
   Galera Nodes
```

**Stack:**
- **Backend:** FastAPI 0.110+, SQLAlchemy 2.0 (async), Pydantic v2, paramiko, python-jose, bcrypt, cryptography (Fernet)
- **Frontend:** Vue 3, Vite 5, Pinia, Vue Router, TypeScript
- **DB:** SQLite (single file, named Docker volume)
- **Auth:** JWT в `httpOnly` cookie, проверка через `GET /api/auth/me`
- **Realtime:** WebSocket `/ws/clusters/{cluster_id}` + 5s polling fallback
- **Process:** runs as `nonroot` (uid 1001) — no root inside container

---

## 📁 Project Structure

```
galera_orchestrator_v2/
├── backend/
│   ├── main.py              # FastAPI app, middleware, routes
│   ├── auth.py              # JWT + bcrypt login, cookie management
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── ssh_client.py        # paramiko wrapper
│   ├── galera_client.py     # MariaDB/wsrep queries
│   ├── poller.py            # Background polling loop
│   ├── operations/          # Recovery, rolling restart, maintenance
│   └── config.py            # Settings from .env
├── frontend/
│   ├── src/
│   │   ├── pages/           # Overview, Nodes, Topology, Recovery, Settings
│   │   ├── components/      # NodeCard, Sparkline, Drawer, etc.
│   │   ├── stores/          # Pinia — clusters, nodes, ws, version
│   │   └── api/             # Axios client
│   └── vite.config.ts
├── Dockerfile
├── docker-compose.yml        # Dev (build from source)
├── docker-compose.ghcr.yml   # Prod (pull from GHCR)
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

> ⚠️ После смены `FERNET_SECRET_KEY` все зашифрованные пароли узлов станут нечитаемыми.
> Всегда делай бэкап перед ротацией ключей.

---

## 👨‍💻 Development

```bash
git clone https://github.com/Leg1onary/galera_orchestrator_v2.git
cd galera_orchestrator_v2
cp .env.example .env

# В .env для dev:
#   COOKIE_SECURE=false
#   DOCS_ENABLED=true
#   ADMIN_PASSWORD_HASH=<bcrypt-хэш>

docker compose up -d
# Frontend: http://localhost:5173  (Vite dev server, HMR)
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs  (только если DOCS_ENABLED=true)
```

Генерация bcrypt-хэша для dev `.env`:
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'admin', bcrypt.gensalt(12)).decode())"
```

---

## 🧪 E2E Tests

```bash
# Запуск всех тестов
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Только backend unit-тесты
docker compose exec backend pytest tests/ -v
```

---

## 🔒 Security Notes

| Concern | Mitigation |
|---|---|
| 🔑 **Admin password** | Хранится как `bcrypt` хэш (`ADMIN_PASSWORD_HASH`). Plaintext в `.env` никогда не записывается. |
| 🎫 **JWT secret** | Минимум 32 символа. Генерировать: `openssl rand -hex 32`. Сервер не стартует с дефолтным значением. |
| 🔐 **Node DB passwords** | Зашифрованы в SQLite через Fernet. Смена `FERNET_SECRET_KEY` инвалидирует все пароли. |
| 💻 **SSH key** | Монтируется `:ro` — контейнер не может изменить или украсть ключ. |
| 🍪 **JWT в браузере** | Только в `httpOnly` cookie — недоступен JavaScript, защита от XSS. |
| 🔇 **Dual secrets** | `JWT_SECRET_KEY` и `FERNET_SECRET_KEY` **обязаны** быть разными значениями. |
| 🌐 **Security headers** | Каждый ответ содержит: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`. |
| 📄 **OpenAPI schema** | `/docs`, `/redoc`, `/openapi.json` отключены по умолчанию (`DOCS_ENABLED=false`). |
| 🔒 **Secure cookie** | `COOKIE_SECURE=true` по умолчанию — cookie не отправляется по HTTP. |
| 👤 **Non-root process** | Контейнер запускается от `nonroot` (uid 1001) — компрометация процесса не даёт root на хосте. |
| ⚠️ **No mock mode** | Все SSH / SQL операции **реальные** — используй тестовый кластер для экспериментов. |
| 🌐 **CORS** | В проде SPA и API на одном origin — CORS middleware активен только в dev. |

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

Также убедись что `COOKIE_SECURE=false` если доступаешься по HTTP (без TLS).
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

<details>
<summary>🔑 Как сменить пароль admin</summary>

```bash
# Генерируй новый bcrypt-хэш
python3 -c "import bcrypt; print(bcrypt.hashpw(b'newpassword', bcrypt.gensalt(12)).decode())"

# Обнови в .env
sed -i "s|^ADMIN_PASSWORD_HASH=.*|ADMIN_PASSWORD_HASH=<новый_хэш>|" ~/galera-orchestrator/.env

# Перезапусти контейнер
docker compose -f ~/galera-orchestrator/docker-compose.ghcr.yml restart
```
</details>

<details>
<summary>🔃 Кнопка «Check updates» показывает «registry unavailable»</summary>

Возможные причины:
- Сервер без доступа в интернет (изолированная сеть) — это ожидаемое поведение
- Docker CLI недоступен внутри контейнера — проверь что `docker.sock` не нужен (по умолчанию не монтируется)
- `ghcr.io` заблокирован файрволом

Для обновления в изолированной сети используй `update.sh` с хоста:
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
