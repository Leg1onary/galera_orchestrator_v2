// frontend/src/api/diagnostics.ts
import { api } from '@/api/client'

// ── Types ─────────────────────────────────────────────────────────────────────

export type DiagCheckResult = {
    node_id: number
    node_name: string
    checks: Record<string, string | number | null>
    error: string | null
}

export type DiagResourceResult = {
    node_id: number
    node_name: string
    resources: {
        cpu_pct: number | null
        ram_used: number | null
        ram_total: number | null
        disk_used: number | null
        disk_total: number | null
    }
    error: string | null
}

export type ConfigDiffResult = {
    nodes: Array<{ node_id: number; node_name: string }>
    diffs: Record<string, Record<string, string | null>>
    node_errors: Array<{ node_id: number; node_name: string; error: string }>
}

export type NodeVariablesResult = {
    node_id: number
    node_name: string
    variables: Array<{ name: string; value: string }>
    error: string | null
}

export type GaleraStatusResult = {
    node_id: number
    node_name: string
    status: Record<string, string>
    error: string | null
}

export type ProcessListEntry = {
    id: number | null
    user: string | null
    host: string | null
    db: string | null
    command: string | null
    time: number | null
    state: string | null
    info: string | null
}

export type ProcessListResult = {
    node_id: number
    node_name: string
    processes: ProcessListEntry[]
    error: string | null
}

export type SlowQueryRow = {
    start_time: string
    user_host: string
    query_time: string
    lock_time: string
    rows_sent: number | null
    rows_examined: number | null
    db: string
    sql_text: string
}

export type SlowQueryNodeResult = {
    node_id: number
    node_name: string
    slow_log_enabled: boolean | null
    rows: SlowQueryRow[]
    error: string | null
}

export type SlowQueryParams = {
    nodeId?: number
    minQueryTime?: number  // seconds, 0 = no filter
    limit?: number         // default 200
}

export type InnodbStatusResult = {
    node_id: number
    node_name: string
    content: string | null
    error: string | null
}

export type ErrorLogResult = {
    node_id: number
    node_name: string
    content: string | null
    error: string | null
}

export type ArbTestResult = {
    arb_id: number
    arb_name: string
    success: boolean
    latency_ms: number | null
    error: string | null
}

export type ArbLogResult = {
    arb_id: number
    arb_name: string
    content: string | null
    error: string | null
}

// ── Slow query log toggle ──────────────────────────────────────────────────
export type SlowQueryToggleResult = {
    node_id: number
    node_name: string
    enabled: boolean | null
    error: string | null
}

// ── API ───────────────────────────────────────────────────────────────────────

export const diagnosticsApi = {
    checkAll: (clusterId: number): Promise<DiagCheckResult[]> =>
        api
            .post<DiagCheckResult[]>(`/api/clusters/${clusterId}/diagnostics/check-all`)
            .then((r) => r.data),

    getResources: (clusterId: number): Promise<DiagResourceResult[]> =>
        api
            .post<DiagResourceResult[]>(`/api/clusters/${clusterId}/diagnostics/resources`)
            .then((r) => r.data),

    getConfigDiff: (clusterId: number): Promise<ConfigDiffResult> =>
        api
            .get<ConfigDiffResult>(`/api/clusters/${clusterId}/diagnostics/config-diff`)
            .then((r) => r.data),

    getVariables: (clusterId: number, nodeId?: number): Promise<NodeVariablesResult[]> =>
        api
            .get<NodeVariablesResult[]>(`/api/clusters/${clusterId}/diagnostics/variables`, {
                params: nodeId ? { node_id: nodeId } : undefined,
            })
            .then((r) => r.data),

    getVariablesAll: (clusterId: number, nodeId?: number): Promise<NodeVariablesResult[]> =>
        api
            .get<NodeVariablesResult[]>(`/api/clusters/${clusterId}/diagnostics/variables/all`, {
                params: nodeId ? { node_id: nodeId } : undefined,
            })
            .then((r) => r.data),

    getGaleraStatus: (clusterId: number): Promise<GaleraStatusResult[]> =>
        api
            .get<GaleraStatusResult[]>(`/api/clusters/${clusterId}/diagnostics/galera-status`)
            .then((r) => r.data),

    getProcessList: (clusterId: number, nodeId?: number): Promise<ProcessListResult[]> =>
        api
            .get<ProcessListResult[]>(`/api/clusters/${clusterId}/diagnostics/process-list`, {
                params: nodeId ? { node_id: nodeId } : undefined,
            })
            .then((r) => r.data),

    getSlowQueries: (
        clusterId: number,
        params?: SlowQueryParams,
    ): Promise<SlowQueryNodeResult[]> => {
        const p: Record<string, unknown> = {}
        if (params?.nodeId)         p.node_id         = params.nodeId
        if (params?.minQueryTime)   p.min_query_time  = params.minQueryTime
        if (params?.limit)          p.limit           = params.limit
        return api
            .get<SlowQueryNodeResult[]>(`/api/clusters/${clusterId}/diagnostics/slow-queries`, {
                params: Object.keys(p).length ? p : undefined,
            })
            .then((r) => r.data)
    },

    getInnodbStatus: (clusterId: number, nodeId: number): Promise<InnodbStatusResult> =>
        api
            .get<InnodbStatusResult>(`/api/clusters/${clusterId}/nodes/${nodeId}/innodb-status`)
            .then((r) => r.data),

    getErrorLog: (clusterId: number, nodeId: number, lines?: number): Promise<ErrorLogResult> =>
        api
            .get<ErrorLogResult>(`/api/clusters/${clusterId}/nodes/${nodeId}/error-log`, {
                params: lines ? { lines } : undefined,
            })
            .then((r) => r.data),

    testArbConnection: (clusterId: number, arbId: number): Promise<ArbTestResult> =>
        api
            .get<ArbTestResult>(`/api/clusters/${clusterId}/arbitrators/${arbId}/test-connection`)
            .then((r) => r.data),

    getArbLog: (clusterId: number, arbId: number, lines?: number): Promise<ArbLogResult> =>
        api
            .get<ArbLogResult>(`/api/clusters/${clusterId}/arbitrators/${arbId}/log`, {
                params: lines ? { lines } : undefined,
            })
            .then((r) => r.data),

    toggleSlowQueryLog: (clusterId: number, nodeId: number, enable: boolean): Promise<SlowQueryToggleResult> =>
        api
            .post<SlowQueryToggleResult>(
                `/api/clusters/${clusterId}/diagnostics/nodes/${nodeId}/slow-query-log/toggle`,
                null,
                { params: { enable } },
            )
            .then((r) => r.data),
}
