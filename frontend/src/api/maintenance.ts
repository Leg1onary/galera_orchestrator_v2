import { api } from '@/api/client'

export type MaintenanceNodeState = {
    node_id: number
    node_name: string
    host: string
    port: number
    wsrep_state: string           // SYNCED / DONOR / JOINER / etc.
    maintenance: boolean          // флаг в БД
    maintenance_drift: boolean    // БД=true но MariaDB read_only=0
    read_only: boolean
    enabled: boolean
}

export type RollingRestartConfig = {
    node_order: number[]          // массив node_id в порядке рестарта
    wait_timeout_sec: number      // таймаут ожидания SYNCED (default 300)
}

export type RollingRestartStatus = {
    operation_id: string
    state: 'pending' | 'running' | 'finished' | 'failed' | 'cancelled'
    current_node_id: number | null
    completed_node_ids: number[]
    failed_node_id: number | null
    progress_pct: number
    message: string | null
    error: string | null
    started_at: string | null
    finished_at: string | null
}

export const maintenanceApi = {
    // Список нод с maintenance-состоянием (использует /nodes endpoint)
    listNodes: (clusterId: number) =>
        api.get<MaintenanceNodeState[]>(`/api/clusters/${clusterId}/nodes`)
            .then((r) => r.data),

    enterMaintenance: (clusterId: number, nodeId: number) =>
        api.post(`/api/clusters/${clusterId}/nodes/${nodeId}/enter-maintenance`),

    exitMaintenance: (clusterId: number, nodeId: number) =>
        api.post(`/api/clusters/${clusterId}/nodes/${nodeId}/exit-maintenance`),

    startRollingRestart: (clusterId: number, config: RollingRestartConfig) =>
        api.post<{ operation_id: string }>(
            `/api/clusters/${clusterId}/maintenance/rolling-restart`,
            config,
        ).then((r) => r.data),

    cancel: (clusterId: number) =>
        api.post(`/api/clusters/${clusterId}/maintenance/cancel`),

    getStatus: (clusterId: number) =>
        api.get<RollingRestartStatus>(
            `/api/clusters/${clusterId}/maintenance/status`,
        ).then((r) => r.data),
}