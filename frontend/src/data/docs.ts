// src/data/docs.ts
// Static documentation content — no API calls, no polling (ТЗ раздел 18.1)

export type DocBadge = 'Safe' | 'Danger' | 'Warning' | 'Action' | 'Info'

export type DocTab =
    | 'service'
    | 'recovery'
    | 'variables'
    | 'diagnostics'
    | 'architecture'
    | 'websocket'
    | 'faq'

export type DocCard = {
    id: string
    tab: DocTab
    section: string
    title: string
    badge: DocBadge
    description: string
    code?: string
    note?: string
}

export const DOCS: DocCard[] = [
    // ── Tab: service — MariaDB Service Commands ─────────────────────────────
    {
        id: 'svc-start',
        tab: 'service',
        section: 'MariaDB',
        title: 'Start',
        badge: 'Safe',
        description:
            'Запустить MariaDB (и Galera node) через systemd. Нода начнёт процедуру Joiner — попытается выполнить IST или SST от донора.',
        code: 'systemctl start mariadb.service',
        note: 'Если кластер полностью остановлен, старт одной ноды в обычном режиме может завершиться ошибкой. Используй Bootstrap.',
    },
    {
        id: 'svc-stop',
        tab: 'service',
        section: 'MariaDB',
        title: 'Stop',
        badge: 'Danger',
        description:
            'Остановить MariaDB на ноде. Нода выйдет из кластера (wsrep_cluster_size уменьшится). Остальные ноды продолжат работу, если сохранится кворум.',
        code: 'systemctl stop mariadb.service',
        note: 'При остановке последней ноды кластер теряет Primary Component. Сохраняй порядок остановки.',
    },
    {
        id: 'svc-restart',
        tab: 'service',
        section: 'MariaDB',
        title: 'Restart',
        badge: 'Warning',
        description:
            'Перезапустить MariaDB с кратким даунтаймом ноды. Нода перейдёт в Joiner и выполнит IST, если seqno не сильно отстал, иначе SST.',
        code: 'systemctl restart mariadb.service',
    },
    {
        id: 'svc-rejoin',
        tab: 'service',
        section: 'MariaDB',
        title: 'Rejoin (Force)',
        badge: 'Action',
        description:
            'Принудительный рестарт ноды для переподключения к кластеру через UI. Эквивалентно systemctl restart mariadb. Используй, когда нода застряла в состоянии OFFLINE или DESYNCED.',
        note: 'Для полного Recovery wizard используй страницу Recovery.',
    },
    {
        id: 'svc-ro',
        tab: 'service',
        section: 'Read Mode',
        title: 'Set Read-Only',
        badge: 'Warning',
        description:
            'Перевести ноду в режим read-only через SQL. Нода продолжает обрабатывать SELECT-запросы, но отклоняет DML.',
        code: 'SET GLOBAL read_only = 1;\n-- или\nSET GLOBAL super_read_only = 1;',
        note: 'Не влияет на репликацию Galera — запросы из других нод применяются.',
    },
    {
        id: 'svc-rw',
        tab: 'service',
        section: 'Read Mode',
        title: 'Set Read-Write',
        badge: 'Safe',
        description:
            'Снять флаг read-only с ноды, сделав её доступной для записи.',
        code: 'SET GLOBAL read_only = 0;\nSET GLOBAL super_read_only = 0;',
    },
    {
        id: 'svc-ping',
        tab: 'service',
        section: 'Diagnostics',
        title: 'Ping (Test Connection)',
        badge: 'Info',
        description:
            'Проверить доступность ноды по SSH и DB-соединению. Возвращает статус SSH, статус DB и измеренную задержку для каждого.',
        note: 'SSH timeout — 5 сек, DB timeout — 3 сек.',
    },

    // ── Tab: recovery ────────────────────────────────────────────────────────
    {
        id: 'rec-bootstrap-wizard',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Bootstrap Wizard',
        badge: 'Danger',
        description:
            'Пошаговый wizard восстановления кластера после полной остановки (все ноды OFFLINE). Читает grastate.dat и seqno с каждой ноды, определяет наиболее актуальную и делает её Primary Component через `pc.bootstrap=1`.',
        note: 'Запускай только если кластер полностью упал. При работающем кластере Bootstrap вызовет split-brain.',
    },
    {
        id: 'rec-non-primary-fix',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Non-Primary Fix',
        badge: 'Danger',
        description:
            'Принудительная установка ноды как Primary Component через wsrep provider option. Применяется когда кластер завис в non-Primary состоянии (wsrep_cluster_status != PRIMARY).',
        code: "SET GLOBAL wsrep_provider_options='pc.bootstrap=1';",
        note: 'Убедись, что только одна нода получает этот статус. Параллельный bootstrap на двух нодах создаёт split-brain.',
    },
    {
        id: 'rec-wsrep-recover',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'wsrep-recover-all',
        badge: 'Danger',
        description:
            'Запуск MariaDB в режиме wsrep-recover для получения последнего seqno без подключения к кластеру. Используется для определения самой актуальной ноды перед Bootstrap.',
        code: 'mysqld_safe --wsrep-recover 2>&1 | grep "Recovered position"',
    },
    {
        id: 'rec-grastate',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'grastate.dat',
        badge: 'Danger',
        description:
            'Файл состояния Galera — хранит UUID кластера, seqno и флаг safe_to_bootstrap. Значение safe_to_bootstrap=1 означает, что нода была последней при корректном завершении.',
        code: 'cat /var/lib/mysql/grastate.dat',
        note: 'Никогда не редактируй safe_to_bootstrap вручную без понимания последствий.',
    },
    {
        id: 'rec-sst',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'SST Warning',
        badge: 'Warning',
        description:
            'State Snapshot Transfer — полная копия данных с донора на Joiner. Занимает много времени при больших базах. Во время SST донор помечается как DONOR/DESYNCED и не принимает запись.',
        note: 'Предпочитай IST, удерживая gcache достаточно большим (wsrep_provider_options: gcache.size).',
    },
    {
        id: 'rec-ist',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'IST vs SST',
        badge: 'Info',
        description:
            'Incremental State Transfer — передача только пропущенных транзакций через gcache. Быстрая и не нагружает донора. Возможна только если отставание ноды укладывается в размер gcache на доноре.',
    },
    {
        id: 'rec-rejoin',
        tab: 'recovery',
        section: 'Rejoin',
        title: 'Rejoin Node',
        badge: 'Action',
        description:
            'Переподключение отдельной ноды к рабочему кластеру через перезапуск MariaDB. Отличается от Bootstrap — кластер уже имеет Primary Component.',
        code: 'systemctl restart mariadb.service',
    },

    // ── Tab: variables ───────────────────────────────────────────────────────
    {
        id: 'var-clustersize',
        tab: 'variables',
        section: 'Cluster State',
        title: 'wsrep_cluster_size',
        badge: 'Info',
        description:
            'Количество нод в кластере на текущий момент. Должно совпадать с ожидаемым числом нод. Снижение указывает на потерю ноды.',
    },
    {
        id: 'var-clusterstatus',
        tab: 'variables',
        section: 'Cluster State',
        title: 'wsrep_cluster_status',
        badge: 'Info',
        description:
            'Статус компонента: PRIMARY (кворум есть, запись разрешена) или non-Primary (кворум потерян, запись заблокирована). Значение non-Primary — критический признак.',
    },
    {
        id: 'var-localstate',
        tab: 'variables',
        section: 'Node State',
        title: 'wsrep_local_state_comment',
        badge: 'Info',
        description:
            'Текстовое состояние ноды: Synced (полностью в кластере), Joiner (получает данные), Donor (отдаёт SST), Desynced (временно отключена от потока).',
    },
    {
        id: 'var-connected',
        tab: 'variables',
        section: 'Node State',
        title: 'wsrep_connected',
        badge: 'Info',
        description:
            'ON — нода подключена к кластеру через wsrep-провайдер. OFF — нода изолирована.',
    },
    {
        id: 'var-ready',
        tab: 'variables',
        section: 'Node State',
        title: 'wsrep_ready',
        badge: 'Info',
        description:
            'ON — нода принимает SQL-запросы и участвует в репликации. OFF — нода не готова (например, во время SST или при потере кворума).',
    },
    {
        id: 'var-flowcontrol',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_flow_control_paused',
        badge: 'Warning',
        description:
            'Доля времени (0–1), когда репликация была приостановлена из-за Flow Control. Значение > 0.1 (10%) означает, что медленная нода тормозит весь кластер.',
        note: 'Ищи ноду с большим wsrep_local_recv_queue — именно она инициирует FC.',
    },
    {
        id: 'var-recvqueue',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_local_recv_queue',
        badge: 'Warning',
        description:
            'Очередь входящих транзакций на применение. Ненулевое значение означает отставание ноды. Растущая очередь — признак нагрузки на применение или медленного диска.',
    },
    {
        id: 'var-sendqueue',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_local_send_queue',
        badge: 'Info',
        description:
            'Очередь транзакций ожидающих отправки другим нодам. В норме 0. Рост указывает на сетевые проблемы или перегрузку.',
    },
    {
        id: 'var-lastcommitted',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_last_committed',
        badge: 'Info',
        description:
            'Sequence number последней применённой транзакции. Используется для сравнения актуальности нод при Bootstrap.',
    },

    // ── Tab: diagnostics ─────────────────────────────────────────────────────
    {
        id: 'diag-conncheck',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'Connection Check',
        badge: 'Info',
        description:
            'Параллельная проверка SSH и DB-соединений для всех нод и арбитраторов кластера. Показывает статус SSH, MariaDB, задержки. Запускается вручную (не polling).',
    },
    {
        id: 'diag-configdiff',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'Config Diff',
        badge: 'Info',
        description:
            'Сравнение wsrep-переменных (SHOW GLOBAL VARIABLES LIKE "wsrep%") между всеми нодами. Отклонения в конфигурации между нодами отображаются как diff-строки.',
    },
    {
        id: 'diag-innodb',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'InnoDB Status',
        badge: 'Warning',
        description:
            'Вывод SHOW ENGINE INNODB STATUS выбранной ноды. Содержит секцию LATEST DETECTED DEADLOCK, транзакционный лог, buffer pool stats. Полезно для диагностики блокировок.',
        code: 'SHOW ENGINE INNODB STATUS\\G',
    },
    {
        id: 'diag-resources',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'System Resources',
        badge: 'Info',
        description:
            'CPU load avg, RAM (used/total), Disk usage (/), Uptime по каждой ноде через SSH (/proc/loadavg, free -b, df -B1 /).',
        note: 'CPU > 80% — Warning, > 95% — Danger. RAM > 85% — Warning. Disk > 80% — Warning.',
    },
    {
        id: 'diag-arblog',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'Arbitrator Log',
        badge: 'Info',
        description:
            'Последние N строк лога garbd через SSH (journalctl -u garbd или tail /var/log/garbd.log). Полезно для диагностики проблем с арбитратором.',
        code: 'journalctl -u garbd -n 100 --no-pager',
    },
    {
        id: 'diag-variables',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'SHOW GLOBAL VARIABLES',
        badge: 'Info',
        description:
            'Полный вывод SHOW GLOBAL VARIABLES с фильтром по wsrep-переменным (или любой подстроке). Key-value таблица с поиском.',
        code: "SHOW GLOBAL VARIABLES WHERE Variable_name LIKE 'wsrep%';",
    },

    // ── Tab: architecture ────────────────────────────────────────────────────
    {
        id: 'arch-overview',
        tab: 'architecture',
        section: 'Деплой',
        title: 'Один контейнер',
        badge: 'Info',
        description:
            'Galera Orchestrator v2 работает в одном Docker-контейнере. FastAPI отдаёт собранную Vue 3 SPA-статику и REST API. SQLite хранится на volume /data/orchestrator.db.',
    },
    {
        id: 'arch-fernet',
        tab: 'architecture',
        section: 'Безопасность',
        title: 'Шифрование паролей (Fernet)',
        badge: 'Info',
        description:
            'Пароли MariaDB-нод хранятся в SQLite в зашифрованном виде (Fernet symmetric encryption). Ключ задаётся переменной FERNET_SECRET_KEY. При смене ключа существующие пароли станут нечитаемыми.',
        note: 'Сгенерируй ключ: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',
    },
    {
        id: 'arch-ssh',
        tab: 'architecture',
        section: 'SSH',
        title: 'SSH-ключ (Global)',
        badge: 'Warning',
        description:
            'Используется один глобальный SSH-ключ для всех нод и арбитраторов. Ключ монтируется в контейнер read-only по пути /root/.ssh/id_rsa. Никогда не хранится в БД.',
        code: '# docker-compose.yml\nvolumes:\n  - ~/.ssh/id_rsa:/root/.ssh/id_rsa:ro',
        note: 'SSH timeout подключения — 5 сек. Timeout выполнения команды — 10 сек.',
    },
    {
        id: 'arch-auth',
        tab: 'architecture',
        section: 'Безопасность',
        title: 'JWT в httpOnly Cookie',
        badge: 'Info',
        description:
            'Аутентификация через JWT, хранящийся только в httpOnly cookie. JavaScript не имеет доступа к токену. Сессия проверяется через GET /api/auth/me.',
    },
    {
        id: 'arch-cluster-scope',
        tab: 'architecture',
        section: 'API',
        title: 'Cluster-scoped API',
        badge: 'Info',
        description:
            'Все endpoints привязаны к cluster_id: /api/clusters/{cluster_id}/... Это гарантирует изоляцию данных между кластерами. При смене кластера в Header все Vue Query кэши инвалидируются.',
    },
    {
        id: 'arch-lock',
        tab: 'architecture',
        section: 'Операции',
        title: 'Cluster-level Lock',
        badge: 'Warning',
        description:
            'При выполнении recovery или rolling restart кластер блокируется — параллельный запуск второй операции вернёт 409 Conflict. Статус блокировки виден в activeoperation поле status endpoint.',
    },

    // ── Tab: websocket ────────────────────────────────────────────────────────
    {
        id: 'ws-realtime',
        tab: 'websocket',
        section: 'Real-time',
        title: 'WebSocket Events',
        badge: 'Info',
        description:
            'Frontend подключается к WS /ws/clusters/{cluster_id}. Авторизация через httpOnly cookie. При смене кластера соединение переустанавливается.',
    },
    {
        id: 'ws-events',
        tab: 'websocket',
        section: 'Real-time',
        title: 'Типы событий',
        badge: 'Info',
        description:
            'node_state_changed, arbitrator_state_changed, operation_started, operation_progress, operation_finished, log_entry. События приходят при изменении состояния по результатам polling или во время операций.',
        code: '// Пример события:\n{\n  "event": "node_state_changed",\n  "cluster_id": 1,\n  "ts": "2026-04-09T00:00:00Z",\n  "payload": {\n    "node_id": 2,\n    "old_state": "SYNCED",\n    "new_state": "OFFLINE"\n  }\n}',
    },
    {
        id: 'ws-reconnect',
        tab: 'websocket',
        section: 'Real-time',
        title: 'Reconnect',
        badge: 'Info',
        description:
            'При обрыве WS-соединения Footer показывает статус Disconnected (красный). Frontend автоматически переподключается каждые 5 секунд.',
    },
    {
        id: 'ws-footer',
        tab: 'websocket',
        section: 'UI',
        title: 'Footer WS-индикатор',
        badge: 'Info',
        description:
            'Footer отображает статус WebSocket-соединения: Connected (зелёный) / Reconnecting (жёлтый) / Disconnected (красный). Управляется через Pinia ws store.',
    },
    {
        id: 'ws-wsrep',
        tab: 'websocket',
        section: 'wsrep-переменные',
        title: 'Polling + WS модель',
        badge: 'Info',
        description:
            'Polling (интервал из system_settings) — source of truth для полного состояния нод. WebSocket — дельта-события для инкрементального обновления UI без перезапроса. Данные в ring buffer: 30 точек для спарклайнов.',
    },

    // ── Tab: faq ──────────────────────────────────────────────────────────────
    {
        id: 'faq-restore',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Как восстановить упавший кластер?',
        badge: 'Info',
        description:
            'Перейди на страницу Recovery. Wizard автоматически прочитает grastate.dat с каждой ноды, определит актуальную (по seqno и safe_to_bootstrap) и предложит план Bootstrap. Подтверди и следи за прогрессом.',
    },
    {
        id: 'faq-warning',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Когда нода переходит в Warning?',
        badge: 'Warning',
        description:
            'Нода считается degraded (отображается оранжевым) если: wsrep_ready=OFF, состояние DONOR/JOINER/DESYNCED, или maintenance=true + read_only=0 (maintenance drift).',
    },
    {
        id: 'faq-splitbrain',
        tab: 'faq',
        section: 'Критические ситуации',
        title: 'Split-brain',
        badge: 'Danger',
        description:
            'Split-brain возникает когда два независимых набора нод считают себя Primary Component. Обычно происходит при неправильном Bootstrap или сетевой партиции. Кластер показывает статус critical. Требует ручного вмешательства — останови все ноды кроме одной, затем Bootstrap.',
    },
    {
        id: 'faq-ist-sst',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Когда происходит IST, когда SST?',
        badge: 'Info',
        description:
            'IST (быстрый) — если отставание Joiner ноды покрывается gcache на доноре. SST (медленный, полная копия) — если gcache недостаточен или нода была отключена слишком долго. Размер gcache: wsrep_provider_options: gcache.size.',
    },
    {
        id: 'faq-polling',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Как изменить интервал обновления?',
        badge: 'Info',
        description:
            'Интервал polling настраивается в Settings → System → Polling Interval (сек). Минимум рекомендуется 5 сек, чтобы не нагружать ноды диагностическими запросами.',
    },
]

// Константы для рендера вкладок
export const DOC_TABS: { id: DocTab; label: string }[] = [
    { id: 'service',      label: 'Сервис MariaDB' },
    { id: 'recovery',     label: 'Recovery' },
    { id: 'variables',    label: 'wsrep-переменные' },
    { id: 'diagnostics',  label: 'Diagnostics' },
    { id: 'architecture', label: 'Архитектура' },
    { id: 'websocket',    label: 'WebSocket' },
    { id: 'faq',          label: 'FAQ' },
]

export const BADGE_CONFIG: Record<DocBadge, { severity: string; label: string }> = {
    Safe:    { severity: 'success', label: 'Safe' },
    Danger:  { severity: 'danger',  label: 'Danger' },
    Warning: { severity: 'warn',    label: 'Warning' },
    Action:  { severity: 'info',    label: 'Action' },
    Info:    { severity: 'secondary', label: 'Info' },
}