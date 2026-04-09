<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">Diagnostics</h1>
      <p class="page-subtitle">
        Live database and system diagnostics for all cluster nodes.
      </p>
    </div>

    <div v-if="!clusterStore.selectedClusterId" class="empty-state">
      <i class="pi pi-server empty-state-icon" />
      <p>No cluster selected.</p>
    </div>

    <Tabs v-else v-model:value="activeTab" lazy>
      <TabList>
        <Tab value="processes">
          <i class="pi pi-list mr-2" />Process list
        </Tab>
        <Tab value="slow-queries">
          <i class="pi pi-clock mr-2" />Slow queries
        </Tab>
        <Tab value="galera-vars">
          <i class="pi pi-sliders-h mr-2" />Galera variables
        </Tab>
        <Tab value="galera-status">
          <i class="pi pi-chart-bar mr-2" />Galera status
        </Tab>
        <Tab value="innodb">
          <i class="pi pi-database mr-2" />InnoDB status
        </Tab>
        <Tab value="errorlog">
          <i class="pi pi-file-edit mr-2" />Error log
        </Tab>
      </TabList>

      <TabPanels>
        <TabPanel value="processes">
          <ProcessListPanel :active="activeTab === 'processes'" />
        </TabPanel>
        <TabPanel value="slow-queries">
          <SlowQueryPanel :active="activeTab === 'slow-queries'" />
        </TabPanel>
        <TabPanel value="galera-vars">
          <GaleraVarsPanel :active="activeTab === 'galera-vars'" />
        </TabPanel>
        <TabPanel value="galera-status">
          <GaleraStatusPanel :active="activeTab === 'galera-status'" />
        </TabPanel>
        <TabPanel value="innodb">
          <InnodbStatusPanel :active="activeTab === 'innodb'" />
        </TabPanel>
        <TabPanel value="errorlog">
          <ErrorLogPanel :active="activeTab === 'errorlog'" />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Tabs, TabList, Tab, TabPanels, TabPanel } from 'primevue'
import { useClusterStore } from '@/stores/cluster'
import ProcessListPanel   from '@/components/diagnostics/ProcessListPanel.vue'
import SlowQueryPanel     from '@/components/diagnostics/SlowQueryPanel.vue'
import GaleraVarsPanel    from '@/components/diagnostics/GaleraVarsPanel.vue'
import GaleraStatusPanel  from '@/components/diagnostics/GaleraStatusPanel.vue'
import InnodbStatusPanel  from '@/components/diagnostics/InnodbStatusPanel.vue'
import ErrorLogPanel      from '@/components/diagnostics/ErrorLogPanel.vue'

const clusterStore = useClusterStore()
// Дефолтная вкладка — processes, самая частоиспользуемая
const activeTab = ref('processes')
</script>

<style scoped>
/* Убираем лишний padding TabPanel — панели сами управляют своим отступом */
:deep(.p-tabpanels) { padding: var(--space-4) 0 0; }
</style>