<template>
  <div class="diag-panel">
    <div class="toolbar">
      <span class="toolbar-title">connection_check</span>
      <div class="toolbar-actions">
        <span v-if="fetchedAt" class="fetched-at">{{ fetchedAt }}</span>
        <button class="btn-refresh" :disabled="isLoading" @click="run">
          <i :class="['pi', isLoading ? 'pi-spin pi-spinner' : 'pi-play']" />
          <span>{{ isLoading ? 'Checking…' : 'Run check' }}</span>
        </button>
      </div>
    </div>

    <div v-if="error" class="error-alert">
      <i class="pi pi-exclamation-circle" />
      <span>{{ (error as Error).message }}</span>
    </div>

    <template v-else-if="rows && rows.length">
      <div class="check-table">
        <div class="check-thead">
          <span>Name</span>
          <span>Role</span>
          <span>SSH</span>
          <span>DB</span>
          <span>SSH latency</span>
          <span>DB latency</span>
        </div>
        <div v-for="row in rows" :key="row.id + row.role" class="check-row">
          <span class="row-name">
            <i :class="['pi', row.role === 'Node' ? 'pi-server' : 'pi-circle']" class="role-icon" />
            {{ row.name }}
            <span class="row-host">{{ row.host }}</span>
          </span>
          <span>
            <span :class="['badge-role', row.role === 'Node' ? 'role-node' : 'role-arb']">{{ row.role }}</span>
          </span>
          <span>
            <StatusDot :ok="row.ssh_ok" />
          </span>
          <span>
            <StatusDot v-if="row.role === 'Node'" :ok="row.db_ok" />
            <span v-else class="text-faint">N/A</span>
          </span>
          <span class="lat">{{ row.ssh_latency_ms != null ? row.ssh_latency_ms + ' ms' : '—' }}</span>
          <span class="lat">{{ row.role === 'Node' && row.db_latency_ms != null ? row.db_latency_ms + ' ms' : '—' }}</span>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><i class="pi pi-wifi" /></div>
      <p>Click <strong>Run check</strong> to test all connections.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMutation }   from '@tanstack/vue-query'
import { useClusterStore }  from '@/stores/cluster'
import { diagnosticsApi, type ConnectionCheckRow } from '@/api/diagnostics'
import StatusDot from './StatusDot.vue'

defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()
const fetchedAt    = ref<string | null>(null)
const rows         = ref<ConnectionCheckRow[] | null>(null)
const error        = ref<Error | null>(null)

const { mutate, isPending: isLoading } = useMutation({
  mutationFn: () => diagnosticsApi.checkAll(clusterStore.selectedClusterId!),
  onSuccess: (data) => {
    rows.value     = data
    fetchedAt.value = new Date().toLocaleTimeString()
    error.value    = null
  },
  onError: (e: unknown) => {
    error.value = e instanceof Error ? e : new Error(String(e))
  },
})

function run() {
  if (!clusterStore.selectedClusterId) return
  mutate()
}
</script>

<style scoped>
.diag-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.toolbar-title {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text-muted);
  letter-spacing: 0.03em;
  text-transform: lowercase;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.fetched-at {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-faint);
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 5px var(--space-4);
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-normal);
}

.btn-refresh:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-refresh:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn-refresh .pi { font-size: 0.7rem; }

/* TABLE */
.check-table {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.check-thead,
.check-row {
  display: grid;
  grid-template-columns: 2fr 90px 64px 64px 110px 110px;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
}

.check-thead {
  background: var(--color-surface-2);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.check-row {
  border-bottom: 1px solid var(--color-border-muted);
  font-size: var(--text-sm);
  transition: background var(--transition-fast);
}

.check-row:last-child { border-bottom: none; }
.check-row:hover { background: var(--color-surface-3); }

.row-name {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 500;
  color: var(--color-text);
}

.row-host {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.role-icon { font-size: 0.7rem; color: var(--color-text-faint); }

.badge-role {
  display: inline-block;
  padding: 1px 7px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.role-node { background: rgba(45,212,191,0.12); color: var(--color-primary); }
.role-arb  { background: rgba(168,139,250,0.12); color: #a78bfa; }

.lat {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.text-faint { font-size: var(--text-xs); color: var(--color-text-faint); }

.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.20);
  color: var(--color-error); font-size: var(--text-sm);
}

.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-3);
  padding: var(--space-12);
  color: var(--color-text-muted); font-size: var(--text-sm); text-align: center;
}

.empty-icon {
  width: 44px; height: 44px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-3); border: 1px solid var(--color-border);
  color: var(--color-text-faint); font-size: 1.1rem;
}
</style>
