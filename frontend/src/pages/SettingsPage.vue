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
    <div class="pg-head">
      <div class="pg-head-icon"><i class="pi pi-sliders-h" /></div>
      <div>
        <h1 class="pg-title">Settings</h1>
        <p class="pg-desc">Manage clusters, nodes, arbitrators, datacenters, and system configuration.</p>
      </div>
    </div>

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
  padding: 0;
  gap: var(--space-5);
}

.pg-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.pg-head-icon {
  width: 36px; height: 36px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-highlight);
  border: 1px solid rgba(45, 212, 191, 0.18);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-size: 0.875rem;
}
.pg-title {
  font-size: var(--text-xl); font-weight: 700;
  color: var(--color-text); letter-spacing: -0.02em; line-height: 1.2;
}
.pg-desc {
  font-size: var(--text-xs); color: var(--color-text-muted); margin-top: 2px;
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
