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
      <!-- Defs: маркеры стрелок для каждого типа соединения -->
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

      <!-- Connection lines — ДО зон чтобы линии были под карточками -->
      <g class="connections">
        <path
            v-for="(line, i) in connectionPaths"
            :key="i"
            :d="line.d"
            :stroke="line.color"
            :stroke-width="CONN_STROKE"
            :stroke-dasharray="line.dash > 0 ? `${line.dash} ${line.dash}` : undefined"
            fill="none"
            stroke-opacity="0.65"
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
import { ref, computed } from 'vue'
import DCZone from './DCZone.vue'
// BLOCKER fix: используем все константы из файла, без локальных переопределений
import {
  CARD_W, CARD_H,
  ARB_W, ARB_H,
  NODE_GAP,
  DC_PAD, DC_GAP,
  CONN_STROKE, CONN_DASH_SYNC,
} from './topology.constants'
// MAJOR fix: используем актуальный тип из topology-7.ts
import type { TopologyViewModel, TopoNode, TopoDatacenter } from '@/api/topology'

const CANVAS_MARGIN = 24
const NODE_START_Y  = 36  // высота заголовка DC-зоны

// Маркеры стрелок с токен-цветами через CSS variables (MINOR fix)
// Hex используем только как fallback — SVG не поддерживает var() в атрибутах fill
const CONNECTION_STATES = [
  { id: 'arrow-synced', color: '#437a22' },  // --color-success (light)
  { id: 'arrow-sync',   color: '#d19900' },  // --color-gold
  { id: 'arrow-error',  color: '#a12c7b' },  // --color-error
] as const

// ── Props / Emits ─────────────────────────────────────────────────────────────
const props = defineProps<{
  topology: TopologyViewModel
}>()
const emit = defineEmits<{ nodeClick: [node: TopoNode] }>()

// MAJOR fix: объявляем ref для wrapper
const wrapperRef = ref<HTMLDivElement>()

// OFFLINE-состояния по ТЗ п.7.3
const OFFLINE_STATES = new Set([null, undefined, 'OFFLINE'])
function isOffline(node: TopoNode): boolean {
  return OFFLINE_STATES.has(node.wsrep_local_state_comment as any) || !node.last_check_ts
}

// ── All DCs включая виртуальную "No DC" ──────────────────────────────────────
const allDCs = computed((): TopoDatacenter[] => {
  const dcs = [...props.topology.datacenters]
  // MINOR fix: camelCase поля из topology-7.ts
  const hasUnassigned =
      props.topology.unassignedNodes.length > 0 ||
      props.topology.unassignedArbitrators.length > 0
  if (hasUnassigned) {
    dcs.push({
      id: -1,
      name: 'No DC',
      nodes: props.topology.unassignedNodes,
      arbitrators: props.topology.unassignedArbitrators,
    })
  }
  return dcs
})

// ── Размеры зон ───────────────────────────────────────────────────────────────
// MAJOR fix: учитываем и арбитраторы для высоты зоны
function zoneHeight(dc: TopoDatacenter): number {
  const itemCount = Math.max(dc.nodes.length, dc.arbitrators.length, 1)
  return NODE_START_Y + itemCount * (CARD_H + NODE_GAP) - NODE_GAP + DC_PAD
}

function zoneWidth(dc: TopoDatacenter): number {
  const hasArbs = dc.arbitrators.length > 0
  // BLOCKER fix: используем DC_PAD из констант (не локальный ZONE_PADDING_X)
  const base = CARD_W + DC_PAD * 2
  return hasArbs ? base + ARB_W + NODE_GAP : base
}

// ── Позиции зон ───────────────────────────────────────────────────────────────
const zones = computed(() => {
  let curX = CANVAS_MARGIN
  return allDCs.value.map((dc) => {
    const w = zoneWidth(dc)
    const h = zoneHeight(dc)
    const zone = { dc, x: curX, y: CANVAS_MARGIN, width: w, height: h }
    curX += w + DC_GAP  // BLOCKER fix: DC_GAP из констант
    return zone
  })
})

// ── SVG размеры ───────────────────────────────────────────────────────────────
const svgW = computed(() => {
  if (!zones.value.length) return 400
  const last = zones.value[zones.value.length - 1]
  return last.x + last.width + CANVAS_MARGIN
})
const svgH = computed(() => {
  if (!zones.value.length) return 300
  return Math.max(...zones.value.map((z) => z.y + z.height)) + CANVAS_MARGIN
})

// ── Центр правого края карточки ноды в глобальных координатах ─────────────────
function nodeCenter(nodeId: number): { x: number; y: number } | null {
  for (const zone of zones.value) {
    const idx = zone.dc.nodes.findIndex((n) => n.id === nodeId)
    if (idx === -1) continue
    return {
      // MAJOR fix: DC_PAD из констант вместо локального PADDING
      x: zone.x + DC_PAD + CARD_W,
      y: zone.y + NODE_START_Y + idx * (CARD_H + NODE_GAP) + CARD_H / 2,
    }
  }
  return null
}

// ── Линии связи ───────────────────────────────────────────────────────────────
const connectionPaths = computed(() => {
  const paths: { d: string; color: string; dash: number; markerId: string }[] = []

  for (const [aId, bId] of props.topology.connections) {
    const a = nodeCenter(aId)
    const b = nodeCenter(bId)
    if (!a || !b) continue

    const nodeA = findNode(aId)
    const nodeB = findNode(bId)
    const { color, markerId, dash } = connectionStyle(nodeA, nodeB)

    // Левый край карточки B — правый край A + отступ до следующей зоны
    const aRight = { x: a.x, y: a.y }
    const bLeft  = { x: b.x - CARD_W, y: b.y }
    const cp1x   = aRight.x + (bLeft.x - aRight.x) * 0.5
    const d      = `M ${aRight.x} ${aRight.y} C ${cp1x} ${aRight.y}, ${cp1x} ${bLeft.y}, ${bLeft.x} ${bLeft.y}`

    paths.push({ d, color, dash, markerId })
  }
  return paths
})

function findNode(id: number): TopoNode | undefined {
  for (const dc of allDCs.value) {
    const n = dc.nodes.find((n) => n.id === id)
    if (n) return n
  }
}

// BLOCKER fix: SYNCED uppercase + MAJOR fix: isOffline() вместо wsrep_connected
function connectionStyle(
    a?: TopoNode,
    b?: TopoNode,
): { color: string; markerId: string; dash: number } {
  if (!a || !b) {
    return { color: '#7a7974', markerId: 'arrow-error', dash: 0 }
  }
  if (isOffline(a) || isOffline(b)) {
    return { color: '#a12c7b', markerId: 'arrow-error', dash: 0 }
  }
  // BLOCKER fix: uppercase 'SYNCED'
  const bothSynced =
      a.wsrep_local_state_comment === 'SYNCED' &&
      b.wsrep_local_state_comment === 'SYNCED'
  if (bothSynced) {
    return { color: '#437a22', markerId: 'arrow-synced', dash: CONN_DASH_ACTIVE }
  }
  // DONOR/JOINER/DESYNCED — синхронизация в процессе (ТЗ п.12.4)
  return { color: '#d19900', markerId: 'arrow-sync', dash: CONN_DASH_SYNC }
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
}
</style>