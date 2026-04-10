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

const STEPS = [
  { value: 1, label: 'Scan nodes',  icon: 'pi pi-search',  desc: 'Read grastate.dat via SSH' },
  { value: 2, label: 'Bootstrap',   icon: 'pi pi-bolt',    desc: 'Start the bootstrap node' },
  { value: 3, label: 'Rejoin',      icon: 'pi pi-sync',    desc: 'Bring remaining nodes back' },
  { value: 4, label: 'Done',        icon: 'pi pi-check',   desc: 'Cluster restored' },
]

watch(() => clusterStore.selectedClusterId, (id) => { if (id) store.init(id) })
onMounted(() => { if (clusterStore.selectedClusterId) store.init(clusterStore.selectedClusterId) })
onUnmounted(() => store.destroy())
</script>

<template>
  <div class="recovery-page anim-fade-in">

    <!-- PAGE HEAD -->
    <div class="rp-head">
      <div class="section-title">Recovery Wizard</div>
      <p class="rp-desc">Use this wizard when all nodes are down and the cluster cannot start automatically.</p>
    </div>

    <!-- Guard: no cluster -->
    <div v-if="!clusterStore.selectedClusterId" class="rp-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <!-- Guard: healthy -->
    <Message v-else-if="clusterIsHealthy" severity="success" :closable="false" class="rp-guard-msg">
      <div class="rp-guard-body">
        <strong>Cluster is healthy</strong>
        <span>Recovery wizard is only available when the cluster cannot start automatically.</span>
      </div>
    </Message>

    <!-- WIZARD two-column layout -->
    <div v-else class="rp-wizard">

      <!-- LEFT: vertical step sidebar -->
      <aside class="rp-sidebar">
        <div
          v-for="s in STEPS"
          :key="s.value"
          class="rp-step-item"
          :class="{
            'rp-step--active':    store.step === s.value,
            'rp-step--done':      store.step > s.value,
            'rp-step--upcoming':  store.step < s.value,
          }"
        >
          <div class="rp-step-indicator">
            <span v-if="store.step > s.value" class="rp-step-check">
              <i class="pi pi-check" />
            </span>
            <span v-else class="rp-step-num">{{ s.value }}</span>
          </div>
          <div class="rp-step-connector" v-if="s.value < STEPS.length" />
          <div class="rp-step-meta">
            <span class="rp-step-label">{{ s.label }}</span>
            <span class="rp-step-subdesc">{{ s.desc }}</span>
          </div>
        </div>
      </aside>

      <!-- RIGHT: step content -->
      <main class="rp-content">
        <Transition name="step" mode="out-in">
          <Step1Scan    v-if="store.step === 1" key="1" @next="store.goNext()" />
          <Step2Bootstrap v-else-if="store.step === 2" key="2" @back="store.goBack()" @next="store.goNext()" />
          <Step3Rejoin  v-else-if="store.step === 3" key="3" @back="store.goBack()" @next="store.goNext()" />
          <Step4Done    v-else-if="store.step === 4" key="4" @go-overview="router.push({ name: 'overview' })" />
        </Transition>
      </main>

    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════
   PAGE ROOT — full width
═══════════════════════════════════════ */
.recovery-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  /* no max-width — занимаем всё доступное пространство */
  width: 100%;
  height: 100%;
}

.rp-head { display: flex; flex-direction: column; gap: var(--space-1); }
.rp-desc { font-size: var(--text-sm); color: var(--color-text-muted); }

.rp-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-16);
  font-size: var(--text-sm);
}

.rp-guard-msg { width: 100%; }
.rp-guard-body { display: flex; flex-direction: column; gap: var(--space-1); font-size: var(--text-sm); }

/* ═══════════════════════════════════════
   TWO-COLUMN WIZARD
═══════════════════════════════════════ */
.rp-wizard {
  display: grid;
  /* sidebar фиксированная ширина, контент растягивается */
  grid-template-columns: 220px 1fr;
  gap: var(--space-6);
  flex: 1;
  min-height: 0;
}

/* ═══════════════════════════════════════
   LEFT SIDEBAR — vertical stepper
═══════════════════════════════════════ */
.rp-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  align-self: start;
  /* прилипает к верху при скролле контента */
  position: sticky;
  top: var(--space-4);
}

.rp-step-item {
  display: grid;
  /* indicator | connector | meta */
  grid-template-areas:
    "ind  meta"
    "conn meta";
  grid-template-columns: 28px 1fr;
  grid-template-rows: auto 1fr;
  column-gap: var(--space-3);
  padding: 0;
}

/* Коннектор — вертикальная линия между шагами */
.rp-step-connector {
  grid-area: conn;
  width: 2px;
  min-height: var(--space-6);
  background: var(--color-border);
  margin: 4px auto 4px;
  border-radius: 1px;
  transition: background 300ms ease;
}
.rp-step--done .rp-step-connector {
  background: var(--color-primary);
}

/* Indicator circle */
.rp-step-indicator {
  grid-area: ind;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
  transition: background 200ms ease, border-color 200ms ease, color 200ms ease;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-faint);
}

.rp-step--active .rp-step-indicator {
  border-color: var(--color-primary);
  background: color-mix(in oklch, var(--color-primary) 15%, transparent);
  color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--color-primary) 20%, transparent);
}

.rp-step--done .rp-step-indicator {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.rp-step-check { display: flex; align-items: center; justify-content: center; }
.rp-step-check .pi { font-size: 0.7rem; }

/* Meta */
.rp-step-meta {
  grid-area: meta;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: var(--space-6);
  padding-top: 4px;
}

.rp-step-item:last-child .rp-step-meta {
  padding-bottom: 0;
}

.rp-step-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  transition: color 200ms ease;
  line-height: 1.2;
}
.rp-step--active .rp-step-label  { color: var(--color-text); }
.rp-step--done   .rp-step-label  { color: var(--color-primary); }

.rp-step-subdesc {
  font-size: 0.68rem;
  color: var(--color-text-faint);
  line-height: 1.3;
}
.rp-step--active .rp-step-subdesc { color: var(--color-text-muted); }

/* ═══════════════════════════════════════
   RIGHT CONTENT PANEL
═══════════════════════════════════════ */
.rp-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-8);
  min-height: 400px;
  overflow: auto;
}

/* ═══════════════════════════════════════
   STEP TRANSITION
═══════════════════════════════════════ */
.step-enter-active,
.step-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.step-enter-from {
  opacity: 0;
  transform: translateX(12px);
}
.step-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}
</style>
