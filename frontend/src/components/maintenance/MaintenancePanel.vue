<template>
  <div class="maintenance-panel">
    <NodeMaintenanceTable />
    <RollingRestartWizard />
  </div>
</template>

<script setup lang="ts">
import { onUnmounted, watch } from 'vue'
import { useMaintenanceStore } from '@/stores/maintenance'
import NodeMaintenanceTable from './NodeMaintenanceTable.vue'
import RollingRestartWizard from './RollingRestartWizard.vue'

const props = defineProps<{ clusterId: number }>()
const store = useMaintenanceStore()

// Single source of init — watch with immediate:true replaces onMounted + watch combo
// to avoid double store.init() call on first render
watch(
  () => props.clusterId,
  (id) => store.init(id),
  { immediate: true }
)
onUnmounted(() => store.destroy())
</script>

<style scoped>
.maintenance-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
</style>
