<template>
  <DataTable
      :value="nodes"
      :loading="loading"
      dataKey="id"
      sortField="name"
      :sortOrder="1"
      scrollable
      scrollHeight="flex"
      class="node-table"
      @row-click="(e) => emit('select', e.data)"
  >
    <!-- Status -->
    <Column field="wsrep_local_state_comment" header="Status" :sortable="true" style="width: 160px">
      <template #body="{ data }">
        <NodeStatusBadge :node="data" />
      </template>
    </Column>

    <!-- Name -->
    <Column field="name" header="Node" :sortable="true" style="min-width: 160px">
      <template #body="{ data }">
        <div class="flex flex-col gap-0.5">
          <span class="font-medium text-sm">{{ data.name }}</span>
          <span class="text-xs text-muted-color font-mono">{{ data.host }}:{{ data.port }}</span>
        </div>
      </template>
    </Column>

    <!-- Datacenter -->
    <Column field="datacenter_name" header="DC" :sortable="true" style="width: 100px">
      <template #body="{ data }">
        <span class="text-sm text-muted-color">{{ data.datacenter_name ?? '—' }}</span>
      </template>
    </Column>

    <!-- Read-only -->
    <Column field="read_only" header="R/O" style="width: 70px">
      <template #body="{ data }">
        <Tag
            v-if="data.read_only !== null"
            :value="data.read_only ? 'RO' : 'RW'"
            :severity="data.read_only ? 'warn' : 'success'"
            class="text-xs"
        />
        <span v-else class="text-muted-color text-xs">—</span>
      </template>
    </Column>

    <!-- Maintenance -->
    <Column field="maintenance" header="Maint" style="width: 80px">
      <template #body="{ data }">
        <Tag
            v-if="data.maintenance"
            value="MAINT"
            severity="warn"
            class="text-xs"
        />
        <!-- Drift: maintenance=true в БД но read_only=false в MariaDB -->
        <Tag
            v-else-if="data.maintenance_drift"
            value="DRIFT"
            severity="danger"
            class="text-xs"
            v-tooltip.top="'maintenance flag set but node is read-write'"
        />
        <span v-else class="text-muted-color text-xs">—</span>
      </template>
    </Column>

    <!-- Flow Control -->
    <Column field="wsrep_flow_control_paused" header="FC" style="width: 80px">
      <template #body="{ data }">
        <span
            class="text-sm font-mono"
            :class="fcClass(data.wsrep_flow_control_paused)"
        >
          {{ data.wsrep_flow_control_paused !== null
            ? (data.wsrep_flow_control_paused * 100).toFixed(1) + '%'
            : '—' }}
        </span>
      </template>
    </Column>

    <!-- Recv Queue -->
    <Column field="wsrep_local_recv_queue_avg" header="RecvQ" style="width: 90px">
      <template #body="{ data }">
        <span
            class="text-sm font-mono"
            :class="recvClass(data.wsrep_local_recv_queue_avg)"
        >
          {{ data.wsrep_local_recv_queue_avg !== null
            ? data.wsrep_local_recv_queue_avg.toFixed(2)
            : '—' }}
        </span>
      </template>
    </Column>

    <!-- Last seen -->
    <Column field="last_seen" header="Last seen" style="width: 120px">
      <template #body="{ data }">
        <span class="text-xs text-muted-color">
          {{ data.last_seen ? formatRelative(data.last_seen) : '—' }}
        </span>
      </template>
    </Column>

    <!-- Actions -->
    <Column header="" style="width: 56px" :frozen="true" alignFrozen="right">
      <template #body="{ data }">
        <NodeActionMenu :node="data" :cluster-id="clusterId" @action-done="emit('refresh')" />
      </template>
    </Column>

    <template #empty>
      <div class="py-12 text-center text-muted-color text-sm">No nodes configured for this cluster.</div>
    </template>

    <template #loading>
      <div class="py-12 text-center text-muted-color text-sm">Loading nodes…</div>
    </template>
  </DataTable>
</template>

<script setup lang="ts">
import { DataTable, Column, Tag } from 'primevue'
import NodeStatusBadge from './NodeStatusBadge.vue'
import NodeActionMenu from './NodeActionMenu.vue'
import type { NodeListItem } from '@/api/nodes'
import { formatRelative } from '@/utils/time'

const props = defineProps<{
  nodes: NodeListItem[]
  loading: boolean
  clusterId: number
}>()

const emit = defineEmits<{
  select: [node: NodeListItem]
  refresh: []
}>()

function fcClass(val: number | null) {
  if (val === null) return ''
  if (val > 0.1) return 'text-red-500'
  if (val > 0.01) return 'text-yellow-500'
  return 'text-green-500'
}

function recvClass(val: number | null) {
  if (val === null) return ''
  if (val > 10) return 'text-red-500'
  if (val > 2) return 'text-yellow-500'
  return ''
}
</script>