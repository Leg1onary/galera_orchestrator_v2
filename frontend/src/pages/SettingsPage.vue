<script setup lang="ts">
import { ref } from 'vue'
import ClustersTab    from '@/components/settings/ClustersTab.vue'
import NodesTab       from '@/components/settings/NodesTab.vue'
import ArbitratorsTab from '@/components/settings/ArbitratorsTab.vue'
import DatacentersTab from '@/components/settings/DatacentersTab.vue'
import SystemTab      from '@/components/settings/SystemTab.vue'

const activeTab = ref('clusters')

const TABS = [
  { value: 'clusters',    label: 'Clusters',    icon: 'pi-server' },
  { value: 'nodes',       label: 'Nodes',       icon: 'pi-desktop' },
  { value: 'arbitrators', label: 'Arbitrators', icon: 'pi-circle' },
  { value: 'datacenters', label: 'Datacenters', icon: 'pi-map-marker' },
  { value: 'system',      label: 'System',      icon: 'pi-cog' },
]
</script>

<template>
  <div class="settings-page anim-fade-in">
    <!-- Page title -->
    <div class="settings-page__title">Settings</div>

    <!-- ── Horizontal tab bar ── -->
    <div class="settings-page__tabbar-wrap">
      <div class="settings-page__tabbar" role="tablist">
        <button
          v-for="t in TABS"
          :key="t.value"
          role="tab"
          :aria-selected="activeTab === t.value"
          class="settings-page__tab"
          :class="{ 'settings-page__tab--active': activeTab === t.value }"
          @click="activeTab = t.value"
        >
          <i :class="'pi ' + t.icon" class="settings-page__tab-icon" />
          <span>{{ t.label }}</span>
        </button>
      </div>
    </div>

    <!-- ── Tab content ── -->
    <div class="settings-page__body">
      <ClustersTab    v-if="activeTab === 'clusters'" />
      <NodesTab       v-else-if="activeTab === 'nodes'" />
      <ArbitratorsTab v-else-if="activeTab === 'arbitrators'" />
      <DatacentersTab v-else-if="activeTab === 'datacenters'" />
      <SystemTab      v-else-if="activeTab === 'system'" />
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-8) var(--space-8);
  gap: var(--space-6);
}

.settings-page__title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
  text-transform: none;
  letter-spacing: -0.01em;
}

/* ── Tab bar: full width, horizontal scroll if needed ── */
.settings-page__tabbar-wrap {
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.settings-page__tabbar-wrap::-webkit-scrollbar { display: none; }

.settings-page__tabbar {
  display: flex;
  gap: 0;
  min-width: max-content;
  padding-bottom: 0;
}

.settings-page__tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: color 150ms ease, border-color 150ms ease;
  margin-bottom: -1px;
}
.settings-page__tab:hover {
  color: var(--color-text);
}
/* fix #5: was hardcoded #2dd4bf */
.settings-page__tab--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.settings-page__tab-icon {
  font-size: 0.8rem;
  opacity: 0.8;
}

/* ── Content ── */
.settings-page__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
</style>
