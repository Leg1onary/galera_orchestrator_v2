import { api } from '@/api/client'

// ТЗ п.2.8: допустимые статусы операций
export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'           // [BLOCKER FIX] было 'finished'
    | 'failed'
    | 'cancel_requested'  // [MAJOR FIX] отсутствовало
    | 'cancelled'

// NodeGrastate — не в ТЗ явно, но соответствует логике Step 1 Recovery wizard (ТЗ п.13.7)
// Читается из grastate.dat через SSH
export type NodeGrastate = {
    node_id: number
    node_name: string
    host: string
    reachable: boolean
    safe_to_bootstrap: 0 | 1
    seqno: number             // -1 если нода запущена или не читается
    uuid: string | null
    error: string | null
}

// Данные для отображения Step 1 wizard
// Формируются на фронте из GET /status + NodeGrastate данных
export type RecoveryScanResult = {
    nodes: NodeGrastate[]
    recommended_bootstrap_node_id: number | null
    cluster_is_healthy: boolean
}

// ТЗ п.9.1: формат ответа GET /recovery/status -> active_operation
export type RecoveryOperationStatus = {
    operation_id: number       // [BLOCKER FIX] number, не string
    state: OperationStatus
    current_step?: string | null  // не в ТЗ — уточнить с бэком
    progress_pct: number          // 0–100
    message: string | null
    started_at: string | null
    finished_at: string | null
    error: string | null
}

export type RejoinPayload = {
    node_id: number
}

export const recoveryApi = {
    // [MAJOR FIX] scan() удалён — endpoint отсутствует в ТЗ п.9.1.
    // Step 1 wizard читает кластерный /status и NodeListItem из /nodes.
    // Grastate данные приходят из backend при запуске bootstrap.

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/recovery/bootstrap
    bootstrap: (clusterId: number, nodeId: number) =>
        api
            .post<{ accepted: boolean; operation_id: number }>(
                `/api/clusters/${clusterId}/recovery/bootstrap`,
                { node_id: nodeId }
                // [MAJOR FIX] force убран — не в ТЗ п.9.1
            )
            .then((r) => r.data),

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/recovery/rejoin
    rejoin: (clusterId: number, nodeId: number) =>
        api
            .post<{ accepted: boolean; operation_id: number }>(
                `/api/clusters/${clusterId}/recovery/rejoin`,
                { node_id: nodeId } satisfies RejoinPayload
            )
            .then((r) => r.data),

    // ТЗ п.9.1: POST /api/clusters/{cluster_id}/recovery/cancel
    cancel: (clusterId: number) =>
        api
            .post(`/api/clusters/${clusterId}/recovery/cancel`)
            .then((r) => r.data), // [MINOR FIX] добавлен unwrap

    // ТЗ п.9.1: GET /api/clusters/{cluster_id}/recovery/status
    getStatus: (clusterId: number) =>
        api
            .get<{ active_operation: RecoveryOperationStatus | null }>(
                `/api/clusters/${clusterId}/recovery/status`
            )
            .then((r) => r.data),
}