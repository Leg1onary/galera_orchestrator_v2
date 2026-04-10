// ТЗ раздел 16: системные настройки (polling interval, event log limit, timezone).
// CRUD сущностей (nodes, clusters и т.д.) выполняется через Vue Query напрямую
// в компонентах Settings — отдельный store для них избыточен.
import { defineStore } from 'pinia'
import { api } from '@/api/client'
import { extractApiError } from '@/utils/api'

export interface SystemSettings {
    id:                          number
    polling_interval_sec:        number
    event_log_limit:             number
    timezone:                    string
    rolling_restart_timeout_sec: number
    updated_at:                  string
}

export type SystemSettingsPatch = Partial<Omit<SystemSettings, 'id' | 'updated_at'>>

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        settings:    null as SystemSettings | null,
        // MAJOR fix: _loaded — соглашение "не трогать снаружи напрямую, только через reload()"
        _loaded:     false,
        loading:     false,
        loadError:   null as string | null,
        // MAJOR fix: updateError убран — update() только пробрасывает ошибку,
        // компонент сам решает как её показать. Двойная ответственность устранена.
    }),

    getters: {
        isReady: (state): boolean => state._loaded && !state.loading,

        // MAJOR fix: дефолты приведены к значениям из SystemTab и ТЗ
        pollingIntervalSec: (state): number =>
            state.settings?.polling_interval_sec ?? 30,

        eventLogLimit: (state): number =>
            state.settings?.event_log_limit ?? 1000,

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
                // MAJOR fix: extractApiError вместо дублирующегося chain
                this.loadError = extractApiError(err)
                // _loaded остаётся false — следующий вызов повторит попытку
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
                // MAJOR fix: только пробрасываем — компонент обрабатывает через extractApiError
                throw err
            }
        },

        // MAJOR fix: reload вместо forceLoad — семантически точнее,
        // SystemTab вызывает settingsStore.reload() после сохранения
        async reload() {
            this._loaded = false
            await this.load(true)
        },

        // MINOR fix: сброс при logout
        reset() {
            this.settings  = null
            this._loaded   = false
            this.loading   = false
            this.loadError = null
        },
    },
})