// ТЗ раздел 6.2: Header управляет выбором контура и кластера.
// При смене cluster_id — инвалидировать Vue Query и переподключить WS.
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import type { QueryClient } from '@tanstack/vue-query'

export interface Contour {
    id: number
    name: string
}

// [BLOCKER FIX] ТЗ п.19.1: cluster-level lock
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
    // [BLOCKER FIX] ТЗ п.7.1 + п.9.2: cluster health status
    status: 'healthy' | 'degraded' | 'critical' | null
    // [BLOCKER FIX] ТЗ п.19.1: для cluster-level lock
    active_operation: ActiveOperation | null
}

interface ClusterState {
    contours: Contour[]
    clusters: Cluster[]
    selectedContourId: number | null
    selectedClusterId: number | null
    loading: boolean
    error: string | null // [MAJOR FIX]
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

        // [BLOCKER FIX] ТЗ п.19.1: удобный геттер для cluster lock
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
                if (!this.selectedContourId && data.length > 0) {
                    await this.selectContour(data[0].id)
                }
            } catch (e: any) {
                // [MAJOR FIX] фиксируем ошибку — компоненты могут показать error state
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

                const saved = sessionStorage.getItem('selectedClusterId')
                if (saved && data.find((c) => c.id === Number(saved))) {
                    this.selectedClusterId = Number(saved)
                } else if (!this.selectedClusterId && data.length > 0) {
                    this.selectedClusterId = data[0].id
                }
            } catch (e: any) {
                this.error = e?.response?.data?.detail ?? 'Failed to load clusters'
            } finally {
                this.loading = false
            }
        },

        async selectContour(contourId: number) {
            this.selectedContourId = contourId
            this.selectedClusterId = null
            // [MAJOR FIX] при смене контура сбрасываем сохранённый выбор кластера
            sessionStorage.removeItem('selectedClusterId')
            await this.loadClusters(contourId)
        },

        // ТЗ 6.2: при смене кластера инвалидируем все cluster-scoped Vue Query запросы
        // queryClient передаётся снаружи (из компонента) — composable context required
        async selectCluster(clusterId: number, queryClient?: QueryClient) {
            this.selectedClusterId = clusterId
            sessionStorage.setItem('selectedClusterId', String(clusterId))
            queryClient?.invalidateQueries({ queryKey: ['cluster'] })
            // WS переподключение делает AppLayout через watch(selectedClusterId)
        },
    },
})