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
    // [BLOCKER FIX] ТЗ п.2.7 + п.14: rolling_restart_timeout_sec в system_settings
    rolling_restart_timeout_sec: number
    updated_at: string
}

export type SystemSettingsPatch = Partial<Omit<SystemSettings, 'id' | 'updated_at'>>

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        settings: null as SystemSettings | null,
        loaded: false,
        loading: false,
        // [BLOCKER FIX] хранить ошибку загрузки — UI может показать banner
        loadError: null as string | null,
        updateError: null as string | null,
    }),

    getters: {
        // Удобные геттеры для часто используемых значений
        pollingIntervalSec: (state): number =>
            state.settings?.polling_interval_sec ?? 5,
        eventLogLimit: (state): number =>
            state.settings?.event_log_limit ?? 200,
        rollingRestartTimeoutSec: (state): number =>
            state.settings?.rolling_restart_timeout_sec ?? 300,
    },

    actions: {
        // [BLOCKER FIX] try/catch + error state + force параметр
        async load(force = false) {
            if (this.loaded && !force) return
            this.loading = true
            this.loadError = null
            try {
                const { data } = await api.get<SystemSettings>('/api/settings/system')
                this.settings = data
                this.loaded = true
            } catch (err: any) {
                this.loadError = err?.response?.data?.detail ?? err.message
                // Не ставим loaded = true чтобы следующий вызов мог повторить попытку
            } finally {
                this.loading = false
            }
        },

        async update(patch: SystemSettingsPatch) {
            // [MAJOR FIX] guard против пустого patch
            if (Object.keys(patch).length === 0) return
            this.updateError = null
            try {
                const { data } = await api.patch<SystemSettings>('/api/settings/system', patch)
                this.settings = data
            } catch (err: any) {
                this.updateError = err?.response?.data?.detail ?? err.message
                throw err // пробрасываем — компонент может показать toast
            }
        },

        // [MAJOR FIX] принудительный сброс кэша
        async forceLoad() {
            this.loaded = false
            await this.load(true)
        },
    },
})