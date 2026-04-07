<template>
  <div class="page-topology">
    <!-- SVG topology -->
    <Card class="mb-4">
      <template #header>
        <div class="card-title">
          <i class="pi pi-sitemap" />
          SVG Топология кластера
        </div>
      </template>
      <template #content>
        <TopologySVG :nodes="cluster.nodes" :arbitrators="cluster.arbitrators" />
      </template>
    </Card>

    <!-- wsrep comparison table -->
    <Card>
      <template #header>
        <div class="card-title">
          <i class="pi pi-table" />
          Сравнение wsrep-переменных
        </div>
      </template>
      <template #content>
        <div class="table-wrap">
          <DataTable :value="wsrepRows" size="small" stripedRows
            class="wsrep-table" scrollable scroll-height="500px">
            <Column field="variable" header="Переменная" frozen style="min-width:240px">
              <template #body="{ data }">
                <div class="var-cell">
                  <span>{{ data.variable }}</span>
                  <span v-if="data.hint" class="hint-icon" v-tooltip.right="data.hint">?</span>
                </div>
              </template>
            </Column>
            <Column v-for="node in cluster.nodes" :key="node.id" :header="node.name || node.id">
              <template #body="{ data }">
                <span :class="cellClass(data, node.id)">
                  {{ data.values[node.id] ?? '—' }}
                </span>
              </template>
            </Column>
          </DataTable>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import TopologySVG from '@/components/topology/TopologySVG.vue'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()

const WSREP_VARS = [
  { key: 'wsrep_cluster_status',         hint: 'Статус кластера. Норма: Primary' },
  { key: 'wsrep_cluster_size',            hint: 'Число нод в кластере. Норма: ≥ 3' },
  { key: 'wsrep_local_state_comment',     hint: 'Состояние ноды. Норма: Synced' },
  { key: 'wsrep_flow_control_paused',     hint: 'Доля времени в flow control. Норма: < 0.05' },
  { key: 'wsrep_local_recv_queue',        hint: 'Очередь входящих транзакций. Норма: 0' },
  { key: 'wsrep_local_send_queue',        hint: 'Очередь исходящих транзакций. Норма: 0' },
  { key: 'wsrep_local_cert_failures',     hint: 'Ошибки сертификации. Норма: 0' },
  { key: 'wsrep_bf_aborts',               hint: 'BF-прерывания. Норма: ≈ 0' },
  { key: 'wsrep_last_committed',          hint: 'Последний применённый seqno. Норма: одинаков на всех нодах' },
  { key: 'wsrep_cluster_state_uuid',      hint: 'UUID кластера. Расхождение = Split-Brain!' },
  { key: 'wsrep_connected',               hint: 'Подключение к кластеру. Норма: ON' },
  { key: 'wsrep_ready',                   hint: 'Готовность принимать запросы. Норма: ON' },
  { key: 'wsrep_cluster_conf_id',         hint: 'Конфигурационный ID кластера' },
  { key: 'wsrep_cert_deps_distance',      hint: 'Среднее расстояние сертификационных зависимостей' },
  { key: 'wsrep_local_commits',           hint: 'Число успешных commit (информационно)' },
]

const wsrepRows = computed(() => {
  return WSREP_VARS.map(({ key, hint }) => {
    const values = {}
    cluster.nodes.forEach(n => { values[n.id] = n[key] ?? null })
    return { variable: key, hint, values }
  })
})

function cellClass(row, nodeId) {
  const val = row.values[nodeId]
  if (val == null) return ''
  // Check divergence
  const allVals = Object.values(row.values).filter(v => v != null)
  const unique = new Set(allVals)
  if (unique.size > 1) return 'cell-diverge'
  return ''
}
</script>

<style scoped>
.page-topology { display: flex; flex-direction: column; gap: 1rem; }
.mb-4 { margin-bottom: 1rem; }
.card-title { display: flex; align-items: center; gap: 0.5rem; font-size: 14px; font-weight: 600; padding: 0.875rem 1.25rem; }

.table-wrap { overflow: auto; }
.var-cell { display: flex; align-items: center; gap: 0.375rem; font-family: var(--font-mono); font-size: 12px; }
.hint-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--color-bg-elevated); border: 1px solid var(--color-border);
  font-size: 10px; font-weight: 700; color: var(--color-text-muted);
  cursor: default; flex-shrink: 0;
}
.cell-diverge { color: var(--color-status-error); font-weight: 600; }
</style>
