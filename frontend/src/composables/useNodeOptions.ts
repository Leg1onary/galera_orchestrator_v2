// Composable для списка нод кластера — используется во всех диагностических панелях
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/api/client'
import { useClusterStore } from '@/stores/cluster'

export interface NodeOption {
    label: string
    value: number
}

interface NodeShort {
    id: number
    name: string
}

export function useNodeOptions() {
    const clusterStore = useClusterStore()

    const { data } = useQuery({
        queryKey: computed(() => ['cluster-nodes', clusterStore.selectedClusterId]),
        queryFn: () =>
            api
                .get<NodeShort[]>(`/api/clusters/${clusterStore.selectedClusterId}/nodes`)
                .then((r) => r.data),
        enabled: computed(() => !!clusterStore.selectedClusterId),
        staleTime: 30_000,
    })

    const nodeOptions = computed<NodeOption[]>(
        () => (data.value ?? []).map((n) => ({ label: n.name, value: n.id })),
    )

    return { nodeOptions }
}