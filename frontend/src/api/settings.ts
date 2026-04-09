import { api } from '@/api/client'

// ── Datacenters ────────────────────────────────────────────────────────────
export interface Datacenter {
    id: number
    name: string
    contour_id: number
    description: string | null
}
export interface DatacenterCreate { name: string; contour_id: number; description?: string }

// ── Clusters ───────────────────────────────────────────────────────────────
export interface ClusterSetting {
    id: number
    name: string
    contour_id: number
    description: string | null
    db_host: string
    db_port: number
    db_user: string
    // db_password — write-only, никогда не возвращается из API
}
export interface ClusterCreate {
    name: string
    contour_id: number
    description?: string
    db_host: string
    db_port: number
    db_user: string
    db_password: string
}
export interface ClusterUpdate extends Partial<Omit<ClusterCreate, 'db_password'>> {
    db_password?: string  // опционально при обновлении
}

// ── Nodes ──────────────────────────────────────────────────────────────────
export interface NodeSetting {
    id: number
    name: string
    host: string
    port: number
    ssh_port: number
    ssh_user: string
    enabled: boolean
    datacenter_id: number | null
    cluster_id: number
    description: string | null
}
export interface NodeCreate {
    name: string
    host: string
    port?: number          // default 3306
    ssh_port?: number      // default 22
    ssh_user?: string      // default root
    enabled?: boolean
    datacenter_id?: number | null
    description?: string
}

// ── Arbitrators ────────────────────────────────────────────────────────────
export interface ArbitratorSetting {
    id: number
    name: string
    host: string
    port: number
    ssh_port: number
    ssh_user: string
    enabled: boolean
    datacenter_id: number | null
    cluster_id: number
    description: string | null
}
export interface ArbitratorCreate {
    name: string
    host: string
    port?: number
    ssh_port?: number
    ssh_user?: string
    enabled?: boolean
    datacenter_id?: number | null
    description?: string
}

// ── System settings ────────────────────────────────────────────────────────
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
    // Datacenters
    listDatacenters: () =>
        api.get<Datacenter[]>('/api/datacenters').then((r) => r.data),
    createDatacenter: (data: DatacenterCreate) =>
        api.post<Datacenter>('/api/datacenters', data).then((r) => r.data),
    updateDatacenter: (id: number, data: Partial<DatacenterCreate>) =>
        api.patch<Datacenter>(`/api/datacenters/${id}`, data).then((r) => r.data),
    deleteDatacenter: (id: number) =>
        api.delete(`/api/datacenters/${id}`),

    // Clusters
    listClusters: (contourId?: number) =>
        api.get<ClusterSetting[]>('/api/clusters', { params: contourId ? { contour_id: contourId } : {} })
            .then((r) => r.data),
    createCluster: (data: ClusterCreate) =>
        api.post<ClusterSetting>('/api/clusters', data).then((r) => r.data),
    updateCluster: (id: number, data: ClusterUpdate) =>
        api.patch<ClusterSetting>(`/api/clusters/${id}`, data).then((r) => r.data),
    deleteCluster: (id: number) =>
        api.delete(`/api/clusters/${id}`),

    // Nodes
    listNodes: (clusterId: number) =>
        api.get<NodeSetting[]>(`/api/clusters/${clusterId}/nodes`).then((r) => r.data),
    createNode: (clusterId: number, data: NodeCreate) =>
        api.post<NodeSetting>(`/api/clusters/${clusterId}/nodes`, data).then((r) => r.data),
    updateNode: (clusterId: number, nodeId: number, data: Partial<NodeCreate>) =>
        api.patch<NodeSetting>(`/api/clusters/${clusterId}/nodes/${nodeId}`, data).then((r) => r.data),
    deleteNode: (clusterId: number, nodeId: number) =>
        api.delete(`/api/clusters/${clusterId}/nodes/${nodeId}`),

    // Arbitrators
    listArbitrators: (clusterId: number) =>
        api.get<ArbitratorSetting[]>(`/api/clusters/${clusterId}/arbitrators`).then((r) => r.data),
    createArbitrator: (clusterId: number, data: ArbitratorCreate) =>
        api.post<ArbitratorSetting>(`/api/clusters/${clusterId}/arbitrators`, data).then((r) => r.data),
    updateArbitrator: (clusterId: number, arbId: number, data: Partial<ArbitratorCreate>) =>
        api.patch<ArbitratorSetting>(`/api/clusters/${clusterId}/arbitrators/${arbId}`, data).then((r) => r.data),
    deleteArbitrator: (clusterId: number, arbId: number) =>
        api.delete(`/api/clusters/${clusterId}/arbitrators/${arbId}`),

    // System
    getSystem: () =>
        api.get<SystemSettingsFull>('/api/settings/system').then((r) => r.data),
    patchSystem: (data: SystemSettingsPatch) =>
        api.patch<SystemSettingsFull>('/api/settings/system', data).then((r) => r.data),
}