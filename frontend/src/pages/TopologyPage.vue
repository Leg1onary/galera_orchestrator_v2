<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import DataTable from 'primevue/datatable'
import Column    from 'primevue/column'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'
import NodeDetailDrawer from '@/components/nodes/NodeDetailDrawer.vue'
import type { NodeListItem } from '@/api/nodes'

// ── Types ─────────────────────────────────────────────────────────────────────
interface NodeLive {
  id: number
  name: string
  host: string
  port: number
  dc_id: number | null
  dc_name: string | null
  wsrep_local_state_comment: string | null
  wsrep_ready: string | null
  wsrep_flow_control_paused: number | null
  wsrep_local_recv_queue: number | null
  ssh_ok: boolean
  readonly: boolean
  maintenance: boolean
  maintenance_drift: boolean
  live: {
    wsrep_local_state_comment: string | null
    wsrep_ready: string | null
    wsrep_flow_control_paused: number | null
    wsrep_local_recv_queue: number | null
    wsrep_incoming_addresses: string | null
    ssh_ok: boolean
    readonly: boolean
    maintenance_drift: boolean
    db_ok: boolean
    ssh_latency_ms: number | null
    db_latency_ms: number | null
    error: string | null
  } | null
}

interface ArbLive {
  id: number
  name: string
  host: string
  dc_id: number | null
  dc_name: string | null
  live: {
    ssh_ok: boolean
    garbd_running: boolean
    ssh_latency_ms: number | null
    state: string
    error: string | null
  } | null
}

interface DCGroup {
  dcId: number | null
  dcName: string
  nodes: NodeLive[]
  arbs: ArbLive[]
}

// ── Layout constants ──────────────────────────────────────────────────────────
const DC_W    = 560
const DC_PAD  = 24
const DC_GAP  = 80
const B_W     = 240
const B_H     = 130
const B_ARB_H = 100
const B_GAP   = 30
const TOP_OFF = 40
const SIDE    = 24
const ARC_TOP = 80

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId!)
const { data, isLoading } = useClusterStatus(clusterId)

interface NodeNorm {
  id: number
  name: string
  host: string
  port: number
  dc_id: number | null
  dc_name: string | null
  maintenance: boolean
  ssh_ok: boolean
  db_ok: boolean
  wsrep_local_state_comment: string | null
  wsrep_ready: string | null
  wsrep_flow_control_paused: number | null
  wsrep_local_recv_queue: number | null
  wsrep_incoming_addresses: string
  readonly: boolean
  maintenance_drift: boolean
  ssh_latency_ms: number | null
  db_latency_ms: number | null
  error: string | null
}

interface ArbNorm {
  id: number
  name: string
  host: string
  dc_id: number | null
  dc_name: string | null
  ssh_ok: boolean
  garbd_running: boolean
  ssh_latency_ms: number | null
}

const nodes = computed<NodeNorm[]>(() =>
  (data.value?.nodes ?? []).map((n: NodeLive) => ({
    id:           n.id,
    name:         n.name,
    host:         n.host,
    port:         n.port,
    dc_id:        n.dc_id,
    dc_name:      n.dc_name,
    maintenance:  n.maintenance,
    ssh_ok:                    n.live?.ssh_ok                    ?? false,
    db_ok:                     n.live?.db_ok                     ?? false,
    wsrep_local_state_comment: n.live?.wsrep_local_state_comment ?? null,
    wsrep_ready:               n.live?.wsrep_ready               ?? null,
    wsrep_flow_control_paused: n.live?.wsrep_flow_control_paused ?? null,
    wsrep_local_recv_queue:    n.live?.wsrep_local_recv_queue    ?? null,
    wsrep_incoming_addresses:  n.live?.wsrep_incoming_addresses  ?? '',
    readonly:                  n.live?.readonly                  ?? false,
    maintenance_drift:         n.live?.maintenance_drift         ?? false,
    ssh_latency_ms:            n.live?.ssh_latency_ms            ?? null,
    db_latency_ms:             n.live?.db_latency_ms             ?? null,
    error:                     n.live?.error                     ?? null,
  }))
)

const arbitrators = computed<ArbNorm[]>(() =>
  (data.value?.arbitrators ?? []).map((a: ArbLive) => ({
    id:             a.id,
    name:           a.name,
    host:           a.host,
    dc_id:          a.dc_id,
    dc_name:        a.dc_name,
    ssh_ok:         a.live?.ssh_ok         ?? false,
    garbd_running:  a.live?.garbd_running  ?? false,
    ssh_latency_ms: a.live?.ssh_latency_ms ?? null,
  }))
)

// ── NodeDetailDrawer ──────────────────────────────────────────────────────────
const drawerNode = ref<NodeListItem | null>(null)

function nodeNormToListItem(n: NodeNorm): NodeListItem {
  return {
    id:              n.id,
    name:            n.name,
    host:            n.host,
    port:            n.port,
    ssh_port:        22,
    ssh_user:        '',
    db_user:         '',
    enabled:         true,
    maintenance:     n.maintenance,
    datacenter_id:   n.dc_id,
    datacenter_name: n.dc_name,
    cluster_id:      clusterId.value,
    live: n.ssh_ok || n.db_ok ? {
      wsrep_cluster_status:      null,
      wsrep_cluster_size:        null,
      wsrep_connected:           null,
      wsrep_ready:               n.wsrep_ready,
      wsrep_local_state_comment: n.wsrep_local_state_comment,
      wsrep_local_recv_queue:    n.wsrep_local_recv_queue,
      wsrep_local_send_queue:    null,
      wsrep_flow_control_paused: n.wsrep_flow_control_paused,
      readonly:                  n.readonly,
      maintenance_drift:         n.maintenance_drift,
      ssh_ok:                    n.ssh_ok,
      db_ok:                     n.db_ok,
      ssh_latency_ms:            n.ssh_latency_ms,
      db_latency_ms:             n.db_latency_ms,
      error:                     n.error,
      last_check_ts:             null,
      flow_control_history:      [],
      recv_queue_history:        [],
    } : null,
  }
}

function openDrawer(nodeId: number) {
  const found = nodes.value.find(n => n.id === nodeId)
  drawerNode.value = found
    ? nodeNormToListItem(found)
    : {
        id: nodeId, name: '', host: '', port: 3306,
        ssh_port: 22, ssh_user: '', db_user: '',
        enabled: true, maintenance: false,
        datacenter_id: null, datacenter_name: null,
        cluster_id: clusterId.value, live: null,
      }
}
function closeDrawer() { drawerNode.value = null }

// ── Header stats ──────────────────────────────────────────────────────────────
const syncedCount = computed(() =>
  nodes.value.filter(n => n.ssh_ok && (n.wsrep_local_state_comment ?? '').toUpperCase() === 'SYNCED').length
)

// ── DC groups ─────────────────────────────────────────────────────────────────
const dcGroups = computed<DCGroup[]>(() => {
  const map = new Map<string, DCGroup>()
  for (const n of nodes.value) {
    const key = n.dc_id != null ? String(n.dc_id) : '__none__'
    if (!map.has(key)) map.set(key, { dcId: n.dc_id, dcName: n.dc_name ?? 'No DC', nodes: [], arbs: [] })
    map.get(key)!.nodes.push(n as unknown as NodeLive)
  }
  for (const a of arbitrators.value) {
    const key = a.dc_id != null ? String(a.dc_id) : '__none__'
    if (!map.has(key)) map.set(key, { dcId: a.dc_id, dcName: a.dc_name ?? 'No DC', nodes: [], arbs: [] })
    map.get(key)!.arbs.push(a as unknown as ArbLive)
  }
  return Array.from(map.values())
})

function dcHeight(dc: DCGroup): number {
  const nodeRows = Math.ceil(dc.nodes.length / 2)
  const nodesH   = nodeRows * (B_H + B_GAP)
  const arbsH    = dc.arbs.length * (B_ARB_H + B_GAP)
  return TOP_OFF + 8 + nodesH + arbsH + SIDE
}

const svgViewH = computed(() =>
  ARC_TOP + Math.max(...(dcGroups.value.length ? dcGroups.value.map(dcHeight) : [200])) + 24
)
const svgViewW = computed(() =>
  Math.max(dcGroups.value.length * (DC_W + DC_GAP) + DC_PAD * 2, 400)
)

function dcX(di: number)  { return DC_PAD + di * (DC_W + DC_GAP) }
function badgeX(di: number, ni: number) { return dcX(di) + SIDE + (ni % 2) * (B_W + B_GAP) }
function badgeY(ni: number) { return ARC_TOP + TOP_OFF + 10 + Math.floor(ni / 2) * (B_H + B_GAP) }
function arbBadgeY(dc: DCGroup, ai: number) {
  return ARC_TOP + TOP_OFF + 10 + Math.ceil(dc.nodes.length / 2) * (B_H + B_GAP) + ai * (B_ARB_H + B_GAP)
}

// ── Connection lines ──────────────────────────────────────────────────────────
function parseIncomingHosts(raw: string): Set<string> {
  if (!raw || raw === '0.0.0.0') return new Set()
  return new Set(
    raw.split(',').map(s => s.trim().split(':')[0]).filter(Boolean)
  )
}

interface ConnectionLine {
  x1: number; y1: number
  x2: number; y2: number
  style: 'synced' | 'active' | 'offline'
}

function nodeBadgeAnchor(nodeId: number): { x: number; y: number } | null {
  for (let di = 0; di < dcGroups.value.length; di++) {
    const dc = dcGroups.value[di]
    const ni = (dc.nodes as unknown as NodeNorm[]).findIndex(n => n.id === nodeId)
    if (ni === -1) continue
    return {
      x: badgeX(di, ni) + B_W / 2,
      y: badgeY(ni) + 4,
    }
  }
  return null
}

function arcPath(x1: number, y1: number, x2: number, y2: number): string {
  const mx   = (x1 + x2) / 2
  const dx   = Math.abs(x2 - x1)
  const dy   = Math.abs(y2 - y1)
  const dist = Math.sqrt(dx * dx + dy * dy)
  const sag  = Math.max(50, dist * 0.4)
  const cy   = Math.min(y1, y2) - sag
  return `M${x1},${y1} Q${mx},${cy} ${x2},${y2}`
}

const connectionLines = computed<ConnectionLine[]>(() => {
  const allNodes = nodes.value
  const lines: ConnectionLine[] = []
  const seen = new Set<string>()

  for (const nodeA of allNodes) {
    const peersOfA = parseIncomingHosts(nodeA.wsrep_incoming_addresses)
    if (!peersOfA.size) continue

    for (const nodeB of allNodes) {
      if (nodeA.id === nodeB.id) continue
      if (!peersOfA.has(nodeB.host)) continue

      const pairKey = [nodeA.id, nodeB.id].sort((a, b) => a - b).join('-')
      if (seen.has(pairKey)) continue
      seen.add(pairKey)

      const cA = nodeBadgeAnchor(nodeA.id)
      const cB = nodeBadgeAnchor(nodeB.id)
      if (!cA || !cB) continue

      const aState = (nodeA.wsrep_local_state_comment ?? '').toUpperCase()
      const bState = (nodeB.wsrep_local_state_comment ?? '').toUpperCase()
      let style: ConnectionLine['style'] = 'active'
      if (!nodeA.ssh_ok || !nodeB.ssh_ok || aState === 'OFFLINE' || bState === 'OFFLINE') {
        style = 'offline'
      } else if (aState === 'SYNCED' && bState === 'SYNCED') {
        style = 'synced'
      }

      lines.push({ x1: cA.x, y1: cA.y, x2: cB.x, y2: cB.y, style })
    }
  }
  return lines
})

function nodeSSHOk(n: unknown): boolean     { return (n as NodeNorm).ssh_ok }
function nodeState(n: unknown): string|null { return (n as NodeNorm).wsrep_local_state_comment }
function nodeReady(n: unknown): string|null { return (n as NodeNorm).wsrep_ready }
function nodeRO(n: unknown): boolean        { return (n as NodeNorm).readonly }
function nodeMaint(n: unknown): boolean     { return (n as NodeNorm).maintenance }
function nodeDrift(n: unknown): boolean     { return (n as NodeNorm).maintenance_drift }

function arbSSHOk(a: unknown): boolean  { return (a as ArbNorm).ssh_ok }
function arbGarbd(a: unknown): boolean  { return (a as ArbNorm).garbd_running }

function nodeColor(n: unknown): string {
  const s = (nodeState(n) ?? '').toUpperCase()
  if (!nodeSSHOk(n) || s === 'OFFLINE') return 'var(--color-offline)'
  if (nodeReady(n) === 'OFF')           return 'var(--color-degraded)'
  if (s === 'SYNCED' && nodeRO(n))      return 'var(--color-readonly)'
  if (s === 'SYNCED')                   return 'var(--color-synced)'
  if (s === 'DONOR' || s === 'JOINER' || s === 'DESYNCED') return 'var(--color-donor)'
  return 'var(--color-text-faint)'
}

function arbColor(a: unknown): string {
  if (!arbSSHOk(a)) return 'var(--color-offline)'
  if (!arbGarbd(a)) return 'var(--color-degraded)'
  return 'var(--color-synced)'
}

function nodeStatLabel(n: unknown): string {
  const s = (nodeState(n) ?? '').toUpperCase()
  if (!nodeSSHOk(n))          return 'OFFLINE'
  if (nodeReady(n) === 'OFF') return 'DEGRADED'
  return s || '\u2014'
}
function arbStatLabel(a: unknown): string {
  if (!arbSSHOk(a)) return 'OFFLINE'
  if (!arbGarbd(a)) return 'DEGRADED'
  return 'ONLINE'
}

// ── Tooltip ───────────────────────────────────────────────────────────────────
const tooltip = ref<{ node?: NodeNorm; arb?: ArbNorm; x: number; y: number } | null>(null)
function showNodeTip(e: MouseEvent, n: NodeNorm) { tooltip.value = { node: n, x: e.clientX, y: e.clientY } }
function showArbTip(e: MouseEvent, a: ArbNorm)   { tooltip.value = { arb:  a, x: e.clientX, y: e.clientY } }
function hideTip() { tooltip.value = null }

function onScroll() { tooltip.value = null }
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <div class="topology-page anim-fade-in" @mouseleave="hideTip">

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <template v-else>
      <!-- HEADER -->
      <div class="pg-head">
        <div class="pg-head-icon"><i class="pi pi-sitemap" /></div>
        <div class="pg-head-body">
          <div class="pg-head-top">
            <h1 class="pg-title">Topology</h1>
            <div class="topo-header-stats">
              <span class="stat-chip stat-chip--synced">
                <span class="stat-dot" style="background:var(--color-synced)"/>
                {{ syncedCount }} / {{ nodes.length }} SYNCED
              </span>
              <span v-if="arbitrators.length" class="stat-chip">
                <span class="stat-dot" style="background:var(--color-text-faint)"/>
                {{ arbitrators.filter(a => a.ssh_ok).length }} / {{ arbitrators.length }} ARB
              </span>
              <span v-if="connectionLines.length" class="stat-chip">
                <span class="stat-dot" style="background:var(--color-primary)"/>
                {{ connectionLines.filter(l => l.style === 'synced').length }} / {{ connectionLines.length }} links
              </span>
            </div>
          </div>
          <p class="pg-desc">Visual map of cluster nodes, datacenters, and replication links.</p>
        </div>
      </div>

      <!-- LOADING — canvas skeleton -->
      <div v-if="isLoading" class="topo-canvas-skeleton">
        <div class="tcs-inner">
          <div class="tcs-zone" v-for="i in 2" :key="i">
            <Skeleton height="1rem" width="7rem" />
            <Skeleton height="130px" />
            <Skeleton height="130px" />
          </div>
        </div>
      </div>

      <template v-else>
        <!-- CANVAS -->
        <div class="topo-canvas-wrap">
          <svg
            class="topo-svg"
            xmlns="http://www.w3.org/2000/svg"
            :viewBox="`0 0 ${svgViewW} ${svgViewH}`"
            :width="svgViewW"
            :height="svgViewH"
            preserveAspectRatio="xMinYMin meet"
          >
            <defs>
              <filter id="glow-synced"  x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b"/>
                <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="glow-offline" x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b"/>
                <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="glow-line-synced" x="-40%" y="-200%" width="180%" height="500%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="b"/>
                <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="glow-line-active" x="-40%" y="-200%" width="180%" height="500%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b"/>
                <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>

            <!-- DC zones + badges -->
            <g v-for="(dc, di) in dcGroups" :key="di">
              <rect
                :x="dcX(di)" :y="ARC_TOP + 4"
                :width="DC_W" :height="dcHeight(dc)"
                rx="10" ry="10"
                class="dc-zone-rect"
              />
              <text :x="dcX(di) + SIDE" :y="ARC_TOP + 22" class="dc-zone-label">
                {{ dc.dcName.toUpperCase() }}
              </text>

              <g
                v-for="(node, ni) in dc.nodes" :key="(node as any).id"
                :transform="`translate(${badgeX(di, ni)}, ${badgeY(ni)})`"
                class="topo-badge topo-badge--clickable"
                @mouseenter="(e) => showNodeTip(e, node as unknown as NodeNorm)"
                @mouseleave="hideTip"
                @click="openDrawer((node as any).id)"
              >
                <rect x="0" y="0" :width="B_W" :height="B_H" rx="10" class="badge-bg" />
                <rect
                  x="0" y="0" :width="B_W" height="6" rx="4"
                  :fill="nodeColor(node)"
                  :filter="nodeSSHOk(node) && nodeState(node)?.toUpperCase() === 'SYNCED' ? 'url(#glow-synced)' : undefined"
                />
                <circle
                  cx="18" cy="30" r="6"
                  :fill="nodeColor(node)"
                  :filter="!nodeSSHOk(node) ? 'url(#glow-offline)' : undefined"
                  :class="{ 'dot-pulse': !nodeSSHOk(node) }"
                />
                <text x="32" y="35" class="badge-name">{{ (node as any).name }}</text>
                <text x="10" y="54" class="badge-host">{{ (node as any).host }}:{{ (node as any).port }}</text>
                <text x="10" y="76" class="badge-state" :fill="nodeColor(node)">{{ nodeStatLabel(node) }}</text>
                <rect x="10" y="88" width="48" height="22" rx="5"
                  :fill="nodeRO(node) ? 'color-mix(in oklch, var(--color-readonly) 15%, transparent)' : 'color-mix(in oklch, var(--color-synced) 12%, transparent)'"
                />
                <text x="34" y="103" class="badge-pill"
                  :fill="nodeRO(node) ? 'var(--color-readonly)' : 'var(--color-synced)'"
                >{{ nodeRO(node) ? 'RO' : 'RW' }}</text>
                <rect
                  v-if="nodeMaint(node)"
                  x="64" y="88" width="62" height="22" rx="5"
                  fill="color-mix(in oklch, var(--color-degraded) 12%, transparent)"
                />
                <text
                  v-if="nodeMaint(node)"
                  x="95" y="103" class="badge-pill"
                  fill="var(--color-degraded)"
                >MAINT</text>
                <circle
                  v-if="nodeDrift(node)"
                  :cx="B_W - 10" :cy="B_H - 10" r="5"
                  fill="var(--color-offline)"
                />
                <text :x="B_W - 12" y="20" class="badge-open-hint">⤢</text>
              </g>

              <g
                v-for="(arb, ai) in dc.arbs" :key="`arb-${(arb as any).id}`"
                :transform="`translate(${dcX(di) + SIDE}, ${arbBadgeY(dc, ai)})`"
                class="topo-badge topo-badge--arb"
                @mouseenter="(e) => showArbTip(e, arb as unknown as ArbNorm)"
                @mouseleave="hideTip"
              >
                <rect x="0" y="0" :width="B_W" :height="B_ARB_H" rx="10" class="badge-bg badge-bg--arb" />
                <rect x="0" y="0" :width="B_W" height="5" rx="4" :fill="arbColor(arb)" />
                <circle cx="18" cy="30" r="5" :fill="arbColor(arb)" />
                <text x="32" y="35" class="badge-name">{{ (arb as any).name }}</text>
                <text x="10" y="54" class="badge-host">{{ (arb as any).host }}</text>
                <text x="10" y="76" class="badge-state" :fill="arbColor(arb)">{{ arbStatLabel(arb) }}</text>
              </g>
            </g>

            <!-- Arcs — LAST (SVG z-order) -->
            <g class="conn-layer">
              <path
                v-for="(line, i) in connectionLines"
                :key="`conn-${i}`"
                :d="arcPath(line.x1, line.y1, line.x2, line.y2)"
                class="topo-arc"
                :class="`topo-arc--${line.style}`"
                :filter="line.style === 'synced' ? 'url(#glow-line-synced)' : line.style === 'active' ? 'url(#glow-line-active)' : undefined"
              />
            </g>
          </svg>
        </div>

        <!-- LEGEND -->
        <div class="topo-legend">
          <span class="legend-title">Legend</span>
          <div class="legend-items">
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-synced)"/><span>SYNCED RW</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-readonly)"/><span>SYNCED RO</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-donor)"/><span>DONOR / JOINER</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-degraded)"/><span>wsrep_ready=OFF</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-offline)"/><span>OFFLINE</span></div>
            <div class="legend-item legend-item--conn"><span class="legend-arc legend-arc--synced"/><span>Both SYNCED</span></div>
            <div class="legend-item legend-item--conn"><span class="legend-arc legend-arc--active"/><span>Connected</span></div>
            <div class="legend-item legend-item--conn"><span class="legend-arc legend-arc--offline"/><span>Peer offline</span></div>
            <div class="legend-item legend-item--hint"><span class="legend-icon">⤢</span><span>Click badge → details</span></div>
          </div>
        </div>

        <!-- NODES TABLE -->
        <div class="node-table-wrap">
          <div class="node-table-header">
            <span class="node-table-title">Nodes</span>
            <span class="node-table-count">{{ nodes.length }}</span>
          </div>
          <DataTable
            :value="nodes"
            class="topo-dt"
            :row-hover="true"
            :row-class="() => 'node-row--clickable'"
            size="small"
            @row-click="(e) => openDrawer(e.data.id)"
          >
            <Column header="Node" style="min-width:160px">
              <template #body="{ data: n }">
                <div class="cell-name">
                  <span
                    class="status-dot"
                    :class="{ 'status-dot--pulse': !n.ssh_ok }"
                    :style="{ background: nodeColor(n), boxShadow: `0 0 6px ${nodeColor(n)}` }"
                  />
                  <span class="name-text">{{ n.name }}</span>
                  <span v-if="n.maintenance" class="maint-badge">MAINT</span>
                </div>
              </template>
            </Column>
            <Column header="Host">
              <template #body="{ data: n }">
                <span class="cell-mono">{{ n.host }}:{{ n.port }}</span>
              </template>
            </Column>
            <Column header="State">
              <template #body="{ data: n }">
                <span class="cell-state" :style="{ color: nodeColor(n) }">{{ nodeStatLabel(n) }}</span>
              </template>
            </Column>
            <Column header="DC">
              <template #body="{ data: n }">
                <span class="cell-muted">{{ n.dc_name ?? '\u2014' }}</span>
              </template>
            </Column>
            <Column header="Mode">
              <template #body="{ data: n }">
                <span class="mode-pill" :class="n.readonly ? 'mode-ro' : 'mode-rw'">{{ n.readonly ? 'RO' : 'RW' }}</span>
              </template>
            </Column>
            <Column header="SSH">
              <template #body="{ data: n }">
                <span class="ssh-cell" :class="n.ssh_ok ? 'ssh-ok' : 'ssh-fail'">
                  <i :class="n.ssh_ok ? 'pi pi-check-circle' : 'pi pi-times-circle'" />
                  {{ n.ssh_ok ? 'OK' : 'FAIL' }}
                </span>
              </template>
            </Column>
            <Column header="SSH lat">
              <template #body="{ data: n }">
                <span class="cell-mono" :class="n.ssh_latency_ms != null && n.ssh_latency_ms > 100 ? 'cell-warn' : ''">
                  {{ n.ssh_latency_ms != null ? `${n.ssh_latency_ms} ms` : '\u2014' }}
                </span>
              </template>
            </Column>
            <Column header="DB lat">
              <template #body="{ data: n }">
                <span class="cell-mono" :class="n.db_latency_ms != null && n.db_latency_ms > 100 ? 'cell-warn' : ''">
                  {{ n.db_latency_ms != null ? `${n.db_latency_ms} ms` : '\u2014' }}
                </span>
              </template>
            </Column>
          </DataTable>
        </div>

        <!-- ARBITRATORS TABLE -->
        <div v-if="arbitrators.length" class="node-table-wrap">
          <div class="node-table-header">
            <span class="node-table-title">Arbitrators</span>
            <span class="node-table-count">{{ arbitrators.length }}</span>
          </div>
          <DataTable
            :value="arbitrators"
            class="topo-dt"
            :row-hover="true"
            size="small"
          >
            <Column header="Name" style="min-width:160px">
              <template #body="{ data: a }">
                <div class="cell-name">
                  <span class="status-dot" :style="{ background: arbColor(a), boxShadow: `0 0 6px ${arbColor(a)}` }"/>
                  <span class="name-text">{{ a.name }}</span>
                  <span class="arb-badge">ARB</span>
                </div>
              </template>
            </Column>
            <Column header="Host">
              <template #body="{ data: a }">
                <span class="cell-mono">{{ a.host }}</span>
              </template>
            </Column>
            <Column header="State">
              <template #body="{ data: a }">
                <span class="cell-state" :style="{ color: arbColor(a) }">{{ arbStatLabel(a) }}</span>
              </template>
            </Column>
            <Column header="DC">
              <template #body="{ data: a }">
                <span class="cell-muted">{{ a.dc_name ?? '\u2014' }}</span>
              </template>
            </Column>
            <Column header="SSH lat">
              <template #body="{ data: a }">
                <span class="cell-mono" :class="a.ssh_latency_ms != null && a.ssh_latency_ms > 100 ? 'cell-warn' : ''">
                  {{ a.ssh_latency_ms != null ? `${a.ssh_latency_ms} ms` : '\u2014' }}
                </span>
              </template>
            </Column>
          </DataTable>
        </div>
      </template>
    </template>

    <NodeDetailDrawer
      v-if="drawerNode !== null"
      :node="drawerNode"
      :cluster-id="clusterId"
      @close="closeDrawer"
    />

    <Teleport to="body">
      <div
        v-if="tooltip"
        class="topo-tooltip"
        :style="{ left: `${tooltip.x + 12}px`, top: `${tooltip.y - 8}px` }"
      >
        <template v-if="tooltip.node">
          <div class="tt-name">{{ tooltip.node.name }}</div>
          <div class="tt-row"><span>Host</span><span class="tt-val">{{ tooltip.node.host }}:{{ tooltip.node.port }}</span></div>
          <div class="tt-row"><span>State</span><span class="tt-val" :style="{ color: nodeColor(tooltip.node) }">{{ nodeStatLabel(tooltip.node) }}</span></div>
          <div class="tt-row"><span>DC</span><span class="tt-val">{{ tooltip.node.dc_name ?? '\u2014' }}</span></div>
          <div class="tt-row"><span>SSH</span><span class="tt-val" :style="{ color: tooltip.node.ssh_ok ? 'var(--color-synced)' : 'var(--color-offline)' }">{{ tooltip.node.ssh_ok ? 'OK' : 'FAIL' }}</span></div>
          <div v-if="tooltip.node.ssh_latency_ms != null" class="tt-row">
            <span>SSH lat</span><span class="tt-val">{{ tooltip.node.ssh_latency_ms }} ms</span>
          </div>
          <div v-if="tooltip.node.db_latency_ms != null" class="tt-row">
            <span>DB lat</span><span class="tt-val">{{ tooltip.node.db_latency_ms }} ms</span>
          </div>
          <div v-if="tooltip.node.wsrep_incoming_addresses" class="tt-row">
            <span>Peers</span>
            <span class="tt-val tt-peers">{{ tooltip.node.wsrep_incoming_addresses }}</span>
          </div>
          <div v-if="tooltip.node.wsrep_flow_control_paused != null" class="tt-row">
            <span>Flow Ctrl</span><span class="tt-val">{{ (tooltip.node.wsrep_flow_control_paused * 100).toFixed(1) }}%</span>
          </div>
          <div v-if="tooltip.node.wsrep_local_recv_queue != null" class="tt-row">
            <span>Recv Queue</span><span class="tt-val">{{ tooltip.node.wsrep_local_recv_queue }}</span>
          </div>
          <div class="tt-hint">Click to open details</div>
        </template>
        <template v-if="tooltip.arb">
          <div class="tt-name">{{ tooltip.arb.name }} <span class="tt-tag">ARB</span></div>
          <div class="tt-row"><span>Host</span><span class="tt-val">{{ tooltip.arb.host }}</span></div>
          <div class="tt-row"><span>State</span><span class="tt-val" :style="{ color: arbColor(tooltip.arb) }">{{ arbStatLabel(tooltip.arb) }}</span></div>
          <div class="tt-row"><span>garbd</span><span class="tt-val" :style="{ color: tooltip.arb.garbd_running ? 'var(--color-synced)' : 'var(--color-offline)' }">{{ tooltip.arb.garbd_running ? 'running' : 'stopped' }}</span></div>
          <div v-if="tooltip.arb.ssh_latency_ms != null" class="tt-row">
            <span>SSH lat</span><span class="tt-val">{{ tooltip.arb.ssh_latency_ms }} ms</span>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.topology-page { display: flex; flex-direction: column; gap: var(--space-6); }

.pg-empty {
  display: flex; align-items: center; gap: var(--space-3);
  color: var(--color-text-muted); padding: var(--space-12);
  justify-content: center; font-size: var(--text-sm);
}

/* ═══════════════════════════════════════
   HEADER — pg-head pattern
═══════════════════════════════════════ */
.pg-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.pg-head-icon {
  width: 36px; height: 36px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-highlight);
  border: 1px solid rgba(45, 212, 191, 0.18);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-size: 0.875rem;
}
.pg-head-body { flex: 1; min-width: 0; }
.pg-head-top {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.pg-title {
  font-size: var(--text-xl); font-weight: 700;
  color: var(--color-text); letter-spacing: -0.02em; line-height: 1.2;
}
.pg-desc {
  font-size: var(--text-xs); color: var(--color-text-muted); margin-top: 2px;
}
.topo-header-stats {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 3px var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  white-space: nowrap;
}
.stat-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

/* ═══════════════════════════════════════
   CANVAS SKELETON (loading state)
═══════════════════════════════════════ */
.topo-canvas-skeleton {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  min-height: 280px;
}
.tcs-inner {
  display: flex;
  gap: var(--space-8);
}
.tcs-zone {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  flex: 1;
  max-width: 260px;
}

/* ═══════════════════════════════════════
   CANVAS WRAP
═══════════════════════════════════════ */
.topo-canvas-wrap {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  overflow-x: auto;
  overflow-y: hidden;
}
.topo-svg { display: block; height: auto; min-height: 280px; }

/* ═══════════════════════════════════════
   SVG — ZONES + BADGES
═══════════════════════════════════════ */
.dc-zone-rect  { fill: var(--color-surface-2); stroke: var(--color-border); stroke-width: 1; }
.dc-zone-label { fill: var(--color-text-faint); font-size: 13px; font-weight: 700; letter-spacing: .08em; font-family: var(--font-body, sans-serif); }

.topo-badge           { cursor: default; }
.topo-badge--clickable { cursor: pointer; }
.badge-bg             { fill: var(--color-surface-offset); stroke: var(--color-border); stroke-width: 1; }
.topo-badge--clickable:hover .badge-bg { fill: var(--color-surface-dynamic); stroke: var(--color-primary); stroke-width: 1.5; }
.badge-bg--arb        { opacity: .85; }

.badge-name      { fill: var(--color-text);       font-size: 16px; font-weight: 600; font-family: var(--font-body, sans-serif); }
.badge-host      { fill: var(--color-text-muted); font-size: 11px; font-family: var(--font-mono, monospace); }
.badge-state     { font-size: 14px; font-weight: 700; letter-spacing: .05em; font-family: var(--font-body, sans-serif); }
.badge-pill      { font-size: 11px; font-weight: 700; letter-spacing: .05em; text-anchor: middle; font-family: var(--font-body, sans-serif); }
.badge-open-hint { fill: var(--color-text-faint); font-size: 13px; text-anchor: end; opacity: 0; transition: opacity .15s; }
.topo-badge--clickable:hover .badge-open-hint { opacity: 1; }

/*
 * dot-pulse — CSS animation for offline dot.
 * Replaces SVG SMIL <animate> which misbehaves on VDI/Chrome.
 */
@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.15; }
}
.dot-pulse { animation: dot-pulse 1.8s ease-in-out infinite; }

/* ═══════════════════════════════════════
   SVG — CONNECTION ARCS (CSS tokens only)
═══════════════════════════════════════ */
.topo-arc { fill: none; stroke-linecap: round; }

.topo-arc--synced {
  stroke: var(--color-synced);
  stroke-width: 2.5;
  stroke-dasharray: 8 4;
  opacity: 0.95;
}
.topo-arc--active {
  stroke: var(--color-readonly);
  stroke-width: 2;
  stroke-dasharray: 5 4;
  opacity: 0.85;
}
.topo-arc--offline {
  stroke: var(--color-text-faint);
  stroke-width: 1.5;
  stroke-dasharray: 3 5;
  opacity: 0.45;
}

/* ═══════════════════════════════════════
   LEGEND
═══════════════════════════════════════ */
.topo-legend {
  display: flex; flex-wrap: wrap; align-items: center;
  gap: var(--space-2) var(--space-5);
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--space-2) var(--space-4);
}
.legend-title  { font-size: var(--text-xs); text-transform: uppercase; letter-spacing: .08em; color: var(--color-text-faint); font-weight: 600; }
.legend-items  { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-4); align-items: center; }
.legend-item   { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-text-muted); }
.legend-item--hint { color: var(--color-text-faint); }
.legend-dot    { width: 7px; height: 7px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.legend-icon   { font-size: 0.75rem; line-height: 1; }
.legend-arc    { display: inline-block; width: 22px; height: 3px; border-radius: 2px; flex-shrink: 0; }
.legend-arc--synced  { background: var(--color-synced);      opacity: 0.95; }
.legend-arc--active  { background: var(--color-readonly);    opacity: 0.85; }
.legend-arc--offline { background: var(--color-text-faint);  opacity: 0.5; }

/* ═══════════════════════════════════════
   TABLES
═══════════════════════════════════════ */
.node-table-wrap {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.node-table-header {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}
.node-table-title {
  font-size: var(--text-sm); font-weight: 700;
  color: var(--color-text); text-transform: uppercase; letter-spacing: .06em;
}
.node-table-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; height: 20px; padding: 0 var(--space-2);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: var(--text-xs); font-weight: 700; color: var(--color-text-muted);
  font-family: var(--font-mono);
}

/* ── DataTable overrides ── */
:deep(.topo-dt .p-datatable-table-container) {
  border: none;
  box-shadow: none;
  border-radius: 0;
}
:deep(.topo-dt .p-datatable-thead > tr > th) {
  padding: var(--space-3) var(--space-5) !important;
  text-align: left;
  font-size: var(--text-xs) !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint) !important;
  white-space: nowrap;
  background: var(--color-surface-offset) !important;
  border-bottom: 1px solid var(--color-border) !important;
}
:deep(.topo-dt .p-datatable-tbody > tr > td) {
  padding: var(--space-3) var(--space-5) !important;
  border-bottom: 1px solid color-mix(in oklch, var(--color-border) 60%, transparent) !important;
  vertical-align: middle;
}
:deep(.topo-dt .p-datatable-tbody > tr:last-child > td) {
  border-bottom: none !important;
}
:deep(.topo-dt .p-datatable-tbody > tr:hover > td) {
  background: var(--color-surface-offset) !important;
}
:deep(.topo-dt .p-datatable-tbody > tr.node-row--clickable) {
  cursor: pointer;
}

.cell-name { display: flex; align-items: center; gap: var(--space-3); }

@keyframes status-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}
.status-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; transition: box-shadow .3s;
}
.status-dot--pulse { animation: status-pulse 1.8s ease-in-out infinite; }

.name-text    { font-size: var(--text-sm); font-weight: 600; color: var(--color-text); }
.maint-badge,
.arb-badge    { font-size: 9px; font-weight: 700; letter-spacing: .06em; border-radius: var(--radius-sm); padding: 1px 5px; }
.maint-badge  { background: color-mix(in oklch, var(--color-degraded) 12%, transparent); color: var(--color-degraded); }
.arb-badge    { background: var(--color-surface-offset); border: 1px solid var(--color-border); color: var(--color-text-faint); }

.cell-mono    { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-state   { font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 700; letter-spacing: .05em; }
.cell-muted   { font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-warn    { color: var(--color-degraded) !important; }

.mode-pill {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 32px; padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs); font-weight: 700; letter-spacing: .06em;
}
.mode-rw { background: color-mix(in oklch, var(--color-synced)   10%, transparent); color: var(--color-synced);   border: 1px solid color-mix(in oklch, var(--color-synced)   25%, transparent); }
.mode-ro { background: color-mix(in oklch, var(--color-readonly) 10%, transparent); color: var(--color-readonly); border: 1px solid color-mix(in oklch, var(--color-readonly) 25%, transparent); }

.ssh-cell { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); font-weight: 600; }
.ssh-ok   { color: var(--color-synced); }
.ssh-fail { color: var(--color-offline); }

/* ═══════════════════════════════════════
   TOOLTIP
═══════════════════════════════════════ */
.topo-tooltip {
  position: fixed; z-index: 9999;
  background: var(--color-surface-2); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--space-3) var(--space-4);
  box-shadow: var(--shadow-lg); min-width: 180px; pointer-events: none;
}
.tt-name  { font-size: var(--text-sm); font-weight: 700; color: var(--color-text); margin-bottom: var(--space-2); display: flex; align-items: center; gap: var(--space-2); }
.tt-tag   { font-size: 9px; background: var(--color-surface-offset); border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 1px 5px; color: var(--color-text-faint); font-weight: 600; letter-spacing: .06em; }
.tt-row   { display: flex; justify-content: space-between; gap: var(--space-4); font-size: var(--text-xs); color: var(--color-text-muted); line-height: 1.7; }
.tt-val   { font-family: var(--font-mono); color: var(--color-text); }
.tt-peers { font-size: 9px; max-width: 140px; word-break: break-all; color: var(--color-text-muted); }
.tt-hint  { margin-top: var(--space-2); font-size: var(--text-xs); color: var(--color-text-faint); text-align: center; border-top: 1px solid var(--color-divider); padding-top: var(--space-2); }
</style>
