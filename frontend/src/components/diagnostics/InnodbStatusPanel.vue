<template>
  <div class="diag-panel">
    <PanelToolbar
        title="innodb_status"
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
      <div v-for="node in data" :key="node.node_id" class="node-block">
        <div class="node-block-header">
          <div class="node-block-left">
            <div class="node-dot" />
            <span class="node-block-name">{{ node.node_name }}</span>
            <span class="node-sep">/</span>
            <span class="node-block-host">{{ node.host }}</span>
          </div>
          <button class="copy-btn" v-tooltip="'Copy to clipboard'" @click="copyText(node.status_text)">
            <i class="pi pi-copy" />
            <span>Copy</span>
          </button>
        </div>
        <div class="terminal-wrap">
          <pre class="innodb-pre">{{ node.status_text }}</pre>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><i class="pi pi-database" /></div>
      <p>No data yet. Click refresh to load.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import { useClusterStore }   from '@/stores/cluster'
import { diagnosticsApi }    from '@/api/diagnostics'
import PanelToolbar          from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const toast        = useToast()
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-innodb', clusterStore.selectedClusterId]),
  queryFn: () => diagnosticsApi.getInnodbStatus(clusterStore.selectedClusterId!),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
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
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.node-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.node-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.node-block-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
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

.copy-btn:hover {
  background: var(--color-surface-3);
  border-color: var(--color-border-hover);
  color: var(--color-text);
}

/* TERMINAL */
.terminal-wrap {
  background: #0a0b0e;
  border-top: none;
}

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

/* Custom scrollbar for terminal */
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
