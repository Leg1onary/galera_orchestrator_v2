import { defineStore } from 'pinia'

export type WsStatus = 'connected' | 'connecting' | 'disconnected'

export type WsEventType =
    | 'node_state_changed'
    | 'arbitrator_state_changed'
    | 'operation_started'
    | 'operation_progress'
    | 'operation_finished'
    | 'operation_cancelled'
    | 'log_entry'

export interface WsEvent {
    event: WsEventType
    cluster_id: number
    ts: string
    payload: Record<string, unknown>
}

type WsHandler = (event: WsEvent) => void

// Module-level — вне реактивного state
let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
const handlers = new Set<WsHandler>()

export const useWsStore = defineStore('ws', {
    state: () => ({
        connectionStatus: 'disconnected' as WsStatus,
        connectedClusterId: null as number | null,
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

        // ← вот метод .on() который используется в recoveryStore
        on(handler: WsHandler): () => void {
            handlers.add(handler)
            return () => handlers.delete(handler)
        },
    },
})

type WsStoreInstance = ReturnType<typeof useWsStore>

function _startConnection(clusterId: number, store: WsStoreInstance) {
    store.$patch({ connectionStatus: 'connecting', connectedClusterId: clusterId })

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${protocol}://${location.host}/ws/clusters/${clusterId}`)

    ws.onopen = () => {
        store.$patch({ connectionStatus: 'connected' })
        _clearReconnectTimer()
    }

    ws.onmessage = (msg) => {
        try {
            const event: WsEvent = JSON.parse(msg.data)
            // ТЗ 5.2: фильтрация по cluster_id
            if (event.cluster_id === store.connectedClusterId) {
                handlers.forEach((h) => h(event))
            }
        } catch {
            // malformed message
        }
    }

    ws.onclose = () => {
        store.$patch({ connectionStatus: 'disconnected' })
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
        ws.onclose = null  // предотвращаем reconnect при явном disconnect
        ws.close()
        ws = null
    }
    store.$patch({ connectionStatus: 'disconnected', connectedClusterId: null })
}

function _scheduleReconnect(clusterId: number, store: WsStoreInstance) {
    _clearReconnectTimer()
    reconnectTimer = setTimeout(() => _startConnection(clusterId, store), 5000)
}

function _clearReconnectTimer() {
    if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
    }
}

// Хелпер для использования в компонентах через onMounted/onUnmounted
// Эквивалентен useWsStore().on(handler)
export function onWsEvent(handler: WsHandler): () => void {
    const wsStore = useWsStore()
    return wsStore.on(handler)
}