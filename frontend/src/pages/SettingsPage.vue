<template>
  <div class="settings-page">
    <div class="page-toolbar">
      <h1 class="page-title">Settings</h1>
    </div>

    <div class="settings-body">
      <Tabs v-model:value="activeTab" orientation="vertical" lazy class="settings-tabs">
        <TabList class="settings-tablist">
          <Tab value="clusters">
            <i class="pi pi-server mr-2" />Clusters
          </Tab>
          <Tab value="nodes">
            <i class="pi pi-desktop mr-2" />Nodes
          </Tab>
          <Tab value="arbitrators">
            <i class="pi pi-circle mr-2" />Arbitrators
          </Tab>
          <Tab value="datacenters">
            <i class="pi pi-map-marker mr-2" />Datacenters
          </Tab>
          <Tab value="system">
            <i class="pi pi-cog mr-2" />System
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import ClustersTab from '@/components/settings/ClustersTab.vue'
import NodesTab from '@/components/settings/NodesTab.vue'
import ArbitratorsTab from '@/components/settings/ArbitratorsTab.vue'
import DatacentersTab from '@/components/settings/DatacentersTab.vue'
import SystemTab from '@/components/settings/SystemTab.vue'

const activeTab = ref('clusters')
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.page-toolbar {
  display: flex;
  align-items: center;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.page-title { font-size: var(--text-lg); font-weight: 600; }
.settings-body { flex: 1; overflow: hidden; display: flex; }
.settings-tabs { width: 100%; height: 100%; display: flex; }
.settings-tablist { width: 180px; flex-shrink: 0; border-right: 1px solid var(--color-border); padding: var(--space-3) 0; }
.settings-panels { flex: 1; overflow-y: auto; padding: var(--space-6); }

/* Глобальные стили для tab-content внутри панелей */
:deep(.tab-content) { display: flex; flex-direction: column; gap: var(--space-4); }
:deep(.tab-toolbar) { display: flex; justify-content: flex-end; }
:deep(.empty-row) { padding: var(--space-8); text-align: center; color: var(--color-text-muted); font-size: var(--text-sm); }
</style>