<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button label="Add node" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <DataTable :value="items" :loading="isLoading" dataKey="id" size="small">
      <Column field="name" header="Name" :sortable="true" />
      <Column field="host" header="Host">
        <template #body="{ data }">
          <span class="font-mono text-xs">{{ data.host }}:{{ data.port }}</span>
        </template>
      </Column>
      <Column field="ssh_user" header="SSH">
        <template #body="{ data }">
          <span class="font-mono text-xs">{{ data.ssh_user }}@{{ data.host }}:{{ data.ssh_port }}</span>
        </template>
      </Column>
      <Column field="datacenter_id" header="DC">
        <template #body="{ data }">{{ dcName(data.datacenter_id) }}</template>
      </Column>
      <Column field="enabled" header="Enabled" style="width: 80px">
        <template #body="{ data }">
          <Tag :value="data.enabled ? 'Yes' : 'No'" :severity="data.enabled ? 'success' : 'secondary'" class="text-xs" />
        </template>
      </Column>
      <Column header="" style="width: 80px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text rounded size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="openDelete(data)" />
          </div>
        </template>
      </Column>
      <template #empty><div class="empty-row">No nodes configured.</div></template>
    </DataTable>

    <EntityFormModal
        v-if="modal.open"
        :title="modal.mode === 'create' ? 'Add node' : 'Edit node'"
        :fields="nodeFields"
        :initial-values="modal.initial"
        :loading="saving"
        :api-error="apiError"
        submit-label="Save"
        @submit="handleSubmit"
        @cancel="closeModal"
    />

    <DeleteConfirmModal
        v-if="deleteTarget"
        :entity-name="deleteTarget.name"
        warning-text="The node will be removed from monitoring."
        :loading="deleting"
        @confirm="handleDelete"
        @cancel="deleteTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { DataTable, Column, Button, Tag, useToast } from 'primevue'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type NodeSetting } from '@/api/settings'
import { useClusterStore } from '@/stores/cluster'

const qc = useQueryClient()
const toast = useToast()
const clusterStore = useClusterStore()
const clusterId = computed(() => clusterStore.selectedClusterId!)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'nodes-settings']),
  queryFn: () => settingsApi.listNodes(clusterId.value),
  enabled: computed(() => !!clusterId.value),
})

const { data: datacenters } = useQuery({
  queryKey: ['datacenters'],
  queryFn: () => settingsApi.listDatacenters(),
})

const dcOptions = computed(() => [
  { label: '— None —', value: null },
  ...(datacenters.value ?? []).map((d) => ({ label: d.name, value: d.id })),
])

function dcName(id: number | null) {
  return datacenters.value?.find((d) => d.id === id)?.name ?? '—'
}

const nodeFields = computed((): FormField[] => [
  { key: 'name',        label: 'Name',           required: true, placeholder: 'node-01' },
  { key: 'host',        label: 'Host / IP',       required: true, placeholder: '10.0.0.1' },
  { key: 'port',        label: 'DB Port',         type: 'number', min: 1, max: 65535, placeholder: '3306' },
  { key: 'ssh_user',    label: 'SSH User',        placeholder: 'root' },
  { key: 'ssh_port',    label: 'SSH Port',        type: 'number', min: 1, max: 65535, placeholder: '22' },
  { key: 'datacenter_id', label: 'Datacenter',   type: 'select', options: dcOptions.value, placeholder: 'Select DC' },
  { key: 'enabled',     label: 'Enabled',        type: 'toggle', toggleLabel: 'Monitor this node' },
  { key: 'description', label: 'Description',    type: 'textarea', placeholder: 'Optional' },
])

const modal = ref<{ open: boolean; mode: 'create' | 'edit'; id?: number; initial?: Record<string, unknown> }>({
  open: false, mode: 'create',
})
const deleteTarget = ref<NodeSetting | null>(null)
const saving = ref(false)
const deleting = ref(false)
const apiError = ref<string | null>(null)

function openCreate() { modal.value = { open: true, mode: 'create' }; apiError.value = null }
function openEdit(node: NodeSetting) {
  modal.value = {
    open: true, mode: 'edit', id: node.id,
    initial: {
      name: node.name, host: node.host, port: node.port,
      ssh_user: node.ssh_user, ssh_port: node.ssh_port,
      datacenter_id: node.datacenter_id, enabled: node.enabled,
      description: node.description ?? '',
    },
  }
  apiError.value = null
}
function openDelete(node: NodeSetting) { deleteTarget.value = node }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  saving.value = true
  apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await settingsApi.createNode(clusterId.value, values as any)
    } else {
      await settingsApi.updateNode(clusterId.value, modal.value.id!, values as any)
    }
    qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes-settings'] })
    qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes'] })
    toast.add({ severity: 'success', summary: 'Saved', life: 2500 })
    closeModal()
  } catch (err: any) {
    apiError.value = err?.response?.data?.detail ?? err.message
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await settingsApi.deleteNode(clusterId.value, deleteTarget.value.id)
    qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes-settings'] })
    qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes'] })
    toast.add({ severity: 'success', summary: 'Deleted', life: 2500 })
    deleteTarget.value = null
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err?.response?.data?.detail ?? err.message, life: 5000 })
  } finally {
    deleting.value = false
  }
}
</script>