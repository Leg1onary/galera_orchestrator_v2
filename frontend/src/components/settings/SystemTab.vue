<template>
  <div class="tab-content">
    <div v-if="isLoading" class="loading-state">
      <span class="skeleton skeleton-text" style="width:200px;height:16px" />
    </div>

    <form v-else-if="form" class="settings-form" @submit.prevent="save">

      <div class="field-group">
        <label for="polling-interval" class="field-label">
          Polling interval (seconds)
          <span class="field-hint">How often backend polls node status via SSH/DB</span>
        </label>
        <input
          id="polling-interval"
          type="number"
          v-model.number="form.polling_interval_sec"
          :min="5" :max="300"
          class="field-input"
        />
      </div>

      <div class="field-group">
        <label for="event-log-limit" class="field-label">
          Event log limit
          <span class="field-hint">Maximum number of events stored per cluster</span>
        </label>
        <input
          id="event-log-limit"
          type="number"
          v-model.number="form.event_log_limit"
          :min="100" :max="10000"
          class="field-input"
        />
      </div>

      <div class="field-group">
        <label for="timezone" class="field-label">
          Timezone
          <span class="field-hint">Used for displaying timestamps in the UI</span>
        </label>
        <input
          id="timezone"
          type="text"
          v-model="form.timezone"
          placeholder="Europe/Moscow"
          class="field-input"
        />
      </div>

      <div v-if="apiError" class="error-alert">
        <i class="pi pi-exclamation-circle" />
        {{ apiError }}
      </div>

      <div class="form-footer">
        <button type="submit" class="btn-save" :disabled="saving">
          <i v-if="saving" class="pi pi-spin pi-spinner" style="font-size:0.85rem" />
          <i v-else class="pi pi-check" style="font-size:0.85rem" />
          {{ saving ? 'Saving…' : 'Save settings' }}
        </button>
        <span v-if="savedAt" class="saved-at">Saved at {{ savedAt }}</span>
      </div>

      <div v-if="data" class="system-meta">
        <span class="meta-text">Last updated: {{ formatDate(data.updated_at) }}</span>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import { settingsApi } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useSettingsStore } from '@/stores/settings'

const qc            = useQueryClient()
const toast         = useToast()
const settingsStore = useSettingsStore()

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

function formatDate(raw: string): string {
  try { return new Date(raw).toLocaleString() } catch { return raw }
}

async function save() {
  saving.value = true; apiError.value = null
  try {
    await settingsApi.patchSystem({
      polling_interval_sec: form.polling_interval_sec,
      event_log_limit:      form.event_log_limit,
      timezone:             form.timezone,
    })
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

.loading-state { padding: var(--space-8) 0; }

.settings-form { display: flex; flex-direction: column; gap: var(--space-5); }

.field-group   { display: flex; flex-direction: column; gap: var(--space-2); }
.field-label   { font-size: var(--text-sm); font-weight: 500; color: var(--color-text); }
.field-hint    { display: block; font-size: var(--text-xs); color: var(--color-text-muted); font-weight: 400; margin-top: 2px; }

.field-input {
  width: 100%;
  background: #0f1015;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-family: inherit;
  padding: var(--space-2) var(--space-3);
  line-height: 1.5;
  outline: none;
  transition: border-color 150ms ease, box-shadow 150ms ease;
  -webkit-appearance: none;
  appearance: none;
  box-sizing: border-box;
}
.field-input::placeholder { color: var(--color-text-faint); }
.field-input:focus {
  border-color: rgba(45,212,191,0.45);
  box-shadow: 0 0 0 3px rgba(45,212,191,0.08);
}

.form-footer { display: flex; align-items: center; gap: var(--space-3); margin-top: var(--space-2); }
.saved-at    { font-size: var(--text-xs); color: var(--color-text-muted); }

.btn-save {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-md);
  font-size: var(--text-sm); font-weight: 600; font-family: inherit;
  color: #0d1117; background: #2dd4bf;
  border: none; cursor: pointer;
  transition: all 150ms ease;
}
.btn-save:hover:not(:disabled) { background: #5eead4; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

.system-meta { padding-top: var(--space-4); border-top: 1px solid var(--color-divider); }
.meta-text   { font-size: var(--text-xs); color: var(--color-text-muted); }

.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.2);
  color: #f87171;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

.skeleton { display: inline-block; border-radius: var(--radius-sm); background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.05) 75%); background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
</style>
