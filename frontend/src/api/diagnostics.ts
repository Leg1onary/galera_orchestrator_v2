import { api } from '@/api/client'

// ── Process list ───────────────────────────────────────────────────────────
export type ProcessRow = {
    id: number
    user: string
    host: string
    db: string | null
    command: string
    time: number          // секунды
    state: string | null
    info: string | null   // SQL query
}

// ── Slow queries ───────────────────────────────────────────────────────────
export type SlowQueryRow = {
    query_digest: string
    schema_name: string | null
    exec_count: number
    avg_latency_ms: number
    max_latency_ms: number
    rows_examined_avg: number
    rows_sent_avg: number
    last_seen: string
}

// ── Galera vars / status ───────────────────────────────────────────────────
export type KVRow = {
    variable_name: string
    value: string
}

// ── InnoDB status ──────────────────────────────────────────────────────────
export type InnodbStatusResult = {
    node_id: number
    node_name: string
    raw_text: string
    deadlock_section: string | null   // вырезанный блок LATEST DETECTED DEADLOCK
    fetched_at: string
}

// ── Error log ──────────────────────────────────────────────────────────────
export type ErrorLogLine = {
    line_no: number
    raw: string
    level: 'ERROR' | 'WARNING' | 'NOTE' | 'SYSTEM' | 'UNKNOWN'
    timestamp: string | null
}

export type ErrorLogResult = {
    node_id: number
    node_name: string
    lines: ErrorLogLine[]
    total_lines: number
    fetched_at: string
}

// ── Kill ───────────────────────────────────────────────────────────────────
export type KillResult = {
    killed: boolean
    message: string
}

export const diagnosticsApi = {
    getProcessList: (clusterId: number, nodeId?: number) =>
        api.get<ProcessRow[]>(`/api/clusters/${clusterId}/diagnostics/processes`, {
            params: nodeId ? { node_id: nodeId } : {},
        }).then((r) => r.data),

    killProcess: (clusterId: number, nodeId: number, processId: number) =>
        api.post<KillResult>(
            `/api/clusters/${clusterId}/diagnostics/processes/${processId}/kill`,
            { node_id: nodeId },
        ).then((r) => r.data),

    getSlowQueries: (clusterId: number, nodeId?: number, minLatencyMs = 1000) =>
        api.get<SlowQueryRow[]>(`/api/clusters/${clusterId}/diagnostics/slow-queries`, {
            params: { ...(nodeId ? { node_id: nodeId } : {}), min_latency_ms: minLatencyMs },
        }).then((r) => r.data),

    getGaleraVars: (clusterId: number, nodeId?: number) =>
        api.get<KVRow[]>(`/api/clusters/${clusterId}/diagnostics/galera-vars`, {
            params: nodeId ? { node_id: nodeId } : {},
        }).then((r) => r.data),

    getGaleraStatus: (clusterId: number, nodeId?: number) =>
        api.get<KVRow[]>(`/api/clusters/${clusterId}/diagnostics/galera-status`, {
            params: nodeId ? { node_id: nodeId } : {},
        }).then((r) => r.data),

    getInnodbStatus: (clusterId: number, nodeId: number) =>
        api.get<InnodbStatusResult>(`/api/clusters/${clusterId}/diagnostics/innodb-status`, {
            params: { node_id: nodeId },
        }).then((r) => r.data),

    getErrorLog: (clusterId: number, nodeId: number, lines = 200) =>
        api.get<ErrorLogResult>(`/api/clusters/${clusterId}/diagnostics/error-log`, {
            params: { node_id: nodeId, lines },
        }).then((r) => r.data),
}