// ТЗ раздел 11: GET /api/clusters/{id}/topology
// Возвращает структуру для отрисовки топологии: DCs, ноды, арбитраторы, связи.
import { api } from '@/api/client'

export type NodeState =
    | 'Synced'
    | 'Donor/Desynced'
    | 'Joining'
    | 'Joined'
    | 'Error'
    | 'Offline'

export interface TopoNode {
    id: number
    name: string
    host: string
    port: number
    enabled: boolean
    datacenter_id: number | null
    wsrep_local_state_comment: NodeState | null
    wsrep_connected: boolean | null
    wsrep_ready: boolean | null
    read_only: boolean | null
    maintenance: boolean | null
    maintenance_drift: boolean | null
    last_seen: string | null
}

export interface TopoArbitrator {
    id: number
    name: string
    host: string
    port: number
    enabled: boolean
    datacenter_id: number | null
    is_running: boolean | null
    last_seen: string | null
}

export interface TopoDatacenter {
    id: number
    name: string
    nodes: TopoNode[]
    arbitrators: TopoArbitrator[]
}

export interface TopologyData {
    cluster_id: number
    cluster_name: string
    datacenters: TopoDatacenter[]
    // Ноды/арбитраторы без привязки к DC
    unassigned_nodes: TopoNode[]
    unassigned_arbitrators: TopoArbitrator[]
    // Связи: какие ноды connected друг с другом
    // backend отдаёт пары [node_id, node_id] для живых соединений
    connections: [number, number][]
}

export const topologyApi = {
    get: (clusterId: number) =>
        api
            .get<TopologyData>(`/api/clusters/${clusterId}/topology`)
            .then((r) => r.data),
}