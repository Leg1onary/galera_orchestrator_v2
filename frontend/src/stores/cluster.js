import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useClusterStore = defineStore('cluster', () => {
  // ── State ───────────────────────────────────────────────
  const status       = ref(null)
  const contours     = ref({})
  const selection    = ref({ contour: 'test', cluster_index: 0 })
  const activeCluster= ref(null)
  const mode         = ref('mock')          // 'mock' | 'real'
  const scenario     = ref('normal')
  const prefs        = ref({ theme: 'dark', poll_interval: 5 })
  const logs         = ref([])
  const loading      = ref(false)
  const error        = ref(null)
  const version      = ref(null)
  const wsConnected  = ref(false)

  // Sparkline ring-buffers per node
  const sparklines   = ref({})   // { nodeId: { fc: [], rq: [] } }

  // ── Getters ─────────────────────────────────────────────
  const isMock       = computed(() => mode.value === 'mock')
  const nodes        = computed(() => status.value?.nodes || [])
  const arbitrators  = computed(() => status.value?.arbitrators || [])
  const clusterName  = computed(() => status.value?.cluster_name || '—')
  const clusterHealth= computed(() => {
    const s = status.value
    if (!s) return 'unknown'
    if (s.cluster_status === 'Primary' && s.nodes_synced === s.nodes_total) return 'ok'
    if (s.cluster_status !== 'Primary') return 'error'
    return 'warn'
  })

  const contourList  = computed(() => Object.keys(contours.value))
  const currentContourClusters = computed(() => {
    const c = contours.value[selection.value.contour]
    return c || []
  })

  // ── Actions ─────────────────────────────────────────────
  async function fetchStatus() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/api/status')
      applyStatus(data)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function applyStatus(data) {
    status.value = data
    mode.value = data.use_mock ? 'mock' : 'real'
    // Update sparklines
    if (data.nodes) {
      data.nodes.forEach(n => {
        if (!sparklines.value[n.id]) {
          sparklines.value[n.id] = { fc: [], rq: [] }
        }
        const sl = sparklines.value[n.id]
        const fc = parseFloat(n.wsrep_flow_control_paused) || 0
        const rq = parseInt(n.wsrep_local_recv_queue) || 0
        sl.fc.push(fc); if (sl.fc.length > 50) sl.fc.shift()
        sl.rq.push(rq); if (sl.rq.length > 50) sl.rq.shift()
      })
    }
  }

  async function fetchContours() {
    const { data } = await api.get('/api/contours')
    contours.value = data.contours || {}
    selection.value = data.selection || selection.value
    activeCluster.value = data.active_cluster || null
  }

  async function selectContour(contour, cluster_index = 0) {
    await api.post('/api/contours/select', { contour, cluster_index })
    selection.value = { contour, cluster_index }
    await fetchStatus()
  }

  async function selectCluster(idx) {
    await api.post('/api/contours/select', { contour: selection.value.contour, cluster_index: idx })
    selection.value = { ...selection.value, cluster_index: idx }
    await fetchStatus()
  }

  async function toggleMode() {
    const newMode = mode.value === 'mock' ? 'real' : 'mock'
    await api.post('/api/config/mode', { mode: newMode })
    mode.value = newMode
    await fetchStatus()
    await fetchContours()
  }

  async function setMode(m) {
    await api.post('/api/config/mode', { mode: m })
    mode.value = m
    await fetchStatus()
    await fetchContours()
  }

  async function fetchVersion() {
    try {
      const { data } = await api.get('/api/version')
      version.value = data
    } catch {}
  }

  async function fetchLogs() {
    const { data } = await api.get('/api/log')
    logs.value = data.events || []
  }

  async function clearLogs() {
    await api.delete('/api/log')
    logs.value = []
  }

  async function fetchPrefs() {
    try {
      const { data } = await api.get('/api/prefs')
      prefs.value = data
    } catch {}
  }

  async function savePrefs(p) {
    await api.post('/api/prefs', p)
    prefs.value = { ...prefs.value, ...p }
  }

  async function setScenario(name) {
    await api.post(`/api/scenario/${name}`)
    scenario.value = name
    await fetchStatus()
  }

  async function nodeAction(nodeId, action) {
    const { data } = await api.post(`/api/node/${nodeId}/action`, { action })
    await fetchStatus()
    return data
  }

  function addLog(level, message, source = 'ui') {
    logs.value.unshift({ level, message, source, ts: new Date().toISOString() })
    if (logs.value.length > 500) logs.value.pop()
  }

  return {
    status, contours, selection, activeCluster, mode, scenario, prefs,
    logs, loading, error, version, wsConnected, sparklines,
    isMock, nodes, arbitrators, clusterName, clusterHealth,
    contourList, currentContourClusters,
    fetchStatus, applyStatus, fetchContours, selectContour, selectCluster,
    toggleMode, setMode, fetchVersion, fetchLogs, clearLogs,
    fetchPrefs, savePrefs, setScenario, nodeAction, addLog,
  }
})
