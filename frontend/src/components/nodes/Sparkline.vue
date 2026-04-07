<template>
  <div class="sparkline-wrap">
    <div class="sparkline-item">
      <div class="sparkline-label">FLOW CONTROL</div>
      <div class="sparkline-value" :class="flowClass">{{ flowVal }}</div>
      <svg class="sparkline-svg" :height="height" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none">
        <polyline
          :points="flowPoints"
          fill="none"
          :stroke="flowClass === 'warn' ? 'var(--warning)' : 'var(--primary)'"
          stroke-width="1.5"
          stroke-linejoin="round"
          stroke-linecap="round"
        />
      </svg>
    </div>
    <div class="sparkline-item">
      <div class="sparkline-label">RECV QUEUE</div>
      <div class="sparkline-value" :class="recvClass">{{ recvVal }}</div>
      <svg class="sparkline-svg" :height="height" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none">
        <polyline
          :points="recvPoints"
          fill="none"
          :stroke="recvClass === 'warn' ? 'var(--warning)' : 'var(--success)'"
          stroke-width="1.5"
          stroke-linejoin="round"
          stroke-linecap="round"
        />
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  flowHistory: { type: Array, default: () => [0] },
  recvHistory: { type: Array, default: () => [0] },
})

const width  = 80
const height = 24

function makePoints(data) {
  if (!data || data.length === 0) return `0,${height} ${width},${height}`
  const len  = data.length
  const max  = Math.max(...data, 0.001)
  return data.map((v, i) => {
    const x = (i / Math.max(len - 1, 1)) * width
    const y = height - (v / max) * (height - 2) - 1
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

const flowPoints = computed(() => makePoints(props.flowHistory))
const recvPoints = computed(() => makePoints(props.recvHistory))

const flowVal = computed(() => {
  const v = props.flowHistory?.at(-1) ?? 0
  return typeof v === 'number' ? v.toFixed(3) : '0.000'
})
const recvVal = computed(() => {
  const v = props.recvHistory?.at(-1) ?? 0
  return String(v)
})

const flowClass = computed(() => {
  const v = parseFloat(flowVal.value)
  return v > 0.05 ? 'warn' : 'ok'
})
const recvClass = computed(() => {
  const v = parseInt(recvVal.value, 10)
  return v > 0 ? 'warn' : 'ok'
})
</script>
