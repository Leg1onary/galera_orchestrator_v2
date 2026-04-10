<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Error log"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    >
      <!-- MAJOR fix: inline style → class -->
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="Select node…"
          size="small"
          class="node-select"
      />
      <!-- MAJOR fix: utility классы → scoped -->
      <div class="lines-control">
        <span class="lines-label">Lines</span>
        <Select
            v-model="linesCount"
            :options="LINE_OPTIONS"
            option-label="label"
            option-value="value"
            size="small"
            class="lines-select"
        />
      </div>
      <div class="level-toggles">
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
      <i class="pi pi-exclamation-circle" />
      {{ error.message }}
    </div>

    <div v-if="!selectedNodeId" class="empty-state-inline">
      <i class="pi pi-info-circle" />
      Select a node to view error log.
    </div>

    <template v-else>
      <!-- MAJOR fix: utility классы mb-2, ml-auto, text-xs, text-muted-color → scoped -->
      <div v-if="data" class="stats-bar">
        <span class="stat" v-for="lvl in LEVELS" :key="lvl">
          <span :class="`dot dot--${lvl.toLowerCase()}`" />
          {{ countByLevel(lvl) }} {{ lvl }}
        </span>
        <span class="stats-source">
          Showing last {{ data.total_lines }} lines from {{ data.node_name }}
        </span>
      </div>

      <!-- MAJOR fix: inline style → scoped класс -->
      <VirtualScroller
          :items="filteredLines"
          :item-size="22"
          class="log-scroller"
          :lazy="false"
      >
        <template #item="{ item }">
          <div class="log-line" :class="`log-line--${item.level.toLowerCase()}`">
            <span class="log-lineno">{{ item.line_no }}</span>
            <span v-if="item.timestamp" class="log-ts">{{ item.timestamp }}</span>
            <span class="log-badge" :class="`badge--${item.level.toLowerCase()}`">
              {{ item.level }}
            </span>
            <span class="log-text">{{ stripTimestamp(item.raw) }}</span>
          </div>
        </template>
        <template #loader>
          <div class="log-line log-line--loader">Loading…</div>
        </template>
      </VirtualScroller>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useQuery, keepPreviousData } from '@tanstack/vue-query'
// BLOCKER fix: раздельные импорты
import Select         from 'primevue/select'
import ToggleButton   from 'primevue/togglebutton'
import VirtualScroller from 'primevue/virtualscroller'
import { useClusterStore }                from '@/stores/cluster'
import { diagnosticsApi, type ErrorLogLine } from '@/api/diagnostics'
import PanelToolbar                       from './PanelToolbar.vue'
import { useDiagAutoRefresh }             from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }                 from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const selectedNodeId = ref<number | undefined>(undefined)
const linesCount     = ref(200)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions }                  = useNodeOptions()

const LEVELS = ['ERROR', 'WARNING', 'NOTE', 'SYSTEM'] as const
const LINE_OPTIONS = [
  { label: '100',  value: 100  },
  { label: '200',  value: 200  },
  { label: '500',  value: 500  },
  { label: '1000', value: 1000 },
]

const levelFilter = reactive<Record<string, boolean>>({
  ERROR:   true,
  WARNING: true,
  NOTE:    false,
  SYSTEM:  false,
  UNKNOWN: true,
})

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => [
    'diag-errorlog',
    clusterStore.selectedClusterId,
    selectedNodeId.value,
    linesCount.value,
  ]),
  queryFn: () =>
      diagnosticsApi.getErrorLog(
          clusterStore.selectedClusterId!,
          selectedNodeId.value!,
          linesCount.value,
      ),
  enabled:          computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedNodeId.value),
  refetchInterval,
  staleTime:        0,
  // MINOR fix: не мигаем пустым состоянием при смене linesCount
  placeholderData:  keepPreviousData,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filteredLines = computed((): ErrorLogLine[] => {
  if (!data.value) return []
  return data.value.lines.filter((l) => levelFilter[l.level] !== false)
})

function countByLevel(lvl: string): number {
  return data.value?.lines.filter((l) => l.level === lvl).length ?? 0
}

function stripTimestamp(raw: string): string {
  return raw.replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+/, '')
}
</script>

<style scoped>
/* MAJOR fix: utility классы → scoped */
.node-select  { width: 180px; }
.lines-select { width: 90px; }

.lines-control {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.lines-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.level-toggles {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

/* MAJOR fix: stats-bar без utility ml-auto, mb-2 */
.stats-bar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
}
.stats-source {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-left: auto;   /* вместо ml-auto */
}

/* MAJOR fix: VirtualScroller без inline style */
.log-scroller {
  height: 520px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.log-line--loader { color: var(--color-text-muted); }

.stat { display: flex; align-items: center; gap: var(--space-1); }
.dot  { width: 8px; height: 8px; border-radius: var(--radius-full); flex-shrink: 0; }
.dot--error   { background: var(--color-error); }
.dot--warning { background: var(--color-warning); }
.dot--note    { background: var(--color-blue); }
.dot--system  { background: var(--color-text-faint); }

.log-line {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  padding: 2px var(--space-3);
  font-size: 0.7rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  line-height: 22px;
  border-bottom: 1px solid var(--color-divider);
}
.log-line--error   { background: color-mix(in oklch, var(--color-error) 4%, transparent); }
.log-line--warning { background: color-mix(in oklch, var(--color-warning) 4%, transparent); }
.log-lineno { min-width: 44px; color: var(--color-text-faint); text-align: right; flex-shrink: 0; }
.log-ts     { min-width: 155px; color: var(--color-text-muted); flex-shrink: 0; }
.log-badge  {
  min-width: 60px;
  font-weight: 700;
  text-align: center;
  border-radius: var(--radius-sm);
  padding: 0 4px;
  flex-shrink: 0;
  font-size: 0.65rem;
}
.badge--error   { color: var(--color-error);   background: color-mix(in oklch, var(--color-error) 15%, transparent); }
.badge--warning { color: var(--color-warning); background: color-mix(in oklch, var(--color-warning) 15%, transparent); }
.badge--note    { color: var(--color-blue);    background: color-mix(in oklch, var(--color-blue) 12%, transparent); }
.badge--system  { color: var(--color-text-muted); background: var(--color-surface-offset); }
.badge--unknown { color: var(--color-text-muted); background: var(--color-surface-offset); }
.log-text   { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--color-text); }

:deep(.level-btn--error.p-togglebutton-checked)   { --p-togglebutton-checked-background: color-mix(in oklch, var(--color-error) 15%, transparent); color: var(--color-error); }
:deep(.level-btn--warning.p-togglebutton-checked) { --p-togglebutton-checked-background: color-mix(in oklch, var(--color-warning) 15%, transparent); color: var(--color-warning); }
:deep(.level-btn--note.p-togglebutton-checked)    { --p-togglebutton-checked-background: color-mix(in oklch, var(--color-blue) 12%, transparent); color: var(--color-blue); }

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