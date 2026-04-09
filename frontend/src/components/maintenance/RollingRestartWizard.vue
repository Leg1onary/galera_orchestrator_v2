<!--
  Wizard wrapper — Dialog + stepper header + step router.
  Открывается через store.openWizard(), закрывается через store.closeWizard().
-->
<template>
  <Dialog
      v-model:visible="store.wizardOpen"
      header="Rolling Restart Wizard"
      modal
      :closable="!store.operationRunning"
      :style="{ width: '680px' }"
      @hide="store.closeWizard()"
  >
    <!-- Stepper -->
    <div class="wizard-steps mb-5">
      <div
          v-for="(label, idx) in STEP_LABELS"
          :key="idx"
          class="wizard-step-indicator"
          :class="{
          'step--active':    store.wizardStep === idx + 1,
          'step--completed': store.wizardStep > idx + 1,
          'step--pending':   store.wizardStep < idx + 1,
        }"
      >
        <div class="step-circle">
          <i v-if="store.wizardStep > idx + 1" class="pi pi-check" />
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <span class="step-label">{{ label }}</span>
      </div>
    </div>

    <!-- Step content -->
    <RRStep1Config  v-if="store.wizardStep === 1" />
    <RRStep2Progress v-else-if="store.wizardStep === 2" />
    <RRStep3Done    v-else-if="store.wizardStep === 3" />
  </Dialog>
</template>

<script setup lang="ts">
import { Dialog } from 'primevue'
import { useMaintenanceStore } from '@/stores/maintenance'
import RRStep1Config from './RRStep1Config.vue'
import RRStep2Progress from './RRStep2Progress.vue'
import RRStep3Done from './RRStep3Done.vue'

const store = useMaintenanceStore()

const STEP_LABELS = ['Configure', 'Progress', 'Done']
</script>

<style scoped>
.wizard-steps {
  display: flex; gap: 0;
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-divider);
}
.wizard-step-indicator {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  gap: var(--space-1); position: relative;
}
.wizard-step-indicator:not(:last-child)::after {
  content: ''; position: absolute; top: 14px; left: 50%;
  width: 100%; height: 2px; background: var(--color-border); z-index: 0;
}
.wizard-step-indicator.step--completed:not(:last-child)::after {
  background: var(--color-primary);
}
.step-circle {
  width: 28px; height: 28px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-xs); font-weight: 600;
  border: 2px solid var(--color-border);
  background: var(--color-surface); color: var(--color-text-muted);
  position: relative; z-index: 1;
  transition: border-color var(--transition-interactive), background var(--transition-interactive);
}
.step--active .step-circle    { border-color: var(--color-primary); color: var(--color-primary); }
.step--completed .step-circle { border-color: var(--color-primary); background: var(--color-primary); color: #fff; }
.step-label { font-size: var(--text-xs); color: var(--color-text-muted); text-align: center; }
.step--active .step-label { color: var(--color-primary); font-weight: 500; }
</style>