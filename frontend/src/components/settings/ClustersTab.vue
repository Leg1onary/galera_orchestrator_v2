<!-- Аналогичен DatacentersTab, но с полями db_host, db_port, db_user, db_password -->
<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button label="Add cluster" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <DataTable :value="items" :loading="isLoading" dataKey="id" size="small">
      <Column field="name" header="Name" :sortable="true" />
      <Column field="db_host" header="DB Host">
        <template #body="{ data }">
          <span class="font-mono text-xs">{{ data.db_host }}:{{ data.db_port }}</span>
        </template>
      </Column>
      <Column field="db_user" header="DB User">
        <template #body="{ data }">
          <span class="font-mono text-xs">{{ data.db_user }}</span>
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
      <template #empty><div class="empty-row">No clusters configured.</div></template>
    </DataTable>

    <EntityFormModal
        v-if="modal.open"
        :title="modal.mode === 'create' ? 'Add cluster' : 'Edit cluster'"
        :fields="CLUSTER_FIELDS(modal.mode)"
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
        warning-text="All nodes and arbitrators of this cluster will also be deleted."
        :loading="deleting"
        @confirm="handleDelete"
        @cancel="deleteTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { DataTable, Column, Button, useToast } from 'primevue'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type ClusterSetting } from '@/api/settings'
import { useClusterStore } from '@/stores/cluster'

const qc = useQueryClient()
const toast = useToast()
const clusterStore = useClusterStore()
const contourId = computed(() => clusterStore.selectedContourId)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['clusters-settings', contourId.value]),
  queryFn: () => settingsApi.listClusters(contourId.value ?? undefined),
})

function CLUSTER_FIELDS(mode: 'create' | 'edit'): FormField[] {
  return [
    { key: 'name',        label: 'Name',         required: true },
    { key: 'db_host',     label: 'DB Host',      required: true, placeholder: '10.0.0.1' },
    { key: 'db_port',     label: 'DB Port',      type: 'number', min: 1, max: 65535, placeholder: '3306' },
    { key: 'db_user',     label: 'DB User',      placeholder: 'monitoring' },
    {
      key: 'db_password',
      label: mode === 'create' ? 'DB Password' : 'DB Password (leave blank to keep)',
      type: 'password',
      required: mode === 'create',
    },
    { key: 'description', label: 'Description',  type: 'textarea' },
  ]
}

const modal = ref<{ open: boolean; mode: 'create' | 'edit'; id?: number; initial?: Record<string, unknown> }>({
  open: false, mode: 'create',
})
const deleteTarget = ref<ClusterSetting | null>(null)
const saving = ref(false)
const deleting = ref(false)
const apiError = ref<string | null>(null)

function openCreate() { modal.value = { open: true, mode: 'create' }; apiError.value = null }
function openEdit(c: ClusterSetting) {
  modal.value = {
    open: true, mode: 'edit', id: c.id,
    initial: { name: c.name, db_host: c.db_host, db_port: c.db_port, db_user: c.db_user, description: c.description ?? '' },
  }
  apiError.value = null
}
function openDelete(c: ClusterSetting) { deleteTarget.value = c }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  saving.value = true; apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await settingsApi.createCluster({ ...values, contour_id: contourId.value! } as any)
    } else {
      const patch = { ...values }
      if (!patch.db_password) delete patch.db_password
      await settingsApi.updateCluster(modal.value.id!, patch as any)
    }
    qc.invalidateQueries({ queryKey: ['clusters-settings'] })
    qc.invalidateQueries({ queryKey: ['clusters'] })  // инвалидируем header switcher
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
    await settingsApi.deleteCluster(deleteTarget.value.id)
    qc.invalidateQueries({ queryKey: ['clusters-settings'] })
    qc.invalidateQueries({ queryKey: ['clusters'] })
    toast.add({ severity: 'success', summary: 'Deleted', life: 2500 })
    deleteTarget.value = null
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err?.response?.data?.detail ?? err.message, life: 5000 })
  } finally {
    deleting.value = false
  }
}
</script>