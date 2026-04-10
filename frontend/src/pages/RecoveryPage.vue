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

const STEP_LABELS = ['Scan nodes', 'Select bootstrap node', 'Rejoin', 'Done']

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
    <div v-else-if="clusterIsHealthy" class="guard-banner">
      <i class="pi pi-check-circle guard-icon guard-icon--ok" />
      <div>
        <div class="guard-title">Cluster is healthy</div>
        <div class="guard-sub">Recovery wizard is only available when the cluster cannot start automatically.</div>
      </div>
    </div>

    <!-- Wizard -->
    <div v-else class="wizard">
      <!-- Steps header -->
      <div class="wizard-steps" role="list">
        <div
          v-for="(label, idx) in STEP_LABELS"
          :key="idx"
          class="ws-item"
          :class="{
            'ws-item--active':    store.step === idx + 1,
            'ws-item--done':      store.step >  idx + 1,
            'ws-item--pending':   store.step <  idx + 1,
          }"
          role="listitem"
        >
          <div class="ws-circle">
            <i v-if="store.step > idx + 1" class="pi pi-check" />
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <span class="ws-label">{{ label }}</span>
          <div v-if="idx < STEP_LABELS.length - 1" class="ws-line" />
        </div>
      </div>

      <!-- Step content -->
      <div class="wizard-body">
        <Step1Scan       v-if="store.step === 1" @next="store.goNext()" />
        <Step2Bootstrap  v-else-if="store.step === 2" @back="store.goBack()" @next="store.goNext()" />
        <Step3Rejoin     v-else-if="store.step === 3" @back="store.goBack()" @next="store.goNext()" />
        <Step4Done       v-else-if="store.step === 4" @go-overview="router.push({ name: 'overview' })" />
      </div>
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

/* Guard banner */
.guard-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
}

.guard-icon { font-size: 1.25rem; margin-top: 2px; }
.guard-icon--ok { color: var(--color-success); }

.guard-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
}

.guard-sub {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

/* Wizard */
.wizard {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

/* Steps header */
.wizard-steps {
  display: flex;
  align-items: center;
}

.ws-item {
  display: flex;
  align-items: center;
  flex: 1;
  position: relative;
}

.ws-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: 700;
  flex-shrink: 0;
  border: 1.5px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  transition: all var(--transition-normal);
  z-index: 1;
}

.ws-item--active  .ws-circle { border-color: var(--color-primary); color: var(--color-primary); background: var(--color-primary-dim); }
.ws-item--done    .ws-circle { border-color: var(--color-synced);  color: var(--color-synced);  background: var(--color-synced-dim); }

.ws-label {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-muted);
  margin-left: var(--space-2);
  white-space: nowrap;
}

.ws-item--active .ws-label { color: var(--color-text); }
.ws-item--done   .ws-label { color: var(--color-text-muted); }

.ws-line {
  flex: 1;
  height: 1px;
  background: var(--color-border-muted);
  margin: 0 var(--space-2);
}

/* Wizard body */
.wizard-body {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
}
</style>
