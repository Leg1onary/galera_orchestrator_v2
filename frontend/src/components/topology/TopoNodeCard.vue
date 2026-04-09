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
        stroke-width="1.5"
    />

    <!-- Status dot -->
    <circle
        :cx="14"
        :cy="H / 2"
        r="5"
        :fill="dotColor"
    >
      <animate
          v-if="isPulsing"
          attributeName="opacity"
          values="1;0.3;1"
          dur="1.2s"
          repeatCount="indefinite"
      />
    </circle>

    <!-- Node name -->
    <text
        x="26"
        :y="H / 2 - 6"
        font-size="11"
        font-weight="600"
        :fill="textColor"
    >{{ truncate(node.name, 16) }}</text>

    <!-- Host:port -->
    <text
        x="26"
        :y="H / 2 + 8"
        font-size="9"
        font-family="monospace"
        :fill="mutedColor"
    >{{ node.host }}:{{ node.port }}</text>

    <!-- RO badge -->
    <g v-if="node.read_only">
      <rect
          :x="W - 28" :y="6"
          width="22" height="13"
          rx="3"
          fill="#b07a0020"
          stroke="#b07a00"
          stroke-width="0.8"
      />
      <text
          :x="W - 17" :y="15.5"
          font-size="8"
          font-weight="700"
          text-anchor="middle"
          fill="#b07a00"
      >RO</text>
    </g>

    <!-- MAINT badge -->
    <g v-if="node.maintenance">
      <rect
          :x="W - 44" :y="H - 18"
          width="38" height="12"
          rx="3"
          fill="#b07a0015"
          stroke="#b07a00"
          stroke-width="0.8"
      />
      <text
          :x="W - 25" :y="H - 9"
          font-size="7.5"
          font-weight="600"
          text-anchor="middle"
          fill="#b07a00"
      >MAINT</text>
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CARD_W, CARD_H,  ARB_W, ARB_H } from './topology.constants'
import type { TopoNode } from '@/api/topology'

// Card dimensions — константы для вычисления позиций линий снаружи

const W = CARD_W
const H = CARD_H

const props = defineProps<{
  node: TopoNode
  x: number
  y: number
}>()
const emit = defineEmits<{ click: [] }>()

// Цвета берём из CSS custom properties через getComputedStyle
// SVG не поддерживает var() в fill напрямую, поэтому используем
// захардкоженные значения из Nexus палитры (light mode).
// TODO: при добавлении dark mode toggle — читать из document root.
const STATE_COLORS: Record<string, string> = {
  Synced:           '#437a22',
  'Donor/Desynced': '#006494',
  Joining:          '#d19900',
  Joined:           '#d19900',
  Error:            '#a12c7b',
  Offline:          '#7a7974',
}

const dotColor = computed(() => {
  if (!props.node.wsrep_connected || !props.node.last_seen) return STATE_COLORS.Offline
  return STATE_COLORS[props.node.wsrep_local_state_comment ?? 'Offline'] ?? STATE_COLORS.Error
})

const isPulsing = computed(() =>
    ['Joining', 'Joined'].includes(props.node.wsrep_local_state_comment ?? '')
)

const isOnline = computed(() => props.node.wsrep_connected && props.node.last_seen)

const cardFill = computed(() =>
    isOnline.value ? 'var(--color-surface)' : 'var(--color-surface-offset)'
)

const cardStroke = computed(() => {
  if (props.node.maintenance_drift) return '#a12c7b'
  if (!isOnline.value) return 'var(--color-border)'
  return 'var(--color-border)'
})

const textColor = computed(() =>
    isOnline.value ? 'var(--color-text)' : 'var(--color-text-muted)'
)

const mutedColor = 'var(--color-text-muted)'

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '…' : s
}
</script>