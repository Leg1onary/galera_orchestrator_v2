<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'
import NodeTable from '@/components/nodes/NodeTable.vue'
import NodeDetailDrawer from '@/components/nodes/NodeDetailDrawer.vue'
import EntityFormModal, { type FormField } from '@/components/settings/EntityFormModal.vue'
import { settingsApi } from '@/api/settings'
import { useQuery } from '@tanstack/vue-query'
import { extractApiError } from '@/utils/api'
import type { NodeListItem, NodeStatusItem } from '@/api/nodes'

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId!)
const qc           = useQueryClient()
const toast        = useToast()

const { data, isLoading, refetch } = useClusterStatus(clusterId)

const nodes = computed<NodeListItem[]>(() =>
  (data.value?.nodes ?? []).map((n: NodeStatusItem) => ({
    id:               n.id,
    name:             n.name,
    host:             n.host,
    port:             n.port,
    ssh_port:         n.ssh_port,
    ssh_user:         n.ssh_user,
    db_user:          n.db_user,
    enabled:          n.enabled,
    maintenance:      n.maintenance,
    datacenter_id:    n.dc_id,
    datacenter_name:  n.dc_name,
    cluster_id:       clusterId.value,
    live:             n.live ?? null,
  }))
)

const selectedNode = ref<NodeListItem | null>(null)

function onSelect(node: NodeListItem) {
  selectedNode.value = node
}
function onDrawerClose() {
  selectedNode.value = null
}

// ── Add node modal ──────────────────────────────────────────────────────────
const showAddModal = ref(false)
const saving       = ref(false)
const apiError     = ref<string | null>(null)

const { data: datacenters } = useQuery({
  queryKey: ['datacenters'],
  queryFn:  () => settingsApi.listDatacenters(),
})

const dcOptions = computed(() => [
  { label: '— None —', value: null },
  ...(datacenters.value ?? []).map((d: { id: number; name: string }) => ({ label: d.name, value: d.id })),
])

const addNodeFields = computed((): FormField[] => [
  { key: 'name',          label: 'Name',        required: true,  placeholder: 'node-01' },
  { key: 'host',          label: 'Host / IP',   required: true,  placeholder: '10.0.0.1' },
  { key: 'port',          label: 'DB Port',     type: 'number',  min: 1, max: 65535, placeholder: '3306' },
  { key: 'ssh_user',      label: 'SSH User',    placeholder: 'root' },
  { key: 'ssh_port',      label: 'SSH Port',    type: 'number',  min: 1, max: 65535, placeholder: '22' },
  { key: 'db_user',       label: 'DB User',     placeholder: 'monitor_user' },
  { key: 'db_password',   label: 'DB Password', type: 'password', placeholder: '••••••••' },
  { key: 'datacenter_id', label: 'Datacenter',  type: 'select',  options: dcOptions.value, placeholder: '— None —' },
  { key: 'enabled',       label: 'Enabled',     type: 'toggle',  toggleLabel: 'Monitor this node' },
])

const addNodeDefaults = computed(() => ({
  name: '', host: '', port: 3306,
  ssh_user: 'root', ssh_port: 22,
  db_user: '', db_password: '',
  datacenter_id: null, enabled: true,
}))

function openAddModal() {
  apiError.value = null
  showAddModal.value = true
}

async function handleAddSubmit(values: Record<string, unknown>) {
  if (!clusterId.value) { apiError.value = 'No cluster selected'; return }
  saving.value = true
  apiError.value = null
  try {
    await settingsApi.createNode({ cluster_id: clusterId.value, ...(values as any) })
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes-settings'] })
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'status'] })
    await refetch()
    toast.add({ severity: 'success', summary: 'Node added', life: 2500 })
    showAddModal.value = false
  } catch (err) {
    apiError.value = extractApiError(err)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="nodes-page anim-fade-in">

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" />
      <span>No cluster selected</span>
    </div>

    <template v-else>
      <div class="pg-header">
        <div class="section-title">Nodes
          <span class="pg-count">{{ nodes.length }}</span>
        </div>
        <div class="pg-header__actions">
          <button class="btn-add" @click="openAddModal">
            <i class="pi pi-plus" />
            Add node
          </button>
          <Button
            icon="pi pi-refresh"
            severity="secondary"
            text
            size="small"
            :loading="isLoading"
            @click="refetch()"
            v-tooltip.left="'Refresh'"
            aria-label="Refresh nodes"
          />
        </div>
      </div>

      <div v-if="isLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner" /><span>Loading nodes&hellip;</span>
      </div>

      <div v-else-if="nodes.length === 0" class="pg-empty">
        <i class="pi pi-inbox" />
        <span>No nodes registered for this cluster</span>
      </div>

      <NodeTable
        v-else
        :nodes="nodes"
        :loading="isLoading"
        :cluster-id="clusterId"
        @select="onSelect"
        @refresh="refetch()"
      />
    </template>

    <NodeDetailDrawer
      :node="selectedNode"
      :cluster-id="clusterId"
      @close="onDrawerClose"
    />

    <EntityFormModal
      v-if="showAddModal"
      title="Add node"
      submit-label="Add node"
      :fields="addNodeFields"
      :initial-values="addNodeDefaults"
      :loading="saving"
      :api-error="apiError"
      @submit="handleAddSubmit"
      @cancel="showAddModal = false"
    />
  </div>
</template>

<style scoped>
.nodes-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.pg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pg-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.btn-add {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: rgba(45,212,191,0.1);
  border: 1px solid rgba(45,212,191,0.25);
  border-radius: var(--radius-md);
  color: #2dd4bf;
  font-size: var(--text-sm);
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 150ms ease;
}
.btn-add:hover { background: rgba(45,212,191,0.18); border-color: rgba(45,212,191,0.4); }
.btn-add .pi  { font-size: 0.75rem; }

.pg-count {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  font-weight: 500;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 1px 7px;
  margin-left: var(--space-2);
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

.loading-state {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-8);
  font-size: var(--text-sm);
}
</style>
