import { api } from '@/api/client'

// ── Datacenters ────────────────────────────────────────────────────────────
// ТЗ п.2.2: datacenters — только id, name
export interface Datacenter {
    id: number
    name: string
}
export interface DatacenterCreate {
    name: string
}

// ── Clusters ───────────────────────────────────────────────────────────────
// БД: id, name, contour_id, description
// GET /api/settings/clusters также возвращает contour_name (JOIN contours)
export interface ClusterSetting {
    id: number
    name: string
    contour_id: number
    contour_name?: string
    description?: string | null
}
export interface ClusterCreate {
    name: string
    contour_id: number
    description?: string
}
export type ClusterUpdate = Partial<ClusterCreate>

// ── Nodes ──────────────────────────────────────────────────────────────────
// ТЗ п.2.4: id, name, host, port, ssh_port, ssh_user, cluster_id, dc_id, maintenance, enabled
export interface NodeSetting {
    id: number
    name: string
    host: string
    port: number
    ssh_port: number
    ssh_user: string
    enabled: boolean
    dc_id: number | null
    cluster_id: number
}
// ТЗ п.16.1: cluster_id в теле запроса при создании
export interface NodeCreate {
    cluster_id: number
    name: string
    host: string
    port?: number        // default 3306
    ssh_port?: number    // default 22
    ssh_user?: string    // default root
    enabled?: boolean
    dc_id?: number | null
}

// ── Arbitrators ────────────────────────────────────────────────────────────
// ТЗ п.2.5: id, name, host, ssh_port, ssh_user, cluster_id, dc_id, enabled
export interface ArbitratorSetting {
    id: number
    name: string
    host: string
    ssh_port: number
    ssh_user: string
    enabled: boolean
    dc_id: number | null
    cluster_id: number
}
export interface ArbitratorCreate {
    cluster_id: number
    name: string
    host: string
    ssh_port?: number
    ssh_user?: string
    enabled?: boolean
    dc_id?: number | null
}

// ── System settings ────────────────────────────────────────────────────────
// ТЗ п.2.7
export interface SystemSettingsFull {
    id: number
    polling_interval_sec: number
    event_log_limit: number
    timezone: string
    updated_at: string
}
export interface SystemSettingsPatch {
    polling_interval_sec?: number
    event_log_limit?: number
    timezone?: string
}

// ── API ────────────────────────────────────────────────────────────────────
export const settingsApi = {
    // Datacenters — ТЗ п.16.1: /api/settings/datacenters
    listDatacenters: () =>
        api.get<Datacenter[]>('/api/settings/datacenters').then((r) => r.data),
    createDatacenter: (data: DatacenterCreate) =>
        api.post<Datacenter>('/api/settings/datacenters', data).then((r) => r.data),
    updateDatacenter: (id: number, data: Partial<DatacenterCreate>) =>
        api.patch<Datacenter>(`/api/settings/datacenters/${id}`, data).then((r) => r.data),
    deleteDatacenter: (id: number) =>
        api.delete(`/api/settings/datacenters/${id}`),

    // Clusters — ТЗ п.16.1: /api/settings/clusters
    listClusters: (contourId?: number) =>
        api
            .get<ClusterSetting[]>('/api/settings/clusters', {
                params: contourId ? { contour_id: contourId } : {},
            })
            .then((r) => r.data),
    createCluster: (data: ClusterCreate) =>
        api.post<ClusterSetting>('/api/settings/clusters', data).then((r) => r.data),
    updateCluster: (id: number, data: ClusterUpdate) =>
        api.patch<ClusterSetting>(`/api/settings/clusters/${id}`, data).then((r) => r.data),
    deleteCluster: (id: number) =>
        api.delete(`/api/settings/clusters/${id}`),

    // Nodes — ТЗ п.16.1: /api/settings/nodes?cluster_id=N
    listNodes: (clusterId: number) =>
        api
            .get<NodeSetting[]>('/api/settings/nodes', { params: { cluster_id: clusterId } })
            .then((r) => r.data),
    createNode: (data: NodeCreate) =>
        api.post<NodeSetting>('/api/settings/nodes', data).then((r) => r.data),
    updateNode: (nodeId: number, data: Partial<NodeCreate>) =>
        api.patch<NodeSetting>(`/api/settings/nodes/${nodeId}`, data).then((r) => r.data),
    deleteNode: (nodeId: number) =>
        api.delete(`/api/settings/nodes/${nodeId}`),

    // Arbitrators — ТЗ п.16.1: /api/settings/arbitrators?cluster_id=N
    listArbitrators: (clusterId: number) =>
        api
            .get<ArbitratorSetting[]>('/api/settings/arbitrators', {
                params: { cluster_id: clusterId },
            })
            .then((r) => r.data),
    createArbitrator: (data: ArbitratorCreate) =>
        api.post<ArbitratorSetting>('/api/settings/arbitrators', data).then((r) => r.data),
    updateArbitrator: (arbId: number, data: Partial<ArbitratorCreate>) =>
        api.patch<ArbitratorSetting>(`/api/settings/arbitrators/${arbId}`, data).then((r) => r.data),
    deleteArbitrator: (arbId: number) =>
        api.delete(`/api/settings/arbitrators/${arbId}`),

    // System — ТЗ п.16.1: /api/settings/system
    getSystem: () =>
        api.get<SystemSettingsFull>('/api/settings/system').then((r) => r.data),
    patchSystem: (data: SystemSettingsPatch) =>
        api.patch<SystemSettingsFull>('/api/settings/system', data).then((r) => r.data),
}
