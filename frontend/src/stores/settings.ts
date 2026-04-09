// ТЗ раздел 16: системные настройки (polling interval, event log limit, timezone).
// CRUD сущностей (nodes, clusters и т.д.) выполняется через Vue Query напрямую
// в компонентах Settings — отдельный store для них избыточен.
import { defineStore } from 'pinia'
import { api } from '@/api/client'

export interface SystemSettings {
    id: number
    polling_interval_sec: number
    event_log_limit: number
    timezone: string
    updated_at: string
}

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        settings: null as SystemSettings | null,
        loaded: false,
    }),

    actions: {
        async load() {
            if (this.loaded) return
            const { data } = await api.get<SystemSettings>('/api/settings/system')
            this.settings = data
            this.loaded = true
        },

        async update(patch: Partial<Omit<SystemSettings, 'id' | 'updated_at'>>) {
            const { data } = await api.patch<SystemSettings>('/api/settings/system', patch)
            this.settings = data
        },
    },
})