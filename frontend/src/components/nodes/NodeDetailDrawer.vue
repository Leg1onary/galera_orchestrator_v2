<!-- src/components/nodes/NodeDetailDrawer.vue -->
<!-- ТЗ 11.4: Drawer с 3 вкладками — Overview / Logs / InnoDB -->
<template>
  <Drawer
      v-model:visible="visible"
      position="right"
      style="width: min(680px, 95vw)"
      @hide="emit('close')"
  >
    <!-- ── Custom header ─────────────────────────────────────── -->
    <template #header>
      <div class="drawer-header">
        <NodeStatusBadge v-if="node" :node="node" />
        <span class="drawer-title">{{ node?.name }}</span>
        <span class="drawer-host">{{ node?.host }}:{{ node?.port }}</span>
      </div>
    </template>

    <!-- ── Tabs ──────────────────────────────────────────────── -->
    <Tabs v-model:value="activeTab" lazy>
      <TabList>
        <Tab value="overview">Overview</Tab>
        <Tab value="logs">Logs</Tab>
        <Tab value="innodb">InnoDB</Tab>
      </TabList>

      <TabPanels>

        <!-- ── Tab: Overview ─────────────────────────────────── -->
        <TabPanel value="overview">
          <div v-if="detailsLoading" class="tab-state">
            <i class="pi pi-spin pi-spinner" /> Loading…
          </div>
          <div v-else-if="details" class="overview-body">

            <!-- Sparklines -->
            <div class="sparklines-grid">
              <SparklineCard
                  label="Flow Control"
                  :data="details.sparkline_flow_control ?? []"
                  :color="fcColor(details.wsrep_flow_control_paused)"
                  unit="%"
                  :scale="100"
              />
              <SparklineCard
                  label="Recv Queue"
                  :data="details.sparkline_recv_queue ?? []"
                  :color="recvColor(details.wsrep_local_recv_queue_avg)"
                  unit=""
              />
            </div>

            <!-- Live stats -->
            <div class="stats-grid">
              <StatRow label="Cluster status"  :value="details.wsrep_cluster_status" />
              <StatRow label="Cluster size"    :value="details.wsrep_cluster_size" />
              <StatRow label="State"           :value="details.wsrep_local_state_comment" />
              <StatRow label="Connected"       :value="boolLabel(details.wsrep_connected)" />
              <StatRow label="Ready"           :value="boolLabel(details.wsrep_ready)" />
              <StatRow label="Read-only"       :value="boolLabel(details.read_only)" />
              <StatRow label="Flow control"    :value="details.wsrep_flow_control_paused != null
                                                 ? (details.wsrep_flow_control_paused * 100).toFixed(2) + '%'
                                                 : '—'" />
              <StatRow label="Send queue"      :value="details.wsrep_local_send_queue_avg" />
              <StatRow label="Recv queue"      :value="details.wsrep_local_recv_queue_avg" />
              <StatRow label="Last check"      :value="details.last_check_ts
                                                 ? formatRelative(details.last_check_ts)
                                                 : '—'" />
            </div>

            <!-- Node config info -->
            <div class="stats-grid mt-section">
              <StatRow label="Host"        :value="`${details.host}:${details.port}`" />
              <StatRow label="SSH port"    :value="details.ssh_port" />
              <StatRow label="SSH user"    :value="details.ssh_user" />
              <StatRow label="DB user"     :value="details.db_user ?? '—'" />
              <StatRow label="Datacenter"  :value="details.datacenter_name ?? '—'" />
              <StatRow label="Enabled"     :value="boolLabel(details.enabled)" />
            </div>

            <!-- Last error block -->
            <div v-if="details.last_error" class="error-block">
              <i class="pi pi-exclamation-triangle" />
              {{ details.last_error }}
            </div>
          </div>
          <div v-else class="tab-state">No data available.</div>
        </TabPanel>

        <!-- ── Tab: Logs ─────────────────────────────────────── -->
        <TabPanel value="logs">
          <div v-if="logsLoading" class="tab-state">
            <i class="pi pi-spin pi-spinner" /> Loading…
          </div>
          <div v-else-if="!nodeLogs?.length" class="tab-state">
            No log entries for this node.
          </div>
          <ul v-else class="log-list">
            <li
                v-for="e in nodeLogs"
                :key="e.ts + e.source"
                :class="['log-entry', e.level.toLowerCase()]"
            >
              <span class="log-ts">{{ formatRelative(e.ts) }}</span>
              <span class="log-level">{{ e.level }}</span>
              <span class="log-source">{{ e.source }}</span>
              <span class="log-msg">{{ e.message }}</span>
            </li>
          </ul>
        </TabPanel>

        <!-- ── Tab: InnoDB ────────────────────────────────────── -->
        <TabPanel value="innodb">
          <div class="innodb-toolbar">
            <Button
                label="Refresh"
                icon="pi pi-refresh"
                size="small"
                text
                :loading="innodbLoading"
                @click="fetchInnodb"
            />
          </div>

          <div v-if="innodbLoading" class="tab-state">
            <i class="pi pi-spin pi-spinner" /> Loading…
          </div>
          <div v-else-if="innodbStatus">
            <div v-if="innodbStatus.deadlock_section" class="innodb-deadlock">
              <div class="innodb-deadlock-title">
                <i class="pi pi-exclamation-circle" /> Last deadlock
              </div>
              <pre class="innodb-pre">{{ innodbStatus.deadlock_section }}</pre>
            </div>
            <details>
              <summary class="innodb-summary">Full InnoDB status</summary>
              <pre class="innodb-pre">{{ innodbStatus.raw }}</pre>
            </details>
          </div>
          <div v-else class="tab-state">
            Click Refresh to load InnoDB status.
          </div>
        </TabPanel>

      </TabPanels>
    </Tabs>

    <!-- ── Footer ────────────────────────────────────────────── -->
    <template #footer>
      <div class="drawer-footer">
        <Button
            label="Test connection"
            icon="pi pi-wifi"
            size="small"
            outlined
            @click="showTestModal = true"
        />
        <span class="footer-ts">
          {{ details?.last_check_ts
            ? 'Last seen ' + formatRelative(details.last_check_ts)
            : '' }}
        </span>
      </div>
    </template>
  </Drawer>

  <TestConnectionModal
      v-if="showTestModal && node"
      :node-id="node.id"
      :cluster-id="clusterId"
      :node-name="node.name"
      @close="showTestModal = false"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import Drawer from 'primevue/drawer'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Button from 'primevue/button'
import NodeStatusBadge from './NodeStatusBadge.vue'
import SparklineCard from './SparklineCard.vue'
import StatRow from './StatRow.vue'
import TestConnectionModal from './TestConnectionModal.vue'
// fix: getNodeLogs — named export из объекта nodesApi, не standalone функция
import { nodesApi } from '@/api/nodes'
import type { NodeListItem, InnoDbStatus, NodeDetails, NodeLogEntry } from '@/api/nodes'
import { formatRelative } from '@/utils/time'

const props = defineProps<{
  node: NodeListItem | null
  clusterId: number
}>()
const emit = defineEmits<{ close: [] }>()

const visible = computed({
  get: () => props.node !== null,
  set: (val) => { if (!val) emit('close') },
})

const activeTab = ref('overview')
const showTestModal = ref(false)
const innodbStatus = ref<InnoDbStatus | null>(null)
const innodbLoading = ref(false)

watch(
    () => props.node?.id,
    () => {
      activeTab.value = 'overview'
      showTestModal.value = false
      innodbStatus.value = null
    },
)

const { data: details, isLoading: detailsLoading } = useQuery<NodeDetails>({
  queryKey: computed(() => ['cluster', props.clusterId, 'node-details', props.node?.id]),
  queryFn: () => nodesApi.details(props.clusterId, props.node!.id),
  enabled: computed(() => props.node !== null),
  refetchInterval: 10_000,
})

// fix: nodesApi.getNodeLogs вместо standalone getNodeLogs
const { data: nodeLogs, isLoading: logsLoading } = useQuery<NodeLogEntry[]>({
  queryKey: computed(() => ['cluster', props.clusterId, 'node-logs', props.node?.id]),
  queryFn: () => nodesApi.getNodeLogs(props.clusterId, props.node!.id, 50),
  enabled: computed(() => props.node !== null && activeTab.value === 'logs'),
  staleTime: 10_000,
})

async function fetchInnodb() {
  if (!props.node) return
  innodbLoading.value = true
  try {
    innodbStatus.value = await nodesApi.innodbStatus(props.clusterId, props.node.id)
  } finally {
    innodbLoading.value = false
  }
}

function boolLabel(v: boolean | string | null | undefined): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'string') return v
  return v ? 'Yes' : 'No'
}

function fcColor(v: number | null): string {
  if (!v || v <= 0.01) return 'var(--color-success)'
  if (v <= 0.1)        return 'var(--color-gold)'
  return 'var(--color-notification)'
}

function recvColor(v: number | null): string {
  if (!v || v <= 2) return 'var(--color-primary)'
  if (v <= 10)      return 'var(--color-gold)'
  return 'var(--color-notification)'
}
</script>

<style scoped>
.drawer-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}
.drawer-title {
  font-weight: 600;
  font-size: var(--text-base);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.drawer-host {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-family: monospace;
  white-space: nowrap;
}
.overview-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.sparklines-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}
.mt-section { margin-top: var(--space-2); }
.stats-grid {
  display: grid;
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.log-list {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: var(--text-xs);
  max-height: 480px;
  overflow-y: auto;
}
.log-entry {
  display: grid;
  grid-template-columns: 90px 48px 100px 1fr;
  align-items: baseline;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  font-variant-numeric: tabular-nums;
}
.log-entry.warn  { background: var(--color-warning-highlight); }
.log-entry.error { background: var(--color-error-highlight); }
.log-ts, .log-source { color: var(--color-text-muted); }
.log-msg { color: var(--color-text); }
.log-level { font-weight: 600; }
.log-entry.info  .log-level { color: var(--color-blue); }
.log-entry.warn  .log-level { color: var(--color-gold); }
.log-entry.error .log-level { color: var(--color-notification); }
.innodb-toolbar { margin-bottom: var(--space-3); }
.innodb-deadlock { margin-bottom: var(--space-4); }
.innodb-deadlock-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-notification);
  margin-bottom: var(--space-2);
}
.innodb-summary {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  margin-bottom: var(--space-2);
}
.innodb-pre {
  font-size: var(--text-xs);
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
  background: var(--color-surface-offset);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  max-height: 400px;
  overflow-y: auto;
}
.error-block {
  display: flex;
  gap: var(--space-2);
  align-items: flex-start;
  padding: var(--space-3);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  border-radius: var(--radius-sm);
  color: var(--color-error);
  font-size: var(--text-sm);
}
.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.footer-ts {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.tab-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-8);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>
