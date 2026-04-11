// ТЗ раздел 16: системные настройки (polling interval, event log limit).
// CRUD сущностей (nodes, clusters и т.д.) выполняется через Vue Query напрямую
// в компонентах Settings — отдельный store для них избыточен.
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { extractApiError } from '@/utils/api'

export interface SystemSettings {
    id:                          number
    polling_interval_sec:        number
    event_log_limit:             number
    rolling_restart_timeout_sec: number
    updated_at:                  string
}

export type SystemSettingsPatch = Partial<Omit<SystemSettings, 'id' | 'updated_at'>>

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        settings:    null as SystemSettings | null,
        _loaded:     false,
        loading:     false,
        loadError:   null as string | null,
    }),

    getters: {
        isReady: (state): boolean => state._loaded && !state.loading,

        pollingIntervalSec: (state): number =>
            state.settings?.polling_interval_sec ?? 30,

        eventLogLimit: (state): number =>
            state.settings?.event_log_limit ?? 100,

        rollingRestartTimeoutSec: (state): number =>
            state.settings?.rolling_restart_timeout_sec ?? 300,
    },

    actions: {
        async load(force = false) {
            if (this._loaded && !force) return
            this.loading   = true
            this.loadError = null
            try {
                const { data } = await api.get<SystemSettings>('/api/settings/system')
                this.settings = data
                this._loaded  = true
            } catch (err) {
                this.loadError = extractApiError(err)
            } finally {
                this.loading = false
            }
        },

        async update(patch: SystemSettingsPatch) {
            if (Object.keys(patch).length === 0) return
            try {
                const { data } = await api.patch<SystemSettings>('/api/settings/system', patch)
                this.settings = data
            } catch (err) {
                throw err
            }
        },

        async reload() {
            this._loaded = false
            await this.load(true)
        },

        reset() {
            this.settings  = null
            this._loaded   = false
            this.loading   = false
            this.loadError = null
        },
    },
})
