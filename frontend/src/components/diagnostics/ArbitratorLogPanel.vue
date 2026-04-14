<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
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
        <select
          v-model="selectedId"
          class="sel"
          :disabled="loadingArbs || arbitrators.length === 0"
        >
          <option v-if="arbitrators.length === 0" :value="null">No arbitrators</option>
          <option v-for="a in arbitrators" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>

        <select v-model="lines" class="sel sel-lines">
          <option :value="20">20 lines</option>
          <option :value="50">50 lines</option>
          <option :value="100">100 lines</option>
        </select>

        <button class="btn-icon" :disabled="loading || !selectedId" @click="fetchLog" title="Refresh">
          <i :class="['pi', loading ? 'pi-spin pi-spinner' : 'pi-refresh']" />
        </button>
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

.sel {
  padding: var(--space-1) var(--space-3);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  outline: none;
  transition: border-color var(--transition-interactive);
}
.sel:focus { border-color: var(--color-primary); }
.sel:disabled { opacity: 0.5; cursor: not-allowed; }
.sel-lines { width: 100px; }

.btn-icon {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--transition-interactive), color var(--transition-interactive);
}
.btn-icon:hover:not(:disabled) { background: var(--color-surface-offset); color: var(--color-text); }
.btn-icon:disabled { opacity: 0.4; cursor: not-allowed; }

.alert-err {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-highlight);
  border: 1px solid oklch(from var(--color-error) l c h / 0.25);
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
