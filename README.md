<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="80" height="80">
  <circle cx="60" cy="60" r="58" stroke="#3b82f6" stroke-width="4" fill="none"/>
  <circle cx="30" cy="60" r="14" fill="#22c55e"/>
  <circle cx="90" cy="60" r="14" fill="#22c55e"/>
  <circle cx="60" cy="28" r="14" fill="#3b82f6"/>
  <line x1="44" y1="60" x2="76" y2="60" stroke="#3b82f6" stroke-width="3"/>
  <line x1="60" y1="28" x2="30" y2="60" stroke="#3b82f6" stroke-width="3"/>
  <line x1="60" y1="28" x2="90" y2="60" stroke="#3b82f6" stroke-width="3"/>
</svg>

# Galera Orchestrator v2

**Современный веб-интерфейс мониторинга и управления MariaDB Galera Cluster**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue.js](https://img.shields.io/badge/Vue-3.4-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![PrimeVue](https://img.shields.io/badge/PrimeVue-3.53-00C0EF)](https://primevue.org)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![Pinia](https://img.shields.io/badge/Pinia-2.1-FFD859)](https://pinia.vuejs.org)
[![MariaDB](https://img.shields.io/badge/MariaDB-Galera-003545?logo=mariadb&logoColor=white)](https://mariadb.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/Leg1onary/galera_orchestrator_v2/actions)

[**Что нового в v2**](#-что-нового-в-v2) ·
[**Быстрый старт**](#-быстрый-старт) ·
[**Функционал**](#-функционал) ·
[**Архитектура**](#-архитектура) ·
[**Конфигурация**](#-конфигурация) ·
[**Разработка**](#-разработка)

</div>

---

## ✨ Что нового в v2

Полный рефакторинг исходного проекта с монолитного `index.html` (8 000 строк Vanilla JS) на современный продуктовый стек:

| | v1 | v2 |
|---|---|---|
| Frontend | Vanilla JS / single HTML | **Vue 3 + PrimeVue + Pinia + Vite** |
| Сборка | Нет | **Vite** — tree-shaking, code splitting |
| State management | Глобальные переменные | **Pinia stores** |
| Роутинг | Ручное показывание `div` | **Vue Router** с lazy-loading |
| Компоненты | Кастомный CSS | **PrimeVue** component library |
| Авторизация | Выключена по умолчанию | **Включена по умолчанию** (`admin` / `admin`) |
| Деплой | Shell-скрипты | **Docker + docker-compose** |
| CI/CD | Нет | **GitHub Actions** (lint + build + smoke-test) |
| Topology | Static SVG | **Динамический SVG** с DC-сегментами |

---

## 🚀 Быстрый старт

### Требования

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2+

### 1. Клонировать и запустить

```bash
git clone https://github.com/Leg1onary/galera_orchestrator_v2.git
cd galera_orchestrator_v2

docker compose up -d
```

Открыть в браузере: **`http://<IP>:8000`**

Логин по умолчанию: **`admin`** / **`admin`**

> ⚠️ Смените пароль в `config/nodes.yaml` перед вводом в production.

---

### 2. Заполнить конфигурацию

При первом запуске `config/nodes.yaml` создаётся автоматически из шаблона.  
Откройте файл и пропишите реальные ноды:

```bash
nano config/nodes.yaml
```

После изменения конфига — горячая перезагрузка без рестарта контейнера:

```bash
curl -X POST http://localhost:8000/api/config/reload \
  -H "Authorization: Bearer <your-token>"
```

---

### 3. Переключиться в REAL-режим

По умолчанию запускается в **MOCK-режиме** (безопасная демонстрация без подключений к серверам).  
Переключить в REAL можно прямо из header интерфейса — кнопка **MOCK / REAL**.

---

## 📋 Функционал

### 🏠 Обзор

| KPI | Источник | Норма |
|---|---|---|
| Cluster Status | `wsrep_cluster_status` | Primary |
| Cluster Size | `wsrep_cluster_size` | ≥ 3 |
| Synced Nodes | `wsrep_local_state_comment == Synced` | Все ноды |
| Flow Control | `wsrep_flow_control_paused` | < 0.05 |
| Cert Failures | Σ `wsrep_local_cert_failures` | 0 |
| Max Δ seqno | Разница `wsrep_last_committed` | 0 |
| BF Aborts | Σ `wsrep_bf_aborts` | ≈ 0 |

- Карточки нод со **спарклайнами** Flow Control и Recv Queue (50 тиков)
- Карточки арбитров: статус RUNNING / OFFLINE, members в кворуме
- **Mock-сценарии**: normal / gc01 down / gc02 down / flow control / SST in progress

### 🖥 Ноды

- Полные метрики на каждой карточке
- Кнопки управления: **Start / Stop / Restart / Rejoin**
- Переключатели **R/O** / **R/W**
- SSH **Ping** (systemctl is-active mariadb)
- **Поиск и фильтрация** по имени, IP, DC, состоянию
- **Браузерные уведомления** (non-Primary, Flow Control > 0.1, OFFLINE)

### 🗺 Топология

- **Динамический SVG-граф** — ноды, арбитры, DC-сегменты, соединения
- Цветовая индикация: Synced (зелёный), Donor (жёлтый), Joining (синий), Offline (красный)
- **Таблица сравнения 16 wsrep-переменных** — расхождения подсвечиваются красным
- Автоопределение Split-Brain по `wsrep_cluster_state_uuid`
- Tooltips с описанием каждой переменной на русском

### 🔄 Recovery

- **Bootstrap Wizard** — автовыбор ноды с максимальным seqno, пошаговое восстановление
- Просмотр seqno / `grastate.dat` по всем нодам параллельно
- Сброс `safe_to_bootstrap`
- `pc-bootstrap` (SET GLOBAL wsrep_provider_options)
- Полная симуляция в mock-режиме без SSH/DB вызовов

### 🔧 Обслуживание

**Maintenance Wizard** — 7-шаговый безопасный процесс обслуживания ноды:

```
R/O ON → Дренаж (recv_queue=0) → Stop → Работы → Start → Synced → R/W ON
```

- **SST Progress Monitor** — polling прогресса SST каждые 3 секунды
- Назначение SST-донора

### 🩺 Диагностика

| Инструмент | Источник |
|---|---|
| Process List | `SHOW PROCESSLIST` + Kill Query |
| InnoDB Status | `SHOW ENGINE INNODB STATUS` |
| Check-All | Комплексная wsrep-проверка всех нод |
| System Health | SSH → CPU / RAM / Disk |
| galera.cnf diff | SSH → сравнение конфигов между нодами |
| Event Log | Ring buffer 500 записей |

### ⚙️ Настройки

- Управление кластерами (создание, переименование, удаление)
- Добавление / удаление нод и арбитров
- Глобальные DB credentials
- YAML Preview + горячая перезагрузка конфига

### 📖 Документация (встроенная)

- Справочник по 16 wsrep-переменным (описание, источник, норма)
- FAQ по 6 типичным проблемам: non-Primary, Flow Control, безопасная остановка, SST/IST, garbd, cluster_size=1

---

## 🏗 Архитектура

```
galera_orchestrator_v2/
├── backend/                  # FastAPI (Python 3.9+)
│   ├── main.py               # 55 API эндпоинтов + WebSocket /ws/cluster
│   ├── galera_client.py      # Коннектор: pymysql → MariaDB, paramiko → SSH
│   ├── mock_data.py          # Mock-данные и 5 сценариев (no network)
│   ├── config.py             # nodes.yaml v2 schema, Pydantic, selection/mode
│   ├── auth.py               # JWT HS256 + bcrypt middleware
│   ├── requirements.txt
│   └── static/               # ← Vue-сборка (генерируется в Docker build)
│
├── frontend/                 # Vue 3 + PrimeVue + Vite
│   ├── src/
│   │   ├── pages/            # 9 страниц: Overview, Nodes, Topology, Recovery,
│   │   │                     #   Maintenance, Diagnostics, Settings, Docs, Login
│   │   ├── components/       # NodeCard, Sparkline, TopologySVG, layout/*
│   │   ├── stores/           # Pinia: cluster.js, auth.js
│   │   ├── api/              # Axios + JWT-интерцептор + 401→/login редирект
│   │   └── router/           # Vue Router hash-mode
│   ├── vite.config.js        # outDir: ../backend/static
│   └── package.json
│
├── config/
│   ├── nodes.yaml            # Ваш конфиг (монтируется в Docker, не в git)
│   ├── nodes.example.yaml    # Шаблон — auth включена, admin/admin
│   ├── mode.json             # mock/real (автосоздаётся)
│   └── selection.json        # Активный контур/кластер (автосоздаётся)
│
├── .github/workflows/ci.yml  # CI: ruff + smoke-test + npm build + docker build
├── Dockerfile                # Multi-stage: Node 20 build → Python 3.11 serve
└── docker-compose.yml
```

### Поток данных

```
Browser (Vue 3 SPA — hash routing)
  │
  ├─ WebSocket /ws/cluster?token=<jwt>   ← пуш каждые poll_interval сек
  │                                          + события (start/stop/errors)
  └─ HTTP /api/*
       Authorization: Bearer <jwt>
                │
                ▼
         FastAPI (uvicorn)
               │
       ┌───────┴───────────┐
       │ mock_data.py      │  MOCK-режим — нет сетевых вызовов
       │ galera_client.py  │  REAL-режим:
       │   pymysql ────────┼──→ MariaDB :3306 (wsrep_*)
       │   paramiko ───────┼──→ SSH :22 (garbd, systemctl, grastate)
       └───────────────────┘
```

---

## 🐳 Docker

### docker-compose.yml (разобранный)

```yaml
services:
  galera-orchestrator:
    build: .          # multi-stage: npm build → python serve
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config   # конфиг — persist на хосте
      - ~/.ssh:/root/.ssh:ro   # SSH-ключи для REAL-режима
      - ./logs:/app/logs
    restart: unless-stopped
```

### Управление

```bash
# Запуск
docker compose up -d

# Логи (follow)
docker compose logs -f

# Перезапуск (после изменения Dockerfile)
docker compose up -d --build

# Остановка
docker compose down

# Обновление до новой версии
git pull
docker compose up -d --build
```

### Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `GALERA_PORT` | `8000` | Внешний порт |
| `GALERA_HOST` | `0.0.0.0` | Bind-адрес внутри контейнера |

---

## 🔐 Авторизация

**В v2 авторизация включена по умолчанию.** Логин: `admin`, пароль: `admin`.

### Смена пароля

```bash
# 1. Войти в контейнер и сгенерировать хэш
docker compose exec galera-orchestrator \
  python3 -c "import bcrypt; print(bcrypt.hashpw(b'newpassword', bcrypt.gensalt()).decode())"

# 2. Вставить хэш в config/nodes.yaml
nano config/nodes.yaml
```

```yaml
auth:
  enabled: true
  username: admin
  password_hash: "$2b$12$ваш-новый-хэш"
  token_expire_hours: 24
  secret_key: "уникальная-строка-минимум-32-символа"  # обязательно замените!
```

```bash
# 3. Горячая перезагрузка — без рестарта
curl -X POST http://localhost:8000/api/config/reload \
  -H "Authorization: Bearer <your-token>"
```

---

## ⚙️ Конфигурация

### nodes.yaml — полная схема (v2)

```yaml
contours:
  test:
    clusters:
      - name: test-cluster-1
        nodes:
          - id: gc01
            name: gc01
            host: 192.168.1.10
            port: 3306
            ssh_port: 22
            ssh_user: root
            ssh_key: /root/.ssh/id_rsa  # путь внутри контейнера
            db_user: monitor_user        # per-node override (опционально)
            db_password: ""
            dc: DC1
            enabled: true
        arbitrators:
          - id: arb-01
            host: 192.168.1.12
            ssh_port: 22
            ssh_user: root
            ssh_key: /root/.ssh/id_rsa
            dc: DC1
            enabled: true
  prod:
    clusters:
      - name: prod-cluster-1
        nodes: [...]

db:
  user: monitor_user
  password: CHANGE_ME

settings:
  poll_interval: 5   # секунды

auth:
  enabled: true
  username: admin
  password_hash: "$2b$12$..."
  token_expire_hours: 24
  secret_key: "..."
```

### MariaDB — пользователь мониторинга

```sql
CREATE USER 'monitor_user'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'monitor_user'@'%';
FLUSH PRIVILEGES;
```

### SSH-ключ без пассфразы

```bash
# Генерация
ssh-keygen -t ed25519 -f ~/.ssh/galera_orch -N ""

# Распределить на все ноды и арбитры
ssh-copy-id -i ~/.ssh/galera_orch.pub root@192.168.1.10

# В docker-compose.yml ~/.ssh монтируется как /root/.ssh:ro
# В nodes.yaml указывать путь внутри контейнера: /root/.ssh/galera_orch
```

---

## 🛠 Разработка

```bash
# Backend (hot-reload)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend dev server (в отдельном терминале)
cd frontend
npm install
npm run dev
# → http://localhost:5173  (Vite proxy → :8000)
```

### CI (GitHub Actions)

При каждом push/PR автоматически запускаются:

| Job | Что делает |
|---|---|
| `backend` | `ruff check` + import smoke-test + `GET /api/health` |
| `frontend` | `npm ci` + `npm run build` + upload artifact |
| `docker` | `docker build` (только на main/master) |

---

## 📊 API

Swagger UI: **`http://<host>:8000/docs`** — 55 эндпоинтов.

Все `/api/*` и `/ws/*` требуют заголовок:
```
Authorization: Bearer <token>
```
Публичные (без токена): `/`, `/api/health`, `/api/auth/login`, `/api/auth/status`.

---

## 🗺 Roadmap

- [x] Vue 3 + PrimeVue + Pinia фронтенд
- [x] Авторизация включена по умолчанию
- [x] Docker + docker-compose (multi-stage)
- [x] GitHub Actions CI
- [x] Динамический SVG topology с DC-сегментами
- [ ] История метрик в SQLite (временные ряды 30/90 дней)
- [ ] Prometheus `/metrics` экспорт
- [ ] Webhook-уведомления (Telegram / Slack / generic)
- [ ] Экспорт wsrep-дампа в CSV/JSON

---

## 🔗 Ссылки

- **v1 (оригинал):** [galera_orchestrator](https://github.com/Leg1onary/galera_orchestrator)
- **MariaDB Galera Docs:** [galeracluster.com](https://galeracluster.com/library/)
- **Swagger UI:** `http://<host>:8000/docs`

---

<div align="center">

**Galera Orchestrator v2** — Self-hosted · Docker-first · No external dependencies

</div>
