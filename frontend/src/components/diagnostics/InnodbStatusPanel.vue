<template>
  <div class="diag-panel">
    <PanelToolbar
        title="InnoDB status"
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
          placeholder="Select node…"
          size="small"
          class="node-select"
      />
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      {{ error.message }}
    </div>

    <div v-if="!selectedNodeId" class="empty-state-inline">
      <i class="pi pi-info-circle" />
      Select a node to view InnoDB status.
    </div>

    <template v-else-if="data">
      <!-- MAJOR fix: убраны inline styles и utility классы -->
      <div v-if="data.deadlock_section" class="deadlock-block">
        <div class="deadlock-header">
          <i class="pi pi-exclamation-triangle deadlock-icon" />
          <span class="deadlock-title">Latest detected deadlock</span>
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
          <span class="node-label">{{ data.node_name }}</span>
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
import { useQuery }      from '@tanstack/vue-query'
// BLOCKER fix: раздельные импорты
import Button   from 'primevue/button'
import Select   from 'primevue/select'
// BLOCKER fix: useToast из правильного пути
import { useToast } from 'primevue/usetoast'
import { useClusterStore }      from '@/stores/cluster'
import { diagnosticsApi }       from '@/api/diagnostics'
import PanelToolbar             from './PanelToolbar.vue'
import { useDiagAutoRefresh }   from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }       from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const toast          = useToast()
const selectedNodeId = ref<number | undefined>(undefined)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => [
    'diag-innodb',
    clusterStore.selectedClusterId,
    selectedNodeId.value,
  ]),
  queryFn: () =>
      diagnosticsApi.getInnodbStatus(
          clusterStore.selectedClusterId!,
          selectedNodeId.value!,
      ),
  enabled:        computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedNodeId.value),
  refetchInterval,
  staleTime:      0,
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
.node-select { width: 180px; }

/* MAJOR fix: убраны inline styles и utility классы */
.deadlock-block {
  margin-bottom: var(--space-4);
  border: 1px solid color-mix(in oklch, var(--color-warning) 35%, transparent);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: color-mix(in oklch, var(--color-warning) 5%, transparent);
}
.deadlock-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid color-mix(in oklch, var(--color-warning) 25%, transparent);
}
/* MINOR fix: цвет иконки через класс, не inline style */
.deadlock-icon  { color: var(--color-warning); }
.deadlock-title { font-size: var(--text-sm); font-weight: 500; }
.deadlock-text  { max-height: 200px; }

.raw-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.raw-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-offset);
  border-bottom: 1px solid var(--color-border);
}
/* MAJOR fix: убран Tailwind font-mono text-xs text-muted-color */
.node-label {
  font-family: var(--font-mono, monospace);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
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

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  margin-bottom: var(--space-3);
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  font-size: var(--text-sm);
}
.empty-state-inline {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>