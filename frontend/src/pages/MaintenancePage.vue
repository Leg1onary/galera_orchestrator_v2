<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">Maintenance</h1>
      <p class="page-subtitle">
        Manage per-node maintenance mode and perform rolling restarts.
      </p>
    </div>

    <div v-if="!clusterStore.selectedClusterId" class="empty-state">
      <i class="pi pi-server empty-state-icon" />
      <p>No cluster selected.</p>
    </div>

    <template v-else>
      <!-- Node maintenance table -->
      <NodeMaintenanceTable />

      <!-- Rolling restart wizard (Dialog) -->
      <RollingRestartWizard />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeMaintenanceTable from '@/components/maintenance/NodeMaintenanceTable.vue'
import RollingRestartWizard from '@/components/maintenance/RollingRestartWizard.vue'

const clusterStore = useClusterStore()
const store = useMaintenanceStore()

onMounted(() => {
  if (clusterStore.selectedClusterId) {
    store.init(clusterStore.selectedClusterId)
  }
})

onUnmounted(() => {
  store.destroy()
})
</script>