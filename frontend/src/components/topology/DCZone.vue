<template>
  <g :transform="`translate(${x}, ${y})`">

    <!-- Zone border -->
    <rect
        :width="width"
        :height="height"
        rx="10"
        fill="var(--color-surface-offset)"
        stroke="var(--color-divider)"
        stroke-width="1"
        stroke-dasharray="6 3"
    />

    <!-- DC label (MAJOR fix: text-transform и font-size через style) -->
    <text
        :x="DC_PAD"
        y="22"
        style="font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;"
        fill="var(--color-text-muted)"
    >{{ dc.name }}</text>

    <!-- Nodes -->
    <TopoNodeCard
        v-for="(node, i) in dc.nodes"
        :key="'n' + node.id"
        :node="node"
        :x="DC_PAD"
        :y="NODE_START_Y + i * (CARD_H + NODE_GAP)"
        @click="emit('nodeClick', node)"
    />

    <!-- Arbitrators — правее нод -->
    <TopoArbitratorCard
        v-for="(arb, i) in dc.arbitrators"
        :key="'a' + arb.id"
        :arb="arb"
        :x="DC_PAD + CARD_W + NODE_GAP"
        :y="NODE_START_Y + i * (ARB_H + NODE_GAP)"
    />

  </g>
</template>

<script setup lang="ts">
// BLOCKER fix: импортируем компоненты
import TopoNodeCard from './TopoNodeCard.vue'
import TopoArbitratorCard from './TopoArbitratorCard.vue'
// BLOCKER fix: убраны локальные дубли, всё из topology.constants
import { CARD_W, CARD_H, ARB_H, NODE_GAP, DC_PAD } from './topology.constants'
import type { TopoDatacenter, TopoNode } from '@/api/topology'

const NODE_START_Y = 36  // высота заголовка зоны — не в topology.constants (специфично для DCZone)

const props = defineProps<{
  dc: TopoDatacenter
  x: number
  y: number
  width: number
  height: number
}>()

const emit = defineEmits<{ nodeClick: [node: TopoNode] }>()
</script>