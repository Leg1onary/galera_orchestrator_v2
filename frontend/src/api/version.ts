import { apiClient } from './client'

export interface VersionInfo {
  version: string
}

export interface UpdateCheckInfo {
  update_available: boolean
  current_version:  string
  latest_digest:    string | null
  current_digest:   string | null
  checked_at:       string | null
  error:            string | null
}

export const versionApi = {
  getVersion(): Promise<VersionInfo> {
    return apiClient.get<VersionInfo>('/version')
  },

  checkUpdate(): Promise<UpdateCheckInfo> {
    return apiClient.get<UpdateCheckInfo>('/version/check')
  },
}
