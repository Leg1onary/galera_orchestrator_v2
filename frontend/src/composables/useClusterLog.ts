// Composable — GET /api/clusters/{id}/log
// ТЗ п.10.1: Overview использует этот эндпоинт для EventLog.
// Таблица event_logs хранит операции оркестратора (recovery, maintenance,
// node actions, auth, diagnostics, ssh) — см. ТЗ п.2.6, п.19.2.
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
      // Бэкенд может вернуть { events: [...] } или сразу [...]
      return Array.isArray(data) ? data : data.events
    },
    refetchInterval: computed(() => settingsStore.pollingIntervalSec * 1000),
    staleTime: 5_000,
    enabled: computed(() => !!clusterId.value),
  })

  // ТЗ п.5.2: инвалидируем лог при появлении новых записей через WS
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
