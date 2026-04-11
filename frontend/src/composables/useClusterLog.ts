// Composable — GET /api/clusters/{id}/log
// ТЗ п.10.1: Overview использует этот эндпоинт для EventLog.
import { computed, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { api } from '@/api/client'
import { onWsEvent } from '@/stores/ws'
import { useSettingsStore } from '@/stores/settings'
import type { ClusterEvent } from '@/composables/useClusterStatus'

export interface ClusterLogResponse {
  events: ClusterEvent[]
}

export function useClusterLog(clusterId: Ref<number | null>) {
  const qc            = useQueryClient()
  const settingsStore = useSettingsStore()

  const query = useQuery({
    queryKey: computed(() => ['cluster', clusterId.value, 'log']),
    queryFn: async () => {
      if (!clusterId.value) return []
      const limit = settingsStore.eventLogLimit
      const { data } = await api.get<ClusterLogResponse | ClusterEvent[]>(
        `/api/clusters/${clusterId.value}/log`,
        { params: { limit } },
      )
      // DEBUG: убрать после диагностики
      console.log('[useClusterLog] raw response:', JSON.stringify(data).slice(0, 500))
      const items = Array.isArray(data) ? data : data.events
      if (items?.length) {
        console.log('[useClusterLog] first item keys:', Object.keys(items[0]))
        console.log('[useClusterLog] first item:', JSON.stringify(items[0]))
      }
      return items
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
