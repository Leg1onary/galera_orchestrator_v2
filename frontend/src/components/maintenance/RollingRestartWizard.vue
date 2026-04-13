<!--
  Wizard wrapper — Dialog + stepper header + step router.
  Открывается через store.openWizard(), закрывается через store.closeWizard().
-->
<template>
  <Dialog
      v-model:visible="store.wizardOpen"
      header="Rolling Restart Wizard"
      modal
      :closable="isClosable"
      :close-on-escape="isClosable"
      :dismissable-mask="false"
      :style="{ width: '700px' }"
      :pt="{
        root: { style: 'max-width: calc(100vw - 2rem)' },
        content: { style: 'padding: 1.75rem 2rem 2rem' },
        header: { style: 'padding: 1.25rem 2rem' },
      }"
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

    <!-- Step content with transition -->
    <Transition name="rr-step" mode="out-in">
      <RRStep1Config   v-if="store.wizardStep === 1" key="1" />
      <RRStep2Progress v-else-if="store.wizardStep === 2" key="2" />
      <RRStep3Done     v-else-if="store.wizardStep === 3" key="3" />
    </Transition>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Dialog from 'primevue/dialog'
import { useMaintenanceStore } from '@/stores/maintenance'
import RRStep1Config   from './RRStep1Config.vue'
import RRStep2Progress from './RRStep2Progress.vue'
import RRStep3Done     from './RRStep3Done.vue'

const store = useMaintenanceStore()
const STEP_LABELS = ['Configure', 'Progress', 'Done']

// Fix: avoid race where operationRunning is still true for one tick
// when operation_finished arrives and wizardStep flips to 3.
// Allow closing on step 1 (not started) and step 3 (finished/failed/cancelled).
// Block closing only while step 2 is active (operation in flight).
const isClosable = computed(() =>
  store.wizardStep === 1 || store.wizardStep === 3
)
</script>

<style scoped>
.wizard-steps {
  display: flex;
  padding-bottom: var(--space-6);
  margin-bottom: var(--space-6);
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

/* Connector line */
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
      color         var(--transition-interactive),
      box-shadow    var(--transition-interactive);
}
.step--active .step-circle {
  border-color: var(--color-primary);
  color: var(--color-primary);
  box-shadow: 0 0 0 4px color-mix(in oklch, var(--color-primary) 15%, transparent);
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

/* Step transition */
.rr-step-enter-active,
.rr-step-leave-active  { transition: opacity 220ms ease, transform 220ms ease; }
.rr-step-enter-from    { opacity: 0; transform: translateX(10px); }
.rr-step-leave-to      { opacity: 0; transform: translateX(-10px); }
</style>
