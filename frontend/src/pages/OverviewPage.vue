<template>
  <div>
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Обзор кластера</h1>
        <p class="page-subtitle">{{ subtitle }}</p>
        <p style="font-size:0.72rem;color:var(--text-faint);margin-top:2px">
          Обновлено: {{ lastUpdateStr }}
        </p>
      </div>

      <!-- Scenario selector — only in mock mode -->
      <div v-if="cluster.isMock" class="flex-row">
        <div style="display:flex;align-items:center;gap:var(--space-2)">
          <span style="font-size:var(--text-xs);font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--text-muted)">Сценарий</span>
          <select
            class="form-input"
            style="width:230px"
            :value="cluster.scenario"
            @change="e => cluster.applyScenario(e.target.value)"
          >
            <option value="normal">✅ Normal — All Synced</option>
            <option value="gc01_down">🔴 gc01 — Node Down</option>
            <option value="gc02_down">🔴 gc02 — Node Down</option>
            <option value="flow_control">🟡 Flow Control Active</option>
            <option value="sst_in_progress">🔄 SST In Progress</option>
          </select>
        </div>
      </div>

      <!-- LIVE badge in real mode -->
      <div
        v-if="cluster.isReal"
        style="display:flex;align-items:center;gap:var(--space-2);background:var(--success-dim);border:1px solid var(--success);border-radius:var(--radius-full);padding:4px 14px"
      >
        <span style="width:8px;height:8px;border-radius:50%;background:var(--success);display:inline-block"></span>
        <span style="font-size:var(--text-xs);font-weight:700;color:var(--success)">LIVE &middot; REAL DATA</span>
      </div>
    </div>

    <!-- KPI Grid -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Cluster Status</div>
        <div class="kpi-value" :class="cluster.clusterStatusClass">
          {{ cluster.status?.cluster_status || '—' }}
        </div>
        <div class="kpi-sub">{{ cluster.status?.nodes?.[0]?.wsrep_cluster_status || 'Primary' }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cluster Size</div>
        <div class="kpi-value info">{{ cluster.nodes.length }}</div>
        <div class="kpi-sub">нод в кластере</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Synced Nodes</div>
        <div class="kpi-value" :class="cluster.nodesSynced === cluster.nodes.length ? 'ok' : 'warn'">
          {{ cluster.nodesSynced }}/{{ cluster.nodes.length }}
        </div>
        <div class="kpi-sub">wsrep_local_state = Synced</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Flow Control</div>
        <div class="kpi-value" :class="cluster.flowControl > 0.05 ? 'warn' : 'ok'">
          {{ cluster.flowControl.toFixed(3) }}
        </div>
        <div class="kpi-sub">wsrep_flow_control_paused</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Recv Queue</div>
        <div class="kpi-value" :class="maxRecvQueue > 0 ? 'warn' : 'ok'">{{ maxRecvQueue }}</div>
        <div class="kpi-sub">wsrep_local_recv_queue max</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Repl Lag</div>
        <div class="kpi-value" :class="seqnoLag > 100 ? 'warn' : 'ok'">{{ seqnoLag }}</div>
        <div class="kpi-sub">&Delta; wsrep_last_committed</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cert Fail / BF Ab</div>
        <div class="kpi-value" :class="cluster.certFailures > 0 ? 'warn' : 'ok'">
          {{ cluster.certFailures }} / {{ maxBfAborts }}
        </div>
        <div class="kpi-sub">cert_failures / bf_aborts</div>
      </div>
    </div>

    <!-- Nodes -->
    <h2 class="card-title" style="font-size:var(--text-lg);margin-bottom:var(--space-5)">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="2" width="20" height="8" rx="2"/>
        <rect x="2" y="14" width="20" height="8" rx="2"/>
      </svg>
      Состояние нод
    </h2>

    <div v-if="cluster.loading && !cluster.nodes.length" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">
      <span class="spin-dot" style="margin-right:8px"></span>
      Загрузка данных кластера…
    </div>

    <div class="nodes-grid">
      <NodeCard
        v-for="node in cluster.nodes"
        :key="node.id"
        :node="node"
        @action="handleNodeAction"
      />
    </div>

    <!-- Arbitrators -->
    <div v-if="cluster.arbitrators.length" style="margin-bottom:var(--space-8)">
      <h2 class="card-title" style="font-size:var(--text-lg);margin-bottom:var(--space-5)">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/>
        </svg>
        Арбитры (garbd)
      </h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--space-4)">
        <div
          v-for="arb in cluster.arbitrators"
          :key="arb.id"
          class="card"
          style="padding:var(--space-5)"
        >
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-3)">
            <div>
              <div style="font-weight:700">{{ arb.id || arb.host }}</div>
              <div style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted)">{{ arb.host }}:{{ arb.ssh_port || 22 }}</div>
            </div>
            <div style="display:flex;gap:6px;align-items:center">
              <span v-if="arb.dc" class="dc-badge">{{ arb.dc }}</span>
              <span class="node-state-badge" :class="arb.online ? 'badge-synced' : 'badge-offline'">
                {{ arb.online ? 'RUNNING' : 'DOWN' }}
              </span>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            <div class="metric-row">
              <div class="metric-key">members</div>
              <div class="metric-val">{{ arb.members || '—' }}</div>
            </div>
            <div class="metric-row">
              <div class="metric-key">status</div>
              <div class="metric-val" :class="arb.online ? 'ok' : 'error'">{{ arb.status || (arb.online ? 'RUNNING' : 'DOWN') }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Event Log -->
    <div class="log-wrap">
      <div class="log-toolbar">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16"/>
          <polyline points="14 2 14 8 20 8"/>
          <rect x="8" y="13" width="8" height="2"/>
          <rect x="8" y="17" width="8" height="2"/>
        </svg>
        <span style="font-size:var(--text-sm);font-weight:600">Журнал событий</span>
        <div style="flex:1"></div>
        <button
          class="log-filter-btn all"
          :class="{ active: logFilter === 'all' }"
          @click="logFilter = 'all'"
        >Все</button>
        <button
          class="log-filter-btn info-f"
          :class="{ active: logFilter === 'INFO' }"
          @click="logFilter = 'INFO'"
        >INFO</button>
        <button
          class="log-filter-btn warn-f"
          :class="{ active: logFilter === 'WARN' }"
          @click="logFilter = 'WARN'"
        >WARN</button>
        <button
          class="log-filter-btn error-f"
          :class="{ active: logFilter === 'ERROR' }"
          @click="logFilter = 'ERROR'"
        >ERROR</button>
        <button class="btn btn-ghost btn-sm" @click="exportLog">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Экспорт
        </button>
        <button class="btn btn-ghost btn-sm" @click="cluster.clearLog()">Очистить</button>
      </div>
      <div class="log-body">
        <div v-if="!filteredLog.length" style="color:var(--text-faint);text-align:center;padding:var(--space-4)">
          Журнал пуст
        </div>
        <div v-for="(entry, i) in filteredLog" :key="i" class="log-line">
          <span class="log-time">{{ entry.time }}</span>
          <span class="log-level" :class="entry.level">{{ entry.level }}</span>
          <span class="log-msg">{{ entry.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import NodeCard from '@/components/nodes/NodeCard.vue'
import { useClusterStore } from '@/stores/cluster.js'

const cluster   = useClusterStore()
const toast     = useToast()
const logFilter = ref('all')

// FIX: include cluster name in subtitle
const subtitle = computed(() => {
  const contourLabel = cluster.contour === 'prod' ? 'Prod-контур' : 'Тестовый контур'
  const modeLabel    = cluster.isMock ? '· Симуляция' : '· Реальные данные'
  const clusterLabel = cluster.clusterName && cluster.clusterName !== '—'
    ? ` · ${cluster.clusterName}`
    : ''
  return `${contourLabel}${clusterLabel} ${modeLabel}`
})

const lastUpdateStr = computed(() => {
  if (!cluster.lastUpdate) return '—'
  const d = cluster.lastUpdate
  const h = String(d.getHours()).padStart(2,'0')
  const m = String(d.getMinutes()).padStart(2,'0')
  const s = String(d.getSeconds()).padStart(2,'0')
  return `${h}:${m}:${s}`
})

const maxRecvQueue = computed(() =>
  Math.max(0, ...cluster.nodes.map(n =>
    parseInt(n.wsrep_local_recv_queue ?? n.metrics?.wsrep_local_recv_queue ?? 0, 10) || 0
  ))
)

const seqnoLag = computed(() => {
  const seqnos = cluster.nodes
    .map(n => parseInt(n.wsrep_last_committed ?? n.metrics?.wsrep_last_committed ?? 0, 10) || 0)
    .filter(v => v > 0)
  if (!seqnos.length) return 0
  return Math.max(...seqnos) - Math.min(...seqnos)
})

const maxBfAborts = computed(() =>
  Math.max(0, ...cluster.nodes.map(n =>
    parseInt(n.wsrep_bf_aborts ?? n.metrics?.wsrep_bf_aborts ?? 0, 10) || 0
  ))
)

const filteredLog = computed(() =>
  logFilter.value === 'all'
    ? cluster.eventLog
    : cluster.eventLog.filter(e => e.level === logFilter.value)
)

// FIX: route ping and rejoin to dedicated store methods;
//      all other actions go to generic nodeAction()
async function handleNodeAction({ nodeId, action, _ping, _rejoin }) {
  try {
    if (_ping) {
      // ping → GET /api/node/{id}/test-connection
      await cluster.pingNode(nodeId)
      return
    }
    if (_rejoin) {
      // rejoin → POST /api/node/{id}/rejoin
      const { default: api } = await import('@/api/index.js')
      const resp = await api.post(`/api/node/${nodeId}/rejoin`)
      cluster.addLog('INFO', `Rejoin ${nodeId}: ${resp.data?.msg || 'OK'}`)
      toast.add({ severity: 'success', summary: 'Rejoin', detail: resp.data?.msg || 'Запущен', life: 3000 })
      await cluster.fetchStatus()
      return
    }
    // generic: start / stop / restart / set_read_only / set_read_write
    await cluster.nodeAction(nodeId, action)
    toast.add({ severity: 'success', summary: 'Готово', detail: `${action} → ${nodeId}`, life: 3000 })
    await cluster.fetchStatus()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: String(e.message), life: 5000 })
  }
}

function exportLog() {
  const lines = cluster.eventLog.map(e => `${e.time} ${e.level.padEnd(5)} ${e.msg}`).join('\n')
  const blob  = new Blob([lines], { type: 'text/plain' })
  const url   = URL.createObjectURL(blob)
  const a     = document.createElement('a')
  a.href = url
  a.download = `galera_log_${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}
</script>
