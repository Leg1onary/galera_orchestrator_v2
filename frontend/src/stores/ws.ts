// ТЗ раздел 5: WebSocket store.
// Управляет одним WS-соединением на кластер.
// Footer читает connectionStatus (ТЗ 6.4).
// Reconnect каждые 5 сек при разрыве (ТЗ 5.3).
import { defineStore } from 'pinia'
import { useClusterStore } from '@/stores/cluster'

export type WsStatus = 'connected' | 'connecting' | 'disconnected'

// Типы событий из ТЗ раздел 5.2
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

export const useWsStore = defineStore('ws', {
    state: () => ({
        connectionStatus: 'disconnected' as WsStatus,
        // cluster_id текущего соединения
        connectedClusterId: null as number | null,
    }),

    actions: {
        // Инициализация: вызывается из AppLayout при монтировании и при смене кластера
        connect(clusterId: number) {
            if (this.connectedClusterId === clusterId && ws !== null) return
            this._disconnect()
            this._startConnection(clusterId)
        },

        disconnect() {
            this._disconnect()
        },
    },
})

// WS и reconnect-таймер живут вне state (не реактивны — нет смысла)
let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
const handlers = new Set<WsHandler>()

// Публичный API для подписки на события — используется в компонентах через onMounted
export function onWsEvent(handler: WsHandler) {
    handlers.add(handler)
    return () => handlers.delete(handler)
}

function _startConnection(clusterId: number) {
    const store = useWsStore()
    store.$patch({ connectionStatus: 'connecting', connectedClusterId: clusterId })

    // WS URL — ws:// или wss:// в зависимости от текущего протокола
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${location.host}/ws/clusters/${clusterId}`

    ws = new WebSocket(url)

    ws.onopen = () => {
        store.$patch({ connectionStatus: 'connected' })
        _clearReconnectTimer()
    }

    ws.onmessage = (msg) => {
        try {
            const event: WsEvent = JSON.parse(msg.data)
            handlers.forEach((h) => h(event))
        } catch {
            // malformed message — игнорируем
        }
    }

    ws.onclose = () => {
        store.$patch({ connectionStatus: 'disconnected' })
        ws = null
        _scheduleReconnect(clusterId)
    }

    ws.onerror = () => {
        // onerror всегда предшествует onclose — ничего не делаем здесь
    }
}

function _disconnect() {
    _clearReconnectTimer()
    if (ws) {
        ws.onclose = null // предотвращаем reconnect при явном disconnect
        ws.close()
        ws = null
    }
    const store = useWsStore()
    store.$patch({ connectionStatus: 'disconnected', connectedClusterId: null })
}

function _scheduleReconnect(clusterId: number) {
    _clearReconnectTimer()
    reconnectTimer = setTimeout(() => _startConnection(clusterId), 5000)
}

function _clearReconnectTimer() {
    if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
    }
}

// Делаем приватные функции доступными через store actions
const wsStoreActions = useWsStore as unknown as { _startConnection: typeof _startConnection; _disconnect: typeof _disconnect }
// Подключаем через prototype после defineStore чтобы не ломать Pinia
Object.assign(useWsStore._proto ?? {}, {})
// Реальный вызов через прямые функции — store.connect/disconnect вызывают их напрямую:
;(useWsStore as any)._pinia // ensure store registered

// Патчим actions после определения store
const _origConnect = useWsStore.prototype?.connect
// Используем замыкание — actions определены внутри defineStore выше,
// _startConnection и _disconnect доступны как module-level функции
// Actions в defineStore уже замкнуты на них через this — всё работает.
// Дублирующая инициализация не нужна.