<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type KVRow } from '@/api/diagnostics'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

type NodeData = { node_name: string; variables: KVRow[]; error: string | null }

const nodes      = ref<NodeData[]>([])
const loading    = ref(false)
const error      = ref<string | null>(null)
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
    // Fix: set activeNode directly after data is available — avoids watch() dedup race
    if (nodes.value.length > 0) {
      activeNode.value = nodes.value[0].node_name
    }
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
    <div class="panel-header">
      <div class="panel-title">
        <i class="pi pi-sliders-h" />
        <span>Global Variables</span>
        <span v-if="!loading && activeNode" class="count-badge">
          {{ currentRows.length }}
        </span>
      </div>
      <div class="header-actions">
        <div class="search-wrap">
          <i class="pi pi-search search-icon" />
          <input
            v-model="search"
            class="search-input"
            type="text"
            placeholder="Filter variables…"
          />
        </div>
        <button class="btn-icon" :disabled="loading" @click="load" title="Refresh">
          <i :class="['pi', loading ? 'pi-spin pi-spinner' : 'pi-refresh']" />
        </button>
      </div>
    </div>

    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <!-- Node tabs -->
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

    <!-- Per-node fetch error -->
    <div v-if="activeNodeError" class="alert-warn">
      <i class="pi pi-exclamation-triangle" /> {{ activeNodeError }}
    </div>

    <div v-if="loading" class="skeleton-wrap">
      <div v-for="i in 12" :key="i" class="skeleton-row" />
    </div>

    <div v-else-if="currentRows.length === 0 && !error && !activeNodeError" class="empty-hint">
      <i class="pi pi-info-circle" />
      {{ search ? 'No variables match the filter.' : 'No data available.' }}
    </div>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th style="width:50%">Variable</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in currentRows" :key="row.variable_name">
            <td class="var-name">{{ row.variable_name }}</td>
            <td class="mono val">{{ row.value }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; gap: var(--space-4); }

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.count-badge {
  padding: 2px var(--space-2);
  background: var(--color-primary-highlight);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
}

.header-actions { display: flex; align-items: center; gap: var(--space-3); }

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
}
.search-input {
  padding: var(--space-2) var(--space-3) var(--space-2) calc(var(--space-3) + 16px);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text);
  width: 220px;
  outline: none;
  transition: border-color var(--transition-interactive);
}
.search-input:focus { border-color: var(--color-primary); }

.btn-icon {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--transition-interactive), color var(--transition-interactive);
}
.btn-icon:hover:not(:disabled) { background: var(--color-surface-offset); color: var(--color-text); }
.btn-icon:disabled { opacity: 0.4; cursor: not-allowed; }

.alert-err {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid oklch(from var(--color-error) l c h / 0.25);
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
  border: 1px solid oklch(from var(--color-warning) l c h / 0.25);
  border-radius: var(--radius-md);
  color: var(--color-warning);
  font-size: var(--text-sm);
}

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
  border-color: oklch(from var(--color-primary) l c h / 0.35);
  color: var(--color-primary);
  font-weight: 600;
}

.skeleton-wrap { display: flex; flex-direction: column; gap: var(--space-2); }
.skeleton-row {
  height: 32px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-surface-offset) 25%, var(--color-surface-dynamic) 50%, var(--color-surface-offset) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  max-height: 600px;
  overflow-y: auto;
}

table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
thead { background: var(--color-surface-2); position: sticky; top: 0; z-index: 1; }
th {
  padding: var(--space-2) var(--space-3);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
}
td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--color-surface-2); }

.var-name { color: var(--color-text); }
.mono { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.val { color: var(--color-text-muted); word-break: break-all; }
</style>
