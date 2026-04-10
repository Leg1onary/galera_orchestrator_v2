// ТЗ раздел 8, 19.1: cluster_operations — активная операция на кластер.
// Источник правды — WS события operation_started / operation_finished.
// REST-опрос как fallback при первой загрузке страницы.
import { defineStore } from 'pinia'
import { api } from '@/api/client'

export type OperationStatus =
    | 'pending'
    | 'running'
    | 'success'
    | 'failed'
    | 'cancel_requested'
    | 'cancelled'

// [MAJOR FIX] ТЗ п.2.8: type через дефис, не underscore
export type OperationType =
    | 'recovery-bootstrap'
    | 'recovery-rejoin'
    | 'rolling-restart'
    | 'node-action'

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
    activeOperations: Record<number, ClusterOperation | null>
}

export const useOperationsStore = defineStore('operations', {
    state: (): OperationsState => ({
        activeOperations: {},
    }),

    getters: {
        activeOperation: (state) => (clusterId: number): ClusterOperation | null =>
            state.activeOperations[clusterId] ?? null,

        isLocked: (state) => (clusterId: number): boolean => {
            const op = state.activeOperations[clusterId]
            // [MINOR FIX] op != null покрывает и undefined и null
            return op != null && ['pending', 'running', 'cancel_requested'].includes(op.status)
        },
    },

    actions: {
        // [BLOCKER FIX] ТЗ п.9.1: опрашиваем оба endpoint'а — recovery + maintenance status.
        // Активная операция может быть на любом из них.
        // Альтернатива: GET /api/clusters/{id}/status тоже содержит active_operation.
        async fetchActive(clusterId: number) {
            try {
                const [recoveryRes, maintenanceRes] = await Promise.allSettled([
                    api.get(`/api/clusters/${clusterId}/recovery/status`),
                    api.get(`/api/clusters/${clusterId}/maintenance/status`),
                ])

                const recoveryOp =
                    recoveryRes.status === 'fulfilled'
                        ? recoveryRes.value.data.active_operation ?? null
                        : null

                const maintenanceOp =
                    maintenanceRes.status === 'fulfilled'
                        ? maintenanceRes.value.data.active_operation ?? null
                        : null

                // Берём ту что активна (pending/running/cancel_requested)
                const active = [recoveryOp, maintenanceOp].find(
                    (op) => op != null && ['pending', 'running', 'cancel_requested'].includes(op.status)
                ) ?? recoveryOp ?? maintenanceOp ?? null

                // [MAJOR FIX] spread вместо прямого присвоения — Vue 3 reactivity
                this.activeOperations = { ...this.activeOperations, [clusterId]: active }
            } catch {
                this.activeOperations = { ...this.activeOperations, [clusterId]: null }
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
                // payload — полный объект ClusterOperation при старте
                this.activeOperations = {
                    ...this.activeOperations,
                    [cluster_id]: payload as unknown as ClusterOperation,
                }
            }

            if (type === 'operation_progress') {
                const op = this.activeOperations[cluster_id]
                if (op) {
                    this.activeOperations = {
                        ...this.activeOperations,
                        [cluster_id]: { ...op, ...(payload as Partial<ClusterOperation>) },
                    }
                }
            }

            // [MAJOR FIX] operation_finished — merge, не замена:
            // payload содержит только status + finished_at, не весь объект
            if (type === 'operation_finished') {
                const op = this.activeOperations[cluster_id]
                if (op) {
                    this.activeOperations = {
                        ...this.activeOperations,
                        [cluster_id]: { ...op, ...(payload as Partial<ClusterOperation>) },
                    }
                }
            }
        },

        clear(clusterId: number) {
            this.activeOperations = { ...this.activeOperations, [clusterId]: null }
        },
    },
})