import { defineStore } from 'pinia'

export type WsStatus = 'connected' | 'connecting' | 'reconnecting' | 'disconnected'

// [BLOCKER FIX] ТЗ п.5.2: только зафиксированные события. 'operation_cancelled' удалён.
export type WsEventType =
    | 'node_state_changed'
    | 'arbitrator_state_changed'
    | 'operation_started'
    | 'operation_progress'
    | 'operation_finished'
    | 'log_entry'

export interface WsEvent {
    event: WsEventType
    cluster_id: number
    ts: string
    payload: Record<string, unknown>
}

type WsHandler = (event: WsEvent) => void

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
const handlers = new Set<WsHandler>()

export const useWsStore = defineStore('ws', {
    state: () => ({
        connectionStatus: 'disconnected' as WsStatus,
        connectedClusterId: null as number | null,
        // [BLOCKER FIX] ТЗ п.8: polling fallback флаг
        pollingFallbackActive: false,
    }),

    actions: {
        connect(clusterId: number) {
            if (this.connectedClusterId === clusterId && ws !== null) return
            _disconnect(this)
            _startConnection(clusterId, this)
        },

        disconnect() {
            _disconnect(this)
        },

        on(handler: WsHandler): () => void {
            handlers.add(handler)
            return () => handlers.delete(handler)
        },

        // [MAJOR FIX] явная очистка всех handlers (при смене кластера)
        clearHandlers() {
            handlers.clear()
        },
    },
})

type WsStoreInstance = ReturnType<typeof useWsStore>

function _startConnection(clusterId: number, store: WsStoreInstance) {
    store.$patch({ connectionStatus: 'connecting', connectedClusterId: clusterId })

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${protocol}://${location.host}/ws/clusters/${clusterId}`)

    ws.onopen = () => {
        store.$patch({
            connectionStatus: 'connected',
            pollingFallbackActive: false, // [BLOCKER FIX] WS восстановлен — polling off
        })
        _clearReconnectTimer()
    }

    ws.onmessage = (msg) => {
        try {
            const event: WsEvent = JSON.parse(msg.data)
            if (event.cluster_id === store.connectedClusterId) {
                handlers.forEach((h) => h(event))
            }
        } catch {
            // malformed message
        }
    }

    ws.onclose = () => {
        store.$patch({
            connectionStatus: 'disconnected',
            pollingFallbackActive: true, // [BLOCKER FIX] ТЗ п.8: включаем polling fallback
        })
        ws = null
        _scheduleReconnect(clusterId, store)
    }

    ws.onerror = () => {
        // onerror всегда предшествует onclose
    }
}

function _disconnect(store: WsStoreInstance) {
    _clearReconnectTimer()
    if (ws) {
        ws.onclose = null
        ws.close()
        ws = null
    }
    store.$patch({
        connectionStatus: 'disconnected',
        connectedClusterId: null,
        pollingFallbackActive: false,
    })
}

function _scheduleReconnect(clusterId: number, store: WsStoreInstance) {
    _clearReconnectTimer()
    // [MINOR FIX] ТЗ п.5.3: 5 сек до reconnect — зафиксировано в ТЗ
    store.$patch({ connectionStatus: 'reconnecting' })
    reconnectTimer = setTimeout(() => _startConnection(clusterId, store), 5000)
}

function _clearReconnectTimer() {
    if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
    }
}

export function onWsEvent(handler: WsHandler): () => void {
    const wsStore = useWsStore()
    return wsStore.on(handler)
}