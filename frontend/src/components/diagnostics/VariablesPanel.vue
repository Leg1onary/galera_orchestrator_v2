<script setup lang="ts">
import { ref, computed, watch, toRef } from 'vue'
import InputText from 'primevue/inputtext'
import Button    from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column    from 'primevue/column'
import { useClusterStore }  from '@/stores/cluster'
import { useSettingsStore } from '@/stores/settings'
import { diagnosticsApi, type KVRow } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore  = useClusterStore()
const settingsStore = useSettingsStore()

const intervalMs = computed(() => settingsStore.pollingIntervalSec * 1000)
const { autoRefresh } = useDiagAutoRefresh(toRef(props, 'active'), intervalMs)

type NodeData = { node_name: string; variables: KVRow[]; error: string | null }

const nodes      = ref<NodeData[]>([])
const loading    = ref(false)
const error      = ref<string | null>(null)
const fetchedAt  = ref<string | null>(null)
const search     = ref('')
const activeNode = ref<string | null>(null)

const nodeNames = computed(() => nodes.value.map((n) => n.node_name))

const currentRows = computed<KVRow[]>(() => {
  if (!activeNode.value) return []
  const node = nodes.value.find((n) => n.node_name === activeNode.value)
  if (!node) return []
  const rows = node.variables
  const q = search.value.toLowerCase().trim()
  return q
      ? rows.filter((r) => r.variable_name.toLowerCase().includes(q) || r.value.toLowerCase().includes(q))
      : rows
})

const activeNodeError = computed(() => {
  if (!activeNode.value) return null
  return nodes.value.find((n) => n.node_name === activeNode.value)?.error ?? null
})

async function load() {
  const clusterId = clusterStore.selectedClusterId
  if (!clusterId) return
  loading.value    = true
  error.value      = null
  nodes.value      = []
  activeNode.value = null
  try {
    const raw = await diagnosticsApi.variablesAll(clusterId)
    nodes.value = raw.map((n) => ({
      node_name: n.node_name,
      variables: (n.variables ?? []).map((v) => ({ variable_name: v.name, value: v.value })),
      error:     n.error ?? null,
    }))
    if (nodes.value.length > 0) activeNode.value = nodes.value[0].node_name
    fetchedAt.value = new Date().toLocaleTimeString()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

watch(() => props.active, (v) => { if (v) load() }, { immediate: true })
watch(() => clusterStore.selectedClusterId, () => { if (props.active) load() })
</script>

<template>
  <div class="panel">

    <!-- ── Toolbar ── -->
    <PanelToolbar
        title="global_variables"
        :loading="loading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="load"
        @toggle-auto="autoRefresh = $event"
    />

    <!-- ── Subheader: count badge + search + refresh ── -->
    <div class="panel-subheader">
      <span v-if="!loading && activeNode" class="count-badge">
        {{ currentRows.length }} variables
      </span>
      <div class="header-actions">
        <div class="search-wrap">
          <i class="pi pi-search search-icon" />
          <InputText
              v-model="search"
              class="search-input"
              placeholder="Filter variables…"
          />
        </div>
        <Button
            icon="pi pi-refresh"
            severity="secondary"
            :loading="loading"
            :disabled="loading"
            v-tooltip.top="'Refresh'"
            aria-label="Refresh variables"
            @click="load"
        />
      </div>
    </div>

    <!-- ── Error ── -->
    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <!-- ── Node tabs ── -->
    <div v-if="nodeNames.length > 0" class="node-tabs">
      <button
          v-for="n in nodeNames"
          :key="n"
          class="node-tab"
          :class="{ active: activeNode === n }"
          @click="activeNode = n"
      >
        {{ n }}
      </button>
    </div>

    <!-- ── Per-node fetch error ── -->
    <div v-if="activeNodeError" class="alert-warn">
      <i class="pi pi-exclamation-triangle" /> {{ activeNodeError }}
    </div>

    <!-- ── Skeleton ── -->
    <div v-if="loading" class="skeleton-wrap">
      <div v-for="i in 12" :key="i" class="skeleton-row" />
    </div>

    <!-- ── Empty ── -->
    <div v-else-if="currentRows.length === 0 && !error && !activeNodeError" class="empty-hint">
      <i class="pi pi-info-circle" />
      {{ search ? 'No variables match the filter.' : 'No data available.' }}
    </div>

    <!-- ── Table ── -->
    <div v-else class="table-wrap">
      <DataTable
          :value="currentRows"
          class="vars-table"
          :row-hover="true"
          scroll-height="600px"
          scrollable
          size="small"
      >
        <Column field="variable_name" header="Variable" style="width:50%">
          <template #body="{ data: row }">
            <span class="var-name">{{ row.variable_name }}</span>
          </template>
        </Column>
        <Column field="value" header="Value">
          <template #body="{ data: row }">
            <span class="mono val">{{ row.value }}</span>
          </template>
        </Column>
      </DataTable>
    </div>

  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; gap: var(--space-4); }

/* ── Subheader ── */
.panel-subheader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
  min-height: 2rem;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: var(--color-primary-highlight);
  color: var(--color-primary);
  border: 1px solid color-mix(in oklch, var(--color-primary) 25%, transparent);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
}

.header-actions { display: flex; align-items: center; gap: var(--space-3); }

/* ── Search ── */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: var(--space-3);
  color: var(--color-text-faint);
  font-size: 0.75rem;
  pointer-events: none;
  z-index: 1;
}
:deep(.search-input.p-inputtext) {
  padding-left: calc(var(--space-3) + 16px) !important;
  width: 220px;
}

/* ── Alerts ── */
.alert-err {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid rgba(248,113,113,0.25);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.alert-warn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-warning-highlight);
  border: 1px solid color-mix(in oklch, var(--color-warning) 28%, transparent);
  border-radius: var(--radius-md);
  color: var(--color-warning);
  font-size: var(--text-sm);
}

/* ── Node tabs ── */
.node-tabs {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.node-tab {
  padding: var(--space-1) var(--space-3);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--transition-interactive), color var(--transition-interactive), border-color var(--transition-interactive);
}
.node-tab:hover { background: var(--color-surface-offset); color: var(--color-text); }
.node-tab.active {
  background: var(--color-primary-highlight);
  border-color: color-mix(in oklch, var(--color-primary) 35%, transparent);
  color: var(--color-primary);
  font-weight: 600;
}

/* ── Skeleton ── */
.skeleton-wrap { display: flex; flex-direction: column; gap: var(--space-2); }
.skeleton-row {
  height: 32px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
      90deg,
      var(--color-surface-offset) 25%,
      var(--color-surface-dynamic) 50%,
      var(--color-surface-offset) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

/* ── Empty ── */
.empty-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

/* ── Table wrapper ── */
.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

:deep(.vars-table .p-datatable-table-container) {
  border: none;
  border-radius: 0;
  overflow: hidden;
}
:deep(.vars-table .p-datatable-thead > tr > th) {
  padding: var(--space-2) var(--space-4) !important;
  font-size: var(--text-xs) !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted) !important;
  background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
}
:deep(.vars-table .p-datatable-tbody > tr > td) {
  padding: var(--space-2) var(--space-4) !important;
  border-bottom: 1px solid var(--color-border) !important;
  vertical-align: middle;
}
:deep(.vars-table .p-datatable-tbody > tr:last-child > td) {
  border-bottom: none !important;
}
:deep(.vars-table .p-datatable-tbody > tr:hover > td) {
  background: var(--color-surface-2) !important;
}

.var-name { color: var(--color-text); }
.mono     { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.val      { color: var(--color-text-muted); word-break: break-all; }
</style>