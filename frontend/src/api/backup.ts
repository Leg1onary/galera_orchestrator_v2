import { api } from '@/api/client'

// ── Backup Server ─────────────────────────────────────────────────────────────
export interface BackupServer {
    id:         number
    cluster_id: number
    name:       string
    host:       string
    ssh_port:   number
    ssh_user:   string
    backup_dir: string
    enabled:    boolean
}

export interface BackupServerCreate {
    cluster_id: number
    name:       string
    host:       string
    ssh_port?:  number  // default 22
    ssh_user?:  string  // default root
    backup_dir: string
    enabled?:   boolean
}

export type BackupServerUpdate = Omit<BackupServerCreate, 'cluster_id'>

// ── Scan Response ─────────────────────────────────────────────────────────────
export type BackupType = 'full' | 'schema-only' | 'unknown'
export type BackupTool = 'mysqldump' | 'mariabackup' | 'unknown'

export interface BackupFile {
    filename:    string
    type:        BackupType
    tool:        BackupTool
    size_bytes:  number
    modified_at: string | null
}

export interface BackupScanResult {
    server_id:  number
    backup_dir: string
    scanned_at: string
    files:      BackupFile[]
}

// ── API ────────────────────────────────────────────────────────────────────────
export const backupApi = {
    // Settings CRUD — /api/settings/backup-servers
    listServers: (clusterId: number) =>
        api
            .get<BackupServer[]>('/api/settings/backup-servers', { params: { cluster_id: clusterId } })
            .then((r) => r.data),

    createServer: (data: BackupServerCreate) =>
        api.post<BackupServer>('/api/settings/backup-servers', data).then((r) => r.data),

    updateServer: (id: number, data: BackupServerUpdate) =>
        api.patch<BackupServer>(`/api/settings/backup-servers/${id}`, data).then((r) => r.data),

    deleteServer: (id: number) =>
        api.delete(`/api/settings/backup-servers/${id}`),

    // Scan — /api/clusters/{cluster_id}/backup/scan?server_id={id}
    scan: (clusterId: number, serverId: number) =>
        api
            .get<BackupScanResult>(`/api/clusters/${clusterId}/backup/scan`, {
                params: { server_id: serverId },
            })
            .then((r) => r.data),
}
