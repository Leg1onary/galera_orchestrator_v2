<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Error log"
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
          size="small"
          class="lines-input"
          v-tooltip="'Number of lines'"
      />
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      {{ error.message }}
    </div>

    <template v-else-if="data">
      <!-- LEGEND -->
      <div class="log-legend">
        <span class="legend-item legend-item--error"><i class="pi pi-circle-fill" /> Error</span>
        <span class="legend-item legend-item--warn"><i class="pi pi-circle-fill" /> Warning</span>
        <span class="legend-item legend-item--note"><i class="pi pi-circle-fill" /> Note</span>
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
  if (l.includes('[warning]') || l.includes('[warn]'))  return 'log-line--warn'
  if (l.includes('[note]'))                              return 'log-line--note'
  return ''
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.node-select  { width: 180px; }
.lines-input  { width: 110px; }

/* LEGEND */
.log-legend {
  display: flex;
  gap: var(--space-4);
  align-items: center;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.legend-item .pi { font-size: 0.5rem; }
.legend-item--error .pi { color: var(--color-error); }
.legend-item--warn  .pi { color: var(--color-warning); }
.legend-item--note  .pi { color: var(--color-primary); }

/* LOG */
.log-wrap {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  font-family: var(--font-mono, monospace);
  font-size: var(--text-xs);
  max-height: 560px;
  overflow-y: auto;
}
.log-line {
  display: flex;
  gap: var(--space-3);
  padding: 3px var(--space-4);
  border-bottom: 1px solid var(--color-divider);
  line-height: 1.6;
  transition: background 100ms ease;
}
.log-line:last-child { border-bottom: none; }
.log-line:hover { background: var(--color-surface-dynamic); }

.log-num {
  flex-shrink: 0;
  width: 40px;
  text-align: right;
  color: var(--color-text-faint);
  user-select: none;
  font-variant-numeric: tabular-nums;
}
.log-text {
  flex: 1;
  color: var(--color-text-muted);
  white-space: pre-wrap;
  word-break: break-all;
}

.log-line--error { background: color-mix(in oklch, var(--color-error) 8%, transparent); }
.log-line--error .log-text { color: var(--color-error); }
.log-line--warn  { background: color-mix(in oklch, var(--color-warning) 7%, transparent); }
.log-line--warn  .log-text { color: var(--color-warning); }
.log-line--note  .log-text { color: var(--color-primary); }

.log-empty {
  display: flex; align-items: center; justify-content: center; gap: var(--space-2);
  padding: var(--space-8);
  color: var(--color-text-faint); font-size: var(--text-sm);
}

/* ERROR */
.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-error) 25%, transparent);
  color: var(--color-error); font-size: var(--text-sm);
}

.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--space-12);
  color: var(--color-text-muted); font-size: var(--text-sm); text-align: center;
}
.empty-icon {
  width: 48px; height: 48px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-offset); color: var(--color-text-faint); font-size: 1.2rem;
}
</style>
