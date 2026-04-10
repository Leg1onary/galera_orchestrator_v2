// ТЗ раздел 12: Topology — данные из трёх endpoint'ов
// GET /api/clusters/{id}/status
// GET /api/clusters/{id}/nodes
// GET /api/clusters/{id}/arbitrators
// Отдельного /topology endpoint'а нет — TopologyCanvas собирает данные на фронте.
import type { NodeListItem } from '@/api/nodes'

// ТЗ п.7.2/7.3: сырое значение wsrep_local_state_comment из MariaDB
// Возможные значения: 'Synced', 'Donor/Desynced', 'Joining', 'Joined', 'Disconnected'
// null — нода недоступна (SSH/DB down) — визуально OFFLINE
export type WsrepStateComment =
    | 'Synced'
    | 'Donor/Desynced'
    | 'Joining'
    | 'Joined'
    | 'Disconnected'
    | null

// ТЗ п.7.3: визуальный статус ноды (computed на фронте из live-полей)
// BLOCKER FIX: 'Error' и кастомный 'Offline' — не wsrep значения
export type NodeVisualStatus =
    | 'SYNCED'        // wsrep_local_state_comment='Synced', read_only=false
    | 'SYNCED_RO'     // wsrep_local_state_comment='Synced', read_only=true
    | 'DONOR'         // 'Donor/Desynced'
    | 'JOINER'        // 'Joining' | 'Joined'
    | 'DESYNCED'      // wsrep_ready=false
    | 'OFFLINE'       // нода недоступна (нет live данных / SSH down)

// ТЗ п.9.2: структура арбитратора из GET /api/clusters/{id}/arbitrators
export interface TopoArbitrator {
    id: number
    name: string
    host: string
    ssh_port: number             // MAJOR FIX: ssh_port, не port
    enabled: boolean
    dc_id: number | null         // MINOR FIX: dc_id, не datacenter_id
    // live-поля (ТЗ п.7.4)
    state: 'online' | 'degraded' | 'offline' | null
    ssh_ok: boolean | null
    garbd_running: boolean | null  // MAJOR FIX: garbd_running, не is_running
    latency_ssh_ms: number | null
    last_check_ts: string | null   // MINOR FIX: last_check_ts, не last_seen
}

// TopoNode — переиспользуем NodeListItem из api/nodes.ts
// (содержит все нужные live-поля ТЗ п.7.2)
export type { NodeListItem as TopoNode } from '@/api/nodes'

// Структура для TopologyCanvas — собирается на фронте
// из /status + /nodes + /arbitrators
export interface TopoDatacenter {
    id: number
    name: string
    nodes: NodeListItem[]
    arbitrators: TopoArbitrator[]
}

// ТЗ п.12.3: итоговая модель для TopologyCanvas
// Собирается в stores/cluster или TopologyPage из трёх API-ответов
export interface TopologyViewModel {
    cluster_id: number
    cluster_name: string
    datacenters: TopoDatacenter[]
    unassigned_nodes: NodeListItem[]
    unassigned_arbitrators: TopoArbitrator[]
    // [не в ТЗ] connections убраны — связи строятся логически на фронте
}

// ТЗ п.9.2: отдельный API-метод только для арбитраторов кластера
// /nodes и /status уже есть в nodesApi и clusterApi — не дублируем
import { api } from '@/api/client'

export const topologyApi = {
    // ТЗ п.9.2: GET /api/clusters/{cluster_id}/arbitrators
    getArbitrators: (clusterId: number) =>
        api
            .get<TopoArbitrator[]>(`/api/clusters/${clusterId}/arbitrators`)
            .then((r) => r.data),
}