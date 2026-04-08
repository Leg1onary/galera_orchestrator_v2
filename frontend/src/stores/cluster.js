import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/index.js'

const LS_MODE    = 'galera_data_mode'  // 'mock' | 'real'
const LS_CONTOUR = 'galera_contour'    // 'test' | 'prod'
const LS_POLL    = 'galera_poll_interval'

export const useClusterStore = defineStore('cluster', () => {
  // ── State ────────────────────────────────────────────────────────
  const dataMode      = ref(localStorage.getItem(LS_MODE) || 'mock')
  const contour       = ref(localStorage.getItem(LS_CONTOUR) || 'test')
  const pollInterval  = ref(Number(localStorage.getItem(LS_POLL)) || 5)  // seconds
  const clusterIndex  = ref(0)
  const contours      = ref({})     // { test: ['cluster-1', ...], prod: [] }

  const status        = ref(null)   // raw /api/status response
  const loading       = ref(false)
  const lastUpdate    = ref(null)   // Date object
  const eventLog      = ref([])     // [{time, level, msg}]
  const gitSha        = ref('v2.0.0')
  const scenario      = ref('normal')

  // History for sparklines (per node, last 30 points)
  const sparkHistory  = ref({})     // { nodeId: { flow: [], recv: [] } }

  // ── Computed ─────────────────────────────────────────────────────
  const nodes = computed(() => status.value?.nodes || [])
  const arbitrators = computed(() => status.value?.arbitrators || [])
  const clusterName  = computed(() => status.value?.cluster_name || '—')
  const clusterState = computed(() => status.value?.cluster_status || 'unknown')
  const isMock       = computed(() => dataMode.value === 'mock')
  const isReal       = computed(() => dataMode.value === 'real')

  const nodesSynced  = computed(() =>
    nodes.value.filter(n => n.state === 'Synced' && n.online).length
  )
  const nodesOnline  = computed(() =>
    nodes.value.filter(n => n.online).length
  )
  const arbOnline    = computed(() =>
    arbitrators.value.filter(a => a.online).length
  )
  const flowControl  = computed(() =>
    status.value?.flow_control ?? 0
  )
  const certFailures = computed(() =>
    status.value?.cert_failures ?? 0
  )

  // header status dot class
  const clusterStatusClass = computed(() => {
    const s = clusterState.value
    if (s === 'healthy') return 'ok'
    if (s === 'degraded') return 'warn'
    if (s === 'critical' || s === 'error') return 'error'
    return 'ok'
  })

  // ── Actions ──────────────────────────────────────────────────────
  function addLog(level, msg) {
    const now = new Date()
    const h   = String(now.getHours()).padStart(2,'0')
    const m   = String(now.getMinutes()).padStart(2,'0')
    const s   = String(now.getSeconds()).padStart(2,'0')
    eventLog.value.unshift({ time: `${h}:${m}:${s}`, level, msg })
    if (eventLog.value.length > 200) eventLog.value.pop()
  }

  function clearLog() {
    eventLog.value = []
  }

  function _updateSparkHistory(nodes) {
    nodes.forEach(n => {
      if (!sparkHistory.value[n.id]) {
        sparkHistory.value[n.id] = { flow: [], recv: [] }
      }
      const h = sparkHistory.value[n.id]
      const flow = parseFloat(n.wsrep_flow_control_paused || n.metrics?.wsrep_flow_control_paused || 0)
      const recv = parseInt(n.wsrep_local_recv_queue || n.metrics?.wsrep_local_recv_queue || 0, 10)
      h.flow.push(flow); if (h.flow.length > 30) h.flow.shift()
      h.recv.push(recv); if (h.recv.length > 30) h.recv.shift()
    })
  }

  async function fetchStatus() {
    loading.value = true
    try {
      const resp = await api.get('/api/status')
      const data = resp.data

      // Log cluster status changes
      const prevStatus = status.value?.cluster_status
      if (prevStatus && prevStatus !== data.cluster_status) {
        addLog('INFO', `Статус кластера: ${prevStatus} → ${data.cluster_status}`)
      }

      // Log node state changes
      const prevNodes = status.value?.nodes || []
      const prevByIdState = Object.fromEntries(prevNodes.map(n => [n.id, n.state]))
      ;(data.nodes || []).forEach(n => {
        const prev = prevByIdState[n.id]
        if (prev && prev !== n.state) {
          addLog('WARN', `Нода ${n.name || n.id}: ${prev} → ${n.state}`)
        }
      })

      status.value     = data
      lastUpdate.value = new Date()
      _updateSparkHistory(data.nodes || [])
    } catch (e) {
      addLog('ERROR', `Ошибка получения статуса: ${e.message}`)
    } finally {
      loading.value = false
    }
  }

  async function setDataMode(mode) {
    dataMode.value = mode
    localStorage.setItem(LS_MODE, mode)
    try {
      await api.post('/api/config/mode', { mode })
    } catch { /* ignore */ }
    await fetchStatus()
    addLog('INFO', `Режим данных: ${mode.toUpperCase()}`)
  }

  async function syncModeWithBackend() {
    try {
      const resp = await api.get('/api/config/mode')
      const backendMode = resp.data?.mode
      if (backendMode && backendMode !== dataMode.value) {
        dataMode.value = backendMode
        localStorage.setItem(LS_MODE, backendMode)
      }
    } catch { /* backend unavailable — use localStorage value */ }
  }

  async function loadContours() {
    try {
      const resp = await api.get('/api/contours')
      contours.value = resp.data?.contours || {}
      const sel = resp.data?.selection || {}
      contour.value      = sel.contour       || contour.value
      clusterIndex.value = sel.cluster_index || 0
    } catch { /* no contours endpoint */ }
  }

  async function selectContour(c) {
    contour.value = c
    localStorage.setItem(LS_CONTOUR, c)
    clusterIndex.value = 0
    try {
      await api.post('/api/contours/select', { contour: c, cluster_index: 0 })
    } catch { /* ignore */ }
    await fetchStatus()
  }

  async function selectCluster(idx) {
    clusterIndex.value = idx
    try {
      await api.post('/api/contours/select', { contour: contour.value, cluster_index: idx })
    } catch { /* ignore */ }
    await fetchStatus()
  }

  async function applyScenario(name) {
    scenario.value = name
    try {
      // fix: backend expects /api/scenario/{name}, not POST body
      await api.post(`/api/scenario/${name}`)
      addLog('INFO', `Сценарий: ${name}`)
    } catch (e) {
      addLog('ERROR', `Сценарий ${name}: ${e.message}`)
    }
    await fetchStatus()
  }

  async function nodeAction(nodeId, action) {
    addLog('INFO', `${action} → ${nodeId}`)
    try {
      // fix: backend endpoint is /api/node/{id}/action with body {action}
      const resp = await api.post(`/api/node/${nodeId}/action`, { action })
      addLog('INFO', resp.data?.msg || `${action} выполнен`)
    } catch (e) {
      addLog('ERROR', `${action} ${nodeId}: ${e.message}`)
      throw e
    }
  }

  async function setReadOnly(nodeId, enabled) {
    const action = enabled ? 'set_read_only' : 'set_read_write'
    return nodeAction(nodeId, action)
  }

  async function pingNode(nodeId) {
    // ping is not a backend action — use test-connection endpoint instead
    addLog('INFO', `ping → ${nodeId}`)
    try {
      const resp = await api.get(`/api/node/${nodeId}/test-connection`)
      const ssh = resp.data?.ssh
      const db  = resp.data?.db
      addLog(resp.data?.ok ? 'INFO' : 'WARN',
        `${nodeId}: SSH=${ssh?.message || '?'}, DB=${db?.message || '?'}`)
    } catch (e) {
      addLog('ERROR', `ping ${nodeId}: ${e.message}`)
      throw e
    }
  }

  async function fetchGitSha() {
    try {
      const resp = await api.get('/api/version')
      gitSha.value = resp.data?.sha || resp.data?.version || 'v2.0.0'
    } catch { /* ignore */ }
  }

  function setPollInterval(secs) {
    pollInterval.value = secs
    localStorage.setItem(LS_POLL, secs)
  }

  return {
    // state
    dataMode, contour, pollInterval, clusterIndex, contours,
    status, loading, lastUpdate, eventLog, gitSha, scenario, sparkHistory,
    // computed
    nodes, arbitrators, clusterName, clusterState,
    isMock, isReal, nodesSynced, nodesOnline, arbOnline,
    flowControl, certFailures, clusterStatusClass,
    // actions
    addLog, clearLog, fetchStatus, setDataMode,
    syncModeWithBackend, loadContours, selectContour, selectCluster,
    applyScenario, nodeAction, setReadOnly, pingNode,
    fetchGitSha, setPollInterval,
  }
})
