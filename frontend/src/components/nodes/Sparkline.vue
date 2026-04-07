<template>
  <div class="sparkline-wrap">
    <svg :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none"
      :width="width" :height="height" style="display:block;width:100%">
      <polyline :points="points" fill="none" :stroke="lineColor" stroke-width="1.5" stroke-linejoin="round" />
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:      { type: Array, default: () => [] },
  threshold: { type: Number, default: 0 },
  colorOk:   { type: String, default: '#22c55e' },
  colorWarn: { type: String, default: '#f59e0b' },
  width:     { type: Number, default: 120 },
  height:    { type: Number, default: 30 },
})

const lineColor = computed(() => {
  const last = props.data[props.data.length - 1] || 0
  return last > props.threshold ? props.colorWarn : props.colorOk
})

const points = computed(() => {
  const d = props.data
  if (d.length < 2) return ''
  const max = Math.max(...d, props.threshold * 2, 0.001)
  return d.map((v, i) => {
    const x = (i / (d.length - 1)) * props.width
    const y = props.height - (v / max) * (props.height - 4) - 2
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
})
</script>
