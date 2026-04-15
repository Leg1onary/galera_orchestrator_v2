import { api } from '@/api/client'

// ── Config diff ──────────────────────────────────────────────────────────────────
export type ConfigDiffValueEntry = {
    node_id: number
    node_name: string
    value: string | null
    fetch_error: boolean
}

export type ConfigDiffRow = {
    variable: string
    values: ConfigDiffValueEntry[]
    has_diff: boolean
}

export type ConfigDiffResponse = {
    variables: ConfigDiffRow[]
    nodes: { node_id: number; node_name: string; host: string; fetch_ok: boolean }[]
    diff_found: boolean
}

// ── Variables ──────────────────────────────────────────────────────────────────
export type KVRow = {
    variable_name: string
    value: string
}

export type VariablesResult = Record<string, KVRow[]>

interface RawVariablesResult {
    node_id: number
    node_name: string
    host: string
    total: number
    variables: { name: string; value: string }[]
    error?: string | null
}

// ── Check all (connections) ────────────────────────────────────────────────────
export type ConnectionCheckRow = {
    node_id: number
    node_name: string
    arbitrator_name?: string
    host: string
    role: 'node' | 'arbitrator'
    ssh_ok: boolean | null
    db_ok: boolean | null
    ssh_latency_ms: number | null
    db_latency_ms: number | null
    ssh_error: string | null
    db_error: string | null
    garbd_running?: boolean | null
    latency_ssh_ms?: number | null
}

export type CheckAllResponse = {
    nodes: ConnectionCheckRow[]
    arbitrators: ConnectionCheckRow[]
}

interface RawArbCheckRow {
    arbitrator_id: number
    arbitrator_name: string
    host: string
    role: 'arbitrator'
    ssh_ok: boolean | null
    latency_ssh_ms: number | null
    ssh_error: string | null
    garbd_running?: boolean | null
}

interface RawCheckAllResponse {
    nodes: ConnectionCheckRow[]
    arbitrators: RawArbCheckRow[]
}

function normalizeArbRow(raw: RawArbCheckRow): ConnectionCheckRow {
    return {
        node_id:        raw.arbitrator_id,
        node_name:      raw.arbitrator_name,
        arbitrator_name: raw.arbitrator_name,
        host:           raw.host,
        role:           'arbitrator',
        ssh_ok:         raw.ssh_ok,
        db_ok:          null,
        ssh_latency_ms: raw.latency_ssh_ms,
        db_latency_ms:  null,
        ssh_error:      raw.ssh_error,
        db_error:       null,
        garbd_running:  raw.garbd_running ?? null,
        latency_ssh_ms: raw.latency_ssh_ms,
    }
}

// ── Resources ──────────────────────────────────────────────────────────────────
export type NodeResourceRow = {
    node_id: number
    node_name: string
    cpu_percent: number | null
    ram_used_bytes: number | null
    ram_total_bytes: number | null
    disk_used_bytes: number | null
    disk_total_bytes: number | null
    load_avg_1: number | null
    uptime_since: string | null
    error: string | null
}

interface RawResourceNode {
    node_id: number
    node_name: string
    host: string
    cpu_load: { load1: number; load5: number; load15: number } | null
    ram: { total_bytes: number; used_bytes: number; free_bytes: number; available_bytes: number | null } | null
    disk: { total_bytes: number; used_bytes: number; available_bytes: number; use_percent: string } | null
    uptime_since: string | null
    error: string | null
}

function normalizeResourceNode(raw: RawResourceNode): NodeResourceRow {
    return {
        node_id:         raw.node_id,
        node_name:       raw.node_name,
        load_avg_1:      raw.cpu_load?.load1 ?? null,
        cpu_percent:     raw.cpu_load ? Math.min(Math.round(raw.cpu_load.load1 * 100), 100) : null,
        ram_used_bytes:  raw.ram?.used_bytes ?? null,
        ram_total_bytes: raw.ram?.total_bytes ?? null,
        disk_used_bytes: raw.disk?.used_bytes ?? null,
        disk_total_bytes: raw.disk?.total_bytes ?? null,
        uptime_since:    raw.uptime_since,
        error:           raw.error,
    }
}

// ── Arbitrator log ──────────────────────────────────────────────────────────────
export type ArbitratorLogResult = {
    arbitrator_id: number
    arbitrator_name: string
    lines: string[]
    fetched_at: string
    error: string | null
}

// ── Arbitrator test connection ──────────────────────────────────────────────────
export type ArbitratorConnectionResult = {
    ssh_ok: boolean
    garbd_running: boolean
    latency_ssh_ms: number | null
}

// ── Galera status ──────────────────────────────────────────────────────────────
export type GaleraStatusNodeResult = {
    node_id: number
    node_name: string
    host: string
    status: Record<string, string>
    error: string | null
}

// ── Process list ──────────────────────────────────────────────────────────────
export type ProcessRow = {
    id: number
    user: string
    host: string
    db: string | null
    command: string
    time: number
    state: string | null
    info: string | null
}

export type ProcessListNodeResult = {
    node_id: number
    node_name: string
    error: string | null
    processes: ProcessRow[]
}

// ── Kill process result ────────────────────────────────────────────────────────
export type KillProcessResult = {
    ok: boolean
    process_id: number
    node_name: string
}

// ── Kill processes (bulk) result — #6 ─────────────────────────────────────────
export type KillProcessesFilter = 'sleep' | 'user'

export type KillProcessesBody = {
    filter: KillProcessesFilter
    min_time?: number
    user?: string
}

export type KillProcessesResult = {
    killed: number[]
    skipped: number
    errors: string[]
    node_name: string
}

// ── Slow query log ──────────────────────────────────────────────────────────────
export type SlowQueryRow = {
    start_time: string
    user_host: string
    query_time: string
    lock_time: string
    rows_sent: number
    rows_examined: number
    db: string | null
    sql_text: string
}

export type SlowQueryNodeResult = {
    node_id: number
    node_name: string
    slow_log_enabled: boolean | null
    rows: SlowQueryRow[]
    error: string | null
}

// ── Error log ──────────────────────────────────────────────────────────────────
export type ErrorLogResult = {
    node_id: number
    node_name: string
    lines: string[]
    fetched_at: string
    error: string | null
}

// ── Purge binary logs — #9 ─────────────────────────────────────────────────────
export type PurgeBinaryLogsBody = {
    mode: 'date' | 'days'
    before_date: string  // always a MySQL datetime string: 'YYYY-MM-DD HH:MM:SS'
}

export type PurgeBinaryLogsResult = {
    ok: boolean
    query_executed: string
    node_name: string
}

// ── Disk usage — #13 ───────────────────────────────────────────────────────────
export type DiskUsageTableRow = {
    schema: string
    table: string
    data_mb: number
    index_mb: number
    total_mb: number
}

export type DiskUsageBinaryLog = {
    log_name: string
    file_size: number
}

export type DiskUsageNodeResult = {
    node_id: number
    node_name: string
    top_tables: DiskUsageTableRow[]
    binary_logs: DiskUsageBinaryLog[]
    binary_logs_total_mb: number | null
    ibdata1_mb: number | null
    error: string | null
}

// ── SST Status — #11 ───────────────────────────────────────────────────────────
export type SstStatusItem = {
    node_id: number
    node_name: string
    state: string
    state_since_ts: string | null
    stuck_for_sec: number | null
    is_stuck: boolean
}

export type RestartSstResponse = {
    ok: boolean
    node_id: number
    message: string
}

// ── Active transactions — #15 ─────────────────────────────────────────────────
export type ActiveTrxRow = {
    trx_id: string
    trx_state: string
    trx_started: string
    trx_age_sec: number
    trx_mysql_thread_id: number
    trx_query: string | null
    trx_tables_locked: number
    trx_rows_locked: number
    trx_rows_modified: number
    user: string | null
}

export type ActiveTrxNodeResult = {
    node_id: number
    node_name: string
    transactions: ActiveTrxRow[]
    error: string | null
}

export const diagnosticsApi = {

    configDiff: (clusterId: number): Promise<ConfigDiffResponse> =>
        api
            .get<ConfigDiffResponse>(`/api/clusters/${clusterId}/diagnostics/config-diff`)
            .then((r) => r.data),

    variablesForNode: (clusterId: number, nodeId: number, wsrepOnly = false): Promise<KVRow[]> =>
        api
            .get<RawVariablesResult>(`/api/clusters/${clusterId}/diagnostics/variables`, {
                params: { node_id: nodeId, wsrep_only: wsrepOnly },
            })
            .then((r) => r.data.variables.map((v) => ({ variable_name: v.name, value: v.value }))),

    variablesAll: (clusterId: number, wsrepOnly = false): Promise<RawVariablesResult[]> =>
        api
            .get<RawVariablesResult[]>(`/api/clusters/${clusterId}/diagnostics/variables/all`, {
                params: { wsrep_only: wsrepOnly },
            })
            .then((r) => r.data),

    checkAll: (clusterId: number): Promise<CheckAllResponse> =>
        api
            .post<RawCheckAllResponse>(`/api/clusters/${clusterId}/diagnostics/check-all`)
            .then((r) => ({
                nodes:        r.data.nodes,
                arbitrators:  r.data.arbitrators.map(normalizeArbRow),
            })),

    resources: (clusterId: number): Promise<NodeResourceRow[]> =>
        api
            .post<{ nodes: RawResourceNode[] }>(`/api/clusters/${clusterId}/diagnostics/resources`)
            .then((r) => r.data.nodes.map(normalizeResourceNode)),

    arbitratorLog: (clusterId: number, arbitratorId: number, lines: 20 | 50 | 100 = 50) =>
        api
            .get<ArbitratorLogResult>(
                `/api/clusters/${clusterId}/arbitrators/${arbitratorId}/log`,
                { params: { lines } },
            )
            .then((r) => r.data),

    arbitratorTestConnection: (clusterId: number, arbitratorId: number) =>
        api
            .get<ArbitratorConnectionResult>(
                `/api/clusters/${clusterId}/arbitrators/${arbitratorId}/test-connection`,
            )
            .then((r) => r.data),

    innodbStatus: (clusterId: number, nodeId: number) =>
        api
            .get(`/api/clusters/${clusterId}/nodes/${nodeId}/innodb-status`)
            .then((r) => r.data),

    getGaleraStatus: (clusterId: number) =>
        api
            .get<GaleraStatusNodeResult[]>(`/api/clusters/${clusterId}/diagnostics/galera-status`)
            .then((r) => r.data),

    getProcessList: (clusterId: number, nodeId?: number) =>
        api
            .get<ProcessListNodeResult[]>(
                `/api/clusters/${clusterId}/diagnostics/process-list`,
                { params: nodeId !== undefined ? { node_id: nodeId } : {} },
            )
            .then((r) => r.data),

    killProcess: (clusterId: number, nodeId: number, processId: number): Promise<KillProcessResult> =>
        api
            .post<KillProcessResult>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/kill-process/${processId}`,
            )
            .then((r) => r.data),

    killProcesses: (clusterId: number, nodeId: number, body: KillProcessesBody): Promise<KillProcessesResult> =>
        api
            .post<KillProcessesResult>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/kill-processes`,
                body,
            )
            .then((r) => r.data),

    getSlowQueries: (clusterId: number, nodeId?: number) =>
        api
            .get<SlowQueryNodeResult[]>(
                `/api/clusters/${clusterId}/diagnostics/slow-queries`,
                { params: nodeId !== undefined ? { node_id: nodeId } : {} },
            )
            .then((r) => r.data),

    getErrorLog: (clusterId: number, nodeId: number, lines = 200) =>
        api
            .get<ErrorLogResult>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/error-log`,
                { params: { lines } },
            )
            .then((r) => r.data),

    setSlowQueryLog: (clusterId: number, nodeId: number, enabled: boolean) =>
        api
            .post<{ ok: boolean; slow_query_log: string }>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/set-slow-query-log`,
                { enabled },
            )
            .then((r) => r.data),

    purgeBinaryLogs: (clusterId: number, nodeId: number, body: PurgeBinaryLogsBody): Promise<PurgeBinaryLogsResult> =>
        api
            .post<PurgeBinaryLogsResult>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/purge-binary-logs`,
                body,
            )
            .then((r) => r.data),

    diskUsage: (clusterId: number, nodeId: number): Promise<DiskUsageNodeResult> =>
        api
            .post<DiskUsageNodeResult>(
                `/api/clusters/${clusterId}/diagnostics/disk-usage`,
                { node_id: nodeId },
            )
            .then((r) => r.data),

    // ── SST Status — #11 ─────────────────────────────────────────────────────
    getSstStatus: (clusterId: number): Promise<SstStatusItem[]> =>
        api
            .get<SstStatusItem[]>(`/api/clusters/${clusterId}/nodes/sst-status`)
            .then((r) => r.data),

    restartSst: (clusterId: number, nodeId: number): Promise<RestartSstResponse> =>
        api
            .post<RestartSstResponse>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/restart-sst`,
            )
            .then((r) => r.data),

    // ── Active transactions — #15 ─────────────────────────────────────────────
    getActiveTransactions: (clusterId: number, nodeId?: number, minAgeSec = 5): Promise<ActiveTrxNodeResult[]> =>
        api
            .get<ActiveTrxNodeResult[]>(
                `/api/clusters/${clusterId}/diagnostics/active-transactions`,
                { params: {
                    ...(nodeId !== undefined ? { node_id: nodeId } : {}),
                    min_age_sec: minAgeSec,
                }},
            )
            .then((r) => r.data),
}
