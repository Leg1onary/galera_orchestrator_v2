<template>
  <div class="wizard-step">
    <div class="step-header">
      <h2 class="step-title">Step 1 — Scan nodes</h2>
      <p class="step-desc">
        The orchestrator will connect to each node via SSH and read
        <code>grastate.dat</code> to determine which node is safe to bootstrap.
      </p>
    </div>

    <!-- Before scan -->
    <div v-if="!store.scanResult && !store.scanning" class="scan-idle">
      <i class="pi pi-search scan-idle-icon" />
      <p class="scan-hint">No scan performed yet.</p>
      <Button label="Start scan" icon="pi pi-play" @click="store.scan()" />
    </div>

    <!-- Scanning -->
    <div v-else-if="store.scanning" class="scan-progress">
      <ProgressSpinner style="width: 40px; height: 40px" />
      <p class="scan-hint">Connecting to nodes via SSH…</p>
    </div>

    <!-- SSH/scan error -->
    <div v-else-if="store.scanError" class="scan-error">
      <i class="pi pi-times-circle" style="color: var(--color-error)" />
      <p class="scan-error-msg">{{ store.scanError }}</p>
      <Button label="Retry" icon="pi pi-refresh" size="small" outlined @click="store.scan()" />
    </div>

    <!-- Results -->
    <template v-else-if="store.scanResult">

      <!-- Cluster healthy -->
      <Message
          v-if="store.scanResult.cluster_is_healthy"
          severity="success"
          class="mb-4"
      >
        Cluster appears healthy — all nodes are reachable and SYNCED.
        Recovery is not required.
      </Message>

      <!-- MAJOR fix: split-brain warning по ТЗ п.13.7 -->
      <Message
          v-else-if="store.scanResult.is_split_brain"
          severity="error"
          class="mb-4"
      >
        Split-brain detected: multiple Primary Components found.
        Manual intervention required — do not bootstrap automatically.
      </Message>

      <DataTable
          :value="store.scanResult.nodes"
          dataKey="node_id"
          size="small"
          style="margin-bottom: var(--space-4)"
      >
        <Column field="node_name" header="Node" :sortable="true">
          <template #body="{ data }">
            <span style="font-weight: 500">{{ data.node_name }}</span>
            <span style="font-size: var(--text-xs); color: var(--color-text-muted); margin-left: var(--space-2)">
              {{ data.host }}
            </span>
          </template>
        </Column>

        <Column header="SSH" style="width: 80px">
          <template #body="{ data }">
            <StatusBadge :status="data.reachable ? 'ok' : 'err'" />
          </template>
        </Column>

        <Column header="seqno" style="width: 90px">
          <template #body="{ data }">
            <span v-if="!data.reachable" style="color: var(--color-text-muted)">—</span>
            <!-- MINOR fix: seqno -1 = MariaDB is running, grastate не читается -->
            <span
                v-else-if="data.seqno === -1"
                style="color: var(--color-gold); font-size: var(--text-xs)"
            >node running</span>
            <span v-else style="font-family: monospace; font-size: var(--text-sm)">
              {{ data.seqno }}
            </span>
          </template>
        </Column>

        <Column header="safe_to_bootstrap" style="width: 140px">
          <template #body="{ data }">
            <span v-if="!data.reachable" style="color: var(--color-text-muted)">—</span>
            <Tag
                v-else
                :value="data.safe_to_bootstrap === 1 ? 'YES' : 'NO'"
                :severity="data.safe_to_bootstrap === 1 ? 'success' : 'secondary'"
                style="font-size: var(--text-xs)"
            />
          </template>
        </Column>

        <Column header="uuid" style="width: 200px">
          <template #body="{ data }">
            <span
                v-if="data.uuid"
                style="font-family: monospace; font-size: var(--text-xs); color: var(--color-text-muted)"
            >{{ data.uuid.slice(0, 8) }}…</span>
            <span v-else style="color: var(--color-text-muted)">—</span>
          </template>
        </Column>

        <Column header="Error">
          <template #body="{ data }">
            <span
                v-if="data.error"
                style="font-size: var(--text-xs); color: var(--color-error)"
            >{{ data.error }}</span>
            <span v-else style="color: var(--color-text-muted)">—</span>
          </template>
        </Column>
      </DataTable>

      <div class="step-actions">
        <Button
            label="Re-scan"
            icon="pi pi-refresh"
            outlined
            size="small"
            @click="store.scan()"
        />
        <Button
            label="Next: Select bootstrap node"
            icon="pi pi-arrow-right"
            iconPos="right"
            :disabled="store.scanResult.cluster_is_healthy
            || store.scanResult.is_split_brain
            || !hasReachableNodes"
            @click="emit('next')"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
// BLOCKER fix: раздельные импорты PrimeVue
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
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
  gap: var(--space-4);
}
.step-header { display: flex; flex-direction: column; gap: var(--space-2); }
.step-title  { font-size: var(--text-lg); font-weight: 600; }
.step-desc   { font-size: var(--text-sm); color: var(--color-text-muted); }

.scan-idle,
.scan-progress,
.scan-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-8) 0;
  color: var(--color-text-muted);
}
.scan-idle-icon { font-size: 2rem; color: var(--color-text-faint); }
.scan-hint      { font-size: var(--text-sm); }
.scan-error-msg { font-size: var(--text-sm); color: var(--color-error); }

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>