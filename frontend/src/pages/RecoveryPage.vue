<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'
import { useRecoveryStore } from '@/stores/recovery'
import { ref } from 'vue'
import Step1Scan           from '@/components/recovery/Step1Scan.vue'
import Step2Bootstrap      from '@/components/recovery/Step2Bootstrap.vue'
import Step3Rejoin         from '@/components/recovery/Step3Rejoin.vue'
import Step4Done           from '@/components/recovery/Step4Done.vue'
import GrastateInspectorPanel from '@/components/recovery/GrastateInspectorPanel.vue'
import SnapshotPanel          from '@/components/recovery/SnapshotPanel.vue'
import IstSstHelper           from '@/components/recovery/IstSstHelper.vue'
import SplitBrainWizard       from '@/components/recovery/SplitBrainWizard.vue'
import FullClusterRecovery    from '@/components/recovery/FullClusterRecovery.vue'
import type { ClusterStatusResponse } from '@/composables/useClusterStatus'

const router       = useRouter()
const clusterStore = useClusterStore()
const store        = useRecoveryStore()
const queryClient  = useQueryClient()

const clusterStatus = computed(() => {
  if (!clusterStore.selectedClusterId) return null
  return queryClient.getQueryData<ClusterStatusResponse>(
    ['cluster', clusterStore.selectedClusterId, 'status']
  )
})

const clusterIsHealthy = computed(() => {
  if (clusterStatus.value === undefined || clusterStatus.value === null) return false
  return clusterStatus.value.status === 'healthy'
})

const statusReady = computed(() =>
  clusterStatus.value !== undefined && clusterStatus.value !== null
)

const STEPS = [
  { value: 1, label: 'Scan nodes',  icon: 'pi pi-search',  desc: 'Read cluster status via SSH' },
  { value: 2, label: 'Bootstrap',   icon: 'pi pi-bolt',    desc: 'Start the bootstrap node' },
  { value: 3, label: 'Rejoin',      icon: 'pi pi-sync',    desc: 'Bring remaining nodes back' },
  { value: 4, label: 'Done',        icon: 'pi pi-check',   desc: 'Cluster restored' },
]

watch(() => clusterStore.selectedClusterId, (id) => { if (id) store.init(id) })
onMounted(() => { if (clusterStore.selectedClusterId) store.init(clusterStore.selectedClusterId) })
onUnmounted(() => store.destroy())

/* ─ Recovery Tools tabs ─ */
const TOOL_TABS = [
  { value: 'grastate',    label: 'grastate.dat',        icon: 'pi-file-edit'   },
  { value: 'snapshot',    label: 'Node Snapshot',       icon: 'pi-camera'      },
  { value: 'ist-sst',     label: 'IST vs SST Helper',   icon: 'pi-directions'  },
  { value: 'split-brain', label: 'Split-Brain Wizard',  icon: 'pi-sitemap'     },
  { value: 'full-cluster',label: 'Full Cluster Recovery', icon: 'pi-refresh'   },
] as const
type ToolTab = typeof TOOL_TABS[number]['value']
const activeTool = ref<ToolTab>('grastate')
</script>

<template>
  <div class="recovery-page anim-fade-in">

    <!-- PAGE HEAD -->
    <div class="rp-head">
      <div class="pg-head-icon"><i class="pi pi-replay" /></div>
      <div>
        <h1 class="pg-title">Recovery</h1>
        <p class="rp-desc">Step-by-step wizard to restore a Galera cluster when all nodes are down.</p>
      </div>
    </div>

    <!-- Info banner -->
    <div class="info-banner">
      <div class="info-card">
        <div class="info-card-header">
          <i class="pi pi-database" />
          <span>What is Recovery?</span>
        </div>
        <p>
          Recovery is used when the <strong>entire cluster is down</strong> and cannot
          restart automatically. This happens after simultaneous crashes, power loss,
          or a split-brain scenario that left all nodes in a non-primary state.
        </p>
      </div>

      <div class="info-card">
        <div class="info-card-header">
          <i class="pi pi-list-check" />
          <span>How the wizard works</span>
        </div>
        <p>
          <strong>Step 1</strong> scans all nodes via SSH and reads
          <code>grastate.dat</code> to find the node with the highest
          <code>seqno</code>. <strong>Step 2</strong> bootstraps that node
          as a new primary component. <strong>Step 3</strong> rejoins the
          remaining nodes one by one.
        </p>
      </div>

      <div class="info-card">
        <div class="info-card-header">
          <i class="pi pi-exclamation-triangle" />
          <span>Safety notes</span>
        </div>
        <p>
          Never bootstrap a node with <code>safe_to_bootstrap: 0</code> unless
          you are certain it has the most recent data — this risks
          <strong>data loss</strong>. If the wizard is interrupted after
          bootstrap, rejoin the remaining nodes manually via
          <em>systemctl start mariadb</em>.
        </p>
      </div>
    </div>

    <!-- Guard: no cluster -->
    <div v-if="!clusterStore.selectedClusterId" class="rp-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <div v-else-if="!statusReady" class="rp-loading">
      <i class="pi pi-spin pi-spinner" /><span>Loading cluster status…</span>
    </div>

    <Message v-else-if="clusterIsHealthy" severity="success" :closable="false" class="rp-guard-msg">
      <div class="rp-guard-body">
        <strong>Cluster is healthy</strong>
        <span>Recovery wizard is only available when the cluster cannot start automatically.</span>
      </div>
    </Message>

    <!-- WIZARD -->
    <div v-else class="rp-wizard">

      <!-- LEFT: vertical step sidebar -->
      <aside class="rp-sidebar">
        <div
          v-for="s in STEPS"
          :key="s.value"
          class="rp-step-item"
          :class="{
            'rp-step--active':   store.step === s.value,
            'rp-step--done':     store.step > s.value,
            'rp-step--upcoming': store.step < s.value,
          }"
        >
          <div class="rp-step-indicator">
            <span v-if="store.step > s.value" class="rp-step-check"><i class="pi pi-check" /></span>
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
          <Step1Scan      v-if="store.step === 1"      key="1" @next="store.goNext()" />
          <Step2Bootstrap v-else-if="store.step === 2" key="2" @back="store.goBack()" @next="store.goNext()" />
          <Step3Rejoin    v-else-if="store.step === 3" key="3" @next="store.goNext()" />
          <Step4Done      v-else-if="store.step === 4" key="4" @go-overview="router.push({ name: 'overview' })" />
        </Transition>
      </main>
    </div>

    <!-- ════ RECOVERY TOOLS ════════════════════════════════════════ -->
    <div v-if="clusterStore.selectedClusterId" class="rt-section">

      <!-- Section header -->
      <div class="rt-head">
        <div class="rt-head-icon"><i class="pi pi-wrench" /></div>
        <div>
          <h2 class="rt-title">Recovery Tools</h2>
          <p class="rt-desc">Diagnostic and recovery utilities — use independently of the wizard.</p>
        </div>
      </div>

      <!-- Tab rail -->
      <div class="rt-tabs">
        <button
          v-for="t in TOOL_TABS"
          :key="t.value"
          class="rt-tab"
          :class="{ 'rt-tab--active': activeTool === t.value }"
          @click="activeTool = t.value"
        >
          <i :class="['pi', t.icon]" />
          <span>{{ t.label }}</span>
        </button>
      </div>

      <!-- Tool panels -->
      <div class="rt-panel">
        <Transition name="rt-fade" mode="out-in">
          <GrastateInspectorPanel  v-if="activeTool === 'grastate'"      key="grastate"     :cluster-id="clusterStore.selectedClusterId" />
          <SnapshotPanel           v-else-if="activeTool === 'snapshot'"   key="snapshot"     :cluster-id="clusterStore.selectedClusterId" />
          <IstSstHelper            v-else-if="activeTool === 'ist-sst'"    key="ist-sst"      :cluster-id="clusterStore.selectedClusterId" />
          <SplitBrainWizard        v-else-if="activeTool === 'split-brain'" key="split-brain" :cluster-id="clusterStore.selectedClusterId" />
          <FullClusterRecovery     v-else-if="activeTool === 'full-cluster'" key="full-cluster" :cluster-id="clusterStore.selectedClusterId" />
        </Transition>
      </div>

    </div>

  </div>
</template>

<style scoped>
.recovery-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  width: 100%;
  height: 100%;
}

.rp-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.pg-head-icon {
  width: 36px; height: 36px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-highlight);
  border: 1px solid rgba(45, 212, 191, 0.18);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-size: 0.875rem;
}
.pg-title {
  font-size: var(--text-xl); font-weight: 700;
  color: var(--color-text); letter-spacing: -0.02em; line-height: 1.2;
}
.rp-desc { font-size: var(--text-sm); color: var(--color-text-muted); }

/* ─ Info banner ──────────────────────────────────────────────── */
.info-banner {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}
@media (max-width: 900px) {
  .info-banner { grid-template-columns: 1fr; }
}
.info-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.info-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}
.info-card-header .pi { font-size: 0.875rem; color: var(--color-primary); flex-shrink: 0; }
.info-card:last-child .info-card-header .pi { color: var(--color-warning); }
.info-card p { font-size: var(--text-xs); color: var(--color-text-muted); line-height: 1.65; margin: 0; }
.info-card p strong { color: var(--color-text); font-weight: 600; }
.info-card p code {
  font-family: var(--font-mono, monospace);
  font-size: 0.75em;
  background: var(--color-surface-offset);
  border-radius: var(--radius-sm);
  padding: 1px 5px;
  color: var(--color-primary);
}
.info-card p em { font-style: normal; font-weight: 600; color: var(--color-text); }

/* ─ Guards ──────────────────────────────────────────────────── */
.rp-empty {
  display: flex; align-items: center; justify-content: center;
  gap: var(--space-3); color: var(--color-text-muted);
  padding: var(--space-16); font-size: var(--text-sm);
}
.rp-loading {
  display: flex; align-items: center; justify-content: center;
  gap: var(--space-3); color: var(--color-text-muted);
  padding: var(--space-12); font-size: var(--text-sm);
}
.rp-guard-msg  { width: 100%; }
.rp-guard-body { display: flex; flex-direction: column; gap: var(--space-1); font-size: var(--text-sm); }
:deep(.rp-guard-msg .p-message-content) {
  padding: var(--space-4) var(--space-5);
  gap: var(--space-3);
}

/* ═══ WIZARD ═════════════════════════════════════════════════ */
.rp-wizard {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: var(--space-6);
  flex: 1;
  min-height: 0;
}
@media (max-width: 860px) {
  .rp-wizard {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  .rp-sidebar {
    position: static !important;
    flex-direction: row !important;
    flex-wrap: wrap;
    padding: var(--space-3) var(--space-4) !important;
  }
  .rp-step-item {
    grid-template-areas: "ind meta" !important;
    grid-template-rows: auto !important;
  }
  .rp-step-connector { display: none !important; }
  .rp-step-meta { padding-bottom: 0 !important; }
}

/* ─ Sidebar ──────────────────────────────────────────────── */
.rp-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  align-self: start;
  position: sticky;
  top: var(--space-4);
}
.rp-step-item {
  display: grid;
  grid-template-areas: "ind  meta" "conn meta";
  grid-template-columns: 28px 1fr;
  grid-template-rows: auto 1fr;
  column-gap: var(--space-3);
}
.rp-step-connector {
  grid-area: conn;
  width: 2px;
  min-height: var(--space-6);
  background: var(--color-border);
  margin: 4px auto 4px;
  border-radius: 1px;
  transition: background 300ms ease;
}
.rp-step--done .rp-step-connector { background: var(--color-primary); }
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
.rp-step-meta {
  grid-area: meta;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: var(--space-6);
  padding-top: 4px;
}
.rp-step-item:last-child .rp-step-meta { padding-bottom: 0; }
.rp-step-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  transition: color 200ms ease;
  line-height: 1.2;
}
.rp-step--active .rp-step-label { color: var(--color-text); }
.rp-step--done   .rp-step-label { color: var(--color-primary); }
.rp-step-subdesc { font-size: 0.68rem; color: var(--color-text-faint); line-height: 1.3; }
.rp-step--active .rp-step-subdesc { color: var(--color-text-muted); }

/* ─ Content panel ────────────────────────────────────────── */
.rp-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-8);
  min-height: 400px;
  overflow: auto;
}
@media (max-width: 600px) {
  .rp-content { padding: var(--space-4); }
}

/* ─ Step transition ───────────────────────────────────────── */
.step-enter-active,
.step-leave-active  { transition: opacity 280ms ease, transform 280ms ease; }
.step-enter-from    { opacity: 0; transform: translateX(12px); }
.step-leave-to      { opacity: 0; transform: translateX(-12px); }

/* ═══ RECOVERY TOOLS SECTION ════════════════════════════════ */
.rt-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border);
  margin-top: var(--space-2);
}

.rt-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.rt-head-icon {
  width: 36px; height: 36px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(96, 165, 250, 0.1);
  border: 1px solid rgba(96, 165, 250, 0.2);
  border-radius: var(--radius-md);
  color: var(--color-info);
  font-size: 0.875rem;
}
.rt-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.rt-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* Tab rail */
.rt-tabs {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.rt-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition:
    color 160ms ease,
    background 160ms ease,
    border-color 160ms ease,
    box-shadow 160ms ease;
}
.rt-tab .pi { font-size: 0.75rem; opacity: 0.7; }

.rt-tab:hover:not(.rt-tab--active) {
  color: var(--color-text);
  background: var(--color-surface-offset);
}

.rt-tab--active {
  color: var(--color-info) !important;
  background: rgba(96, 165, 250, 0.08) !important;
  border-color: rgba(96, 165, 250, 0.3) !important;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.07);
}
.rt-tab--active .pi { opacity: 1; }

/* Panel */
.rt-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
}
@media (max-width: 600px) {
  .rt-panel { padding: var(--space-4); }
}

/* Transition */
.rt-fade-enter-active,
.rt-fade-leave-active  { transition: opacity 160ms ease, transform 160ms ease; }
.rt-fade-enter-from    { opacity: 0; transform: translateY(6px); }
.rt-fade-leave-to      { opacity: 0; transform: translateY(-4px); }
</style>
