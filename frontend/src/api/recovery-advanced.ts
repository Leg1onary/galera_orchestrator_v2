import { api } from '@/api/client'

// ── #3 grastate.dat Inspector ────────────────────────────────────────────────
export type GrastateNodeResult = {
  node_id: number
  node_name: string
  host: string
  raw: string | null
  uuid: string | null
  seqno: number | null
  safe_to_bootstrap: boolean | null
  cert_index: string | null
  gvwstate_exists: boolean
  wsrep_recover_needed: boolean
  error: string | null
}

export type GrastateAnalysis = {
  max_seqno: number | null
  max_seqno_nodes: string[]
  safe_bootstrap_count: number
  safe_bootstrap_nodes: string[]
  dirty_crash_count: number
  warnings: { level: 'danger' | 'warn' | 'info'; message: string }[]
}

export type GrastateResponse = {
  nodes: GrastateNodeResult[]
  analysis: GrastateAnalysis
}

// ── #7 Node State Snapshot ───────────────────────────────────────────────────
export type SnapshotProcessRow = {
  id: string
  user: string
  command: string
  time: string
  state: string
  info: string | null
}

export type SnapshotNodeResult = {
  node_id: number
  node_name: string
  host: string
  ssh_ok: boolean
  db_ok: boolean
  wsrep_status: Record<string, string> | null
  active_transactions: number | null
  top_processes: SnapshotProcessRow[] | null
  disk_free_gb: number | null
  grastate: string | null
  error: string | null
}

export type SnapshotResponse = {
  cluster_id: number
  collected_at: string
  collected_by: string
  nodes: SnapshotNodeResult[]
}

// ── #8 IST vs SST Info ───────────────────────────────────────────────────────
export type IstSstNodeInfo = {
  node_id: number
  node_name: string
  host: string
  wsrep_local_state_comment: string | null
  wsrep_local_cached_downtime: number | null
  gcache_size_bytes: number | null
  gcache_file_size_bytes: number | null
  sst_method: string | null
  wsrep_provider_options: string | null
  ist_likely: boolean | null
  error: string | null
}

export type IstSstResponse = {
  nodes: IstSstNodeInfo[]
}

// ── #6 Split-Brain Recovery ───────────────────────────────────────────────────
export type SplitBrainRequest = {
  trusted_node_id: number
}

// ── #9 Full Cluster Recovery ──────────────────────────────────────────────────
export type FullClusterRequest = {
  node_order: number[]
}

export type FullClusterRecoveryResponse = {
  accepted: boolean
  operation_id: number
  bootstrap_node: string | null
  node_order: number[]
  message: string
}

// ── #11 Flow Control ──────────────────────────────────────────────────────────
export type FlowControlNodeResult = {
  node_id: number
  node_name: string
  host: string
  wsrep_flow_control_paused: number | null
  wsrep_flow_control_sent: number | null
  wsrep_flow_control_recv: number | null
  wsrep_local_recv_queue_avg: number | null
  wsrep_local_send_queue_avg: number | null
  alert: boolean
  error: string | null
}

// ── #14 Cert Conflicts ────────────────────────────────────────────────────────
export type CertConflictNodeResult = {
  node_id: number
  node_name: string
  host: string
  wsrep_local_cert_failures: number | null
  wsrep_local_replays: number | null
  wsrep_cert_deps_distance: number | null
  wsrep_local_bf_aborts: number | null
  alert: boolean
  error: string | null
}

// ── #13 Disk Sentinel ─────────────────────────────────────────────────────────
export type DiskSentinelNodeResult = {
  node_id: number
  node_name: string
  host: string
  gcache_configured_bytes: number | null
  gcache_file_size_bytes: number | null
  ibdata1_size_bytes: number | null
  datadir_free_bytes: number | null
  datadir_total_bytes: number | null
  sst_method: string | null
  alert_free_space: boolean
  alert_gcache_overflow: boolean
  alert_ibdata1_large: boolean
  error: string | null
}

// ── #15 Quorum Status ─────────────────────────────────────────────────────────
export type QuorumNodeStatus = {
  node_id: number
  node_name: string
  host: string
  wsrep_cluster_status: string | null
  wsrep_cluster_size: number | null
  wsrep_local_state_comment: string | null
  wsrep_connected: string | null
  error: string | null
}

export type QuorumStatusResponse = {
  cluster_id: number
  total_configured: number
  primary_count: number
  non_primary_count: number
  offline_count: number
  cluster_size: number | null
  quorum_ok: boolean
  status: 'healthy' | 'degraded' | 'critical'
  nodes: QuorumNodeStatus[]
}

// ── wsrep-recover result ──────────────────────────────────────────────────────
export type WsrepRecoverResult = {
  node_id: number
  node_name: string
  recovered_uuid: string | null
  recovered_seqno: number | null
  raw_output: string
  patched_grastate: boolean
  error: string | null
}

// ── API object ────────────────────────────────────────────────────────────────
export const recoveryAdvancedApi = {
  // #3
  getGrastate: (clusterId: number): Promise<GrastateResponse> =>
    api.get<GrastateResponse>(`/api/clusters/${clusterId}/recovery/grastate`).then(r => r.data),

  // #7
  takeSnapshot: (clusterId: number): Promise<SnapshotResponse> =>
    api.post<SnapshotResponse>(`/api/clusters/${clusterId}/recovery/snapshot`).then(r => r.data),

  // #8
  getIstSstInfo: (clusterId: number): Promise<IstSstResponse> =>
    api.get<IstSstResponse>(`/api/clusters/${clusterId}/recovery/ist-sst-info`).then(r => r.data),

  // #6
  startSplitBrainRecovery: (clusterId: number, body: SplitBrainRequest) =>
    api.post<{ accepted: boolean; operation_id: number }>(
      `/api/clusters/${clusterId}/recovery/split-brain`, body
    ).then(r => r.data),

  // #9 — body is optional; if omitted, backend auto-detects bootstrap node via grastate.dat
  startFullClusterRecovery: (clusterId: number, body?: FullClusterRequest) =>
    api.post<{ accepted: boolean; operation_id: number; bootstrap_node?: string; node_order?: number[] }>(
      `/api/clusters/${clusterId}/recovery/full-cluster`, body ?? {}
    ).then(r => r.data),

  // #11
  getFlowControl: (clusterId: number): Promise<FlowControlNodeResult[]> =>
    api.get<FlowControlNodeResult[]>(`/api/clusters/${clusterId}/diagnostics/flow-control`).then(r => r.data),

  // #14
  getCertConflicts: (clusterId: number): Promise<CertConflictNodeResult[]> =>
    api.get<CertConflictNodeResult[]>(`/api/clusters/${clusterId}/diagnostics/cert-conflicts`).then(r => r.data),

  // #13
  getDiskSentinel: (clusterId: number): Promise<DiskSentinelNodeResult[]> =>
    api.get<DiskSentinelNodeResult[]>(`/api/clusters/${clusterId}/diagnostics/disk-sentinel`).then(r => r.data),

  // #15
  getQuorumStatus: (clusterId: number): Promise<QuorumStatusResponse> =>
    api.get<QuorumStatusResponse>(`/api/clusters/${clusterId}/diagnostics/quorum-status`).then(r => r.data),

  // wsrep-recover: run on a node with seqno=-1, patches grastate.dat automatically
  runWsrepRecover: (clusterId: number, nodeId: number): Promise<WsrepRecoverResult> =>
    api.post<WsrepRecoverResult>(`/api/clusters/${clusterId}/recovery/wsrep-recover/${nodeId}`).then(r => r.data),
}
