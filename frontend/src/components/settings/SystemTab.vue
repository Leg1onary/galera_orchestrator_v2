<template>
  <div class="tab-content">

    <!-- ── Loading ── -->
    <div v-if="isLoading" class="loading-state">
      <div class="skeleton-form-card">
        <div class="skeleton skeleton-header" />
        <div class="skeleton-fields">
          <div v-for="i in 3" :key="i" class="skeleton-field-card">
            <div class="skeleton skeleton-label" />
            <div class="skeleton skeleton-input" />
          </div>
        </div>
      </div>
    </div>

    <!-- ── Form ── -->
    <form v-else-if="form" class="settings-form-card" @submit.prevent="save" novalidate>

      <!-- Header -->
      <div class="form-header">
        <div class="form-header__icon">
          <i class="pi pi-cog" />
        </div>
        <div class="form-header__body">
          <span class="form-title">System settings</span>
          <span class="form-subtitle">Global backend polling and maintenance timing configuration.</span>
        </div>
      </div>

      <!-- Fields -->
      <div class="fields-stack">

        <!-- Polling interval -->
        <div class="field-card">
          <div class="field-meta">
            <div class="field-meta__left">
              <span class="field-title">Polling interval</span>
              <span class="field-hint">How often backend polls node status via SSH/DB</span>
            </div>
            <span class="field-range">5 – 300 sec</span>
          </div>
          <IftaLabel class="field-ifta">
            <InputNumber
                input-id="polling-interval"
                v-model="form.polling_interval_sec"
                :min="5"
                :max="300"
                :use-grouping="false"
                fluid
                suffix=" sec"
            />
            <label for="polling-interval">Polling interval (seconds)</label>
          </IftaLabel>
        </div>

        <!-- Event log limit -->
        <div class="field-card">
          <div class="field-meta">
            <div class="field-meta__left">
              <span class="field-title">Event log limit</span>
              <span class="field-hint">Maximum number of events stored per cluster</span>
            </div>
            <span class="field-range">100 – 10 000 events</span>
          </div>
          <IftaLabel class="field-ifta">
            <InputNumber
                input-id="event-log-limit"
                v-model="form.event_log_limit"
                :min="100"
                :max="10000"
                :use-grouping="true"
                fluid
                suffix=" events"
            />
            <label for="event-log-limit">Event log limit</label>
          </IftaLabel>
        </div>

        <!-- Rolling restart timeout -->
        <div class="field-card">
          <div class="field-meta">
            <div class="field-meta__left">
              <span class="field-title">Rolling restart timeout</span>
              <span class="field-hint">Maximum wait time per node during a rolling restart operation</span>
            </div>
            <span class="field-range">30 – 3 600 sec</span>
          </div>
          <IftaLabel class="field-ifta">
            <InputNumber
                input-id="rolling-restart-timeout"
                v-model="form.rolling_restart_timeout_sec"
                :min="30"
                :max="3600"
                :use-grouping="false"
                fluid
                suffix=" sec"
            />
            <label for="rolling-restart-timeout">Rolling restart timeout (seconds)</label>
          </IftaLabel>
        </div>

      </div>

      <!-- Error -->
      <Message v-if="apiError" severity="error" :closable="false" class="form-error-msg">
        <div class="msg-inner">
          <i class="pi pi-exclamation-circle" />
          <span>{{ apiError }}</span>
        </div>
      </Message>

      <!-- Footer -->
      <div class="form-footer">
        <Button
            type="submit"
            :label="saving ? 'Saving…' : 'Save settings'"
            :icon="saving ? undefined : 'pi pi-check'"
            :loading="saving"
            :disabled="saving"
        />
        <Transition name="fade-in">
          <div v-if="savedAt" class="saved-badge">
            <i class="pi pi-check-circle" />
            <span>Saved at {{ savedAt }}</span>
          </div>
        </Transition>
      </div>

      <!-- Meta -->
      <div v-if="data" class="form-meta">
        <i class="pi pi-clock" />
        <span>Last updated: {{ formatDate(data.updated_at) }}</span>
      </div>

    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import InputNumber from 'primevue/inputnumber'
import IftaLabel  from 'primevue/iftalabel'
import Button     from 'primevue/button'
import Message    from 'primevue/message'
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
  polling_interval_sec:        30,
  event_log_limit:             1000,
  rolling_restart_timeout_sec: 300,
})

watch(data, (val) => {
  if (!val) return
  form.polling_interval_sec        = val.polling_interval_sec
  form.event_log_limit             = val.event_log_limit
  form.rolling_restart_timeout_sec = val.rolling_restart_timeout_sec
}, { immediate: true })

const saving   = ref(false)
const apiError = ref<string | null>(null)
const savedAt  = ref<string | null>(null)

function formatDate(raw: string): string {
  try { return new Date(raw).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'medium' }) }
  catch { return raw }
}

async function save() {
  saving.value = true
  apiError.value = null
  try {
    await settingsApi.patchSystem({
      polling_interval_sec:        form.polling_interval_sec,
      event_log_limit:             form.event_log_limit,
      rolling_restart_timeout_sec: form.rolling_restart_timeout_sec,
    })
    await settingsStore.reload()
    await qc.invalidateQueries({ queryKey: ['system-settings'] })
    savedAt.value = new Date().toLocaleTimeString('ru-RU', { timeStyle: 'medium' })
    toast.add({ severity: 'success', summary: 'Settings saved', life: 2500 })
  } catch (err) {
    apiError.value = extractApiError(err)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* ── Root ── */
.tab-content {
  max-width: 40rem;
  display: flex;
  flex-direction: column;
}

/* ── Skeleton loading ── */
.skeleton-form-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
}

.skeleton-header {
  height: 2.5rem;
  width: 60%;
  border-radius: var(--radius-md);
}

.skeleton-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.skeleton-field-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-surface-offset);
  border: 1px solid color-mix(in oklch, var(--color-border) 78%, transparent);
  border-radius: var(--radius-lg);
}

.skeleton-label { height: 14px; width: 40%; border-radius: var(--radius-sm); }
.skeleton-input { height: 44px; width: 100%; border-radius: var(--radius-md); }

.skeleton {
  display: block;
  background:
      linear-gradient(
          90deg,
          color-mix(in oklch, var(--color-surface-dynamic) 80%, transparent) 25%,
          color-mix(in oklch, var(--color-surface-dynamic) 100%, transparent) 50%,
          color-mix(in oklch, var(--color-surface-dynamic) 80%, transparent) 75%
      );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

/* ── Form card ── */
.settings-form-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
}

/* ── Form header ── */
.form-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid color-mix(in oklch, var(--color-border) 72%, transparent);
}

.form-header__icon {
  width: 2.5rem;
  height: 2.5rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  background: var(--color-primary-highlight);
  color: var(--color-primary);
  font-size: 1.1rem;
}

.form-header__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.form-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.3;
}

.form-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.45;
}

/* ── Fields stack ── */
.fields-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* ── Field card ── */
.field-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-surface-offset);
  border: 1px solid color-mix(in oklch, var(--color-border) 78%, transparent);
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-interactive);
}

.field-card:focus-within {
  border-color: color-mix(in oklch, var(--color-primary) 40%, var(--color-border));
}

.field-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.field-meta__left {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.field-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}

.field-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.4;
}

.field-range {
  flex-shrink: 0;
  font-size: var(--text-xs);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: var(--color-text-faint);
  padding: 3px 8px;
  border-radius: var(--radius-full);
  background: color-mix(in oklch, var(--color-surface-dynamic) 70%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-border) 60%, transparent);
  white-space: nowrap;
  align-self: flex-start;
}

/* ── IftaLabel + InputNumber ── */
.field-ifta {
  width: 100%;
}

:deep(.field-ifta.p-iftalabel) {
  width: 100%;
}

:deep(.field-ifta .p-inputnumber) {
  width: 100%;
}

:deep(.field-ifta .p-inputnumber-input) {
  width: 100%;
  min-height: 3.5rem;
  padding-top: 1.5rem;
  padding-bottom: 0.5rem;
  padding-left: var(--space-3);
  padding-right: var(--space-3);
  box-sizing: border-box;
}

:deep(.field-ifta.p-iftalabel label) {
  top: 0.5rem;
  font-size: var(--text-xs);
  line-height: 1;
  pointer-events: none;
}

/* ── Error message ── */
.form-error-msg {
  width: 100%;
}

.msg-inner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* ── Footer ── */
.form-footer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.saved-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 5px 10px;
  border-radius: var(--radius-full);
  background: var(--color-success-highlight);
  border: 1px solid color-mix(in oklch, var(--color-success) 28%, transparent);
  color: var(--color-success);
  font-size: var(--text-xs);
  font-weight: 600;
}

/* ── Meta ── */
.form-meta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--space-4);
  border-top: 1px solid color-mix(in oklch, var(--color-border) 72%, transparent);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.form-meta .pi {
  color: var(--color-text-faint);
  font-size: 0.8rem;
}

/* ── Transition ── */
.fade-in-enter-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.fade-in-leave-active { transition: opacity 0.2s ease; }
.fade-in-enter-from   { opacity: 0; transform: translateX(-6px); }
.fade-in-leave-to     { opacity: 0; }
</style>