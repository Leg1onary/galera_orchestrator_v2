<template>
  <div class="diag-panel">
    <PanelToolbar
        title="galera_variables"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ error.message }}</span>
    </div>

    <template v-else-if="data && data.length">
      <div class="search-wrap">
        <InputText v-model="search" placeholder="Filter variables…" size="small" class="search-input" />
        <span class="search-count">{{ filteredCount }} variables</span>
      </div>

      <div v-for="node in data" :key="node.node_id" class="node-block">
        <div class="node-block-header">
          <div class="node-dot" />
          <span class="node-block-name">{{ node.node_name }}</span>
          <span class="node-sep">/</span>
          <span class="node-block-host">{{ node.host }}</span>
        </div>
        <div class="vars-table">
          <div
              v-for="(val, key) in filteredVars(node.variables)"
              :key="key"
              class="vars-row"
          >
            <span class="vars-key">
              <span v-if="search" v-html="highlight(String(key))" />
              <span v-else>{{ key }}</span>
            </span>
            <span class="vars-val">{{ val }}</span>
          </div>
          <div v-if="!Object.keys(filteredVars(node.variables)).length" class="vars-empty">
            No matching variables.
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><i class="pi pi-sliders-h" /></div>
      <p>No data yet. Click refresh to load.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery }      from '@tanstack/vue-query'
import InputText  from 'primevue/inputtext'
import { useClusterStore }   from '@/stores/cluster'
import { diagnosticsApi }    from '@/api/diagnostics'
import PanelToolbar          from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const search       = ref('')
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-galera-vars', clusterStore.selectedClusterId]),
  queryFn: () => diagnosticsApi.getGaleraVariables(clusterStore.selectedClusterId!),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

function filteredVars(vars: Record<string, unknown>): Record<string, unknown> {
  if (!search.value.trim()) return vars
  const q = search.value.toLowerCase()
  return Object.fromEntries(
      Object.entries(vars).filter(([k, v]) =>
          k.toLowerCase().includes(q) || String(v).toLowerCase().includes(q)
      )
  )
}

const filteredCount = computed(() => {
  if (!data.value?.length) return 0
  return Object.keys(filteredVars(data.value[0].variables ?? {})).length
})

function highlight(text: string): string {
  if (!search.value.trim()) return text
  const escaped = search.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>')
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.search-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.search-input { width: 280px; }

.search-count {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
}

.node-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.node-block-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.node-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  flex-shrink: 0;
}

.node-block-name { font-size: var(--text-sm); font-weight: 700; color: var(--color-text); font-family: var(--font-mono); }
.node-sep        { color: var(--color-text-faint); font-size: var(--text-xs); }
.node-block-host { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-text-muted); }

.vars-table { display: flex; flex-direction: column; }

.vars-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--color-border-muted);
  transition: background var(--transition-fast);
}

.vars-row:last-child { border-bottom: none; }
.vars-row:nth-child(even) { background: rgba(255,255,255,0.015); }
.vars-row:hover { background: var(--color-surface-3); }

.vars-key {
  flex: 0 0 280px;
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  word-break: break-all;
}

.vars-val {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text);
  word-break: break-all;
}

.vars-empty {
  padding: var(--space-5);
  text-align: center;
  font-size: var(--text-xs);
  color: var(--color-text-faint);
}

/* Search highlight */
:deep(mark) {
  background: rgba(45,212,191,0.25);
  color: var(--color-primary);
  border-radius: 2px;
  padding: 0 1px;
}

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
