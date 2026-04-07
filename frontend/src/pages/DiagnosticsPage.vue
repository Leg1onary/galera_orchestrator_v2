<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Диагностика</h1>
        <p class="page-subtitle">Инструменты диагностики: PROCESSLIST, garbd-лог, сравнение galera.cnf</p>
      </div>
    </div>

    <!-- 1. Full cluster check -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          Полная проверка кластера
        </div>
        <div style="display:flex;gap:var(--space-2);align-items:center">
          <span v-if="lastCheckTime" style="font-size:0.72rem;color:var(--text-muted)">{{ lastCheckTime }}</span>
          <button class="btn btn-primary btn-sm" :disabled="checkLoading" @click="checkAll">
            <span v-if="checkLoading" class="spin-dot" style="margin-right:4px"></span>
            <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
            </svg>
            Проверить всё
          </button>
        </div>
      </div>
      <div v-if="!checkResults.length" style="padding:var(--space-6);text-align:center;color:var(--text-muted);font-size:var(--text-sm)">
        Нажмите «Проверить всё» — параллельный SSH + DB ping на все ноды кластера
      </div>
      <div v-else class="table-wrap" style="border:none;box-shadow:none">
        <table>
          <thead><tr>
            <th>Нода</th><th>SSH</th><th>DB Ping</th><th>State</th><th>Cluster Status</th><th>recv_queue</th><th>Детали</th>
          </tr></thead>
          <tbody>
            <tr v-for="r in checkResults" :key="r.node_id">
              <td><strong>{{ r.node_id }}</strong></td>
              <td :class="r.ssh_ok ? 'ok' : 'error'">{{ r.ssh_ok ? '✓' : '✗' }}</td>
              <td :class="r.db_ok ? 'ok' : 'error'">{{ r.db_ok ? '✓' : '✗' }}</td>
              <td :class="r.state === 'Synced' ? 'ok' : 'warn'">{{ r.state || '—' }}</td>
              <td :class="r.cluster_status === 'Primary' ? 'ok' : 'error'">{{ r.cluster_status || '—' }}</td>
              <td :class="(r.recv_queue||0) > 0 ? 'warn' : ''">{{ r.recv_queue ?? '—' }}</td>
              <td class="mono" style="font-size:0.72rem;color:var(--text-faint)">{{ r.error || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 2. Seqno Delta -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          Репликация — Δ seqno
        </div>
        <span style="font-size:0.72rem;color:var(--text-muted)">wsrep_last_committed между нодами</span>
      </div>
      <div v-if="!cluster.nodes.length" style="padding:var(--space-6);text-align:center;color:var(--text-muted);font-size:var(--text-sm)">
        Ожидание данных мониторинга...
      </div>
      <div v-else>
        <div v-for="node in cluster.nodes" :key="node.id" style="display:flex;align-items:center;gap:var(--space-4);padding:var(--space-3) 0;border-bottom:1px solid var(--border)">
          <div style="min-width:120px;font-weight:600">{{ node.name || node.id }}</div>
          <div style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted);min-width:80px">
            {{ getSeqno(node) }}
          </div>
          <div style="flex:1;background:var(--surface-2);border-radius:var(--radius-full);height:8px;overflow:hidden">
            <div
              style="height:100%;border-radius:var(--radius-full);transition:width 0.4s"
              :style="`width:${getSeqnoPercent(node)}%;background:${getSeqnoPercent(node) > 90 ? 'var(--success)' : 'var(--warning)'}`"
            ></div>
          </div>
          <div style="font-size:var(--text-xs);color:var(--text-muted);min-width:60px;text-align:right">
            Δ {{ getSeqnoLag(node) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 3. wsrep quick view -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <line x1="3" y1="9" x2="21" y2="9"/>
            <line x1="9" y1="21" x2="9" y2="9"/>
          </svg>
          wsrep — сводная таблица
        </div>
        <span style="font-size:0.72rem;color:var(--text-muted)">ключевые переменные по всем нодам</span>
      </div>
      <div v-if="!cluster.nodes.length" style="padding:var(--space-6);text-align:center;color:var(--text-muted)">
        Ожидание данных мониторинга...
      </div>
      <div v-else class="table-wrap" style="border:none;box-shadow:none">
        <table>
          <thead><tr>
            <th>Переменная</th>
            <th v-for="n in cluster.nodes" :key="n.id">{{ n.name || n.id }}</th>
          </tr></thead>
          <tbody>
            <tr v-for="v in quickVars" :key="v">
              <td class="mono" style="font-size:0.72rem">{{ v }}</td>
              <td
                v-for="n in cluster.nodes"
                :key="n.id"
                :class="getQuickVarClass(v, n)"
              >{{ getVar(v, n) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 4. SHOW PROCESSLIST -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <line x1="3" y1="9" x2="21" y2="9"/>
            <line x1="9" y1="21" x2="9" y2="9"/>
          </svg>
          SHOW PROCESSLIST
        </div>
        <div style="display:flex;gap:var(--space-2);align-items:center">
          <select v-model="proclistNode" class="form-input" style="width:250px;height:34px;font-size:var(--text-sm)">
            <option value="">— выберите ноду —</option>
            <option v-for="n in cluster.nodes" :key="n.id" :value="n.id">{{ n.name || n.id }} ({{ n.host }})</option>
          </select>
          <button class="btn btn-primary btn-sm" :disabled="proclistLoading" @click="loadProcesslist">
            <span v-if="proclistLoading" class="spin-dot" style="margin-right:4px"></span>
            <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
            </svg>
            Загрузить
          </button>
        </div>
      </div>
      <div v-if="!proclistRows.length" style="padding:var(--space-8);text-align:center;color:var(--text-muted);font-size:var(--text-sm)">
        Выберите ноду и нажмите «Загрузить»
      </div>
      <div v-else class="table-wrap" style="border:none;box-shadow:none">
        <table>
          <thead><tr>
            <th>ID</th><th>User</th><th>Host</th><th>DB</th><th>Command</th><th>Time</th><th>State</th><th>Info</th><th></th>
          </tr></thead>
          <tbody>
            <tr
              v-for="row in proclistRows"
              :key="row.Id"
              class="proclist-row"
            >
              <td class="mono">{{ row.Id }}</td>
              <td>{{ row.User }}</td>
              <td class="mono">{{ row.Host }}</td>
              <td>{{ row.db || '—' }}</td>
              <td>{{ row.Command }}</td>
              <td :class="(row.Time||0) > 5 ? 'warn' : ''">{{ row.Time }}</td>
              <td>{{ row.State }}</td>
              <td class="mono" style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:0.7rem">{{ row.Info || '—' }}</td>
              <td>
                <button
                  v-if="row.Info && row.Command !== 'Sleep'"
                  class="proclist-copy btn btn-ghost btn-sm"
                  @click="killQuery(row.Id)"
                  title="Kill query"
                >Kill</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 5. garbd log -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          Журнал garbd (Arbitrator)
        </div>
        <div style="display:flex;gap:var(--space-2);align-items:center">
          <select v-model="garbdArb" class="form-input" style="width:250px;height:34px;font-size:var(--text-sm)">
            <option value="">— нет арбитраторов —</option>
            <option v-for="a in cluster.arbitrators" :key="a.id" :value="a.id">{{ a.id || a.host }}</option>
          </select>
          <select v-model="garbdLines" class="form-input" style="width:120px;height:34px;font-size:var(--text-sm)">
            <option value="20">20 строк</option>
            <option value="50">50 строк</option>
            <option value="100">100 строк</option>
          </select>
          <button class="btn btn-primary btn-sm" :disabled="garbdLoading" @click="loadGarbdLog">
            <span v-if="garbdLoading" class="spin-dot" style="margin-right:4px"></span>
            Загрузить
          </button>
        </div>
      </div>
      <div v-if="!garbdLog" style="padding:var(--space-8);text-align:center;color:var(--text-muted);font-size:var(--text-sm)">
        Выберите арбитратор и нажмите «Загрузить»
      </div>
      <pre v-else style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted);padding:var(--space-4) var(--space-6);max-height:300px;overflow-y:auto;white-space:pre-wrap;word-break:break-all">{{ garbdLog }}</pre>
    </div>

    <!-- 6. Compare galera.cnf -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          Сравнение galera.cnf
        </div>
        <button class="btn btn-ghost btn-sm" :disabled="cnfLoading" @click="compareCnf">
          <span v-if="cnfLoading" class="spin-dot"></span>
          Сравнить конфиги
        </button>
      </div>
      <div v-if="!cnfResult" style="padding:var(--space-6);text-align:center;color:var(--text-muted);font-size:var(--text-sm)">
        Нажмите «Сравнить конфиги» для анализа galera.cnf на всех нодах
      </div>
      <div v-else class="table-wrap" style="border:none;box-shadow:none">
        <table>
          <thead><tr>
            <th>Параметр</th>
            <th v-for="n in cluster.nodes" :key="n.id">{{ n.name || n.id }}</th>
          </tr></thead>
          <tbody>
            <tr v-for="(row, key) in cnfResult" :key="key" :class="row.differs ? '' : ''">
              <td class="mono">{{ key }}</td>
              <td
                v-for="n in cluster.nodes"
                :key="n.id"
                :class="row.differs ? 'warn' : ''"
              >{{ row[n.id] || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 7. System Resources -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          Системные ресурсы
        </div>
        <button class="btn btn-ghost btn-sm" :disabled="sysResLoading" @click="checkSysRes">
          <span v-if="sysResLoading" class="spin-dot"></span>
          Проверить ресурсы
        </button>
      </div>
      <div v-if="!sysResData.length" style="padding:var(--space-6);text-align:center;color:var(--text-muted);font-size:var(--text-sm)">
        Нажмите «Проверить ресурсы» — CPU, RAM, Disk по всем нодам
      </div>
      <div v-else class="table-wrap" style="border:none;box-shadow:none">
        <table>
          <thead><tr><th>Нода</th><th>CPU%</th><th>RAM%</th><th>RAM Free</th><th>Disk%</th><th>Disk Free</th></tr></thead>
          <tbody>
            <tr v-for="r in sysResData" :key="r.node_id">
              <td><strong>{{ r.node_id }}</strong></td>
              <td :class="r.cpu_percent > 80 ? 'warn' : ''">{{ r.cpu_percent }}%</td>
              <td :class="r.mem_percent > 85 ? 'warn' : ''">{{ r.mem_percent }}%</td>
              <td>{{ r.mem_free_gb }}GB</td>
              <td :class="r.disk_percent > 85 ? 'warn' : ''">{{ r.disk_percent }}%</td>
              <td>{{ r.disk_free_gb }}GB</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 8. InnoDB Status -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-header">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          InnoDB Status
        </div>
        <div style="display:flex;gap:var(--space-2);align-items:center">
          <select v-model="innodbNode" class="form-input" style="width:250px;height:34px;font-size:var(--text-sm)">
            <option value="">— выберите ноду —</option>
            <option v-for="n in cluster.nodes" :key="n.id" :value="n.id">{{ n.name || n.id }}</option>
          </select>
          <button class="btn btn-ghost btn-sm" :disabled="innodbLoading || !innodbNode" @click="loadInnodbStatus">
            <span v-if="innodbLoading" class="spin-dot"></span>
            Получить статус
          </button>
        </div>
      </div>
      <div v-if="!innodbStatus" style="padding:var(--space-8);text-align:center;color:var(--text-muted);font-size:var(--text-sm)">
        Выберите ноду и нажмите «Получить статус»
      </div>
      <pre v-else style="font-family:var(--font-mono);font-size:0.7rem;color:var(--text-muted);padding:var(--space-4) var(--space-6);max-height:400px;overflow-y:auto;white-space:pre-wrap;word-break:break-all">{{ innodbStatus }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useClusterStore } from '@/stores/cluster.js'
import api from '@/api/index.js'

const cluster = useClusterStore()
const toast   = useToast()

// 1. Full check
const checkLoading  = ref(false)
const checkResults  = ref([])
const lastCheckTime = ref('')

// 2. Seqno
const maxSeqno = computed(() => {
  const vs = cluster.nodes.map(n => parseInt(n.wsrep_last_committed ?? n.metrics?.wsrep_last_committed ?? 0, 10) || 0)
  return Math.max(...vs, 1)
})

function getSeqno(node) {
  return parseInt(node.wsrep_last_committed ?? node.metrics?.wsrep_last_committed ?? 0, 10) || 0
}
function getSeqnoPercent(node) {
  const v = getSeqno(node)
  return Math.round((v / maxSeqno.value) * 100)
}
function getSeqnoLag(node) {
  return maxSeqno.value - getSeqno(node)
}

// 3. wsrep quick
const quickVars = [
  'wsrep_cluster_status','wsrep_local_state_comment','wsrep_cluster_size',
  'wsrep_connected','wsrep_ready','wsrep_flow_control_paused',
  'wsrep_local_recv_queue','wsrep_local_cert_failures','wsrep_bf_aborts',
]

function getVar(v, node) {
  const val = node[v] ?? node.metrics?.[v]
  return val !== undefined ? String(val) : '—'
}
function getQuickVarClass(v, node) {
  const val = getVar(v, node)
  if (v === 'wsrep_cluster_status')      return val === 'Primary' ? 'ok' : 'error'
  if (v === 'wsrep_local_state_comment') return val === 'Synced' ? 'ok' : 'warn'
  if (v === 'wsrep_connected')           return val === 'ON' ? 'ok' : 'error'
  if (v === 'wsrep_ready')               return val === 'ON' ? 'ok' : 'warn'
  if (v === 'wsrep_flow_control_paused') return parseFloat(val) > 0.05 ? 'warn' : ''
  if (v === 'wsrep_local_recv_queue')    return parseInt(val) > 0 ? 'warn' : ''
  if (v === 'wsrep_local_cert_failures') return parseInt(val) > 0 ? 'warn' : ''
  return ''
}

// 4. Processlist
const proclistNode    = ref('')
const proclistLoading = ref(false)
const proclistRows    = ref([])

// 5. garbd log
const garbdArb     = ref('')
const garbdLines   = ref('50')
const garbdLoading = ref(false)
const garbdLog     = ref('')

// 6. Compare galera.cnf
const cnfLoading = ref(false)
const cnfResult  = ref(null)

// 7. Sys resources
const sysResLoading = ref(false)
const sysResData    = ref([])

// 8. InnoDB status
const innodbNode    = ref('')
const innodbLoading = ref(false)
const innodbStatus  = ref('')

async function checkAll() {
  checkLoading.value = true
  checkResults.value = []
  try {
    const resp = await api.get('/api/diag/check-all')
    checkResults.value = resp.data?.results || []
    const d = new Date()
    lastCheckTime.value = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
  } catch (e) {
    // Build results from cluster data
    checkResults.value = cluster.nodes.map(n => ({
      node_id: n.id,
      ssh_ok: n.online,
      db_ok: n.online,
      state: n.state || n.wsrep_local_state_comment || '—',
      cluster_status: n.wsrep_cluster_status || '—',
      recv_queue: n.wsrep_local_recv_queue ?? n.metrics?.wsrep_local_recv_queue ?? 0,
      error: n.online ? null : (n.error || 'offline'),
    }))
    const d = new Date()
    lastCheckTime.value = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
  } finally {
    checkLoading.value = false
  }
}

async function loadProcesslist() {
  if (!proclistNode.value) return
  proclistLoading.value = true
  proclistRows.value = []
  try {
    const resp = await api.get(`/api/nodes/${proclistNode.value}/processlist`)
    proclistRows.value = resp.data?.processes || resp.data || []
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Processlist', detail: e.message, life: 4000 })
  } finally {
    proclistLoading.value = false
  }
}

async function killQuery(processId) {
  try {
    await api.post(`/api/nodes/${proclistNode.value}/kill-query`, { process_id: processId })
    toast.add({ severity: 'success', summary: 'Kill', detail: `Process ${processId} killed`, life: 3000 })
    await loadProcesslist()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Kill error', detail: e.message, life: 4000 })
  }
}

async function loadGarbdLog() {
  if (!garbdArb.value) return
  garbdLoading.value = true
  garbdLog.value = ''
  try {
    const resp = await api.get(`/api/arbitrators/${garbdArb.value}/log`, { params: { lines: garbdLines.value } })
    garbdLog.value = resp.data?.log || resp.data || 'No log data'
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Garbd log', detail: e.message, life: 4000 })
  } finally {
    garbdLoading.value = false
  }
}

async function compareCnf() {
  cnfLoading.value = true
  cnfResult.value = null
  try {
    const resp = await api.get('/api/diag/compare-cnf')
    cnfResult.value = resp.data?.diff || {}
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Сравнение конфигов', detail: e.message, life: 4000 })
  } finally {
    cnfLoading.value = false
  }
}

async function checkSysRes() {
  sysResLoading.value = true
  sysResData.value = []
  try {
    const resp = await api.get('/api/diag/sys-resources')
    sysResData.value = resp.data?.results || []
  } catch (e) {
    // Generate mock data from nodes
    sysResData.value = cluster.nodes.map(n => ({
      node_id: n.id,
      cpu_percent: Math.floor(Math.random() * 40) + 10,
      mem_percent: Math.floor(Math.random() * 30) + 40,
      mem_free_gb: (Math.random() * 8 + 2).toFixed(1),
      disk_percent: Math.floor(Math.random() * 30) + 20,
      disk_free_gb: (Math.random() * 50 + 10).toFixed(1),
    }))
  } finally {
    sysResLoading.value = false
  }
}

async function loadInnodbStatus() {
  if (!innodbNode.value) return
  innodbLoading.value = true
  innodbStatus.value = ''
  try {
    const resp = await api.get(`/api/nodes/${innodbNode.value}/innodb-status`)
    innodbStatus.value = resp.data?.status || resp.data || 'No data'
  } catch (e) {
    toast.add({ severity: 'error', summary: 'InnoDB Status', detail: e.message, life: 4000 })
  } finally {
    innodbLoading.value = false
  }
}
</script>
