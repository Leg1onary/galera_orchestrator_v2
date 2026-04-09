<template>
  <div class="diag-panel">
    <PanelToolbar
        title="InnoDB status"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = !autoRefresh"
    >
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="Select node…"
          size="small"
          style="width: 180px"
      />
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />{{ (error as any)?.message }}
    </div>

    <div v-if="!selectedNodeId" class="empty-state-inline">
      <i class="pi pi-info-circle" />
      Select a node to view InnoDB status.
    </div>

    <template v-else-if="data">
      <div v-if="data.deadlock_section" class="deadlock-block mb-4">
        <div class="deadlock-header">
          <i class="pi pi-exclamation-triangle" style="color: var(--color-warning)" />
          <span class="font-medium text-sm">Latest detected deadlock</span>
          <Button
              icon="pi pi-copy"
              text
              rounded
              size="small"
              aria-label="Copy deadlock"
              @click="copy(data.deadlock_section!)"
          />
        </div>
        <pre class="raw-text deadlock-text">{{ data.deadlock_section }}</pre>
      </div>

      <div class="raw-block">
        <div class="raw-block-header">
          <span class="text-xs text-muted-color font-mono">{{ data.node_name }}</span>
          <Button
              icon="pi pi-copy"
              text
              rounded
              size="small"
              label="Copy"
              aria-label="Copy full output"
              @click="copy(data.raw_text)"
          />
        </div>
        <pre class="raw-text">{{ data.raw_text }}</pre>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { Button, Select, useToast } from 'primevue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions } from '@/composables/useNodeOptions'   // ← fix

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const toast = useToast()
const selectedNodeId = ref<number | undefined>(undefined)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions } = useNodeOptions()   // ← fix

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-innodb', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => diagnosticsApi.getInnodbStatus(clusterStore.selectedClusterId!, selectedNodeId.value!),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedNodeId.value),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

async function copy(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.add({ severity: 'success', summary: 'Copied', life: 1500 })
  } catch {
    toast.add({ severity: 'error', summary: 'Copy failed', life: 2000 })
  }
}
</script>

<style scoped>
.raw-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.raw-block-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-offset);
  border-bottom: 1px solid var(--color-border);
}
.raw-text {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-surface);
  padding: var(--space-4);
  overflow-x: auto;
  max-height: 520px;
  overflow-y: auto;
  white-space: pre;
  margin: 0;
}
.deadlock-block {
  border: 1px solid color-mix(in oklch, var(--color-warning) 35%, transparent);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: color-mix(in oklch, var(--color-warning) 5%, transparent);
}
.deadlock-header {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid color-mix(in oklch, var(--color-warning) 25%, transparent);
}
.deadlock-text { max-height: 200px; }
.empty-state-inline {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>