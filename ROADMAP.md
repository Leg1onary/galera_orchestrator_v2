# Galera Orchestrator v2 — Roadmap

> Базовый MVP реализован полностью (и сверх ТЗ).
> Этот файл фиксирует план дополнительных улучшений вне MVP.
> Обновляется по мере реализации.

---

## ✅ Уже реализовано (улучшения вне MVP)

| # | Фича | Файлы |
|---|---|---|
| 1 | Экранирование unicode-символов в NodesTable (`—`, `…`) | `NodesTable.vue` |
| 2 | Отображение `name` для арбитра в ConnectionCheckPanel | `diagnostics.ts` |
| 3 | Enable/Disable `slow_query_log` прямо из UI | `SlowQueryPanel.vue`, `diagnostics.py`, `diagnostics.ts` |
| 4 | Фильтры в SlowQueryPanel (query time, db, user, query text) | `SlowQueryPanel.vue` |

---

## 🚧 В работе / Запланировано

### Блок 1 — Аварийные инструменты (по одному)

| # | Фича | Описание | Статус |
|---|---|---|---|
| 5 | **Kill process** | Кнопка Kill рядом с каждым процессом в ProcessListPanel. Backend: `POST /nodes/{node_id}/kill-process/{process_id}` | 🔲 Следующий |
| 6 | **Rejoin node** | Рестарт MariaDB на ноде через SSH (`systemctl restart mariadb`). Проверка статуса до/после. | 🔲 Запланировано |
| 7 | **Bootstrap cluster** | Авто-определение ноды с наибольшим `seqno` из `grastate.dat`, выполнение `pc.bootstrap=YES`. Защита от случайного запуска. | 🔲 Запланировано |
| 8 | **Purge binary logs** | Модальное окно с выбором даты/количества дней. `PURGE BINARY LOGS BEFORE ...` | 🔲 Запланировано |
| 9 | **Stuck SST detector + restart** | Детект ноды в состоянии `Joining`/`Donor/Desynced` дольше порога. Кнопка рестарта SST. | 🔲 Запланировано |
| 10 | **Replication lag alert widget** | Виджет на Overview: `wsrep_local_recv_queue_avg` > порога → алерт с рекомендацией | 🔲 Запланировано |

### Блок 2 — Smart Advisor

| # | Фича | Описание | Статус |
|---|---|---|---|
| 11 | **Advisor panel** | `GET /api/clusters/{id}/advisor` — детерминированные правила поверх существующих данных. Карточки проблем с кнопками действий (из блока 1). Виджет на дашборде + полная панель в Diagnostics. | 🔲 После блока 1 |

---

## 📐 Архитектурные принципы улучшений

- Все новые backend-эндпоинты: `cluster-scoped` → `/api/clusters/{cluster_id}/...`
- Деструктивные действия (Bootstrap, Kill, Rejoin): требуют подтверждения в UI (ConfirmDialog)
- SSH-операции: через существующий `SSHClient` из `services/ssh_client.py`
- DB-операции: через существующий `DBClient` из `services/db_client.py`
- Все действия пишутся в `event_log` через `write_event()`
- Фронтенд: toast на успех/ошибку, рефетч данных после действия
- Права: 403 если недостаточно привилегий → показываем пользователю

---

## 🗂 Контекст для восстановления чата

**Репозиторий:** `Leg1onary/galera_orchestrator_v2`  
**Стек:** Python 3.11 / FastAPI / SQLAlchemy Core / SQLite / paramiko / pymysql + Vue 3 / Vite / Pinia / TanStack Vue Query / PrimeVue  
**Эталон:** `galera-orchestrator-v2-final-spec.docx` — базовый контракт, всё новое помечается как "вне MVP"  
**Текущая задача:** реализуем аварийные инструменты поштучно (#5 → #10), затем Advisor (#11)
