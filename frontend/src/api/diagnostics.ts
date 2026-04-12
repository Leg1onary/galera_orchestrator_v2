import { api } from '@/api/client'

// ── Config diff ────────────────────────────────────────────────────────────
// Backend: GET /diagnostics/config-diff
// Response: { variables: [{variable, values: [{node_id,node_name,value,fetch_error}], has_diff}], nodes: [...], diff_found }
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

// ── Variables ──────────────────────────────────────────────────────────────
// Backend: GET /diagnostics/variables?node_id=N
// Response: { node_id, node_name, host, total, variables: [{name, value}] }
export type KVRow = {
    variable_name: string
    value: string
}

export type VariablesResult = Record<string, KVRow[]>

// Raw shape from backend per single node request
interface RawVariablesResult {
    node_id: number
    node_name: string
    host: string
    total: number
    variables: { name: string; value: string }[]
}

// ── Check all (connections) ────────────────────────────────────────────────
export type ConnectionCheckRow = {
    node_id: number
    node_name: string
    host: string
    role: 'node' | 'arbitrator'
    ssh_ok: boolean | null
    db_ok: boolean | null
    ssh_latency_ms: number | null
    db_latency_ms: number | null
    ssh_error: string | null
    db_error: string | null
    // arbitrator-only
    garbd_running?: boolean | null
    latency_ssh_ms?: number | null
}

export type CheckAllResponse = {
    nodes: ConnectionCheckRow[]
    arbitrators: ConnectionCheckRow[]
}

// ── Resources ──────────────────────────────────────────────────────────────
// Backend: POST /diagnostics/resources
// Response: { nodes: [{node_id, node_name, host, cpu_load:{load1,load5,load15}, ram:{total_bytes,used_bytes,free_bytes,available_bytes}, disk:{total_bytes,used_bytes,available_bytes,use_percent}, uptime_since, error}] }
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
export type GaleraStatusNodeResult = {
    node_id: number
    node_name: string
    host: string
    status: Record<string, string>
    error: string | null
}

// ── Process list ───────────────────────────────────────────────────────────
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
export type ErrorLogResult = {
    node_id: number
    node_name: string
    lines: string[]
    fetched_at: string
    error: string | null
}

export const diagnosticsApi = {

    configDiff: (clusterId: number): Promise<ConfigDiffResponse> =>
        api
            .get<ConfigDiffResponse>(`/api/clusters/${clusterId}/diagnostics/config-diff`)
            .then((r) => r.data),

    // variables: backend requires ?node_id=N and returns single-node result.
    // This helper fetches for one node; VariablesPanel orchestrates multi-node loading.
    variablesForNode: (clusterId: number, nodeId: number, wsrepOnly = false): Promise<KVRow[]> =>
        api
            .get<RawVariablesResult>(`/api/clusters/${clusterId}/diagnostics/variables`, {
                params: { node_id: nodeId, wsrep_only: wsrepOnly },
            })
            .then((r) => r.data.variables.map((v) => ({ variable_name: v.name, value: v.value }))),

    checkAll: (clusterId: number): Promise<CheckAllResponse> =>
        api
            .post<CheckAllResponse>(`/api/clusters/${clusterId}/diagnostics/check-all`)
            .then((r) => r.data),

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
}
