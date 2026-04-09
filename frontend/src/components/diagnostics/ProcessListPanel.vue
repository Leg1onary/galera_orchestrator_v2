<template>
  <div class="diag-panel">
    <PanelToolbar
        title="Process list"
        :loading="isLoading"
        :fetched-at="fetchedAt"
        :auto-refresh="autoRefresh"
        @refresh="refetch()"
        @toggle-auto="autoRefresh = !autoRefresh"
    >
      <Select
          v-model="selectedNodeId"
          :options="nodeOptions"
          option-label="label"
          option-value="value"
          placeholder="All nodes"
          size="small"
          style="width: 180px"
          show-clear
      />
    </PanelToolbar>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />{{ (error as any)?.message }}
    </div>

    <DataTable
        :value="filtered"
        :loading="isLoading"
        dataKey="id"
        size="small"
        :rows="50"
        paginator
        paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink"
        sort-field="time"
        :sort-order="-1"
    >
      <template #header>
        <div class="flex items-center gap-2">
          <InputText
              v-model="search"
              placeholder="Filter by user, db, query…"
              size="small"
              style="width: 260px"
          />
          <ToggleSwitch v-model="hideSystem" />
          <span class="text-xs text-muted-color">Hide system</span>
        </div>
      </template>

      <Column field="id" header="ID" style="width: 70px" :sortable="true" />
      <Column field="user" header="User" style="width: 120px" :sortable="true" />
      <Column field="host" header="Host" style="width: 140px">
        <template #body="{ data }">
          <span class="font-mono text-xs">{{ data.host }}</span>
        </template>
      </Column>
      <Column field="db" header="DB" style="width: 100px">
        <template #body="{ data }">{{ data.db ?? '—' }}</template>
      </Column>
      <Column field="command" header="Command" style="width: 100px" />
      <Column field="time" header="Time (s)" style="width: 90px" :sortable="true">
        <template #body="{ data }">
          <span :class="data.time > 10 ? 'text-warning-color font-medium' : ''">
            {{ data.time }}
          </span>
        </template>
      </Column>
      <Column field="state" header="State" style="width: 130px">
        <template #body="{ data }">{{ data.state ?? '—' }}</template>
      </Column>
      <Column field="info" header="Query">
        <template #body="{ data }">
          <span
              v-if="data.info"
              class="font-mono text-xs query-cell"
              :title="data.info"
          >
            {{ data.info.slice(0, 120) }}{{ data.info.length > 120 ? '…' : '' }}
          </span>
          <span v-else class="text-muted-color">—</span>
        </template>
      </Column>
      <Column header="" style="width: 70px">
        <template #body="{ data }">
          <!-- fix: disabled когда нода не выбрана -->
          <Button
              v-if="data.command !== 'Daemon'"
              icon="pi pi-times"
              text
              rounded
              size="small"
              severity="danger"
              v-tooltip="selectedNodeId ? 'KILL ' + data.id : 'Select a node first'"
              :disabled="!selectedNodeId"
              :loading="killing === data.id"
              @click="handleKill(data)"
          />
        </template>
      </Column>

      <template #empty>
        <div class="empty-row">No active processes.</div>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { DataTable, Column, Button, Select, InputText, ToggleSwitch, useToast } from 'primevue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type ProcessRow } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'
import { useDiagAutoRefresh } from '@/composables/useDiagAutoRefresh'
import { useNodeOptions } from '@/composables/useNodeOptions'   // ← fix

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const toast = useToast()

const selectedNodeId = ref<number | undefined>(undefined)
const search = ref('')
const hideSystem = ref(true)
const killing = ref<number | null>(null)
const { autoRefresh, refetchInterval } = useDiagAutoRefresh(props)
const { nodeOptions } = useNodeOptions()   // ← fix: убрали statusSummary

const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
  queryKey: computed(() => ['diag-processes', clusterStore.selectedClusterId, selectedNodeId.value]),
  queryFn: () => diagnosticsApi.getProcessList(clusterStore.selectedClusterId!, selectedNodeId.value),
  enabled: computed(() => props.active && !!clusterStore.selectedClusterId),
  refetchInterval,
  staleTime: 0,
})

const fetchedAt = computed(() =>
    dataUpdatedAt.value ? new Date(dataUpdatedAt.value).toLocaleTimeString() : null
)

const filtered = computed(() => {
  let rows: ProcessRow[] = data.value ?? []
  if (hideSystem.value) {
    rows = rows.filter((r) => r.command !== 'Daemon' && r.user !== 'system user')
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    rows = rows.filter(
        (r) =>
            r.user.toLowerCase().includes(q) ||
            (r.db ?? '').toLowerCase().includes(q) ||
            (r.info ?? '').toLowerCase().includes(q),
    )
  }
  return rows
})

async function handleKill(row: ProcessRow) {
  if (!clusterStore.selectedClusterId || !selectedNodeId.value) return  // кнопка disabled, но guard остаётся
  killing.value = row.id
  try {
    const res = await diagnosticsApi.killProcess(
        clusterStore.selectedClusterId,
        selectedNodeId.value,
        row.id,
    )
    toast.add({
      severity: res.killed ? 'success' : 'warn',
      summary: res.killed ? `Killed process ${row.id}` : 'Kill failed',
      detail: res.message,
      life: 3000,
    })
    refetch()
  } catch (err: any) {
    toast.add({ severity: 'error', summary: 'Error', detail: err?.response?.data?.detail ?? err.message, life: 5000 })
  } finally {
    killing.value = null
  }
}
</script>

<style scoped>
.query-cell { display: block; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>