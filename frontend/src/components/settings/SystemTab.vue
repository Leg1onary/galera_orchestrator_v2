<template>
  <div class="tab-content">
    <div v-if="isLoading" class="loading-state">Loading…</div>

    <form v-else-if="form" class="settings-form" @submit.prevent="save">
      <!-- MAJOR fix: InputNumber + label accessibility через inputId -->
      <div class="field-group">
        <label for="polling-interval" class="field-label">
          Polling interval (seconds)
          <span class="field-hint">How often backend polls node status via SSH/DB</span>
        </label>
        <InputNumber
            inputId="polling-interval"
            v-model="form.polling_interval_sec"
            :min="5" :max="300"
            class="field-input"
            size="small"
        />
      </div>

      <div class="field-group">
        <label for="event-log-limit" class="field-label">
          Event log limit
          <span class="field-hint">Maximum number of events stored per cluster</span>
        </label>
        <InputNumber
            inputId="event-log-limit"
            v-model="form.event_log_limit"
            :min="100" :max="10000"
            class="field-input"
            size="small"
        />
      </div>

      <div class="field-group">
        <label for="timezone" class="field-label">
          Timezone
          <span class="field-hint">Used for displaying timestamps in the UI</span>
        </label>
        <InputText
            id="timezone"
            v-model="form.timezone"
            placeholder="Europe/Moscow"
            class="field-input"
            size="small"
        />
      </div>

      <div v-if="apiError" class="error-alert">
        <i class="pi pi-exclamation-circle" />
        {{ apiError }}
      </div>

      <div class="form-footer">
        <Button label="Save settings" icon="pi pi-check" type="submit" :loading="saving" />
        <span v-if="savedAt" class="saved-at">Saved at {{ savedAt }}</span>
      </div>

      <!-- MINOR fix: v-if первым, форматирование даты -->
      <div v-if="data" class="system-meta">
        <span class="meta-text">
          Last updated: {{ formatDate(data.updated_at) }}
        </span>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import Button      from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText   from 'primevue/inputtext'
import { useToast } from 'primevue/usetoast'
import { settingsApi } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useSettingsStore } from '@/stores/settings'

const qc             = useQueryClient()
const toast          = useToast()
const settingsStore  = useSettingsStore()

const { data, isLoading } = useQuery({
  queryKey: ['system-settings'],
  queryFn:  () => settingsApi.getSystem(),
})

const form = reactive({
  polling_interval_sec: 30,
  event_log_limit:      1000,
  timezone:             'UTC',
})

watch(data, (val) => {
  if (!val) return
  form.polling_interval_sec = val.polling_interval_sec
  form.event_log_limit      = val.event_log_limit
  form.timezone             = val.timezone
}, { immediate: true })

const saving   = ref(false)
const apiError = ref<string | null>(null)
const savedAt  = ref<string | null>(null)

// MINOR fix: форматирование даты из API
function formatDate(raw: string): string {
  try { return new Date(raw).toLocaleString() } catch { return raw }
}

async function save() {
  saving.value  = true
  apiError.value = null
  try {
    await settingsApi.patchSystem({
      polling_interval_sec: form.polling_interval_sec,
      event_log_limit:      form.event_log_limit,
      timezone:             form.timezone,
    })
    // MAJOR fix: через метод store, не прямая мутация поля
    await settingsStore.reload()
    await qc.invalidateQueries({ queryKey: ['system-settings'] })
    savedAt.value = new Date().toLocaleTimeString()
    toast.add({ severity: 'success', summary: 'Settings saved', life: 2500 })
  } catch (err) {
    apiError.value = extractApiError(err)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.tab-content   { max-width: 32rem; display: flex; flex-direction: column; }
/* MAJOR fix: utility → scoped */
.loading-state { padding: var(--space-8) 0; text-align: center; color: var(--color-text-muted); font-size: var(--text-sm); }
.settings-form { display: flex; flex-direction: column; gap: var(--space-5); }
.field-group   { display: flex; flex-direction: column; gap: var(--space-1); }
.field-label   { font-size: var(--text-sm); font-weight: 500; color: var(--color-text); }
.field-hint    { display: block; font-size: var(--text-xs); color: var(--color-text-muted); font-weight: 400; margin-top: 2px; }
.field-input   { width: 100%; }
.form-footer   { display: flex; align-items: center; gap: var(--space-3); }
.saved-at      { font-size: var(--text-xs); color: var(--color-text-muted); }
.system-meta   { padding-top: var(--space-4); border-top: 1px solid var(--color-divider); }
.meta-text     { font-size: var(--text-xs); color: var(--color-text-muted); }
.error-alert   {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}
</style>