<template>
  <div class="wizard-step">

    <!-- HEADER -->
    <div class="step-header">
      <h2 class="step-title">Step 1 — Scan nodes</h2>
      <p class="step-desc">
        The orchestrator will connect to each node via SSH and read
        <code class="inline-code">grastate.dat</code> to determine which node is safe to bootstrap.
      </p>
    </div>

    <!-- IDLE -->
    <div v-if="!store.scanResult && !store.scanning" class="state-idle">
      <div class="state-idle-icon">
        <i class="pi pi-search" />
      </div>
      <p class="state-idle-hint">No scan performed yet.</p>
      <Button label="Start scan" icon="pi pi-play" class="idle-btn" @click="store.scan()" />
    </div>

    <!-- SCANNING -->
    <div v-else-if="store.scanning" class="state-scanning">
      <ProgressSpinner style="width: 36px; height: 36px" />
      <p class="state-scanning-hint">Connecting to nodes via SSH…</p>
    </div>

    <!-- SSH/SCAN ERROR -->
    <div v-else-if="store.scanError" class="state-error">
      <div class="state-error-icon"><i class="pi pi-times-circle" /></div>
      <p class="state-error-msg">{{ store.scanError }}</p>
      <Button label="Retry" icon="pi pi-refresh" size="small" outlined @click="store.scan()" />
    </div>

    <!-- RESULTS -->
    <template v-else-if="store.scanResult">

      <!-- Cluster healthy banner -->
      <div v-if="store.scanResult.cluster_is_healthy" class="result-banner result-banner--success">
        <i class="pi pi-check-circle" />
        <div>
          <strong>Cluster appears healthy</strong>
          <p>All nodes are reachable and SYNCED. Recovery is not required.</p>
        </div>
      </div>

      <!-- Split-brain banner -->
      <div v-else-if="store.scanResult.is_split_brain" class="result-banner result-banner--error">
        <i class="pi pi-exclamation-circle" />
        <div>
          <strong>Split-brain detected</strong>
          <p>Multiple Primary Components found. Manual intervention required — do not bootstrap automatically.</p>
        </div>
      </div>

      <!-- NODE TABLE -->
      <div class="scan-table-wrap">
        <DataTable
            :value="store.scanResult.nodes"
            dataKey="node_id"
            size="small"
            class="scan-table"
        >
          <Column field="node_name" header="Node" :sortable="true">
            <template #body="{ data }">
              <div class="cell-node">
                <span class="cell-node-name">{{ data.node_name }}</span>
                <span class="cell-node-host">{{ data.host }}</span>
              </div>
            </template>
          </Column>

          <Column header="SSH" style="width: 72px">
            <template #body="{ data }">
              <span class="ssh-badge" :class="data.reachable ? 'ssh-badge--ok' : 'ssh-badge--fail'">
                <i :class="data.reachable ? 'pi pi-check' : 'pi pi-times'" />
                {{ data.reachable ? 'OK' : 'FAIL' }}
              </span>
            </template>
          </Column>

          <Column header="seqno" style="width: 100px">
            <template #body="{ data }">
              <span v-if="!data.reachable" class="cell-muted">—</span>
              <span v-else-if="data.seqno === -1" class="cell-running">node running</span>
              <span v-else class="cell-mono">{{ data.seqno }}</span>
            </template>
          </Column>

          <Column header="safe_to_bootstrap" style="width: 150px">
            <template #body="{ data }">
              <span v-if="!data.reachable" class="cell-muted">—</span>
              <span
                v-else
                class="stb-badge"
                :class="data.safe_to_bootstrap === 1 ? 'stb-badge--yes' : 'stb-badge--no'"
              >
                {{ data.safe_to_bootstrap === 1 ? 'YES' : 'NO' }}
              </span>
            </template>
          </Column>

          <Column header="UUID" style="width: 160px">
            <template #body="{ data }">
              <span v-if="data.uuid" class="cell-uuid">{{ data.uuid.slice(0, 8) }}…</span>
              <span v-else class="cell-muted">—</span>
            </template>
          </Column>

          <Column header="Error">
            <template #body="{ data }">
              <span v-if="data.error" class="cell-error">{{ data.error }}</span>
              <span v-else class="cell-muted">—</span>
            </template>
          </Column>
        </DataTable>
      </div>

      <!-- ACTIONS -->
      <div class="step-actions">
        <Button label="Re-scan" icon="pi pi-refresh" outlined size="small" @click="store.scan()" />
        <Button
            label="Next: Select bootstrap node"
            icon="pi pi-arrow-right"
            iconPos="right"
            :disabled="store.scanResult.cluster_is_healthy || store.scanResult.is_split_brain || !hasReachableNodes"
            @click="emit('next')"
        />
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import { useRecoveryStore } from '@/stores/recovery'
import StatusBadge from '@/components/shared/StatusBadge.vue'

const emit = defineEmits<{ next: [] }>()
const store = useRecoveryStore()

const hasReachableNodes = computed(() =>
    (store.scanResult?.nodes ?? []).some((n) => n.reachable)
)
</script>

<style scoped>
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  height: 100%;
}

/* HEADER */
.step-header { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title  {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}
.step-desc   { font-size: var(--text-sm); color: var(--color-text-muted); line-height: 1.5; }
.inline-code {
  font-family: var(--font-mono);
  font-size: 0.85em;
  background: var(--color-surface-offset);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  color: var(--color-primary);
}

/* IDLE STATE */
.state-idle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-6);
  padding: var(--space-16) 0;
  flex: 1;
}
.state-idle-icon {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-offset);
  color: var(--color-text-faint);
  font-size: 1.8rem;
  border: 1px solid var(--color-border);
}
.state-idle-hint {
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

/* Bigger idle button */
.state-idle :deep(.idle-btn.p-button) {
  padding: var(--space-3) var(--space-8);
  font-size: var(--text-base);
  font-weight: 600;
}

/* SCANNING STATE */
.state-scanning {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-16) 0;
  flex: 1;
}
.state-scanning-hint { font-size: var(--text-sm); color: var(--color-text-muted); }

/* ERROR STATE */
.state-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-12) 0;
  flex: 1;
}
.state-error-icon {
  font-size: 2rem;
  color: var(--color-error);
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in oklch, var(--color-error) 12%, transparent);
  border-radius: var(--radius-full);
}
.state-error-msg { font-size: var(--text-sm); color: var(--color-error); text-align: center; max-width: 48ch; }

/* BANNERS */
.result-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  font-size: var(--text-sm);
  line-height: 1.5;
}
.result-banner i { font-size: 1.1rem; margin-top: 1px; flex-shrink: 0; }
.result-banner strong { display: block; font-weight: 600; margin-bottom: 2px; }
.result-banner p { margin: 0; color: var(--color-text-muted); font-size: var(--text-xs); }

.result-banner--success {
  background: color-mix(in oklch, var(--color-success) 10%, transparent);
  border-color: color-mix(in oklch, var(--color-success) 30%, transparent);
  color: var(--color-success);
}
.result-banner--error {
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  border-color: color-mix(in oklch, var(--color-error) 30%, transparent);
  color: var(--color-error);
}

/* TABLE */
.scan-table-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

/* CELL STYLES */
.cell-node { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name { font-size: var(--text-sm); font-weight: 600; color: var(--color-text); }
.cell-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-muted     { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-mono      { font-family: var(--font-mono); font-size: var(--text-sm); font-variant-numeric: tabular-nums; }
.cell-running   { font-size: var(--text-xs); color: var(--color-gold); font-style: italic; }
.cell-uuid      { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-error     { font-size: var(--text-xs); color: var(--color-error); }

/* SSH badge */
.ssh-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 2px 7px;
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

/* safe_to_bootstrap badge */
.stb-badge {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 2px 8px;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
  margin-top: auto;
}
</style>
