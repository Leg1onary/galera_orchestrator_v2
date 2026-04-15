<template>
  <g
      :transform="`translate(${x}, ${y})`"
      class="topo-node"
      style="cursor: pointer"
      @click="emit('click')"
  >
    <!-- Card background -->
    <rect
        :width="W"
        :height="H"
        rx="8"
        :fill="cardFill"
        :stroke="cardStroke"
        :stroke-width="maintenanceDrift ? 2 : 1.5"
    />

    <!-- Status dot с пульсацией для JOINING/JOINED -->
    <circle :cx="14" :cy="H / 2" r="5" :fill="dotColor">
      <animate
          v-if="isPulsing"
          attributeName="opacity"
          values="1;0.3;1"
          dur="1.2s"
          repeatCount="indefinite"
      />
    </circle>

    <!-- Node name (MAJOR fix: font-size 12px — floor) -->
    <text
        x="26"
        :y="H / 2 - 5"
        style="font-size: 12px; font-weight: 600;"
        :fill="textColor"
    >{{ truncate(node.name, 16) }}</text>

    <!-- Host:port (MAJOR fix: font-size 11px) -->
    <text
        x="26"
        :y="H / 2 + 8"
        style="font-size: 11px; font-family: monospace;"
        fill-opacity="0.65"
        :fill="mutedColor"
    >{{ node.host }}:{{ node.port }}</text>

    <!-- RO badge (MAJOR fix: font-size 10px) -->
    <g v-if="node.readonly">
      <rect
          :x="W - 28" :y="5"
          width="22" height="14"
          rx="3"
          fill="#b07a0020"
          stroke="#b07a00"
          stroke-width="0.8"
      />
      <text
          :x="W - 17" :y="15"
          style="font-size: 0.75rem; font-weight: 700;"
          text-anchor="middle"
          fill="#b07a00"
      >RO</text>
    </g>

    <!-- MAINT badge (MAJOR fix: font-size 10px, позиция пересчитана) -->
    <g v-if="node.maintenance">
      <rect
          :x="W - 46" :y="H - 18"
          width="40" height="13"
          rx="3"
          fill="#b07a0015"
          stroke="#b07a00"
          stroke-width="0.8"
      />
      <text
          :x="W - 26" :y="H - 8"
          style="font-size: 0.75rem; font-weight: 600;"
          text-anchor="middle"
          fill="#b07a00"
      >MAINT</text>
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
// MINOR fix: убраны неиспользуемые ARB_W, ARB_H
import { CARD_W, CARD_H } from './topology.constants'
import type { TopoNode } from '@/api/topology'

const W = CARD_W
const H = CARD_H

const props = defineProps<{
  node: TopoNode
  x: number
  y: number
}>()
const emit = defineEmits<{ click: [] }>()

// BLOCKER fix: ключи приведены к реальным значениям из ТЗ п.7.3
const STATE_COLORS: Record<string, string> = {
  SYNCED:        '#437a22',   // --color-success
  DonorDesynced: '#006494',   // --color-blue
  Joining:       '#d19900',   // --color-gold
  Joined:        '#d19900',
  Error:         '#a12c7b',   // --color-error
  Offline:       '#7a7974',   // --color-text-muted
}

// MAJOR fix: offline = state_comment null ИЛИ нет lastCheckTs
const isOffline = computed(() =>
    !props.node.wsrep_local_state_comment || !props.node.lastCheckTs
)

const dotColor = computed(() => {
  if (isOffline.value) return STATE_COLORS.Offline
  return STATE_COLORS[props.node.wsrep_local_state_comment!] ?? STATE_COLORS.Error
})

const isPulsing = computed(() =>
    ['Joining', 'Joined'].includes(props.node.wsrep_local_state_comment ?? '')
)

// MINOR fix: maintenance_drift через camelCase + влияет и на fill
const maintenanceDrift = computed(() => props.node.maintenanceDrift ?? false)

const cardFill = computed(() => {
  if (maintenanceDrift.value) return 'var(--color-error-highlight)'
  return isOffline.value ? 'var(--color-surface-offset)' : 'var(--color-surface)'
})

const cardStroke = computed(() => {
  if (maintenanceDrift.value) return 'var(--color-error)'
  return 'var(--color-border)'
})

const textColor = computed(() =>
    isOffline.value ? 'var(--color-text-muted)' : 'var(--color-text)'
)

const mutedColor = 'var(--color-text-muted)'

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '…' : s
}
</script>