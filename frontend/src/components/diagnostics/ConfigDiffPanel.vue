<template>
  <div class="diag-panel">
    <PanelToolbar
        title="config_diff"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ (error as Error).message }}</span>
    </div>

    <template v-else-if="data && data.length">
      <!-- Node names header -->
      <div v-if="nodeNames.length" class="diff-header-row">
        <span class="diff-var-col">Variable</span>
        <span v-for="name in nodeNames" :key="name" class="diff-node-col">{{ name }}</span>
      </div>

      <div class="diff-table">
        <div
            v-for="row in data"
            :key="row.variable_name"
            :class="['diff-row', row.has_diff ? 'row-diff' : 'row-same']"
        >
          <span class="diff-var">
            <i v-if="row.has_diff" class="pi pi-exclamation-triangle diff-warn-icon" />
            {{ row.variable_name }}
          </span>
          <span
              v-for="name in nodeNames"
              :key="name"
              :class="['diff-val', row.has_diff ? 'val-diff' : '']"
          >
            {{ row.values[name] ?? '—' }}
          </span>
        </div>
      </div>

      <div class="diff-summary">
        <span class="diff-count-diff">{{ diffCount }} diff{{ diffCount !== 1 ? 's' : '' }}</span>
        <span class="diff-sep">/</span>
        <span class="diff-count-total">{{ data.length }} variables</span>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><i class="pi pi-code" /></div>
      <p>No data yet. Click refresh to load.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useClusterStore }  from '@/stores/cluster'
import { diagnosticsApi }   from '@/api/diagnostics'
import PanelToolbar         from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-config-diff', clusterStore.selectedClusterId]),
  queryFn: () => diagnosticsApi.configDiff(clusterStore.selectedClusterId!),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

// Collect node names from the first row that has values
const nodeNames = computed<string[]>(() => {
  if (!data.value?.length) return []
  return Object.keys(data.value[0].values)
})

const diffCount = computed(() => data.value?.filter((r) => r.has_diff).length ?? 0)
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.diff-header-row {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.diff-var-col  { flex: 0 0 280px; }
.diff-node-col { flex: 1; font-family: var(--font-mono); }

.diff-table {
  border: 1px solid var(--color-border);
  border-top: none;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  overflow: hidden;
}

.diff-row {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--color-border-muted);
  transition: background var(--transition-fast);
}

.diff-row:last-child { border-bottom: none; }
.diff-row:hover { background: var(--color-surface-3); }
.row-diff { background: rgba(248,113,113,0.04); }
.row-diff:hover { background: rgba(248,113,113,0.08); }

.diff-var {
  flex: 0 0 280px;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.diff-warn-icon { color: var(--color-warning); font-size: 0.65rem; }

.diff-val {
  flex: 1;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text);
  word-break: break-all;
}

.val-diff { color: var(--color-warning); font-weight: 600; }

.diff-summary {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
}

.diff-count-diff  { color: var(--color-warning); font-weight: 700; }
.diff-sep         { color: var(--color-text-faint); }
.diff-count-total { color: var(--color-text-faint); }

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
