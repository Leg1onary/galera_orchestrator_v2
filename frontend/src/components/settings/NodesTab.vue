<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <button class="btn-add" @click="openCreate">
        <i class="pi pi-plus" />
        Add node
      </button>
    </div>

    <div class="s-table-wrap">
      <table class="s-table">
        <thead>
          <tr>
            <th class="s-table__th">Name <i class="pi pi-sort-alt s-table__sort-icon" /></th>
            <th class="s-table__th">Host</th>
            <th class="s-table__th">SSH</th>
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
              <td><span class="skeleton skeleton-text" /></td>
              <td><span class="skeleton skeleton-text" style="width:40px" /></td>
              <td />
            </tr>
          </template>

          <tr v-else-if="!items?.length">
            <td colspan="6" class="s-table__empty">
              <i class="pi pi-server" style="font-size:1.5rem;opacity:0.3;display:block;margin-bottom:0.5rem" />
              No nodes configured.
            </td>
          </tr>

          <tr v-else v-for="row in items" :key="row.id" class="s-table__row">
            <td class="s-table__td s-table__td--name">{{ row.name }}</td>
            <td class="s-table__td">
              <span class="mono-cell">{{ row.host }}:{{ row.port }}</span>
            </td>
            <td class="s-table__td">
              <span class="mono-cell">{{ row.ssh_user }}:{{ row.ssh_port }}</span>
            </td>
            <td class="s-table__td">{{ dcName(row.datacenter_id) }}</td>
            <td class="s-table__td">
              <span :class="['status-badge', row.enabled ? 'status-badge--yes' : 'status-badge--no']">
                {{ row.enabled ? 'Yes' : 'No' }}
              </span>
            </td>
            <td class="s-table__td s-table__td--actions">
              <div class="row-actions">
                <button class="row-btn row-btn--clone" @click="openClone(row)" title="Clone node">
                  <i class="pi pi-copy" />
                </button>
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
      :title="modalTitle"
      :fields="nodeFields"
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
      warning-text="The node will be removed from monitoring."
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
import { settingsApi, type NodeSetting } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useClusterStore } from '@/stores/cluster'

const qc           = useQueryClient()
const toast        = useToast()
const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'nodes-settings']),
  queryFn:  () => settingsApi.listNodes(clusterId.value!),
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

type ModalMode = 'create' | 'edit' | 'clone'

const modal = ref<{
  open:     boolean
  mode:     ModalMode
  id?:      number
  initial?: Record<string, unknown>
}>({ open: false, mode: 'create' })

// db_password hint differs by mode: edit = keep existing if empty, create/clone = required
const nodeFields = computed((): FormField[] => [
  { key: 'name',          label: 'Name',          required: true, placeholder: 'db-01' },
  { key: 'host',          label: 'Host / IP',      required: true, placeholder: '10.0.0.1' },
  { key: 'port',          label: 'MySQL Port',     type: 'number', min: 1, max: 65535, placeholder: '3306' },
  { key: 'ssh_user',      label: 'SSH User',       placeholder: 'root' },
  { key: 'ssh_port',      label: 'SSH Port',       type: 'number', min: 1, max: 65535, placeholder: '22' },
  { key: 'db_user',       label: 'DB User',        required: true, placeholder: 'monitor' },
  {
    key:          'db_password',
    label:        'DB Password',
    type:         'password',
    required:     modal.value.mode === 'create',
    placeholder:  modal.value.mode === 'edit' ? 'leave empty to keep current' : '••••••••',
    hint:         modal.value.mode === 'edit'
                    ? 'Leave empty to keep the existing password.'
                    : modal.value.mode === 'clone'
                    ? 'Cannot be copied for security reasons. Enter password for the new node.'
                    : undefined,
  },
  {
    key: 'datacenter_id', label: 'Datacenter',     type: 'select',
    options: dcOptions.value,
  },
  { key: 'enabled', label: 'Enabled', type: 'toggle', toggleLabel: 'Monitor this node' },
])

const modalTitle = computed(() => {
  if (modal.value.mode === 'edit')  return 'Edit node'
  if (modal.value.mode === 'clone') return 'Clone node'
  return 'Add node'
})

const deleteTarget = ref<NodeSetting | null>(null)
const saving       = ref(false)
const deleting     = ref(false)
const apiError     = ref<string | null>(null)

function openCreate() {
  modal.value = { open: true, mode: 'create' }
  apiError.value = null
}

function openEdit(node: NodeSetting) {
  modal.value = {
    open: true, mode: 'edit', id: node.id,
    initial: {
      name:          node.name,
      host:          node.host,
      port:          node.port,
      ssh_user:      node.ssh_user,
      ssh_port:      node.ssh_port,
      db_user:       node.db_user,
      db_password:   '',
      datacenter_id: node.datacenter_id,
      enabled:       node.enabled,
    },
  }
  apiError.value = null
}

// Clone: prefill name as "Copy of <original>", host from original so user can adjust,
// all other params copied as-is. db_password is intentionally empty —
// the backend does not expose passwords in GET /api/settings/nodes response.
function openClone(node: NodeSetting) {
  modal.value = {
    open: true, mode: 'clone',
    initial: {
      name:          `Copy of ${node.name}`,
      host:          node.host,
      port:          node.port,
      ssh_user:      node.ssh_user,
      ssh_port:      node.ssh_port,
      db_user:       node.db_user,
      db_password:   '',
      datacenter_id: node.datacenter_id,
      enabled:       node.enabled,
    },
  }
  apiError.value = null
}

function openDelete(node: NodeSetting) { deleteTarget.value = node }
function closeModal() { modal.value = { open: false, mode: 'create' } }

async function handleSubmit(values: Record<string, unknown>) {
  if (!clusterId.value) { apiError.value = 'No cluster selected'; return }
  saving.value = true; apiError.value = null
  try {
    if (modal.value.mode === 'edit') {
      await settingsApi.updateNode(modal.value.id!, values as any)
    } else {
      // both 'create' and 'clone' go through createNode
      await settingsApi.createNode({ cluster_id: clusterId.value, ...(values as any) })
    }
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes-settings'] })
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
    await settingsApi.deleteNode(deleteTarget.value.id)
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'nodes-settings'] })
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

.row-btn--clone {
  color: var(--color-text-faint);
}
.row-btn--clone:hover {
  color: var(--color-primary, #2dd4bf);
  background: rgba(45, 212, 191, 0.08);
}
</style>
