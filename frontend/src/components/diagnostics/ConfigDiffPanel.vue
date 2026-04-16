<script setup lang="ts">
import { ref, watch, computed, toRef } from 'vue'
import ToggleSwitch from 'primevue/toggleswitch'
import Button       from 'primevue/button'
import DataTable    from 'primevue/datatable'
import Column       from 'primevue/column'
import { useClusterStore } from '@/stores/cluster'
import { useSettingsStore } from '@/stores/settings'
import { diagnosticsApi, type ConfigDiffResponse, type ConfigDiffRow } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'

const props = defineProps<{ active: boolean }>()
const clusterStore  = useClusterStore()
const settingsStore = useSettingsStore()

const intervalMs = computed(() => settingsStore.pollingIntervalSec * 1000)
const { autoRefresh } = useDiagAutoRefresh(toRef(props, 'active'), intervalMs)

const data      = ref<ConfigDiffResponse | null>(null)
const loading   = ref(false)
const error     = ref<string | null>(null)
const fetchedAt = ref<string | null>(null)
const showAll   = ref(false)

async function load() {
  const id = clusterStore.selectedClusterId
  if (!id) return
  loading.value = true
  error.value   = null
  try {
    data.value  = await diagnosticsApi.configDiff(id)
    fetchedAt.value = new Date().toLocaleTimeString()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

watch(() => props.active, (v) => { if (v) load() }, { immediate: true })
watch(() => clusterStore.selectedClusterId, () => { if (props.active) load() })

const nodeNames = computed(() => data.value?.nodes.map((n) => n.node_name) ?? [])
const rows      = computed(() => data.value?.variables ?? [])
const diffCount = computed(() => rows.value.filter((r) => r.has_diff).length)
const displayed = computed(() =>
    showAll.value ? rows.value : rows.value.filter((r) => r.has_diff)
)

function cellValue(row: ConfigDiffRow, nodeName: string) {
  const entry = row.values.find((v) => v.node_name === nodeName)
  if (!entry) return { value: null, error: false }
  if (entry.fetch_error) return { value: null, error: true }
  return { value: entry.value, error: false }
}
</script>

<template>
  <div class="panel">

    <!-- ── Toolbar (как в ConnectionCheckPanel) ── -->
    <PanelToolbar
        title="config_diff"
        :loading="loading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="load"
        @toggle-auto="autoRefresh = $event"
    />

    <!-- ── Badge + Toggle ── -->
    <div class="panel-subheader">
      <div class="diff-badge-wrap">
        <span
            v-if="!loading && data"
            class="badge-diff"
            :class="diffCount === 0 ? 'badge-ok' : 'badge-warn'"
        >
          <i :class="['pi', diffCount === 0 ? 'pi-check-circle' : 'pi-exclamation-circle']" />
          {{ diffCount === 0 ? 'consistent' : `${diffCount} diff${diffCount !== 1 ? 's' : ''}` }}
        </span>
      </div>
      <div class="toggle-row" @click.stop="showAll = !showAll">
        <ToggleSwitch
            :model-value="showAll"
            @update:model-value="showAll = $event"
            @click.stop
        />
        <span class="toggle-label">Show all variables</span>
      </div>
    </div>

    <!-- ── Error ── -->
    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <!-- ── Skeleton ── -->
    <div v-if="loading" class="skeleton-wrap">
      <div v-for="i in 8" :key="i" class="skeleton-row" />
    </div>

    <template v-else-if="data">

      <!-- All consistent, no diffs -->
      <div v-if="diffCount === 0 && !showAll" class="all-ok">
        <i class="pi pi-check-circle" />
        All wsrep variables are consistent across nodes.
      </div>

      <!-- No rows at all -->
      <div v-else-if="rows.length === 0" class="empty-hint">
        <i class="pi pi-info-circle" /> No variables fetched.
      </div>

      <!-- Table -->
      <div v-else class="table-wrap">
        <DataTable
            :value="displayed"
            class="diff-table"
            :row-class="(row: ConfigDiffRow) => row.has_diff ? 'row-diff' : ''"
            :row-hover="true"
            scroll-height="600px"
            scrollable
            size="small"
        >
          <Column field="variable" header="Variable" style="min-width:200px">
            <template #body="{ data: row }">
              <span class="var-name">{{ row.variable }}</span>
            </template>
          </Column>
          <Column
              v-for="n in nodeNames"
              :key="n"
              :field="n"
              :header="n"
              style="min-width:120px"
          >
            <template #body="{ data: row }">
              <span v-if="cellValue(row, n).error" class="err-mark val-err" title="Fetch error">err</span>
              <span
                  v-else
                  class="val-cell mono"
                  :class="{ 'val-diff': row.has_diff }"
              >{{ cellValue(row, n).value ?? '—' }}</span>
            </template>
          </Column>
        </DataTable>
      </div>

      <!-- Fetch warnings -->
      <div v-if="data.nodes.some((n) => !n.fetch_ok)" class="fetch-warn">
        <i class="pi pi-exclamation-triangle" />
        Could not fetch variables from:
        {{ data.nodes.filter((n) => !n.fetch_ok).map((n) => n.node_name).join(', ') }}
      </div>

    </template>
  </div>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── Subheader row: badge + toggle ── */
.panel-subheader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.diff-badge-wrap {
  display: flex;
  align-items: center;
  min-height: 1.5rem;
}

.badge-diff {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
}

.badge-warn {
  background: var(--color-warning-highlight);
  color: var(--color-warning);
  border: 1px solid color-mix(in oklch, var(--color-warning) 25%, transparent);
}

.badge-ok {
  background: var(--color-success-highlight);
  color: var(--color-success);
  border: 1px solid color-mix(in oklch, var(--color-success) 25%, transparent);
}

/* ── Toggle ── */
.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  user-select: none;
}

.toggle-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

:deep(.p-toggleswitch) {
  pointer-events: none;
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

.all-ok {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: var(--color-success-highlight);
  border: 1px solid rgba(74,222,128,0.25);
  border-radius: var(--radius-md);
  color: var(--color-success);
  font-size: var(--text-sm);
}

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

.fetch-warn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-warning-highlight);
  border: 1px solid color-mix(in oklch, var(--color-warning) 28%, transparent);
  border-radius: var(--radius-md);
  color: var(--color-warning);
  font-size: var(--text-xs);
}

/* ── Skeleton ── */
.skeleton-wrap { display: flex; flex-direction: column; gap: var(--space-2); }
.skeleton-row {
  height: 36px;
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

/* ── Table wrapper — даёт боковые отступы ── */
.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

/* ── DataTable overrides ── */
:deep(.diff-table .p-datatable-table-container) {
  border: none;
  border-radius: 0;
  overflow-x: auto;
}
:deep(.diff-table .p-datatable-thead > tr > th) {
  padding: var(--space-2) var(--space-4) !important;
  font-size: var(--text-xs) !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted) !important;
  background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
  white-space: nowrap;
}
:deep(.diff-table .p-datatable-tbody > tr > td) {
  padding: var(--space-2) var(--space-4) !important;
  border-bottom: 1px solid var(--color-border) !important;
  vertical-align: top;
}
:deep(.diff-table .p-datatable-tbody > tr:last-child > td) {
  border-bottom: none !important;
}
:deep(.diff-table .p-datatable-tbody > tr.row-diff > td) {
  background: rgba(96,165,250,0.04) !important;
}
:deep(.diff-table .p-datatable-tbody > tr.row-diff:hover > td) {
  background: rgba(96,165,250,0.07) !important;
}
:deep(.diff-table .p-datatable-tbody > tr:not(.row-diff):hover > td) {
  background: var(--color-surface-2) !important;
}

.var-name { font-weight: 500; white-space: nowrap; color: var(--color-text); }
.mono     { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.val-cell { color: var(--color-text-muted); }
.val-diff { color: var(--color-warning) !important; font-weight: 500; }
.val-err  { color: var(--color-error) !important; }
.err-mark { font-size: var(--text-xs); font-family: var(--font-mono, monospace); opacity: 0.7; }
</style>
