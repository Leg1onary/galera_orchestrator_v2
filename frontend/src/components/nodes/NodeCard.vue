<template>
  <div class="node-card" :class="cardClass">
    <!-- Error banner -->
    <div v-if="node.error" class="node-error-banner">{{ node.error }}</div>

    <!-- Header -->
    <div class="node-header">
      <div>
        <div class="node-name">{{ node.name || node.id }}</div>
        <div class="node-host">{{ node.host }}:{{ node.port || 3306 }}</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <span class="dc-badge" v-if="node.dc">DC: {{ node.dc }}</span>
        <span class="node-state-badge" :class="stateBadgeClass">{{ stateLabel }}</span>
      </div>
    </div>

    <!-- Metrics grid 2×4 -->
    <div class="node-metrics">
      <div class="metric-row">
        <div class="metric-key">wsrep_cluster_status</div>
        <div class="metric-val" :class="m('wsrep_cluster_status') === 'Primary' ? 'ok' : 'warn'">
          {{ m('wsrep_cluster_status') }}
        </div>
      </div>
      <div class="metric-row">
        <div class="metric-key">wsrep_cluster_size</div>
        <div class="metric-val">{{ m('wsrep_cluster_size') }}</div>
      </div>
      <div class="metric-row">
        <div class="metric-key">wsrep_connected</div>
        <div class="metric-val" :class="m('wsrep_connected') === 'ON' ? 'ok' : 'error'">
          {{ m('wsrep_connected') }}
        </div>
      </div>
      <div class="metric-row">
        <div class="metric-key">wsrep_ready</div>
        <div class="metric-val" :class="m('wsrep_ready') === 'ON' ? 'ok' : 'warn'">
          {{ m('wsrep_ready') }}
        </div>
      </div>
      <div class="metric-row">
        <div class="metric-key">wsrep_local_state</div>
        <div class="metric-val" :class="stateClass">{{ m('wsrep_local_state_comment') }}</div>
      </div>
      <div class="metric-row">
        <div class="metric-key">recv_queue</div>
        <div class="metric-val" :class="parseInt(m('wsrep_local_recv_queue')) > 0 ? 'warn' : ''">
          {{ m('wsrep_local_recv_queue') }}
        </div>
      </div>
      <div class="metric-row">
        <div class="metric-key">send_queue</div>
        <div class="metric-val" :class="parseInt(m('wsrep_local_send_queue')) > 0 ? 'warn' : ''">
          {{ m('wsrep_local_send_queue') }}
        </div>
      </div>
      <div class="metric-row">
        <div class="metric-key">flow_control</div>
        <div class="metric-val" :class="parseFloat(m('wsrep_flow_control_paused')) > 0.01 ? 'warn' : ''">
          {{ m('wsrep_flow_control_paused') }}
        </div>
      </div>
    </div>

    <!-- Action buttons row 1 -->
    <div class="node-actions">
      <button class="btn btn-success btn-sm" @click="$emit('action', { nodeId: node.id, action: 'start' })">
        ▶ Start
      </button>
      <button class="btn btn-danger btn-sm" @click="confirmStop">
        ⏹ Stop
      </button>
      <button class="btn btn-warning btn-sm" @click="confirmRestart">
        ↺ Restart
      </button>
      <button class="btn btn-primary btn-sm" @click="$emit('action', { nodeId: node.id, action: 'rejoin' })">
        → Rejoin
      </button>
    </div>

    <!-- Toggle buttons row 2 -->
    <div class="node-actions">
      <button
        class="btn btn-sm"
        :class="node.read_only ? 'btn-warning' : 'btn-ghost'"
        @click="$emit('action', { nodeId: node.id, action: node.read_only ? 'readonly-off' : 'readonly-on' })"
        :title="node.read_only ? 'Read-Only включён — нажать для R/W' : 'Нажать для включения R/O'"
      >
        {{ node.read_only ? '🔒 R/O' : '✓ R/W' }}
      </button>
      <button class="btn btn-ghost btn-sm" @click="$emit('action', { nodeId: node.id, action: 'ping' })">
        ⊙ Ping
      </button>
    </div>

    <!-- Sparklines -->
    <Sparkline
      :flow-history="flowHistory"
      :recv-history="recvHistory"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import Sparkline from './Sparkline.vue'
import { useClusterStore } from '@/stores/cluster.js'

const props = defineProps({
  node: { type: Object, required: true },
})

const emit    = defineEmits(['action'])
const confirm = useConfirm()
const cluster = useClusterStore()

// Get a metric value: try node top-level fields, then node.metrics
function m(key) {
  const n = props.node
  if (n[key] !== undefined && n[key] !== null) return String(n[key])
  if (n.metrics?.[key] !== undefined) return String(n.metrics[key])
  return '—'
}

const state = computed(() => {
  const n = props.node
  if (!n.online) return 'offline'
  const s = (n.state || n.wsrep_local_state_comment || '').toLowerCase()
  if (s.includes('synced'))  return 'synced'
  if (s.includes('donor'))   return 'donor'
  if (s.includes('joiner') || s.includes('joining')) return 'joiner'
  return 'synced'
})

const cardClass = computed(() => state.value)
const stateLabel = computed(() => {
  if (!props.node.online) return 'OFFLINE'
  return m('wsrep_local_state_comment').toUpperCase() || 'UNKNOWN'
})

const stateBadgeClass = computed(() => {
  switch (state.value) {
    case 'synced':  return 'badge-synced'
    case 'donor':   return 'badge-donor'
    case 'joiner':  return 'badge-joiner'
    case 'offline': return 'badge-offline'
    default:        return 'badge-primary'
  }
})

const stateClass = computed(() => {
  switch (state.value) {
    case 'synced':  return 'ok'
    case 'donor':   return 'warn'
    case 'joiner':  return ''
    case 'offline': return 'error'
    default:        return ''
  }
})

// Sparkline history from store
const flowHistory = computed(() =>
  cluster.sparkHistory[props.node.id]?.flow || [0]
)
const recvHistory = computed(() =>
  cluster.sparkHistory[props.node.id]?.recv || [0]
)

function confirmStop() {
  confirm.require({
    message: `Остановить MariaDB на ноде "${props.node.name || props.node.id}"?`,
    header:  'Подтверждение',
    icon:    'pi pi-exclamation-triangle',
    accept:  () => emit('action', { nodeId: props.node.id, action: 'stop' }),
  })
}

function confirmRestart() {
  confirm.require({
    message: `Перезапустить MariaDB на ноде "${props.node.name || props.node.id}"?`,
    header:  'Подтверждение',
    icon:    'pi pi-refresh',
    accept:  () => emit('action', { nodeId: props.node.id, action: 'restart' }),
  })
}
</script>
