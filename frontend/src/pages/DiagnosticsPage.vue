<script setup lang="ts">
import { ref, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import ProcessListPanel  from '@/components/diagnostics/ProcessListPanel.vue'
import SlowQueryPanel    from '@/components/diagnostics/SlowQueryPanel.vue'
import GaleraVarsPanel   from '@/components/diagnostics/GaleraVarsPanel.vue'
import GaleraStatusPanel from '@/components/diagnostics/GaleraStatusPanel.vue'
import InnodbStatusPanel from '@/components/diagnostics/InnodbStatusPanel.vue'
import ErrorLogPanel     from '@/components/diagnostics/ErrorLogPanel.vue'

const clusterStore = useClusterStore()
const activeTab    = ref('processes')

watch(
  () => clusterStore.selectedClusterId,
  (id, prev) => { if (id && prev && id !== prev) activeTab.value = 'processes' }
)

const TABS = [
  { value: 'processes',    label: 'Process list',    icon: 'pi-list' },
  { value: 'slow-queries', label: 'Slow queries',    icon: 'pi-clock' },
  { value: 'galera-vars',  label: 'Galera variables', icon: 'pi-sliders-h' },
  { value: 'galera-status',label: 'Galera status',   icon: 'pi-chart-bar' },
  { value: 'innodb',       label: 'InnoDB status',   icon: 'pi-database' },
  { value: 'errorlog',     label: 'Error log',       icon: 'pi-file-edit' },
]
</script>

<template>
  <div class="diagnostics-page anim-fade-in">

    <div class="pg-head">
      <div class="section-title">Diagnostics</div>
      <p class="pg-desc">Live database and system diagnostics for all cluster nodes.</p>
    </div>

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <Tabs v-else v-model:value="activeTab" lazy>
      <TabList class="diag-tablist">
        <Tab
          v-for="t in TABS"
          :key="t.value"
          :value="t.value"
        >
          <i :class="'pi ' + t.icon" class="tab-icon" />
          {{ t.label }}
        </Tab>
      </TabList>

      <TabPanels class="diag-panels">
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

<style scoped>
.diagnostics-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.pg-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.pg-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.pg-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-12);
  justify-content: center;
  font-size: var(--text-sm);
}

.diag-tablist { border-bottom: 1px solid var(--color-border-muted); }
.tab-icon { font-size: 0.75rem; margin-right: var(--space-2); }

:deep(.diag-panels) { padding: var(--space-5) 0 0; }
</style>
