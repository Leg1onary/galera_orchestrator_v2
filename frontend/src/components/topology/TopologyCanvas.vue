<!--
  SVG топология без внешних зависимостей.
  Раскладка: DC-зоны горизонтально, ноды внутри вертикально.
  Линии связи: curved bezier между центрами нод из разных DC.
  Unassigned ноды — в зоне "No DC" справа.
-->
<template>
  <div class="canvas-wrapper" ref="wrapperRef">
    <svg
        :viewBox="`0 0 ${svgW} ${svgH}`"
        :width="svgW"
        :height="svgH"
        class="topology-svg"
    >
      <!-- Defs: маркер для стрелки на линиях -->
      <defs>
        <marker
            v-for="state in CONNECTION_STATES"
            :key="state.id"
            :id="state.id"
            markerWidth="6" markerHeight="6"
            refX="5" refY="3"
            orient="auto"
        >
          <path d="M0,0 L0,6 L6,3 z" :fill="state.color" />
        </marker>
      </defs>

      <!-- Connection lines — рендерим ДО зон чтобы линии были под карточками -->
      <g class="connections">
        <path
            v-for="(line, i) in connectionPaths"
            :key="i"
            :d="line.d"
            :stroke="line.color"
            stroke-width="1.5"
            fill="none"
            stroke-opacity="0.6"
            :marker-end="`url(#${line.markerId})`"
        />
      </g>

      <!-- DC Zones -->
      <DCZone
          v-for="zone in zones"
          :key="zone.dc.id"
          :dc="zone.dc"
          :x="zone.x"
          :y="zone.y"
          :width="zone.width"
          :height="zone.height"
          @node-click="emit('nodeClick', $event)"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import DCZone from './DCZone.vue'
import { CARD_W, CARD_H,  ARB_W, ARB_H } from './topology.constants'
import type { TopologyData, TopoNode, TopoDatacenter } from '@/api/topology'

const PADDING = 16
const NODE_GAP = 10
const NODE_START_Y = 36
const ZONE_GAP = 32     // горизонтальный отступ между DC-зонами
const ZONE_PADDING_X = 16
const ZONE_PADDING_Y = 12
const CANVAS_MARGIN = 24

// Маркеры стрелок для разных типов соединений
const CONNECTION_STATES = [
  { id: 'arrow-active', color: '#437a22' },
  { id: 'arrow-slow',   color: '#d19900' },
  { id: 'arrow-error',  color: '#a12c7b' },
]

const props = defineProps<{
  topology: TopologyData
}>()

const emit = defineEmits<{ nodeClick: [node: TopoNode] }>()

// Все DC включая виртуальную "No DC" для unassigned нод
const allDCs = computed((): TopoDatacenter[] => {
  const dcs = [...props.topology.datacenters]
  const hasUnassigned =
      props.topology.unassigned_nodes.length > 0 ||
      props.topology.unassigned_arbitrators.length > 0
  if (hasUnassigned) {
    dcs.push({
      id: -1,
      name: 'No DC',
      nodes: props.topology.unassigned_nodes,
      arbitrators: props.topology.unassigned_arbitrators,
    })
  }
  return dcs
})

// Высота зоны = заголовок + все ноды/арбитраторы + отступы
function zoneHeight(dc: TopoDatacenter): number {
  const itemCount = Math.max(dc.nodes.length, 1)
  return NODE_START_Y + itemCount * (CARD_H + NODE_GAP) - NODE_GAP + ZONE_PADDING_Y
}

// Ширина зоны = карточка ноды + арбитраторы если есть
function zoneWidth(dc: TopoDatacenter): number {
  const hasArbs = dc.arbitrators.length > 0
  const base = CARD_W + ZONE_PADDING_X * 2
  return hasArbs ? base + ARB_W + 12 : base
}

// Позиции зон
const zones = computed(() => {
  let curX = CANVAS_MARGIN
  return allDCs.value.map((dc) => {
    const w = zoneWidth(dc)
    const h = zoneHeight(dc)
    const zone = { dc, x: curX, y: CANVAS_MARGIN, width: w, height: h }
    curX += w + ZONE_GAP
    return zone
  })
})

// Размер SVG
const svgW = computed(() => {
  if (zones.value.length === 0) return 400
  const last = zones.value[zones.value.length - 1]
  return last.x + last.width + CANVAS_MARGIN
})
const svgH = computed(() => {
  if (zones.value.length === 0) return 300
  return Math.max(...zones.value.map((z) => z.y + z.height)) + CANVAS_MARGIN
})

// Центр карточки ноды в глобальных координатах SVG
function nodeCenter(nodeId: number): { x: number; y: number } | null {
  for (const zone of zones.value) {
    const idx = zone.dc.nodes.findIndex((n) => n.id === nodeId)
    if (idx === -1) continue
    return {
      x: zone.x + PADDING + CARD_W,   // правый край карточки
      y: zone.y + NODE_START_Y + idx * (CARD_H + NODE_GAP) + CARD_H / 2,
    }
  }
  return null
}

// Линии связи между нодами
const connectionPaths = computed(() => {
  const paths: { d: string; color: string; markerId: string }[] = []

  for (const [aId, bId] of props.topology.connections) {
    const a = nodeCenter(aId)
    const b = nodeCenter(bId)
    if (!a || !b) continue

    // Определяем цвет линии по состоянию обеих нод
    const nodeA = findNode(aId)
    const nodeB = findNode(bId)
    const color = connectionColor(nodeA, nodeB)
    const markerId = color === '#437a22'
        ? 'arrow-active'
        : color === '#d19900' ? 'arrow-slow' : 'arrow-error'

    // Кубическая безье-кривая между правым краем A и левым краем B
    const aRight = { x: a.x, y: a.y }
    const bLeft  = { x: b.x - CARD_W, y: b.y }  // левый край второй карточки
    const cp1x = aRight.x + (bLeft.x - aRight.x) * 0.5
    const d = `M ${aRight.x} ${aRight.y} C ${cp1x} ${aRight.y}, ${cp1x} ${bLeft.y}, ${bLeft.x} ${bLeft.y}`

    paths.push({ d, color, markerId })
  }
  return paths
})

function findNode(id: number): TopoNode | undefined {
  for (const dc of allDCs.value) {
    const n = dc.nodes.find((n) => n.id === id)
    if (n) return n
  }
}

function connectionColor(a?: TopoNode, b?: TopoNode): string {
  if (!a || !b) return '#7a7974'
  const bothSynced = a.wsrep_local_state_comment === 'Synced' &&
      b.wsrep_local_state_comment === 'Synced'
  if (bothSynced) return '#437a22'
  const eitherOffline = !a.wsrep_connected || !b.wsrep_connected
  if (eitherOffline) return '#a12c7b'
  return '#d19900'
}
</script>

<style scoped>
.canvas-wrapper {
  overflow: auto;
  width: 100%;
  height: 100%;
  padding: var(--space-4);
}
.topology-svg {
  display: block;
  /* SVG использует CSS custom properties напрямую через fill/stroke="var(--color-*)" */
  --color-surface: var(--color-surface);
}
</style>