<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Ноды кластера</h1>
        <p class="page-subtitle">Детальные wsrep-метрики по каждому узлу</p>
      </div>
      <div style="display:flex;align-items:center;gap:var(--space-2)">
        <label class="notif-toggle" title="Уведомления браузера при деградации кластера">
          <input type="checkbox" v-model="notifEnabled" @change="toggleNotifications">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          Уведомления
        </label>
        <button class="btn btn-ghost btn-sm" @click="cluster.fetchStatus()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
          </svg>
          Обновить
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="node-search-wrap">
      <input
        type="text"
        class="node-search-input"
        v-model="searchQuery"
        placeholder="Поиск по имени, IP, DC, состоянию..."
      />
      <span class="node-search-count">{{ filteredNodes.length }} из {{ cluster.nodes.length }}</span>
      <button
        v-if="searchQuery"
        class="btn btn-ghost btn-sm"
        @click="searchQuery = ''"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div v-if="cluster.loading && !cluster.nodes.length" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">
      <span class="spin-dot" style="margin-right:8px"></span>
      Загрузка данных…
    </div>

    <div v-else-if="!filteredNodes.length && searchQuery" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">
      Ничего не найдено по запросу «{{ searchQuery }}»
    </div>

    <div class="nodes-grid">
      <NodeCard
        v-for="node in filteredNodes"
        :key="node.id"
        :node="node"
        @action="handleNodeAction"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import NodeCard from '@/components/nodes/NodeCard.vue'
import { useClusterStore } from '@/stores/cluster.js'

const cluster        = useClusterStore()
const toast          = useToast()
const searchQuery    = ref('')
const notifEnabled   = ref(false)

const filteredNodes = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return cluster.nodes
  return cluster.nodes.filter(n => {
    const haystack = [
      n.name, n.id, n.host, n.dc,
      n.state, n.wsrep_local_state_comment,
    ].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(q)
  })
})

function toggleNotifications(e) {
  if (e.target.checked) {
    Notification.requestPermission().then(p => {
      if (p !== 'granted') {
        notifEnabled.value = false
        toast.add({ severity: 'warn', summary: 'Уведомления', detail: 'Разрешение не выдано', life: 3000 })
      }
    })
  }
}

async function handleNodeAction({ nodeId, action }) {
  try {
    await cluster.nodeAction(nodeId, action)
    toast.add({ severity: 'success', summary: 'Готово', detail: `${action} → ${nodeId}`, life: 3000 })
    await cluster.fetchStatus()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: String(e.message), life: 5000 })
  }
}
</script>
