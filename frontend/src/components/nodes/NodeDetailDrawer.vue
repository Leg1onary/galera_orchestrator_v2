<!-- ТЗ раздел 9.4: Drawer с 3 вкладками — Overview / Variables / InnoDB -->
<template>
  <Drawer
      v-model:visible="visible"
      :header="node?.name ?? 'Node details'"
      position="right"
      style="width: min(680px, 95vw)"
      @hide="emit('close')"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <NodeStatusBadge v-if="node" :node="node" />
        <span class="font-semibold text-base">{{ node?.name }}</span>
        <span class="text-xs text-muted-color font-mono">{{ node?.host }}:{{ node?.port }}</span>
      </div>
    </template>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="overview">Overview</Tab>
        <Tab value="variables">Variables</Tab>
        <Tab value="innodb">InnoDB</Tab>
      </TabList>

      <!-- ── Tab: Overview ─────────────────────────────────── -->
      <TabPanels>
        <TabPanel value="overview">
          <div v-if="detailsLoading" class="py-8 text-center text-muted-color text-sm">
            Loading…
          </div>
          <div v-else-if="details" class="space-y-5">
            <!-- Sparklines -->
            <div class="grid grid-cols-2 gap-4">
              <SparklineCard
                  label="Flow Control"
                  :data="details.sparkline_flow_control"
                  :color="fcColor(details.wsrep_flow_control_paused)"
                  unit="%"
                  :scale="100"
              />
              <SparklineCard
                  label="Recv Queue"
                  :data="details.sparkline_recv_queue"
                  :color="recvColor(details.wsrep_local_recv_queue_avg)"
                  unit=""
              />
            </div>

            <!-- Live stats grid -->
            <div class="stats-grid">
              <StatRow label="Cluster status"  :value="details.wsrep_cluster_status" />
              <StatRow label="Cluster size"    :value="details.wsrep_cluster_size" />
              <StatRow label="State"           :value="details.wsrep_local_state_comment" />
              <StatRow label="Connected"       :value="boolLabel(details.wsrep_connected)" />
              <StatRow label="Ready"           :value="boolLabel(details.wsrep_ready)" />
              <StatRow label="Read-only"       :value="boolLabel(details.read_only)" />
              <StatRow label="Commit window"   :value="details.wsrep_commit_window" />
              <StatRow label="Send queue avg"  :value="details.wsrep_local_send_queue_avg?.toFixed(3)" />
              <StatRow label="Version"         :value="details.version" />
              <StatRow label="Uptime"          :value="formatUptime(details.uptime_seconds)" />
            </div>

            <div v-if="details.last_error" class="error-block">
              <i class="pi pi-exclamation-triangle" />
              {{ details.last_error }}
            </div>
          </div>
        </TabPanel>

        <!-- ── Tab: Variables ────────────────────────────────── -->
        <TabPanel value="variables">
          <div class="mb-3">
            <InputText
                v-model="varFilter"
                placeholder="Filter variables…"
                size="small"
                class="w-full"
            />
          </div>
          <div v-if="varsLoading" class="py-6 text-center text-muted-color text-sm">Loading…</div>
          <div v-else class="var-list">
            <div
                v-for="v in filteredVars"
                :key="v.variable_name"
                class="var-row"
            >
              <span class="var-name">{{ v.variable_name }}</span>
              <span class="var-value">{{ v.value }}</span>
            </div>
            <div v-if="filteredVars.length === 0" class="py-6 text-center text-muted-color text-sm">
              No matching variables.
            </div>
          </div>
        </TabPanel>

        <!-- ── Tab: InnoDB ────────────────────────────────────── -->
        <TabPanel value="innodb">
          <Button
              label="Refresh"
              icon="pi pi-refresh"
              size="small"
              text
              :loading="innodbLoading"
              class="mb-3"
              @click="fetchInnodb"
          />
          <div v-if="innodbLoading" class="py-6 text-center text-muted-color text-sm">Loading…</div>
          <div v-else-if="innodbStatus">
            <div v-if="innodbStatus.deadlock_section" class="mb-4">
              <div class="text-sm font-semibold text-error mb-1 flex items-center gap-2">
                <i class="pi pi-exclamation-circle" /> Last deadlock
              </div>
              <pre class="innodb-pre">{{ innodbStatus.deadlock_section }}</pre>
            </div>
            <details>
              <summary class="text-sm text-muted-color cursor-pointer mb-2">
                Full InnoDB status
              </summary>
              <pre class="innodb-pre">{{ innodbStatus.raw }}</pre>
            </details>
          </div>
          <div v-else class="py-6 text-center text-muted-color text-sm">
            Click Refresh to load InnoDB status.
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- Footer: Test connection button -->
    <template #footer>
      <div class="flex justify-between items-center w-full">
        <Button
            label="Test connection"
            icon="pi pi-wifi"
            size="small"
            outlined
            @click="showTestModal = true"
        />
        <span class="text-xs text-muted-color">
          {{ details?.last_seen ? 'Last seen ' + formatRelative(details.last_seen) : '' }}
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
import {
  Drawer, Tabs, TabList, Tab, TabPanels, TabPanel,
  Button, InputText,
} from 'primevue'
import NodeStatusBadge from './NodeStatusBadge.vue'
import SparklineCard from './SparklineCard.vue'
import StatRow from './StatRow.vue'
import TestConnectionModal from './TestConnectionModal.vue'
import { nodesApi } from '@/api/nodes'
import type { NodeListItem, InnoDbStatus } from '@/api/nodes'
import { formatRelative, formatUptime } from '@/utils/time'

const props = defineProps<{
  node: NodeListItem | null
  clusterId: number
}>()
const emit = defineEmits<{ close: [] }>()

const visible = computed(() => props.node !== null)
const activeTab = ref('overview')
const varFilter = ref('')
const showTestModal = ref(false)
const innodbStatus = ref<InnoDbStatus | null>(null)
const innodbLoading = ref(false)

// Reset state on node change
watch(() => props.node?.id, () => {
  activeTab.value = 'overview'
  varFilter.value = ''
  innodbStatus.value = null
})

// Details query — refetch every 10s while drawer open
const { data: details, isLoading: detailsLoading } = useQuery({
  queryKey: computed(() => ['cluster', props.clusterId, 'node-details', props.node?.id]),
  queryFn: () => nodesApi.details(props.clusterId, props.node!.id),
  enabled: computed(() => props.node !== null),
  refetchInterval: 10_000,
})

// Variables query — load on tab activation, no auto-refetch
const { data: variables, isLoading: varsLoading } = useQuery({
  queryKey: computed(() => ['cluster', props.clusterId, 'node-variables', props.node?.id]),
  queryFn: () => nodesApi.variables(props.clusterId, props.node!.id),
  enabled: computed(() => props.node !== null && activeTab.value === 'variables'),
  staleTime: 30_000,
})

const filteredVars = computed(() => {
  const q = varFilter.value.toLowerCase()
  return (variables.value ?? []).filter(
      (v) => !q || v.variable_name.toLowerCase().includes(q) || v.value.toLowerCase().includes(q)
  )
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

function boolLabel(v: boolean | null) {
  if (v === null) return '—'
  return v ? 'Yes' : 'No'
}
function fcColor(v: number | null) {
  if (!v || v <= 0.01) return 'var(--color-success)'
  if (v <= 0.1) return 'var(--color-gold)'
  return 'var(--color-error)'
}
function recvColor(v: number | null) {
  if (!v || v <= 2) return 'var(--color-primary)'
  if (v <= 10) return 'var(--color-gold)'
  return 'var(--color-error)'
}
</script>

<style scoped>
.stats-grid { display: grid; gap: 0; border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow: hidden; }
.var-list { display: flex; flex-direction: column; gap: 0; font-size: var(--text-xs); max-height: 500px; overflow-y: auto; }
.var-row { display: flex; justify-content: space-between; gap: 1rem; padding: 0.3rem 0.5rem; border-bottom: 1px solid var(--color-divider); }
.var-row:last-child { border-bottom: none; }
.var-name { color: var(--color-text-muted); font-family: monospace; }
.var-value { color: var(--color-text); font-family: monospace; text-align: right; }
.innodb-pre { font-size: 11px; font-family: monospace; white-space: pre-wrap; word-break: break-all; background: var(--color-surface-offset); padding: 0.75rem; border-radius: var(--radius-sm); max-height: 400px; overflow-y: auto; }
.error-block { display: flex; gap: 0.5rem; align-items: flex-start; padding: 0.75rem; background: color-mix(in oklch, var(--color-error) 10%, transparent); border-radius: var(--radius-sm); color: var(--color-error); font-size: var(--text-sm); }
</style>