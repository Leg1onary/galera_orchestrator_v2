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
      :close-on-escape="!store.operationRunning"
      :dismissable-mask="false"
      :style="{ width: '680px' }"
      @hide="store.closeWizard()"
  >
    <!-- Stepper -->
    <div class="wizard-steps">
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
    <RRStep1Config   v-if="store.wizardStep === 1" />
    <RRStep2Progress v-else-if="store.wizardStep === 2" />
    <RRStep3Done     v-else-if="store.wizardStep === 3" />
  </Dialog>
</template>

<script setup lang="ts">
import Dialog from 'primevue/dialog'
import { useMaintenanceStore } from '@/stores/maintenance'
import RRStep1Config   from './RRStep1Config.vue'
import RRStep2Progress from './RRStep2Progress.vue'
import RRStep3Done     from './RRStep3Done.vue'

const store = useMaintenanceStore()
const STEP_LABELS = ['Configure', 'Progress', 'Done']
</script>

<style scoped>
.wizard-steps {
  display: flex;
  padding-bottom: var(--space-5);
  margin-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.wizard-step-indicator {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  position: relative;
}

/* Connector line между шагами */
.wizard-step-indicator:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 13px;
  left: calc(50% + 16px);
  right: calc(-50% + 16px);
  height: 2px;
  background: var(--color-border);
  z-index: 0;
  transition: background var(--transition-interactive);
}
.wizard-step-indicator.step--completed:not(:last-child)::after {
  background: var(--color-primary);
}

/* Circle */
.step-circle {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: 700;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  position: relative;
  z-index: 1;
  transition:
      border-color  var(--transition-interactive),
      background    var(--transition-interactive),
      color         var(--transition-interactive);
}
.step--active .step-circle {
  border-color: var(--color-primary);
  color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--color-primary) 15%, transparent);
}
.step--completed .step-circle {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

/* Label */
.step-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  transition: color var(--transition-interactive);
}
.step--active .step-label {
  color: var(--color-primary);
  font-weight: 600;
}
.step--completed .step-label {
  color: var(--color-text-muted);
}
</style>
