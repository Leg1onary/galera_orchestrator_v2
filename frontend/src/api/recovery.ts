import { api } from '@/api/client'

export type NodeGrastate = {
    node_id: number
    node_name: string
    host: string
    reachable: boolean           // SSH доступна
    safe_to_bootstrap: 0 | 1
    seqno: number                // -1 если нода запущена или не читается
    uuid: string | null
    error: string | null         // если SSH упала
}

export type RecoveryScanResult = {
    nodes: NodeGrastate[]
    recommended_bootstrap_node_id: number | null  // id с safe_to_bootstrap=1 и max seqno
    cluster_is_healthy: boolean  // если true — recovery не нужен
}

export type RecoveryOperationStatus = {
    operation_id: string
    state: 'pending' | 'running' | 'finished' | 'failed' | 'cancelled'
    current_step: string | null
    progress_pct: number         // 0–100
    message: string | null
    started_at: string | null
    finished_at: string | null
    error: string | null
}

export type RejoinPayload = {
    node_id: number
}

export const recoveryApi = {
    scan: (clusterId: number) =>
        api.post<RecoveryScanResult>(`/api/clusters/${clusterId}/recovery/scan`)
            .then((r) => r.data),

    bootstrap: (clusterId: number, nodeId: number, force = false) =>
        api.post<{ operation_id: string }>(`/api/clusters/${clusterId}/recovery/bootstrap`, {
            node_id: nodeId,
            force,
        }).then((r) => r.data),

    rejoin: (clusterId: number, nodeId: number) =>
        api.post<{ operation_id: string }>(`/api/clusters/${clusterId}/recovery/rejoin`, {
            node_id: nodeId,
        } satisfies RejoinPayload).then((r) => r.data),

    cancel: (clusterId: number) =>
        api.post(`/api/clusters/${clusterId}/recovery/cancel`),

    getStatus: (clusterId: number) =>
        api.get<RecoveryOperationStatus>(`/api/clusters/${clusterId}/recovery/status`)
            .then((r) => r.data),
}