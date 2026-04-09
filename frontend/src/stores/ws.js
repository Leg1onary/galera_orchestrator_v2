import { defineStore } from 'pinia'

/**
 * WebSocket store — manages the cluster-scoped WebSocket connection.
 *
 * STUB — Phase 1 implementation.
 *
 * Per ТЗ section 5:
 * - Endpoint: WS /ws/clusters/{cluster_id}
 * - Auth: httpOnly cookie sent automatically by browser on upgrade
 * - Reconnect: every 5 seconds on disconnect, show 'Disconnected' in Footer
 * - On reconnect: re-subscribe to current cluster_id
 * - Events to handle: node_state_changed, arbitrator_state_changed,
 *   operation_started, operation_progress, operation_finished, log_entry
 *
 * Per ТЗ section 6.4: Footer reads connected/reconnecting from this store.
 */
export const useWsStore = defineStore('ws', {
    state: () => ({
        /**
         * Whether the WebSocket is currently connected.
         * Shown in Footer per ТЗ section 6.4.
         */
        connected: false,

        /**
         * Whether a reconnection attempt is in progress.
         */
        reconnecting: false,

        /**
         * The cluster_id this WebSocket is currently subscribed to.
         * Null when not connected or no cluster selected.
         */
        subscribedClusterId: null,

        /**
         * Number of reconnect attempts since last successful connection.
         * Used to implement exponential backoff in Phase 1 (capped at 5 sec per ТЗ).
         */
        reconnectAttempts: 0,

        /**
         * Last WebSocket error message, if any.
         * Shown in Footer or as a tooltip.
         */
        lastError: null,
    }),

    getters: {
        /**
         * Human-readable connection status for Footer display.
         * Per ТЗ section 6.4.
         */
        statusLabel: (state) => {
            if (state.connected) return 'Connected'
            if (state.reconnecting) return 'Reconnecting...'
            return 'Disconnected'
        },

        /**
         * CSS status colour for Footer indicator dot.
         */
        statusColor: (state) => {
            if (state.connected) return 'var(--color-synced)'
            if (state.reconnecting) return 'var(--color-warning)'
            return 'var(--color-offline)'
        },
    },

    actions: {
        /**
         * Connect to WS /ws/clusters/{clusterId}.
         * STUB — implement in Phase 1.
         * @param {number} clusterId
         */
        connect(clusterId) {
            // TODO Phase 1:
            // this._socket = new WebSocket(`/ws/clusters/${clusterId}`)
            // attach onopen, onmessage, onerror, onclose handlers
            // onmessage dispatches events to relevant stores
            // onclose starts reconnect loop (5s per ТЗ)
            console.debug('[wsStore] connect() stub — Phase 1 pending', clusterId)
        },

        /**
         * Disconnect and clear reconnect timer.
         * STUB — implement in Phase 1.
         */
        disconnect() {
            // TODO Phase 1: close socket, clear reconnect timer
            this.connected = false
            this.reconnecting = false
            this.subscribedClusterId = null
            console.debug('[wsStore] disconnect() stub')
        },

        /**
         * Reconnect to the current cluster (used after cluster switch).
         * STUB — implement in Phase 1.
         */
        reconnect() {
            if (this.subscribedClusterId !== null) {
                this.disconnect()
                this.connect(this.subscribedClusterId)
            }
        },
    },
})