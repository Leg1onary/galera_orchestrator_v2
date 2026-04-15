<script setup lang="ts">
import { ref, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import ConnectionCheckPanel     from '@/components/diagnostics/ConnectionCheckPanel.vue'
import ConfigDiffPanel          from '@/components/diagnostics/ConfigDiffPanel.vue'
import VariablesPanel           from '@/components/diagnostics/VariablesPanel.vue'
import SystemResourcesPanel     from '@/components/diagnostics/SystemResourcesPanel.vue'
import InnodbStatusPanel        from '@/components/diagnostics/InnodbStatusPanel.vue'
import ArbitratorLogPanel       from '@/components/diagnostics/ArbitratorLogPanel.vue'
import ProcessListPanel         from '@/components/diagnostics/ProcessListPanel.vue'
import ActiveTransactionsPanel  from '@/components/diagnostics/ActiveTransactionsPanel.vue'
import SlowQueryPanel           from '@/components/diagnostics/SlowQueryPanel.vue'
import ErrorLogPanel            from '@/components/diagnostics/ErrorLogPanel.vue'
import PurgeBinaryLogsPanel     from '@/components/diagnostics/PurgeBinaryLogsPanel.vue'
import SstStatusPanel           from '@/components/diagnostics/SstStatusPanel.vue'
import FlushPanel               from '@/components/diagnostics/FlushPanel.vue'
import ConfigHealthPanel        from '@/components/diagnostics/ConfigHealthPanel.vue'
import AdvisorPanel             from '@/components/diagnostics/AdvisorPanel.vue'

const clusterStore = useClusterStore()
const activeTab    = ref('advisor')

watch(
  () => clusterStore.selectedClusterId,
  (id, prev) => { if (id && prev && id !== prev) activeTab.value = 'advisor' }
)

const TABS = [
  { value: 'advisor',      label: 'Advisor',                icon: 'pi-lightbulb' },
  { value: 'connections',  label: 'Connection Check',       icon: 'pi-wifi' },
  { value: 'config-diff',  label: 'Config Diff',            icon: 'pi-code' },
  { value: 'variables',    label: 'Variables',              icon: 'pi-sliders-h' },
  { value: 'resources',    label: 'System Resources',       icon: 'pi-server' },
  { value: 'innodb',       label: 'InnoDB Status',          icon: 'pi-database' },
  { value: 'arb-log',      label: 'Arbitrator Log',         icon: 'pi-file-edit' },
  { value: 'process-list', label: 'Process List',           icon: 'pi-list' },
  { value: 'active-trx',   label: 'Active Transactions',    icon: 'pi-arrows-h' },
  { value: 'slow-query',   label: 'Slow Queries',           icon: 'pi-clock' },
  { value: 'error-log',    label: 'Error Log',              icon: 'pi-exclamation-triangle' },
  { value: 'purge-binlog', label: 'Purge Binary Logs',      icon: 'pi-trash' },
  { value: 'sst-status',   label: 'SST Status',             icon: 'pi-sync' },
  { value: 'config-health', label: 'Config Health',         icon: 'pi-shield' },
  { value: 'flush',        label: 'Flush',                  icon: 'pi-replay' },
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
        <p class="pg-desc">Connectivity, config, resources and logs for this cluster.</p>
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
        <TabPanel value="advisor">
          <AdvisorPanel :active="activeTab === 'advisor'" />
        </TabPanel>
        <TabPanel value="connections">
          <ConnectionCheckPanel :active="activeTab === 'connections'" />
        </TabPanel>
        <TabPanel value="config-diff">
          <ConfigDiffPanel :active="activeTab === 'config-diff'" />
        </TabPanel>
        <TabPanel value="variables">
          <VariablesPanel :active="activeTab === 'variables'" />
        </TabPanel>
        <TabPanel value="resources">
          <SystemResourcesPanel :active="activeTab === 'resources'" />
        </TabPanel>
        <TabPanel value="innodb">
          <InnodbStatusPanel :active="activeTab === 'innodb'" />
        </TabPanel>
        <TabPanel value="arb-log">
          <ArbitratorLogPanel :active="activeTab === 'arb-log'" />
        </TabPanel>
        <TabPanel value="process-list">
          <ProcessListPanel :active="activeTab === 'process-list'" />
        </TabPanel>
        <TabPanel value="active-trx">
          <ActiveTransactionsPanel :active="activeTab === 'active-trx'" />
        </TabPanel>
        <TabPanel value="slow-query">
          <SlowQueryPanel :active="activeTab === 'slow-query'" />
        </TabPanel>
        <TabPanel value="error-log">
          <ErrorLogPanel :active="activeTab === 'error-log'" />
        </TabPanel>
        <TabPanel value="purge-binlog">
          <PurgeBinaryLogsPanel />
        </TabPanel>
        <TabPanel value="sst-status">
          <SstStatusPanel :active="activeTab === 'sst-status'" />
        </TabPanel>
        <TabPanel value="config-health">
          <ConfigHealthPanel :active="activeTab === 'config-health'" />
        </TabPanel>
        <TabPanel value="flush">
          <FlushPanel />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style>
/*
  Terminal color tokens — scoped to diagnostics page root.
  Used by InnodbStatusPanel and ErrorLogPanel instead of hardcoded hex values.
  Override here to support future theme switching.
*/
.diagnostics-page {
  --color-terminal-bg:    #0a0b0e;
  --color-terminal-text:  #8b949e;
  --color-terminal-ok:    #7dcfad;
  --color-terminal-warn:  #fbbf24;
  --color-terminal-error: #f87171;
}
</style>

<style scoped>
.diagnostics-page {
  display: flex;
  flex-direction: column;
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
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-highlight);
  border: 1px solid oklch(from var(--color-primary) l c h / 0.18);
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
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  color: var(--color-text-faint);
  font-size: 1.1rem;
}

.pg-empty-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.diag-tabs {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.diag-tablist {
  gap: var(--space-1);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0;
  flex-wrap: wrap;
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
  background: var(--color-surface-offset);
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
  padding: var(--space-5) var(--space-1) 0;
  background: transparent;
}
</style>
