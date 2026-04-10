// Composable — инкапсулирует useQuery на GET /api/clusters/{id}/status
// + инвалидацию по WS-событиям node_state_changed / arbitrator_state_changed
import { computed, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { api } from '@/api/client'
import { onWsEvent } from '@/stores/ws'
import { useSettingsStore } from '@/stores/settings'
import type { NodeListItem } from '@/api/nodes'
import type { TopoArbitrator } from '@/api/topology'

export interface ClusterEvent {
  id: number
  created_at: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  node_name?: string | null
}

export interface ClusterStatusResponse {
  cluster_status: string | null       // значение wsrep_cluster_status кластера
  nodes: NodeListItem[]
  arbitrators: TopoArbitrator[]
  recent_events: ClusterEvent[]
}

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
    if (
      event.cluster_id === clusterId.value &&
      (event.event === 'node_state_changed' || event.event === 'arbitrator_state_changed')
    ) {
      qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'status'] })
    }
  })

  onUnmounted(() => unsub())

  return query
}
