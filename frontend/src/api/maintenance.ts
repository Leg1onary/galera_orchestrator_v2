import { api } from '@/api/client'

// ── Operation states ──────────────────────────────────────────────────────────
// set_operation_status() пишет: 'pending'|'running'|'success'|'failed'|
//                               'cancel_requested'|'cancelled'
// 'finished' — фронтовая нормализация 'success' для UI
export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'           // реальный DB/WS статус при успехе
    | 'finished'          // нормализованный фронт-статус (success → finished)

// ── Operation states ───────────────────────────────────────────────────────────────────
// ТЗ п.2.8 — точные строки, которые отдаёт бэкенд
export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'
    | 'failed'
    | 'cancel_requested'
    | 'cancelled'

// ── Active operation ──────────────────────────────────────────────────────────
// get_active_operation() SELECT: id, type, status, started_at, created_by,
//                                target_node_id, details_json
// НЕТ полей: current_node_id, completed_node_ids, progress_pct, message
// Эти поля доступны ТОЛЬКО через WS-события operation_progress

// ── Active operation ────────────────────────────────────────────────────────────────
// ТЗ п.9.1: полный набор полей которые читает store.init()

export type ActiveOperation = {
    id:             number        // Integer autoincrement из cluster_operations
    type:           'rolling_restart' | 'recovery_bootstrap' | 'recovery_rejoin' | 'node_action'
    status:         OperationStatus
    started_at:     string | null
    created_by:     string | null
    target_node_id: number | null
    details_json:   string | null // raw JSON строка — парсить на фронте при необходимости
    error_message:  string | null // из cluster_operations.error_message
    // Поля прогресса ОТСУТСТВУЮТ в get_active_operation() — только через WS
}

// ── Status response ───────────────────────────────────────────────────────────────────
export type MaintenanceStatusResponse = {
    active_operation: ActiveOperation | null
}


// ── Node state ────────────────────────────────────────────────────────────────
// Гибрид: поля из nodes (БД) + live поля от поллера (LiveNodeState.to_dict())
// ВАЖНО: live поле называется 'readonly', не 'read_only' (из LiveNodeState.to_dict())

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
    wsrep_local_state_comment?: string | null  // 'SYNCED'|'OFFLINE'|'DONOR'|'JOINER'|'DESYNCED'
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
    operation_id: number   // Integer autoincrement — не UUID строка
    message:      string
}

// Хранится в store.rrStatus — фронтовое представление прогресса операции
// Собирается из init() (только base поля) + WS-событий (прогресс)
export type RollingRestartStatus = {
    operation_id:        number        // Integer
    state:               OperationStatus
    // Поля прогресса — только из WS, не из getStatus()
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
    // ТЗ п.9.2 — ENDPOINT НУЖНО ДОБАВИТЬ НА БЭКЕНД
    // GET /api/clusters/{cluster_id}/maintenance/nodes не существует в routers/maintenance.py
    // Требует реализации get_maintenance_nodes() в services/maintenance.py
    listNodes: (clusterId: number) =>
        api
            .get<MaintenanceNodeState[]>(`/api/clusters/${clusterId}/maintenance/nodes`)
            .then((r) => r.data),

    // ТЗ п.9.3: POST /api/clusters/{cluster_id}/nodes/{node_id}/actions
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

    // ТЗ п.9.1 — БЭКЕНД НЕ ЧИТАЕТ BODY (нужно добавить RollingRestartBody в роутер)
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

    // Возвращает только: id, type, status, started_at, created_by,
    //                    target_node_id, details_json
    // НЕ содержит: current_node_id, completed_node_ids, progress_pct, message
    getStatus: (clusterId: number) =>
        api
            .get<MaintenanceStatusResponse>(
                `/api/clusters/${clusterId}/maintenance/status`,
            )
            .then((r) => r.data),
}
