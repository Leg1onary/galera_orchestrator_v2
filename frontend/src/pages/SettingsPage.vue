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
    <div class="section-title">Settings</div>

    <Tabs v-model:value="activeTab" orientation="vertical" lazy class="settings-tabs">
      <TabList class="settings-tablist">
        <Tab
          v-for="t in TABS"
          :key="t.value"
          :value="t.value"
          class="settings-tab"
        >
          <i :class="'pi ' + t.icon" class="tab-icon" />
          {{ t.label }}
        </Tab>
      </TabList>

      <TabPanels class="settings-panels">
        <TabPanel value="clusters">
          <ClustersTab />
        </TabPanel>
        <TabPanel value="nodes">
          <NodesTab />
        </TabPanel>
        <TabPanel value="arbitrators">
          <ArbitratorsTab />
        </TabPanel>
        <TabPanel value="datacenters">
          <DatacentersTab />
        </TabPanel>
        <TabPanel value="system">
          <SystemTab />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  height: 100%;
}

.settings-tabs {
  display: flex;
  flex: 1;
  min-height: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.settings-tablist {
  width: 176px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border-muted);
  padding: var(--space-2) 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--color-surface-2);
}

.settings-tab {
  justify-content: flex-start;
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  font-weight: 450;
  gap: var(--space-3);
  border-radius: 0;
}

.tab-icon { font-size: 0.8rem; }

.settings-panels {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

:deep(.tab-content)  { display: flex; flex-direction: column; gap: var(--space-4); }
:deep(.tab-toolbar)  { display: flex; justify-content: flex-end; }
:deep(.empty-row)    { padding: var(--space-8); text-align: center; color: var(--color-text-muted); font-size: var(--text-sm); }
</style>
