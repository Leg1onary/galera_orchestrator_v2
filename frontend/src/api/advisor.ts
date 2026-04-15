import { api } from '@/api/client'

export type AdvisorSeverity = 'info' | 'warn' | 'critical'
export type AdvisorCategory =
  | 'config'
  | 'performance'
  | 'replication'
  | 'availability'
  | 'storage'
  | 'sst'
  | 'maintenance'
  | 'security'

export type AdvisorActionType =
  | 'none'
  | 'open_panel'
  | 'node_action'
  | 'recovery_action'
  | 'maintenance_action'
  | 'config_change'

export interface AdvisorEvidence {
  node_ids?: number[] | null
  params?: Record<string, unknown> | null
  raw_refs?: Record<string, unknown>[] | null
}

export interface AdvisorRecommendedAction {
  action_type: AdvisorActionType
  action_id?: string | null
  description?: string | null
  ui_hint?: string | null   // e.g. "open-diagnostics-tab:config-health"
  danger_level?: AdvisorSeverity | null
}

export interface AdvisorCard {
  id: string
  severity: AdvisorSeverity
  category: AdvisorCategory
  source: string
  title: string
  summary: string
  details?: string | null
  evidence?: AdvisorEvidence | null
  recommended_action?: AdvisorRecommendedAction | null
  links?: Record<string, string[]> | null
}

export interface AdvisorResponse {
  cluster_id: number
  generated_at: string
  advisors: AdvisorCard[]
}

export const advisorApi = {
  getAdvisor: (
    clusterId: number,
    severityMin?: AdvisorSeverity,
  ): Promise<AdvisorResponse> =>
    api
      .get<AdvisorResponse>(`/api/clusters/${clusterId}/advisor`, {
        params: severityMin ? { severity_min: severityMin } : {},
      })
      .then((r) => r.data),
}
