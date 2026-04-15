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
| 7 | **Rejoin node** | Standalone-действие: `systemctl restart mariadb` через SSH, проверка `wsrep_cluster_status` до/после, ConfirmDialog. | `nodes.py`, `NodeActionsPanel.vue` |
| 8 | **Bootstrap cluster** | 4-шаговый wizard: скан SSH всех нод, чтение `grastate.dat`/`seqno`, bootstrap ноды с макс `seqno`, rejoin остальных | `RecoveryPage.vue`, `recovery/` стор, `stores/recovery.ts` |
| 9 | **Purge binary logs** | Модальное окно с выбором даты/количества дней, `PURGE BINARY LOGS BEFORE ...` | `nodes.py`, frontend-модал |
| 10 | **Desync / Resync ноды** | `SET GLOBAL wsrep_desync = ON/OFF` — вывод ноды из репликации для тяжёлых операций без тормозов кластера. | `nodes.py`, `NodeActionsPanel.vue` |
| 11 | **Stuck SST detector + restart** | Детект ноды в `Joining`/`Donor/Desynced` дольше порога. `GET /nodes/sst-status`, `POST /nodes/{node_id}/restart-sst`. | `nodes.py`, `poller.py`, `SstStatusPanel.vue` |
| 12 | **FLUSH операции** | `FLUSH LOGS`, `FLUSH TABLES WITH READ LOCK`, `UNLOCK TABLES`. | `nodes.py`, `NodeActionsPanel.vue` |
| 13 | **Disk usage детализация** | Топ-10 самых больших таблиц (`information_schema.TABLES`), размер бинлогов (`SHOW BINARY LOGS`), размер ibdata1. Панель в секции System Resources на DiagnosticsPage. | `diagnostics.py` (`POST /diagnostics/disk-usage`), `diagnostics.ts`, `DiskUsagePanel.vue` |
| 14 | **Replication lag alert widget** | Виджет на Overview: `wsrep_local_recv_queue_avg` > порога → алерт с рекомендацией увеличить `wsrep_slave_threads`. | `diagnostics.py`, `diagnostics.ts`, `ReplicationLagAlert.vue` |
| 15 | **Активные транзакции** | `information_schema.INNODB_TRX` — транзакции старше N секунд, с кнопкой Kill. Отдельно от processlist. | `diagnostics.py`, `diagnostics.ts`, `ActiveTransactionsPanel.vue` |
| 16 | **Deadlock история** | Парсинг последнего дедлока из `SHOW ENGINE INNODB STATUS`, отображение victim/blocker trx в читаемом виде. | `diagnostics.py`, `diagnostics.ts`, `DeadlockPanel.vue` |
| 17 | **Config Health Check** | Проверка ключевых параметров (`innodb_buffer_pool_size` ~70% RAM, `max_connections`, `wsrep_slave_threads` >= CPU cores) — статусы ok/warn/error с рекомендациями. | `diagnostics.py`, `diagnostics.ts`, `ConfigHealthPanel.vue` |

---

## 🚧 В работе / Запланировано

### Блок — Smart Advisor

| # | Фича | Описание | Статус |
|---|---|---|---|
| 20 | **Advisor panel** | `GET /api/clusters/{cluster_id}/advisor` — детерминированные правила поверх существующих диагностических данных. Карточки проблем (severity, evidence, recommended action) с кнопками действий. Виджет на Overview + полная панель в Diagnostics. | 🔲 Запланировано |

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
**Текущая задача:** все аварийные инструменты, мониторинг и конфигурационные проверки (#1–#17) реализованы; следующий шаг — Advisor (#20)  
**Следующий шаг:** #20 — Advisor panel (backend endpoint + AdvisorPanel.vue + Overview widget)
