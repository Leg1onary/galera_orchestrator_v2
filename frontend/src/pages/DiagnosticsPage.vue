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
  { value: 'processes',     label: 'Process list',    icon: 'pi-list' },
  { value: 'slow-queries',  label: 'Slow queries',    icon: 'pi-clock' },
  { value: 'galera-vars',   label: 'Galera variables', icon: 'pi-sliders-h' },
  { value: 'galera-status', label: 'Galera status',   icon: 'pi-chart-bar' },
  { value: 'innodb',        label: 'InnoDB status',   icon: 'pi-database' },
  { value: 'errorlog',      label: 'Error log',       icon: 'pi-file-edit' },
]
</script>

<template>
  <div class="diagnostics-page anim-fade-in">

    <div class="pg-head">
      <div class="pg-head-icon">
        <i class="pi pi-search" />
      </div>
      <div class="pg-head-text">
        <h1 class="pg-title">Diagnostics</h1>
        <p class="pg-desc">Live database and system diagnostics for all cluster nodes.</p>
      </div>
    </div>

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <div class="pg-empty-icon"><i class="pi pi-server" /></div>
      <span class="pg-empty-label">No cluster selected</span>
    </div>

    <Tabs v-else v-model:value="activeTab" lazy class="diag-tabs">
      <TabList class="diag-tablist">
        <Tab v-for="t in TABS" :key="t.value" :value="t.value" class="diag-tab">
          <i :class="['pi', t.icon]" class="tab-icon" />
          <span>{{ t.label }}</span>
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

/* ── PAGE HEADER ── */
.pg-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.pg-head-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-dim);
  border: 1px solid rgba(45, 212, 191, 0.18);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-size: 0.875rem;
}

.pg-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.pg-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
  letter-spacing: 0.01em;
}

/* ── EMPTY ── */
.pg-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-12) var(--space-8);
}

.pg-empty-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  color: var(--color-text-faint);
  font-size: 1.1rem;
}

.pg-empty-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* ── TABS ── */
.diag-tabs {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.diag-tablist {
  gap: var(--space-1);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0;
}

.diag-tab {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  color: var(--color-text-muted);
  border: 1px solid transparent;
  border-bottom: none;
  transition: color var(--transition-normal), background var(--transition-normal);
  margin-bottom: -1px;
}

.diag-tab:hover {
  color: var(--color-text);
  background: var(--color-surface-3);
}

:deep(.p-tab[data-p-active='true'].diag-tab) {
  color: var(--color-primary);
  background: var(--color-surface);
  border-color: var(--color-border);
  border-bottom-color: var(--color-surface);
}

.tab-icon {
  font-size: 0.75rem;
  opacity: 0.8;
}

:deep(.diag-panels) {
  padding: var(--space-5) 0 0;
  background: transparent;
}
</style>
