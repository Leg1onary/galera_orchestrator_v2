<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const route    = useRoute()
const router   = useRouter()
const clusterStore = useClusterStore()
const authStore    = useAuthStore()

// Human-readable page name from route meta or name
const pageName = computed(() => {
  if (route.meta?.title) return route.meta.title as string
  const name = String(route.name ?? '')
  return name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
})

async function logout() {
  await authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="app-header">
    <!-- Left: breadcrumb -->
    <div class="header-left">
      <span class="header-cluster" v-if="clusterStore.currentCluster">
        <i class="pi pi-database" style="font-size: 0.7rem; opacity: 0.5" />
        {{ clusterStore.currentCluster.name }}
      </span>
      <span v-if="clusterStore.currentCluster" class="header-sep">/</span>
      <span class="header-page">{{ pageName }}</span>
    </div>

    <!-- Right: actions -->
    <div class="header-right">
      <button
        class="header-btn"
        v-tooltip.bottom="'Logout'"
        @click="logout"
        aria-label="Logout"
      >
        <i class="pi pi-sign-out" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  border-bottom: 1px solid var(--color-border-muted);
  background: var(--color-bg);
  position: sticky;
  top: 0;
  z-index: 40;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  min-width: 0;
}

.header-cluster {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
  font-weight: 500;
  white-space: nowrap;
}

.header-sep {
  color: var(--color-text-faint);
  user-select: none;
}

.header-page {
  color: var(--color-text);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.header-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  transition: all var(--transition-normal);
  cursor: pointer;
  background: none;
  border: none;
}

.header-btn:hover {
  color: var(--color-text);
  background: var(--color-surface-3);
}

.header-btn:active {
  background: var(--color-surface-4);
}
</style>
