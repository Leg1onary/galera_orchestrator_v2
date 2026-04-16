<script setup lang="ts">
/**
 * #3 grastate.dat Inspector Panel
 * Shows parsed grastate.dat from all nodes with analysis warnings.
 */
import { ref, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import { recoveryAdvancedApi, type GrastateResponse, type GrastateNodeResult } from '@/api/recovery-advanced'

const props = defineProps<{ clusterId: number | null }>()

const data    = ref<GrastateResponse | null>(null)
const loading = ref(false)
const error   = ref<string | null>(null)
const expanded = ref<Set<number>>(new Set())

async function load() {
  if (!props.clusterId) return
  loading.value = true
  error.value = null
  try {
    data.value = await recoveryAdvancedApi.getGrastate(props.clusterId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, (id) => { if (id) load() }, { immediate: true })

function toggleExpand(nodeId: number) {
  if (expanded.value.has(nodeId)) expanded.value.delete(nodeId)
  else expanded.value.add(nodeId)
}

function seqnoClass(node: GrastateNodeResult): string {
  if (node.error) return 'cell-err-text'
  if (node.seqno === null) return 'cell-muted'
  if (node.seqno === -1) return 'cell-warn'
  if (node.seqno === data.value?.analysis?.max_seqno) return 'cell-max'
  return 'cell-mono'
}

function stbSeverity(v: boolean | null): 'success' | 'secondary' | 'danger' {
  if (v === true) return 'success'
  if (v === false) return 'danger'
  return 'secondary'
}
</script>

<template>
  <div class="gs-panel">

    <!-- Header -->
    <div class="gs-header">
      <div class="gs-header-left">
        <h3 class="gs-title">grastate.dat Inspector</h3>
        <p class="gs-desc">Reads <code>grastate.dat</code> from all nodes. Use before Bootstrap to verify safe_to_bootstrap and seqno values.</p>
      </div>
      <Button
        icon="pi pi-refresh"
        label="Scan"
        :loading="loading"
        size="small"
        @click="load()"
      />
    </div>

    <!-- Warnings from analysis -->
    <template v-if="data?.analysis?.warnings?.length">
      <Message
        v-for="(w, i) in data.analysis.warnings"
        :key="i"
        :severity="w.level === 'danger' ? 'error' : 'warn'"
        :closable="false"
        class="gs-warning"
      >
        {{ w.message }}
      </Message>
    </template>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <!-- Analysis summary -->
    <div v-if="data && !loading" class="gs-summary">
      <div class="gs-stat">
        <span class="gs-stat-label">Max seqno</span>
        <span class="gs-stat-val gs-stat-val--max">{{ data.analysis.max_seqno ?? '—' }}</span>
      </div>
      <div class="gs-stat-sep" />
      <div class="gs-stat">
        <span class="gs-stat-label">Safe to bootstrap</span>
        <span class="gs-stat-val" :class="data.analysis.safe_bootstrap_count > 0 ? 'gs-stat-val--ok' : 'gs-stat-val--warn'">
          {{ data.analysis.safe_bootstrap_count }} node{{ data.analysis.safe_bootstrap_count !== 1 ? 's' : '' }}
        </span>
      </div>
      <div class="gs-stat-sep" />
      <div class="gs-stat">
        <span class="gs-stat-label">Dirty crash</span>
        <span class="gs-stat-val" :class="data.analysis.dirty_crash_count > 0 ? 'gs-stat-val--warn' : ''">
          {{ data.analysis.dirty_crash_count }} node{{ data.analysis.dirty_crash_count !== 1 ? 's' : '' }}
        </span>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !data" class="gs-skeleton">
      <Skeleton v-for="i in 3" :key="i" height="52px" />
    </div>

    <!-- Table -->
    <DataTable
      v-else-if="data"
      :value="data.nodes"
      dataKey="node_id"
      size="small"
      class="settings-table gs-table"
    >
      <template #empty>
        <div class="panel-empty"><i class="pi pi-inbox" /><span>No nodes</span></div>
      </template>

      <Column field="node_name" header="Node">
        <template #body="{ data: row }">
          <div class="cell-node">
            <span class="cell-node-name">{{ row.node_name }}</span>
            <span class="cell-node-host">{{ row.host }}</span>
          </div>
        </template>
      </Column>

      <Column header="seqno" style="width: 100px">
        <template #body="{ data: row }">
          <div class="cell-seqno-wrap">
            <span :class="seqnoClass(row)">
              {{ row.error ? 'ERR' : (row.seqno ?? '—') }}
            </span>
            <span v-if="row.seqno === -1" class="cell-seqno-note">wsrep-recover needed</span>
            <Tag
              v-if="row.seqno === data?.analysis?.max_seqno && row.seqno !== null"
              value="MAX"
              severity="success"
              class="max-tag"
            />
          </div>
        </template>
      </Column>

      <Column header="safe_to_btsp" style="width: 130px">
        <template #body="{ data: row }">
          <Tag
            v-if="row.safe_to_bootstrap !== null"
            :value="row.safe_to_bootstrap ? 'YES' : 'NO'"
            :severity="stbSeverity(row.safe_to_bootstrap)"
            :icon="!row.safe_to_bootstrap ? 'pi pi-times' : 'pi pi-check'"
          />
          <span v-else class="cell-muted">—</span>
        </template>
      </Column>

      <Column header="UUID" style="width: 260px">
        <template #body="{ data: row }">
          <span class="cell-uuid">{{ row.uuid ?? (row.error ? '—' : '—') }}</span>
        </template>
      </Column>

      <Column header="gvwstate" style="width: 100px">
        <template #body="{ data: row }">
          <Tag
            v-if="!row.error"
            :value="row.gvwstate_exists ? 'EXISTS' : 'ABSENT'"
            :severity="row.gvwstate_exists ? 'info' : 'secondary'"
          />
          <span v-else class="cell-muted">—</span>
        </template>
      </Column>

      <Column header="Raw / Error">
        <template #body="{ data: row }">
          <div v-if="row.error" class="cell-error">
            <i class="pi pi-exclamation-circle" />
            {{ row.error }}
          </div>
          <Button
            v-else-if="row.raw"
            size="small"
            text
            :icon="expanded.has(row.node_id) ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
            :label="expanded.has(row.node_id) ? 'Hide' : 'Show raw'"
            @click="toggleExpand(row.node_id)"
          />
          <span v-else class="cell-muted">—</span>
        </template>
      </Column>

    </DataTable>

    <!-- Expanded raw grastate.dat -->
    <template v-if="data">
      <div
        v-for="node in data.nodes"
        :key="`raw-${node.node_id}`"
        v-show="expanded.has(node.node_id) && node.raw"
        class="gs-raw-block"
      >
        <div class="gs-raw-label">{{ node.node_name }} — grastate.dat</div>
        <pre class="gs-raw">{{ node.raw }}</pre>
      </div>
    </template>

  </div>
</template>

<style scoped>
.gs-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.gs-header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4);
}
.gs-header-left { display: flex; flex-direction: column; gap: var(--space-1); }
.gs-title { font-size: var(--text-lg); font-weight: 700; color: var(--color-text); margin: 0; letter-spacing: -0.02em; }
.gs-desc  { font-size: var(--text-xs); color: var(--color-text-muted); margin: 0; }
.gs-desc code {
  font-family: var(--font-mono); font-size: 0.9em;
  background: var(--color-surface-3); border-radius: var(--radius-sm); padding: 1px 4px;
  color: var(--color-primary);
}

.gs-warning { width: 100%; }

.gs-summary {
  display: flex; align-items: center; gap: 0;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-5);
}
.gs-stat { display: flex; flex-direction: column; gap: 3px; flex: 1; align-items: center; }
.gs-stat-sep { width: 1px; height: 32px; background: var(--color-border); }
.gs-stat-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-text-faint); font-weight: 600; }
.gs-stat-val {
  font-size: var(--text-md); font-weight: 800; color: var(--color-text-muted);
  font-family: var(--font-mono); line-height: 1;
}
.gs-stat-val--max  { color: var(--color-synced); }
.gs-stat-val--ok   { color: var(--color-synced); }
.gs-stat-val--warn { color: var(--color-warning); }

.gs-skeleton { display: flex; flex-direction: column; gap: var(--space-2); }

.cell-node      { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-mono      { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-muted     { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-error     { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-error); }
.cell-error .pi { font-size: 0.7rem; }
.cell-err-text  { color: var(--color-error); font-size: var(--text-xs); font-family: var(--font-mono); }
.cell-warn      { color: var(--color-warning); font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 700; }
.cell-max       { color: var(--color-synced); font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 800; }
.cell-uuid      { font-family: var(--font-mono); font-size: 0.65rem; color: var(--color-text-faint); }
.cell-seqno-wrap { display: flex; flex-direction: column; gap: 2px; }
.cell-seqno-note { font-size: 0.6rem; color: var(--color-warning); font-style: italic; }
.max-tag { font-size: 0.6rem !important; }

.panel-empty {
  display: flex; align-items: center; gap: var(--space-3);
  color: var(--color-text-faint); padding: var(--space-6); font-size: var(--text-sm);
}

:deep(.settings-table .p-datatable-table-container) { border: none; box-shadow: none; border-radius: 0; }
:deep(.settings-table .p-datatable-thead > tr > th) {
  padding: var(--space-4) var(--space-6) !important; font-size: var(--text-xs) !important;
  font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--color-text-faint) !important; background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
}
:deep(.settings-table .p-datatable-tbody > tr > td) {
  padding: var(--space-4) var(--space-6) !important;
  border-bottom: 1px solid var(--color-border-muted) !important; vertical-align: middle;
}
:deep(.settings-table .p-datatable-tbody > tr:hover > td) { background: rgba(45,212,191,0.04) !important; }

.gs-raw-block {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.gs-raw-label {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-surface-3);
  border-bottom: 1px solid var(--color-border);
}
.gs-raw {
  margin: 0;
  padding: var(--space-4);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-primary);
  line-height: 1.7;
  overflow-x: auto;
  white-space: pre;
}
</style>
