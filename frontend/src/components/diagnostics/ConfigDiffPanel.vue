<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type ConfigDiffResponse, type ConfigDiffRow } from '@/api/diagnostics'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

const data      = ref<ConfigDiffResponse | null>(null)
const loading   = ref(false)
const error     = ref<string | null>(null)
const showAll   = ref(false)

async function load() {
  const id = clusterStore.selectedClusterId
  if (!id) return
  loading.value = true
  error.value   = null
  try {
    data.value = await diagnosticsApi.configDiff(id)
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

function cellValue(row: ConfigDiffRow, nodeName: string): { value: string | null; error: boolean } {
  const entry = row.values.find((v) => v.node_name === nodeName)
  if (!entry) return { value: null, error: false }
  if (entry.fetch_error) return { value: null, error: true }
  return { value: entry.value, error: false }
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">
        <i class="pi pi-code" />
        <span>Config Diff</span>
        <span v-if="!loading && data" class="badge-diff" :class="{ 'badge-ok': diffCount === 0 }">
          {{ diffCount === 0 ? 'consistent' : `${diffCount} diff${diffCount !== 1 ? 's' : ''}` }}
        </span>
      </div>
      <div class="header-actions">
        <label class="toggle-label">
          <input type="checkbox" v-model="showAll" />
          Show all variables
        </label>
        <button class="btn-icon" :disabled="loading" @click="load" title="Refresh">
          <i :class="['pi', loading ? 'pi-spin pi-spinner' : 'pi-refresh']" />
        </button>
      </div>
    </div>

    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <div v-if="loading" class="skeleton-wrap">
      <div v-for="i in 8" :key="i" class="skeleton-row" />
    </div>

    <template v-else-if="data">
      <!-- No diffs and not showing all -->
      <div v-if="diffCount === 0 && !showAll" class="all-ok">
        <i class="pi pi-check-circle" />
        All wsrep variables are consistent across nodes.
      </div>

      <!-- No variables fetched at all -->
      <div v-else-if="rows.length === 0" class="empty-hint">
        <i class="pi pi-info-circle" /> No variables fetched.
      </div>

      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Variable</th>
              <th v-for="n in nodeNames" :key="n">{{ n }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in displayed"
              :key="row.variable"
              :class="{ 'row-diff': row.has_diff }"
            >
              <td class="var-name">{{ row.variable }}</td>
              <td
                v-for="n in nodeNames"
                :key="n"
                class="val-cell mono"
                :class="{
                  'val-diff': row.has_diff,
                  'val-err': cellValue(row, n).error
                }"
              >
                <template v-if="cellValue(row, n).error">
                  <span class="err-mark" title="Fetch error">err</span>
                </template>
                <template v-else>
                  {{ cellValue(row, n).value ?? '—' }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Node fetch errors summary -->
      <div
        v-if="data.nodes.some((n) => !n.fetch_ok)"
        class="fetch-warn"
      >
        <i class="pi pi-exclamation-triangle" />
        Could not fetch variables from:
        {{ data.nodes.filter((n) => !n.fetch_ok).map((n) => n.node_name).join(', ') }}
      </div>
    </template>
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

.badge-diff {
  padding: 2px var(--space-2);
  background: var(--color-warning-highlight);
  color: var(--color-warning);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
}
.badge-diff.badge-ok {
  background: var(--color-success-highlight);
  color: var(--color-success);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  cursor: pointer;
  user-select: none;
}

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

.all-ok {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: var(--color-success-highlight);
  border: 1px solid oklch(from var(--color-success) l c h / 0.25);
  border-radius: var(--radius-md);
  color: var(--color-success);
  font-size: var(--text-sm);
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.fetch-warn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-warning-highlight);
  border: 1px solid oklch(from var(--color-warning) l c h / 0.25);
  border-radius: var(--radius-md);
  color: var(--color-warning);
  font-size: var(--text-xs);
}

.skeleton-wrap { display: flex; flex-direction: column; gap: var(--space-2); }
.skeleton-row {
  height: 36px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-surface-offset) 25%, var(--color-surface-dynamic) 50%, var(--color-surface-offset) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow-x: auto;
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
  white-space: nowrap;
}
td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
  vertical-align: top;
}
tr:last-child td { border-bottom: none; }

.var-name { font-weight: 500; white-space: nowrap; }
.mono { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.val-cell { color: var(--color-text-muted); }

.row-diff td { background: oklch(from var(--color-warning) l c h / 0.04); }
.row-diff:hover td { background: oklch(from var(--color-warning) l c h / 0.07); }
.val-diff { color: var(--color-warning) !important; font-weight: 500; }

.val-err { color: var(--color-error) !important; }
.err-mark {
  font-size: var(--text-xs);
  font-family: var(--font-mono, monospace);
  opacity: 0.7;
}
</style>
