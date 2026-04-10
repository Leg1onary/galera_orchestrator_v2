<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'
import { useRecoveryStore } from '@/stores/recovery'
import Step1Scan from '@/components/recovery/Step1Scan.vue'
import Step2Bootstrap from '@/components/recovery/Step2Bootstrap.vue'
import Step3Rejoin from '@/components/recovery/Step3Rejoin.vue'
import Step4Done from '@/components/recovery/Step4Done.vue'

const router       = useRouter()
const clusterStore = useClusterStore()
const store        = useRecoveryStore()
const queryClient  = useQueryClient()

const clusterStatus = computed(() => {
  if (!clusterStore.selectedClusterId) return null
  return queryClient.getQueryData<{ cluster_status: string }>(
    ['cluster', clusterStore.selectedClusterId, 'status']
  )
})

const clusterIsHealthy = computed(
  () => clusterStatus.value?.cluster_status === 'healthy'
)

watch(() => clusterStore.selectedClusterId, (id) => { if (id) store.init(id) })
onMounted(() => { if (clusterStore.selectedClusterId) store.init(clusterStore.selectedClusterId) })
onUnmounted(() => store.destroy())
</script>

<template>
  <div class="recovery-page anim-fade-in">
    <div class="pg-head">
      <div class="section-title">Recovery Wizard</div>
      <p class="pg-desc">Use this wizard when all nodes are down and the cluster cannot start automatically.</p>
    </div>

    <!-- Guard: no cluster -->
    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <!-- Guard: healthy -->
    <Message v-else-if="clusterIsHealthy" severity="success" :closable="false" class="guard-msg">
      <div class="guard-body">
        <strong>Cluster is healthy</strong>
        <span>Recovery wizard is only available when the cluster cannot start automatically.</span>
      </div>
    </Message>

    <!-- Wizard -->
    <div v-else class="wizard">

      <!-- PrimeVue Stepper (linear) -->
      <Stepper :value="store.step" linear class="recovery-stepper">
        <StepList>
          <Step :value="1">Scan nodes</Step>
          <Step :value="2">Bootstrap</Step>
          <Step :value="3">Rejoin</Step>
          <Step :value="4">Done</Step>
        </StepList>

        <StepPanels>
          <StepPanel :value="1">
            <Step1Scan @next="store.goNext()" />
          </StepPanel>
          <StepPanel :value="2">
            <Step2Bootstrap @back="store.goBack()" @next="store.goNext()" />
          </StepPanel>
          <StepPanel :value="3">
            <Step3Rejoin @back="store.goBack()" @next="store.goNext()" />
          </StepPanel>
          <StepPanel :value="4">
            <Step4Done @go-overview="router.push({ name: 'overview' })" />
          </StepPanel>
        </StepPanels>
      </Stepper>

    </div>
  </div>
</template>

<style scoped>
.recovery-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  max-width: 760px;
}

.pg-head { display: flex; flex-direction: column; gap: var(--space-2); }
.pg-desc { font-size: var(--text-sm); color: var(--color-text-muted); }

.pg-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-12);
  justify-content: center;
  font-size: var(--text-sm);
}

.guard-msg { width: 100%; }
.guard-body { display: flex; flex-direction: column; gap: var(--space-1); font-size: var(--text-sm); }

.wizard { display: flex; flex-direction: column; gap: var(--space-4); }

.recovery-stepper :deep(.p-steppanels) {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-top: var(--space-4);
}
</style>
