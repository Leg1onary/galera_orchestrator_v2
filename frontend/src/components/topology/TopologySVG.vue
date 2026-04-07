<template>
  <div class="topology-container">
    <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="topology-svg">
      <!-- DC segments -->
      <g v-for="dc in dcGroups" :key="dc.name">
        <rect :x="dc.x - 12" :y="dc.y - 30" :width="dc.w + 24" :height="dc.h + 44"
          fill="none" :stroke="dcColor" stroke-width="1" stroke-dasharray="6,4" rx="10"/>
        <text :x="dc.x" :y="dc.y - 12" fill="#6b7280" font-size="11" font-weight="600" letter-spacing="1">
          {{ dc.name }}
        </text>
      </g>

      <!-- Connection lines between nodes -->
      <g v-for="link in links" :key="link.id">
        <line :x1="link.x1" :y1="link.y1" :x2="link.x2" :y2="link.y2"
          stroke="#2d3748" stroke-width="1.5" stroke-dasharray="4,3"/>
      </g>

      <!-- Node circles -->
      <g v-for="n in nodePositions" :key="n.id" class="node-group"
        :transform="`translate(${n.x},${n.y})`">
        <circle :r="nodeR" :fill="nodeFill(n.state)" :stroke="nodeStroke(n.state)"
          stroke-width="2" />
        <circle :r="nodeR - 4" fill="none" :stroke="nodeStroke(n.state)"
          stroke-width="1" opacity="0.4"/>
        <!-- Ping dot -->
        <circle :r="4" :cx="nodeR - 2" :cy="-(nodeR - 2)"
          :fill="n.online ? '#22c55e' : '#ef4444'" />
        <text text-anchor="middle" :y="5" fill="#e2e8f0" font-size="11" font-weight="700">{{ n.label }}</text>
        <text text-anchor="middle" :y="nodeR + 16" fill="#6b7280" font-size="10">{{ n.state }}</text>
        <text text-anchor="middle" :y="nodeR + 28" fill="#475569" font-size="9">{{ n.host }}</text>
      </g>

      <!-- Arbitrator diamonds -->
      <g v-for="a in arbPositions" :key="a.id" :transform="`translate(${a.x},${a.y})`">
        <polygon :points="`0,${-arbR} ${arbR},0 0,${arbR} ${-arbR},0`"
          :fill="arbFill(a.status)" stroke="#374151" stroke-width="2"/>
        <text text-anchor="middle" :y="4" fill="#e2e8f0" font-size="9" font-weight="600">ARB</text>
        <text text-anchor="middle" :y="arbR + 14" fill="#6b7280" font-size="9">{{ a.id }}</text>
      </g>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  nodes:       { type: Array, default: () => [] },
  arbitrators: { type: Array, default: () => [] },
})

const svgW   = 700
const svgH   = 320
const nodeR  = 32
const arbR   = 20
const dcColor= '#374151'

// Group nodes by DC
const dcGroups = computed(() => {
  const map = {}
  props.nodes.forEach(n => { const dc = n.dc || 'DC'; (map[dc] = map[dc] || []).push(n) })
  const dcNames = Object.keys(map)
  const colW = svgW / dcNames.length
  return dcNames.map((name, di) => {
    const dcNodes = map[name]
    const col = di
    const x = col * colW + 60
    const baseY = 80
    const rowH  = 90
    return {
      name,
      nodes: dcNodes,
      x,
      y: baseY,
      w: Math.max(100, (dcNodes.length - 1) * 100),
      h: 100,
    }
  })
})

// Node positions
const nodePositions = computed(() => {
  const map = {}
  props.nodes.forEach(n => { const dc = n.dc || 'DC'; (map[dc] = map[dc] || []).push(n) })
  const dcNames = Object.keys(map)
  const colW = svgW / (dcNames.length || 1)
  const result = []
  dcNames.forEach((dc, di) => {
    const dcNodes = map[dc]
    dcNodes.forEach((n, ni) => {
      result.push({
        id: n.id,
        label: n.name || n.id,
        x: di * colW + 80 + ni * 110,
        y: 130,
        host: n.host,
        state: n.wsrep_local_state_comment || (n.online ? 'Synced' : 'Offline'),
        online: n.online !== false,
      })
    })
  })
  // If only one DC, spread nodes evenly
  if (dcNames.length <= 1 && props.nodes.length > 0) {
    const spacing = svgW / (props.nodes.length + 1)
    props.nodes.forEach((n, i) => {
      result[i] = { ...result[i], x: spacing * (i + 1), y: 130 }
    })
  }
  return result
})

// Arbitrator positions
const arbPositions = computed(() => {
  const spacing = svgW / (props.arbitrators.length + 1)
  return props.arbitrators.map((a, i) => ({
    id: a.id,
    x: spacing * (i + 1),
    y: 250,
    status: a.status || 'unknown',
  }))
})

// Connection links between all node pairs
const links = computed(() => {
  const pos = nodePositions.value
  const result = []
  for (let i = 0; i < pos.length; i++) {
    for (let j = i + 1; j < pos.length; j++) {
      result.push({ id: `${pos[i].id}-${pos[j].id}`, x1: pos[i].x, y1: pos[i].y, x2: pos[j].x, y2: pos[j].y })
    }
  }
  // Arb to all nodes
  arbPositions.value.forEach(a => {
    pos.forEach(n => {
      result.push({ id: `${n.id}-${a.id}`, x1: n.x, y1: n.y, x2: a.x, y2: a.y })
    })
  })
  return result
})

function nodeFill(state) {
  const s = (state || '').toLowerCase()
  if (s === 'synced')  return '#052e16'
  if (s.includes('donor'))   return '#451a03'
  if (s.includes('join'))    return '#172554'
  if (s.includes('offline')) return '#1c0a0a'
  return '#1e2535'
}
function nodeStroke(state) {
  const s = (state || '').toLowerCase()
  if (s === 'synced')  return '#22c55e'
  if (s.includes('donor'))   return '#f59e0b'
  if (s.includes('join'))    return '#3b82f6'
  if (s.includes('offline')) return '#ef4444'
  return '#374151'
}
function arbFill(status) {
  const s = (status || '').toLowerCase()
  if (s === 'running') return '#052e16'
  if (s === 'offline') return '#1c0a0a'
  return '#1e2535'
}
</script>

<style scoped>
.topology-container { width: 100%; overflow-x: auto; }
.topology-svg { display: block; width: 100%; height: auto; min-height: 300px; background: var(--color-bg-primary); border-radius: var(--radius-sm); }
.node-group { cursor: default; }
</style>
