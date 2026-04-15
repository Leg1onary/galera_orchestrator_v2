<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button
        icon="pi pi-plus"
        label="Add cluster"
        size="small"
        class="btn-add-pv"
        @click="openCreate"
      />
    </div>

    <div class="st-wrap">
      <DataTable
        :value="items ?? []"
        :loading="isLoading"
        sort-field="name"
        :sort-order="1"
        row-hover
        class="settings-table"
        data-key="id"
      >
        <template #empty>
          <div class="st-empty">
            <i class="pi pi-server" />
            <span>No clusters configured.</span>
          </div>
        </template>

        <Column field="name" header="Name" :sortable="true" style="min-width:160px">
          <template #body="{ data }">
            <span class="cell-name">{{ data.name }}</span>
          </template>
        </Column>

        <Column field="contour_name" header="Contour" style="min-width:120px">
          <template #body="{ data }">
            <span class="cell-mono">{{ data.contour_name ?? data.contour_id }}</span>
          </template>
        </Column>

        <Column field="description" header="Description">
          <template #body="{ data }">
            <span class="cell-muted">{{ data.description || '—' }}</span>
          </template>
        </Column>

        <Column header="" style="width:96px; text-align:right">
          <template #body="{ data }">
            <div class="row-actions">
              <button class="row-btn row-btn--edit" title="Edit" @click="openEdit(data)">
                <i class="pi pi-pencil" />
              </button>
              <button class="row-btn row-btn--delete" title="Delete" @click="openDelete(data)">
                <i class="pi pi-trash" />
              </button>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <EntityFormModal
      v-if="modal.open"
      :title="modal.mode === 'create' ? 'Add cluster' : 'Edit cluster'"
      :fields="clusterFields"
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
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type ClusterSetting } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useClusterStore } from '@/stores/cluster'

const qc           = useQueryClient()
const toast        = useToast()
const clusterStore = useClusterStore()
const contourId    = computed(() => clusterStore.selectedContourId)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['clusters-settings', contourId.value]),
  queryFn:  () => settingsApi.listClusters(contourId.value ?? undefined),
})

const clusterFields = computed<FormField[]>(() => [
  { key: 'name',        label: 'Name',        required: true },
  { key: 'description', label: 'Description', type: 'textarea' },
])

const modal = ref<{
  open:     boolean
  mode:     'create' | 'edit'
  id?:      number
  initial?: Record<string, unknown>
}>({ open: false, mode: 'create' })

const deleteTarget = ref<ClusterSetting | null>(null)
const saving       = ref(false)
const deleting     = ref(false)
const apiError     = ref<string | null>(null)

function openCreate() {
  modal.value = { open: true, mode: 'create' }
  apiError.value = null
}
function openEdit(c: ClusterSetting) {
  modal.value = {
    open: true, mode: 'edit', id: c.id,
    initial: {
      name:        c.name,
      description: c.description ?? '',
    },
  }
  apiError.value = null
}
function openDelete(c: ClusterSetting) { deleteTarget.value = c }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  if (!contourId.value) { apiError.value = 'No contour selected'; return }
  saving.value = true
  apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await settingsApi.createCluster({ ...values, contour_id: contourId.value } as any)
    } else {
      await settingsApi.updateCluster(modal.value.id!, values as any)
    }
    await qc.invalidateQueries({ queryKey: ['clusters-settings'] })
    await qc.invalidateQueries({ queryKey: ['clusters'] })
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
    await settingsApi.deleteCluster(deleteTarget.value.id)
    await qc.invalidateQueries({ queryKey: ['clusters-settings'] })
    await qc.invalidateQueries({ queryKey: ['clusters'] })
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
.tab-content { display: flex; flex-direction: column; gap: var(--space-5); }
.tab-toolbar { display: flex; justify-content: flex-end; }

.btn-add-pv { /* handled by global .p-button */ }

.st-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

/* DataTable overrides */
:deep(.settings-table .p-datatable-table-container) { border: none; box-shadow: none; border-radius: 0; }
:deep(.settings-table .p-datatable-thead > tr > th) {
  padding: var(--space-4) var(--space-6) !important;
  font-size: var(--text-xs) !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint) !important;
  background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
  white-space: nowrap;
  user-select: none;
}
:deep(.settings-table .p-datatable-tbody > tr > td) {
  padding: var(--space-4) var(--space-6) !important;
  border-bottom: 1px solid var(--color-border-muted) !important;
  vertical-align: middle;
}
:deep(.settings-table .p-datatable-tbody > tr:last-child > td) { border-bottom: none !important; }
:deep(.settings-table .p-datatable-tbody > tr:hover > td) {
  background: rgba(45,212,191,0.04) !important;
}
:deep(.settings-table .p-datatable-tbody > tr) { background: var(--color-surface); }

/* Cells */
.cell-name  { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-mono  { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-muted { font-size: var(--text-sm); color: var(--color-text-muted); }

/* Row actions */
.row-actions { display: flex; gap: var(--space-2); justify-content: flex-end; }
.row-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
  border: none; background: transparent;
  cursor: pointer; transition: all 150ms ease;
  font-size: 0.8rem;
}
.row-btn--edit   { color: var(--color-text-faint); }
.row-btn--edit:hover   { color: var(--color-primary); background: var(--color-primary-dim); }
.row-btn--delete { color: var(--color-text-faint); }
.row-btn--delete:hover { color: var(--color-error); background: rgba(248,113,113,0.1); }

/* Empty state */
.st-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: var(--space-3); padding: var(--space-16) var(--space-4);
  color: var(--color-text-faint); font-size: var(--text-sm);
}
.st-empty .pi { font-size: 1.75rem; opacity: 0.25; }
</style>
