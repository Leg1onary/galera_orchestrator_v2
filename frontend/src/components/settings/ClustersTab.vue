<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button label="Add cluster" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <DataTable :value="items" :loading="isLoading" dataKey="id" size="small">
      <Column field="name" header="Name" :sortable="true" />
      <Column field="db_host" header="DB Host">
        <template #body="{ data }">
          <!-- MAJOR fix: utility font-mono text-xs → scoped класс -->
          <span class="mono-cell">{{ data.db_host }}:{{ data.db_port }}</span>
        </template>
      </Column>
      <Column field="db_user" header="DB User">
        <template #body="{ data }">
          <span class="mono-cell">{{ data.db_user }}</span>
        </template>
      </Column>
      <!-- MINOR fix: style → :pt -->
      <Column header="" :pt="{ root: { style: 'width: 80px' } }">
        <template #body="{ data }">
          <!-- MAJOR fix: flex gap-1 → scoped класс -->
          <div class="row-actions">
            <Button icon="pi pi-pencil" text rounded size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="openDelete(data)" />
          </div>
        </template>
      </Column>
      <template #empty>
        <div class="empty-row">No clusters configured.</div>
      </template>
    </DataTable>

    <!-- MAJOR fix: fields через computed, не вызов в template -->
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
// BLOCKER fix: раздельные импорты
import DataTable from 'primevue/datatable'
import Column   from 'primevue/column'
import Button   from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type ClusterSetting } from '@/api/settings'
import { extractApiError } from '@/utils/api'   // MAJOR fix: утилита
import { useClusterStore } from '@/stores/cluster'

const qc           = useQueryClient()
const toast        = useToast()
const clusterStore = useClusterStore()
const contourId    = computed(() => clusterStore.selectedContourId)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['clusters-settings', contourId.value]),
  queryFn:  () => settingsApi.listClusters(contourId.value ?? undefined),
})

// MAJOR fix: через computed, чтобы не создавался новый массив при каждом рендере
const clusterFields = computed<FormField[]>(() => [
  { key: 'name',        label: 'Name',        required: true },
  { key: 'db_host',     label: 'DB Host',     required: true, placeholder: '10.0.0.1' },
  { key: 'db_port',     label: 'DB Port',     type: 'number', min: 1, max: 65535 },
  { key: 'db_user',     label: 'DB User',     placeholder: 'monitoring' },
  {
    key:      'db_password',
    label:    modal.value.mode === 'create' ? 'DB Password' : 'DB Password (leave blank to keep)',
    type:     'password',
    required: modal.value.mode === 'create',
  },
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
      db_host:     c.db_host,
      db_port:     c.db_port,
      db_user:     c.db_user,
      description: c.description ?? '',
      // db_password намеренно не передаём
    },
  }
  apiError.value = null
}
function openDelete(c: ClusterSetting) { deleteTarget.value = c }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  // MAJOR fix: guard вместо non-null assertion
  if (!contourId.value) {
    apiError.value = 'No contour selected'
    return
  }
  saving.value = true
  apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await settingsApi.createCluster({ ...values, contour_id: contourId.value } as any)
    } else {
      // MINOR fix: явно строим patch без db_password если пустой
      const { db_password, ...rest } = values
      const patch: Record<string, unknown> = { ...rest }
      if (db_password) patch.db_password = db_password
      await settingsApi.updateCluster(modal.value.id!, patch as any)
    }
    await qc.invalidateQueries({ queryKey: ['clusters-settings'] })
    await qc.invalidateQueries({ queryKey: ['clusters'] })
    toast.add({ severity: 'success', summary: 'Saved', life: 2500 })
    closeModal()
  } catch (err) {
    // MAJOR fix: extractApiError вместо дублирующегося err?.response?.data?.detail
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
.tab-content  { display: flex; flex-direction: column; gap: var(--space-4); }
.tab-toolbar  { display: flex; justify-content: flex-end; }
/* MAJOR fix: utility классы → scoped */
.row-actions  { display: flex; gap: var(--space-1); }
.mono-cell    { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.empty-row    { padding: var(--space-4); color: var(--color-text-muted); font-size: var(--text-sm); }
</style>