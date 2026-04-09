<!-- ТЗ 6.2: лого, выбор контура, выбор кластера, статус кластера, logout -->
<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/api/client'
import type { Contour, Cluster } from '@/stores/cluster'

const props = defineProps<{
  username: string | null
  contours: Contour[]
  clusters: Cluster[]
  selectedContourId: number | null
  selectedClusterId: number | null
}>()

const emit = defineEmits<{
  (e: 'select-contour', id: number): void
  (e: 'select-cluster', id: number): void
  (e: 'logout'): void
}>()

// Статус выбранного кластера для индикатора в хедере
const { data: clusterStatus } = useQuery({
  queryKey: computed(() => ['cluster', props.selectedClusterId, 'status']),
  queryFn: () =>
      api
          .get(`/api/clusters/${props.selectedClusterId}/status`)
          .then((r) => r.data),
  enabled: computed(() => !!props.selectedClusterId),
  refetchInterval: 10_000,
  staleTime: 5_000,
})

const statusClass = computed(() => {
  const s = clusterStatus.value?.status
  if (s === 'healthy') return 'status-healthy'
  if (s === 'degraded') return 'status-degraded'
  if (s === 'critical') return 'status-critical'
  return 'status-unknown'
})
</script>

<template>
  <header class="app-header">
    <!-- Лого -->
    <div class="header-logo">
      <span class="logo-icon">⬡</span>
      <span class="logo-text">Galera Orchestrator</span>
    </div>

    <!-- Выбор контура -->
    <div class="header-selectors">
      <Dropdown
          :options="contours"
          :model-value="selectedContourId"
          option-label="name"
          option-value="id"
          placeholder="Контур"
          class="selector-contour"
          @change="(e: any) => emit('select-contour', e.value)"
      />

      <!-- Выбор кластера -->
      <Dropdown
          :options="clusters"
          :model-value="selectedClusterId"
          option-label="name"
          option-value="id"
          placeholder="Кластер"
          class="selector-cluster"
          @change="(e: any) => emit('select-cluster', e.value)"
      />

      <!-- Статус индикатор (ТЗ 6.2) -->
      <span v-if="clusterStatus" :class="['cluster-status-badge', statusClass]">
        {{ clusterStatus.status }}
      </span>
    </div>

    <!-- Пользователь и logout -->
    <div class="header-user">
      <span class="username">{{ username }}</span>
      <Button
          label="Logout"
          severity="secondary"
          size="small"
          text
          @click="emit('logout')"
      />
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0 1.5rem;
  height: 56px;
  background: #1a1f2e;
  border-bottom: 1px solid #2a3040;
  flex-shrink: 0;
  z-index: 100;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  white-space: nowrap;
  color: #4ade80;
}

.username { font-size: 0.875rem; color: #94a3b8; }

/* статус badges — они уже хардкодом, ок, но dark mode плохо читается */
.status-healthy  { background: #052e16; color: #4ade80; }
.status-degraded { background: #451a03; color: #fbbf24; }
.status-critical { background: #450a0a; color: #f87171; }
.status-unknown  { background: #1e293b; color: #64748b; }

.logo-icon { font-size: 1.25rem; }

.header-selectors {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.selector-contour { width: 160px; }
.selector-cluster  { width: 200px; }

.cluster-status-badge {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

</style>