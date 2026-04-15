<script setup lang="ts">
import { ref, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { diagnosticsApi, type ConfigHealthNodeResult } from '@/api/diagnostics'
import PanelToolbar from './PanelToolbar.vue'

const props = defineProps<{ active: boolean }>()
const clusterStore = useClusterStore()

const loading = ref(false)
const error = ref<string | null>(null)
const results = ref<ConfigHealthNodeResult[]>([])
const fetched = ref(false)

const STATUS_META = {
  ok: { icon: 'pi-check-circle', cls: 'status-ok', label: 'OK' },
  warn: { icon: 'pi-exclamation-circle', cls: 'status-warn', label: 'WARN' },
  error: { icon: 'pi-times-circle', cls: 'status-error', label: 'ERR' },
  info: { icon: 'pi-info-circle', cls: 'status-info', label: 'INFO' },
} as const

async function load() {
  const cid = clusterStore.selectedClusterId
  if (!cid) return
  loading.value = true
  error.value = null
  try {
    results.value = await diagnosticsApi.getConfigHealth(cid)
    fetched.value = true
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

watch(() => props.active, (val) => {
  if (val && !fetched.value) load()
})

watch(() => clusterStore.selectedClusterId, () => {
  fetched.value = false
  results.value = []
})
</script>

<template>
  <div class="cfg-health-panel">
    <PanelToolbar
      title="Config Health Check"
      description="Проверка ключевых параметров MariaDB по best-practice правилам."
      icon="pi-shield"
      :loading="loading"
      @refresh="load"
    />

    <div v-if="error" class="panel-error">
      <i class="pi pi-exclamation-triangle" />
      <span>{{ error }}</span>
    </div>

    <div v-else-if="!fetched && !loading" class="panel-idle">
      <i class="pi pi-shield" />
      <span>Нажми Refresh для запуска проверки</span>
    </div>

    <div v-else-if="loading" class="panel-loading">
      <i class="pi pi-spin pi-spinner" />
      <span>Проверяем ноды…</span>
    </div>

    <template v-else>
      <div v-for="node in results" :key="node.node_id" class="node-block">
        <div class="node-header">
          <span class="node-name">{{ node.node_name }}</span>
          <span class="node-host">{{ node.host }}</span>
          <span v-if="node.error" class="node-err-badge">
            <i class="pi pi-times-circle" /> {{ node.error }}
          </span>
          <template v-else>
            <span
              v-for="st in ['error', 'warn', 'ok', 'info']"
              :key="st"
              :class="['node-stat-badge', STATUS_META[st as keyof typeof STATUS_META].cls]"
            >
              {{ node.checks.filter(c => c.status === st).length }}
              {{ STATUS_META[st as keyof typeof STATUS_META].label }}
            </span>
          </template>
        </div>

        <table v-if="node.checks.length" class="checks-table">
          <thead>
            <tr>
              <th>Параметр</th>
              <th>Значение</th>
              <th>Статус</th>
              <th>Рекомендация / Контекст</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="chk in node.checks" :key="chk.param" :class="'row-' + chk.status">
              <td class="param-cell"><code>{{ chk.param }}</code></td>
              <td class="val-cell">{{ chk.current_human }}</td>
              <td class="st-cell">
                <span :class="['st-badge', STATUS_META[chk.status].cls]">
                  <i :class="['pi', STATUS_META[chk.status].icon]" />
                  {{ STATUS_META[chk.status].label }}
                </span>
              </td>
              <td class="rec-cell">
                <span v-if="chk.recommendation" class="rec-text">{{ chk.recommendation }}</span>
                <span v-if="chk.context" class="ctx-text">{{ chk.context }}</span>
                <span v-if="!chk.recommendation && !chk.context" class="ctx-text">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.cfg-health-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.panel-error,
.panel-idle,
.panel-loading {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.panel-error {
  color: var(--color-error);
}

.node-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.node-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-offset);
  border-bottom: 1px solid var(--color-border);
}

.node-name {
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--color-text);
}

.node-host {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-family: monospace;
}

.node-err-badge {
  font-size: var(--text-xs);
  color: var(--color-error);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.node-stat-badge {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.checks-table {
  width: 100%;
  border-collapse: collapse;
}

.checks-table th {
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.checks-table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid oklch(from var(--color-border) l c h / 0.5);
  font-size: var(--text-sm);
  vertical-align: top;
}

.checks-table tr:last-child td {
  border-bottom: none;
}

.row-error td:first-child { border-left: 2px solid var(--color-error); }
.row-warn td:first-child { border-left: 2px solid var(--color-warning); }
.row-ok td:first-child { border-left: 2px solid var(--color-success); }
.row-info td:first-child { border-left: 2px solid var(--color-blue); }

.param-cell code {
  font-size: var(--text-xs);
  background: var(--color-surface-offset);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  color: var(--color-text);
}

.val-cell {
  font-family: monospace;
  color: var(--color-text);
}

.st-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.status-ok { color: var(--color-success); background: var(--color-success-highlight); }
.status-warn { color: var(--color-warning); background: var(--color-warning-highlight); }
.status-error { color: var(--color-error); background: var(--color-error-highlight); }
.status-info { color: var(--color-blue); background: var(--color-blue-highlight); }

.rec-cell {
  max-width: 420px;
}

.rec-text {
  display: block;
  color: var(--color-text);
  line-height: 1.4;
}

.ctx-text {
  display: block;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  margin-top: 2px;
}
</style>
