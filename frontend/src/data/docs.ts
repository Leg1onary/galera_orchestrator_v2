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
        id: 'svc-status',
        tab: 'service',
        section: 'MariaDB',
        title: 'Status Check',
        badge: 'Info',
        description:
            'Проверить статус systemd-юнита MariaDB. Показывает активен ли процесс, PID, последние строки лога и дату последнего старта.',
        code: 'systemctl status mariadb.service\n# краткая проверка:\nsystemctl is-active mariadb.service',
    },
    {
        id: 'svc-enable',
        tab: 'service',
        section: 'MariaDB',
        title: 'Enable / Disable автозапуск',
        badge: 'Warning',
        description:
            'Включить или отключить автоматический запуск MariaDB при старте ОС. Без enable нода не поднимется после перезагрузки сервера.',
        code: 'systemctl enable mariadb.service   # включить автозапуск\nsystemctl disable mariadb.service  # отключить автозапуск',
        note: 'На нодах production всегда держи enable включённым.',
    },
    {
        id: 'svc-new-cluster',
        tab: 'service',
        section: 'MariaDB',
        title: 'galera_new_cluster',
        badge: 'Danger',
        description:
            'Специальная команда для первоначального запуска кластера или Bootstrap после полного падения. Запускает MariaDB с параметром --wsrep-new-cluster, делая ноду Primary Component.',
        code: 'galera_new_cluster\n# или напрямую:\nmysqld_safe --wsrep-new-cluster &',
        note: 'Используй только на одной ноде — той, у которой наибольший seqno. Wizard Recovery делает это автоматически.',
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
    {
        id: 'svc-wsrep-status',
        tab: 'service',
        section: 'Diagnostics',
        title: 'Быстрая проверка состояния Galera',
        badge: 'Info',
        description:
            'Минимальный набор SQL-запросов для ручной диагностики состояния ноды и кластера прямо в консоли.',
        code: "SHOW STATUS LIKE 'wsrep_cluster_status';\nSHOW STATUS LIKE 'wsrep_local_state_comment';\nSHOW STATUS LIKE 'wsrep_cluster_size';\nSHOW STATUS LIKE 'wsrep_connected';\nSHOW STATUS LIKE 'wsrep_ready';",
    },
    {
        id: 'svc-journal',
        tab: 'service',
        section: 'Diagnostics',
        title: 'Просмотр логов MariaDB',
        badge: 'Info',
        description:
            'Просмотр системного журнала MariaDB через journald. Незаменимо при диагностике проблем старта, SST и ошибок репликации.',
        code: '# Последние 100 строк:\njournalctl -u mariadb -n 100 --no-pager\n\n# Живой поток:\njournalctl -u mariadb -f\n\n# С фильтром по времени:\njournalctl -u mariadb --since "1 hour ago"',
    },
    {
        id: 'svc-flush-logs',
        tab: 'service',
        section: 'MariaDB',
        title: 'FLUSH LOGS / бинлог',
        badge: 'Warning',
        description:
            'Принудительная ротация бинарных логов. Используется перед бэкапом или для уменьшения размера текущего binlog-файла.',
        code: 'FLUSH BINARY LOGS;\n-- Посмотреть текущий binlog:\nSHOW MASTER STATUS;\n-- Удалить старые binlog до указанного файла:\nPURGE BINARY LOGS TO \'mariadb-bin.000100\';',
        note: 'В Galera binlog не используется для репликации между нодами, но может быть нужен для внешних реплик (async slave).',
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
        id: 'rec-quorum',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Кворум и формула',
        badge: 'Warning',
        description:
            'Galera требует кворума для работы в режиме Primary Component: больше половины нод должны быть доступны. При 3 нодах минимум 2, при 5 нодах — минимум 3. Арбитратор (garbd) считается нодой для кворума, но не хранит данные.',
        note: 'Формула: кворум = ⌊N/2⌋ + 1. При чётном числе нод без арбитратора — риск split-brain при сетевой партиции 50/50.',
    },
    {
        id: 'rec-evict',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Evict (исключить ноду)',
        badge: 'Danger',
        description:
            'Принудительное исключение ноды из кластера через wsrep provider. Используется когда нода "зависла" в кластере и мешает кворуму, но не отвечает.',
        code: "-- Выполнить на живой ноде:\nSET GLOBAL wsrep_provider_options='evs.evict=<node-uuid>';",
        note: 'UUID ноды смотри в wsrep_gcomm_uuid или в логах MariaDB.',
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
        id: 'rec-gcache',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'gcache.size — тюнинг',
        badge: 'Info',
        description:
            'gcache (Galera Write-Set Cache) хранит последние транзакции для IST. Чем больше gcache, тем дольше нода может быть офлайн и вернуться через IST, а не SST.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_provider_options="gcache.size=512M"',
        note: 'Для высоконагруженных кластеров рекомендуется 1–2 GB. gcache хранится в /var/lib/mysql/galera.cache.',
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
    {
        id: 'rec-sst-mariabackup',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'SST через mariabackup',
        badge: 'Info',
        description:
            'mariabackup — рекомендуемый SST-метод. В отличие от rsync, не блокирует запись на доноре во время передачи (hot backup). Требует установки пакета mariadb-backup на всех нодах.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_sst_method=mariabackup\nwsrep_sst_auth=sst_user:password',
        note: 'Создай выделенного пользователя SST: GRANT RELOAD, PROCESS, LOCK TABLES, REPLICATION CLIENT ON *.* TO sst_user@localhost;',
    },
    {
        id: 'rec-donor-selection',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'Выбор донора для SST',
        badge: 'Info',
        description:
            'По умолчанию Galera выбирает донора автоматически. Можно указать предпочтительного донора явно, чтобы SST не нагружал production-ноду.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_sst_donor=db-02,db-03',
        note: 'Список через запятую — Galera попробует по порядку. Если указанные доноры недоступны, выберет любой.',
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
        id: 'var-clusteruuid',
        tab: 'variables',
        section: 'Cluster State',
        title: 'wsrep_cluster_state_uuid',
        badge: 'Info',
        description:
            'UUID кластера — уникальный идентификатор Galera-кластера. Должен быть одинаковым на всех нодах. Расхождение UUID означает, что нода подключилась не к тому кластеру или граstate повреждён.',
        code: "SHOW STATUS LIKE 'wsrep_cluster_state_uuid';",
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
    {
        id: 'var-certdeps',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_cert_deps_distance',
        badge: 'Info',
        description:
            'Среднее расстояние между транзакциями, которые можно применять параллельно. Чем больше значение — тем лучше Galera параллелизирует применение транзакций. Значение < 1 означает полностью последовательное применение.',
        note: 'Для увеличения параллелизма увеличь wsrep_slave_threads (до числа ядер CPU).',
    },
    {
        id: 'var-slavethreads',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_slave_threads',
        badge: 'Info',
        description:
            'Число потоков, применяющих входящие транзакции (write-sets) от других нод. Рекомендуется устанавливать равным числу ядер CPU или вдвое больше. По умолчанию 1.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_slave_threads = 4',
        note: 'Смотри wsrep_cert_deps_distance — если значение > 1, потоки реально параллелятся.',
    },
    {
        id: 'var-causalreads',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_causal_reads / wsrep_sync_wait',
        badge: 'Warning',
        description:
            'wsrep_sync_wait (новее) или wsrep_causal_reads (устар.) — заставляют ноду дождаться применения всех входящих транзакций перед выполнением SELECT. Устраняет грязные чтения, но добавляет латентность.',
        code: 'SET SESSION wsrep_sync_wait = 1;  -- для SELECT\nSET SESSION wsrep_sync_wait = 3;  -- для SELECT + UPDATE',
        note: 'Используй только там, где нужна строгая консистентность. На глобальном уровне сильно снижает производительность.',
    },
    {
        id: 'var-applyoooe',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_apply_oooe',
        badge: 'Info',
        description:
            'Доля транзакций, применённых вне порядка (Out-Of-Order Execution). Чем выше значение — тем эффективнее работает параллельное применение. Значение 0 означает строго последовательное применение.',
    },
    {
        id: 'var-repl-max-ws-size',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_max_ws_size',
        badge: 'Warning',
        description:
            'Максимальный размер write-set одной транзакции (по умолчанию 2 GB). Транзакции крупнее этого лимита будут отклонены Galera с ошибкой. Актуально при bulk-операциях.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_max_ws_size=2G',
        note: 'Разбивай большие UPDATE/DELETE на батчи по 1k–10k строк — это снизит нагрузку на всю репликацию.',
    },
    {
        id: 'var-gcache-recover',
        tab: 'variables',
        section: 'Performance',
        title: 'gcache.recover',
        badge: 'Info',
        description:
            'Позволяет переиспользовать gcache после перезапуска ноды вместо его полного сброса. Ускоряет повторное подключение через IST после planned shutdown.',
        code: 'wsrep_provider_options="gcache.recover=yes; gcache.size=1G"',
        note: 'Доступно в MariaDB 10.4+. На старых версиях gcache сбрасывается при каждом рестарте.',
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
    {
        id: 'diag-checkall',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'Check All',
        badge: 'Action',
        description:
            'Запуск всех диагностических проверок одновременно: connection check, config diff, system resources. Результаты агрегируются в единый отчёт. Удобно для быстрой диагностики перед maintenance.',
    },
    {
        id: 'diag-deadlock',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'Deadlock Detection',
        badge: 'Warning',
        description:
            'Galera использует оптимистичную блокировку (Optimistic Locking) — конфликты транзакций обнаруживаются при commit, а не при чтении. Это означает, что два клиента могут обновить одну строку, но второй получит Deadlock при коммите.',
        code: '-- Найти последний deadlock:\nSHOW ENGINE INNODB STATUS\\G\n-- Секция: LATEST DETECTED DEADLOCK',
        note: 'Galera добавляет свой тип конфликта: wsrep_conflict. Смотри wsrep_local_cert_failures для статистики.',
    },
    {
        id: 'diag-certfailures',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'wsrep_local_cert_failures',
        badge: 'Warning',
        description:
            'Счётчик транзакций, отклонённых на стадии сертификации Galera (конфликт write-sets). Растущий счётчик — признак высокого уровня конкуренции за одни и те же строки между нодами.',
        code: "SHOW STATUS LIKE 'wsrep_local_cert_failures';",
    },
    {
        id: 'diag-processlist',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'Активные запросы',
        badge: 'Info',
        description:
            'Просмотр всех активных соединений и выполняемых запросов. Полезно для обнаружения долгих транзакций, которые могут блокировать Galera-репликацию.',
        code: 'SHOW FULL PROCESSLIST;\n-- Только долгие запросы (> 5 сек):\nSELECT * FROM information_schema.PROCESSLIST\nWHERE TIME > 5 AND COMMAND != \'Sleep\'\nORDER BY TIME DESC;',
        note: 'Долгие незакоммиченные транзакции могут вызвать рост wsrep_local_recv_queue на всех нодах.',
    },
    {
        id: 'diag-table-locks',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'Блокировки таблиц',
        badge: 'Warning',
        description:
            'Диагностика блокировок на уровне таблиц и строк. В Galera критично следить за длинными транзакциями — они блокируют применение write-sets на всех нодах.',
        code: '-- Активные блокировки:\nSELECT * FROM information_schema.INNODB_LOCKS;\n-- Ожидающие блокировки:\nSELECT * FROM information_schema.INNODB_LOCK_WAITS;',
    },
    {
        id: 'diag-disk-usage',
        tab: 'diagnostics',
        section: 'Панели',
        title: 'Размер баз данных',
        badge: 'Info',
        description:
            'Быстрый просмотр размеров баз данных и топ таблиц по размеру. Помогает спланировать место для SST и бэкапов.',
        code: '-- Размер всех БД:\nSELECT table_schema AS db,\n  ROUND(SUM(data_length + index_length)/1024/1024, 1) AS size_mb\nFROM information_schema.TABLES\nGROUP BY table_schema ORDER BY size_mb DESC;',
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
        id: 'arch-docker-compose',
        tab: 'architecture',
        section: 'Деплой',
        title: 'docker-compose пример',
        badge: 'Info',
        description:
            'Минимальный docker-compose.yml для запуска Galera Orchestrator v2. Монтирует SSH-ключ read-only и volume для SQLite.',
        code: 'services:\n  orchestrator:\n    image: galera-orchestrator-v2\n    ports:\n      - "8000:8000"\n    environment:\n      - FERNET_SECRET_KEY=your_fernet_key_here\n      - JWT_SECRET_KEY=your_jwt_secret_here\n    volumes:\n      - ./data:/data\n      - ~/.ssh/id_rsa:/root/.ssh/id_rsa:ro\n    restart: unless-stopped',
        note: 'Никогда не используй одинаковые FERNET_SECRET_KEY и JWT_SECRET_KEY на разных окружениях.',
    },
    {
        id: 'arch-sqlite',
        tab: 'architecture',
        section: 'Деплой',
        title: 'SQLite Volume',
        badge: 'Warning',
        description:
            'База данных SQLite хранится в /data/orchestrator.db внутри контейнера. Обязательно монтируй volume — без него все настройки теряются при пересоздании контейнера.',
        code: 'volumes:\n  - ./data:/data',
        note: 'Для резервного копирования достаточно скопировать файл orchestrator.db. SQLite поддерживает горячий бэкап через sqlite3 .backup.',
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
        id: 'arch-contours',
        tab: 'architecture',
        section: 'Структура данных',
        title: 'Contours & Datacenters',
        badge: 'Info',
        description:
            'Кластеры организованы по контурам (prod / stage / dev) и датацентрам. Контур — логическая группа, датацентр — физическое расположение ноды. Эти атрибуты используются для отображения топологии и выбора приоритетного донора при SST.',
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
    {
        id: 'arch-rolling-restart',
        tab: 'architecture',
        section: 'Операции',
        title: 'Rolling Restart — логика',
        badge: 'Warning',
        description:
            'Rolling restart перезапускает ноды по одной, чтобы сохранить кластер работоспособным. Порядок: сначала ноды DONOR/DESYNCED, затем SYNCED-ноды, в последнюю очередь — Primary-нода (с наибольшим seqno). Между каждым перезапуском ждёт возврата ноды в SYNCED.',
        note: 'Если нода не возвращается в SYNCED за отведённое время, rolling restart отменяется с ошибкой.',
    },
    {
        id: 'arch-backup-sqlite',
        tab: 'architecture',
        section: 'Деплой',
        title: 'Бэкап SQLite',
        badge: 'Info',
        description:
            'SQLite поддерживает онлайн-бэкап без остановки оркестратора. Файл orchestrator.db можно скопировать напрямую или использовать встроенную команду .backup.',
        code: '# Копирование файла (безопасно при работающем оркестраторе):\ncp /data/orchestrator.db /backup/orchestrator_$(date +%Y%m%d).db\n\n# Через sqlite3:\nsqlite3 /data/orchestrator.db ".backup /backup/orchestrator.db"',
        note: 'Рекомендуется делать бэкап перед обновлением версии оркестратора.',
    },
    {
        id: 'arch-env-vars',
        tab: 'architecture',
        section: 'Деплой',
        title: 'Переменные окружения',
        badge: 'Info',
        description:
            'Все секреты передаются через переменные окружения, не в конфиг-файлах. Обязательные: FERNET_SECRET_KEY (шифрование паролей в БД), JWT_SECRET_KEY (подпись токенов).',
        code: 'FERNET_SECRET_KEY=<base64-fernet-key>   # 44 символа\nJWT_SECRET_KEY=<random-string>           # >= 32 символа\nJWT_EXPIRE_MINUTES=60                    # опционально, дефолт 60\nPOLLING_INTERVAL=10                      # опционально, дефолт 10',
        note: 'Никогда не коммить секреты в репозиторий. Используй .env файл с .gitignore или Docker secrets.',
    },
    {
        id: 'arch-api-auth',
        tab: 'architecture',
        section: 'API',
        title: 'API — структура эндпоинтов',
        badge: 'Info',
        description:
            'Основные группы эндпоинтов: /api/auth/* (логин/логаут/me), /api/clusters/* (CRUD кластеров), /api/clusters/{id}/nodes/* (ноды), /api/clusters/{id}/status (polling), /api/clusters/{id}/operations/* (recovery, rolling restart).',
        code: 'GET  /api/auth/me\nPOST /api/auth/login\nPOST /api/auth/logout\nGET  /api/clusters/{id}/status\nPOST /api/clusters/{id}/operations/bootstrap\nPOST /api/clusters/{id}/operations/rolling-restart\nGET  /api/clusters/{id}/operations/{op_id}',
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
        id: 'ws-operation-progress',
        tab: 'websocket',
        section: 'Real-time',
        title: 'operation_progress payload',
        badge: 'Info',
        description:
            'Событие operation_progress транслирует шаги выполняемой операции (recovery, rolling restart). Содержит step, total, message и текущий статус.',
        code: '{\n  "event": "operation_progress",\n  "cluster_id": 1,\n  "ts": "2026-04-09T00:01:00Z",\n  "payload": {\n    "operation_id": 42,\n    "step": 2,\n    "total": 5,\n    "message": "Restarting node db-02...",\n    "status": "running"\n  }\n}',
    },
    {
        id: 'ws-auth',
        tab: 'websocket',
        section: 'Real-time',
        title: 'WS Auth Flow',
        badge: 'Info',
        description:
            'WebSocket-соединение устанавливается после успешного логина. Backend проверяет JWT из httpOnly cookie при handshake. Если токен истёк — соединение отклоняется с кодом 4401, frontend редиректит на /login.',
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
        section: 'Архитектура данных',
        title: 'Polling + WS модель',
        badge: 'Info',
        description:
            'Polling (интервал из system_settings) — source of truth для полного состояния нод. WebSocket — дельта-события для инкрементального обновления UI без перезапроса. Данные в ring buffer: 30 точек для спарклайнов.',
    },
    {
        id: 'ws-cluster-switch',
        tab: 'websocket',
        section: 'Архитектура данных',
        title: 'Смена кластера',
        badge: 'Info',
        description:
            'При переключении кластера в шапке: WS-соединение закрывается и открывается заново для нового cluster_id, все Vue Query кэши инвалидируются, ring buffer спарклайнов очищается. Данные нового кластера подгружаются с нуля.',
    },
    {
        id: 'ws-log-entry',
        tab: 'websocket',
        section: 'Real-time',
        title: 'log_entry event',
        badge: 'Info',
        description:
            'Событие log_entry приходит при записи новой строки в журнал операции. Используется для live-вывода прогресса в UI без отдельного polling лога.',
        code: '{\n  "event": "log_entry",\n  "cluster_id": 1,\n  "ts": "2026-04-09T00:01:05Z",\n  "payload": {\n    "operation_id": 42,\n    "level": "info",\n    "message": "Node db-02 reached SYNCED state"\n  }\n}',
    },
    {
        id: 'ws-ping-pong',
        tab: 'websocket',
        section: 'Real-time',
        title: 'Keepalive (ping/pong)',
        badge: 'Info',
        description:
            'Backend отправляет WebSocket ping каждые 30 сек для удержания соединения через NAT и прокси. Если pong не пришёл за 10 сек — соединение считается мёртвым и закрывается. Frontend переподключается автоматически.',
        note: 'При развёртывании за nginx добавь proxy_read_timeout 120s и proxy_send_timeout 120s для WS-локейшна.',
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
        id: 'faq-joiner-stuck',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Нода зависла в состоянии JOINER',
        badge: 'Warning',
        description:
            'Если нода долго остаётся в JOINER — идёт SST. При большой базе это может занять часы. Проверь прогресс SST на доноре: он будет в состоянии DONOR/DESYNCED. Если SST прервался — нода перезапустится и начнёт заново.',
        code: '-- На доноре:\nSHOW STATUS LIKE "wsrep_local_state_comment";\n-- Должно быть: Donor/Desynced\n\n-- Прогресс SST в логах:\ntail -f /var/log/mysql/error.log | grep -i sst',
        note: 'Если SST использует rsync — донор заблокирует запись на всё время передачи. Рассмотри переход на mariabackup как SST-метод.',
    },
    {
        id: 'faq-add-node',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Как добавить новую ноду?',
        badge: 'Info',
        description:
            'Добавить ноду в Settings → Nodes → Add Node. Укажи IP, порт, пользователя MySQL и SSH. После сохранения нода появится в топологии. Для подключения к кластеру запусти MariaDB на новой ноде с правильным wsrep_cluster_address — она автоматически выполнит SST.',
        note: 'Убедись что новая нода имеет доступ к SSH-ключу (authorized_keys) и открытые порты: 3306 (MySQL), 4567 (Galera), 4568 (IST), 4444 (SST).',
    },
    {
        id: 'faq-maintenance',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Что делает Maintenance Mode?',
        badge: 'Warning',
        description:
            'Maintenance Mode переводит ноду в read_only=1 и устанавливает флаг maintenance=true в БД оркестратора. Нода остаётся в кластере и продолжает репликацию, но не принимает запись от клиентов. Используй перед обслуживанием сервера.',
        note: 'Maintenance Drift — аномалия: maintenance=true, но read_only=0. Оркестратор помечает такую ноду как degraded.',
    },
    {
        id: 'faq-garbd',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Что такое garbd (арбитратор)?',
        badge: 'Info',
        description:
            'garbd (Galera Arbitrator) — лёгкий демон, который участвует в голосовании за кворум, но не хранит данные и не выполняет репликацию. Используется в кластерах с чётным числом нод (2, 4) для предотвращения split-brain.',
        code: '# Запуск garbd:\ngarbd --address gcomm://node1:4567,node2:4567 \\\n      --group my_cluster_name \\\n      --log /var/log/garbd.log',
        note: 'garbd не является заменой полноценной ноды. При падении всех нод garbd не поможет с восстановлением.',
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
        id: 'faq-ports',
        tab: 'faq',
        section: 'Критические ситуации',
        title: 'Нужные порты для Galera',
        badge: 'Warning',
        description:
            'Убедись что между всеми нодами открыты необходимые порты. Блокировка любого из них вызовет проблемы с репликацией или SST.',
        code: '3306  — MySQL клиент\n4567  — Galera репликация (TCP+UDP)\n4568  — IST (Incremental State Transfer)\n4444  — SST (rsync / mariabackup)',
        note: 'Для garbd нужен только порт 4567.',
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
    {
        id: 'faq-cluster-address',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Что такое wsrep_cluster_address?',
        badge: 'Info',
        description:
            'wsrep_cluster_address — список IP-адресов нод кластера в формате gcomm://. При старте нода подключается к любому из перечисленных адресов и получает актуальный список участников.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"\n\n# Первый старт кластера (bootstrap):\nwsrep_cluster_address="gcomm://"',
        note: 'gcomm:// (пустой) означает запуск нового кластера. Используй только при Bootstrap, затем верни полный список.',
    },
    {
        id: 'faq-remove-node',
        tab: 'faq',
        section: 'Частые вопросы',
        title: 'Как удалить ноду из кластера?',
        badge: 'Warning',
        description:
            'Чтобы корректно вывести ноду: 1) останови MariaDB на ноде (systemctl stop), 2) убедись что кворум сохранился (wsrep_cluster_size уменьшилось), 3) удали ноду в Settings → Nodes. Кластер продолжит работу без неё.',
        note: 'Обнови wsrep_cluster_address на оставшихся нодах, убрав IP удалённой ноды — иначе при каждом старте будут timeout-ошибки подключения.',
    },
    {
        id: 'faq-nginx-ws',
        tab: 'faq',
        section: 'Критические ситуации',
        title: 'WebSocket не работает за nginx',
        badge: 'Warning',
        description:
            'При проксировании через nginx WebSocket-соединения требуют явной настройки upgrade-заголовков. Без них соединение устанавливается как обычный HTTP и сразу закрывается.',
        code: 'location /ws/ {\n    proxy_pass http://orchestrator:8000;\n    proxy_http_version 1.1;\n    proxy_set_header Upgrade $http_upgrade;\n    proxy_set_header Connection "upgrade";\n    proxy_set_header Host $host;\n    proxy_read_timeout 120s;\n    proxy_send_timeout 120s;\n}',
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
