<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <button class="btn-add" @click="openCreate">
        <i class="pi pi-plus" />
        Add cluster
      </button>
    </div>

    <!-- ── Table ── -->
    <div class="s-table-wrap">
      <table class="s-table">
        <thead>
          <tr>
            <th class="s-table__th">Name <i class="pi pi-sort-alt s-table__sort-icon" /></th>
            <th class="s-table__th">Contour</th>
            <th class="s-table__th">Description</th>
            <th class="s-table__th s-table__th--actions" />
          </tr>
        </thead>
        <tbody>
          <!-- Loading skeleton -->
          <template v-if="isLoading">
            <tr v-for="i in 3" :key="i" class="s-table__row">
              <td><span class="skeleton skeleton-text" /></td>
              <td><span class="skeleton skeleton-text" /></td>
              <td><span class="skeleton skeleton-text" /></td>
              <td />
            </tr>
          </template>

          <!-- Empty -->
          <tr v-else-if="!items?.length">
            <td colspan="4" class="s-table__empty">
              <i class="pi pi-server" style="font-size:1.5rem; opacity:0.3; display:block; margin-bottom:0.5rem" />
              No clusters configured.
            </td>
          </tr>

          <!-- Rows -->
          <tr v-else v-for="row in items" :key="row.id" class="s-table__row">
            <td class="s-table__td s-table__td--name">{{ row.name }}</td>
            <td class="s-table__td">
              <span class="mono-cell">{{ row.contour_name ?? row.contour_id }}</span>
            </td>
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
/* All shared styles live in assets/settings-shared.css */
</style>
