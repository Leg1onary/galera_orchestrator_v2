<template>
  <div class="page-nodes">
    <!-- Toolbar -->
    <div class="nodes-toolbar">
      <div class="search-wrap">
        <IconField iconPosition="left">
          <InputIcon class="pi pi-search" />
          <InputText v-model="filter" placeholder="Поиск по имени, IP, DC, состоянию…" class="search-input" />
        </IconField>
        <Button v-if="filter" icon="pi pi-times" text size="small" @click="filter = ''" />
        <span class="search-count">{{ filteredNodes.length }} / {{ cluster.nodes.length }}</span>
      </div>
      <Button
        :icon="notifEnabled ? 'pi pi-bell-slash' : 'pi pi-bell'"
        :label="notifEnabled ? 'Уведомления вкл' : 'Уведомления'"
        size="small" :outlined="!notifEnabled" @click="toggleNotifications" />
    </div>

    <!-- Node grid -->
    <div class="nodes-grid mt-3">
      <NodeCard v-for="node in filteredNodes" :key="node.id"
        :node="node" :sparkline="cluster.sparklines[node.id]" />
    </div>

    <div v-if="filteredNodes.length === 0" class="no-results">
      <i class="pi pi-search" style="font-size:2rem;color:var(--color-text-muted)" />
      <p>Нода не найдена по запросу «{{ filter }}»</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useWebNotification } from '@vueuse/core'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import Button from 'primevue/button'
import NodeCard from '@/components/nodes/NodeCard.vue'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()
const filter = ref('')
const notifEnabled = ref(false)

const filteredNodes = computed(() => {
  const q = filter.value.toLowerCase()
  if (!q) return cluster.nodes
  return cluster.nodes.filter(n =>
    (n.name || n.id || '').toLowerCase().includes(q) ||
    (n.host || '').toLowerCase().includes(q) ||
    (n.dc || '').toLowerCase().includes(q) ||
    (n.wsrep_local_state_comment || '').toLowerCase().includes(q) ||
    (n.wsrep_cluster_status || '').toLowerCase().includes(q)
  )
})

// ── useWebNotification ───────────────────────────────────────────
const { isSupported, permissionGranted, requestPermission, show } = useWebNotification({
  title: 'Galera Orchestrator',
  icon: '/favicon.svg',
})

async function toggleNotifications() {
  if (notifEnabled.value) { notifEnabled.value = false; return }
  if (!isSupported.value) { alert('Браузерные уведомления не поддерживаются'); return }
  await requestPermission()
  if (permissionGranted.value) notifEnabled.value = true
}

// Watch for triggers
watch(() => cluster.nodes, (nodes) => {
  if (!notifEnabled.value) return
  nodes.forEach(n => {
    if (n.wsrep_cluster_status && n.wsrep_cluster_status !== 'Primary')
      show({ title: 'Galera Orchestrator', body: `${n.name}: non-Primary!` })
    if (parseFloat(n.wsrep_flow_control_paused) > 0.1)
      show({ title: 'Flow Control', body: `${n.name}: fc_paused = ${n.wsrep_flow_control_paused}` })
    if (n.online === false)
      show({ title: 'Нода Offline', body: `${n.name}: OFFLINE` })
  })
}, { deep: true })
</script>

<style scoped>
.page-nodes { display: flex; flex-direction: column; }
.nodes-toolbar { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.search-wrap { display: flex; align-items: center; gap: 0.5rem; flex: 1; min-width: 200px; }
.search-input { width: 100%; }
.search-count { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; }
.mt-3 { margin-top: 1rem; }
.no-results { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; padding: 3rem 1rem; color: var(--color-text-muted); text-align: center; }
</style>
