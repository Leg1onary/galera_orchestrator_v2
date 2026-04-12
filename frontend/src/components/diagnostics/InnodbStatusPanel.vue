<template>
  <div class="diag-panel">
    <PanelToolbar
        title="SHOW ENGINE INNODB STATUS"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <!-- Node selector -->
    <div class="selector-row">
      <label class="sel-label">Node</label>
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="Select node…"
          class="node-select"
          size="small"
      />
    </div>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ (error as Error).message }}</span>
    </div>

    <template v-else-if="data">
      <!-- Deadlock banner -->
      <div v-if="data.has_deadlock" class="deadlock-banner">
        <i class="pi pi-exclamation-triangle" />
        <span>Latest detected deadlock found in InnoDB status</span>
      </div>

      <div class="terminal-block">
        <div class="terminal-header">
          <span class="terminal-label">full_status</span>
          <button class="copy-btn" v-tooltip="'Copy to clipboard'" @click="copyText(data.full_status)">
            <i class="pi pi-copy" />
            <span>Copy</span>
          </button>
        </div>
        <div class="terminal-wrap">
          <pre class="innodb-pre">{{ data.full_status }}</pre>
        </div>
      </div>

      <template v-if="data.has_deadlock && data.latest_deadlock">
        <div class="terminal-block">
          <div class="terminal-header">
            <span class="terminal-label terminal-label-warn">latest_deadlock</span>
            <button class="copy-btn" @click="copyText(data.latest_deadlock!)">
              <i class="pi pi-copy" />
              <span>Copy</span>
            </button>
          </div>
          <div class="terminal-wrap">
            <pre class="innodb-pre pre-warn">{{ data.latest_deadlock }}</pre>
          </div>
        </div>
      </template>
    </template>

    <div v-else-if="!isLoading && selectedNodeId" class="empty-state">
      <div class="empty-icon"><i class="pi pi-database" /></div>
      <p>No data yet. Click refresh to load.</p>
    </div>

    <div v-else-if="!selectedNodeId" class="empty-state">
      <div class="empty-icon"><i class="pi pi-database" /></div>
      <p>Select a node to view InnoDB status.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery }   from '@tanstack/vue-query'
import { useToast }   from 'primevue/usetoast'
import Select         from 'primevue/select'
import { useClusterStore }    from '@/stores/cluster'
import { nodesApi }           from '@/api/nodes'
import PanelToolbar           from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }     from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const toast          = useToast()
const selectedNodeId = ref<number | null>(null)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions } = useNodeOptions()

// Auto-select first node when list loads
watch(nodeOptions, (opts) => {
  if (opts.length && !selectedNodeId.value) selectedNodeId.value = opts[0].value
}, { immediate: true })

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-innodb', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => nodesApi.innodbStatus(clusterStore.selectedClusterId!, selectedNodeId.value!),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedNodeId.value),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.add({ severity: 'success', summary: 'Copied', life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Copy failed', life: 2000 })
  }
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); padding: 15px; }

.selector-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.sel-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.node-select { width: 220px; }

.deadlock-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(249,115,22,0.08);
  border: 1px solid rgba(249,115,22,0.25);
  color: var(--color-warning);
  font-size: var(--text-sm);
  font-weight: 600;
}

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
  font-weight: 600;
  color: var(--color-text-muted);
}

.terminal-label-warn { color: var(--color-warning); }

.copy-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: 3px var(--space-3);
  border-radius: var(--radius-md);
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.copy-btn .pi { font-size: 0.65rem; }
.copy-btn:hover { background: var(--color-surface-3); border-color: var(--color-border-hover); color: var(--color-text); }

.terminal-wrap { background: #0a0b0e; }

.innodb-pre {
  margin: 0;
  padding: var(--space-4) var(--space-5);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: #7dcfad;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 520px;
  overflow-y: auto;
}

.pre-warn { color: #fbbf24; }

.innodb-pre::-webkit-scrollbar       { width: 4px; }
.innodb-pre::-webkit-scrollbar-track { background: transparent; }
.innodb-pre::-webkit-scrollbar-thumb { background: rgba(125,207,173,0.2); border-radius: 2px; }

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
