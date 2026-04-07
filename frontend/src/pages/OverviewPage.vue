<template>
  <div class="page-overview">
    <!-- KPI Panel -->
    <section class="kpi-grid mb-4">
      <div class="kpi-card">
        <div class="kpi-label">Cluster Status</div>
        <div class="kpi-value" :class="clusterStatusClass">{{ s?.cluster_status || '—' }}</div>
        <div class="kpi-sub">{{ s?.contour?.toUpperCase() }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cluster Size</div>
        <div class="kpi-value">{{ s?.cluster_size ?? '—' }}</div>
        <div class="kpi-sub">{{ s?.nodes_total }} нод + {{ s?.arbitrators?.length || 0 }} арб</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Synced Nodes</div>
        <div class="kpi-value" :class="syncedClass">{{ s?.nodes_synced ?? '—' }}</div>
        <div class="kpi-sub">из {{ s?.nodes_total ?? '—' }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Flow Control</div>
        <div class="kpi-value" :class="fcClass">{{ fcValue }}</div>
        <div class="kpi-sub">wsrep_flow_control_paused</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cert Failures</div>
        <div class="kpi-value" :class="s?.cert_failures ? 'warn' : ''">{{ s?.cert_failures ?? '—' }}</div>
        <div class="kpi-sub">сумма по нодам</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Max Δ seqno</div>
        <div class="kpi-value" :class="seqnoDeltaClass">{{ seqnoDelta }}</div>
        <div class="kpi-sub">расхождение</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">BF Aborts</div>
        <div class="kpi-value">{{ bfAborts ?? '—' }}</div>
        <div class="kpi-sub">wsrep_bf_aborts</div>
      </div>
    </section>

    <!-- Mock scenarios -->
    <section v-if="cluster.isMock" class="mb-4">
      <div class="section-header">
        <i class="pi pi-play-circle" />
        <span class="section-title">Mock сценарии</span>
      </div>
      <div class="scenario-btns">
        <Button v-for="sc in scenarios" :key="sc.value"
          :label="sc.label" size="small"
          :outlined="cluster.scenario !== sc.value"
          :severity="sc.severity"
          @click="cluster.setScenario(sc.value)" />
      </div>
    </section>

    <!-- Node cards -->
    <section>
      <div class="section-header">
        <i class="pi pi-server" />
        <span class="section-title">Ноды</span>
        <span class="section-sub">{{ cluster.nodes.length }} нод</span>
      </div>
      <div class="nodes-grid">
        <NodeCard v-for="node in cluster.nodes" :key="node.id"
          :node="node" :sparkline="cluster.sparklines[node.id]" />
      </div>
    </section>

    <!-- Arbitrators -->
    <section v-if="cluster.arbitrators.length" class="mt-4">
      <div class="section-header">
        <i class="pi pi-share-alt" />
        <span class="section-title">Арбитры</span>
      </div>
      <div class="nodes-grid">
        <div v-for="arb in cluster.arbitrators" :key="arb.id" class="arb-card">
          <div class="arb-header">
            <span class="nc-name">{{ arb.id }}</span>
            <span v-if="arb.dc" class="nc-dc">{{ arb.dc }}</span>
            <span class="badge" :class="arbBadgeClass(arb)">{{ arb.status || 'UNKNOWN' }}</span>
          </div>
          <div class="arb-meta mono">{{ arb.host }}:{{ arb.ssh_port || 22 }}</div>
          <div class="arb-members" v-if="arb.members != null">members: {{ arb.members }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Button from 'primevue/button'
import NodeCard from '@/components/nodes/NodeCard.vue'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()
const s = computed(() => cluster.status)

const clusterStatusClass = computed(() => s.value?.cluster_status === 'Primary' ? 'ok' : 'error')
const syncedClass = computed(() => {
  if (!s.value) return ''
  return s.value.nodes_synced === s.value.nodes_total ? 'ok' : s.value.nodes_synced > 0 ? 'warn' : 'error'
})
const fcValue = computed(() => {
  const v = parseFloat(s.value?.flow_control)
  return isNaN(v) ? '—' : v.toFixed(4)
})
const fcClass = computed(() => {
  const v = parseFloat(s.value?.flow_control) || 0
  return v >= 0.05 ? 'warn' : ''
})
const seqnoDelta = computed(() => {
  const nodes = s.value?.nodes?.filter(n => n.wsrep_last_committed != null) || []
  if (nodes.length < 2) return '—'
  const vals = nodes.map(n => Number(n.wsrep_last_committed))
  return Math.max(...vals) - Math.min(...vals)
})
const seqnoDeltaClass = computed(() => {
  const d = seqnoDelta.value
  if (d === '—') return ''
  return d >= 5 ? 'error' : d > 0 ? 'warn' : ''
})
const bfAborts = computed(() => {
  return s.value?.nodes?.reduce((acc, n) => acc + (Number(n.wsrep_bf_aborts) || 0), 0) ?? '—'
})

function arbBadgeClass(arb) {
  const st = (arb.status || '').toLowerCase()
  if (st === 'running') return 'badge-synced'
  if (st === 'offline') return 'badge-offline'
  return 'badge-unknown'
}

const scenarios = [
  { value: 'normal',          label: 'Normal',          severity: 'success' },
  { value: 'gc01_down',       label: 'gc01 Down',       severity: 'danger'  },
  { value: 'gc02_down',       label: 'gc02 Down',       severity: 'danger'  },
  { value: 'flow_control',    label: 'Flow Control',    severity: 'warning' },
  { value: 'sst_in_progress', label: 'SST in Progress', severity: 'info'    },
]
</script>

<style scoped>
.page-overview { display: flex; flex-direction: column; gap: 0; }
.mb-4 { margin-bottom: 1.5rem; }
.mt-4 { margin-top: 1.5rem; }

.scenario-btns { display: flex; flex-wrap: wrap; gap: 0.5rem; }

.arb-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.875rem 1rem;
}
.arb-header { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 4px; }
.arb-meta   { font-size: 11px; color: var(--color-text-muted); }
.arb-members{ font-size: 12px; color: var(--color-text-secondary); margin-top: 4px; }
</style>
