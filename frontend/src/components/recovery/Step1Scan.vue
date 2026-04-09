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
      <div class="scan-idle-icon">
        <i class="pi pi-search" style="font-size: 2rem; color: var(--color-text-faint)" />
      </div>
      <p class="text-sm text-muted-color mb-4">No scan performed yet.</p>
      <Button label="Start scan" icon="pi pi-play" @click="store.scan()" />
    </div>

    <!-- Scanning -->
    <div v-else-if="store.scanning" class="scan-progress">
      <ProgressSpinner style="width: 40px; height: 40px" />
      <p class="text-sm text-muted-color mt-3">Connecting to nodes via SSH…</p>
    </div>

    <!-- Error -->
    <div v-else-if="store.scanError" class="scan-error">
      <i class="pi pi-times-circle" style="color: var(--color-error)" />
      <p class="text-sm">{{ store.scanError }}</p>
      <Button label="Retry" icon="pi pi-refresh" size="small" outlined @click="store.scan()" />
    </div>

    <!-- Results table -->
    <template v-else-if="store.scanResult">
      <!-- Cluster healthy guard -->
      <Message v-if="store.scanResult.cluster_is_healthy" severity="success" class="mb-4">
        Cluster appears healthy — all nodes are reachable and SYNCED.
        Recovery is not required.
      </Message>

      <DataTable :value="store.scanResult.nodes" dataKey="node_id" size="small" class="mb-4">
        <Column field="node_name" header="Node" :sortable="true">
          <template #body="{ data }">
            <span class="font-medium">{{ data.node_name }}</span>
            <span class="text-xs text-muted-color ml-2">{{ data.host }}</span>
          </template>
        </Column>
        <Column header="SSH" style="width: 80px">
          <template #body="{ data }">
            <StatusBadge :status="data.reachable ? 'ok' : 'err'" />
          </template>
        </Column>
        <Column header="seqno" style="width: 90px">
          <template #body="{ data }">
            <span v-if="!data.reachable" class="text-muted-color">—</span>
            <span v-else-if="data.seqno === -1" class="text-warning-color text-xs">running?</span>
            <span v-else class="font-mono text-sm">{{ data.seqno }}</span>
          </template>
        </Column>
        <Column header="safe_to_bootstrap" style="width: 140px">
          <template #body="{ data }">
            <span v-if="!data.reachable" class="text-muted-color">—</span>
            <Tag
                v-else
                :value="data.safe_to_bootstrap === 1 ? 'YES' : 'NO'"
                :severity="data.safe_to_bootstrap === 1 ? 'success' : 'secondary'"
                class="text-xs"
            />
          </template>
        </Column>
        <Column header="uuid" style="width: 200px">
          <template #body="{ data }">
            <span v-if="data.uuid" class="font-mono text-xs text-muted-color">
              {{ data.uuid.slice(0, 8) }}…
            </span>
            <span v-else class="text-muted-color">—</span>
          </template>
        </Column>
        <Column header="Error">
          <template #body="{ data }">
            <span v-if="data.error" class="text-xs text-error-color">{{ data.error }}</span>
            <span v-else class="text-muted-color">—</span>
          </template>
        </Column>
      </DataTable>

      <div class="flex justify-between items-center">
        <Button label="Re-scan" icon="pi pi-refresh" outlined size="small" @click="store.scan()" />
        <Button
            label="Next: Select bootstrap node"
            icon="pi pi-arrow-right"
            icon-pos="right"
            :disabled="store.scanResult.cluster_is_healthy || !hasReachableNodes"
            @click="emit('next')"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button, DataTable, Column, Tag, Message, ProgressSpinner } from 'primevue'
import { useRecoveryStore } from '@/stores/recovery'
import StatusBadge from '@/components/shared/StatusBadge.vue'

const emit = defineEmits<{ next: [] }>()
const store = useRecoveryStore()

const hasReachableNodes = computed(() =>
    (store.scanResult?.nodes ?? []).some((n) => n.reachable)
)
</script>