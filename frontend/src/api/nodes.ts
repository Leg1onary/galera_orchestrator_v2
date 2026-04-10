import { api } from '@/api/client'

export type NodeAction =
    | 'set-readonly'
    | 'set-readwrite'
    | 'enter-maintenance'
    | 'exit-maintenance'
    | 'start'
    | 'stop'
    | 'restart'
    | 'rejoin-force'

export interface NodeListItem {
    id: number
    name: string
    host: string
    port: number
    enabled: boolean
    dc_id: number | null
    datacenter_name: string | null
    wsrep_local_state_comment: string | null
    wsrep_cluster_status: string | null
    wsrep_connected: boolean | null
    wsrep_ready: boolean | null
    read_only: boolean | null
    maintenance: boolean | null
    maintenance_drift: boolean | null
    wsrep_flow_control_paused: number | null
    wsrep_local_recv_queue_avg: number | null
    last_check_ts: string | null
    last_error?: string | null
}

export interface NodeDetails extends NodeListItem {
    wsrep_local_state: number | null
    wsrep_cluster_size: number | null
    wsrep_commit_window: number | null
    wsrep_local_send_queue_avg: number | null
    uptime_seconds: number | null
    version: string | null
    sparkline_flow_control: number[]
    sparkline_recv_queue: number[]
}

export interface TestConnectionResult {
    ssh_ok: boolean
    ssh_latency_ms: number | null
    ssh_error: string | null
    db_ok: boolean
    db_latency_ms: number | null
    db_error: string | null
}

export interface InnoDbStatus {
    raw: string
    deadlock_section: string | null
    parsed_at: string
}

export interface NodeActionResponse {
    accepted: boolean
    operation_id?: number | null
    message: string
}

export interface NodeLogEntry {
    ts: string
    level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
    source: string
    message: string
    operation_id: number | null
}

// ТЗ п.11.6: поля которые можно обновить через PATCH
export interface NodePatch {
    enabled?: boolean
}

export const nodesApi = {
    list: (clusterId: number) =>
        api.get<NodeListItem[]>(`/api/clusters/${clusterId}/nodes`).then((r) => r.data),

    details: (clusterId: number, nodeId: number) =>
        api
            .get<NodeDetails>(`/api/clusters/${clusterId}/nodes/${nodeId}/details`)
            .then((r) => r.data),

    action: (clusterId: number, nodeId: number, action: NodeAction) =>
        api
            .post<NodeActionResponse>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/actions`,
                { action }
            )
            .then((r) => r.data),

    // ТЗ п.11.6: PATCH /api/clusters/{cluster_id}/nodes/{id}
    // Используется для включения/отключения ноды (поле enabled)
    patch: (clusterId: number, nodeId: number, data: NodePatch) =>
        api
            .patch<NodeListItem>(
                `/api/clusters/${clusterId}/nodes/${nodeId}`,
                data
            )
            .then((r) => r.data),

    testConnection: (clusterId: number, nodeId: number) =>
        api
            .get<TestConnectionResult>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/test-connection`
            )
            .then((r) => r.data),

    innodbStatus: (clusterId: number, nodeId: number) =>
        api
            .get<InnoDbStatus>(`/api/clusters/${clusterId}/nodes/${nodeId}/innodb-status`)
            .then((r) => r.data),

    // fix: добавлен getNodeLogs — используется в NodeDetailDrawer
    // ТЗ п.8.2: GET /api/clusters/{cluster_id}/nodes/{node_id}/logs
    getNodeLogs: (clusterId: number, nodeId: number, limit = 100) =>
        api
            .get<NodeLogEntry[]>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/logs`,
                { params: { limit } }
            )
            .then((r) => r.data),
}
