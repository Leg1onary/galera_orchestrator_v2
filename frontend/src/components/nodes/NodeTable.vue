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
    <Column field="name" header="Status" style="width: 160px">
      <template #body="{ data }">
        <NodeStatusBadge :node="data" />
      </template>
    </Column>

    <!-- Name -->
    <Column field="name" header="Node" :sortable="true" style="min-width: 160px">
      <template #body="{ data }">
        <div class="node-name-cell">
          <span class="node-name">{{ data.name }}</span>
          <span class="node-host">{{ data.host }}:{{ data.port }}</span>
        </div>
      </template>
    </Column>

    <!-- Datacenter -->
    <Column field="datacenter_name" header="DC" :sortable="true" style="width: 100px">
      <template #body="{ data }">
        <span class="col-muted">{{ data.datacenter_name || '—' }}</span>
      </template>
    </Column>

    <!-- Read-only -->
    <Column header="R/O" style="width: 70px">
      <template #body="{ data }">
        <Tag
          v-if="data.live !== null"
          :value="data.live?.readonly ? 'RO' : 'RW'"
          :severity="data.live?.readonly ? 'warn' : 'success'"
        />
        <span v-else class="col-muted">—</span>
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
        <Tag
            v-else-if="data.live?.maintenance_drift"
            value="DRIFT"
            severity="danger"
            class="text-xs"
            v-tooltip.top="'maintenance flag set but node is read-write'"
        />
        <span v-else class="col-muted">—</span>
      </template>
    </Column>

    <!-- Flow Control -->
    <Column header="FC" style="width: 80px">
      <template #body="{ data }">
        <span
            class="mono-val"
            :class="fcClass(data.live?.wsrep_flow_control_paused ?? null)"
        >
          {{ data.live?.wsrep_flow_control_paused != null
            ? (data.live.wsrep_flow_control_paused * 100).toFixed(1) + '%'
            : '—' }}
        </span>
      </template>
    </Column>

    <!-- Recv Queue -->
    <Column header="RecvQ" style="width: 90px">
      <template #body="{ data }">
        <span
            class="mono-val"
            :class="recvClass(data.live?.wsrep_local_recv_queue ?? null)"
        >
          {{ data.live?.wsrep_local_recv_queue != null
            ? data.live.wsrep_local_recv_queue
            : '—' }}
        </span>
      </template>
    </Column>

    <!-- Last seen -->
    <Column header="Last seen" style="width: 120px">
      <template #body="{ data }">
        <span class="col-muted">
          {{ data.live?.last_check_ts ? formatRelative(data.live.last_check_ts) : '—' }}
        </span>
      </template>
    </Column>

    <!-- Enabled -->
    <Column field="enabled" header="Enabled" style="width: 90px">
      <template #body="{ data }">
        <span :class="['enabled-badge', data.enabled ? 'enabled-badge--on' : 'enabled-badge--off']">
          {{ data.enabled ? 'Yes' : 'No' }}
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
      <div class="table-empty">No nodes configured for this cluster.</div>
    </template>

    <template #loading>
      <div class="table-empty">Loading nodes…</div>
    </template>
  </DataTable>
</template>

<script setup lang="ts">
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
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
  if (val > 0.1)   return 'val-danger'
  if (val > 0.01)  return 'val-warn'
  return 'val-ok'
}

function recvClass(val: number | null) {
  if (val === null) return ''
  if (val > 10) return 'val-danger'
  if (val > 2)  return 'val-warn'
  return ''
}
</script>

<style scoped>
/* ── Header spacing ───────────────────────────────── */
:deep(.p-datatable-thead > tr > th) {
  padding: var(--space-3) var(--space-4) !important;
  font-size: var(--text-sm) !important;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--color-text-muted);
  white-space: nowrap;
}
:deep(.p-datatable-tbody > tr > td) {
  padding: var(--space-3) var(--space-4) !important;
}

.val-danger { color: var(--color-notification); }
.val-warn   { color: var(--color-gold); }
.val-ok     { color: var(--color-success); }
.node-name-cell { display: flex; flex-direction: column; gap: 2px; }
.node-name  { font-weight: 500; font-size: var(--text-sm); }
.node-host  { color: var(--color-text-muted); font-family: monospace; font-size: var(--text-xs); }
.col-muted  { color: var(--color-text-muted); font-size: var(--text-sm); }
.mono-val   { font-family: monospace; font-size: var(--text-sm); font-variant-numeric: tabular-nums; }
.table-empty { padding: var(--space-12); text-align: center; color: var(--color-text-muted); font-size: var(--text-sm); }
.enabled-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
}
.enabled-badge--on  { background: rgba(74,222,128,0.1); color: #4ade80; }
.enabled-badge--off { background: rgba(255,255,255,0.05); color: var(--color-text-faint); }
</style>
