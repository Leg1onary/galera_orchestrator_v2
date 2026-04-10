import { api } from '@/api/client'

// ── Config diff ────────────────────────────────────────────────────────────
// ТЗ п.15.4: сравнение wsrep-переменных между нодами
export type ConfigDiffRow = {
    variable_name: string
    values: Record<string, string> // { node_name: value }
    has_diff: boolean
}

// ── Variables ──────────────────────────────────────────────────────────────
// ТЗ п.15.5: SHOW GLOBAL VARIABLES со всех нод
export type KVRow = {
    variable_name: string
    value: string
}

export type VariablesResult = Record<string, KVRow[]> // node_name → rows

// ── Check all (connections) ────────────────────────────────────────────────
// ТЗ п.15.3: SSH + DB проверка всех нод и арбитраторов
export type ConnectionCheckRow = {
    id: number
    name: string
    host: string
    role: 'Node' | 'Arbitrator'
    ssh_ok: boolean | null
    db_ok: boolean | null          // null для арбитраторов (N/A)
    ssh_latency_ms: number | null
    db_latency_ms: number | null
    last_check_ts: string | null
}

// ── Resources ──────────────────────────────────────────────────────────────
// ТЗ п.15.6: CPU/RAM/Disk/Load/Uptime
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
// ТЗ п.15.8: journalctl -u garbd -n N
export type ArbitratorLogResult = {
    arbitrator_id: number
    arbitrator_name: string
    lines: string[]
    fetched_at: string
}

// ── Arbitrator test connection ─────────────────────────────────────────────
// ТЗ п.15.3 + формат ответа п.15 (ssh_ok, garbd_running, latency_ssh_ms)
export type ArbitratorConnectionResult = {
    ssh_ok: boolean
    garbd_running: boolean
    latency_ssh_ms: number | null
}

// ── NOT IN ТЗ (расширения) ─────────────────────────────────────────────────
// ProcessRow, SlowQueryRow, ErrorLogRow, KillResult — не зафиксированы в ТЗ.
// Если бэк их реализует — разрешить явно и раскомментировать ниже.

export const diagnosticsApi = {
    // ТЗ п.9.1: GET /api/clusters/{cluster_id}/diagnostics/config-diff
    configDiff: (clusterId: number) =>
        api
            .get<ConfigDiffRow[]>(`/api/clusters/${clusterId}/diagnostics/config-diff`)
            .then((r) => r.data),

    // ТЗ п.9.1: GET /api/clusters/{cluster_id}/diagnostics/variables
    variables: (clusterId: number) =>
        api
            .get<VariablesResult>(`/api/clusters/${clusterId}/diagnostics/variables`)
            .then((r) => r.data),

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/diagnostics/check-all
    checkAll: (clusterId: number) =>
        api
            .post<ConnectionCheckRow[]>(`/api/clusters/${clusterId}/diagnostics/check-all`)
            .then((r) => r.data),

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/diagnostics/resources
    resources: (clusterId: number) =>
        api
            .post<NodeResourceRow[]>(`/api/clusters/${clusterId}/diagnostics/resources`)
            .then((r) => r.data),

    // ТЗ п.9.1: GET /api/clusters/{cluster_id}/arbitrators/{id}/log?lines=N
    arbitratorLog: (clusterId: number, arbitratorId: number, lines: 20 | 50 | 100 = 50) =>
        api
            .get<ArbitratorLogResult>(
                `/api/clusters/${clusterId}/arbitrators/${arbitratorId}/log`,
                { params: { lines } }
            )
            .then((r) => r.data),

    // ТЗ п.9.1: GET /api/clusters/{cluster_id}/arbitrators/{id}/test-connection
    arbitratorTestConnection: (clusterId: number, arbitratorId: number) =>
        api
            .get<ArbitratorConnectionResult>(
                `/api/clusters/${clusterId}/arbitrators/${arbitratorId}/test-connection`
            )
            .then((r) => r.data),

    // InnoDB status — дублирует nodesApi.innodbStatus().
    // Оставлен здесь для удобства DiagnosticsPage, но вызывает тот же endpoint.
    // ТЗ п.9.1: GET /api/clusters/{cluster_id}/nodes/{id}/innodb-status
    innodbStatus: (clusterId: number, nodeId: number) =>
        api
            .get(`/api/clusters/${clusterId}/nodes/${nodeId}/innodb-status`)
            .then((r) => r.data),
}