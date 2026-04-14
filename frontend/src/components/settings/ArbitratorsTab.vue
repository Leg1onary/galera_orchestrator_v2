<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <button class="btn-add" @click="openCreate">
        <i class="pi pi-plus" />
        Add arbitrator
      </button>
    </div>

    <div class="s-table-wrap">
      <table class="s-table">
        <thead>
          <tr>
            <th class="s-table__th">Name <i class="pi pi-sort-alt s-table__sort-icon" /></th>
            <th class="s-table__th">Host</th>
            <th class="s-table__th">DC</th>
            <th class="s-table__th">Enabled</th>
            <th class="s-table__th s-table__th--actions" />
          </tr>
        </thead>
        <tbody>
          <template v-if="isLoading">
            <tr v-for="i in 3" :key="i" class="s-table__row">
              <td><span class="skeleton skeleton-text" /></td>
              <td><span class="skeleton skeleton-text" /></td>
              <td><span class="skeleton skeleton-text" /></td>
              <td><span class="skeleton skeleton-text" style="width:40px" /></td>
              <td />
            </tr>
          </template>

          <tr v-else-if="!items?.length">
            <td colspan="5" class="s-table__empty">
              <i class="pi pi-server" style="font-size:1.5rem;opacity:0.3;display:block;margin-bottom:0.5rem" />
              No arbitrators configured.
            </td>
          </tr>

          <tr v-else v-for="row in items" :key="row.id" class="s-table__row">
            <td class="s-table__td s-table__td--name">{{ row.name }}</td>
            <td class="s-table__td">
              <span class="mono-cell">{{ row.host }}:{{ row.port }}</span>
            </td>
            <td class="s-table__td">{{ dcName(row.datacenter_id) }}</td>
            <td class="s-table__td">
              <span :class="['status-badge', row.enabled ? 'status-badge--yes' : 'status-badge--no']">
                {{ row.enabled ? 'Yes' : 'No' }}
              </span>
            </td>
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
/* All shared styles live in assets/settings-shared.css */
</style>
