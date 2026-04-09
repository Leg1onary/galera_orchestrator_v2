<template>
  <g :transform="`translate(${x}, ${y})`">
    <!-- Zone border -->
    <rect
        :width="width"
        :height="height"
        rx="12"
        fill="var(--color-surface-offset)"
        :stroke="ZONE_STROKE"
        stroke-width="1"
        stroke-dasharray="6 3"
    />
    <!-- DC label -->
    <text
        x="16"
        y="22"
        font-size="11"
        font-weight="700"
        letter-spacing="0.05em"
        fill="var(--color-text-muted)"
        text-transform="uppercase"
    >
      {{ dc.name.toUpperCase() }}
    </text>

    <!-- Nodes -->
    <TopoNodeCard
        v-for="(node, i) in dc.nodes"
        :key="'n' + node.id"
        :node="node"
        :x="PADDING"
        :y="NODE_START_Y + i * (CARD_H + NODE_GAP)"
        @click="emit('nodeClick', node)"
    />

    <!-- Arbitrators — правее нод -->
    <TopoArbitratorCard
        v-for="(arb, i) in dc.arbitrators"
        :key="'a' + arb.id"
        :arb="arb"
        :x="PADDING + CARD_W + ARB_OFFSET_X"
        :y="NODE_START_Y + i * (ARB_H + NODE_GAP)"
    />
  </g>
</template>

<script setup lang="ts">
import { CARD_W, CARD_H,  ARB_W, ARB_H } from './topology.constants'
import type { TopoDatacenter, TopoNode } from '@/api/topology'

const PADDING = 16
const NODE_GAP = 10
const NODE_START_Y = 36
const ARB_OFFSET_X = 12
const ZONE_STROKE = 'var(--color-divider)'

const props = defineProps<{
  dc: TopoDatacenter
  x: number
  y: number
  width: number
  height: number
}>()

const emit = defineEmits<{ nodeClick: [node: TopoNode] }>()
</script>