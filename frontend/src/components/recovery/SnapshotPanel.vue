<script setup lang="ts">
/**
 * #7 Node State Snapshot — pre-flight one-shot dump.
 * Collects grastate.dat, wsrep status, active transactions, top processes, disk free.
 */
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { recoveryAdvancedApi, type SnapshotResponse, type SnapshotNodeResult } from '@/api/recovery-advanced'

const props = defineProps<{ clusterId: number | null }>()

const data    = ref<SnapshotResponse | null>(null)
const loading = ref(false)
const error   = ref<string | null>(null)
const expanded = ref<Set<number>>(new Set())

async function collect() {
  if (!props.clusterId) return
  loading.value = true
  error.value = null
  try {
    data.value = await recoveryAdvancedApi.takeSnapshot(props.clusterId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Snapshot failed'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, () => { data.value = null; error.value = null })

function toggleExpand(id: number) {
  if (expanded.value.has(id)) expanded.value.delete(id)
  else expanded.value.add(id)
}

function downloadJson() {
  if (!data.value) return
  const blob = new Blob([JSON.stringify(data.value, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `galera-snapshot-cluster${data.value.cluster_id}-${data.value.collected_at.slice(0, 19).replace(/[: ]/g, '-')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function fmtGb(gb: number | null): string {
  return gb !== null ? gb.toFixed(1) + ' GB free' : '—'
}

function wsrepState(node: SnapshotNodeResult): string | null {
  return node.wsrep_status?.['wsrep_local_state_comment'] ?? null
}
function wsrepClusterStatus(node: SnapshotNodeResult): string | null {
  return node.wsrep_status?.['wsrep_cluster_status'] ?? null
}
</script>

<template>
  <div class="snap-panel">

    <!-- Header -->
    <div class="snap-header">
      <div class="snap-header-left">
        <h3 class="snap-title">Pre-Flight Snapshot</h3>
        <p class="snap-desc">
          Collect a point-in-time state dump from all nodes before any recovery operation.
          Save the JSON file as evidence for post-mortem analysis.
        </p>
      </div>
      <div class="snap-header-actions">
        <Button
          v-if="data"
          icon="pi pi-download"
          label="Download JSON"
          size="small"
          outlined
          @click="downloadJson()"
        />
        <Button
          icon="pi pi-camera"
          :label="loading ? 'Collecting…' : 'Collect Snapshot'"
          :loading="loading"
          size="small"
          @click="collect()"
        />
      </div>
    </div>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <!-- Empty state -->
    <div v-if="!data && !loading" class="snap-empty">
      <div class="snap-empty-icon"><i class="pi pi-camera" /></div>
      <p>No snapshot collected yet.</p>
      <p class="snap-empty-hint">Click "Collect Snapshot" to gather live state from all nodes.</p>
    </div>

    <!-- Results -->
    <template v-if="data && !loading">
      <div class="snap-meta">
        <span class="snap-meta-item"><i class="pi pi-clock" />{{ data.collected_at.slice(0, 19).replace('T', ' ') }} UTC</span>
        <span class="snap-meta-item"><i class="pi pi-user" />{{ data.collected_by }}</span>
        <span class="snap-meta-item"><i class="pi pi-server" />{{ data.nodes.length }} nodes</span>
      </div>

      <div class="snap-nodes">
        <div
          v-for="node in data.nodes"
          :key="node.node_id"
          class="snap-node"
          :class="{
            'snap-node--ok':    node.ssh_ok && node.db_ok,
            'snap-node--warn':  node.ssh_ok && !node.db_ok,
            'snap-node--error': !node.ssh_ok || !!node.error,
          }"
        >
          <!-- Node header -->
          <div class="snap-node-header" @click="toggleExpand(node.node_id)">
            <div class="snap-node-left">
              <span class="snap-node-indicator" />
              <span class="snap-node-name">{{ node.node_name }}</span>
              <span class="snap-node-host">{{ node.host }}</span>
            </div>
            <div class="snap-node-badges">
              <Tag :value="node.ssh_ok ? 'SSH OK' : 'SSH FAIL'" :severity="node.ssh_ok ? 'success' : 'danger'" />
              <Tag :value="node.db_ok ? 'DB OK' : 'DB FAIL'" :severity="node.db_ok ? 'success' : 'danger'" />
              <Tag
                v-if="wsrepState(node)"
                :value="wsrepState(node)!"
                :severity="wsrepState(node) === 'Synced' || wsrepState(node) === 'SYNCED' ? 'success' : 'warn'"
              />
              <Tag
                v-if="node.active_transactions !== null"
                :value="`${node.active_transactions} trx`"
                :severity="node.active_transactions > 0 ? 'warn' : 'secondary'"
              />
              <span class="snap-node-disk">{{ fmtGb(node.disk_free_gb) }}</span>
              <i :class="expanded.has(node.node_id) ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="snap-node-chevron" />
            </div>
          </div>

          <!-- Expanded details -->
          <Transition name="expand">
            <div v-if="expanded.has(node.node_id)" class="snap-node-body">

              <div v-if="node.error" class="snap-error">
                <i class="pi pi-exclamation-circle" />{{ node.error }}
              </div>

              <!-- wsrep highlights -->
              <div v-if="node.wsrep_status" class="snap-section">
                <div class="snap-section-title">wsrep status</div>
                <div class="snap-wsrep-grid">
                  <template v-for="(val, key) in node.wsrep_status" :key="key">
                    <span class="ws-key">{{ key }}</span>
                    <span class="ws-val">{{ val }}</span>
                  </template>
                </div>
              </div>

              <!-- grastate.dat -->
              <div v-if="node.grastate" class="snap-section">
                <div class="snap-section-title">grastate.dat</div>
                <pre class="snap-pre">{{ node.grastate }}</pre>
              </div>

              <!-- Top processes -->
              <div v-if="node.top_processes?.length" class="snap-section">
                <div class="snap-section-title">Active processes (top 5 by time)</div>
                <div class="snap-procs">
                  <div v-for="p in node.top_processes" :key="p.id" class="snap-proc">
                    <span class="proc-id">#{{ p.id }}</span>
                    <span class="proc-user">{{ p.user }}</span>
                    <span class="proc-cmd">{{ p.command }}</span>
                    <span class="proc-time">{{ p.time }}s</span>
                    <span class="proc-state">{{ p.state }}</span>
                    <span v-if="p.info" class="proc-info">{{ p.info }}</span>
                  </div>
                </div>
              </div>

            </div>
          </Transition>
        </div>
      </div>
    </template>

  </div>
</template>

<style scoped>
.snap-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.snap-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; }
.snap-header-left  { display: flex; flex-direction: column; gap: var(--space-1); flex: 1; }
.snap-header-actions { display: flex; gap: var(--space-2); flex-shrink: 0; }
.snap-title { font-size: var(--text-lg); font-weight: 700; color: var(--color-text); margin: 0; letter-spacing: -0.02em; }
.snap-desc  { font-size: var(--text-xs); color: var(--color-text-muted); margin: 0; line-height: 1.5; }

/* Empty state */
.snap-empty {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--space-12) var(--space-4); text-align: center;
}
.snap-empty-icon {
  width: 64px; height: 64px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-2); border: 1px solid var(--color-border);
  font-size: 1.6rem; color: var(--color-text-faint);
}
.snap-empty p { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.snap-empty-hint { font-size: var(--text-xs) !important; color: var(--color-text-faint) !important; }

/* Meta row */
.snap-meta {
  display: flex; gap: var(--space-4); flex-wrap: wrap;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.snap-meta-item {
  display: flex; align-items: center; gap: var(--space-2);
  font-size: var(--text-xs); color: var(--color-text-muted);
}
.snap-meta-item .pi { font-size: 0.75rem; color: var(--color-primary); }

/* Node cards */
.snap-nodes { display: flex; flex-direction: column; gap: var(--space-3); }
.snap-node {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border-left: 3px solid var(--color-border);
  transition: border-left-color 200ms;
}
.snap-node--ok    { border-left-color: var(--color-synced); }
.snap-node--warn  { border-left-color: var(--color-warning); }
.snap-node--error { border-left-color: var(--color-error); }

.snap-node-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  cursor: pointer;
  user-select: none;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.snap-node-header:hover { background: var(--color-surface-3); }
.snap-node-left {
  display: flex; align-items: center; gap: var(--space-3);
}
.snap-node-indicator {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  .snap-node--ok &    { background: var(--color-synced); }
  .snap-node--warn &  { background: var(--color-warning); }
  .snap-node--error & { background: var(--color-error); }
}
.snap-node-name { font-weight: 700; font-size: var(--text-sm); color: var(--color-text); }
.snap-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.snap-node-badges { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
.snap-node-disk { font-size: var(--text-xs); color: var(--color-text-faint); font-family: var(--font-mono); }
.snap-node-chevron { font-size: 0.7rem; color: var(--color-text-faint); margin-left: var(--space-2); }

/* Body */
.snap-node-body {
  padding: var(--space-4);
  background: var(--color-surface);
  display: flex; flex-direction: column; gap: var(--space-4);
  border-top: 1px solid var(--color-border-muted);
}
.snap-error { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-error); }
.snap-error .pi { font-size: 0.75rem; }

.snap-section { display: flex; flex-direction: column; gap: var(--space-2); }
.snap-section-title {
  font-size: var(--text-xs); font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--color-text-faint);
}
.snap-wsrep-grid {
  display: grid; grid-template-columns: max-content 1fr;
  gap: 2px 16px;
  font-family: var(--font-mono); font-size: 0.65rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  max-height: 200px; overflow-y: auto;
}
.ws-key { color: var(--color-text-faint); white-space: nowrap; }
.ws-val { color: var(--color-primary); word-break: break-all; }

.snap-pre {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-mono); font-size: var(--text-xs);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-primary); line-height: 1.7;
  overflow-x: auto; white-space: pre;
}

.snap-procs { display: flex; flex-direction: column; gap: 4px; }
.snap-proc {
  display: flex; gap: var(--space-3); align-items: baseline;
  font-family: var(--font-mono); font-size: 0.65rem;
  padding: 3px 0; flex-wrap: wrap;
}
.proc-id    { color: var(--color-text-faint); min-width: 40px; }
.proc-user  { color: var(--color-primary); }
.proc-cmd   { color: var(--color-text-muted); }
.proc-time  { color: var(--color-warning); }
.proc-state { color: var(--color-text-faint); }
.proc-info  { color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; max-width: 300px; }

/* Transition */
.expand-enter-active { transition: max-height 280ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease; max-height: 800px; }
.expand-leave-active { transition: max-height 200ms ease, opacity 150ms ease; }
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; overflow: hidden; }
</style>
