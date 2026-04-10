<template>
  <g :transform="`translate(${x}, ${y})`">

    <!-- Ромб -->
    <polygon
        :points="diamondPoints"
        :fill="arbFill"
        :stroke="arbStroke"
        stroke-width="1.5"
    />

    <!-- Имя (MAJOR fix: font-size 12px) -->
    <text
        :x="CX"
        :y="CY - 6"
        text-anchor="middle"
        style="font-size: 12px; font-weight: 600;"
        fill="var(--color-text)"
    >{{ truncate(arb.name, 10) }}</text>

    <!-- ARB label (MAJOR fix: font-size 10px) -->
    <text
        :x="CX"
        :y="CY + 7"
        text-anchor="middle"
        style="font-size: 10px;"
        fill="var(--color-text-muted)"
    >ARB</text>

    <!-- State indicator — привязан к правому углу ромба (MINOR fix) -->
    <circle
        :cx="CX + hw - 4"
        :cy="CY - hh + 4"
        r="4"
        :fill="indicatorColor"
    />
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
// MINOR fix: убраны CARD_W, CARD_H — не используются
import { ARB_W, ARB_H } from './topology.constants'
import type { TopoArbitrator } from '@/api/topology'

const CX = ARB_W / 2
const CY = ARB_H / 2
const hw = CX - 4   // half-width ромба
const hh = CY - 4   // half-height ромба

const props = defineProps<{
  arb: TopoArbitrator
  x: number
  y: number
}>()

// MAJOR fix: вычисляем state по ТЗ п.7.4: online/degraded/offline
// online   = sshOk && garbdRunning
// degraded = sshOk && !garbdRunning
// offline  = !sshOk
const arbState = computed((): 'online' | 'degraded' | 'offline' => {
  // BLOCKER fix: garbdRunning (camelCase из topology-7.ts), lastCheckTs
  if (!props.arb.sshOk || !props.arb.lastCheckTs) return 'offline'
  if (!props.arb.garbdRunning) return 'degraded'
  return 'online'
})

const indicatorColor = computed(() => {
  switch (arbState.value) {
    case 'online':   return '#437a22'   // --color-success
    case 'degraded': return '#d19900'   // --color-gold
    case 'offline':  return '#7a7974'   // muted
  }
})

const arbFill = computed(() =>
    arbState.value === 'offline'
        ? 'var(--color-surface-offset)'
        : 'var(--color-surface)'
)

const arbStroke = computed(() => {
  switch (arbState.value) {
    case 'online':   return '#006494'              // --color-blue
    case 'degraded': return 'var(--color-gold)'
    case 'offline':  return 'var(--color-border)'
  }
})

const diamondPoints = computed(() => {
  return `${CX},${CY - hh} ${CX + hw},${CY} ${CX},${CY + hh} ${CX - hw},${CY}`
})

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '…' : s
}
</script>