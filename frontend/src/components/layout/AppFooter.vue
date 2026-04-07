<template>
  <footer class="app-footer">
    <a
      :href="`https://github.com/Leg1onary/galera_orchestrator/commit/${cluster.gitSha}`"
      target="_blank"
      rel="noopener"
      style="font-family:var(--font-mono);font-size:0.72rem"
    >{{ shortSha }}</a>
    <span class="footer-sep"></span>
    <a href="https://github.com/Leg1onary/galera_orchestrator" target="_blank" rel="noopener">
      Leg1onary/galera_orchestrator
    </a>
    <span class="footer-sep"></span>
    <span>© 2026 Sergey Sholokhov</span>
    <span class="footer-sep"></span>
    <span>MIT License</span>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster.js'

const cluster = useClusterStore()

const shortSha = computed(() => {
  const sha = cluster.gitSha
  if (!sha || sha.startsWith('v')) return sha || 'v2.0.0'
  return sha.slice(0, 7)
})
</script>
