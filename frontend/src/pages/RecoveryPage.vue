<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">Recovery Wizard</h1>
      <p class="page-subtitle">
        Use this wizard when all nodes are down and the cluster cannot start automatically.
      </p>
    </div>

    <!-- Guard: нет кластера -->
    <div v-if="!clusterStore.selectedClusterId" class="empty-state">
      <i class="pi pi-server empty-state-icon" />
      <p>No cluster selected.</p>
    </div>

    <!-- Wizard -->
    <div v-else class="wizard-container">
      <!-- Stepper header -->
      <div class="wizard-steps">
        <div
            v-for="(label, idx) in STEP_LABELS"
            :key="idx"
            class="wizard-step-indicator"
            :class="{
            'step--active':    store.step === idx + 1,
            'step--completed': store.step > idx + 1,
            'step--pending':   store.step < idx + 1,
          }"
        >
          <div class="step-circle">
            <i v-if="store.step > idx + 1" class="pi pi-check" />
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <span class="step-label">{{ label }}</span>
        </div>
      </div>

      <!-- Step panels -->
      <div class="wizard-body">
        <Step1Scan v-if="store.step === 1" @next="store.step = 2" />
        <Step2Bootstrap
            v-else-if="store.step === 2"
            @back="store.step = 1"
        />
        <Step3Rejoin v-else-if="store.step === 3" />
        <Step4Done
            v-else-if="store.step === 4"
            @go-overview="router.push('/overview')"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'
import { useRecoveryStore } from '@/stores/recovery'
import Step1Scan from '@/components/recovery/Step1Scan.vue'
import Step2Bootstrap from '@/components/recovery/Step2Bootstrap.vue'
import Step3Rejoin from '@/components/recovery/Step3Rejoin.vue'
import Step4Done from '@/components/recovery/Step4Done.vue'

const router = useRouter()
const clusterStore = useClusterStore()
const store = useRecoveryStore()

const STEP_LABELS = ['Scan nodes', 'Select bootstrap node', 'Rejoin', 'Done']

// Если кластер healthy — блокируем вход в wizard
// Читаем из clusterStore.statusSummary (уже загружен Overview/polling)
const clusterIsHealthy = computed(() =>
    clusterStore.statusSummary?.cluster_status === 'healthy'
)

onMounted(() => {
  if (clusterStore.selectedClusterId) {
    store.init(clusterStore.selectedClusterId)
  }
})

onUnmounted(() => {
  store.destroy()
})
</script>

<style scoped>
.wizard-container {
  max-width: 720px;
  margin: 0 auto;
}
.wizard-steps {
  display: flex;
  gap: 0;
  margin-bottom: var(--space-8);
}
.wizard-step-indicator {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  position: relative;
}
/* Connector line between steps */
.wizard-step-indicator:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 16px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--color-border);
  z-index: 0;
}
.wizard-step-indicator.step--completed:not(:last-child)::after {
  background: var(--color-primary);
}
.step-circle {
  width: 32px; height: 32px;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-sm); font-weight: 600;
  position: relative; z-index: 1;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  transition: border-color var(--transition-interactive), background var(--transition-interactive);
}
.step--active .step-circle {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.step--completed .step-circle {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}
.step-label { font-size: var(--text-xs); color: var(--color-text-muted); text-align: center; }
.step--active .step-label { color: var(--color-primary); font-weight: 500; }

.wizard-body {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
}
.healthy-guard {
  display: flex; gap: var(--space-4); align-items: flex-start;
  padding: var(--space-5) var(--space-6);
  background: color-mix(in oklch, var(--color-success) 8%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-success) 25%, transparent);
  border-radius: var(--radius-lg);
  max-width: 560px;
}
/* Shared wizard step styles (injected globally or duplicated per step) */
:deep(.wizard-step) { display: flex; flex-direction: column; gap: var(--space-4); }
:deep(.step-header) { display: flex; flex-direction: column; gap: var(--space-1); padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-divider); }
:deep(.step-title) { font-size: var(--text-lg); font-weight: 600; }
:deep(.step-desc) { font-size: var(--text-sm); color: var(--color-text-muted); }
</style>