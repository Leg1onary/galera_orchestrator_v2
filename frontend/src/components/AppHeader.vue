<!-- ТЗ 6.2: лого, выбор контура, выбор кластера, статус кластера, logout -->
<script setup lang="ts">
import { computed } from 'vue'
import type { Contour, Cluster } from '@/stores/cluster'
import type { SelectChangeEvent } from 'primevue/select'

const props = defineProps<{
  username: string | null
  contours: Contour[]
  clusters: Cluster[]
  selectedContourId: number | null
  selectedClusterId: number | null
  clusterStatus?: { status: 'healthy' | 'degraded' | 'critical' } | null
}>()

const emit = defineEmits<{
  (e: 'select-contour', id: number): void
  (e: 'select-cluster', id: number): void
  (e: 'logout'): void
}>()

const statusClass = computed(() => {
  const s = props.clusterStatus?.status
  if (s === 'healthy')  return 'status-healthy'
  if (s === 'degraded') return 'status-degraded'
  if (s === 'critical') return 'status-critical'
  return 'status-unknown'
})
</script>

<template>
  <header class="app-header">
    <!-- Лого -->
    <div class="header-logo">
      <span class="logo-icon">⭡</span>
      <span class="logo-text">Galera Orchestrator</span>
    </div>

    <!-- Селекторы -->
    <div class="header-selectors">
      <!-- Выбор контура -->
      <Select
          :options="contours"
          :model-value="selectedContourId"
          option-label="name"
          option-value="id"
          placeholder="Контур"
          class="selector-contour"
          @change="(e: SelectChangeEvent) => emit('select-contour', e.value)"
      />

      <!-- Выбор кластера -->
      <Select
          :options="clusters"
          :model-value="selectedClusterId"
          option-label="name"
          option-value="id"
          placeholder="Кластер"
          class="selector-cluster"
          @change="(e: SelectChangeEvent) => emit('select-cluster', e.value)"
      />

      <!-- Статус индикатор (ТЗ 6.2) -->
      <span v-if="props.clusterStatus" :class="['cluster-status-badge', statusClass]">
        {{ props.clusterStatus.status }}
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
  background: var(--p-navigation-background, var(--p-surface-section));
  border-bottom: 1px solid var(--p-content-border-color);
  flex-shrink: 0;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-primary-color);
  font-weight: 600;
  white-space: nowrap;
}

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

/* Бэджи статуса через семантические цвета */
.status-healthy  { background: var(--p-green-950);  color: var(--p-green-400); }
.status-degraded { background: var(--p-yellow-950); color: var(--p-yellow-400); }
.status-critical { background: var(--p-red-950);    color: var(--p-red-400); }
.status-unknown  { background: var(--p-surface-section); color: var(--p-text-muted-color); }

.header-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.username {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}
</style>
