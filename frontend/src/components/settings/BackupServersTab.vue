<template>
  <div class="tab-content">
    <div class="tab-toolbar">
      <Button
        icon="pi pi-plus"
        label="Add backup server"
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
            <span>No backup servers configured.</span>
          </div>
        </template>

        <!-- Name -->
        <Column field="name" header="Name" :sortable="true" style="min-width:140px">
          <template #body="{ data }">
            <span class="cell-name">{{ data.name }}</span>
          </template>
        </Column>

        <!-- Host -->
        <Column field="host" header="Host" style="min-width:160px">
          <template #body="{ data }">
            <span class="cell-mono">{{ data.host }}:{{ data.ssh_port }}</span>
          </template>
        </Column>

        <!-- SSH User -->
        <Column field="ssh_user" header="SSH User" style="min-width:100px">
          <template #body="{ data }">
            <span class="cell-mono">{{ data.ssh_user }}</span>
          </template>
        </Column>

        <!-- Backup Dir -->
        <Column field="backup_dir" header="Backup Dir" style="min-width:180px">
          <template #body="{ data }">
            <span class="cell-path">{{ data.backup_dir }}</span>
          </template>
        </Column>

        <!-- Status -->
        <Column field="enabled" header="Status" style="min-width:90px">
          <template #body="{ data }">
            <Tag
              :value="data.enabled ? 'Enabled' : 'Disabled'"
              :severity="data.enabled ? 'success' : 'secondary'"
              class="status-tag"
            />
          </template>
        </Column>

        <!-- Actions -->
        <Column header="" style="width:96px; text-align:right">
          <template #body="{ data }">
            <div class="row-actions">
              <button class="row-btn row-btn--edit" title="Edit" @click="openEdit(data)">
                <i class="pi pi-pencil" />
              </button>
              <button class="row-btn row-btn--delete" title="Delete" @click="openDeleteModal(data)">
                <i class="pi pi-trash" />
              </button>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Create/Edit modal via EntityFormModal -->
    <EntityFormModal
      v-if="modal.open"
      :title="modal.mode === 'create' ? 'Add backup server' : 'Edit backup server'"
      :fields="serverFields"
      :initial-values="modal.initial"
      :loading="saving"
      :api-error="apiError"
      submit-label="Save"
      @submit="handleSubmit"
      @cancel="closeModal"
    />

    <!-- Delete confirm modal -->
    <DeleteConfirmModal
      v-if="deleteTarget"
      :entity-name="deleteTarget.name"
      warning-text="All scan history will be lost. Actual backup files on disk are NOT deleted."
      :loading="deleting"
      @confirm="handleDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column    from 'primevue/column'
import Button    from 'primevue/button'
import Tag       from 'primevue/tag'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import EntityFormModal, { type FormField } from './EntityFormModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { backupApi, type BackupServer } from '@/api/backup'
import { extractApiError } from '@/utils/api'
import { useClusterStore } from '@/stores/cluster'

const qc           = useQueryClient()
const toast        = useToast()
const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)

const { data: items, isLoading } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'backup-servers']),
  queryFn:  () => backupApi.listServers(clusterId.value!),
  enabled:  computed(() => !!clusterId.value),
})

// ── Form fields ───────────────────────────────────────────────────────────────
const serverFields = computed((): FormField[] => [
  {
    key:         'name',
    label:       'Name',
    required:    true,
    placeholder: 'backup-server-01',
  },
  {
    key:         'host',
    label:       'Host / IP',
    required:    true,
    placeholder: '10.0.0.10',
  },
  {
    key:         'ssh_port',
    label:       'SSH Port',
    type:        'number',
    min:         1,
    max:         65535,
    placeholder: '22',
  },
  {
    key:         'ssh_user',
    label:       'SSH User',
    placeholder: 'root',
  },
  {
    key:         'backup_dir',
    label:       'Backup Directory',
    required:    true,
    placeholder: '/mnt/backups/cluster-a',
    hint:        'Absolute path on the backup server where backup files are stored.',
  },
  {
    key:         'enabled',
    label:       'Enabled',
    type:        'toggle',
    toggleLabel: 'Include in scans',
  },
])

// ── Modal state ───────────────────────────────────────────────────────────────
const modal = ref<{
  open:     boolean
  mode:     'create' | 'edit'
  id?:      number
  initial?: Record<string, unknown>
}>({ open: false, mode: 'create' })

const deleteTarget = ref<BackupServer | null>(null)
const saving       = ref(false)
const deleting     = ref(false)
const apiError     = ref<string | null>(null)

function openCreate() {
  modal.value = { open: true, mode: 'create' }
  apiError.value = null
}

function openEdit(srv: BackupServer) {
  modal.value = {
    open: true,
    mode: 'edit',
    id:   srv.id,
    initial: {
      name:       srv.name,
      host:       srv.host,
      ssh_port:   srv.ssh_port,
      ssh_user:   srv.ssh_user,
      backup_dir: srv.backup_dir,
      enabled:    srv.enabled,
    },
  }
  apiError.value = null
}

function openDeleteModal(srv: BackupServer) { deleteTarget.value = srv }
function closeModal() { modal.value = { open: false, mode: 'create' } }

// ── Submit ────────────────────────────────────────────────────────────────────
async function handleSubmit(values: Record<string, unknown>) {
  if (!clusterId.value) { apiError.value = 'No cluster selected'; return }
  saving.value = true; apiError.value = null
  try {
    if (modal.value.mode === 'create') {
      await backupApi.createServer({ cluster_id: clusterId.value, ...(values as any) })
    } else {
      await backupApi.updateServer(modal.value.id!, values as any)
    }
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'backup-servers'] })
    toast.add({ severity: 'success', summary: 'Saved', life: 2500 })
    closeModal()
  } catch (err) {
    apiError.value = extractApiError(err)
  } finally {
    saving.value = false
  }
}

// ── Delete ────────────────────────────────────────────────────────────────────
async function handleDelete() {
  if (!deleteTarget.value || !clusterId.value) return
  deleting.value = true
  try {
    await backupApi.deleteServer(deleteTarget.value.id)
    await qc.invalidateQueries({ queryKey: ['cluster', clusterId.value, 'backup-servers'] })
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

/* ── DataTable — same pattern as ArbitratorsTab ── */
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
:deep(.settings-table .p-datatable-tbody > tr:hover > td)      { background: rgba(45,212,191,0.04) !important; }
:deep(.settings-table .p-datatable-tbody > tr)                  { background: var(--color-surface); }

/* ── Cells ── */
.cell-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-mono {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.cell-path {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  word-break: break-all;
}

/* ── Status tag passthrough ── */
.status-tag { font-size: var(--text-xs) !important; }

/* ── Row actions ── */
.row-actions { display: flex; gap: var(--space-2); justify-content: flex-end; }
.row-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md); border: none; background: transparent;
  cursor: pointer; transition: all 150ms ease; font-size: 0.8rem;
}
.row-btn--edit:hover   { color: var(--color-primary); background: var(--color-primary-dim); }
.row-btn--delete       { color: var(--color-text-faint); }
.row-btn--delete:hover { color: var(--color-error);   background: rgba(248,113,113,0.1); }
.row-btn--edit         { color: var(--color-text-faint); }

/* ── Empty state ── */
.st-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: var(--space-3); padding: var(--space-16) var(--space-4);
  color: var(--color-text-faint); font-size: var(--text-sm);
}
.st-empty .pi { font-size: 1.75rem; opacity: 0.25; }
</style>
