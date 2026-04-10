// ТЗ раздел 10.5, 6.2: event log кластера.
// Хранит последние N записей (из system_settings.event_log_limit).
// WS log_entry — prepend в начало, trim до лимита.
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { useSettingsStore } from '@/stores/settings'

export type EventLevel = 'INFO' | 'WARN' | 'ERROR'

// [MINOR FIX] ТЗ п.2.6: source — строго зафиксированные значения
export type EventSource =
    | 'system'
    | 'ui'
    | 'diagnostics'
    | 'ws'
    | 'ssh'
    | 'auth'
    | 'recovery'
    | 'maintenance'

export interface EventLogEntry {
    id: number
    ts: string
    level: EventLevel
    source: EventSource
    message: string
    node_id: number | null
    arbitrator_id: number | null
    cluster_id: number | null
    operation_id: number | null
}

export const useEventsStore = defineStore('events', {
    state: () => ({
        entries: [] as EventLogEntry[],
        clusterId: null as number | null,
        loading: false,
        error: null as string | null, // [MAJOR FIX]
    }),

    actions: {
        async load(clusterId: number) {
            // [MAJOR FIX] сбрасываем записи при смене кластера — нет мигания чужих данных
            if (this.clusterId !== clusterId) {
                this.entries = []
            }
            this.loading = true
            this.clusterId = clusterId
            this.error = null
            try {
                const { data } = await api.get<EventLogEntry[]>(
                    `/api/clusters/${clusterId}/log`
                )
                this.entries = data
            } catch (e: any) {
                // [MAJOR FIX] фиксируем ошибку для EventLog компонента
                this.error = e?.response?.data?.detail ?? 'Failed to load event log'
            } finally {
                this.loading = false
            }
        },

        // WS log_entry event → prepend, trim до лимита
        appendFromWs(entry: EventLogEntry) {
            // [MAJOR FIX] только события текущего кластера
            if (entry.cluster_id !== this.clusterId) return

            const settingsStore = useSettingsStore()
            // Проверяем оба возможных пути к event_log_limit
            const limit = settingsStore.system?.event_log_limit ?? 200
            this.entries = [entry, ...this.entries].slice(0, limit)
        },

        async clear(clusterId: number) {
            // [MINOR FIX] пробрасываем ошибку — компонент покажет 409 или другой статус
            await api.delete(`/api/clusters/${clusterId}/log`)
            this.entries = []
        },
    },
})