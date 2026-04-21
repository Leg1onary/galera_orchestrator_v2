<script setup lang="ts">
import { ref, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type ConfigHealthNodeResult } from '@/api/diagnostics'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

const loading  = ref(false)
const error    = ref<string | null>(null)
const results  = ref<ConfigHealthNodeResult[]>([])
const fetched  = ref(false)

const STATUS_META = {
  ok:    { severity: 'success' as const, label: 'OK',   icon: 'pi-check-circle'       },
  warn:  { severity: 'warn'    as const, label: 'WARN', icon: 'pi-exclamation-circle' },
  error: { severity: 'danger'  as const, label: 'ERR',  icon: 'pi-times-circle'       },
  info:  { severity: 'info'    as const, label: 'INFO', icon: 'pi-info-circle'        },
} as const

async function load() {
  const cid = clusterStore.selectedClusterId
  if (!cid) return
  loading.value = true
  error.value   = null
  try {
    results.value = await diagnosticsApi.getConfigHealth(cid)
    fetched.value = true
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

watch(() => props.active, (val) => { if (val && !fetched.value) load() })
watch(() => clusterStore.selectedClusterId, () => { fetched.value = false; results.value = [] })

// Flatten checks for DataTable per node
function nodeStatus(node: ConfigHealthNodeResult) {
  const counts = { error: 0, warn: 0, ok: 0, info: 0 }
  for (const c of node.checks) counts[c.status as keyof typeof counts] = (counts[c.status as keyof typeof counts] || 0) + 1
  return counts
}
</script>

<template>
  <div class="cfg-health">

    <!-- Header toolbar -->
    <div class="cfg-toolbar">
      <div class="cfg-toolbar-left">
        <span class="cfg-toolbar-icon">
          <i class="pi pi-shield" />
        </span>
        <div>
          <div class="cfg-toolbar-title">Config Health Check</div>
          <div class="cfg-toolbar-sub">Checking key MariaDB parameters against best-practice rules</div>
        </div>
      </div>
      <Button
        label="Run Check"
        icon="pi pi-play"
        :loading="loading"
        size="small"
        @click="load"
      />
    </div>

    <!-- Error -->
    <div v-if="error" class="cfg-error">
      <i class="pi pi-exclamation-triangle" />
      <span>{{ error }}</span>
    </div>

    <!-- Idle -->
    <div v-else-if="!fetched && !loading" class="cfg-idle">
      <div class="cfg-idle-icon"><i class="pi pi-shield" /></div>
      <p class="cfg-idle-title">Config Health not started</p>
      <p class="cfg-idle-hint">Click "Run Check" to verify configuration on all cluster nodes.</p>
      <Button label="Run Check" icon="pi pi-play" outlined size="small" @click="load" />
    </div>

    <!-- Loading skeleton -->
    <div v-else-if="loading" class="cfg-loading">
      <div v-for="i in 3" :key="i" class="cfg-skeleton">
        <div class="sk-header"></div>
        <div class="sk-row"></div>
        <div class="sk-row sk-row--short"></div>
        <div class="sk-row"></div>
        <div class="sk-row sk-row--short"></div>
      </div>
    </div>

    <!-- Results -->
    <template v-else>
      <div
        v-for="node in results"
        :key="node.node_id"
        class="node-card"
      >
        <!-- Node header -->
        <div class="node-card-head">
          <div class="node-card-info">
            <span class="node-name">{{ node.node_name }}</span>
            <span class="node-host">{{ node.host }}</span>
          </div>

          <!-- Error badge -->
          <Tag v-if="node.error" severity="danger" :value="node.error" class="node-err-tag" />

          <!-- Stats badges -->
          <template v-else>
            <div class="node-stats">
              <Tag
                v-for="st in ['error', 'warn', 'ok', 'info'] as const"
                :key="st"
                :severity="STATUS_META[st].severity"
                :value="`${nodeStatus(node)[st]} ${STATUS_META[st].label}`"
                rounded
                class="node-stat-tag"
              />
            </div>
          </template>
        </div>

        <!-- DataTable of checks -->
        <DataTable
          v-if="node.checks.length"
          :value="node.checks"
          size="small"
          :show-gridlines="false"
          class="node-table"
          row-class-name="check-row"
        >
          <Column field="param" header="Parameter" class="col-param">
            <template #body="{ data }">
              <div class="param-wrap">
                <span
                  class="param-status-dot"
                  :class="`dot--${data.status}`"
                />
                <code class="param-code">{{ data.param }}</code>
              </div>
            </template>
          </Column>

          <Column field="current_human" header="Value" class="col-val">
            <template #body="{ data }">
              <span class="val-mono">{{ data.current_human }}</span>
            </template>
          </Column>

          <Column header="Status" class="col-status">
            <template #body="{ data }">
              <Tag
                :severity="STATUS_META[data.status as keyof typeof STATUS_META].severity"
                rounded
                class="status-tag"
              >
                <template #default>
                  <i :class="['pi', STATUS_META[data.status as keyof typeof STATUS_META].icon]" />
                  {{ STATUS_META[data.status as keyof typeof STATUS_META].label }}
                </template>
              </Tag>
            </template>
          </Column>

          <Column header="Recommendation" class="col-rec">
            <template #body="{ data }">
              <span v-if="data.recommendation" class="rec-text">{{ data.recommendation }}</span>
              <span v-if="data.context" class="ctx-text">{{ data.context }}</span>
              <span v-if="!data.recommendation && !data.context" class="ctx-text">—</span>
            </template>
          </Column>
        </DataTable>

      </div>
    </template>

  </div>
</template>

<style scoped>
.cfg-health {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* Toolbar */
.cfg-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.cfg-toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.cfg-toolbar-icon {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-highlight);
  border: 1px solid rgba(45,212,191,0.20);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-size: 0.85rem;
  flex-shrink: 0;
}
.cfg-toolbar-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}
.cfg-toolbar-sub {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 1px;
}

/* Error */
.cfg-error {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid rgba(248,113,113,0.25);
  border-radius: var(--radius-lg);
  color: var(--color-error);
  font-size: var(--text-sm);
}

/* Idle */
.cfg-idle {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: var(--space-3);
  padding: var(--space-12) var(--space-8);
  text-align: center;
}
.cfg-idle-icon {
  width: 48px; height: 48px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  color: var(--color-text-faint);
  font-size: 1.2rem;
}
.cfg-idle-title { font-size: var(--text-base); font-weight: 600; color: var(--color-text); }
.cfg-idle-hint  { font-size: var(--text-sm); color: var(--color-text-muted); max-width: 38ch; }

/* Skeleton */
.cfg-loading { display: flex; flex-direction: column; gap: var(--space-4); }
.cfg-skeleton { display: flex; flex-direction: column; gap: var(--space-2); }

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
.sk-header, .sk-row {
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-surface-offset) 25%,
    var(--color-surface-dynamic, var(--color-border)) 50%,
    var(--color-surface-offset) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
.sk-header { height: 32px; width: 280px; }
.sk-row    { height: 20px; width: 100%; }
.sk-row--short { width: 70%; }

/* Node card */
.node-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.node-card-head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-offset);
  border-bottom: 1px solid var(--color-border);
}
.node-card-info { display: flex; align-items: center; gap: var(--space-3); flex: 1; min-width: 0; }
.node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: monospace; }

.node-stats { display: flex; gap: var(--space-2); flex-wrap: wrap; align-items: center; }
.node-stat-tag {
  font-size: var(--text-xs) !important;
  padding: 3px 10px !important;
  font-weight: 600 !important;
}
.node-err-tag  { font-size: var(--text-xs) !important; }

/* DataTable overrides */
.node-table { font-size: var(--text-sm); }
:deep(.node-table .p-datatable-table) { border-collapse: collapse; }
:deep(.node-table .p-datatable-thead > tr > th) {
  background: var(--color-surface-2) !important;
  color: var(--color-text-faint);
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}
:deep(.node-table .p-datatable-tbody > tr > td) {
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border-muted);
  vertical-align: top;
}
:deep(.node-table .p-datatable-tbody > tr:last-child > td) { border-bottom: none; }
:deep(.node-table .p-datatable-tbody > tr:hover > td) {
  background: rgba(45, 212, 191, 0.035);
}

/* Param column */
.param-wrap { display: flex; align-items: center; gap: var(--space-2); }
.param-status-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}
.dot--ok    { background: var(--color-success); }
.dot--warn  { background: var(--color-warning); }
.dot--error { background: var(--color-error);   }
.dot--info  { background: var(--color-blue);    }

.param-code {
  font-family: monospace;
  font-size: 0.8em;
  background: rgba(228,228,231,0.05);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  color: var(--color-text);
}
.val-mono { font-family: monospace; color: var(--color-text); }

/* Status tag */
.status-tag {
  display: inline-flex !important;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs) !important;
  padding: 3px 10px !important;
  font-weight: 600 !important;
}
.status-tag .pi { font-size: var(--text-xs); }

/* Rec column */
.col-rec { max-width: 380px; }
.rec-text { display: block; color: var(--color-text); line-height: 1.4; }
.ctx-text {
  display: block;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  margin-top: 2px;
  font-style: italic;
}
</style>
