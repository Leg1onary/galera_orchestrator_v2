<template>
  <div class="tab-content max-w-lg">
    <div v-if="isLoading" class="py-8 text-center text-muted-color text-sm">Loading…</div>

    <form v-else-if="form" class="space-y-5" @submit.prevent="save">
      <div class="field-group">
        <label class="field-label">
          Polling interval (seconds)
          <span class="field-hint">How often backend polls node status via SSH/DB</span>
        </label>
        <InputNumber
            v-model="form.polling_interval_sec"
            :min="5" :max="300"
            class="w-full" size="small"
        />
      </div>

      <div class="field-group">
        <label class="field-label">
          Event log limit
          <span class="field-hint">Maximum number of events stored per cluster</span>
        </label>
        <InputNumber
            v-model="form.event_log_limit"
            :min="100" :max="10000"
            class="w-full" size="small"
        />
      </div>

      <div class="field-group">
        <label class="field-label">
          Timezone
          <span class="field-hint">Used for displaying timestamps in the UI</span>
        </label>
        <InputText
            v-model="form.timezone"
            placeholder="Europe/Moscow"
            class="w-full" size="small"
        />
      </div>

      <div v-if="apiError" class="error-alert">
        <i class="pi pi-exclamation-circle" />
        {{ apiError }}
      </div>

      <div class="flex items-center gap-3">
        <Button
            label="Save settings"
            icon="pi pi-check"
            type="submit"
            :loading="saving"
        />
        <span v-if="savedAt" class="text-xs text-muted-color">
          Saved at {{ savedAt }}
        </span>
      </div>

      <div class="system-meta" v-if="data">
        <span class="text-xs text-muted-color">Last updated: {{ data.updated_at }}</span>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { Button, InputNumber, InputText, useToast } from 'primevue'
import { settingsApi, type SystemSettingsFull } from '@/api/settings'
import { useSettingsStore } from '@/stores/settings'

const qc = useQueryClient()
const toast = useToast()
const settingsStore = useSettingsStore()

const { data, isLoading } = useQuery({
  queryKey: ['system-settings'],
  queryFn: () => settingsApi.getSystem(),
})

const form = reactive({ polling_interval_sec: 30, event_log_limit: 1000, timezone: 'UTC' })

watch(data, (val) => {
  if (val) {
    form.polling_interval_sec = val.polling_interval_sec
    form.event_log_limit = val.event_log_limit
    form.timezone = val.timezone
  }
}, { immediate: true })

const saving = ref(false)
const apiError = ref<string | null>(null)
const savedAt = ref<string | null>(null)

async function save() {
  saving.value = true
  apiError.value = null
  try {
    await settingsApi.patchSystem({
      polling_interval_sec: form.polling_interval_sec,
      event_log_limit: form.event_log_limit,
      timezone: form.timezone,
    })
    // Синхронизируем Pinia store (используется в events.ts для trim лимита)
    settingsStore.loaded = false
    await settingsStore.load()
    qc.invalidateQueries({ queryKey: ['system-settings'] })
    savedAt.value = new Date().toLocaleTimeString()
    toast.add({ severity: 'success', summary: 'Settings saved', life: 2500 })
  } catch (err: any) {
    apiError.value = err?.response?.data?.detail ?? err.message
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.field-group { display: flex; flex-direction: column; gap: 0.25rem; }
.field-label { font-size: var(--text-sm); font-weight: 500; color: var(--color-text); }
.field-hint { display: block; font-size: var(--text-xs); color: var(--color-text-muted); font-weight: 400; margin-top: 0.125rem; }
.error-alert { display: flex; align-items: center; gap: 0.5rem; padding: 0.625rem 0.75rem; background: color-mix(in oklch, var(--color-error) 10%, transparent); color: var(--color-error); border-radius: var(--radius-sm); font-size: var(--text-sm); }
.system-meta { padding-top: var(--space-4); border-top: 1px solid var(--color-divider); }
</style>