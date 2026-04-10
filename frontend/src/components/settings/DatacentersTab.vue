<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button label="Add datacenter" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <DataTable :value="items" :loading="isLoading" dataKey="id" size="small">
      <Column field="name" header="Name" :sortable="true" />
      <Column field="description" header="Description">
        <template #body="{ data }">{{ data.description || '—' }}</template>
      </Column>
      <Column header="" :pt="{ root: { style: 'width: 80px' } }">
        <template #body="{ data }">
          <div class="row-actions">
            <Button icon="pi pi-pencil" text rounded size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="openDelete(data)" />
          </div>
        </template>
      </Column>
      <template #empty>
        <div class="empty-row">No datacenters configured.</div>
      </template>
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
import { useQuery, useQueryClient } from '@tanstack/vue-query'
// BLOCKER fix: раздельные импорты; MINOR fix: убран лишний useMutation
import DataTable from 'primevue/datatable'
import Column   from 'primevue/column'
import Button   from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type Datacenter } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useClusterStore } from '@/stores/cluster'

const qc           = useQueryClient()
const toast        = useToast()
const clusterStore = useClusterStore()
const contourId    = computed(() => clusterStore.selectedContourId)

// BLOCKER fix: queryKey зависит от contourId
const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['datacenters', contourId.value]),
  queryFn:  () => settingsApi.listDatacenters(contourId.value ?? undefined),
})

// DC_FIELDS статичны — не зависят от mode, поэтому const (не computed)
const DC_FIELDS: FormField[] = [
  { key: 'name',        label: 'Name',        required: true, placeholder: 'dc-moscow' },
  { key: 'description', label: 'Description', type: 'textarea', placeholder: 'Optional' },
]

const modal = ref<{
  open:     boolean
  mode:     'create' | 'edit'
  id?:      number
  initial?: Record<string, unknown>
}>({ open: false, mode: 'create' })

const deleteTarget = ref<Datacenter | null>(null)
const saving       = ref(false)
const deleting     = ref(false)
const apiError     = ref<string | null>(null)

function openCreate() {
  modal.value = { open: true, mode: 'create' }
  apiError.value = null
}
function openEdit(dc: Datacenter) {
  modal.value = {
    open:    true,
    mode:    'edit',
    id:      dc.id,
    initial: { name: dc.name, description: dc.description ?? '' },
  }
  apiError.value = null
}
function openDelete(dc: Datacenter) { deleteTarget.value = dc }
function closeModal()               { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  // MAJOR fix: guard
  if (!contourId.value) {
    apiError.value = 'No contour selected'
    return
  }
  saving.value = true
  apiError.value = null
  try {
    // MINOR fix: явная проверка пустой строки вместо falsy
    const description = (values.description as string).trim() || undefined

    if (modal.value.mode === 'create') {
      await settingsApi.createDatacenter({
        name:        values.name as string,
        contour_id:  contourId.value,
        description,
      })
    } else {
      await settingsApi.updateDatacenter(modal.value.id!, {
        name: values.name as string,
        description,
      })
    }
    await qc.invalidateQueries({ queryKey: ['datacenters'] })
    toast.add({ severity: 'success', summary: 'Saved', life: 2500 })
    closeModal()
  } catch (err) {
    apiError.value = extractApiError(err)
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await settingsApi.deleteDatacenter(deleteTarget.value.id)
    await qc.invalidateQueries({ queryKey: ['datacenters'] })
    toast.add({ severity: 'success', summary: 'Deleted', life: 2500 })
    deleteTarget.value = null
  } catch (err) {
    toast.add({
      severity: 'error',
      summary:  'Error',
      detail:   extractApiError(err),
      life:     5000,
    })
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.tab-content { display: flex; flex-direction: column; gap: var(--space-4); }
.tab-toolbar { display: flex; justify-content: flex-end; }
.row-actions { display: flex; gap: var(--space-1); }
.empty-row   { padding: var(--space-4); color: var(--color-text-muted); font-size: var(--text-sm); }
</style>