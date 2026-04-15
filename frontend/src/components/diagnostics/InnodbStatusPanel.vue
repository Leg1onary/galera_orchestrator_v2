<template>
  <div class="diag-panel">
    <PanelToolbar
        title="SHOW ENGINE INNODB STATUS"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = $event"
    />

    <!-- Node selector -->
    <div class="selector-row">
      <label class="sel-label">Node</label>
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="Select node…"
          class="node-select"
          size="small"
      />
    </div>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ errorMessage }}</span>
    </div>

    <template v-else-if="data">
      <!-- Deadlock banner -->
      <div v-if="data.has_deadlock" class="deadlock-banner">
        <i class="pi pi-exclamation-triangle" />
        <span>Latest detected deadlock found in InnoDB status</span>
      </div>

      <!-- Structured deadlock card (#16) -->
      <template v-if="data.has_deadlock && data.deadlock_parsed">
        <div class="deadlock-card">
          <div class="deadlock-card-header">
            <div class="deadlock-card-title">
              <i class="pi pi-bolt" />
              <span>Latest Deadlock</span>
              <span v-if="data.deadlock_parsed.ts" class="deadlock-ts">{{ data.deadlock_parsed.ts }}</span>
            </div>
            <button class="copy-btn" v-tooltip="'Copy raw deadlock text'" @click="copyText(data.latest_deadlock!)">
              <i class="pi pi-copy" />
              <span>Copy raw</span>
            </button>
          </div>

          <div class="deadlock-trx-grid">
            <!-- Transaction A -->
            <div
                class="deadlock-trx"
                :class="{ 'trx-victim': data.deadlock_parsed.victim === data.deadlock_parsed.transaction_a?.id }"
            >
              <div class="trx-header">
                <span class="trx-label">Transaction A</span>
                <span
                    v-if="data.deadlock_parsed.victim === data.deadlock_parsed.transaction_a?.id"
                    class="victim-badge"
                >
                  <i class="pi pi-times-circle" /> Victim (rolled back)
                </span>
              </div>
              <div class="trx-fields">
                <div class="trx-row" v-if="data.deadlock_parsed.transaction_a?.id">
                  <span class="trx-key">TRX ID</span>
                  <span class="trx-val mono">{{ data.deadlock_parsed.transaction_a.id }}</span>
                </div>
                <div class="trx-row" v-if="data.deadlock_parsed.transaction_a?.table">
                  <span class="trx-key">Table</span>
                  <span class="trx-val mono">{{ data.deadlock_parsed.transaction_a.table }}</span>
                </div>
                <div class="trx-row" v-if="data.deadlock_parsed.transaction_a?.lock_type">
                  <span class="trx-key">Lock</span>
                  <span class="trx-val">
                    <span class="lock-badge">{{ data.deadlock_parsed.transaction_a.lock_type }}</span>
                    <span v-if="data.deadlock_parsed.transaction_a.lock_mode" class="lock-mode">
                      {{ data.deadlock_parsed.transaction_a.lock_mode }}
                    </span>
                    <span v-if="data.deadlock_parsed.transaction_a.waiting !== null" class="lock-wait">
                      {{ data.deadlock_parsed.transaction_a.waiting ? 'waiting' : 'held' }}
                    </span>
                  </span>
                </div>
                <div class="trx-row trx-query" v-if="data.deadlock_parsed.transaction_a?.query">
                  <span class="trx-key">Query</span>
                  <span class="trx-val mono query-text" :title="data.deadlock_parsed.transaction_a.query">
                    {{ data.deadlock_parsed.transaction_a.query }}
                  </span>
                </div>
              </div>
            </div>

            <div class="deadlock-vs"><span>VS</span></div>

            <!-- Transaction B -->
            <div
                class="deadlock-trx"
                :class="{ 'trx-victim': data.deadlock_parsed.victim === data.deadlock_parsed.transaction_b?.id }"
            >
              <div class="trx-header">
                <span class="trx-label">Transaction B</span>
                <span
                    v-if="data.deadlock_parsed.victim === data.deadlock_parsed.transaction_b?.id"
                    class="victim-badge"
                >
                  <i class="pi pi-times-circle" /> Victim (rolled back)
                </span>
              </div>
              <div class="trx-fields">
                <div class="trx-row" v-if="data.deadlock_parsed.transaction_b?.id">
                  <span class="trx-key">TRX ID</span>
                  <span class="trx-val mono">{{ data.deadlock_parsed.transaction_b.id }}</span>
                </div>
                <div class="trx-row" v-if="data.deadlock_parsed.transaction_b?.table">
                  <span class="trx-key">Table</span>
                  <span class="trx-val mono">{{ data.deadlock_parsed.transaction_b.table }}</span>
                </div>
                <div class="trx-row" v-if="data.deadlock_parsed.transaction_b?.lock_type">
                  <span class="trx-key">Lock</span>
                  <span class="trx-val">
                    <span class="lock-badge">{{ data.deadlock_parsed.transaction_b.lock_type }}</span>
                    <span v-if="data.deadlock_parsed.transaction_b.lock_mode" class="lock-mode">
                      {{ data.deadlock_parsed.transaction_b.lock_mode }}
                    </span>
                    <span v-if="data.deadlock_parsed.transaction_b.waiting !== null" class="lock-wait">
                      {{ data.deadlock_parsed.transaction_b.waiting ? 'waiting' : 'held' }}
                    </span>
                  </span>
                </div>
                <div class="trx-row trx-query" v-if="data.deadlock_parsed.transaction_b?.query">
                  <span class="trx-key">Query</span>
                  <span class="trx-val mono query-text" :title="data.deadlock_parsed.transaction_b.query">
                    {{ data.deadlock_parsed.transaction_b.query }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Fallback: raw deadlock text if parsing failed -->
      <template v-else-if="data.has_deadlock && data.latest_deadlock">
        <div class="terminal-block">
          <div class="terminal-header">
            <span class="terminal-label terminal-label-warn">latest_deadlock</span>
            <button class="copy-btn" @click="copyText(data.latest_deadlock!)">
              <i class="pi pi-copy" />
              <span>Copy</span>
            </button>
          </div>
          <div class="terminal-wrap">
            <pre class="innodb-pre pre-warn">{{ data.latest_deadlock }}</pre>
          </div>
        </div>
      </template>

      <!-- Full status block -->
      <div class="terminal-block">
        <div class="terminal-header">
          <span class="terminal-label">full_status</span>
          <button class="copy-btn" v-tooltip="'Copy to clipboard'" @click="copyText(data.full_status)">
            <i class="pi pi-copy" />
            <span>Copy</span>
          </button>
        </div>
        <div class="terminal-wrap">
          <pre class="innodb-pre">{{ data.full_status }}</pre>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading && selectedNodeId" class="empty-state">
      <div class="empty-icon"><i class="pi pi-database" /></div>
      <p>No data yet. Click refresh to load.</p>
    </div>

    <div v-else-if="!selectedNodeId" class="empty-state">
      <div class="empty-icon"><i class="pi pi-database" /></div>
      <p>Select a node to view InnoDB status.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, toRef } from 'vue'
import { useQuery }   from '@tanstack/vue-query'
import { useToast }   from 'primevue/usetoast'
import Select         from 'primevue/select'
import { useClusterStore }    from '@/stores/cluster'
import { useSettingsStore }   from '@/stores/settings'
import { nodesApi }           from '@/api/nodes'
import PanelToolbar           from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions }     from '@/composables/useNodeOptions'

const props = defineProps<{ active: boolean }>()
const clusterStore   = useClusterStore()
const settingsStore  = useSettingsStore()
const toast          = useToast()
const selectedNodeId = ref<number | null>(null)

const intervalMs = computed(() => settingsStore.pollingIntervalSec * 1000)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(toRef(props, 'active'), intervalMs)

const { nodeOptions } = useNodeOptions()

watch(nodeOptions, (opts) => {
  if (opts.length && !selectedNodeId.value) selectedNodeId.value = opts[0].value
}, { immediate: true })

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-innodb', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => nodesApi.innodbStatus(clusterStore.selectedClusterId!, selectedNodeId.value!),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId && !!selectedNodeId.value),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const errorMessage = computed(() => {
  if (!error.value) return ''
  if (error.value instanceof Error) return error.value.message
  if (typeof error.value === 'string') return error.value
  return 'An unknown error occurred'
})

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
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); padding: var(--space-4); }

.selector-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.sel-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.node-select { width: 220px; }

.deadlock-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-warning-highlight);
  border: 1px solid oklch(from var(--color-warning) l c h / 0.25);
  color: var(--color-warning);
  font-size: var(--text-sm);
  font-weight: 600;
}

/* ── Deadlock Card (#16) ─────────────────────────────────────────────────── */

.deadlock-card {
  border: 1px solid oklch(from var(--color-warning) l c h / 0.30);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface);
}

.deadlock-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: var(--color-warning-highlight);
  border-bottom: 1px solid oklch(from var(--color-warning) l c h / 0.20);
}

.deadlock-card-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-warning);
}

.deadlock-ts {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  font-weight: 400;
  color: var(--color-text-muted);
  margin-left: var(--space-2);
}

.deadlock-trx-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0;
}

.deadlock-vs {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 var(--space-3);
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-faint);
  border-left: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
}

.deadlock-trx {
  padding: var(--space-4);
}

.deadlock-trx.trx-victim {
  background: oklch(from var(--color-error) l c h / 0.04);
}

.trx-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.trx-label {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.victim-badge {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-error);
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-error-highlight);
}

.trx-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.trx-row {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: var(--space-2);
  align-items: baseline;
}

.trx-key {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.trx-val {
  font-size: var(--text-xs);
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.mono { font-family: var(--font-mono); }

.lock-badge {
  padding: 1px var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.lock-mode {
  font-family: var(--font-mono);
  color: var(--color-warning);
  font-weight: 600;
}

.lock-wait {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-style: italic;
}

.trx-query .trx-val { align-items: flex-start; }

.query-text {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  cursor: default;
}

/* ── Terminal blocks ─────────────────────────────────────────────────────────── */

.terminal-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
}

.terminal-label {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text-muted);
}

.terminal-label-warn { color: var(--color-warning); }

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
.copy-btn:hover { background: var(--color-surface-3); border-color: var(--color-border-hover); color: var(--color-text); }

.terminal-wrap { background: var(--color-terminal-bg); }

.innodb-pre {
  margin: 0;
  padding: var(--space-4) var(--space-5);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-terminal-ok);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 520px;
  overflow-y: auto;
}

.pre-warn { color: var(--color-terminal-warn); }

.innodb-pre::-webkit-scrollbar       { width: 4px; }
.innodb-pre::-webkit-scrollbar-track { background: transparent; }
.innodb-pre::-webkit-scrollbar-thumb { background: oklch(from var(--color-terminal-ok) l c h / 0.2); border-radius: 2px; }

.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-error-highlight);
  border: 1px solid oklch(from var(--color-error) l c h / 0.20);
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

@media (max-width: 700px) {
  .deadlock-trx-grid {
    grid-template-columns: 1fr;
  }
  .deadlock-vs {
    border: none;
    border-top: 1px solid var(--color-border);
    border-bottom: 1px solid var(--color-border);
    padding: var(--space-2) 0;
  }
}
</style>
