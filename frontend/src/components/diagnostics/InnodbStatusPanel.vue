<template>
  <div class="diag-panel">
    <PanelToolbar
        title="InnoDB status"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      {{ error.message }}
    </div>

    <template v-else-if="data && data.length">
      <div v-for="node in data" :key="node.node_id" class="node-block">
        <div class="node-block-header">
          <div class="node-block-left">
            <span class="node-block-name">{{ node.node_name }}</span>
            <span class="node-block-host">{{ node.host }}</span>
          </div>
          <Button
              icon="pi pi-copy"
              text
              rounded
              size="small"
              v-tooltip="'Copy to clipboard'"
              @click="copyText(node.status_text)"
          />
        </div>
        <pre class="innodb-pre">{{ node.status_text }}</pre>
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
import Button      from 'primevue/button'
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
  border-radius: var(--radius-md);
  overflow: hidden;
}
.node-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-offset);
  border-bottom: 1px solid var(--color-border);
}
.node-block-left { display: flex; align-items: center; gap: var(--space-3); }
.node-block-name { font-size: var(--text-sm); font-weight: 700; color: var(--color-text); }
.node-block-host { font-size: var(--text-xs); font-family: var(--font-mono); color: var(--color-text-muted); }

.innodb-pre {
  margin: 0;
  padding: var(--space-4);
  font-family: var(--font-mono, monospace);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--color-surface);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 480px;
  overflow-y: auto;
}

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
  color: var(--color-text-muted); font-size: var(--text-sm);
}
.empty-icon {
  width: 48px; height: 48px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-offset); color: var(--color-text-faint); font-size: 1.2rem;
}
</style>
