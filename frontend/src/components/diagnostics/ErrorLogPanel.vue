<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Error log"
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
      <div class="flex items-center gap-2">
        <span class="text-xs text-muted-color">Lines</span>
        <Select
            v-model="linesCount"
            :options="LINE_OPTIONS"
            option-label="label"
            option-value="value"
            size="small"
            style="width: 90px"
        />
      </div>
      <div class="flex items-center gap-1">
        <ToggleButton
            v-for="lvl in LEVELS"
            :key="lvl"
            v-model="levelFilter[lvl]"
            :on-label="lvl"
            :off-label="lvl"
            size="small"
            :class="`level-btn level-btn--${lvl.toLowerCase()}`"
        />
      </div>
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />{{ (error as any)?.message }}
    </div>

    <div v-if="!selectedNodeId" class="empty-state-inline">
      <i class="pi pi-info-circle" />
      Select a node to view error log.
    </div>

    <template v-else>
      <div v-if="data" class="stats-bar mb-2">
        <span class="stat" v-for="lvl in LEVELS" :key="lvl">
          <span :class="`dot dot--${lvl.toLowerCase()}`" />
          {{ countByLevel(lvl) }} {{ lvl }}
        </span>
        <span class="text-xs text-muted-color ml-auto">
          Showing last {{ data.total_lines }} lines from {{ data.node_name }}
        </span>
      </div>

      <VirtualScroller
          :items="filteredLines"
          :item-size="22"
          style="height: 520px; border: 1px solid var(--color-border); border-radius: var(--radius-md)"
          :lazy="false"
      >
        <template #item="{ item }">
          <div
              class="log-line"
              :class="`log-line--${item.level.toLowerCase()}`"
          >
            <span class="log-lineno">{{ item.line_no }}</span>
            <span v-if="item.timestamp" class="log-ts">{{ item.timestamp }}</span>
            <span class="log-badge" :class="`badge--${item.level.toLowerCase()}`">
              {{ item.level }}
            </span>
            <span class="log-text">{{ stripTimestamp(item.raw) }}</span>
          </div>
        </template>
        <template #loader>
          <div class="log-line text-muted-color">Loading…</div>
        </template>
      </VirtualScroller>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { Select, ToggleButton, VirtualScroller } from 'primevue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type ErrorLogLine } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions } from '@/composables/useNodeOptions'   // ← fix

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const linesCount = ref(200)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions } = useNodeOptions()   // ← fix

const LEVELS = ['ERROR', 'WARNING', 'NOTE', 'SYSTEM'] as const
const LINE_OPTIONS = [
  { label: '100', value: 100 },
  { label: '200', value: 200 },
  { label: '500', value: 500 },
  { label: '1000', value: 1000 },
]

const levelFilter = reactive<Record<string, boolean>>({
  ERROR: true,
  WARNING: true,
  NOTE: false,
  SYSTEM: false,
  UNKNOWN: true,
})

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({  // ← fix: добавили error
  queryKey: computed(() => ['diag-errorlog', clusterStore.selectedClusterId, selectedNodeId.value, linesCount.value]),
  queryFn: () => diagnosticsApi.getErrorLog(clusterStore.selectedClusterId!, selectedNodeId.value!, linesCount.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedNodeId.value),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filteredLines = computed((): ErrorLogLine[] => {
  if (!data.value) return []
  return data.value.lines.filter((l) => levelFilter[l.level] !== false)
})

function countByLevel(lvl: string) {
  return data.value?.lines.filter((l) => l.level === lvl).length ?? 0
}

function stripTimestamp(raw: string) {
  return raw.replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+/, '')
}
</script>

<style scoped>
/* стили без изменений — оставить из оригинала */
.stats-bar { display: flex; align-items: center; gap: var(--space-4); font-size: var(--text-xs); color: var(--color-text-muted); }
.stat { display: flex; align-items: center; gap: var(--space-1); }
.dot { width: 8px; height: 8px; border-radius: var(--radius-full); flex-shrink: 0; }
.dot--error   { background: var(--color-error); }
.dot--warning { background: var(--color-warning); }
.dot--note    { background: var(--color-blue); }
.dot--system  { background: var(--color-text-faint); }
.log-line { display: flex; align-items: baseline; gap: var(--space-2); padding: 2px var(--space-3); font-size: 0.7rem; font-family: 'JetBrains Mono', 'Fira Code', monospace; line-height: 22px; border-bottom: 1px solid var(--color-divider); }
.log-line--error   { background: color-mix(in oklch, var(--color-error) 4%, transparent); }
.log-line--warning { background: color-mix(in oklch, var(--color-warning) 4%, transparent); }
.log-lineno { min-width: 44px; color: var(--color-text-faint); text-align: right; flex-shrink: 0; }
.log-ts { min-width: 155px; color: var(--color-text-muted); flex-shrink: 0; }
.log-badge { min-width: 60px; font-weight: 700; text-align: center; border-radius: var(--radius-sm); padding: 0 4px; flex-shrink: 0; font-size: 0.65rem; }
.badge--error   { color: var(--color-error);   background: color-mix(in oklch, var(--color-error) 15%, transparent); }
.badge--warning { color: var(--color-warning); background: color-mix(in oklch, var(--color-warning) 15%, transparent); }
.badge--note    { color: var(--color-blue);    background: color-mix(in oklch, var(--color-blue) 12%, transparent); }
.badge--system  { color: var(--color-text-muted); background: var(--color-surface-offset); }
.badge--unknown { color: var(--color-text-muted); background: var(--color-surface-offset); }
.log-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--color-text); }
:deep(.level-btn--error.p-togglebutton-checked)   { --p-togglebutton-checked-background: color-mix(in oklch, var(--color-error) 15%, transparent); color: var(--color-error); }
:deep(.level-btn--warning.p-togglebutton-checked) { --p-togglebutton-checked-background: color-mix(in oklch, var(--color-warning) 15%, transparent); color: var(--color-warning); }
:deep(.level-btn--note.p-togglebutton-checked)    { --p-togglebutton-checked-background: color-mix(in oklch, var(--color-blue) 12%, transparent); color: var(--color-blue); }
.empty-state-inline { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-4); color: var(--color-text-muted); font-size: var(--text-sm); }
</style>