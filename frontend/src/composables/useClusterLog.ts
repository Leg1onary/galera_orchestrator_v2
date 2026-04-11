// Composable — GET /api/clusters/{id}/log
// ТЗ п.10.1: Overview использует этот эндпоинт для EventLog.
import { computed, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { api } from '@/api/client'
import { onWsEvent } from '@/stores/ws'
import { useSettingsStore } from '@/stores/settings'

// Реальная схема ответа бэкенда
export interface ClusterEvent {
  id: number
  ts: string
  level: string
  source?: string | null
  message: string
  node_id?: number | null
  arbitrator_id?: number | null
  operation_id?: number | null
}

export function useClusterLog(clusterId: Ref<number | null>) {
  const qc            = useQueryClient()
  const settingsStore = useSettingsStore()

  const query = useQuery({
    queryKey: computed(() => ['cluster', clusterId.value, 'log']),
    queryFn: async () => {
      if (!clusterId.value) return []
      const limit = settingsStore.eventLogLimit
      const { data } = await api.get<ClusterEvent[] | { events: ClusterEvent[] }>(
        `/api/clusters/${clusterId.value}/log`,
        { params: { limit } },
      )
      return Array.isArray(data) ? data : data.events
    },
    refetchInterval: computed(() => settingsStore.pollingIntervalSec * 1000),
    staleTime: 5_000,
    enabled: computed(() => !!clusterId.value),
  })

  const unsub = onWsEvent((event) => {
    if (event.cluster_id !== clusterId.value) return
    if (
      event.event === 'log_entry' ||
      event.event === 'operation_finished' ||
      event.event === 'operation_started'
    ) {
      qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'log'] })
    }
  })

  onUnmounted(() => unsub())

  return query
}
