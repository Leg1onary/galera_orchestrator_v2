<template>
  <div class="wizard-step">

    <!-- HEADER -->
    <div class="step-header">
      <h2 class="step-title">Step 1 — Scan nodes</h2>
      <p class="step-desc">
        The orchestrator will read cluster status and node states
        to determine which node is safe to bootstrap.
      </p>
    </div>

    <!-- IDLE -->
    <div v-if="!store.clusterStatus && !store.statusLoading" class="state-idle">
      <div class="state-idle-icon"><i class="pi pi-search" /></div>
      <p class="state-idle-hint">No scan performed yet.</p>
      <Button label="Start scan" icon="pi pi-play" class="idle-btn" @click="store.loadStatus()" />
    </div>

    <!-- LOADING -->
    <div v-else-if="store.statusLoading" class="state-scanning">
      <ProgressSpinner style="width: 36px; height: 36px" />
      <p class="state-scanning-hint">Reading cluster status…</p>
    </div>

    <!-- ERROR -->
    <div v-else-if="store.statusError" class="state-error">
      <div class="state-error-icon"><i class="pi pi-times-circle" /></div>
      <p class="state-error-msg">{{ store.statusError }}</p>
      <Button label="Retry" icon="pi pi-refresh" size="small" outlined @click="store.loadStatus()" />
    </div>

    <!-- RESULTS -->
    <template v-else-if="store.clusterStatus">

      <!-- Cluster healthy banner -->
      <div v-if="clusterIsHealthy" class="result-banner result-banner--success">
        <i class="pi pi-check-circle" />
        <div>
          <strong>Cluster appears healthy</strong>
          <p>All nodes are reachable and SYNCED. Recovery is not required.</p>
        </div>
      </div>

      <!-- NODE TABLE -->
      <div class="scan-table-wrap">
        <!-- Empty state -->
        <div v-if="!store.clusterStatus.nodes?.length" class="scan-empty">
          <i class="pi pi-exclamation-circle" />
          <span>No nodes returned from scan. Check SSH connectivity.</span>
        </div>

        <DataTable
            v-else
            :value="store.clusterStatus.nodes"
            dataKey="id"
            size="small"
            class="scan-table"
            scrollable
            scrollHeight="360px"
        >
          <Column field="name" header="Node" :sortable="true">
            <template #body="{ data }">
              <div class="cell-node">
                <span class="cell-node-name">{{ data.name }}</span>
                <span class="cell-node-host">{{ data.host }}</span>
              </div>
            </template>
          </Column>

          <Column header="SSH" style="width: 72px">
            <template #body="{ data }">
              <span class="ssh-badge" :class="data.live?.ssh_ok ? 'ssh-badge--ok' : 'ssh-badge--fail'">
                <i :class="data.live?.ssh_ok ? 'pi pi-check' : 'pi pi-times'" />
                {{ data.live?.ssh_ok ? 'OK' : 'FAIL' }}
              </span>
            </template>
          </Column>

          <Column header="DB" style="width: 72px">
            <template #body="{ data }">
              <span class="ssh-badge" :class="data.live?.db_ok ? 'ssh-badge--ok' : 'ssh-badge--fail'">
                <i :class="data.live?.db_ok ? 'pi pi-check' : 'pi pi-times'" />
                {{ data.live?.db_ok ? 'OK' : 'FAIL' }}
              </span>
            </template>
          </Column>

          <Column header="State" style="width: 140px">
            <template #body="{ data }">
              <span v-if="!data.live" class="cell-muted">—</span>
              <span v-else class="cell-state" :class="stateClass(data.live.wsrep_local_state_comment)">
                {{ data.live.wsrep_local_state_comment ?? 'unknown' }}
              </span>
            </template>
          </Column>

          <Column header="Connected" style="width: 110px">
            <template #body="{ data }">
              <span v-if="!data.live" class="cell-muted">—</span>
              <span v-else class="stb-badge" :class="data.live.wsrep_connected === 'ON' ? 'stb-badge--yes' : 'stb-badge--no'">
                {{ data.live.wsrep_connected === 'ON' ? 'YES' : 'NO' }}
              </span>
            </template>
          </Column>

          <!-- seqno column: key for bootstrap node selection -->
          <Column header="seqno" style="width: 90px">
            <template #body="{ data }">
              <span v-if="data.live?.seqno == null" class="cell-muted">—</span>
              <span v-else class="cell-seqno" :class="data.live.seqno === maxSeqno ? 'cell-seqno--max' : ''">
                {{ data.live.seqno }}
              </span>
            </template>
          </Column>

          <!-- safe_to_bootstrap: critical safety field from grastate.dat -->
          <Column header="safe_to_btsp" style="width: 110px">
            <template #body="{ data }">
              <span v-if="data.live?.safe_to_bootstrap == null" class="cell-muted">—</span>
              <span
                v-else
                class="stb-badge"
                :class="data.live.safe_to_bootstrap === 1 ? 'stb-badge--yes' : 'stb-badge--no'"
              >
                <i v-if="data.live.safe_to_bootstrap !== 1" class="pi pi-exclamation-triangle" style="font-size:0.6rem" />
                {{ data.live.safe_to_bootstrap === 1 ? 'YES' : 'NO' }}
              </span>
            </template>
          </Column>

          <Column header="Error">
            <template #body="{ data }">
              <span v-if="data.live?.error" class="cell-error">{{ data.live.error }}</span>
              <span v-else class="cell-muted">—</span>
            </template>
          </Column>
        </DataTable>
      </div>

      <!-- ACTIONS -->
      <div class="step-actions">
        <Button label="Re-scan" icon="pi pi-refresh" outlined size="small" @click="store.loadStatus()" />

        <!-- When healthy: offer navigation to Overview instead of disabled Next -->
        <Button
          v-if="clusterIsHealthy"
          label="Go to Overview"
          icon="pi pi-home"
          outlined
          size="small"
          @click="emit('go-overview')"
        />

        <span
          v-else
          v-tooltip.top="nextButtonTooltip"
          :class="{ 'next-btn-wrapper': isNextDisabled }"
        >
          <Button
            label="Next: Select bootstrap node"
            icon="pi pi-arrow-right"
            iconPos="right"
            :disabled="isNextDisabled"
            @click="emit('next')"
          />
        </span>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ProgressSpinner from 'primevue/progressspinner'
import { useRecoveryStore } from '@/stores/recovery'
import { useRouter } from 'vue-router'

const emit = defineEmits<{ next: []; 'go-overview': [] }>()
const store = useRecoveryStore()
const router = useRouter()

const clusterIsHealthy = computed(
  () => store.clusterStatus?.cluster_status === 'healthy'
)

// Simplified: previous expr had redundant double condition
const hasOfflineNodes = computed(() =>
  (store.clusterStatus?.nodes ?? []).some(
    (n: any) => n.live?.wsrep_connected !== 'ON'
  )
)

const isNextDisabled = computed(() => clusterIsHealthy.value || !hasOfflineNodes.value)

const nextButtonTooltip = computed(() => {
  if (!isNextDisabled.value) return undefined
  if (clusterIsHealthy.value)
    return 'All nodes are Synced — the cluster is healthy. Recovery is not needed.'
  if (!hasOfflineNodes.value)
    return 'All nodes show wsrep_connected = ON. No offline nodes detected — recovery is not required.'
  return undefined
})

// Max seqno across nodes for highlighting the candidate
const maxSeqno = computed(() => {
  const seqnos = (store.clusterStatus?.nodes ?? [])
    .map((n: any) => n.live?.seqno)
    .filter((s: any) => s != null) as number[]
  return seqnos.length ? Math.max(...seqnos) : null
})

// Fixed: API returns uppercase SYNCED/JOINED/DONOR/DESYNCED
function stateClass(state: string | null): string {
  if (!state) return 'cell-state--unknown'
  const s = state.toUpperCase()
  if (s === 'SYNCED')               return 'cell-state--synced'
  if (s === 'JOINED')               return 'cell-state--joined'
  if (s === 'DONOR' || s === 'DESYNCED') return 'cell-state--donor'
  if (s === 'JOINER')               return 'cell-state--donor'
  return 'cell-state--other'
}
</script>

<style scoped>
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  height: 100%;
}

.step-header { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title  { font-size: var(--text-xl); font-weight: 700; color: var(--color-text); letter-spacing: -0.02em; }
.step-desc   { font-size: var(--text-sm); color: var(--color-text-muted); line-height: 1.5; }

/* IDLE */
.state-idle {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: var(--space-6); padding: var(--space-16) 0; flex: 1;
}
.state-idle-icon {
  width: 72px; height: 72px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-offset); color: var(--color-text-faint);
  font-size: 1.8rem; border: 1px solid var(--color-border);
}
.state-idle-hint { font-size: var(--text-base); color: var(--color-text-muted); }
.state-idle :deep(.idle-btn.p-button) { padding: var(--space-3) var(--space-8); font-size: var(--text-base); font-weight: 600; }

/* SCANNING */
.state-scanning {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: var(--space-4); padding: var(--space-16) 0; flex: 1;
}
.state-scanning-hint { font-size: var(--text-sm); color: var(--color-text-muted); }

/* ERROR */
.state-error {
  display: flex; flex-direction: column;
  align-items: center; gap: var(--space-3);
  padding: var(--space-12) 0; flex: 1;
}
.state-error-icon {
  font-size: 2rem; color: var(--color-error);
  width: 56px; height: 56px;
  display: flex; align-items: center; justify-content: center;
  background: color-mix(in oklch, var(--color-error) 12%, transparent);
  border-radius: var(--radius-full);
}
.state-error-msg { font-size: var(--text-sm); color: var(--color-error); text-align: center; max-width: 48ch; }

/* BANNER */
.result-banner {
  display: flex; align-items: flex-start;
  gap: var(--space-3); padding: var(--space-4);
  border-radius: var(--radius-md); border: 1px solid transparent;
  font-size: var(--text-sm); line-height: 1.5;
}
.result-banner i { font-size: 1.1rem; margin-top: 1px; flex-shrink: 0; }
.result-banner strong { display: block; font-weight: 600; margin-bottom: 2px; }
.result-banner p { margin: 0; color: var(--color-text-muted); font-size: var(--text-xs); }
.result-banner--success {
  background: color-mix(in oklch, var(--color-success) 10%, transparent);
  border-color: color-mix(in oklch, var(--color-success) 30%, transparent);
  color: var(--color-success);
}

/* TABLE */
.scan-table-wrap { border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow: hidden; }
.scan-empty {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-6) var(--space-5);
  color: var(--color-text-muted); font-size: var(--text-sm);
}
.scan-empty .pi { color: var(--color-warning); font-size: 1rem; }

/* CELLS */
.cell-node        { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name   { font-size: var(--text-sm); font-weight: 600; color: var(--color-text); }
.cell-node-host   { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-muted       { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-error       { font-size: var(--text-xs); color: var(--color-error); }

.cell-state              { font-size: var(--text-xs); font-weight: 600; }
.cell-state--synced      { color: var(--color-success); }
.cell-state--joined      { color: var(--color-primary); }
.cell-state--donor       { color: var(--color-warning); }
.cell-state--other       { color: var(--color-warning); }
.cell-state--unknown     { color: var(--color-text-faint); }

/* seqno highlight */
.cell-seqno         { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-seqno--max    {
  color: var(--color-success); font-weight: 700;
  background: color-mix(in oklch, var(--color-success) 10%, transparent);
  border-radius: var(--radius-sm); padding: 1px 5px;
}

/* SSH / connected badges */
.ssh-badge {
  display: inline-flex; align-items: center;
  gap: 4px; font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.06em; padding: 3px 9px;
  border-radius: var(--radius-full);
}
.ssh-badge--ok {
  background: color-mix(in oklch, var(--color-success) 14%, transparent);
  color: var(--color-success);
  border: 1px solid color-mix(in oklch, var(--color-success) 30%, transparent);
}
.ssh-badge--fail {
  background: color-mix(in oklch, var(--color-error) 14%, transparent);
  color: var(--color-error);
  border: 1px solid color-mix(in oklch, var(--color-error) 30%, transparent);
}
.stb-badge {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.08em; padding: 3px 10px;
  border-radius: var(--radius-full);
}
.stb-badge--yes {
  background: color-mix(in oklch, var(--color-success) 14%, transparent);
  color: var(--color-success);
  border: 1px solid color-mix(in oklch, var(--color-success) 30%, transparent);
}
.stb-badge--no {
  background: color-mix(in oklch, var(--color-text-faint) 12%, transparent);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

/* ACTIONS */
.step-actions {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: var(--space-2); border-top: 1px solid var(--color-border); margin-top: auto;
}
.next-btn-wrapper { display: inline-flex; cursor: not-allowed; }
.next-btn-wrapper :deep(.p-button:disabled) { pointer-events: none; }
</style>
