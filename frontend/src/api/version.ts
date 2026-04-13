import { api } from './client'

export interface VersionInfo {
  version: string
}

export type UpdateStatus = 'update_available' | 'up_to_date' | 'registry_unavailable'

export interface UpdateCheckInfo {
  status:          UpdateStatus
  current_version: string
  message:         string
  checked_at:      string | null
}

export const versionApi = {
  getVersion(): Promise<VersionInfo> {
    return api.get<VersionInfo>('/api/version').then(r => r.data)
  },

  checkUpdate(): Promise<UpdateCheckInfo> {
    return api.post<UpdateCheckInfo>('/api/version/check', {}).then(r => r.data)
  },
}
