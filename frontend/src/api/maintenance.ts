import { api } from '@/api/client'
import type { NodeListItem } from '@/api/nodes'

// ТЗ п.2.8: статусы операций
export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'         // [MAJOR FIX] было 'finished'
    | 'failed'
    | 'cancel_requested' // [MAJOR FIX] отсутствовало
    | 'cancelled'

// ТЗ п.9.1: формат active_operation в ответе status endpoint
export type ActiveOperation = {
    id: number           // [BLOCKER FIX] number, не string
    type: 'rolling_restart' | 'recovery_bootstrap' | 'recovery_rejoin' | 'node_action'
    status: OperationStatus
    started_at: string | null
    error_message?: string | null
}

// ТЗ п.9.1: формат ответа GET /maintenance/status
export type MaintenanceStatusResponse = {
    active_operation: ActiveOperation | null
}

// Расширенная live-структура для NodeMaintenanceTable
// Базируется на NodeListItem — без дублирования полей
export type MaintenanceNodeState = {
    node_id: number
    node_name: string
    host: string
    port: number
    wsrep_state: string
    maintenance: boolean
    maintenance_drift: boolean       // ТЗ п.14.10
    read_only: boolean
    enabled: boolean
}

// [MINOR] не в ТЗ — уточнить payload с бэком
export type RollingRestartConfig = {
    node_order?: number[]            // опциональный порядок node_id
    wait_timeout_sec?: number        // таймаут ожидания SYNCED
}

export const maintenanceApi = {
    // Список нод — переиспользует /nodes endpoint, типизирован
    listNodes: (clusterId: number) =>
        api
            .get<NodeListItem[]>(`/api/clusters/${clusterId}/nodes`)
            .then((r) => r.data),

    // [BLOCKER FIX] enter/exitMaintenance удалены.
    // Используй nodesApi.action(clusterId, nodeId, 'enter-maintenance')
    // и nodesApi.action(clusterId, nodeId, 'exit-maintenance') из api/nodes.ts
    // ТЗ п.9.3: все node actions идут через POST /nodes/{id}/actions + body

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/maintenance/rolling-restart
    startRollingRestart: (clusterId: number, config: RollingRestartConfig = {}) =>
        api
            .post<{ accepted: boolean; operation_id: number }>(
                `/api/clusters/${clusterId}/maintenance/rolling-restart`,
                config
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
                `/api/clusters/${clusterId}/maintenance/status`
            )
            .then((r) => r.data),
}