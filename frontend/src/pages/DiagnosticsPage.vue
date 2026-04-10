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
  { value: 'processes',     label: 'Process list',     icon: 'pi-list' },
  { value: 'slow-queries',  label: 'Slow queries',     icon: 'pi-clock' },
  { value: 'galera-vars',   label: 'Galera variables',  icon: 'pi-sliders-h' },
  { value: 'galera-status', label: 'Galera status',    icon: 'pi-chart-bar' },
  { value: 'innodb',        label: 'InnoDB status',    icon: 'pi-database' },
  { value: 'errorlog',      label: 'Error log',        icon: 'pi-file-edit' },
]
</script>

<template>
  <div class="diagnostics-page anim-fade-in">

    <div class="pg-head">
      <div class="pg-head-inner">
        <div class="pg-head-icon"><i class="pi pi-search" /></div>
        <div>
          <h1 class="pg-title">Diagnostics</h1>
          <p class="pg-desc">Live database and system diagnostics for all cluster nodes.</p>
        </div>
      </div>
    </div>

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <div class="pg-empty-icon"><i class="pi pi-server" /></div>
      <p>No cluster selected</p>
    </div>

    <Tabs v-else v-model:value="activeTab" lazy>
      <TabList class="diag-tablist">
        <Tab v-for="t in TABS" :key="t.value" :value="t.value" class="diag-tab">
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

/* PAGE HEADER */
.pg-head {
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}
.pg-head-inner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.pg-head-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in oklch, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  font-size: 1rem;
  flex-shrink: 0;
}
.pg-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}
.pg-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* EMPTY */
.pg-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-16);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
.pg-empty-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-offset);
  color: var(--color-text-faint);
  font-size: 1.2rem;
}

/* TABS */
.diag-tablist {
  border-bottom: 1px solid var(--color-border);
  gap: var(--space-1);
}
.diag-tab { gap: var(--space-2); }
.tab-icon { font-size: 0.78rem; }

:deep(.diag-panels) { padding: var(--space-5) 0 0; }
</style>
