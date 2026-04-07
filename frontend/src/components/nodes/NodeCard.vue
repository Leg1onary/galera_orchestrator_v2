<template>
  <div class="node-card" :class="`state-${nodeState}`">
    <!-- Header -->
    <div class="nc-header">
      <div class="nc-identity">
        <span class="nc-name">{{ node.name || node.id }}</span>
        <span v-if="node.dc" class="nc-dc">{{ node.dc }}</span>
        <span class="badge" :class="stateBadgeClass">{{ displayState }}</span>
      </div>
      <div class="nc-host mono">{{ node.host }}:{{ node.port }}</div>
    </div>

    <!-- Metrics table -->
    <table class="metric-table" v-if="node.online !== false">
      <tbody>
        <tr>
          <td>Cluster Status</td>
          <td :class="clusterStatusClass">{{ node.wsrep_cluster_status || '—' }}</td>
        </tr>
        <tr>
          <td>Cluster Size</td>
          <td>{{ node.wsrep_cluster_size || '—' }}</td>
        </tr>
        <tr>
          <td>Flow Control</td>
          <td :class="fcClass">{{ fcValue }}</td>
        </tr>
        <tr>
          <td>Recv Queue</td>
          <td :class="rqClass">{{ node.wsrep_local_recv_queue ?? '—' }}</td>
        </tr>
        <tr>
          <td>Cert Failures</td>
          <td>{{ node.wsrep_local_cert_failures ?? '—' }}</td>
        </tr>
        <tr>
          <td>Last Committed</td>
          <td class="mono">{{ node.wsrep_last_committed ?? '—' }}</td>
        </tr>
        <tr>
          <td>Read Only</td>
          <td :class="node.read_only ? 'text-warn' : ''">{{ node.read_only ? 'YES' : 'NO' }}</td>
        </tr>
      </tbody>
    </table>

    <div v-else class="nc-offline-msg">
      <i class="pi pi-exclamation-triangle" />
      {{ node.error || 'Нода недоступна' }}
    </div>

    <!-- Sparklines -->
    <div class="nc-sparklines" v-if="sparkline">
      <div class="spark-item">
        <span class="spark-label">Flow Control</span>
        <Sparkline :data="sparkline.fc" :threshold="0.05" color-ok="#22c55e" color-warn="#f59e0b" />
      </div>
      <div class="spark-item">
        <span class="spark-label">Recv Queue</span>
        <Sparkline :data="sparkline.rq" :threshold="1" color-ok="#22c55e" color-warn="#f59e0b" />
      </div>
    </div>

    <!-- Actions -->
    <div class="nc-actions" v-if="node.online !== false || true">
      <Button size="small" text label="Start"   icon="pi pi-play"        @click="action('start')"        :loading="busy === 'start'" />
      <Button size="small" text label="Stop"    icon="pi pi-stop"        @click="action('stop')"         :loading="busy === 'stop'"  severity="danger" />
      <Button size="small" text label="Restart" icon="pi pi-refresh"     @click="action('restart')"      :loading="busy === 'restart'" />
      <Button size="small" text label="Rejoin"  icon="pi pi-sign-in"     @click="action('rejoin')"       :loading="busy === 'rejoin'" />
      <Button size="small" text :label="node.read_only ? 'R/W' : 'R/O'"
        :icon="node.read_only ? 'pi pi-lock-open' : 'pi pi-lock'"
        @click="toggleRO" :loading="busy === 'ro'" />
      <Button size="small" text label="Ping" icon="pi pi-wifi" @click="doPing" :loading="busy === 'ping'" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Sparkline from '@/components/nodes/Sparkline.vue'
import api from '@/api'
import { useClusterStore } from '@/stores/cluster'

const props = defineProps({
  node: { type: Object, required: true },
  sparkline: { type: Object, default: null },
})

const cluster = useClusterStore()
const toast = useToast()
const busy = ref('')

const nodeState = computed(() => {
  if (!props.node.online) return 'offline'
  const s = (props.node.wsrep_local_state_comment || '').toLowerCase()
  if (s === 'synced') return 'synced'
  if (s.includes('donor') || s.includes('desync')) return 'donor'
  if (s.includes('joining') || s.includes('joiner')) return 'joining'
  return 'unknown'
})

const displayState = computed(() => {
  if (!props.node.online) return 'OFFLINE'
  return (props.node.wsrep_local_state_comment || 'UNKNOWN').toUpperCase()
})

const stateBadgeClass = computed(() => `badge-${nodeState.value}`)
const clusterStatusClass = computed(() => props.node.wsrep_cluster_status === 'Primary' ? 'text-ok' : 'text-error')
const fcValue = computed(() => {
  const v = parseFloat(props.node.wsrep_flow_control_paused)
  return isNaN(v) ? '—' : v.toFixed(4)
})
const fcClass = computed(() => {
  const v = parseFloat(props.node.wsrep_flow_control_paused) || 0
  return v >= 0.05 ? 'text-warn' : ''
})
const rqClass = computed(() => {
  return parseInt(props.node.wsrep_local_recv_queue) > 0 ? 'text-warn' : ''
})

async function action(act) {
  busy.value = act
  try {
    await cluster.nodeAction(props.node.id, act)
    toast.add({ severity: 'success', summary: act, detail: `${props.node.name}: ${act} успешно`, life: 2500 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || e.message, life: 4000 })
  } finally { busy.value = '' }
}

async function toggleRO() {
  const act = props.node.read_only ? 'set_read_write' : 'set_read_only'
  busy.value = 'ro'
  try {
    await cluster.nodeAction(props.node.id, act)
    toast.add({ severity: 'success', summary: 'OK', detail: `${props.node.name}: ${act}`, life: 2000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || e.message, life: 4000 })
  } finally { busy.value = '' }
}

async function doPing() {
  busy.value = 'ping'
  try {
    const { data } = await api.get(`/api/node/${props.node.id}/ping`)
    toast.add({ severity: data.ok ? 'success' : 'warn', summary: 'Ping', detail: data.msg || 'OK', life: 2500 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ping failed', detail: e.message, life: 3000 })
  } finally { busy.value = '' }
}
</script>

<style scoped>
.node-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
  display: flex; flex-direction: column;
}
.node-card:hover { border-color: var(--color-accent-primary); box-shadow: var(--shadow-card); }
.node-card.state-offline { border-color: rgba(239,68,68,.4); }

.nc-header { padding: 0.875rem 1rem 0.625rem; display: flex; flex-direction: column; gap: 4px; border-bottom: 1px solid var(--color-border); }
.nc-identity { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.nc-name { font-size: 14px; font-weight: 700; }
.nc-dc   { font-size: 10px; background: var(--color-bg-elevated); border: 1px solid var(--color-border); border-radius: 3px; padding: 1px 5px; color: var(--color-text-muted); }
.nc-host { font-size: 11px; color: var(--color-text-muted); }

.metric-table { margin: 0.5rem 1rem; }
.metric-table td { color: var(--color-text-secondary); }
.text-ok    { color: var(--color-status-ok) !important; }
.text-warn  { color: var(--color-status-warn) !important; }
.text-error { color: var(--color-status-error) !important; }

.nc-offline-msg { padding: 0.75rem 1rem; color: var(--color-status-error); font-size: 13px; display: flex; align-items: center; gap: 0.5rem; }

.nc-sparklines { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; padding: 0.5rem 1rem; border-top: 1px solid var(--color-border); }
.spark-item { display: flex; flex-direction: column; gap: 3px; }
.spark-label { font-size: 10px; color: var(--color-text-muted); font-weight: 600; }

.nc-actions { display: flex; flex-wrap: wrap; gap: 2px; padding: 0.5rem; border-top: 1px solid var(--color-border); }
</style>
