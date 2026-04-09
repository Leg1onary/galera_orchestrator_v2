import { defineStore } from 'pinia'

/**
 * Cluster store — manages the currently selected contour and cluster.
 *
 * STUB — Phase 1 / Phase 5 implementation.
 *
 * Phase 1 responsibilities:
 * - Load available contours from GET /api/contours
 * - Load clusters for selected contour from GET /api/clusters?contour_id=N
 * - Persist selection across navigation (sessionStorage or in-memory)
 *
 * Phase 5 responsibilities:
 * - Invalidate all Vue Query queries when cluster_id changes
 * - Trigger WebSocket reconnection via wsStore when cluster_id changes
 *
 * Per ТЗ section 6.2: currentContourId and currentClusterId are the
 * source of truth for all cluster-scoped API calls and WebSocket connections.
 */
export const useClusterStore = defineStore('cluster', {
    state: () => ({
        /**
         * Currently selected contour ID (1 = test, 2 = prod per seed data).
         * Null means nothing selected yet.
         */
        currentContourId: null,

        /**
         * Currently selected cluster ID.
         * Null means nothing selected yet.
         */
        currentClusterId: null,

        /**
         * List of available contours loaded from the API.
         * Format: [{ id: 1, name: 'test' }, { id: 2, name: 'prod' }]
         */
        contours: [],

        /**
         * List of clusters available for the selected contour.
         * Format: [{ id: 1, name: 'cluster-a', contour_id: 1 }]
         */
        clusters: [],

        /**
         * Whether contours and clusters are currently being loaded.
         */
        loading: false,
    }),

    getters: {
        currentContour: (state) =>
            state.contours.find((c) => c.id === state.currentContourId) ?? null,

        currentCluster: (state) =>
            state.clusters.find((c) => c.id === state.currentClusterId) ?? null,

        hasSelection: (state) =>
            state.currentContourId !== null && state.currentClusterId !== null,
    },

    actions: {
        /**
         * Load contours and auto-select the first cluster.
         * STUB — implement in Phase 1.
         */
        async loadContours() {
            // TODO Phase 1: fetch GET /api/contours and GET /api/clusters
        },

        /**
         * Change the active contour and reset cluster selection.
         * STUB — implement in Phase 5 (triggers Vue Query invalidation + WS reconnect).
         * @param {number} contourId
         */
        async setContour(contourId) {
            // TODO Phase 5: invalidate queries, reconnect WS
            this.currentContourId = contourId
            this.currentClusterId = null
            this.clusters = []
        },

        /**
         * Change the active cluster.
         * STUB — implement in Phase 5 (triggers Vue Query invalidation + WS reconnect).
         * @param {number} clusterId
         */
        async setCluster(clusterId) {
            // TODO Phase 5: queryClient.invalidateQueries(), wsStore.reconnect()
            this.currentClusterId = clusterId
        },
    },
})