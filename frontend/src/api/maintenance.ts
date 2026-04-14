import { api } from '@/api/client'

// ── Operation states ───────────────────────────────────────────────────────────────────
export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'
    | 'failed'
    | 'cancel_requested'
    | 'cancelled'

// ── Active operation ────────────────────────────────────────────────────────────────
export type ActiveOperation = {
    id:             number
    type:           'rolling_restart' | 'recovery_bootstrap' | 'recovery_rejoin' | 'node_action'
    status:         OperationStatus
    started_at:     string | null
    created_by:     string | null
    target_node_id: number | null
    details_json:   string | null
    error_message:  string | null
}

// ── Status response ───────────────────────────────────────────────────────────────────
export type MaintenanceStatusResponse = {
    active_operation: ActiveOperation | null
}

// ── Node state ──────────────────────────────────────────────────────────────────────
export type MaintenanceNodeState = {
    // БД поля (nodes table)
    id:          number
    name:        string
    host:        string
    port:        number
    maintenance: boolean
    enabled:     boolean
    // Live поля (LiveNodeState.to_dict()) — опциональны если поллер ещё не успел
    wsrep_local_state_comment?: string | null
    wsrep_desync?:              boolean | null  // true = нода в режиме desync (wsrep_desync=ON)
    readonly?:                  boolean        // ВАЖНО: 'readonly', не 'read_only'!
    maintenance_drift?:         boolean
    ssh_ok?:                    boolean
    db_ok?:                     boolean
    last_check_ts?:             string | null
}

// ── Rolling restart ───────────────────────────────────────────────────────────────────
export type RollingRestartConfig = {
    node_order?:       number[]
    wait_timeout_sec?: number
}

export type StartRollingRestartResponse = {
    accepted:     boolean
    operation_id: number
    message:      string
}

export type RollingRestartStatus = {
    operation_id:        number
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

// ── Desync response ───────────────────────────────────────────────────────────────────
export type DesyncResponse = {
    ok:           boolean
    node_id:      number
    wsrep_desync: boolean
}

// ── API ──────────────────────────────────────────────────────────────────────────────────
export const maintenanceApi = {
    listNodes: (clusterId: number) =>
        api
            .get<MaintenanceNodeState[]>(`/api/clusters/${clusterId}/maintenance/nodes`)
            .then((r) => r.data),

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

    // ── Desync / Resync (вне MVP) ──────────────────────────────────────────────────
    desyncNode: (clusterId: number, nodeId: number) =>
        api
            .post<DesyncResponse>(`/api/clusters/${clusterId}/nodes/${nodeId}/desync`)
            .then((r) => r.data),

    resyncNode: (clusterId: number, nodeId: number) =>
        api
            .post<DesyncResponse>(`/api/clusters/${clusterId}/nodes/${nodeId}/resync`)
            .then((r) => r.data),

    startRollingRestart: (clusterId: number, config: RollingRestartConfig = {}) =>
        api
            .post<StartRollingRestartResponse>(
                `/api/clusters/${clusterId}/maintenance/rolling-restart`,
                config,
            )
            .then((r) => r.data),

    cancel: (clusterId: number) =>
        api
            .post(`/api/clusters/${clusterId}/maintenance/cancel`)
            .then((r) => r.data),

    getStatus: (clusterId: number) =>
        api
            .get<MaintenanceStatusResponse>(
                `/api/clusters/${clusterId}/maintenance/status`,
            )
            .then((r) => r.data),
}
