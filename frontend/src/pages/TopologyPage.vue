<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Топология</h1>
        <p class="page-subtitle">Схема MariaDB Galera Cluster</p>
      </div>
    </div>

    <!-- SVG Topology -->
    <TopologySVG />

    <!-- wsrep comparison table -->
    <h2 class="card-title" style="font-size:var(--text-lg);margin-bottom:var(--space-5)">
      Сравнение wsrep-переменных
    </h2>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Переменная</th>
            <th v-for="node in cluster.nodes" :key="node.id">
              {{ node.name || node.id }}<br>
              <span style="font-weight:400;font-family:var(--font-mono);font-size:0.7rem;color:var(--text-faint)">{{ node.host }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- seqno lag row — always first -->
          <tr>
            <td class="mono">
              ⊿ seqno lag
              <span class="wsrep-hint" data-tip="Разница wsrep_last_committed между нодами. Показывает отставание в транзакциях.">?</span>
            </td>
            <td
              v-for="node in cluster.nodes"
              :key="node.id"
              :class="getSeqnoLagClass(node)"
            >
              {{ getSeqnoLag(node) }}
            </td>
          </tr>
          <!-- wsrep variables -->
          <tr v-for="varName in wsrepVars" :key="varName">
            <td class="mono">
              {{ varName }}
              <span
                v-if="WSREP_HINTS[varName]"
                class="wsrep-hint"
                :data-tip="WSREP_HINTS[varName]"
              >?</span>
            </td>
            <td
              v-for="node in cluster.nodes"
              :key="node.id"
              :class="getVarClass(varName, node)"
            >
              {{ getVar(varName, node) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TopologySVG from '@/components/topology/TopologySVG.vue'
import { useClusterStore } from '@/stores/cluster.js'

const cluster = useClusterStore()

const WSREP_HINTS = {
  'wsrep_cluster_status':      'Primary — кворум есть, запись разрешена. non-Primary — кластер разделён.',
  'wsrep_local_state_comment': 'Synced — нода синхронизирована. Donor — отдаёт SST. Joining — получает данные.',
  'wsrep_cluster_size':        'Количество нод в кластере. Должно совпадать на всех нодах.',
  'wsrep_flow_control_paused': 'Доля времени (0.0–1.0) когда репликация была приостановлена. >0.1 — проблема.',
  'wsrep_local_recv_queue':    'Очередь входящих транзакций. >0 длительно — нода не справляется.',
  'wsrep_local_send_queue':    'Очередь исходящих транзакций. >0 — проблема сети.',
  'wsrep_cert_deps_distance':  'Потенциал параллельного применения транзакций. Чем выше, тем лучше.',
  'wsrep_local_commits':       'Число транзакций подтверждённых на ноде.',
  'wsrep_local_cert_failures': 'Число транзакций отклонённых из-за конфликтов. >0 — конкурирующая запись.',
  'wsrep_bf_aborts':           'Транзакции прерванные BFA. Ненулевое значение — норма при нагрузке.',
  'wsrep_cluster_conf_id':     'Номер конфигурации кластера. Должен совпадать на всех нодах.',
  'wsrep_cluster_state_uuid':  'UUID кластера. Должен совпадать. Расхождение — Split-Brain.',
  'wsrep_connected':           'ON — нода подключена. OFF — изолирована.',
  'wsrep_ready':               'ON — готова обрабатывать запросы. OFF — синхронизируется.',
}

const wsrepVars = [
  'wsrep_cluster_status',
  'wsrep_local_state_comment',
  'wsrep_cluster_size',
  'wsrep_connected',
  'wsrep_ready',
  'wsrep_flow_control_paused',
  'wsrep_local_recv_queue',
  'wsrep_local_send_queue',
  'wsrep_cert_deps_distance',
  'wsrep_local_commits',
  'wsrep_local_cert_failures',
  'wsrep_bf_aborts',
  'wsrep_cluster_conf_id',
  'wsrep_cluster_state_uuid',
]

function getVar(varName, node) {
  const v = node[varName] ?? node.metrics?.[varName]
  if (v === undefined || v === null) return '—'
  return String(v)
}

function getVarClass(varName, node) {
  const v = getVar(varName, node)
  if (varName === 'wsrep_cluster_status')      return v === 'Primary' ? 'ok' : 'error'
  if (varName === 'wsrep_local_state_comment') return v === 'Synced' ? 'ok' : v === 'Donor/Desynced' ? 'warn' : ''
  if (varName === 'wsrep_connected')            return v === 'ON' ? 'ok' : 'error'
  if (varName === 'wsrep_ready')                return v === 'ON' ? 'ok' : 'warn'
  if (varName === 'wsrep_flow_control_paused') return parseFloat(v) > 0.05 ? 'warn' : ''
  if (varName === 'wsrep_local_recv_queue')    return parseInt(v) > 0 ? 'warn' : ''
  if (varName === 'wsrep_local_cert_failures') return parseInt(v) > 0 ? 'warn' : ''
  // Check for cluster-wide inconsistency
  const allVals = cluster.nodes.map(n => getVar(varName, n))
  const allSame = allVals.every(x => x === allVals[0])
  if (!allSame && ['wsrep_cluster_conf_id','wsrep_cluster_state_uuid','wsrep_cluster_size'].includes(varName)) {
    return 'error'
  }
  return ''
}

// Seqno lag helpers
const maxSeqno = computed(() => {
  const seqnos = cluster.nodes.map(n => {
    return parseInt(n.wsrep_last_committed ?? n.metrics?.wsrep_last_committed ?? 0, 10) || 0
  })
  return Math.max(...seqnos, 0)
})

function getSeqnoLag(node) {
  const v = parseInt(node.wsrep_last_committed ?? node.metrics?.wsrep_last_committed ?? 0, 10) || 0
  const lag = maxSeqno.value - v
  return lag === 0 ? '0' : `+${lag}`
}

function getSeqnoLagClass(node) {
  const v = parseInt(node.wsrep_last_committed ?? node.metrics?.wsrep_last_committed ?? 0, 10) || 0
  const lag = maxSeqno.value - v
  if (lag === 0) return 'ok'
  if (lag < 100) return 'warn'
  return 'error'
}
</script>
