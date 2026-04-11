// Composable — инкапсулирует useQuery на GET /api/clusters/{id}/status
// + инвалидацию по WS-событиям node_state_changed / operation_finished
import { computed, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { api } from '@/api/client'
import { onWsEvent } from '@/stores/ws'
import { useSettingsStore } from '@/stores/settings'
import type { NodeStatusItem } from '@/api/nodes'
import type { TopoArbitrator } from '@/api/topology'

export interface ClusterEvent {
  id: number
  created_at: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  node_name?: string | null
}

// Точная схема GET /api/clusters/{id}/status
export interface ClusterStatusResponse {
  id: number
  name: string
  contour: string
  status: string | null
  primary: boolean
  wsrep_cluster_size: number | null
  online_nodes: number
  total_nodes: number
  online_arbitrators: number
  total_arbitrators: number
  has_live_data: boolean
  last_update_ts: string | null
  nodes: NodeStatusItem[]
  arbitrators: TopoArbitrator[]
  active_operation: unknown | null
}

// WS-события, триггерящие инвалидацию статуса кластера
const STATUS_INVALIDATE_EVENTS = new Set([
  'node_state_changed',
  'arbitrator_state_changed',
  // fix: после завершения операции (stop/start/restart) нода
  // не меняет wsrep-статус мгновенно — поллер подтянет новое состояние
  // только когда придёт operation_finished и мы форсируем рефетч
  'operation_finished',
  'operation_started',
])

export function useClusterStatus(clusterId: Ref<number | null>) {
  const qc             = useQueryClient()
  const settingsStore  = useSettingsStore()

  const query = useQuery({
    queryKey: computed(() => ['cluster', clusterId.value, 'status']),
    queryFn: () => {
      if (!clusterId.value) return Promise.resolve(null)
      return api
        .get<ClusterStatusResponse>(`/api/clusters/${clusterId.value}/status`)
        .then((r) => r.data)
    },
    refetchInterval: computed(() => settingsStore.pollingIntervalSec * 1000),
    staleTime: 5_000,
    enabled: computed(() => !!clusterId.value),
  })

  const unsub = onWsEvent((event) => {
    if (event.cluster_id !== clusterId.value) return
    if (STATUS_INVALIDATE_EVENTS.has(event.event)) {
      qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'status'] })
    }
  })

  onUnmounted(() => unsub())

  return query
}
