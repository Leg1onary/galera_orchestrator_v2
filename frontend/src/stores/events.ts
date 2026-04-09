// ТЗ раздел 10.5, 6.2: event log кластера.
// Хранит последние N записей (из system_settings.event_log_limit).
// WS log_entry — prepend в начало, trim до лимита.
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { useSettingsStore } from '@/stores/settings'

export type EventLevel = 'INFO' | 'WARN' | 'ERROR'

export interface EventLogEntry {
    id: number
    ts: string
    level: EventLevel
    source: string
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
    }),

    actions: {
        async load(clusterId: number) {
            this.loading = true
            this.clusterId = clusterId
            try {
                const { data } = await api.get<EventLogEntry[]>(
                    `/api/clusters/${clusterId}/log`
                )
                this.entries = data
            } finally {
                this.loading = false
            }
        },

        // WS log_entry event → prepend, trim до лимита
        appendFromWs(entry: EventLogEntry) {
            const settings = useSettingsStore()
            const limit = settings.settings?.event_log_limit ?? 200
            this.entries = [entry, ...this.entries].slice(0, limit)
        },

        async clear(clusterId: number) {
            await api.delete(`/api/clusters/${clusterId}/log`)
            this.entries = []
        },
    },
})