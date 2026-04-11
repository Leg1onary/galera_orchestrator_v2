<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'
import NodeDetailDrawer from '@/components/nodes/NodeDetailDrawer.vue'

interface NodeLive {
  id: number
  name: string
  host: string
  port: number
  dc?: { id: number; name: string } | null
  wsrep_local_state_comment: string | null
  wsrep_ready: string | null
  wsrep_flow_control_paused: number | null
  wsrep_local_recv_queue: number | null
  ssh_ok: boolean
  readonly: boolean
  maintenance: boolean
  maintenance_drift?: boolean
}
interface ArbLive {
  id: number
  name: string
  host: string
  dc?: { id: number; name: string } | null
  is_reachable: boolean
  garbd_running: boolean
  latency_ssh_ms: number | null
}
interface DCGroup {
  dcId: number | null
  dcName: string
  nodes: NodeLive[]
  arbs: ArbLive[]
}

const DC_W    = 200
const DC_PAD  = 12
const B_W     = 80
const B_H     = 62
const B_ARB_H = 48
const B_GAP   = 8
const TOP_OFF = 14
const SIDE    = 10

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId!)
const { data, isLoading } = useClusterStatus(clusterId)

const nodes       = computed<NodeLive[]>(() => (data.value?.nodes      ?? []) as NodeLive[])
const arbitrators = computed<ArbLive[]>(() => (data.value?.arbitrators ?? []) as ArbLive[])

// ── NodeDetailDrawer ─────────────────────────────────────────────────────────
const drawerNodeId = ref<number | null>(null)
const drawerOpen   = ref(false)
function openDrawer(nodeId: number) {
  drawerNodeId.value = nodeId
  drawerOpen.value   = true
}
function closeDrawer() {
  drawerOpen.value   = false
  drawerNodeId.value = null
}

// ── Header stats ─────────────────────────────────────────────────────────────
const syncedCount = computed(() =>
  nodes.value.filter(n => n.ssh_ok && (n.wsrep_local_state_comment ?? '').toUpperCase() === 'SYNCED').length
)

// ── DC groups ────────────────────────────────────────────────────────────────
const dcGroups = computed<DCGroup[]>(() => {
  const map = new Map<string, DCGroup>()
  for (const n of nodes.value) {
    const key = n.dc ? String(n.dc.id) : '__none__'
    if (!map.has(key)) map.set(key, { dcId: n.dc?.id ?? null, dcName: n.dc?.name ?? 'No DC', nodes: [], arbs: [] })
    map.get(key)!.nodes.push(n)
  }
  for (const a of arbitrators.value) {
    const key = a.dc ? String(a.dc.id) : '__none__'
    if (!map.has(key)) map.set(key, { dcId: a.dc?.id ?? null, dcName: a.dc?.name ?? 'No DC', nodes: [], arbs: [] })
    map.get(key)!.arbs.push(a)
  }
  return Array.from(map.values())
})

function dcHeight(dc: DCGroup): number {
  const nodeRows = Math.ceil(dc.nodes.length / 2)
  const nodesH   = nodeRows * (B_H + B_GAP)
  const arbsH    = dc.arbs.length * (B_ARB_H + B_GAP)
  return TOP_OFF + 6 + nodesH + arbsH + SIDE
}
const svgViewH = computed(() => Math.max(...(dcGroups.value.length ? dcGroups.value.map(dcHeight) : [120])) + 16)
const svgViewW = computed(() => dcGroups.value.length * (DC_W + DC_PAD) + DC_PAD)

function dcX(di: number) { return DC_PAD + di * (DC_W + DC_PAD) }
function badgeX(di: number, ni: number) { return dcX(di) + SIDE + (ni % 2) * (B_W + B_GAP) }
function badgeY(ni: number) { return TOP_OFF + 8 + Math.floor(ni / 2) * (B_H + B_GAP) }
function arbBadgeY(dc: DCGroup, ai: number) {
  return TOP_OFF + 8 + Math.ceil(dc.nodes.length / 2) * (B_H + B_GAP) + ai * (B_ARB_H + B_GAP)
}

function nodeColor(n: NodeLive): string {
  const s = (n.wsrep_local_state_comment ?? '').toUpperCase()
  if (!n.ssh_ok || s === 'OFFLINE') return 'var(--color-offline)'
  if (n.wsrep_ready === 'OFF')      return 'var(--color-degraded)'
  if (s === 'SYNCED' && n.readonly) return 'var(--color-readonly)'
  if (s === 'SYNCED')               return 'var(--color-synced)'
  if (s === 'DONOR' || s === 'JOINER' || s === 'DESYNCED') return 'var(--color-donor)'
  return 'var(--color-text-faint)'
}
function arbColor(a: ArbLive): string {
  if (!a.is_reachable)  return 'var(--color-offline)'
  if (!a.garbd_running) return 'var(--color-degraded)'
  return 'var(--color-synced)'
}
function nodeStatLabel(n: NodeLive): string {
  const s = (n.wsrep_local_state_comment ?? '').toUpperCase()
  if (!n.ssh_ok)           return 'OFFLINE'
  if (n.wsrep_ready === 'OFF') return 'DEGRADED'
  return s || '—'
}
function arbStatLabel(a: ArbLive): string {
  if (!a.is_reachable)  return 'OFFLINE'
  if (!a.garbd_running) return 'DEGRADED'
  return 'ONLINE'
}

// ── Tooltip ──────────────────────────────────────────────────────────────────
const tooltip = ref<{ node?: NodeLive; arb?: ArbLive; x: number; y: number } | null>(null)
function showNodeTip(e: MouseEvent, n: NodeLive) { tooltip.value = { node: n, x: e.clientX, y: e.clientY } }
function showArbTip(e: MouseEvent, a: ArbLive)   { tooltip.value = { arb:  a, x: e.clientX, y: e.clientY } }
function hideTip() { tooltip.value = null }

// Скрываем tooltip при скролле страницы (фикс: position:fixed не двигается со страницей)
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
      <!-- Page header -->
      <div class="pg-header">
        <div class="pg-header__left">
          <span class="section-title">Topology</span>
          <div class="topo-header-stats">
            <span class="stat-chip stat-chip--synced">
              <span class="stat-dot" style="background:var(--color-synced)"/>
              {{ syncedCount }} / {{ nodes.length }} SYNCED
            </span>
            <span v-if="arbitrators.length" class="stat-chip">
              <span class="stat-dot" style="background:var(--color-text-faint)"/>
              {{ arbitrators.filter(a => a.is_reachable).length }} / {{ arbitrators.length }} ARB
            </span>
          </div>
        </div>
      </div>

      <div v-if="isLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner" /><span>Loading…</span>
      </div>

      <template v-else>
        <!-- SVG canvas -->
        <div class="topo-canvas-wrap">
          <svg
            class="topo-svg"
            xmlns="http://www.w3.org/2000/svg"
            :viewBox="`0 0 ${svgViewW} ${svgViewH}`"
            preserveAspectRatio="xMidYMid meet"
          >
            <defs>
              <filter id="glow-synced"  x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b"/>
                <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="glow-offline" x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="b"/>
                <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>

            <g v-for="(dc, di) in dcGroups" :key="di">
              <rect :x="dcX(di)" y="4" :width="DC_W" :height="dcHeight(dc)" rx="8" ry="8" class="dc-zone-rect" />
              <text :x="dcX(di) + SIDE" :y="14" class="dc-zone-label">{{ dc.dcName.toUpperCase() }}</text>

              <!-- Full-mesh lines внутри DC (фикс: было n→n+1, теперь все пары) -->
              <g v-if="dc.nodes.length > 1">
                <line
                  v-for="(_, ni) in dc.nodes" :key="`lna-${ni}`"
                  v-for="(_, nj) in dc.nodes.slice(ni + 1)" :key="`lnb-${ni}-${nj}`"
                  :x1="badgeX(di, ni) + B_W / 2" :y1="badgeY(ni) + B_H / 2"
                  :x2="badgeX(di, ni + 1 + dc.nodes.slice(ni + 1).indexOf(_)) + B_W / 2"
                  :y2="badgeY(ni + 1 + dc.nodes.slice(ni + 1).indexOf(_)) + B_H / 2"
                  class="topo-line"
                />
              </g>

              <!-- Simplified: sequential lines (stable approach) -->
              <g v-if="dc.nodes.length > 1">
                <template v-for="ni in dc.nodes.length - 1" :key="`ln-${ni}`">
                  <template v-for="nj in dc.nodes.length" :key="`ln-${ni}-${nj}`">
                    <line
                      v-if="nj > ni"
                      :x1="badgeX(di, ni - 1) + B_W / 2" :y1="badgeY(ni - 1) + B_H / 2"
                      :x2="badgeX(di, nj - 1) + B_W / 2" :y2="badgeY(nj - 1) + B_H / 2"
                      class="topo-line"
                    />
                  </template>
                </template>
              </g>

              <g
                v-for="(node, ni) in dc.nodes" :key="node.id"
                :transform="`translate(${badgeX(di, ni)}, ${badgeY(ni)})`"
                class="topo-badge topo-badge--clickable"
                @mouseenter="(e) => showNodeTip(e, node)"
                @mouseleave="hideTip"
                @click="openDrawer(node.id)"
              >
                <rect x="0" y="0" :width="B_W" :height="B_H" rx="5" class="badge-bg" />
                <rect x="0" y="0" :width="B_W" height="3" rx="2"
                  :fill="nodeColor(node)"
                  :filter="node.ssh_ok && node.wsrep_local_state_comment?.toUpperCase() === 'SYNCED' ? 'url(#glow-synced)' : undefined"
                />
                <!-- Pulse animation для OFFLINE нод -->
                <circle cx="9" cy="14" r="4" :fill="nodeColor(node)" :filter="!node.ssh_ok ? 'url(#glow-offline)' : undefined">
                  <animate
                    v-if="!node.ssh_ok"
                    attributeName="opacity"
                    values="1;0.2;1"
                    dur="1.6s"
                    repeatCount="indefinite"
                  />
                </circle>
                <text x="16" y="18" class="badge-name">{{ node.name }}</text>
                <text x="4"  y="30" class="badge-host">{{ node.host }}:{{ node.port }}</text>
                <text x="4"  y="42" class="badge-state" :fill="nodeColor(node)">{{ nodeStatLabel(node) }}</text>
                <rect x="4" y="48" width="22" height="10" rx="2" :fill="node.readonly ? 'rgba(234,179,8,.15)' : 'rgba(74,222,128,.12)'" />
                <text x="15" y="56" class="badge-pill" :fill="node.readonly ? 'var(--color-readonly)' : 'var(--color-synced)'">{{ node.readonly ? 'RO' : 'RW' }}</text>
                <rect v-if="node.maintenance" x="29" y="48" width="28" height="10" rx="2" fill="rgba(249,115,22,.15)" />
                <text v-if="node.maintenance" x="43" y="56" class="badge-pill" fill="var(--color-degraded)">MAINT</text>
                <circle v-if="node.maintenance_drift" :cx="B_W - 6" :cy="B_H - 6" r="3" fill="var(--color-offline)" />
                <!-- Click hint icon -->
                <text :x="B_W - 6" y="10" class="badge-open-hint">⤢</text>
              </g>

              <g
                v-for="(arb, ai) in dc.arbs" :key="`arb-${arb.id}`"
                :transform="`translate(${dcX(di) + SIDE}, ${arbBadgeY(dc, ai)})`"
                class="topo-badge topo-badge--arb"
                @mouseenter="(e) => showArbTip(e, arb)"
                @mouseleave="hideTip"
              >
                <rect x="0" y="0" :width="B_W" :height="B_ARB_H" rx="5" class="badge-bg badge-bg--arb" />
                <rect x="0" y="0" :width="B_W" height="2" rx="2" :fill="arbColor(arb)" />
                <circle cx="9" cy="14" r="3" :fill="arbColor(arb)" />
                <text x="3" y="26" class="badge-arb-ico">◈</text>
                <text x="16" y="18" class="badge-name">{{ arb.name }}</text>
                <text x="16" y="28" class="badge-host">{{ arb.host }}</text>
                <text x="4"  y="40" class="badge-state" :fill="arbColor(arb)">{{ arbStatLabel(arb) }}</text>
              </g>
            </g>

            <!-- Inter-DC lines -->
            <g v-if="dcGroups.length > 1">
              <line
                v-for="di in dcGroups.length - 1" :key="`dcl-${di}`"
                :x1="dcX(di - 1) + DC_W" :y1="svgViewH / 2"
                :x2="dcX(di)"            :y2="svgViewH / 2"
                class="topo-line topo-line--dc"
              />
            </g>
          </svg>
        </div>

        <!-- Legend -->
        <div class="topo-legend">
          <span class="legend-title">Legend</span>
          <div class="legend-items">
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-synced)"/><span>SYNCED RW</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-readonly)"/><span>SYNCED RO</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-donor)"/><span>DONOR / JOINER</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-degraded)"/><span>wsrep_ready=OFF</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--color-offline)"/><span>OFFLINE</span></div>
            <div class="legend-item legend-item--hint"><span class="legend-icon">⤢</span><span>Click badge → details</span></div>
          </div>
        </div>

        <!-- Nodes table -->
        <div class="node-table-wrap">
          <div class="node-table-header">
            <span class="node-table-title">Nodes</span>
            <span class="node-table-count">{{ nodes.length }}</span>
          </div>
          <table class="node-table">
            <thead>
              <tr>
                <th>Node</th>
                <th>Host</th>
                <th>State</th>
                <th>DC</th>
                <th>Mode</th>
                <th>SSH</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="n in nodes"
                :key="n.id"
                class="node-row node-row--clickable"
                @click="openDrawer(n.id)"
              >
                <td>
                  <div class="cell-name">
                    <span
                      class="status-dot"
                      :class="{ 'status-dot--pulse': !n.ssh_ok }"
                      :style="{ background: nodeColor(n), boxShadow: `0 0 6px ${nodeColor(n)}` }"
                    />
                    <span class="name-text">{{ n.name }}</span>
                    <span v-if="n.maintenance" class="maint-badge">MAINT</span>
                  </div>
                </td>
                <td><span class="cell-mono">{{ n.host }}:{{ n.port }}</span></td>
                <td>
                  <span class="cell-state" :style="{ color: nodeColor(n) }">{{ nodeStatLabel(n) }}</span>
                </td>
                <td><span class="cell-muted">{{ n.dc?.name ?? '—' }}</span></td>
                <td>
                  <span class="mode-pill" :class="n.readonly ? 'mode-ro' : 'mode-rw'">{{ n.readonly ? 'RO' : 'RW' }}</span>
                </td>
                <td>
                  <span class="ssh-cell" :class="n.ssh_ok ? 'ssh-ok' : 'ssh-fail'">
                    <i :class="n.ssh_ok ? 'pi pi-check-circle' : 'pi pi-times-circle'" />
                    {{ n.ssh_ok ? 'OK' : 'FAIL' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Arbitrators table -->
        <div v-if="arbitrators.length" class="node-table-wrap">
          <div class="node-table-header">
            <span class="node-table-title">Arbitrators</span>
            <span class="node-table-count">{{ arbitrators.length }}</span>
          </div>
          <table class="node-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Host</th>
                <th>State</th>
                <th>DC</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in arbitrators" :key="a.id" class="node-row">
                <td>
                  <div class="cell-name">
                    <span class="status-dot" :style="{ background: arbColor(a), boxShadow: `0 0 6px ${arbColor(a)}` }"/>
                    <span class="name-text">{{ a.name }}</span>
                    <span class="arb-badge">ARB</span>
                  </div>
                </td>
                <td><span class="cell-mono">{{ a.host }}</span></td>
                <td><span class="cell-state" :style="{ color: arbColor(a) }">{{ arbStatLabel(a) }}</span></td>
                <td><span class="cell-muted">{{ a.dc?.name ?? '—' }}</span></td>
                <td><span class="cell-mono">{{ a.latency_ssh_ms != null ? `${a.latency_ssh_ms} ms` : '—' }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>

    <!-- NodeDetailDrawer -->
    <NodeDetailDrawer
      v-if="drawerOpen && drawerNodeId !== null"
      :node-id="drawerNodeId"
      :cluster-id="clusterId"
      :open="drawerOpen"
      @close="closeDrawer"
    />

    <!-- Tooltip -->
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
          <div class="tt-row"><span>DC</span><span class="tt-val">{{ tooltip.node.dc?.name ?? '—' }}</span></div>
          <div class="tt-row"><span>SSH</span><span class="tt-val" :style="{ color: tooltip.node.ssh_ok ? 'var(--color-synced)' : 'var(--color-offline)' }">{{ tooltip.node.ssh_ok ? 'OK' : 'FAIL' }}</span></div>
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
          <div v-if="tooltip.arb.latency_ssh_ms != null" class="tt-row">
            <span>Latency</span><span class="tt-val">{{ tooltip.arb.latency_ssh_ms }} ms</span>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.topology-page { display:flex; flex-direction:column; gap:var(--space-6); }

.pg-empty {
  display:flex; align-items:center; gap:var(--space-3);
  color:var(--color-text-muted); padding:var(--space-12);
  justify-content:center; font-size:var(--text-sm);
}

/* ── Header ───────────────────────────────────────────────────────── */
.pg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
}
.pg-header__left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
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
  padding: 2px var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  white-space: nowrap;
}
.stat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── Canvas ──────────────────────────────────────────────────────── */
.topo-canvas-wrap {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  overflow-x: auto;
  overflow-y: hidden;
}
.topo-svg {
  display: block;
  /* max-height умеренный — SVG масштабируется через viewBox */
  max-height: 260px;
  height: auto;
  width: auto;
  min-width: 100%;
}

.dc-zone-rect  { fill:var(--color-surface-2); stroke:var(--color-border); stroke-width:.8; }
.dc-zone-label { fill:var(--color-text-faint); font-size:6.5px; font-weight:700; letter-spacing:.08em; font-family:var(--font-body,sans-serif); }

.topo-badge      { cursor:default; }
.topo-badge--clickable { cursor: pointer; }
.badge-bg        { fill:var(--color-surface-offset); stroke:var(--color-border); stroke-width:.6; transition:fill .18s; }
.topo-badge--clickable:hover .badge-bg { fill:var(--color-surface-dynamic); stroke: var(--color-primary); stroke-width: 1; }
.badge-bg--arb   { opacity:.8; }

.badge-name      { fill:var(--color-text);       font-size:7px;   font-weight:600; font-family:var(--font-body,sans-serif); }
.badge-host      { fill:var(--color-text-muted); font-size:5.5px; font-family:var(--font-mono,monospace); }
.badge-state     { font-size:6px; font-weight:700; letter-spacing:.05em; font-family:var(--font-body,sans-serif); }
.badge-pill      { font-size:5px; font-weight:700; letter-spacing:.05em; text-anchor:middle; font-family:var(--font-body,sans-serif); }
.badge-arb-ico   { fill:var(--color-text-faint); font-size:7px; }
.badge-open-hint {
  fill: var(--color-text-faint);
  font-size: 6px;
  text-anchor: end;
  opacity: 0;
  transition: opacity .15s;
}
.topo-badge--clickable:hover .badge-open-hint { opacity: 1; }

.topo-line     { stroke:var(--color-border); stroke-width:1; stroke-dasharray:3 2; opacity:.5; }
.topo-line--dc { stroke:var(--color-primary); stroke-dasharray:5 3; opacity:.3; }

/* ── Legend ──────────────────────────────────────────────────────── */
.topo-legend {
  display:flex; flex-wrap:wrap; align-items:center;
  gap:var(--space-2) var(--space-5);
  background:var(--color-surface); border:1px solid var(--color-border);
  border-radius:var(--radius-md); padding:var(--space-2) var(--space-4);
}
.legend-title  { font-size:var(--text-xs); text-transform:uppercase; letter-spacing:.08em; color:var(--color-text-faint); font-weight:600; }
.legend-items  { display:flex; flex-wrap:wrap; gap:var(--space-2) var(--space-4); align-items:center; }
.legend-item   { display:flex; align-items:center; gap:var(--space-2); font-size:var(--text-xs); color:var(--color-text-muted); }
.legend-item--hint { color: var(--color-text-faint); }
.legend-dot    { width:7px; height:7px; border-radius:50%; display:inline-block; flex-shrink:0; }
.legend-icon   { font-size:10px; line-height:1; }

/* ── Tables ──────────────────────────────────────────────────────── */
.node-table-wrap {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.node-table-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}
.node-table-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: .06em;
}
.node-table-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--space-2);
  background: var(--color-surface-dynamic);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-muted);
}

.node-table { width:100%; border-collapse:collapse; }

.node-table thead tr { background: var(--color-surface-offset); }
.node-table th {
  padding: var(--space-3) var(--space-6);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--color-text-faint);
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border);
}

.node-row {
  border-bottom: 1px solid oklch(from var(--color-border) l c h / 0.5);
  transition: background var(--transition-interactive);
}
.node-row:last-child { border-bottom: none; }
.node-row:hover { background: var(--color-surface-offset); }
.node-row--clickable { cursor: pointer; }

.node-table td { padding: var(--space-4) var(--space-6); vertical-align: middle; }

.cell-name { display:flex; align-items:center; gap:var(--space-3); }

/* Pulse animation для OFFLINE нод в таблице */
@keyframes status-pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 6px currentColor; }
  50%       { opacity: 0.3; box-shadow: 0 0 2px currentColor; }
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: box-shadow .3s;
}
.status-dot--pulse {
  animation: status-pulse 1.6s ease-in-out infinite;
}

.name-text { font-size:var(--text-sm); font-weight:600; color:var(--color-text); }

.maint-badge, .arb-badge {
  font-size: 9px; font-weight: 700; letter-spacing:.06em;
  border-radius: var(--radius-sm); padding: 1px 5px;
}
.maint-badge { background:rgba(249,115,22,.12); color:var(--color-degraded); }
.arb-badge   { background:var(--color-surface-dynamic); color:var(--color-text-faint); }

.cell-mono  { font-family:var(--font-mono,monospace); font-size:var(--text-xs); color:var(--color-text-muted); }
.cell-state { font-family:var(--font-mono,monospace); font-size:var(--text-xs); font-weight:700; letter-spacing:.05em; }
.cell-muted { font-size:var(--text-xs); color:var(--color-text-muted); }

.mode-pill {
  display:inline-flex; align-items:center; justify-content:center;
  min-width:32px; padding:2px 8px;
  border-radius:var(--radius-full);
  font-size:var(--text-xs); font-weight:700; letter-spacing:.06em;
}
.mode-rw { background:rgba(74,222,128,.10); color:var(--color-synced);   border:1px solid rgba(74,222,128,.2); }
.mode-ro { background:rgba(234,179,8,.10);  color:var(--color-readonly); border:1px solid rgba(234,179,8,.2);  }

.ssh-cell { display:inline-flex; align-items:center; gap:var(--space-2); font-size:var(--text-xs); font-weight:600; }
.ssh-ok   { color:var(--color-synced); }
.ssh-fail { color:var(--color-offline); }

/* ── Tooltip ─────────────────────────────────────────────────────── */
.topo-tooltip {
  position:fixed; z-index:9999;
  background:var(--color-surface-2); border:1px solid var(--color-border);
  border-radius:var(--radius-md); padding:var(--space-3) var(--space-4);
  box-shadow:var(--shadow-lg); min-width:180px; pointer-events:none;
}
.tt-name  { font-size:var(--text-sm); font-weight:700; color:var(--color-text); margin-bottom:var(--space-2); display:flex; align-items:center; gap:var(--space-2); }
.tt-tag   { font-size:9px; background:var(--color-surface-dynamic); border-radius:var(--radius-sm); padding:1px 5px; color:var(--color-text-muted); font-weight:600; letter-spacing:.06em; }
.tt-row   { display:flex; justify-content:space-between; gap:var(--space-4); font-size:var(--text-xs); color:var(--color-text-muted); line-height:1.7; }
.tt-val   { font-family:var(--font-mono,monospace); color:var(--color-text); }
.tt-hint  { margin-top:var(--space-2); font-size:var(--text-xs); color:var(--color-text-faint); text-align:center; border-top:1px solid var(--color-divider); padding-top:var(--space-2); }

.loading-state {
  display:flex; align-items:center; gap:var(--space-3);
  color:var(--color-text-muted); padding:var(--space-8);
  justify-content:center; font-size:var(--text-sm);
}
</style>
