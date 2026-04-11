import { api } from '@/api/client'

// ── Config diff ────────────────────────────────────────────────────────────
export type ConfigDiffRow = {
    variable_name: string
    values: Record<string, string>
    has_diff: boolean
}

// ── Variables ──────────────────────────────────────────────────────────────
export type KVRow = {
    variable_name: string
    value: string
}

export type VariablesResult = Record<string, KVRow[]>

// ── Check all (connections) ────────────────────────────────────────────────
export type ConnectionCheckRow = {
    id: number
    name: string
    host: string
    role: 'Node' | 'Arbitrator'
    ssh_ok: boolean | null
    db_ok: boolean | null
    ssh_latency_ms: number | null
    db_latency_ms: number | null
    last_check_ts: string | null
}

// ── Resources ──────────────────────────────────────────────────────────────
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

// ── Arbitrator log ─────────────────────────────────────────────────────────
export type ArbitratorLogResult = {
    arbitrator_id: number
    arbitrator_name: string
    lines: string[]
    fetched_at: string
}

// ── Arbitrator test connection ─────────────────────────────────────────────
export type ArbitratorConnectionResult = {
    ssh_ok: boolean
    garbd_running: boolean
    latency_ssh_ms: number | null
}

// ── Galera status ──────────────────────────────────────────────────────────
// GET /api/clusters/{cluster_id}/diagnostics/galera-status
export type GaleraStatusNodeResult = {
    node_id: number
    node_name: string
    host: string
    status: Record<string, string>
    error: string | null
}

// ── Process list ───────────────────────────────────────────────────────────
// GET /api/clusters/{cluster_id}/diagnostics/process-list?node_id=N
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

// ── Slow query log ─────────────────────────────────────────────────────────
// GET /api/clusters/{cluster_id}/diagnostics/slow-queries?node_id=N
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

// ── Error log ──────────────────────────────────────────────────────────────
// GET /api/clusters/{cluster_id}/nodes/{node_id}/error-log?lines=N
export type ErrorLogResult = {
    node_id: number
    node_name: string
    lines: string[]
    fetched_at: string
    error: string | null
}

export const diagnosticsApi = {
    // ── ТЗ endpoints ──────────────────────────────────────────────────────

    configDiff: (clusterId: number) =>
        api
            .get<ConfigDiffRow[]>(`/api/clusters/${clusterId}/diagnostics/config-diff`)
            .then((r) => r.data),

    variables: (clusterId: number) =>
        api
            .get<VariablesResult>(`/api/clusters/${clusterId}/diagnostics/variables`)
            .then((r) => r.data),

    checkAll: (clusterId: number) =>
        api
            .post<ConnectionCheckRow[]>(`/api/clusters/${clusterId}/diagnostics/check-all`)
            .then((r) => r.data),

    resources: (clusterId: number) =>
        api
            .post<NodeResourceRow[]>(`/api/clusters/${clusterId}/diagnostics/resources`)
            .then((r) => r.data),

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

    // ── Galera status ──────────────────────────────────────────────────────
    // GET /api/clusters/{cluster_id}/diagnostics/galera-status
    getGaleraStatus: (clusterId: number) =>
        api
            .get<GaleraStatusNodeResult[]>(`/api/clusters/${clusterId}/diagnostics/galera-status`)
            .then((r) => r.data),

    // ── Process list (read-only) ───────────────────────────────────────────
    // GET /api/clusters/{cluster_id}/diagnostics/process-list
    getProcessList: (clusterId: number, nodeId?: number) =>
        api
            .get<ProcessListNodeResult[]>(
                `/api/clusters/${clusterId}/diagnostics/process-list`,
                { params: nodeId !== undefined ? { node_id: nodeId } : {} },
            )
            .then((r) => r.data),

    // ── Slow query log ─────────────────────────────────────────────────────
    // GET /api/clusters/{cluster_id}/diagnostics/slow-queries
    getSlowQueries: (clusterId: number, nodeId?: number) =>
        api
            .get<SlowQueryNodeResult[]>(
                `/api/clusters/${clusterId}/diagnostics/slow-queries`,
                { params: nodeId !== undefined ? { node_id: nodeId } : {} },
            )
            .then((r) => r.data),

    // ── Error log ──────────────────────────────────────────────────────────
    // GET /api/clusters/{cluster_id}/nodes/{node_id}/error-log
    getErrorLog: (clusterId: number, nodeId: number, lines = 200) =>
        api
            .get<ErrorLogResult>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/error-log`,
                { params: { lines } },
            )
            .then((r) => r.data),
}
