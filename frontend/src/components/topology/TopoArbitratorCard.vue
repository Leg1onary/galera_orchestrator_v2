<template>
  <g
      :transform="`translate(${x}, ${y})`"
  >
    <!-- Ромб — визуальное отличие арбитратора от ноды -->
    <polygon
        :points="diamondPoints"
        :fill="isRunning ? 'var(--color-surface)' : 'var(--color-surface-offset)'"
        :stroke="isRunning ? '#006494' : 'var(--color-border)'"
        stroke-width="1.5"
    />
    <text
        :x="CX"
        :y="CY - 5"
        text-anchor="middle"
        font-size="10"
        font-weight="600"
        fill="var(--color-text)"
    >{{ truncate(arb.name, 12) }}</text>
    <text
        :x="CX"
        :y="CY + 7"
        text-anchor="middle"
        font-size="8"
        font-family="monospace"
        fill="var(--color-text-muted)"
    >ARB</text>

    <!-- Running indicator -->
    <circle
        :cx="CX + 22" :cy="CY - 14"
        r="4"
        :fill="isRunning ? '#437a22' : '#7a7974'"
    />
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CARD_W, CARD_H,  ARB_W, ARB_H } from './topology.constants'
import type { TopoArbitrator } from '@/api/topology'

// Размеры — ромб вписан в прямоугольник 80x56
const CX = ARB_W / 2
const CY = ARB_H / 2

const props = defineProps<{
  arb: TopoArbitrator
  x: number
  y: number
}>()

const isRunning = computed(() => props.arb.is_running && props.arb.last_seen)

// Точки ромба
const diamondPoints = computed(() => {
  const [cx, cy] = [CX, CY]
  const hw = CX - 4   // half-width
  const hh = CY - 4   // half-height
  return `${cx},${cy - hh} ${cx + hw},${cy} ${cx},${cy + hh} ${cx - hw},${cy}`
})

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '…' : s
}
</script>