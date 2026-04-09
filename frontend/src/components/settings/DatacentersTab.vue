<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button label="Add datacenter" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <DataTable :value="items" :loading="isLoading" dataKey="id" size="small">
      <Column field="name" header="Name" :sortable="true" />
      <Column field="description" header="Description">
        <template #body="{ data }">{{ data.description ?? '—' }}</template>
      </Column>
      <Column header="" style="width: 80px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text rounded size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="openDelete(data)" />
          </div>
        </template>
      </Column>
      <template #empty><div class="empty-row">No datacenters configured.</div></template>
    </DataTable>

    <EntityFormModal
        v-if="modal.open"
        :title="modal.mode === 'create' ? 'Add datacenter' : 'Edit datacenter'"
        :fields="DC_FIELDS"
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
        warning-text="All nodes and arbitrators assigned to this datacenter will become unassigned."
        :loading="deleting"
        @confirm="handleDelete"
        @cancel="deleteTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { DataTable, Column, Button, useToast } from 'primevue'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type Datacenter } from '@/api/settings'
import { useClusterStore } from '@/stores/cluster'

const qc = useQueryClient()
const toast = useToast()
const clusterStore = useClusterStore()
const contourId = computed(() => clusterStore.selectedContourId)

const { data: items, isLoading } = useQuery({
  queryKey: ['datacenters'],
  queryFn: () => settingsApi.listDatacenters(),
})

const DC_FIELDS: FormField[] = [
  { key: 'name', label: 'Name', required: true, placeholder: 'dc-moscow' },
  { key: 'description', label: 'Description', type: 'textarea', placeholder: 'Optional' },
]

// Modal state
const modal = ref<{ open: boolean; mode: 'create' | 'edit'; id?: number; initial?: Record<string, unknown> }>({
  open: false, mode: 'create',
})
const deleteTarget = ref<Datacenter | null>(null)
const saving = ref(false)
const deleting = ref(false)
const apiError = ref<string | null>(null)

function openCreate() {
  modal.value = { open: true, mode: 'create' }
  apiError.value = null
}
function openEdit(dc: Datacenter) {
  modal.value = { open: true, mode: 'edit', id: dc.id, initial: { name: dc.name, description: dc.description ?? '' } }
  apiError.value = null
}
function openDelete(dc: Datacenter) { deleteTarget.value = dc }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  saving.value = true
  apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await settingsApi.createDatacenter({
        name: values.name as string,
        contour_id: contourId.value!,
        description: values.description as string || undefined,
      })
    } else {
      await settingsApi.updateDatacenter(modal.value.id!, {
        name: values.name as string,
        description: values.description as string || undefined,
      })
    }
    qc.invalidateQueries({ queryKey: ['datacenters'] })
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
    await settingsApi.deleteDatacenter(deleteTarget.value.id)
    qc.invalidateQueries({ queryKey: ['datacenters'] })
    toast.add({ severity: 'success', summary: 'Deleted', life: 2500 })
    deleteTarget.value = null
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err?.response?.data?.detail ?? err.message, life: 5000 })
  } finally {
    deleting.value = false
  }
}
</script>