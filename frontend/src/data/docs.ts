// src/data/docs.ts
// Static documentation content — no API calls, no polling

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
            'Start MariaDB (and the Galera node) via systemd. The node will begin the Joiner procedure — attempting IST or SST from a donor.',
        code: 'systemctl start mariadb.service',
        note: 'If the entire cluster is stopped, starting a single node in normal mode may fail. Use Bootstrap instead.',
    },
    {
        id: 'svc-stop',
        tab: 'service',
        section: 'MariaDB',
        title: 'Stop',
        badge: 'Danger',
        description:
            'Stop MariaDB on the node. The node will leave the cluster (wsrep_cluster_size decreases). Other nodes continue operating as long as quorum is maintained.',
        code: 'systemctl stop mariadb.service',
        note: 'Stopping the last node causes the cluster to lose its Primary Component. Maintain the correct shutdown order.',
    },
    {
        id: 'svc-restart',
        tab: 'service',
        section: 'MariaDB',
        title: 'Restart',
        badge: 'Warning',
        description:
            'Restart MariaDB with a brief node downtime. The node will enter Joiner state and perform IST if the seqno gap is small enough, otherwise SST.',
        code: 'systemctl restart mariadb.service',
    },
    {
        id: 'svc-rejoin',
        tab: 'service',
        section: 'MariaDB',
        title: 'Rejoin (Force)',
        badge: 'Action',
        description:
            'Force-restart the node to reconnect it to the cluster via UI. Equivalent to systemctl restart mariadb. Use when a node is stuck in OFFLINE or DESYNCED state.',
        note: 'For a full cluster recovery use the Recovery page.',
    },
    {
        id: 'svc-status',
        tab: 'service',
        section: 'MariaDB',
        title: 'Status Check',
        badge: 'Info',
        description:
            'Check the MariaDB systemd unit status. Shows whether the process is active, its PID, recent log lines, and last start time.',
        code: 'systemctl status mariadb.service\n# quick check:\nsystemctl is-active mariadb.service',
    },
    {
        id: 'svc-enable',
        tab: 'service',
        section: 'MariaDB',
        title: 'Enable / Disable Autostart',
        badge: 'Warning',
        description:
            'Enable or disable automatic MariaDB startup on OS boot. Without enable, the node will not come up after a server reboot.',
        code: 'systemctl enable mariadb.service   # enable autostart\nsystemctl disable mariadb.service  # disable autostart',
        note: 'Always keep enable active on production nodes.',
    },
    {
        id: 'svc-new-cluster',
        tab: 'service',
        section: 'MariaDB',
        title: 'galera_new_cluster',
        badge: 'Danger',
        description:
            'Special command for initial cluster startup or Bootstrap after a full crash. Starts MariaDB with --wsrep-new-cluster, making the node the Primary Component.',
        code: 'galera_new_cluster\n# or directly:\nmysqld_safe --wsrep-new-cluster &',
        note: 'Use only on one node — the one with the highest seqno. The Recovery Wizard does this automatically.',
    },
    {
        id: 'svc-ro',
        tab: 'service',
        section: 'Read Mode',
        title: 'Set Read-Only',
        badge: 'Warning',
        description:
            'Put the node into read-only mode via SQL. The node continues processing SELECT queries but rejects DML.',
        code: 'SET GLOBAL read_only = 1;\n-- or\nSET GLOBAL super_read_only = 1;',
        note: 'Does not affect Galera replication — write-sets from other nodes are still applied.',
    },
    {
        id: 'svc-rw',
        tab: 'service',
        section: 'Read Mode',
        title: 'Set Read-Write',
        badge: 'Safe',
        description:
            'Remove the read-only flag from the node, making it writable again.',
        code: 'SET GLOBAL read_only = 0;\nSET GLOBAL super_read_only = 0;',
    },
    {
        id: 'svc-ping',
        tab: 'service',
        section: 'Diagnostics',
        title: 'Ping (Test Connection)',
        badge: 'Info',
        description:
            'Check node reachability via SSH and DB connection. Returns SSH status, DB status, and measured latency for each.',
        note: 'SSH timeout — 5 sec, DB timeout — 3 sec.',
    },
    {
        id: 'svc-wsrep-status',
        tab: 'service',
        section: 'Diagnostics',
        title: 'Quick Galera Status Check',
        badge: 'Info',
        description:
            'Minimal set of SQL queries for manual node and cluster diagnostics directly in the console.',
        code: "SHOW STATUS LIKE 'wsrep_cluster_status';\nSHOW STATUS LIKE 'wsrep_local_state_comment';\nSHOW STATUS LIKE 'wsrep_cluster_size';\nSHOW STATUS LIKE 'wsrep_connected';\nSHOW STATUS LIKE 'wsrep_ready';",
    },
    {
        id: 'svc-journal',
        tab: 'service',
        section: 'Diagnostics',
        title: 'View MariaDB Logs',
        badge: 'Info',
        description:
            'View the MariaDB system journal via journald. Essential for diagnosing startup issues, SST problems, and replication errors.',
        code: '# Last 100 lines:\njournalctl -u mariadb -n 100 --no-pager\n\n# Live stream:\njournalctl -u mariadb -f\n\n# Filtered by time:\njournalctl -u mariadb --since "1 hour ago"',
    },
    {
        id: 'svc-flush-logs',
        tab: 'service',
        section: 'MariaDB',
        title: 'FLUSH LOGS / Binary Log',
        badge: 'Warning',
        description:
            'Force binary log rotation. Used before a backup or to reduce the size of the current binlog file.',
        code: "FLUSH BINARY LOGS;\n-- Check current binlog:\nSHOW MASTER STATUS;\n-- Purge old binlogs up to a specific file:\nPURGE BINARY LOGS TO 'mariadb-bin.000100';",
        note: 'In Galera, binlog is not used for inter-node replication, but may be needed for external async replicas.',
    },

    // ── Tab: recovery ────────────────────────────────────────────────────────
    {
        id: 'rec-bootstrap-wizard',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Bootstrap Wizard',
        badge: 'Danger',
        description:
            'Step-by-step cluster recovery wizard for a full shutdown (all nodes OFFLINE). Reads grastate.dat and seqno from each node, identifies the most up-to-date one, and promotes it to Primary Component via `pc.bootstrap=1`.',
        note: 'Use only when the cluster is completely down. Running Bootstrap on a healthy cluster will cause split-brain.',
    },
    {
        id: 'rec-non-primary-fix',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Non-Primary Fix',
        badge: 'Danger',
        description:
            'Force-set a node as Primary Component via wsrep provider option. Used when the cluster is stuck in non-Primary state (wsrep_cluster_status != PRIMARY).',
        code: "SET GLOBAL wsrep_provider_options='pc.bootstrap=1';",
        note: 'Make sure only one node receives this status. Parallel bootstrap on two nodes creates split-brain.',
    },
    {
        id: 'rec-wsrep-recover',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'wsrep-recover-all',
        badge: 'Danger',
        description:
            'Start MariaDB in wsrep-recover mode to retrieve the last seqno without joining the cluster. Used to identify the most up-to-date node before Bootstrap.',
        code: 'mysqld_safe --wsrep-recover 2>&1 | grep "Recovered position"',
    },
    {
        id: 'rec-grastate',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'grastate.dat',
        badge: 'Danger',
        description:
            'Galera state file — stores cluster UUID, seqno, and the safe_to_bootstrap flag. safe_to_bootstrap=1 means the node was the last one to shut down cleanly.',
        code: 'cat /var/lib/mysql/grastate.dat',
        note: 'Never edit safe_to_bootstrap manually without understanding the consequences.',
    },
    {
        id: 'rec-quorum',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Quorum & Formula',
        badge: 'Warning',
        description:
            'Galera requires quorum for Primary Component operation: more than half of the nodes must be available. For 3 nodes: minimum 2; for 5 nodes: minimum 3. An arbitrator (garbd) counts toward quorum but does not store data.',
        note: 'Formula: quorum = ⌊N/2⌋ + 1. With an even number of nodes and no arbitrator — split-brain risk on 50/50 network partition.',
    },
    {
        id: 'rec-evict',
        tab: 'recovery',
        section: 'Bootstrap',
        title: 'Evict Node',
        badge: 'Danger',
        description:
            'Forcibly remove a node from the cluster via wsrep provider. Used when a node is "stuck" in the cluster and blocking quorum but not responding.',
        code: "-- Run on a live node:\nSET GLOBAL wsrep_provider_options='evs.evict=<node-uuid>';",
        note: 'Find the node UUID in wsrep_gcomm_uuid or in the MariaDB logs.',
    },
    {
        id: 'rec-sst',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'SST Warning',
        badge: 'Warning',
        description:
            'State Snapshot Transfer — full data copy from donor to Joiner. Takes a long time on large databases. During SST the donor is marked as DONOR/DESYNCED and does not accept writes.',
        note: 'Prefer IST by keeping gcache large enough (wsrep_provider_options: gcache.size).',
    },
    {
        id: 'rec-ist',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'IST vs SST',
        badge: 'Info',
        description:
            'Incremental State Transfer — transfers only missed transactions via gcache. Fast and low-impact on the donor. Only possible if the node\'s lag fits within the donor\'s gcache size.',
    },
    {
        id: 'rec-gcache',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'gcache.size — Tuning',
        badge: 'Info',
        description:
            'gcache (Galera Write-Set Cache) stores recent transactions for IST. The larger the gcache, the longer a node can be offline and still rejoin via IST instead of SST.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_provider_options="gcache.size=512M"',
        note: 'For high-load clusters, 1–2 GB is recommended. gcache is stored at /var/lib/mysql/galera.cache.',
    },
    {
        id: 'rec-rejoin',
        tab: 'recovery',
        section: 'Rejoin',
        title: 'Rejoin Node',
        badge: 'Action',
        description:
            'Reconnect a single node to a running cluster by restarting MariaDB. Unlike Bootstrap — the cluster already has a Primary Component.',
        code: 'systemctl restart mariadb.service',
    },
    {
        id: 'rec-sst-mariabackup',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'SST via mariabackup',
        badge: 'Info',
        description:
            'mariabackup is the recommended SST method. Unlike rsync, it does not block writes on the donor during transfer (hot backup). Requires the mariadb-backup package on all nodes.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_sst_method=mariabackup\nwsrep_sst_auth=sst_user:password',
        note: 'Create a dedicated SST user: GRANT RELOAD, PROCESS, LOCK TABLES, REPLICATION CLIENT ON *.* TO sst_user@localhost;',
    },
    {
        id: 'rec-donor-selection',
        tab: 'recovery',
        section: 'State Transfer',
        title: 'Preferred SST Donor',
        badge: 'Info',
        description:
            'By default Galera selects the SST donor automatically. You can specify a preferred donor explicitly to avoid putting load on a production node.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_sst_donor=db-02,db-03',
        note: 'Comma-separated list — Galera tries them in order. Falls back to any available donor if the listed ones are unreachable.',
    },

    // ── Tab: variables ───────────────────────────────────────────────────────
    {
        id: 'var-clustersize',
        tab: 'variables',
        section: 'Cluster State',
        title: 'wsrep_cluster_size',
        badge: 'Info',
        description:
            'Current number of nodes in the cluster. Should match the expected node count. A decrease indicates a node loss.',
    },
    {
        id: 'var-clusterstatus',
        tab: 'variables',
        section: 'Cluster State',
        title: 'wsrep_cluster_status',
        badge: 'Info',
        description:
            'Component status: PRIMARY (quorum exists, writes allowed) or non-Primary (quorum lost, writes blocked). non-Primary is a critical indicator.',
    },
    {
        id: 'var-clusteruuid',
        tab: 'variables',
        section: 'Cluster State',
        title: 'wsrep_cluster_state_uuid',
        badge: 'Info',
        description:
            'Cluster UUID — unique identifier of the Galera cluster. Must be identical on all nodes. A UUID mismatch means a node joined the wrong cluster or grastate is corrupted.',
        code: "SHOW STATUS LIKE 'wsrep_cluster_state_uuid';",
    },
    {
        id: 'var-localstate',
        tab: 'variables',
        section: 'Node State',
        title: 'wsrep_local_state_comment',
        badge: 'Info',
        description:
            'Human-readable node state: Synced (fully in cluster), Joiner (receiving data), Donor (providing SST), Desynced (temporarily disconnected from the replication stream).',
    },
    {
        id: 'var-connected',
        tab: 'variables',
        section: 'Node State',
        title: 'wsrep_connected',
        badge: 'Info',
        description:
            'ON — node is connected to the cluster via the wsrep provider. OFF — node is isolated.',
    },
    {
        id: 'var-ready',
        tab: 'variables',
        section: 'Node State',
        title: 'wsrep_ready',
        badge: 'Info',
        description:
            'ON — node accepts SQL queries and participates in replication. OFF — node is not ready (e.g., during SST or after quorum loss).',
    },
    {
        id: 'var-flowcontrol',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_flow_control_paused',
        badge: 'Warning',
        description:
            'Fraction of time (0–1) that replication was paused due to Flow Control. A value > 0.1 (10%) means a slow node is throttling the entire cluster.',
        note: 'Find the node with a large wsrep_local_recv_queue — it is the one triggering FC.',
    },
    {
        id: 'var-recvqueue',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_local_recv_queue',
        badge: 'Warning',
        description:
            'Queue of incoming transactions waiting to be applied. A non-zero value indicates node lag. A growing queue is a sign of apply pressure or a slow disk.',
    },
    {
        id: 'var-sendqueue',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_local_send_queue',
        badge: 'Info',
        description:
            'Queue of transactions waiting to be sent to other nodes. Normally 0. Growth indicates network issues or overload.',
    },
    {
        id: 'var-lastcommitted',
        tab: 'variables',
        section: 'Replication Flow',
        title: 'wsrep_last_committed',
        badge: 'Info',
        description:
            'Sequence number of the last applied transaction. Used to compare node freshness during Bootstrap.',
    },
    {
        id: 'var-certdeps',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_cert_deps_distance',
        badge: 'Info',
        description:
            'Average distance between transactions that can be applied in parallel. A higher value means Galera is parallelizing transaction apply more effectively. A value < 1 means fully sequential apply.',
        note: 'To increase parallelism, raise wsrep_slave_threads (up to the number of CPU cores).',
    },
    {
        id: 'var-slavethreads',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_slave_threads',
        badge: 'Info',
        description:
            'Number of threads applying incoming write-sets from other nodes. Recommended: equal to or twice the number of CPU cores. Default is 1.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_slave_threads = 4',
        note: 'Check wsrep_cert_deps_distance — if > 1, threads are actually parallelizing.',
    },
    {
        id: 'var-causalreads',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_causal_reads / wsrep_sync_wait',
        badge: 'Warning',
        description:
            'wsrep_sync_wait (newer) or wsrep_causal_reads (deprecated) — forces the node to wait for all incoming transactions to be applied before executing a SELECT. Eliminates dirty reads but adds latency.',
        code: 'SET SESSION wsrep_sync_wait = 1;  -- for SELECT\nSET SESSION wsrep_sync_wait = 3;  -- for SELECT + UPDATE',
        note: 'Use only where strict consistency is required. Enabling globally severely degrades performance.',
    },
    {
        id: 'var-applyoooe',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_apply_oooe',
        badge: 'Info',
        description:
            'Fraction of transactions applied out-of-order (OOOE). A higher value means parallel apply is working effectively. A value of 0 means strictly sequential apply.',
    },
    {
        id: 'var-repl-max-ws-size',
        tab: 'variables',
        section: 'Performance',
        title: 'wsrep_max_ws_size',
        badge: 'Warning',
        description:
            'Maximum write-set size for a single transaction (default 2 GB). Transactions exceeding this limit are rejected by Galera with an error. Relevant for bulk operations.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_max_ws_size=2G',
        note: 'Break large UPDATE/DELETE into batches of 1k–10k rows — this reduces load on the entire replication pipeline.',
    },
    {
        id: 'var-gcache-recover',
        tab: 'variables',
        section: 'Performance',
        title: 'gcache.recover',
        badge: 'Info',
        description:
            'Allows reusing gcache after a node restart instead of fully resetting it. Speeds up reconnection via IST after a planned shutdown.',
        code: 'wsrep_provider_options="gcache.recover=yes; gcache.size=1G"',
        note: 'Available in MariaDB 10.4+. On older versions, gcache is reset on every restart.',
    },

    // ── Tab: diagnostics ─────────────────────────────────────────────────────
    {
        id: 'diag-conncheck',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'Connection Check',
        badge: 'Info',
        description:
            'Parallel SSH and DB connection check for all cluster nodes and arbitrators. Shows SSH status, MariaDB status, and latency. Triggered manually (not polling).',
    },
    {
        id: 'diag-configdiff',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'Config Diff',
        badge: 'Info',
        description:
            'Compare wsrep variables (SHOW GLOBAL VARIABLES LIKE "wsrep%") across all nodes. Configuration deviations between nodes are displayed as diff lines.',
    },
    {
        id: 'diag-innodb',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'InnoDB Status',
        badge: 'Warning',
        description:
            'Output of SHOW ENGINE INNODB STATUS for the selected node. Contains the LATEST DETECTED DEADLOCK section, transaction log, and buffer pool stats. Useful for diagnosing lock contention.',
        code: 'SHOW ENGINE INNODB STATUS\\G',
    },
    {
        id: 'diag-resources',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'System Resources',
        badge: 'Info',
        description:
            'CPU load avg, RAM (used/total), Disk usage (/), and Uptime per node via SSH (/proc/loadavg, free -b, df -B1 /).',
        note: 'CPU > 80% — Warning, > 95% — Danger. RAM > 85% — Warning. Disk > 80% — Warning.',
    },
    {
        id: 'diag-arblog',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'Arbitrator Log',
        badge: 'Info',
        description:
            'Last N lines of the garbd log via SSH (journalctl -u garbd or tail /var/log/garbd.log). Useful for diagnosing arbitrator issues.',
        code: 'journalctl -u garbd -n 100 --no-pager',
    },
    {
        id: 'diag-variables',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'SHOW GLOBAL VARIABLES',
        badge: 'Info',
        description:
            'Full SHOW GLOBAL VARIABLES output filtered by wsrep variables (or any substring). Key-value table with search.',
        code: "SHOW GLOBAL VARIABLES WHERE Variable_name LIKE 'wsrep%';",
    },
    {
        id: 'diag-checkall',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'Check All',
        badge: 'Action',
        description:
            'Run all diagnostic checks simultaneously: connection check, config diff, system resources. Results are aggregated into a single report. Convenient for a quick health check before maintenance.',
    },
    {
        id: 'diag-deadlock',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'Deadlock Detection',
        badge: 'Warning',
        description:
            'Galera uses optimistic locking — transaction conflicts are detected at commit time, not at read time. This means two clients can update the same row, but the second will receive a Deadlock error on commit.',
        code: '-- Find the last deadlock:\nSHOW ENGINE INNODB STATUS\\G\n-- Section: LATEST DETECTED DEADLOCK',
        note: 'Galera adds its own conflict type: wsrep_conflict. Check wsrep_local_cert_failures for statistics.',
    },
    {
        id: 'diag-certfailures',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'wsrep_local_cert_failures',
        badge: 'Warning',
        description:
            'Counter of transactions rejected at the Galera certification stage (write-set conflict). A growing counter indicates high contention on the same rows across nodes.',
        code: "SHOW STATUS LIKE 'wsrep_local_cert_failures';",
    },
    {
        id: 'diag-processlist',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'Active Queries',
        badge: 'Info',
        description:
            'View all active connections and running queries. Useful for detecting long transactions that may block Galera replication.',
        code: "SHOW FULL PROCESSLIST;\n-- Only long-running queries (> 5 sec):\nSELECT * FROM information_schema.PROCESSLIST\nWHERE TIME > 5 AND COMMAND != 'Sleep'\nORDER BY TIME DESC;",
        note: 'Long uncommitted transactions can cause wsrep_local_recv_queue growth on all nodes.',
    },
    {
        id: 'diag-table-locks',
        tab: 'diagnostics',
        section: 'InnoDB',
        title: 'Table & Row Locks',
        badge: 'Warning',
        description:
            'Diagnose table-level and row-level locks. In Galera, long transactions are critical — they block write-set apply on all nodes.',
        code: '-- Active locks:\nSELECT * FROM information_schema.INNODB_LOCKS;\n-- Waiting locks:\nSELECT * FROM information_schema.INNODB_LOCK_WAITS;',
    },
    {
        id: 'diag-disk-usage',
        tab: 'diagnostics',
        section: 'Panels',
        title: 'Database Sizes',
        badge: 'Info',
        description:
            'Quick overview of database sizes and top tables by size. Helps plan disk space for SST and backups.',
        code: '-- Size of all databases:\nSELECT table_schema AS db,\n  ROUND(SUM(data_length + index_length)/1024/1024, 1) AS size_mb\nFROM information_schema.TABLES\nGROUP BY table_schema ORDER BY size_mb DESC;',
    },

    // ── Tab: architecture ────────────────────────────────────────────────────
    {
        id: 'arch-overview',
        tab: 'architecture',
        section: 'Deployment',
        title: 'Single Container',
        badge: 'Info',
        description:
            'Galera Orchestrator v2 runs in a single Docker container. FastAPI serves the built Vue 3 SPA and REST API. SQLite is stored on a volume at /data/orchestrator.db.',
    },
    {
        id: 'arch-docker-compose',
        tab: 'architecture',
        section: 'Deployment',
        title: 'docker-compose Example',
        badge: 'Info',
        description:
            'Minimal docker-compose.yml for running Galera Orchestrator v2. Mounts the SSH key read-only and a volume for SQLite.',
        code: 'services:\n  orchestrator:\n    image: galera-orchestrator-v2\n    ports:\n      - "8000:8000"\n    environment:\n      - FERNET_SECRET_KEY=your_fernet_key_here\n      - JWT_SECRET_KEY=your_jwt_secret_here\n    volumes:\n      - ./data:/data\n      - ~/.ssh/id_rsa:/root/.ssh/id_rsa:ro\n    restart: unless-stopped',
        note: 'Never use the same FERNET_SECRET_KEY and JWT_SECRET_KEY across different environments.',
    },
    {
        id: 'arch-sqlite',
        tab: 'architecture',
        section: 'Deployment',
        title: 'SQLite Volume',
        badge: 'Warning',
        description:
            'The SQLite database is stored at /data/orchestrator.db inside the container. Always mount a volume — without it all settings are lost when the container is recreated.',
        code: 'volumes:\n  - ./data:/data',
        note: 'To back up, simply copy the orchestrator.db file. SQLite supports hot backup via sqlite3 .backup.',
    },
    {
        id: 'arch-fernet',
        tab: 'architecture',
        section: 'Security',
        title: 'Password Encryption (Fernet)',
        badge: 'Info',
        description:
            'MariaDB node passwords are stored in SQLite in encrypted form (Fernet symmetric encryption). The key is set via the FERNET_SECRET_KEY environment variable. Changing the key will make existing passwords unreadable.',
        note: 'Generate a key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',
    },
    {
        id: 'arch-ssh',
        tab: 'architecture',
        section: 'SSH',
        title: 'SSH Key (Global)',
        badge: 'Warning',
        description:
            'A single global SSH key is used for all nodes and arbitrators. The key is mounted into the container read-only at /root/.ssh/id_rsa. Never stored in the database.',
        code: '# docker-compose.yml\nvolumes:\n  - ~/.ssh/id_rsa:/root/.ssh/id_rsa:ro',
        note: 'SSH connection timeout — 5 sec. Command execution timeout — 10 sec.',
    },
    {
        id: 'arch-auth',
        tab: 'architecture',
        section: 'Security',
        title: 'JWT in httpOnly Cookie',
        badge: 'Info',
        description:
            'Authentication via JWT stored only in an httpOnly cookie. JavaScript cannot access the token. The session is validated via GET /api/auth/me.',
    },
    {
        id: 'arch-cluster-scope',
        tab: 'architecture',
        section: 'API',
        title: 'Cluster-scoped API',
        badge: 'Info',
        description:
            'All endpoints are scoped to cluster_id: /api/clusters/{cluster_id}/... This ensures data isolation between clusters. When the cluster is switched in the header, all Vue Query caches are invalidated.',
    },
    {
        id: 'arch-contours',
        tab: 'architecture',
        section: 'Data Structure',
        title: 'Contours & Datacenters',
        badge: 'Info',
        description:
            'Clusters are organized by contours (prod / stage / dev) and datacenters. A contour is a logical group; a datacenter is the physical location of a node. These attributes are used for topology visualization and preferred donor selection during SST.',
    },
    {
        id: 'arch-lock',
        tab: 'architecture',
        section: 'Operations',
        title: 'Cluster-level Lock',
        badge: 'Warning',
        description:
            'While a recovery or rolling restart is running, the cluster is locked — starting a second operation in parallel returns 409 Conflict. Lock status is visible in the activeOperation field of the status endpoint.',
    },
    {
        id: 'arch-rolling-restart',
        tab: 'architecture',
        section: 'Operations',
        title: 'Rolling Restart — Logic',
        badge: 'Warning',
        description:
            'Rolling restart restarts nodes one at a time to keep the cluster operational. Order: DONOR/DESYNCED nodes first, then SYNCED nodes, and finally the Primary node (with the highest seqno). Waits for each node to return to SYNCED before proceeding.',
        note: 'If a node does not return to SYNCED within the allotted time, the rolling restart is cancelled with an error.',
    },
    {
        id: 'arch-backup-sqlite',
        tab: 'architecture',
        section: 'Deployment',
        title: 'SQLite Backup',
        badge: 'Info',
        description:
            'SQLite supports online backup without stopping the orchestrator. The orchestrator.db file can be copied directly or via the built-in .backup command.',
        code: '# File copy (safe while orchestrator is running):\ncp /data/orchestrator.db /backup/orchestrator_$(date +%Y%m%d).db\n\n# Via sqlite3:\nsqlite3 /data/orchestrator.db ".backup /backup/orchestrator.db"',
        note: 'Recommended to back up before updating the orchestrator version.',
    },
    {
        id: 'arch-env-vars',
        tab: 'architecture',
        section: 'Deployment',
        title: 'Environment Variables',
        badge: 'Info',
        description:
            'All secrets are passed via environment variables, not config files. Required: FERNET_SECRET_KEY (password encryption in DB), JWT_SECRET_KEY (token signing).',
        code: 'FERNET_SECRET_KEY=<base64-fernet-key>   # 44 characters\nJWT_SECRET_KEY=<random-string>           # >= 32 characters\nJWT_EXPIRE_MINUTES=60                    # optional, default 60\nPOLLING_INTERVAL=10                      # optional, default 10',
        note: 'Never commit secrets to the repository. Use an .env file with .gitignore or Docker secrets.',
    },
    {
        id: 'arch-api-auth',
        tab: 'architecture',
        section: 'API',
        title: 'API — Endpoint Structure',
        badge: 'Info',
        description:
            'Main endpoint groups: /api/auth/* (login/logout/me), /api/clusters/* (CRUD), /api/clusters/{id}/nodes/* (nodes), /api/clusters/{id}/status (polling), /api/clusters/{id}/operations/* (recovery, rolling restart).',
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
            'The frontend connects to WS /ws/clusters/{cluster_id}. Authorization via httpOnly cookie. The connection is re-established when switching clusters.',
    },
    {
        id: 'ws-events',
        tab: 'websocket',
        section: 'Real-time',
        title: 'Event Types',
        badge: 'Info',
        description:
            'node_state_changed, arbitrator_state_changed, operation_started, operation_progress, operation_finished, log_entry. Events are emitted when state changes are detected by polling or during operations.',
        code: '// Example event:\n{\n  "event": "node_state_changed",\n  "cluster_id": 1,\n  "ts": "2026-04-09T00:00:00Z",\n  "payload": {\n    "node_id": 2,\n    "old_state": "SYNCED",\n    "new_state": "OFFLINE"\n  }\n}',
    },
    {
        id: 'ws-operation-progress',
        tab: 'websocket',
        section: 'Real-time',
        title: 'operation_progress payload',
        badge: 'Info',
        description:
            'The operation_progress event streams steps of the running operation (recovery, rolling restart). Contains step, total, message, and current status.',
        code: '{\n  "event": "operation_progress",\n  "cluster_id": 1,\n  "ts": "2026-04-09T00:01:00Z",\n  "payload": {\n    "operation_id": 42,\n    "step": 2,\n    "total": 5,\n    "message": "Restarting node db-02...",\n    "status": "running"\n  }\n}',
    },
    {
        id: 'ws-auth',
        tab: 'websocket',
        section: 'Real-time',
        title: 'WS Auth Flow',
        badge: 'Info',
        description:
            'The WebSocket connection is established after a successful login. The backend validates the JWT from the httpOnly cookie during the handshake. If the token has expired — the connection is rejected with code 4401 and the frontend redirects to /login.',
    },
    {
        id: 'ws-reconnect',
        tab: 'websocket',
        section: 'Real-time',
        title: 'Reconnect',
        badge: 'Info',
        description:
            'When the WS connection drops, the Footer shows Disconnected status (red). The frontend automatically reconnects every 5 seconds.',
    },
    {
        id: 'ws-footer',
        tab: 'websocket',
        section: 'UI',
        title: 'Footer WS Indicator',
        badge: 'Info',
        description:
            'The footer displays the WebSocket connection status: Connected (green) / Reconnecting (yellow) / Disconnected (red). Managed via the Pinia ws store.',
    },
    {
        id: 'ws-wsrep',
        tab: 'websocket',
        section: 'Data Architecture',
        title: 'Polling + WS Model',
        badge: 'Info',
        description:
            'Polling (interval from system_settings) is the source of truth for full node state. WebSocket provides delta events for incremental UI updates without re-fetching. Data in ring buffer: 30 points for sparklines.',
    },
    {
        id: 'ws-cluster-switch',
        tab: 'websocket',
        section: 'Data Architecture',
        title: 'Cluster Switch',
        badge: 'Info',
        description:
            'When switching clusters in the header: the WS connection is closed and reopened for the new cluster_id, all Vue Query caches are invalidated, and the sparkline ring buffer is cleared. New cluster data is loaded from scratch.',
    },
    {
        id: 'ws-log-entry',
        tab: 'websocket',
        section: 'Real-time',
        title: 'log_entry event',
        badge: 'Info',
        description:
            'The log_entry event is emitted when a new line is written to the operation journal. Used for live progress output in the UI without separate log polling.',
        code: '{\n  "event": "log_entry",\n  "cluster_id": 1,\n  "ts": "2026-04-09T00:01:05Z",\n  "payload": {\n    "operation_id": 42,\n    "level": "info",\n    "message": "Node db-02 reached SYNCED state"\n  }\n}',
    },
    {
        id: 'ws-ping-pong',
        tab: 'websocket',
        section: 'Real-time',
        title: 'Keepalive (ping/pong)',
        badge: 'Info',
        description:
            'The backend sends a WebSocket ping every 30 seconds to keep the connection alive through NAT and proxies. If pong is not received within 10 seconds — the connection is considered dead and closed. The frontend reconnects automatically.',
        note: 'When deploying behind nginx, add proxy_read_timeout 120s and proxy_send_timeout 120s to the WS location block.',
    },

    // ── Tab: faq ──────────────────────────────────────────────────────────────
    {
        id: 'faq-restore',
        tab: 'faq',
        section: 'Common Questions',
        title: 'How to recover a crashed cluster?',
        badge: 'Info',
        description:
            'Go to the Recovery page. The wizard automatically reads grastate.dat from each node, identifies the most up-to-date one (by seqno and safe_to_bootstrap), and proposes a Bootstrap plan. Confirm and monitor the progress.',
    },
    {
        id: 'faq-joiner-stuck',
        tab: 'faq',
        section: 'Common Questions',
        title: 'Node stuck in JOINER state',
        badge: 'Warning',
        description:
            'If a node stays in JOINER for a long time — SST is in progress. On large databases this can take hours. Check SST progress on the donor: it will be in DONOR/DESYNCED state. If SST was interrupted — the node will restart and begin again.',
        code: '-- On the donor:\nSHOW STATUS LIKE "wsrep_local_state_comment";\n-- Should be: Donor/Desynced\n\n-- SST progress in logs:\ntail -f /var/log/mysql/error.log | grep -i sst',
        note: 'If SST uses rsync — the donor will block writes for the entire transfer duration. Consider switching to mariabackup as the SST method.',
    },
    {
        id: 'faq-add-node',
        tab: 'faq',
        section: 'Common Questions',
        title: 'How to add a new node?',
        badge: 'Info',
        description:
            'Add the node in Settings → Nodes → Add Node. Enter the IP, port, MySQL user, and SSH credentials. After saving, the node appears in the topology. To join the cluster, start MariaDB on the new node with the correct wsrep_cluster_address — it will automatically perform SST.',
        note: 'Make sure the new node has SSH key access (authorized_keys) and open ports: 3306 (MySQL), 4567 (Galera), 4568 (IST), 4444 (SST).',
    },
    {
        id: 'faq-maintenance',
        tab: 'faq',
        section: 'Common Questions',
        title: 'What does Maintenance Mode do?',
        badge: 'Warning',
        description:
            'Maintenance Mode sets read_only=1 and marks the node with maintenance=true in the orchestrator database. The node remains in the cluster and continues replication but does not accept client writes. Use before server maintenance.',
        note: 'Maintenance Drift — an anomaly: maintenance=true but read_only=0. The orchestrator marks such a node as degraded.',
    },
    {
        id: 'faq-garbd',
        tab: 'faq',
        section: 'Common Questions',
        title: 'What is garbd (Arbitrator)?',
        badge: 'Info',
        description:
            'garbd (Galera Arbitrator) is a lightweight daemon that participates in quorum voting but does not store data or perform replication. Used in clusters with an even number of nodes (2, 4) to prevent split-brain.',
        code: '# Start garbd:\ngarbd --address gcomm://node1:4567,node2:4567 \\\n      --group my_cluster_name \\\n      --log /var/log/garbd.log',
        note: 'garbd is not a substitute for a full node. When all nodes are down, garbd cannot assist with recovery.',
    },
    {
        id: 'faq-warning',
        tab: 'faq',
        section: 'Common Questions',
        title: 'When does a node go to Warning state?',
        badge: 'Warning',
        description:
            'A node is considered degraded (shown in orange) if: wsrep_ready=OFF, state is DONOR/JOINER/DESYNCED, or maintenance=true + read_only=0 (maintenance drift).',
    },
    {
        id: 'faq-splitbrain',
        tab: 'faq',
        section: 'Critical Situations',
        title: 'Split-brain',
        badge: 'Danger',
        description:
            'Split-brain occurs when two independent sets of nodes each believe they are the Primary Component. Usually caused by incorrect Bootstrap or a network partition. The cluster shows critical status. Requires manual intervention — stop all nodes except one, then Bootstrap.',
    },
    {
        id: 'faq-ports',
        tab: 'faq',
        section: 'Critical Situations',
        title: 'Required Ports for Galera',
        badge: 'Warning',
        description:
            'Make sure the required ports are open between all nodes. Blocking any of them will cause replication or SST issues.',
        code: '3306  — MySQL client\n4567  — Galera replication (TCP+UDP)\n4568  — IST (Incremental State Transfer)\n4444  — SST (rsync / mariabackup)',
        note: 'garbd only needs port 4567.',
    },
    {
        id: 'faq-ist-sst',
        tab: 'faq',
        section: 'Common Questions',
        title: 'When does IST happen vs SST?',
        badge: 'Info',
        description:
            "IST (fast) — if the Joiner node's lag is covered by the donor's gcache. SST (slow, full copy) — if gcache is insufficient or the node was offline too long. gcache size: wsrep_provider_options: gcache.size.",
    },
    {
        id: 'faq-polling',
        tab: 'faq',
        section: 'Common Questions',
        title: 'How to change the refresh interval?',
        badge: 'Info',
        description:
            'The polling interval is configured in Settings → System → Polling Interval (sec). Minimum recommended is 5 sec to avoid overloading nodes with diagnostic queries.',
    },
    {
        id: 'faq-cluster-address',
        tab: 'faq',
        section: 'Common Questions',
        title: 'What is wsrep_cluster_address?',
        badge: 'Info',
        description:
            'wsrep_cluster_address — a list of cluster node IP addresses in gcomm:// format. On startup, the node connects to any of the listed addresses and retrieves the current member list.',
        code: '# /etc/mysql/conf.d/galera.cnf\nwsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"\n\n# First cluster start (bootstrap):\nwsrep_cluster_address="gcomm://"',
        note: 'gcomm:// (empty) means starting a new cluster. Use only during Bootstrap, then restore the full list.',
    },
    {
        id: 'faq-remove-node',
        tab: 'faq',
        section: 'Common Questions',
        title: 'How to remove a node from the cluster?',
        badge: 'Warning',
        description:
            'To cleanly remove a node: 1) stop MariaDB on the node (systemctl stop), 2) verify quorum is maintained (wsrep_cluster_size decreased), 3) delete the node in Settings → Nodes. The cluster will continue operating without it.',
        note: 'Update wsrep_cluster_address on the remaining nodes, removing the IP of the deleted node — otherwise timeout errors will appear on every startup.',
    },
    {
        id: 'faq-nginx-ws',
        tab: 'faq',
        section: 'Critical Situations',
        title: 'WebSocket not working behind nginx',
        badge: 'Warning',
        description:
            'When proxying through nginx, WebSocket connections require explicit upgrade header configuration. Without it, the connection is treated as regular HTTP and immediately closed.',
        code: 'location /ws/ {\n    proxy_pass http://orchestrator:8000;\n    proxy_http_version 1.1;\n    proxy_set_header Upgrade $http_upgrade;\n    proxy_set_header Connection "upgrade";\n    proxy_set_header Host $host;\n    proxy_read_timeout 120s;\n    proxy_send_timeout 120s;\n}',
    },
]

// Tab render constants
export const DOC_TABS: { id: DocTab; label: string }[] = [
    { id: 'service',      label: 'MariaDB Service' },
    { id: 'recovery',     label: 'Recovery' },
    { id: 'variables',    label: 'wsrep Variables' },
    { id: 'diagnostics',  label: 'Diagnostics' },
    { id: 'architecture', label: 'Architecture' },
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
