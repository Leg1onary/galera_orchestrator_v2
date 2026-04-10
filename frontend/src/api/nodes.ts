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
    dc_id: number | null           // [MINOR FIX] ТЗ п.2.4: поле dc_id, не datacenter_id
    datacenter_name: string | null
    // live fields — ТЗ п.7.2
    wsrep_local_state_comment: string | null
    wsrep_cluster_status: string | null
    wsrep_connected: boolean | null
    wsrep_ready: boolean | null
    read_only: boolean | null
    maintenance: boolean | null
    maintenance_drift: boolean | null
    wsrep_flow_control_paused: number | null
    wsrep_local_recv_queue_avg: number | null
    last_check_ts: string | null   // [MINOR FIX] ТЗ п.7.2: last_check_ts, не last_seen
    last_error?: string | null     // [MINOR] не в ТЗ / возможное расширение бэка
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

// [MAJOR FIX] ТЗ п.9.3: response включает accepted + опциональный operation_id
// operation_id присутствует только для async actions (start/stop/restart/rejoin-force)
export interface NodeActionResponse {
    accepted: boolean
    operation_id?: number | null
    message: string
}

export const nodesApi = {
    list: (clusterId: number) =>
        api.get<NodeListItem[]>(`/api/clusters/${clusterId}/nodes`).then((r) => r.data),

    details: (clusterId: number, nodeId: number) =>
        api
            .get<NodeDetails>(`/api/clusters/${clusterId}/nodes/${nodeId}/details`)
            .then((r) => r.data),

    // [BLOCKER FIX] ТЗ п.9.3: action в body, не в URL
    action: (clusterId: number, nodeId: number, action: NodeAction) =>
        api
            .post<NodeActionResponse>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/actions`,
                { action }  // action передаётся в теле запроса
            )
            .then((r) => r.data),

    // [BLOCKER FIX] ТЗ п.9.1: GET, не POST
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

    // [MAJOR FIX] variables() удалён — endpoint не существует в ТЗ для nodes.
    // Используй diagnosticsApi.variables(clusterId) из api/diagnostics.ts
}