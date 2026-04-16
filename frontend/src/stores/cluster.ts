// ТЗ раздел 6.2: Header управляет выбором контура и кластера.
// При смене cluster_id — инвалидировать Vue Query и переподключить WS.
// Персистентность: selectedContourId + selectedClusterId хранятся в localStorage
// под ключами go2-contour-id и go2-cluster-id. Валидируются при каждом load.
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import type { QueryClient } from '@tanstack/vue-query'

const LS_CLUSTER = 'go2-cluster-id'
const LS_CONTOUR = 'go2-contour-id'

export interface Contour {
    id: number
    name: string
}

export interface ActiveOperation {
    id: number
    type: 'recovery-bootstrap' | 'recovery-rejoin' | 'rolling-restart' | 'node-action'
    status: 'pending' | 'running' | 'success' | 'failed' | 'cancel_requested' | 'cancelled'
    started_at: string | null
}

export interface Cluster {
    id: number
    name: string
    contour_id: number
    status: 'healthy' | 'degraded' | 'critical' | null
    active_operation: ActiveOperation | null
}

interface ClusterState {
    contours: Contour[]
    clusters: Cluster[]
    selectedContourId: number | null
    selectedClusterId: number | null
    loading: boolean
    error: string | null
}

function lsGetId(key: string): number | null {
    const v = localStorage.getItem(key)
    if (!v) return null
    const n = Number(v)
    return Number.isFinite(n) && n > 0 ? n : null
}

export const useClusterStore = defineStore('cluster', {
    state: (): ClusterState => ({
        contours: [],
        clusters: [],
        selectedContourId: null,
        selectedClusterId: null,
        loading: false,
        error: null,
    }),

    getters: {
        selectedCluster: (state): Cluster | null =>
            state.clusters.find((c) => c.id === state.selectedClusterId) ?? null,

        clustersForContour: (state): Cluster[] =>
            state.selectedContourId
                ? state.clusters.filter((c) => c.contour_id === state.selectedContourId)
                : state.clusters,

        isClusterLocked: (state): boolean => {
            const cluster = state.clusters.find((c) => c.id === state.selectedClusterId)
            const op = cluster?.active_operation
            if (!op) return false
            return ['pending', 'running', 'cancel_requested'].includes(op.status)
        },
    },

    actions: {
        async loadContours() {
            this.loading = true
            this.error = null
            try {
                const { data } = await api.get<Contour[]>('/api/contours')
                this.contours = data

                // Восстанавливаем контур из localStorage, валидируем что он существует
                const savedContour = lsGetId(LS_CONTOUR)
                const validContour = savedContour && data.find((c) => c.id === savedContour)
                    ? savedContour
                    : data[0]?.id ?? null

                if (validContour) {
                    await this.selectContour(validContour)
                }
            } catch (e: any) {
                this.error = e?.response?.data?.detail ?? 'Failed to load contours'
            } finally {
                this.loading = false
            }
        },

        async loadClusters(contourId?: number) {
            this.loading = true
            this.error = null
            try {
                const params = contourId ? { contour_id: contourId } : {}
                const { data } = await api.get<Cluster[]>('/api/clusters', { params })
                this.clusters = data

                // Восстанавливаем кластер из localStorage, валидируем что он существует
                const savedCluster = lsGetId(LS_CLUSTER)
                if (savedCluster && data.find((c) => c.id === savedCluster)) {
                    this.selectedClusterId = savedCluster
                } else if (data.length > 0) {
                    // Сохранённый ID невалиден — берём первый и обновляем LS
                    this.selectedClusterId = data[0].id
                    localStorage.setItem(LS_CLUSTER, String(data[0].id))
                }
            } catch (e: any) {
                this.error = e?.response?.data?.detail ?? 'Failed to load clusters'
            } finally {
                this.loading = false
            }
        },

        async selectContour(contourId: number) {
            this.selectedContourId = contourId
            localStorage.setItem(LS_CONTOUR, String(contourId))
            // При смене контура сбрасываем выбранный кластер только в памяти,
            // LS_CLUSTER обновится в loadClusters когда найдём валидный
            this.selectedClusterId = null
            await this.loadClusters(contourId)
        },

        async selectCluster(clusterId: number, queryClient?: QueryClient) {
            this.selectedClusterId = clusterId
            localStorage.setItem(LS_CLUSTER, String(clusterId))
            queryClient?.invalidateQueries({ queryKey: ['cluster'] })
            // WS переподключение делает AppLayout через watch(selectedClusterId)
        },

        /**
         * Сбросить active_operation у конкретного кластера (вызывается из WS-хандлера operation_finished).
         */
        clearActiveOperation(clusterId: number) {
            const idx = this.clusters.findIndex((c) => c.id === clusterId)
            if (idx !== -1) {
                this.clusters = this.clusters.map((c) =>
                    c.id === clusterId ? { ...c, active_operation: null } : c
                )
            }
        },

        /**
         * Установить / обновить active_operation у конкретного кластера.
         */
        setActiveOperation(clusterId: number, op: ActiveOperation | null) {
            this.clusters = this.clusters.map((c) =>
                c.id === clusterId ? { ...c, active_operation: op } : c
            )
        },
    },
})
