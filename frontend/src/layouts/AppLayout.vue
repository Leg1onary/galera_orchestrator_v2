<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppFooter from '@/components/AppFooter.vue'

const route = useRoute()
const sidebarCollapsed = ref(false)

const showLayout = computed(() =>
  route.name !== 'login' && route.name !== 'not-found'
)
</script>

<template>
  <div v-if="showLayout" class="app-shell">
    <AppSidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
    <div class="app-main" :class="{ 'app-main--collapsed': sidebarCollapsed }">
      <AppHeader />
      <main class="app-content">
        <RouterView />
      </main>
      <AppFooter />
    </div>
  </div>
  <RouterView v-else />
</template>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100dvh;
  background: var(--color-bg);
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-slow);
}

.app-main--collapsed {
  margin-left: var(--sidebar-width-collapsed);
}

.app-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  min-height: 0;
}
</style>
