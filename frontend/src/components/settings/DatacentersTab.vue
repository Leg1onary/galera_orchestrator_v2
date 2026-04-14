<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <button class="btn-add" @click="openCreate">
        <i class="pi pi-plus" />
        Add datacenter
      </button>
    </div>

    <div class="s-table-wrap">
      <table class="s-table">
        <thead>
          <tr>
            <th class="s-table__th">Name <i class="pi pi-sort-alt s-table__sort-icon" /></th>
            <th class="s-table__th">Description</th>
            <th class="s-table__th s-table__th--actions" />
          </tr>
        </thead>
        <tbody>
          <template v-if="isLoading">
            <tr v-for="i in 3" :key="i" class="s-table__row">
              <td><span class="skeleton skeleton-text" /></td>
              <td><span class="skeleton skeleton-text" style="width:200px" /></td>
              <td />
            </tr>
          </template>

          <tr v-else-if="!items?.length">
            <td colspan="3" class="s-table__empty">
              <i class="pi pi-building" style="font-size:1.5rem;opacity:0.3;display:block;margin-bottom:0.5rem" />
              No datacenters configured.
            </td>
          </tr>

          <tr v-else v-for="row in items" :key="row.id" class="s-table__row">
            <td class="s-table__td s-table__td--name">{{ row.name }}</td>
            <td class="s-table__td">{{ row.description || '—' }}</td>
            <td class="s-table__td s-table__td--actions">
              <div class="row-actions">
                <button class="row-btn row-btn--edit" @click="openEdit(row)" title="Edit">
                  <i class="pi pi-pencil" />
                </button>
                <button class="row-btn row-btn--delete" @click="openDelete(row)" title="Delete">
                  <i class="pi pi-trash" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

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
import { ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type Datacenter } from '@/api/settings'
import { extractApiError } from '@/utils/api'

const qc    = useQueryClient()
const toast = useToast()

// fix #1: datacenters are global — remove contourId guard that silently blocked saves
const { data: items, isLoading } = useQuery({
  queryKey: ['datacenters'],
  queryFn:  () => settingsApi.listDatacenters(),
})

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

function openCreate() { modal.value = { open: true, mode: 'create' }; apiError.value = null }
function openEdit(dc: Datacenter) {
  modal.value = {
    open: true, mode: 'edit', id: dc.id,
    initial: { name: dc.name, description: dc.description ?? '' },
  }
  apiError.value = null
}
function openDelete(dc: Datacenter) { deleteTarget.value = dc }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  saving.value = true; apiError.value = null
  try {
    const description = (values.description as string)?.trim() || undefined
    if (modal.value.mode === 'create') {
      await settingsApi.createDatacenter({ name: values.name as string, description })
    } else {
      await settingsApi.updateDatacenter(modal.value.id!, { name: values.name as string, description })
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
    toast.add({ severity: 'error', summary: 'Error', detail: extractApiError(err), life: 5000 })
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
/* All shared styles live in assets/settings-shared.css */
</style>
