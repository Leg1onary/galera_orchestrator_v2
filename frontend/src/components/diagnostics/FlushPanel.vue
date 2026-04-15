<template>
  <div class="diag-panel anim-fade-in">

    <div class="panel-head">
      <div class="panel-head-icon"><i class="pi pi-database" /></div>
      <div>
        <div class="panel-title">Flush Operations</div>
        <div class="panel-desc">Execute FLUSH commands on a specific node: rotate binary logs, lock tables for backup, or release locks.</div>
      </div>
    </div>

    <!-- Node selector -->
    <div class="form-card">
      <div class="field">
        <label class="field-label">Target Node</label>
        <Select
            v-model="selectedNodeId"
            :options="nodeOptions"
            option-label="label"
            option-value="value"
            placeholder="Select node…"
            size="small"
            class="field-select"
        />
      </div>

      <!-- Operation cards -->
      <div class="ops-grid">
        <div
            v-for="op in OPERATIONS"
            :key="op.value"
            :class="['op-card', selectedOp === op.value && 'op-card--active', op.danger && 'op-card--danger']" 
            @click="selectedOp = op.value"
        >
          <div class="op-card-header">
            <i :class="['pi', op.icon, 'op-icon']" />
            <span class="op-label">{{ op.label }}</span>
            <i v-if="op.danger" class="pi pi-exclamation-triangle op-warn" />
          </div>
          <div class="op-sql"><code>{{ op.sql }}</code></div>
          <div class="op-desc">{{ op.desc }}</div>
        </div>
      </div>

      <div class="form-footer">
        <Button
            :label="selectedOpMeta?.label ?? 'Execute'"
            :icon="selectedOpMeta?.icon ? 'pi ' + selectedOpMeta.icon : 'pi pi-play'"
            :severity="selectedOpMeta?.danger ? 'danger' : 'primary'"
            size="small"
            :disabled="!canExecute"
            :loading="loading"
            @click="handleExecute"
        />
      </div>
    </div>

    <!-- ConfirmDialog for destructive ops -->
    <ConfirmDialog group="flush-op">
      <template #message="{ message }">
        <div class="confirm-body">
          <i class="pi pi-exclamation-triangle confirm-icon" />
          <div>
            <div class="confirm-title">{{ message.header }}</div>
            <div class="confirm-text">{{ message.message }}</div>
          </div>
        </div>
      </template>
    </ConfirmDialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useConfirm }    from 'primevue/useconfirm'
import { useToast }      from 'primevue/usetoast'
import Select        from 'primevue/select'
import Button        from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'
import { useClusterStore } from '@/stores/cluster'
import { nodesApi }        from '@/api/nodes'
import { useNodeOptions }  from '@/composables/useNodeOptions'
import type { FlushOperation } from '@/api/nodes'

const clusterStore = useClusterStore()
const confirm      = useConfirm()
const toast        = useToast()

const { nodeOptions } = useNodeOptions()

const selectedNodeId = ref<number | null>(null)
const selectedOp     = ref<FlushOperation>('logs')
const loading        = ref(false)

const OPERATIONS: {
  value: FlushOperation
  label: string
  sql: string
  icon: string
  desc: string
  danger: boolean
}[] = [
  {
    value:  'logs',
    label:  'Flush Logs',
    sql:    'FLUSH LOGS',
    icon:   'pi-sync',
    desc:   'Rotate binary, relay and error log files. Safe to run at any time.',
    danger: false,
  },
  {
    value:  'tables_read_lock',
    label:  'Flush & Lock Tables',
    sql:    'FLUSH TABLES WITH READ LOCK',
    icon:   'pi-lock',
    desc:   'Flush all tables and acquire a global read lock. Blocks all writes until UNLOCK TABLES is called.',
    danger: true,
  },
  {
    value:  'unlock_tables',
    label:  'Unlock Tables',
    sql:    'UNLOCK TABLES',
    icon:   'pi-lock-open',
    desc:   'Release the global read lock acquired by FLUSH TABLES WITH READ LOCK.',
    danger: false,
  },
]

const selectedOpMeta = computed(() => OPERATIONS.find((o) => o.value === selectedOp.value))
const canExecute     = computed(() => !!selectedNodeId.value && !!selectedOp.value)

function handleExecute() {
  const meta     = selectedOpMeta.value!
  const nodeName = nodeOptions.value.find((o) => o.value === selectedNodeId.value)?.label ?? String(selectedNodeId.value)

  if (meta.danger) {
    confirm.require({
      group:       'flush-op',
      header:      `${meta.label}?`,
      message:     `${meta.sql}\non node: ${nodeName}`,
      icon:        'pi pi-exclamation-triangle',
      acceptLabel: meta.label,
      rejectLabel: 'Cancel',
      acceptClass: 'p-button-danger',
      accept:      () => doFlush(nodeName),
    })
  } else {
    doFlush(nodeName)
  }
}

async function doFlush(nodeName: string) {
  if (!clusterStore.selectedClusterId || !selectedNodeId.value) return
  loading.value = true
  try {
    const result = await nodesApi.flush(
      clusterStore.selectedClusterId,
      selectedNodeId.value,
      selectedOp.value,
    )
    toast.add({
      severity: 'success',
      summary:  'Flush executed',
      detail:   `${result.query_executed} on ${nodeName}`,
      life:     5000,
    })
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String(err)
    toast.add({
      severity: 'error',
      summary:  'Flush failed',
      detail:   msg,
      life:     7000,
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.diag-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: 15px;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.panel-head-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-highlight);
  border: 1px solid rgba(45,212,191,0.18);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-size: 0.875rem;
}

.panel-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.panel-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.form-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  max-width: 680px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.field-select {
  width: 100%;
}

/* ---- operation cards grid ---- */
.ops-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}

@media (max-width: 700px) {
  .ops-grid { grid-template-columns: 1fr; }
}

.op-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  background: var(--color-surface-offset);
  transition: border-color var(--transition-interactive), background var(--transition-interactive);
}

.op-card:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-highlight);
}

.op-card--active {
  border-color: var(--color-primary);
  background: var(--color-primary-highlight);
  box-shadow: 0 0 0 2px rgba(45,212,191,0.15);
}

.op-card--danger.op-card--active {
  border-color: var(--color-error);
  background: color-mix(in oklch, var(--color-error) 8%, transparent);
  box-shadow: 0 0 0 2px rgba(248,113,113,0.15);
}

.op-card--danger:hover:not(.op-card--active) {
  border-color: var(--color-error);
  background: color-mix(in oklch, var(--color-error) 5%, transparent);
}

.op-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.op-icon {
  font-size: 0.875rem;
  color: var(--color-primary);
}

.op-card--danger .op-icon {
  color: var(--color-error);
}

.op-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  flex: 1;
}

.op-warn {
  font-size: 0.75rem;
  color: var(--color-warning);
}

.op-sql code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-warning);
  background: var(--color-surface-dynamic);
  padding: 3px var(--space-2);
  border-radius: var(--radius-sm);
}

.op-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* ---- footer ---- */
.form-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
}

/* ---- confirm dialog ---- */
.confirm-body {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-2) 0;
}

.confirm-icon {
  font-size: 1.4rem;
  color: var(--color-warning);
  flex-shrink: 0;
  margin-top: 2px;
}

.confirm-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-1);
}

.confirm-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  white-space: pre-line;
}
</style>
