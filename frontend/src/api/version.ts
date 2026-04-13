import { apiClient } from './client'

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
    return apiClient.get<VersionInfo>('/version')
  },

  checkUpdate(): Promise<UpdateCheckInfo> {
    return apiClient.post<UpdateCheckInfo>('/version/check', {})
  },
}
