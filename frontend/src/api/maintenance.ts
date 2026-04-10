import { api } from '@/api/client'

// ── Operation states ───────────────────────────────────────────────────────────────────
// ТЗ п.2.8 — точные строки, которые отдаёт бэкенд
export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'
    | 'failed'
    | 'cancel_requested'
    | 'cancelled'

// ── Active operation ────────────────────────────────────────────────────────────────
// ТЗ п.9.1: полный набор полей которые читает store.init()
export type ActiveOperation = {
    id:                  string        // UUID строка — store.operationId: ref<string|null>
    type:                'rolling_restart' | 'recovery_bootstrap' | 'recovery_rejoin' | 'node_action'
    status:              OperationStatus
    // BLOCKER fix: поля которые store читает в init()
    current_node_id:     number | null
    completed_node_ids:  number[]
    failed_node_id:      number | null
    progress_pct:        number
    message:             string | null
    error_message:       string | null
    started_at:          string | null
}

// ── Status response ───────────────────────────────────────────────────────────────────
export type MaintenanceStatusResponse = {
    active_operation: ActiveOperation | null
}

// ── Node state ──────────────────────────────────────────────────────────────────────
export type MaintenanceNodeState = {
    id:                number
    name:              string
    host:              string
    port:              number
    wsrep_local_state_comment: string   // MAJOR fix: соответствует полю topology/nodes
    maintenance:       boolean
    maintenance_drift: boolean          // ТЗ п.14.10
    read_only:         boolean
    enabled:           boolean
}

// ── Rolling restart ───────────────────────────────────────────────────────────────────
export type RollingRestartConfig = {
    node_order?:        number[]
    wait_timeout_sec?:  number
}

export type StartRollingRestartResponse = {
    accepted:     boolean
    operation_id: string   // MAJOR fix: string UUID, не number
}

// BLOCKER fix: тип который store импортирует и хранит в rrStatus
export type RollingRestartStatus = {
    operation_id:        string
    state:               OperationStatus
    current_node_id:     number | null
    completed_node_ids:  number[]
    failed_node_id:      number | null
    progress_pct:        number
    message:             string | null
    error:               string | null
    started_at:          string | null
    finished_at:         string | null
}

// ── API ──────────────────────────────────────────────────────────────────────────────────
export const maintenanceApi = {
    // ТЗ п.9.2: GET /api/clusters/{cluster_id}/maintenance/nodes
    // MAJOR fix: отдельный endpoint для maintenance-состояния нод, не /nodes
    listNodes: (clusterId: number) =>
        api
            .get<MaintenanceNodeState[]>(`/api/clusters/${clusterId}/maintenance/nodes`)
            .then((r) => r.data),

    // ТЗ п.9.3: POST /api/clusters/{cluster_id}/nodes/{node_id}/actions
    // MAJOR fix: возвращаем методы — store их вызывает
    enterMaintenance: (clusterId: number, nodeId: number) =>
        api
            .post(`/api/clusters/${clusterId}/nodes/${nodeId}/actions`, {
                action: 'enter-maintenance',
            })
            .then((r) => r.data),

    exitMaintenance: (clusterId: number, nodeId: number) =>
        api
            .post(`/api/clusters/${clusterId}/nodes/${nodeId}/actions`, {
                action: 'exit-maintenance',
            })
            .then((r) => r.data),

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/maintenance/rolling-restart
    startRollingRestart: (clusterId: number, config: RollingRestartConfig = {}) =>
        api
            .post<StartRollingRestartResponse>(
                `/api/clusters/${clusterId}/maintenance/rolling-restart`,
                config,
            )
            .then((r) => r.data),

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/maintenance/cancel
    cancel: (clusterId: number) =>
        api
            .post(`/api/clusters/${clusterId}/maintenance/cancel`)
            .then((r) => r.data),

    // ТЗ п.9.1: GET /api/clusters/{cluster_id}/maintenance/status
    getStatus: (clusterId: number) =>
        api
            .get<MaintenanceStatusResponse>(
                `/api/clusters/${clusterId}/maintenance/status`,
            )
            .then((r) => r.data),
}
