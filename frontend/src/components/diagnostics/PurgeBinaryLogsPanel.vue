<template>
  <div class="diag-panel anim-fade-in">
    <div class="panel-head">
      <div class="panel-head-icon"><i class="pi pi-trash" /></div>
      <div>
        <div class="panel-title">Purge Binary Logs</div>
        <div class="panel-desc">Remove binary logs older than a date or N days from a specific node.</div>
      </div>
    </div>

    <div class="form-card">
      <!-- Node selector -->
      <div class="field">
        <label class="field-label">Target Node</label>
        <Select
            v-model="selectedNodeId"
            :options="nodeOptions"
            option-label="label"
            option-value="value"
            placeholder="Select node…"
            size="small"
            class="field-select"
        />
      </div>

      <!-- Mode selector -->
      <div class="field">
        <label class="field-label">Mode</label>
        <SelectButton
            v-model="mode"
            :options="modeOptions"
            option-label="label"
            option-value="value"
            class="mode-select"
        />
      </div>

      <!-- Date mode -->
      <div v-if="mode === 'date'" class="field">
        <label class="field-label">Purge logs before date</label>
        <DatePicker
            v-model="beforeDate"
            show-time
            hour-format="24"
            size="small"
            date-format="yy-mm-dd"
            placeholder="Select date & time…"
            class="field-date"
        />
      </div>

      <!-- Days mode -->
      <div v-if="mode === 'days'" class="field">
        <label class="field-label">Purge logs older than</label>
        <div class="input-row">
          <InputNumber
              v-model="days"
              :min="1"
              :max="365"
              show-buttons
              size="small"
              class="field-number"
          />
          <span class="unit-label">days</span>
        </div>
      </div>

      <!-- Preview -->
      <div v-if="previewQuery" class="preview-block">
        <span class="preview-label">Will execute:</span>
        <code class="preview-code">{{ previewQuery }}</code>
      </div>

      <!-- Purge button -->
      <div class="form-footer">
        <Button
            label="Purge"
            icon="pi pi-trash"
            severity="danger"
            size="small"
            :disabled="!canPurge"
            :loading="loading"
            @click="confirmPurge"
        />
      </div>
    </div>

    <!-- Confirm dialog -->
    <ConfirmDialog group="purge-binlog">
      <template #message="{ message }">
        <div class="confirm-body">
          <i class="pi pi-exclamation-triangle confirm-icon" />
          <div>
            <div class="confirm-title">{{ message.header }}</div>
            <div class="confirm-text">{{ message.message }}</div>
          </div>
        </div>
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed }  from 'vue'
import { useConfirm }     from 'primevue/useconfirm'
import { useToast }       from 'primevue/usetoast'
import Select        from 'primevue/select'
import SelectButton  from 'primevue/selectbutton'
import InputNumber   from 'primevue/inputnumber'
import DatePicker    from 'primevue/datepicker'
import Button        from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'
import { useClusterStore }  from '@/stores/cluster'
import { diagnosticsApi }   from '@/api/diagnostics'
import { useNodeOptions }   from '@/composables/useNodeOptions'

const clusterStore = useClusterStore()
const confirm      = useConfirm()
const toast        = useToast()

const { nodeOptions } = useNodeOptions()

const selectedNodeId = ref<number | null>(null)
const mode           = ref<'date' | 'days'>('days')
const days           = ref<number>(7)
const beforeDate     = ref<Date | null>(null)
const loading        = ref(false)

const modeOptions = [
  { label: 'Older than N days', value: 'days' },
  { label: 'Before date',       value: 'date' },
]

function toMysqlDatetime(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  )
}

function computedBeforeDate(): string | null {
  if (mode.value === 'date') {
    return beforeDate.value ? toMysqlDatetime(beforeDate.value) : null
  }
  const d = new Date()
  d.setDate(d.getDate() - days.value)
  return toMysqlDatetime(d)
}

const previewQuery = computed<string | null>(() => {
  const dt = computedBeforeDate()
  if (!dt) return null
  return `PURGE BINARY LOGS BEFORE '${dt}'`
})

const canPurge = computed(() => {
  if (!selectedNodeId.value) return false
  if (mode.value === 'date') return !!beforeDate.value
  return (days.value ?? 0) >= 1
})

function confirmPurge() {
  const nodeName = nodeOptions.value.find((o) => o.value === selectedNodeId.value)?.label ?? String(selectedNodeId.value)
  const dt       = computedBeforeDate()!
  confirm.require({
    group:       'purge-binlog',
    header:      'Purge binary logs?',
    message:     `${previewQuery.value}\non node: ${nodeName}`,
    icon:        'pi pi-exclamation-triangle',
    acceptLabel: 'Purge',
    rejectLabel: 'Cancel',
    acceptClass: 'p-button-danger',
    accept:      () => doPurge(dt, nodeName),
  })
}

async function doPurge(beforeDateStr: string, _nodeName: string) {
  if (!clusterStore.selectedClusterId || !selectedNodeId.value) return
  loading.value = true
  try {
    const result = await diagnosticsApi.purgeBinaryLogs(
      clusterStore.selectedClusterId,
      selectedNodeId.value,
      { mode: mode.value, before_date: beforeDateStr },
    )
    toast.add({
      severity: 'success',
      summary:  'Binary logs purged',
      detail:   `${result.query_executed} on ${result.node_name}`,
      life:     5000,
    })
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String(err)
    toast.add({
      severity: 'error',
      summary:  'Purge failed',
      detail:   msg,
      life:     7000,
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.diag-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: 15px;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.panel-head-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 22%, transparent);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: 0.875rem;
}

.panel-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.panel-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.form-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  max-width: 520px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.field-select,
.field-date {
  width: 100%;
}

.mode-select {
  width: 100%;
}

:deep(.mode-select .p-selectbutton) {
  width: 100%;
  display: flex;
}
:deep(.mode-select .p-togglebutton) {
  flex: 1;
  justify-content: center;
}

.input-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.field-number {
  width: 140px;
}

.unit-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.preview-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.preview-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-faint);
}

.preview-code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--color-warning);
  word-break: break-all;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-muted);
}

.confirm-body {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-2) 0;
}

.confirm-icon {
  font-size: 1.4rem;
  color: var(--color-warning);
  flex-shrink: 0;
  margin-top: 2px;
}

.confirm-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-1);
}

.confirm-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  white-space: pre-line;
}

.input-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-1) var(--space-3);
}


:deep(.field-number .p-inputnumber) { display: inline-flex; align-items: center; }
:deep(.field-number .p-inputnumber-input) {
  width: 52px;
  text-align: center;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  padding: var(--space-1) var(--space-2);
  background: var(--color-surface-2);
  border: none;
  color: var(--color-text);
}
:deep(.field-number .p-inputnumber-input:focus) {
  outline: none;
  box-shadow: none;
  border: none;
}
:deep(.field-number .p-inputnumber-button) {
  width: 24px;
  background: var(--color-surface-3);
  border: none;
  color: var(--color-text-muted);
  transition: background var(--transition-fast), color var(--transition-fast);
}
:deep(.field-number .p-inputnumber-button:hover) {
  background: var(--color-surface-4);
  color: var(--color-primary);
}
:deep(.field-number .p-inputnumber-button-group) {
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--color-border);
}

</style>
