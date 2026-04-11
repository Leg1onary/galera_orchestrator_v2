<template>
  <div class="diag-panel">
    <PanelToolbar
        title="arbitrator_log"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <div class="selector-row">
      <div class="sel-group">
        <label class="sel-label">Arbitrator</label>
        <Select
            v-model="selectedArbId"
            :options="arbOptions"
            option-label="label"
            option-value="value"
            placeholder="Select arbitrator…"
            class="arb-select"
            size="small"
        />
      </div>
      <div class="sel-group">
        <label class="sel-label">Lines</label>
        <Select
            v-model="lines"
            :options="LINE_OPTIONS"
            option-label="label"
            option-value="value"
            class="lines-select"
            size="small"
        />
      </div>
    </div>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ (error as Error).message }}</span>
    </div>

    <template v-else-if="data">
      <div class="terminal-block">
        <div class="terminal-header">
          <span class="terminal-label">{{ data.arbitrator_name }}</span>
          <span class="terminal-meta">fetched {{ data.fetched_at }}</span>
        </div>
        <div class="terminal-wrap">
          <pre class="log-pre">{{ data.lines.join('\n') }}</pre>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading && selectedArbId" class="empty-state">
      <div class="empty-icon"><i class="pi pi-file-edit" /></div>
      <p>No data yet. Click refresh to load.</p>
    </div>

    <div v-else-if="!selectedArbId" class="empty-state">
      <div class="empty-icon"><i class="pi pi-file-edit" /></div>
      <p>Select an arbitrator to view its log.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery }   from '@tanstack/vue-query'
import Select         from 'primevue/select'
import { useClusterStore }    from '@/stores/cluster'
import { diagnosticsApi }     from '@/api/diagnostics'
import PanelToolbar           from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore  = useClusterStore()
const selectedArbId = ref<number | null>(null)
const lines         = ref<20 | 50 | 100>(50)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)

const LINE_OPTIONS = [
  { label: '20 lines',  value: 20  },
  { label: '50 lines',  value: 50  },
  { label: '100 lines', value: 100 },
]

// Fetch arbitrator list from cluster status
const { data: statusData } = useQuery({
  queryKey: computed(() => ['cluster-status', clusterStore.selectedClusterId]),
  queryFn: () =>
    import('@/api/client').then(({ api }) =>
      api
        .get(`/api/clusters/${clusterStore.selectedClusterId}/status`)
        .then((r) => r.data)
    ),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  staleTime: 30_000,
})

const arbOptions = computed(() => {
  const arbs: Array<{ id: number; name: string }> = statusData.value?.arbitrators ?? []
  return arbs.filter((a) => a).map((a) => ({ label: a.name, value: a.id }))
})

watch(arbOptions, (opts) => {
  if (opts.length && !selectedArbId.value) selectedArbId.value = opts[0].value
}, { immediate: true })

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  // ТЗ п.15.8: GET /api/clusters/{id}/arbitrators/{id}/log?lines=N
  queryKey: computed(() => [
    'diag-arb-log',
    clusterStore.selectedClusterId,
    selectedArbId.value,
    lines.value,
  ]),
  queryFn: () =>
    diagnosticsApi.arbitratorLog(
      clusterStore.selectedClusterId!,
      selectedArbId.value!,
      lines.value,
    ),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedArbId.value),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.selector-row {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.sel-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.sel-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.arb-select  { width: 220px; }
.lines-select { width: 120px; }

.terminal-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.terminal-label {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--color-text);
}

.terminal-meta {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
}

.terminal-wrap { background: #0a0b0e; }

.log-pre {
  margin: 0;
  padding: var(--space-4) var(--space-5);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: #c0caf5;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 580px;
  overflow-y: auto;
}

.log-pre::-webkit-scrollbar       { width: 4px; }
.log-pre::-webkit-scrollbar-track { background: transparent; }
.log-pre::-webkit-scrollbar-thumb { background: rgba(192,202,245,0.2); border-radius: 2px; }

.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.20);
  color: var(--color-error); font-size: var(--text-sm);
}

.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--space-12);
  color: var(--color-text-muted); font-size: var(--text-sm);
}

.empty-icon {
  width: 44px; height: 44px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-3); border: 1px solid var(--color-border);
  color: var(--color-text-faint); font-size: 1.1rem;
}
</style>
