# Galera Orchestrator v2 — Roadmap

> Базовый MVP реализован полностью (и сверх ТЗ).
> Этот файл фиксирует план дополнительных улучшений вне MVP.
> Обновляется по мере реализации.

---

## ✅ Уже реализовано (улучшения вне MVP)

| # | Фича | Описание | Файлы |
|---|---|---|---|
| 1 | Экранирование unicode-символов в NodesTable | `—`, `…` отображаются корректно | `NodesTable.vue` |
| 2 | Отображение `name` для арбитра в ConnectionCheckPanel | `arbitrator_name` маппится в `node_name` | `diagnostics.ts` |
| 3 | Enable/Disable `slow_query_log` прямо из UI | Тоггл через `SET GLOBAL slow_query_log` | `SlowQueryPanel.vue`, `diagnostics.py`, `diagnostics.ts` |
| 4 | Фильтры в SlowQueryPanel | query time, db, user, query text | `SlowQueryPanel.vue` |
| 5 | **Kill process** | Кнопка Kill рядом с процессом, ConfirmDialog, `POST /nodes/{node_id}/kill-process/{process_id}` | `ProcessListPanel.vue`, `diagnostics.py`, `diagnostics.ts` |
| 6 | **Kill ALL по фильтру** | Kill Sleep > N сек или по юзеру, `POST /nodes/{node_id}/kill-processes` | `ProcessListPanel.vue`, `diagnostics.py`, `diagnostics.ts` |
| 8 | **Bootstrap cluster** | 4-шаговый wizard: скан SSH всех нод, чтение `grastate.dat`/`seqno`, bootstrap ноды с макс `seqno`, rejoin остальных | `RecoveryPage.vue`, `recovery/` стор, `stores/recovery.ts` |
| 9 | **Purge binary logs** | Модальное окно с выбором даты/количества дней, `PURGE BINARY LOGS BEFORE ...` | `nodes.py`, frontend-модал |

---

## 🚧 В работе / Запланировано

### Блок 1 — Аварийные инструменты (поштучно, по порядку)

| # | Фича | Описание | Статус |
|---|---|---|---|
| 7 | **Rejoin node** | Standalone-действие для работающего кластера: перезапуск MariaDB на отдельной ноде, которая выпала из кластера при здоровых остальных. `systemctl restart mariadb` через SSH. Проверка `wsrep_cluster_status` до/после. ConfirmDialog. Отличается от RecoveryPage: там wizard для полностью мёртвого кластера, здесь — быстрый rejoin одной ноды без wizardа. | 🔲 Следующий |
| 10 | **Desync / Resync ноды** | `SET GLOBAL wsrep_desync = ON/OFF` — вывод ноды из репликации для тяжёлых операций без тормозов кластера. | 🔲 Запланировано |
| 11 | **Stuck SST detector + restart** | Детект ноды в состоянии `Joining`/`Donor/Desynced` дольше порога. Кнопка рестарта SST. | 🔲 Запланировано |
| 12 | **FLUSH операции** | `FLUSH LOGS` (ротация бинлогов), `FLUSH TABLES WITH READ LOCK` / `UNLOCK TABLES`. Нужны перед бэкапом. | 🔲 Запланировано |

### Блок 2 — Мониторинг и диагностика

| # | Фича | Описание | Статус |
|---|---|---|---|
| 13 | **Disk usage детализация** | Топ-10 самых больших таблиц (`information_schema.TABLES`), размер бинлогов (`SHOW BINARY LOGS`), размер ibdata1. | 🔲 Запланировано |
| 14 | **Replication lag alert widget** | Виджет на Overview: `wsrep_local_recv_queue_avg` > порога → алерт с рекомендацией увеличить `wsrep_slave_threads`. | 🔲 Запланировано |
| 15 | **Активные транзакции** | `information_schema.INNODB_TRX` — транзакции старше N секунд. Отдельно от processlist. | 🔲 Запланировано |
| 16 | **Deadlock история** | Парсинг последнего дедлока из `SHOW ENGINE INNODB STATUS` и отображение в читаемом виде (сейчас есть raw текст). | 🔲 Запланировано |

### Блок 3 — Конфигурация

| # | Фича | Описание | Статус |
|---|---|---|---|
| 17 | **Config Health Check** | Проверка ключевых параметров: `innodb_buffer_pool_size` (~70% RAM), `max_connections`, `wsrep_slave_threads` (>= CPU cores) — с рекомендациями в UI. | 🔲 Запланировано |
| 18 | **Изменение wsrep_provider_options на лету** | `pc.weight`, `evs.suspect_timeout` и др. без рестарта. | 🔲 Запланировано |
| 19 | **Проверка и починка таблиц** | `CHECK TABLE` / `REPAIR TABLE` с выбором таблицы из списка. | 🔲 Запланировано |

### Блок 4 — Smart Advisor

| # | Фича | Описание | Статус |
|---|---|---|---|
| 20 | **Advisor panel** | `GET /api/clusters/{id}/advisor` — детерминированные правила поверх существующих данных. Карточки проблем с кнопками действий из блоков 1–3. Виджет на дашборде + полная панель в Diagnostics. | 🔲 После блоков 1–3 |

---

## 📐 Архитектурные принципы улучшений

- Все новые backend-эндпоинты: `cluster-scoped` → `/api/clusters/{cluster_id}/...`
- Деструктивные действия (Bootstrap, Kill, Rejoin, Flush): требуют подтверждения в UI (`ConfirmDialog`)
- SSH-операции: через существующий `SSHClient` из `services/ssh_client.py`
- DB-операции: через существующий `DBClient` из `services/db_client.py`
- Все действия пишутся в `event_log` через `write_event()`
- Фронтенд: toast на успех/ошибку, рефетч данных после действия
- Права: 403 если недостаточно привилегий → показываем пользователю
- Импорты бэкенда: `BaseModel` из pydantic, `asyncio.to_thread` для блокирующих операций

---

## 🗂 Контекст для восстановления чата

**Репозиторий:** `Leg1onary/galera_orchestrator_v2`  
**Стек:** Python 3.11 / FastAPI / SQLAlchemy Core / SQLite / paramiko / pymysql + Vue 3 / Vite / Pinia / TanStack Vue Query / PrimeVue  
**Эталон:** `galera-orchestrator-v2-final-spec.docx` — базовый контракт, всё новое помечается как "вне MVP"  
**Текущая задача:** реализуем аварийные инструменты поштучно (#7 → #19), затем Advisor (#20)  
**Следующий шаг:** #7 — Rejoin node (standalone, не wizard)
