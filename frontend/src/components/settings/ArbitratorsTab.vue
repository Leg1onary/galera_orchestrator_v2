<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button
        icon="pi pi-plus"
        label="Add arbitrator"
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
            <span>No arbitrators configured.</span>
          </div>
        </template>

        <Column field="name" header="Name" :sortable="true" style="min-width:140px">
          <template #body="{ data }">
            <span class="cell-name">{{ data.name }}</span>
          </template>
        </Column>

        <Column field="host" header="Host" style="min-width:160px">
          <template #body="{ data }">
            <span class="cell-mono">{{ data.host }}:{{ data.port }}</span>
          </template>
        </Column>

        <Column field="datacenter_id" header="DC" style="min-width:80px">
          <template #body="{ data }">
            <span class="cell-muted">{{ dcName(data.datacenter_id) }}</span>
          </template>
        </Column>

        <Column field="enabled" header="Enabled" style="min-width:90px">
          <template #body="{ data }">
            <span :class="['status-badge', data.enabled ? 'status-badge--yes' : 'status-badge--no']">
              {{ data.enabled ? 'Yes' : 'No' }}
            </span>
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
      :title="modal.mode === 'create' ? 'Add arbitrator' : 'Edit arbitrator'"
      :fields="arbitratorFields"
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
import { settingsApi, type ArbitratorSetting } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useClusterStore } from '@/stores/cluster'

const qc           = useQueryClient()
const toast        = useToast()
const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'arbitrators-settings']),
  queryFn:  () => settingsApi.listArbitrators(clusterId.value!),
  enabled:  computed(() => !!clusterId.value),
})

const { data: datacenters } = useQuery({
  queryKey: ['datacenters'],
  queryFn:  () => settingsApi.listDatacenters(),
})

const dcOptions = computed(() => [
  { label: '— None —', value: null },
  ...(datacenters.value ?? []).map((d) => ({ label: d.name, value: d.id })),
])

function dcName(id: number | null) {
  return datacenters.value?.find((d) => d.id === id)?.name ?? '—'
}

// fix #2 (arbitrators): arbFields fully computed so dcOptions is always fresh
const arbFields = computed((): FormField[] => [
  { key: 'name',          label: 'Name',       required: true, placeholder: 'arb-01' },
  { key: 'host',          label: 'Host / IP',  required: true, placeholder: '10.0.0.4' },
  { key: 'port',          label: 'garbd Port', type: 'number', min: 1, max: 65535, placeholder: '4567' },
  { key: 'ssh_user',      label: 'SSH User',   placeholder: 'root' },
  { key: 'ssh_port',      label: 'SSH Port',   type: 'number', min: 1, max: 65535, placeholder: '22' },
  {
    key: 'datacenter_id', label: 'Datacenter', type: 'select',
    options: dcOptions.value,
  },
  { key: 'enabled', label: 'Enabled', type: 'toggle', toggleLabel: 'Monitor this arbitrator' },
])

const modal = ref<{
  open:     boolean
  mode:     'create' | 'edit'
  id?:      number
  initial?: Record<string, unknown>
}>({ open: false, mode: 'create' })

const deleteTarget = ref<ArbitratorSetting | null>(null)
const saving       = ref(false)
const deleting     = ref(false)
const apiError     = ref<string | null>(null)

function openCreate() { modal.value = { open: true, mode: 'create' }; apiError.value = null }
function openEdit(arb: ArbitratorSetting) {
  modal.value = {
    open: true, mode: 'edit', id: arb.id,
    initial: {
      name:          arb.name,
      host:          arb.host,
      port:          arb.port,
      ssh_user:      arb.ssh_user,
      ssh_port:      arb.ssh_port,
      datacenter_id: arb.datacenter_id,
      enabled:       arb.enabled,
    },
  }
  apiError.value = null
}
function openDelete(arb: ArbitratorSetting) { deleteTarget.value = arb }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  if (!clusterId.value) { apiError.value = 'No cluster selected'; return }
  saving.value = true; apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await settingsApi.createArbitrator({ cluster_id: clusterId.value, ...(values as any) })
    } else {
      await settingsApi.updateArbitrator(modal.value.id!, values as any)
    }
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'arbitrators-settings'] })
    toast.add({ severity: 'success', summary: 'Saved', life: 2500 })
    closeModal()
  } catch (err) {
    apiError.value = extractApiError(err)
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!deleteTarget.value || !clusterId.value) return
  deleting.value = true
  try {
    await settingsApi.deleteArbitrator(deleteTarget.value.id)
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'arbitrators-settings'] })
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

.st-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

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
}
:deep(.settings-table .p-datatable-tbody > tr > td) {
  padding: var(--space-4) var(--space-6) !important;
  border-bottom: 1px solid var(--color-border-muted) !important;
  vertical-align: middle;
}
:deep(.settings-table .p-datatable-tbody > tr:last-child > td) { border-bottom: none !important; }
:deep(.settings-table .p-datatable-tbody > tr:hover > td) { background: rgba(45,212,191,0.04) !important; }
:deep(.settings-table .p-datatable-tbody > tr) { background: var(--color-surface); }

.cell-name  { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-mono  { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-muted { font-size: var(--text-sm); color: var(--color-text-muted); }

.status-badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: var(--radius-full);
  font-size: var(--text-xs); font-weight: 600; border: 1px solid transparent;
}
.status-badge--yes { background: rgba(74,222,128,0.1); color: var(--color-synced); border-color: rgba(74,222,128,0.2); }
.status-badge--no  { background: rgba(255,255,255,0.05); color: var(--color-text-faint); border-color: rgba(255,255,255,0.07); }

.row-actions { display: flex; gap: var(--space-2); justify-content: flex-end; }
.row-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md); border: none; background: transparent;
  cursor: pointer; transition: all 150ms ease; font-size: 0.8rem;
}
.row-btn--edit   { color: var(--color-text-faint); }
.row-btn--edit:hover   { color: var(--color-primary); background: var(--color-primary-dim); }
.row-btn--delete { color: var(--color-text-faint); }
.row-btn--delete:hover { color: var(--color-error); background: rgba(248,113,113,0.1); }

.st-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: var(--space-3); padding: var(--space-16) var(--space-4);
  color: var(--color-text-faint); font-size: var(--text-sm);
}
.st-empty .pi { font-size: 1.75rem; opacity: 0.25; }
</style>