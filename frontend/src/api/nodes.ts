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

// GET /api/clusters/{id}/nodes — список нод с live-данными
// Поля соответствуют backend/routers/nodes.py::list_nodes()
export interface NodeListItem {
    id: number
    name: string
    host: string
    port: number
    ssh_port: number
    ssh_user: string
    db_user: string
    enabled: boolean
    maintenance: boolean
    datacenter_id: number | null       // бэкенд: "datacenter_id" (не dc_id)
    datacenter_name: string | null
    cluster_id: number
    live: NodeLiveData | null
}

export interface NodeDetails extends NodeListItem {
    // NodeDetails = NodeListItem (бэкенд get_node() возвращает ту же структуру)
    // Расширенные поля приходят через live (NodeLiveData)
}

// LiveNodeState.to_dict() из backend/services/poller.py
// ВАЖНО: поле называется 'readonly', не 'read_only'
export interface NodeLiveData {
    wsrep_cluster_status: string | null
    wsrep_cluster_size: number | null
    wsrep_connected: string | null      // 'ON' | 'OFF'
    wsrep_ready: string | null          // 'ON' | 'OFF'
    wsrep_local_state_comment: string | null
    wsrep_local_recv_queue: number | null
    wsrep_local_send_queue: number | null
    wsrep_flow_control_paused: number | null
    readonly: boolean                   // ВАЖНО: 'readonly', не 'read_only'
    maintenance_drift: boolean
    ssh_ok: boolean
    db_ok: boolean
    ssh_latency_ms: number | null
    db_latency_ms: number | null
    error: string | null
    last_check_ts: string | null
    flow_control_history: number[]
    recv_queue_history: number[]
}

// GET /api/clusters/{id}/status → nodes[] (используется в ClusterStatusResponse)
export interface NodeStatusItem {
    id: number
    name: string
    host: string
    port: number
    ssh_port: number
    ssh_user: string
    db_user: string
    enabled: boolean
    maintenance: boolean
    dc_id: number | null
    dc_name: string | null
    live: NodeLiveData
}

// GET /api/clusters/{cluster_id}/nodes/{node_id}/test-connection
// backend: test_node_connection() — одно поле error, не ssh_error/db_error
export interface TestConnectionResult {
    node_id: number
    ssh_ok: boolean
    ssh_latency_ms: number | null
    db_ok: boolean
    db_latency_ms: number | null
    error: string | null               // единое поле ошибки (не ssh_error/db_error)
}

// GET /api/clusters/{cluster_id}/nodes/{node_id}/innodb-status
// backend: get_innodb_status() → full_status / latest_deadlock / has_deadlock
export interface InnoDbStatus {
    node_id: number
    full_status: string                // было 'raw' — не совпадало с бэкендом
    latest_deadlock: string | null     // было 'deadlock_section'
    has_deadlock: boolean              // было 'parsed_at' — поле другое
}

export interface NodeActionResponse {
    accepted: boolean
    operation_id?: number | null
    message?: string
}

// GET /api/clusters/{cluster_id}/log?node_id=N&limit=N
export interface NodeLogEntry {
    ts: string
    level: 'INFO' | 'WARN' | 'ERROR'
    source: string
    message: string
    node_id: number | null
    operation_id: number | null
}

// ТЗ п.11.6: поля, обновляемые через PATCH /api/clusters/{id}/nodes/{id}
// backend: NodePatchRequest(enabled, maintenance)
export interface NodePatch {
    enabled?: boolean
    maintenance?: boolean
}

export const nodesApi = {
    list: (clusterId: number) =>
        api.get<NodeListItem[]>(`/api/clusters/${clusterId}/nodes`).then((r) => r.data),

    // GET /api/clusters/{cluster_id}/nodes/{node_id}
    // backend: get_node() — БЕЗ суффикса /details
    details: (clusterId: number, nodeId: number) =>
        api
            .get<NodeDetails>(`/api/clusters/${clusterId}/nodes/${nodeId}`)
            .then((r) => r.data),

    action: (clusterId: number, nodeId: number, action: NodeAction) =>
        api
            .post<NodeActionResponse>(
                `/api/clusters/${clusterId}/nodes/${nodeId}/actions`,
                { action }
            )
            .then((r) => r.data),

    // ТЗ п.11.6: PATCH /api/clusters/{cluster_id}/nodes/{id}
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

    // GET /api/clusters/{cluster_id}/log?node_id={nodeId}&limit={limit}
    // Использует cluster-level event_log endpoint (не /nodes/{id}/logs — такого нет)
    getNodeLogs: (clusterId: number, nodeId: number, limit = 100) =>
        api
            .get<NodeLogEntry[]>(
                `/api/clusters/${clusterId}/log`,
                { params: { node_id: nodeId, limit } }
            )
            .then((r) => r.data),
}
