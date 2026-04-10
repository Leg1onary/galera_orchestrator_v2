<template>
  <div class="diag-panel">
    <PanelToolbar
        title="error_log"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    >
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="Select node"
          size="small"
          class="node-select"
      />
      <InputNumber
          v-model="lineCount"
          :min="10"
          :max="1000"
          :step="50"
          show-buttons
          button-layout="horizontal"
          size="small"
          class="lines-input"
          v-tooltip="'Number of lines'"
      >
        <template #incrementbuttonicon>
          <span class="pi pi-plus" />
        </template>
        <template #decrementbuttonicon>
          <span class="pi pi-minus" />
        </template>
      </InputNumber>
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ error.message }}</span>
    </div>

    <template v-else-if="data">
      <div class="log-meta">
        <div class="log-legend">
          <span class="legend-dot legend-dot--error" /><span class="legend-label">Error</span>
          <span class="legend-dot legend-dot--warn" /><span class="legend-label">Warning</span>
          <span class="legend-dot legend-dot--note" /><span class="legend-label">Note</span>
        </div>
        <span class="log-total">{{ data.lines.length }} lines</span>
      </div>

      <div class="log-wrap">
        <div v-if="!data.lines.length" class="log-empty">
          <i class="pi pi-check-circle" /> No log entries found.
        </div>
        <div
            v-for="(line, idx) in data.lines"
            :key="idx"
            class="log-line"
            :class="lineClass(line)"
        >
          <span class="log-gutter">
            <span class="log-bar" />
          </span>
          <span class="log-num">{{ data.lines.length - idx }}</span>
          <span class="log-text">{{ line }}</span>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><i class="pi pi-file-edit" /></div>
      <p>Select a node and click refresh to load the error log.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery }      from '@tanstack/vue-query'
import Select      from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import { useClusterStore }   from '@/stores/cluster'
import { diagnosticsApi }    from '@/api/diagnostics'
import PanelToolbar          from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }     from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const lineCount      = ref(200)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-errorlog', clusterStore.selectedClusterId, selectedNodeId.value, lineCount.value]),
  queryFn: () => diagnosticsApi.getErrorLog(clusterStore.selectedClusterId!, selectedNodeId.value!, lineCount.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedNodeId.value),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

function lineClass(line: string): string {
  const l = line.toLowerCase()
  if (l.includes('[error]') || l.includes('[fatal]')) return 'log-line--error'
  if (l.includes('[warning]') || l.includes('[warn]')) return 'log-line--warn'
  if (l.includes('[note]'))                            return 'log-line--note'
  return ''
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.node-select {
  width: 160px;
  min-width: 140px;
  flex-shrink: 0;
}

/* InputNumber с кнопками — горизонтальный layout */
.lines-input {
  flex-shrink: 0;
}

:deep(.lines-input .p-inputnumber) {
  display: inline-flex;
  align-items: center;
}

:deep(.lines-input .p-inputnumber-input) {
  width: 64px;
  text-align: center;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

:deep(.lines-input .p-inputnumber-button) {
  width: 28px;
  height: 100%;
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 0.6rem;
}

:deep(.lines-input .p-inputnumber-button:hover) {
  background: var(--color-surface-4);
  border-color: var(--color-border-hover);
  color: var(--color-text);
}

:deep(.lines-input .p-inputnumber-button-group) {
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--color-border);
}

/* META ROW */
.log-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.log-legend {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.legend-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.legend-dot--error { background: var(--color-error); }
.legend-dot--warn  { background: var(--color-warning); }
.legend-dot--note  { background: var(--color-primary); }

.legend-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-right: var(--space-2);
}

.log-total {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
}

/* LOG BODY */
.log-wrap {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  background: #0a0b0e;
  max-height: 580px;
  overflow-y: auto;
}

.log-wrap::-webkit-scrollbar       { width: 4px; }
.log-wrap::-webkit-scrollbar-track { background: transparent; }
.log-wrap::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }

.log-line {
  display: flex;
  align-items: stretch;
  gap: 0;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  line-height: 1.65;
  transition: background 80ms ease;
}

.log-line:last-child { border-bottom: none; }
.log-line:hover { background: rgba(255,255,255,0.03); }

/* LEFT GUTTER with colored bar */
.log-gutter {
  width: 4px;
  flex-shrink: 0;
  display: flex;
  align-items: stretch;
}

.log-bar {
  width: 2px;
  background: transparent;
  margin: 3px 1px;
  border-radius: 1px;
  transition: background var(--transition-fast);
}

.log-line--error .log-bar { background: var(--color-error); }
.log-line--warn  .log-bar { background: var(--color-warning); }
.log-line--note  .log-bar { background: var(--color-primary); }

.log-num {
  flex-shrink: 0;
  width: 44px;
  padding: 3px var(--space-2) 3px var(--space-3);
  text-align: right;
  color: var(--color-text-faint);
  user-select: none;
  font-variant-numeric: tabular-nums;
  border-right: 1px solid rgba(255,255,255,0.04);
  font-size: 0.6rem;
  opacity: 0.6;
}

.log-text {
  flex: 1;
  padding: 3px var(--space-4);
  color: #8b949e;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-line--error .log-text { color: #f87171; }
.log-line--warn  .log-text { color: #fbbf24; }
.log-line--note  .log-text { color: #7dcfad; }

.log-empty {
  display: flex; align-items: center; justify-content: center; gap: var(--space-2);
  padding: var(--space-10);
  color: var(--color-text-faint); font-size: var(--text-sm);
}

/* ERROR */
.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.20);
  color: var(--color-error); font-size: var(--text-sm);
}

/* EMPTY */
.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--space-12);
  color: var(--color-text-muted); font-size: var(--text-sm); text-align: center;
}

.empty-icon {
  width: 44px; height: 44px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-3); border: 1px solid var(--color-border);
  color: var(--color-text-faint); font-size: 1.1rem;
}
</style>
