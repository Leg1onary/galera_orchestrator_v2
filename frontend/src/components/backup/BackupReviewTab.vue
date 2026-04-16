<template>
  <div class="review-tab">

    <!-- ── Toolbar: server selector + Scan button ── -->
    <div class="scan-toolbar">
      <div class="scan-toolbar__left">
        <label class="scan-label">Backup Server</label>
        <Select
          v-model="selectedServerId"
          :options="enabledServers"
          option-label="name"
          option-value="id"
          placeholder="Select a server…"
          class="server-select"
          :disabled="loadingServers || scanning"
        />
      </div>
      <Button
        label="Scan"
        icon="pi pi-search"
        :disabled="!selectedServerId || scanning"
        :loading="scanning"
        @click="runScan"
      />
    </div>

    <!-- ── No servers configured ── -->
    <div v-if="!loadingServers && enabledServers.length === 0" class="empty-state">
      <div class="empty-state__icon">
        <i class="pi pi-server" />
      </div>
      <div class="empty-state__body">
        <p class="empty-state__title">No backup servers configured</p>
        <p class="empty-state__desc">
          Add a backup server in Settings to start reviewing your backups.
        </p>
        <Button
          label="Open Settings"
          icon="pi pi-cog"
          severity="secondary"
          size="small"
          @click="goToSettings"
        />
      </div>
    </div>

    <!-- ── Scan error ── -->
    <Message v-if="scanError" severity="error" :closable="false" class="scan-error">
      <div class="msg-row">
        <span>{{ scanError }}</span>
        <Button
          label="Retry"
          icon="pi pi-refresh"
          severity="danger"
          size="small"
          text
          @click="runScan"
        />
      </div>
    </Message>

    <!-- ── Scan skeleton ── -->
    <div v-if="scanning" class="skeleton-wrap">
      <Skeleton v-for="i in 6" :key="i" height="40px" class="skeleton-row" border-radius="6px" />
    </div>

    <!-- ── Scan results ── -->
    <template v-else-if="scanResult">
      <!-- Meta bar -->
      <div class="scan-meta">
        <span class="scan-meta__dir"><i class="pi pi-folder" /> {{ scanResult.backup_dir }}</span>
        <span class="scan-meta__time">Scanned at {{ fmtDateTime(scanResult.scanned_at) }}</span>
        <span class="scan-meta__count">{{ scanResult.files.length }} file{{ scanResult.files.length !== 1 ? 's' : '' }}</span>
      </div>

      <!-- Empty directory -->
      <Message
        v-if="scanResult.files.length === 0"
        severity="info"
        :closable="false"
        class="empty-dir-msg"
      >
        No backup files found in this directory.
      </Message>

      <!-- File table -->
      <div v-else class="results-wrap">
        <DataTable
          :value="scanResult.files"
          class="backup-dt"
          :row-hover="true"
          sort-field="modified_at"
          :sort-order="-1"
          size="small"
        >
          <!-- Filename -->
          <Column field="filename" header="Filename" :sortable="true" style="min-width:200px">
            <template #body="{ data: f }">
              <span class="filename">{{ f.filename }}</span>
            </template>
          </Column>

          <!-- Type -->
          <Column field="type" header="Type" :sortable="true" style="min-width:120px">
            <template #body="{ data: f }">
              <Tag
                :value="f.type"
                :severity="typeSeverity(f.type)"
                class="type-tag"
              />
            </template>
          </Column>

          <!-- Tool -->
          <Column field="tool" header="Tool" :sortable="true" style="min-width:130px">
            <template #body="{ data: f }">
              <Tag
                :value="f.tool"
                :severity="toolSeverity(f.tool)"
                class="tool-tag"
              />
            </template>
          </Column>

          <!-- Size -->
          <Column field="size_bytes" header="Size" :sortable="true" style="min-width:90px; text-align:right">
            <template #body="{ data: f }">
              <span class="cell-num">{{ fmtSize(f.size_bytes) }}</span>
            </template>
          </Column>

          <!-- Modified -->
          <Column field="modified_at" header="Modified" :sortable="true" style="min-width:160px">
            <template #body="{ data: f }">
              <span class="cell-muted">{{ f.modified_at ? fmtDateTime(f.modified_at) : '—' }}</span>
            </template>
          </Column>
        </DataTable>
      </div>
    </template>

    <!-- ── Initial idle state (server selected, scan not yet run) ── -->
    <div
      v-else-if="selectedServerId && !scanning && !scanError"
      class="idle-hint"
    >
      <i class="pi pi-info-circle" />
      <span>Click <b>Scan</b> to list backup files from the selected server.</span>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import Select   from 'primevue/select'
import Button   from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column   from 'primevue/column'
import Tag      from 'primevue/tag'
import Message  from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import { useQuery } from '@tanstack/vue-query'
import { backupApi, type BackupScanResult, type BackupType, type BackupTool } from '@/api/backup'
import { useClusterStore } from '@/stores/cluster'

const router       = useRouter()
const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)

// ── Server list (enabled only) ────────────────────────────────────────────────
const { data: allServers, isLoading: loadingServers } = useQuery({
  queryKey: computed(() => ['cluster', clusterId.value, 'backup-servers']),
  queryFn:  () => backupApi.listServers(clusterId.value!),
  enabled:  computed(() => !!clusterId.value),
})

const enabledServers = computed(
  () => (allServers.value ?? []).filter((s) => s.enabled)
)

// ── Scan state ────────────────────────────────────────────────────────────────
const selectedServerId = ref<number | null>(null)
const scanning         = ref(false)
const scanResult       = ref<BackupScanResult | null>(null)
const scanError        = ref<string | null>(null)

// Reset scan when cluster or server changes
watch(clusterId, () => {
  selectedServerId.value = null
  scanResult.value       = null
  scanError.value        = null
})

watch(selectedServerId, () => {
  scanResult.value = null
  scanError.value  = null
})

async function runScan() {
  if (!clusterId.value || !selectedServerId.value) return
  scanning.value   = true
  scanError.value  = null
  scanResult.value = null
  try {
    scanResult.value = await backupApi.scan(clusterId.value, selectedServerId.value)
  } catch (err: any) {
    const detail = err?.response?.data?.detail ?? err?.message ?? 'Unknown error'
    scanError.value = `Scan failed: ${detail}`
  } finally {
    scanning.value = false
  }
}

function goToSettings() {
  router.push({ name: 'settings' })
}

// ── Formatters ────────────────────────────────────────────────────────────────
function fmtSize(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`
  if (bytes >= 1_048_576)     return `${(bytes / 1_048_576).toFixed(1)} MB`
  if (bytes >= 1_024)         return `${(bytes / 1_024).toFixed(1)} KB`
  return `${bytes} B`
}

function fmtDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      year:   'numeric',
      month:  '2-digit',
      day:    '2-digit',
      hour:   '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

// ── Tag severities ────────────────────────────────────────────────────────────
function typeSeverity(type: BackupType): string {
  switch (type) {
    case 'full':        return 'success'
    case 'schema-only': return 'warn'
    default:            return 'secondary'
  }
}

function toolSeverity(tool: BackupTool): string {
  switch (tool) {
    case 'mysqldump':   return 'info'
    case 'mariabackup': return 'contrast'
    default:            return 'secondary'
  }
}
</script>

<style scoped>
.review-tab {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ── Scan toolbar ── */
.scan-toolbar {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.scan-toolbar__left {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 240px;
}
.scan-label {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.server-select {
  min-width: 240px;
}

/* ── Empty state (no servers) ── */
.empty-state {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-8) var(--space-6);
  background: var(--color-surface-2);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
}
.empty-state__icon {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-offset);
  border-radius: var(--radius-lg);
  color: var(--color-text-faint);
  font-size: 1.5rem;
}
.empty-state__body { display: flex; flex-direction: column; gap: var(--space-2); }
.empty-state__title { font-size: var(--text-sm); font-weight: 600; color: var(--color-text); }
.empty-state__desc  { font-size: var(--text-sm); color: var(--color-text-muted); max-width: 380px; }

/* ── Error message ── */
.scan-error { width: 100%; }
.msg-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  width: 100%;
}

/* ── Skeletons ── */
.skeleton-wrap { display: flex; flex-direction: column; gap: var(--space-2); }
.skeleton-row  { width: 100%; }

/* ── Scan meta bar ── */
.scan-meta {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  flex-wrap: wrap;
}
.scan-meta__dir {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-mono);
  color: var(--color-text);
  font-weight: 500;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.scan-meta__dir .pi { color: var(--color-text-faint); flex-shrink: 0; }
.scan-meta__time  { color: var(--color-text-muted); white-space: nowrap; }
.scan-meta__count {
  padding: 2px var(--space-3);
  background: var(--color-primary-highlight);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-weight: 600;
  white-space: nowrap;
}

.empty-dir-msg { width: 100%; }

/* ── Results DataTable ── */
.results-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
:deep(.backup-dt .p-datatable-table-container) { border: none; box-shadow: none; border-radius: 0; }
:deep(.backup-dt .p-datatable-thead > tr > th) {
  padding: var(--space-3) var(--space-5) !important;
  font-size: var(--text-xs) !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint) !important;
  background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
  white-space: nowrap;
}
:deep(.backup-dt .p-datatable-tbody > tr > td) {
  padding: var(--space-3) var(--space-5) !important;
  border-bottom: 1px solid var(--color-border-muted) !important;
  vertical-align: middle;
}
:deep(.backup-dt .p-datatable-tbody > tr:last-child > td) { border-bottom: none !important; }
:deep(.backup-dt .p-datatable-tbody > tr:hover > td)      { background: rgba(45,212,191,0.04) !important; }
:deep(.backup-dt .p-datatable-tbody > tr)                  { background: var(--color-surface); }

/* ── Cell styles ── */
.filename {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text);
  word-break: break-all;
}
.cell-num {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: right;
  display: block;
}
.cell-muted {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.type-tag,
.tool-tag { font-size: var(--text-xs) !important; }

/* ── Idle hint ── */
.idle-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
.idle-hint .pi { color: var(--color-text-faint); flex-shrink: 0; }
</style>
