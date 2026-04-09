// ТЗ раздел 6.2: Header управляет выбором контура и кластера.
// При смене cluster_id — инвалидировать Vue Query и переподключить WS.
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { useQueryClient } from '@tanstack/vue-query'

export interface Contour {
    id: number
    name: string
}

export interface Cluster {
    id: number
    name: string
    contour_id: number
}

interface ClusterState {
    contours: Contour[]
    clusters: Cluster[]
    selectedContourId: number | null
    selectedClusterId: number | null
    loading: boolean
}

export const useClusterStore = defineStore('cluster', {
    state: (): ClusterState => ({
        contours: [],
        clusters: [],
        selectedContourId: null,
        selectedClusterId: null,
        loading: false,
    }),

    getters: {
        selectedCluster: (state): Cluster | null =>
            state.clusters.find((c) => c.id === state.selectedClusterId) ?? null,

        clustersForContour: (state): Cluster[] =>
            state.selectedContourId
                ? state.clusters.filter((c) => c.contour_id === state.selectedContourId)
                : state.clusters,
    },

    actions: {
        async loadContours() {
            this.loading = true
            try {
                const { data } = await api.get<Contour[]>('/api/contours')
                this.contours = data
                // Автовыбор первого контура если ничего не выбрано
                if (!this.selectedContourId && data.length > 0) {
                    await this.selectContour(data[0].id)
                }
            } finally {
                this.loading = false
            }
        },

        async loadClusters(contourId?: number) {
            const params = contourId ? { contour_id: contourId } : {}
            const { data } = await api.get<Cluster[]>('/api/clusters', { params })
            this.clusters = data
            // Автовыбор первого кластера
            if (!this.selectedClusterId && data.length > 0) {
                this.selectedClusterId = data[0].id
            }
        },

        async selectContour(contourId: number) {
            this.selectedContourId = contourId
            this.selectedClusterId = null
            await this.loadClusters(contourId)
        },

        // ТЗ 6.2: при смене кластера инвалидируем все cluster-scoped Vue Query запросы
        // и переподключаем WS. queryClient передаётся снаружи (из компонента)
        // чтобы не создавать circular dep с vue-query.
        async selectCluster(clusterId: number, queryClient?: ReturnType<typeof useQueryClient>) {
            this.selectedClusterId = clusterId
            // Инвалидируем все запросы с ключом ['cluster', *]
            queryClient?.invalidateQueries({ queryKey: ['cluster'] })
            // WS переподключение делает AppLayout через watch(selectedClusterId)
        },
    },

    // Persist selectedClusterId и selectedContourId в sessionStorage
    // чтобы F5 не сбрасывал выбор
    persist: {
        paths: ['selectedContourId', 'selectedClusterId'],
        storage: sessionStorage,
    },
})