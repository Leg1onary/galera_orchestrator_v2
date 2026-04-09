// ТЗ раздел 8, 19.1: cluster_operations — активная операция на кластер.
// Источник правды — WS события operation_started / operation_finished.
// REST-полинг как fallback при первой загрузке страницы.
import { defineStore } from 'pinia'
import { api } from '@/api/client'

export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'
    | 'failed'
    | 'cancel_requested'
    | 'cancelled'

export type OperationType =
    | 'recovery_bootstrap'
    | 'recovery_rejoin'
    | 'rolling_restart'
    | 'node_action'

export interface ClusterOperation {
    id: number
    cluster_id: number
    type: OperationType
    status: OperationStatus
    started_at: string | null
    finished_at: string | null
    created_by: string | null
    target_node_id: number | null
    details_json: string | null
    error_message: string | null
}

interface OperationsState {
    // Одна активная операция на cluster_id
    activeOperations: Record<number, ClusterOperation | null>
}

export const useOperationsStore = defineStore('operations', {
    state: (): OperationsState => ({
        activeOperations: {},
    }),

    getters: {
        activeOperation: (state) => (clusterId: number) =>
            state.activeOperations[clusterId] ?? null,

        isLocked: (state) => (clusterId: number) => {
            const op = state.activeOperations[clusterId]
            return op !== null && ['pending', 'running', 'cancel_requested'].includes(op?.status ?? '')
        },
    },

    actions: {
        // Вызывается при монтировании Recovery/Maintenance страниц
        async fetchActive(clusterId: number) {
            try {
                const { data } = await api.get(
                    `/api/clusters/${clusterId}/recovery/status`
                )
                this.activeOperations[clusterId] = data.active_operation ?? null
            } catch {
                this.activeOperations[clusterId] = null
            }
        },

        // Вызывается WS handler-ом в AppLayout
        handleWsEvent(event: {
            event: string
            payload: Record<string, unknown>
            cluster_id: number
        }) {
            const { event: type, payload, cluster_id } = event

            if (type === 'operation_started') {
                this.activeOperations[cluster_id] = payload as unknown as ClusterOperation
            }
            if (type === 'operation_progress') {
                const op = this.activeOperations[cluster_id]
                if (op) {
                    this.activeOperations[cluster_id] = { ...op, ...(payload as object) }
                }
            }
            if (type === 'operation_finished') {
                this.activeOperations[cluster_id] = payload as unknown as ClusterOperation
            }
        },

        clear(clusterId: number) {
            this.activeOperations[clusterId] = null
        },
    },
})