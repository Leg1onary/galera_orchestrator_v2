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

const statusLabel = computed(() => props.clusterStatus?.status ?? null)
const statusClass = computed(() => {
  const s = props.clusterStatus?.status
  if (s === 'healthy')  return 'status-pill--healthy'
  if (s === 'degraded') return 'status-pill--degraded-cluster'
  if (s === 'critical') return 'status-pill--critical'
  return ''
})
</script>

<template>
  <header class="app-header">
    <!-- Лого -->
    <div class="header-logo">
      <svg class="logo-mark" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <polygon points="14,2 26,8.5 26,19.5 14,26 2,19.5 2,8.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
        <polygon points="14,7 21,11 21,17 14,21 7,17 7,11" fill="currentColor" fill-opacity="0.18" stroke="currentColor" stroke-width="1" stroke-linejoin="round"/>
        <circle cx="14" cy="14" r="2.5" fill="currentColor"/>
      </svg>
      <span class="logo-text">Galera Orchestrator</span>
    </div>

    <!-- Центр: контур + кластер + статус -->
    <div class="header-center">
      <div class="selectors-group">
        <Select
            :options="contours"
            :model-value="selectedContourId"
            option-label="name"
            option-value="id"
            placeholder="Контур"
            class="selector selector--contour"
            @change="(e: SelectChangeEvent) => emit('select-contour', e.value)"
        />
        <span class="selector-sep">·</span>
        <Select
            :options="clusters"
            :model-value="selectedClusterId"
            option-label="name"
            option-value="id"
            placeholder="Кластер"
            class="selector selector--cluster"
            @change="(e: SelectChangeEvent) => emit('select-cluster', e.value)"
        />
      </div>

      <span v-if="statusLabel" :class="['status-pill', statusClass]">
        <span class="status-dot" />
        {{ statusLabel }}
      </span>
    </div>

    <!-- Пользователь и logout -->
    <div class="header-user">
      <span class="username">
        <i class="pi pi-user" style="font-size: 0.7rem; opacity: 0.5" />
        {{ username }}
      </span>
      <button class="logout-btn" @click="emit('logout')" title="Выйти">
        <i class="pi pi-sign-out" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: 0 var(--space-5);
  height: var(--header-height);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  position: relative;
  z-index: 40;
}

/* Subtle top glow line */
.app-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(45,212,191,0.4) 30%,
    rgba(45,212,191,0.4) 70%,
    transparent 100%
  );
}

/* ── Logo ── */
.header-logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
  color: var(--color-primary);
}

.logo-mark {
  width: 22px;
  height: 22px;
  filter: drop-shadow(0 0 6px rgba(45,212,191,0.4));
  transition: filter var(--transition-normal);
}

.header-logo:hover .logo-mark {
  filter: drop-shadow(0 0 10px rgba(45,212,191,0.7));
}

.logo-text {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: 0.01em;
  white-space: nowrap;
}

/* ── Center ── */
.header-center {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
}

.selectors-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.selector-sep {
  color: var(--color-text-faint);
  font-size: var(--text-base);
  line-height: 1;
}

/* override PrimeVue Select size */
:deep(.selector .p-select) {
  border-radius: var(--radius-md) !important;
  font-size: var(--text-sm) !important;
}

.selector--contour { width: 140px; }
.selector--cluster { width: 180px; }

/* ── Status pill ── */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: var(--radius-xl);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  border: 1px solid transparent;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-dot 2s ease-in-out infinite;
}

.status-pill--healthy {
  background: rgba(34,197,94,0.1);
  color: #22c55e;
  border-color: rgba(34,197,94,0.25);
}

.status-pill--degraded-cluster {
  background: rgba(249,115,22,0.1);
  color: #f97316;
  border-color: rgba(249,115,22,0.25);
}

.status-pill--critical {
  background: rgba(239,68,68,0.1);
  color: #ef4444;
  border-color: rgba(239,68,68,0.25);
}

/* ── User ── */
.header-user {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
  flex-shrink: 0;
}

.username {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  transition: all var(--transition-normal);
  border: 1px solid transparent;
}

.logout-btn:hover {
  color: var(--color-error);
  background: rgba(239,68,68,0.1);
  border-color: rgba(239,68,68,0.25);
}

.logout-btn i { font-size: 0.875rem; }
</style>
