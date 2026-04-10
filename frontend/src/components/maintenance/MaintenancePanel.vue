<template>
  <div class="maintenance-panel">
    <NodeMaintenanceTable />
    <RollingRestartWizard />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeMaintenanceTable from './NodeMaintenanceTable.vue'
import RollingRestartWizard from './RollingRestartWizard.vue'

const props = defineProps<{ clusterId: number }>()
const store = useMaintenanceStore()

onMounted(() => store.loadNodes())
watch(() => props.clusterId, () => store.loadNodes())
</script>

<style scoped>
.maintenance-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
</style>
