<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClusterStore } from '@/stores/cluster'

import Tag from 'primevue/tag'

import ConnectionCheckPanel    from '@/components/diagnostics/ConnectionCheckPanel.vue'
import ConfigDiffPanel         from '@/components/diagnostics/ConfigDiffPanel.vue'
import VariablesPanel          from '@/components/diagnostics/VariablesPanel.vue'
import SystemResourcesPanel    from '@/components/diagnostics/SystemResourcesPanel.vue'
import InnodbStatusPanel       from '@/components/diagnostics/InnodbStatusPanel.vue'
import ArbitratorLogPanel      from '@/components/diagnostics/ArbitratorLogPanel.vue'
import ProcessListPanel        from '@/components/diagnostics/ProcessListPanel.vue'
import ActiveTransactionsPanel from '@/components/diagnostics/ActiveTransactionsPanel.vue'
import SlowQueryPanel          from '@/components/diagnostics/SlowQueryPanel.vue'
import ErrorLogPanel           from '@/components/diagnostics/ErrorLogPanel.vue'
import PurgeBinaryLogsPanel    from '@/components/diagnostics/PurgeBinaryLogsPanel.vue'
import SstStatusPanel          from '@/components/diagnostics/SstStatusPanel.vue'
import FlushPanel              from '@/components/diagnostics/FlushPanel.vue'
import ConfigHealthPanel       from '@/components/diagnostics/ConfigHealthPanel.vue'
import AdvisorPanel            from '@/components/diagnostics/AdvisorPanel.vue'

const clusterStore = useClusterStore()
const route  = useRoute()
const router = useRouter()

const GROUPS = [
  {
    value: 'analysis',
    label: 'Analysis',
    icon:  'pi-lightbulb',
    desc:  'AI рекомендации и проверка конфигурации',
    tabs: [
      { value: 'advisor',       label: 'Advisor',       icon: 'pi-sparkles' },
      { value: 'config-health', label: 'Config Health', icon: 'pi-shield'   },
    ],
  },
  {
    value: 'config',
    label: 'Config',
    icon:  'pi-sliders-h',
    desc:  'Соединения, переменные и diff конфигурации',
    tabs: [
      { value: 'connections', label: 'Connections', icon: 'pi-wifi'     },
      { value: 'config-diff', label: 'Config Diff', icon: 'pi-code'     },
      { value: 'variables',   label: 'Variables',   icon: 'pi-list'     },
    ],
  },
  {
    value: 'engine',
    label: 'Engine',
    icon:  'pi-server',
    desc:  'Ресурсы, InnoDB и статус SST',
    tabs: [
      { value: 'resources',  label: 'System Resources', icon: 'pi-desktop'  },
      { value: 'innodb',     label: 'InnoDB Status',    icon: 'pi-database' },
      { value: 'sst-status', label: 'SST Status',       icon: 'pi-sync'     },
    ],
  },
  {
    value: 'activity',
    label: 'Activity',
    icon:  'pi-bolt',
    desc:  'Активные процессы, транзакции и медленные запросы',
    tabs: [
      { value: 'process-list', label: 'Process List',   icon: 'pi-list'     },
      { value: 'active-trx',   label: 'Transactions',   icon: 'pi-arrows-h' },
      { value: 'slow-query',   label: 'Slow Queries',   icon: 'pi-clock'    },
    ],
  },
  {
    value: 'logs',
    label: 'Logs & Ops',
    icon:  'pi-file-edit',
    desc:  'Логи ошибок, арбитратора и операции обслуживания',
    tabs: [
      { value: 'error-log',    label: 'Error Log',      icon: 'pi-exclamation-triangle' },
      { value: 'arb-log',      label: 'Arbitrator Log', icon: 'pi-file-edit'            },
      { value: 'purge-binlog', label: 'Purge Binlogs',  icon: 'pi-trash'                },
      { value: 'flush',        label: 'Flush',          icon: 'pi-replay'               },
    ],
  },
] as const

type GroupValue = typeof GROUPS[number]['value']
type TabValue   = typeof GROUPS[number]['tabs'][number]['value']

const activeGroup = ref<GroupValue>('analysis')

const innerTab = ref<Record<GroupValue, TabValue>>({
  analysis: 'advisor',
  config:   'connections',
  engine:   'resources',
  activity: 'process-list',
  logs:     'error-log',
})

const currentGroup = computed(() => GROUPS.find(g => g.value === activeGroup.value)!)
const currentTab   = computed(() => innerTab.value[activeGroup.value])

const panelVisible = ref(true)

function selectGroup(g: GroupValue) {
  if (g === activeGroup.value) return
  panelVisible.value = false
  setTimeout(() => {
    activeGroup.value = g
    panelVisible.value = true
  }, 140)
}

function selectInner(t: TabValue) {
  innerTab.value[activeGroup.value] = t
}

function isActive(tabValue: string) {
  return currentTab.value === tabValue && panelVisible.value
}

watch(
  () => route.query.tab as string | undefined,
  (tab) => {
    if (!tab) return
    for (const g of GROUPS) {
      const found = g.tabs.find(t => t.value === tab)
      if (found) {
        activeGroup.value = g.value
        innerTab.value[g.value] = found.value as TabValue
        router.replace({ query: {} })
        break
      }
    }
  },
  { immediate: true }
)

watch(
  () => clusterStore.selectedClusterId,
  (id, prev) => {
    if (id && prev && id !== prev) {
      activeGroup.value = 'analysis'
      innerTab.value = { analysis: 'advisor', config: 'connections', engine: 'resources', activity: 'process-list', logs: 'error-log' }
    }
  }
)
</script>

<template>
  <div class="diagnostics-page anim-fade-in">

    <div class="pg-head">
      <div class="pg-head-icon"><i class="pi pi-search" /></div>
      <div>
        <h1 class="pg-title">Diagnostics</h1>
        <p class="pg-desc">Connectivity, config, resources and logs for this cluster.</p>
      </div>
    </div>

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <div class="pg-empty-icon"><i class="pi pi-server" /></div>
      <span class="pg-empty-label">No cluster selected</span>
    </div>

    <template v-else>

      <!-- Group selector -->
      <div class="group-rail" role="tablist" aria-label="Diagnostic groups">
        <button
          v-for="g in GROUPS"
          :key="g.value"
          class="grp-btn"
          :class="{ 'grp-btn--active': activeGroup === g.value }"
          role="tab"
          :aria-selected="activeGroup === g.value"
          @click="selectGroup(g.value)"
        >
          <span class="grp-icon-wrap">
            <i :class="['pi', g.icon]" />
          </span>
          <span class="grp-label">{{ g.label }}</span>
          <Tag
            :value="String(g.tabs.length)"
            severity="secondary"
            rounded
            class="grp-count"
          />
        </button>
      </div>

      <!-- Inner shell -->
      <div class="inner-shell">

        <!-- Sub-tab header -->
        <div class="subtab-header">
          <div class="subtab-breadcrumb">
            <i :class="['pi', currentGroup.icon]" class="bc-icon" />
            <span class="bc-group">{{ currentGroup.label }}</span>
            <span class="bc-sep">/</span>
            <span class="bc-desc">{{ currentGroup.desc }}</span>
          </div>

          <Tabs
            :value="currentTab"
            @update:value="selectInner($event as TabValue)"
            class="subtabs"
          >
            <TabList class="subtab-list">
              <Tab
                v-for="t in currentGroup.tabs"
                :key="t.value"
                :value="t.value"
                class="subtab-item"
              >
                <i :class="['pi', t.icon, 'si-icon']" />
                <span>{{ t.label }}</span>
              </Tab>
            </TabList>
          </Tabs>
        </div>

        <!-- Panel -->
        <Transition name="panel-fade" mode="out-in">
          <div v-if="panelVisible" :key="activeGroup" class="panel-area">

            <template v-if="activeGroup === 'analysis'">
              <AdvisorPanel      v-if="currentTab === 'advisor'"       :active="isActive('advisor')" />
              <ConfigHealthPanel v-if="currentTab === 'config-health'" :active="isActive('config-health')" />
            </template>

            <template v-else-if="activeGroup === 'config'">
              <ConnectionCheckPanel v-if="currentTab === 'connections'" :active="isActive('connections')" />
              <ConfigDiffPanel      v-if="currentTab === 'config-diff'" :active="isActive('config-diff')" />
              <VariablesPanel       v-if="currentTab === 'variables'"   :active="isActive('variables')" />
            </template>

            <template v-else-if="activeGroup === 'engine'">
              <SystemResourcesPanel v-if="currentTab === 'resources'"   :active="isActive('resources')" />
              <InnodbStatusPanel    v-if="currentTab === 'innodb'"       :active="isActive('innodb')" />
              <SstStatusPanel       v-if="currentTab === 'sst-status'"  :active="isActive('sst-status')" />
            </template>

            <template v-else-if="activeGroup === 'activity'">
              <ProcessListPanel        v-if="currentTab === 'process-list'" :active="isActive('process-list')" />
              <ActiveTransactionsPanel v-if="currentTab === 'active-trx'"   :active="isActive('active-trx')" />
              <SlowQueryPanel          v-if="currentTab === 'slow-query'"   :active="isActive('slow-query')" />
            </template>

            <template v-else-if="activeGroup === 'logs'">
              <ErrorLogPanel        v-if="currentTab === 'error-log'"    :active="isActive('error-log')" />
              <ArbitratorLogPanel   v-if="currentTab === 'arb-log'"      :active="isActive('arb-log')" />
              <PurgeBinaryLogsPanel v-if="currentTab === 'purge-binlog'" />
              <FlushPanel           v-if="currentTab === 'flush'" />
            </template>

          </div>
        </Transition>
      </div>
    </template>

  </div>
</template>

<style>
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
  /* Гарантируем что страница не выходит за пределы app-content */
  width: 100%;
  min-width: 0;
}

/* Page header */
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

/* Empty */
.pg-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: var(--space-3); padding: var(--space-12) var(--space-8);
}
.pg-empty-icon {
  width: 44px; height: 44px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-offset); border: 1px solid var(--color-border);
  color: var(--color-text-faint); font-size: 1.1rem;
}
.pg-empty-label { font-size: var(--text-sm); color: var(--color-text-muted); }

/* Group rail */
.group-rail {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.grp-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3) var(--space-2) var(--space-2);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition:
    color 160ms ease,
    background 160ms ease,
    border-color 160ms ease,
    box-shadow 160ms ease;
  user-select: none;
  white-space: nowrap;
}

.grp-btn:hover:not(.grp-btn--active) {
  color: var(--color-text);
  background: var(--color-surface-offset);
  border-color: var(--color-border-hover, var(--color-border));
}

.grp-btn--active {
  color: var(--color-primary) !important;
  background: var(--color-primary-highlight) !important;
  border-color: rgba(45, 212, 191, 0.35) !important;
  box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.08);
}

.grp-icon-wrap {
  width: 24px; height: 24px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.05);
  font-size: 0.7rem;
  transition: background 160ms ease;
}
.grp-btn--active .grp-icon-wrap {
  background: rgba(45, 212, 191, 0.15);
}

.grp-label { font-size: var(--text-sm); }

.grp-count {
  opacity: 0.65;
  font-size: var(--text-xs) !important;
  padding: 0 6px !important;
  height: 18px !important;
  line-height: 18px !important;
  min-width: 18px !important;
}
.grp-btn--active .grp-count { opacity: 1; }

/* Inner shell */
.inner-shell {
  /* Занимаем всю доступную ширину, не выходим за неё */
  width: 100%;
  min-width: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  overflow-x: clip;
  overflow-y: visible;
  box-shadow: var(--shadow-sm);
}

/* Sub-tab header */
.subtab-header {
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-3) var(--space-4) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.subtab-breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--space-1);
}

.bc-icon {
  font-size: 0.65rem;
  color: var(--color-primary);
  opacity: 0.85;
}
.bc-group {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-primary);
}
.bc-sep {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
}
.bc-desc {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  display: none;
}
@media (min-width: 860px) { .bc-desc { display: block; } }

/* Sub-tabs via PrimeVue Tabs */
.subtabs { flex: 1; min-width: 0; }

:deep(.subtabs .p-tablist) {
  background: transparent !important;
  border-bottom: none !important;
  padding: 0;
  gap: 2px;
}
:deep(.subtabs .p-tablist-active-bar) {
  bottom: -1px;
  height: 2px;
  background: var(--color-primary);
  border-radius: 2px 2px 0 0;
}

.subtab-item {
  display: inline-flex !important;
  align-items: center !important;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-muted);
  border: none !important;
  background: transparent !important;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  white-space: nowrap;
  transition: color 160ms ease, background 160ms ease;
  margin-bottom: -1px;
}
.subtab-item:hover {
  color: var(--color-text);
  background: rgba(228,228,231,0.04) !important;
}
:deep(.p-tab[data-p-active='true'].subtab-item) {
  color: var(--color-primary);
}

.si-icon {
  font-size: 0.68rem;
  opacity: 0.7;
  transition: opacity 160ms ease;
}
:deep(.p-tab[data-p-active='true'].subtab-item) .si-icon { opacity: 1; }

/* Panel area + transition */
.panel-area {
  padding: var(--space-5);
  /* Широкие таблицы скроллятся горизонтально внутри, не ломая layout */
  overflow-x: auto;
}

.panel-fade-enter-active {
  transition: opacity 160ms ease, transform 160ms ease;
}
.panel-fade-leave-active {
  transition: opacity 100ms ease, transform 100ms ease;
}
.panel-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.panel-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
