<script setup lang="ts">
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import MaintenancePanel from '@/components/maintenance/MaintenancePanel.vue'

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)
</script>

<template>
  <div class="maintenance-page anim-fade-in">

    <div class="pg-head">
      <div class="section-title">Maintenance</div>
      <p class="pg-desc">Schedule and manage rolling maintenance operations across cluster nodes.</p>
    </div>

    <div v-if="!clusterId" class="pg-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <MaintenancePanel v-else :cluster-id="clusterId" />
  </div>
</template>

<style scoped>
.maintenance-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.pg-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.pg-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.pg-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-12);
  justify-content: center;
  font-size: var(--text-sm);
}
</style>
