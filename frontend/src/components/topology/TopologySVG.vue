<template>
  <div class="topology-wrap">
    <svg
      class="topology-svg"
      :viewBox="`0 0 ${svgW} ${svgH}`"
      xmlns="http://www.w3.org/2000/svg"
      style="max-height:420px"
    >
      <!-- Connection lines between nodes -->
      <g v-for="(line, i) in lines" :key="'line-'+i">
        <line
          :x1="line.x1" :y1="line.y1" :x2="line.x2" :y2="line.y2"
          stroke="var(--border-strong)" stroke-width="1.5" stroke-dasharray="4 3"
          opacity="0.7"
        />
        <text
          :x="(line.x1+line.x2)/2" :y="(line.y1+line.y2)/2 - 5"
          text-anchor="middle" font-size="9" fill="var(--text-faint)"
        >IST</text>
      </g>

      <!-- Arbitrator connections -->
      <g v-for="(arb, i) in arbitrators" :key="'arb-line-'+i">
        <line
          v-for="n in nodePositions"
          :key="'arb-conn-'+n.id"
          :x1="arb.cx" :y1="arb.cy - 14"
          :x2="n.cx" :y2="n.cy + 50"
          stroke="var(--text-faint)" stroke-width="1" stroke-dasharray="3 4" opacity="0.4"
        />
      </g>

      <!-- Node cards -->
      <g
        v-for="np in nodePositions"
        :key="np.id"
        class="topo-node-card"
      >
        <!-- Card background -->
        <rect
          :x="np.x" :y="np.y"
          :width="nodeW" :height="nodeH"
          :rx="8"
          :fill="np.online ? 'var(--surface-2)' : 'var(--error-dim)'"
          :stroke="np.borderColor"
          stroke-width="1.5"
        />
        <!-- State stripe top -->
        <rect
          :x="np.x" :y="np.y"
          :width="nodeW" height="3"
          rx="8"
          :fill="np.borderColor"
        />

        <!-- Node name -->
        <text
          :x="np.cx" :y="np.y + 22"
          text-anchor="middle"
          font-size="13" font-weight="700"
          fill="var(--text)"
          font-family="Inter,system-ui,sans-serif"
        >{{ np.name }}</text>

        <!-- IP address -->
        <text
          :x="np.cx" :y="np.y + 38"
          text-anchor="middle"
          font-size="9.5"
          fill="var(--text-muted)"
          font-family="'JetBrains Mono',monospace"
        >{{ np.host }}:{{ np.port }}</text>

        <!-- DC badge -->
        <rect
          v-if="np.dc"
          :x="np.x + 6" :y="np.y + 46"
          :width="dcBadgeWidth(np.dc)" height="16" rx="8"
          fill="var(--surface-3)"
          stroke="var(--border)"
          stroke-width="1"
        />
        <text
          v-if="np.dc"
          :x="np.x + 6 + dcBadgeWidth(np.dc)/2" :y="np.y + 58"
          text-anchor="middle"
          font-size="8.5" font-weight="600"
          fill="var(--text-muted)"
        >{{ np.dc }}</text>

        <!-- State badge -->
        <rect
          :x="np.x + nodeW - stateBadgeWidth(np.state) - 6" :y="np.y + 46"
          :width="stateBadgeWidth(np.state)" height="16" rx="8"
          :fill="np.stateBadgeFill"
        />
        <text
          :x="np.x + nodeW - stateBadgeWidth(np.state)/2 - 6" :y="np.y + 58"
          text-anchor="middle"
          font-size="8" font-weight="700"
          :fill="np.stateBadgeColor"
        >{{ np.state.toUpperCase() }}</text>
      </g>

      <!-- Arbitrators (diamonds) -->
      <g v-for="(arb, i) in arbitrators" :key="'arb-'+i">
        <polygon
          :points="arbPoints(arb)"
          fill="var(--surface-2)"
          :stroke="arb.online ? 'var(--info)' : 'var(--error)'"
          stroke-width="1.5"
        />
        <text
          :x="arb.cx" :y="arb.cy + 1"
          text-anchor="middle"
          font-size="9" font-weight="700"
          fill="var(--text-muted)"
        >garbd</text>
        <text
          :x="arb.cx" :y="arb.cy + 12"
          text-anchor="middle"
          font-size="8"
          fill="var(--text-faint)"
        >{{ arb.host }}</text>
      </g>

      <!-- Status line bottom -->
      <text
        :x="svgW / 2" :y="svgH - 6"
        text-anchor="middle"
        font-size="10"
        fill="var(--text-faint)"
      >Cluster Size: {{ nodes.length }} · Status: {{ clusterStatus }} · Cert Failures: {{ certFailures }}</text>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster.js'

const cluster = useClusterStore()
const nodes       = computed(() => cluster.nodes)
const arbitrators_raw = computed(() => cluster.arbitrators)

// Layout constants
const svgW  = 700
const nodeW = 150
const nodeH = 70
const rowY  = 50

const nodePositions = computed(() => {
  const ns  = nodes.value
  const cnt = ns.length
  if (!cnt) return []

  // Distribute evenly
  const totalW = cnt * nodeW + (cnt - 1) * 30
  const startX = (svgW - totalW) / 2

  return ns.map((n, i) => {
    const x  = startX + i * (nodeW + 30)
    const cx = x + nodeW / 2

    const state  = (n.state || n.wsrep_local_state_comment || 'unknown').toLowerCase()
    const online = n.online !== false

    let borderColor     = 'var(--success)'
    let stateBadgeFill  = 'var(--success-dim)'
    let stateBadgeColor = 'var(--success)'

    if (!online)                              { borderColor = 'var(--error)';   stateBadgeFill = 'var(--error-dim)';   stateBadgeColor = 'var(--error)' }
    else if (state.includes('donor'))         { borderColor = 'var(--warning)'; stateBadgeFill = 'var(--warning-dim)'; stateBadgeColor = 'var(--warning)' }
    else if (state.includes('join'))          { borderColor = 'var(--info)';    stateBadgeFill = 'var(--info-dim)';    stateBadgeColor = 'var(--info)' }

    const displayState = online ? (n.state || n.wsrep_local_state_comment || 'Unknown') : 'Offline'

    return {
      id: n.id, name: n.name || n.id, host: n.host,
      port: n.port || 3306, dc: n.dc,
      online, state: displayState,
      x, y: rowY, cx, cy: rowY + nodeH / 2,
      borderColor, stateBadgeFill, stateBadgeColor,
    }
  })
})

const svgH = computed(() => {
  return arbitrators_raw.value.length ? 340 : 210
})

// Connecting lines between nodes
const lines = computed(() => {
  const ps = nodePositions.value
  const ls = []
  for (let i = 0; i < ps.length - 1; i++) {
    ls.push({
      x1: ps[i].x + nodeW,
      y1: ps[i].cy,
      x2: ps[i+1].x,
      y2: ps[i+1].cy,
    })
  }
  return ls
})

// Arbitrators positioned below nodes
const arbitrators = computed(() => {
  const arbs = arbitrators_raw.value
  if (!arbs.length) return []
  const total = arbs.length
  return arbs.map((a, i) => {
    const cx = svgW / 2 + (i - (total-1)/2) * 160
    const cy = rowY + nodeH + 100
    return { ...a, cx, cy }
  })
})

function arbPoints(arb) {
  const { cx, cy } = arb
  const w = 55, h = 28
  return `${cx},${cy-h} ${cx+w},${cy} ${cx},${cy+h} ${cx-w},${cy}`
}

function dcBadgeWidth(dc) {
  return Math.max(dc.length * 6 + 10, 30)
}
function stateBadgeWidth(state) {
  return Math.max(state.length * 5.5 + 10, 45)
}

const clusterStatus = computed(() =>
  cluster.status?.nodes?.[0]?.wsrep_cluster_status || 'Primary'
)
const certFailures = computed(() => cluster.certFailures)
</script>
