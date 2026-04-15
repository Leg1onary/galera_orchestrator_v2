<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type ArbitratorLogResult } from '@/api/diagnostics'
import { api } from '@/api/client'

type ArbitratorInfo = { id: number; name: string; enabled: boolean }

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

const arbitrators  = ref<ArbitratorInfo[]>([])
const selectedId   = ref<number | null>(null)
const lines        = ref<20 | 50 | 100>(50)
const logResult    = ref<ArbitratorLogResult | null>(null)
const loading      = ref(false)
const loadingArbs  = ref(false)
const error        = ref<string | null>(null)

// Skeleton widths initialised once in onMounted — no hydration mismatch on re-render
const skeletonWidths = ref<number[]>([])
onMounted(() => {
  skeletonWidths.value = Array.from({ length: 10 }, () => 50 + Math.floor(Math.random() * 45))
})

async function loadArbitrators() {
  const id = clusterStore.selectedClusterId
  if (!id) return
  loadingArbs.value = true
  try {
    const raw = await api.get<Array<{ id: number; name: string; enabled: boolean }>>(
      `/api/clusters/${id}/arbitrators`,
    )
    arbitrators.value = raw.data.filter((a) => a.enabled)
    if (arbitrators.value.length > 0 && selectedId.value === null) {
      selectedId.value = arbitrators.value[0].id
    }
  } catch {
    arbitrators.value = []
  } finally {
    loadingArbs.value = false
  }
}

async function fetchLog() {
  const clusterId = clusterStore.selectedClusterId
  const arbId     = selectedId.value
  if (!clusterId || !arbId || loading.value) return
  loading.value = true
  error.value   = null
  try {
    const result = await diagnosticsApi.arbitratorLog(clusterId, arbId, lines.value)
    if (result.error) {
      error.value     = result.error
      logResult.value = null
    } else {
      logResult.value = result
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.active,
  async (v) => {
    if (v) {
      await loadArbitrators()
      if (selectedId.value) fetchLog()
    }
  },
  { immediate: true }
)

watch(
  () => clusterStore.selectedClusterId,
  async () => {
    if (!props.active) return
    selectedId.value = null
    logResult.value  = null
    error.value      = null
    await loadArbitrators()
    if (selectedId.value) fetchLog()
  }
)

watch([selectedId, lines], () => {
  if (props.active && selectedId.value && !loading.value) fetchLog()
})

const logLines = computed(() => logResult.value?.lines ?? [])

const linesOptions = [
  { label: '20 lines', value: 20 as const },
  { label: '50 lines', value: 50 as const },
  { label: '100 lines', value: 100 as const },
]

function lineClass(line: string): string {
  const l = line.toLowerCase()
  if (l.includes('error') || l.includes('err]')) return 'line-err'
  if (l.includes('warn'))                         return 'line-warn'
  return ''
}
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">
        <i class="pi pi-file-edit" />
        <span>Arbitrator Log</span>
      </div>
      <div class="header-actions">
        <Select
          v-model="selectedId"
          :options="arbitrators.length === 0 ? [{ id: null, name: 'No arbitrators' }] : arbitrators"
          option-label="name"
          option-value="id"
          :disabled="loadingArbs || arbitrators.length === 0"
          class="sel-primevue"
        />

        <Select
          v-model="lines"
          :options="linesOptions"
          option-label="label"
          option-value="value"
          class="sel-primevue sel-primevue--lines"
        />

        <Button
          icon="pi pi-refresh"
          severity="secondary"
          :loading="loading"
          :disabled="loading || !selectedId"
          @click="fetchLog"
          v-tooltip.top="'Refresh'"
          aria-label="Refresh log"
        />
      </div>
    </div>

    <div v-if="error" class="alert-err">
      <i class="pi pi-exclamation-triangle" /> {{ error }}
    </div>

    <div v-if="arbitrators.length === 0 && !loadingArbs" class="empty-hint">
      <i class="pi pi-info-circle" /> No enabled arbitrators found in this cluster.
    </div>

    <div v-else-if="loading && !logResult" class="skeleton-log">
      <div
        v-for="(w, i) in skeletonWidths"
        :key="i"
        class="skeleton-line"
        :style="{ width: w + '%' }"
      />
    </div>

    <div v-else-if="logLines.length === 0 && !loading && !error && selectedId" class="empty-hint">
      <i class="pi pi-info-circle" /> No log output returned.
    </div>

    <template v-else-if="logLines.length > 0">
      <div class="log-meta">
        <span v-if="logResult">{{ logResult.arbitrator_name }} — {{ logLines.length }} lines</span>
        <span v-if="logResult?.fetched_at" class="ts">
          fetched at {{ new Date(logResult.fetched_at).toLocaleTimeString() }}
        </span>
      </div>

      <div class="log-box">
        <pre
          v-for="(line, idx) in logLines"
          :key="idx"
          class="log-line"
          :class="lineClass(line)"
        >{{ line }}</pre>
      </div>
    </template>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; gap: var(--space-4); }

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.header-actions { display: flex; align-items: center; gap: var(--space-2); }

/* PrimeVue Select styling in this panel */
.sel-primevue { min-width: 140px; }
.sel-primevue--lines { min-width: 100px; }

.alert-err {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid rgba(248,113,113,0.25);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.skeleton-log { display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-2); }
.skeleton-line {
  height: 14px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-surface-offset) 25%, var(--color-surface-dynamic) 50%, var(--color-surface-offset) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.log-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  padding: 0 var(--space-1);
}
.ts { color: var(--color-text-faint); }

.log-box {
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  max-height: 480px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.log-line {
  font-family: var(--font-mono, monospace);
  font-size: var(--text-xs);
  line-height: 1.6;
  color: var(--color-text-muted);
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  padding: 0;
}
.log-line.line-err  { color: var(--color-error); }
.log-line.line-warn { color: var(--color-warning); }
</style>
