<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button label="Add arbitrator" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <DataTable :value="items" :loading="isLoading" dataKey="id" size="small">
      <Column field="name" header="Name" :sortable="true" />
      <Column field="host" header="Host">
        <template #body="{ data }">
          <span class="mono-cell">{{ data.host }}:{{ data.port }}</span>
        </template>
      </Column>
      <Column field="datacenter_id" header="DC">
        <template #body="{ data }">{{ dcName(data.datacenter_id) }}</template>
      </Column>
      <Column field="enabled" header="Enabled" :pt="{ root: { style: 'width: 80px' } }">
        <template #body="{ data }">
          <!-- MAJOR fix: class="text-xs" → :pt -->
          <Tag
              :value="data.enabled ? 'Yes' : 'No'"
              :severity="data.enabled ? 'success' : 'secondary'"
              :pt="{ root: { class: 'tag-cell' } }"
          />
        </template>
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
        <div class="empty-row">No arbitrators configured.</div>
      </template>
    </DataTable>

    <EntityFormModal
        v-if="modal.open"
        :title="modal.mode === 'create' ? 'Add arbitrator' : 'Edit arbitrator'"
        :fields="arbFields"
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
        warning-text="The arbitrator will be removed from monitoring."
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
import Tag      from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { settingsApi, type ArbitratorSetting } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useClusterStore } from '@/stores/cluster'

const qc           = useQueryClient()
const toast        = useToast()
const clusterStore = useClusterStore()

// MAJOR fix: не используем ! в computed — guard в хендлерах
const clusterId  = computed(() => clusterStore.selectedClusterId)
const contourId  = computed(() => clusterStore.selectedContourId)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'arbitrators-settings']),
  queryFn:  () => settingsApi.listArbitrators(clusterId.value!),
  enabled:  computed(() => !!clusterId.value),
})

// MAJOR fix: queryKey включает contourId (согласованность с DatacentersTab)
const { data: datacenters } = useQuery({
  queryKey: computed(() => ['datacenters', contourId.value]),
  queryFn:  () => settingsApi.listDatacenters(contourId.value ?? undefined),
})

const dcOptions = computed(() => [
  { label: '— None —', value: null },
  ...(datacenters.value ?? []).map((d) => ({ label: d.name, value: d.id })),
])

function dcName(id: number | null) {
  return datacenters.value?.find((d) => d.id === id)?.name ?? '—'
}

const arbFields = computed((): FormField[] => [
  { key: 'name',          label: 'Name',       required: true, placeholder: 'arb-01' },
  { key: 'host',          label: 'Host / IP',  required: true, placeholder: '10.0.0.4' },
  { key: 'port',          label: 'garbd Port', type: 'number', min: 1, max: 65535 },
  { key: 'ssh_user',      label: 'SSH User',   placeholder: 'root' },
  { key: 'ssh_port',      label: 'SSH Port',   type: 'number', min: 1, max: 65535 },
  { key: 'datacenter_id', label: 'Datacenter', type: 'select', options: dcOptions.value },
  { key: 'enabled',       label: 'Enabled',    type: 'toggle', toggleLabel: 'Monitor this arbitrator' },
  { key: 'description',   label: 'Description', type: 'textarea' },
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
      description:   arb.description ?? '',
    },
  }
  apiError.value = null
}
function openDelete(arb: ArbitratorSetting) { deleteTarget.value = arb }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  // MAJOR fix: guard вместо !
  if (!clusterId.value) { apiError.value = 'No cluster selected'; return }
  saving.value = true
  apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await settingsApi.createArbitrator(clusterId.value, values as any)
    } else {
      await settingsApi.updateArbitrator(clusterId.value, modal.value.id!, values as any)
    }
    // MAJOR fix: await
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
    await settingsApi.deleteArbitrator(clusterId.value, deleteTarget.value.id)
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
.tab-content { display: flex; flex-direction: column; gap: var(--space-4); }
.tab-toolbar { display: flex; justify-content: flex-end; }
.row-actions { display: flex; gap: var(--space-1); }
.mono-cell   { font-family: var(--font-mono, monospace); font-size: var(--text-xs); }
.tag-cell    { font-size: var(--text-xs); }
.empty-row   { padding: var(--space-4); color: var(--color-text-muted); font-size: var(--text-sm); }
</style>