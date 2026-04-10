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
import { ref, computed } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
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

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['datacenters', contourId.value]),
  queryFn:  () => settingsApi.listDatacenters(contourId.value ?? undefined),
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
  if (!contourId.value) { apiError.value = 'No contour selected'; return }
  saving.value = true; apiError.value = null
  try {
    const description = (values.description as string).trim() || undefined
    if (modal.value.mode === 'create') {
      await settingsApi.createDatacenter({ name: values.name as string, contour_id: contourId.value, description })
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
.tab-content  { display: flex; flex-direction: column; gap: var(--space-5); }
.tab-toolbar  { display: flex; justify-content: flex-end; }

.btn-add {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: rgba(45,212,191,0.1); border: 1px solid rgba(45,212,191,0.25);
  border-radius: var(--radius-md); color: #2dd4bf;
  font-size: var(--text-sm); font-weight: 500; font-family: inherit;
  cursor: pointer; transition: all 150ms ease;
}
.btn-add:hover { background: rgba(45,212,191,0.18); border-color: rgba(45,212,191,0.4); }
.btn-add .pi  { font-size: 0.75rem; }

.s-table-wrap { border: 1px solid rgba(255,255,255,0.06); border-radius: var(--radius-lg); overflow: hidden; background: #13141a; }
.s-table      { width: 100%; border-collapse: collapse; }
.s-table__th  { padding: var(--space-3) var(--space-4); text-align: left; font-size: var(--text-xs); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-faint); border-bottom: 1px solid rgba(255,255,255,0.06); white-space: nowrap; }
.s-table__th--actions { width: 72px; }
.s-table__sort-icon   { font-size: 0.65rem; opacity: 0.5; margin-left: 4px; }
.s-table__row { border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 120ms ease; }
.s-table__row:last-child { border-bottom: none; }
.s-table__row:hover { background: rgba(255,255,255,0.03); }
.s-table__td  { padding: var(--space-3) var(--space-4); font-size: var(--text-sm); color: var(--color-text-muted); vertical-align: middle; }
.s-table__td--name    { color: var(--color-text); font-weight: 500; }
.s-table__td--actions { text-align: right; }
.s-table__empty { padding: var(--space-12) var(--space-4); text-align: center; color: var(--color-text-faint); font-size: var(--text-sm); }

.row-actions { display: flex; gap: var(--space-1); justify-content: flex-end; }
.row-btn { width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-md); border: none; background: transparent; cursor: pointer; transition: all 150ms ease; font-size: 0.8rem; }
.row-btn--edit   { color: var(--color-text-faint); }
.row-btn--edit:hover   { color: #2dd4bf; background: rgba(45,212,191,0.1); }
.row-btn--delete { color: var(--color-text-faint); }
.row-btn--delete:hover { color: #f87171; background: rgba(248,113,113,0.1); }

.skeleton { display: inline-block; border-radius: var(--radius-sm); background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.05) 75%); background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; }
.skeleton-text { width: 120px; height: 14px; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
</style>
