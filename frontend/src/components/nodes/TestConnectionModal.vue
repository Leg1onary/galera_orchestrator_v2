<!-- src/components/nodes/TestConnectionModal.vue -->
<!-- ТЗ п.11.6: Ping → GET /api/clusters/{id}/nodes/{id}/test-connection -->
<template>
  <Dialog
      v-model:visible="visible"
      :header="`Test connection — ${nodeName}`"
      modal
      :style="{ width: '420px' }"
      @hide="emit('close')"
  >
    <div class="modal-body">

      <p v-if="!result && !loading" class="hint-text">
        Tests SSH and database connectivity to this node.
      </p>

      <div v-if="loading" class="loading-state">
        <i class="pi pi-spin pi-spinner" /> Testing…
      </div>

      <template v-else-if="result">
        <!-- SSH row -->
        <div class="conn-row">
          <div class="conn-label">
            <i class="pi pi-terminal" />
            SSH
          </div>
          <div class="conn-status">
            <i :class="result.ssh_ok ? 'pi pi-check-circle icon--ok' : 'pi pi-times-circle icon--fail'" />
            <span v-if="result.ssh_ok" class="conn-value">
              {{ result.ssh_latency_ms }}ms
            </span>
            <span v-else class="conn-value conn-value--error">
              {{ result.ssh_error ?? 'Failed' }}
            </span>
          </div>
        </div>

        <!-- DB row -->
        <div class="conn-row">
          <div class="conn-label">
            <i class="pi pi-database" />
            Database
          </div>
          <div class="conn-status">
            <i :class="result.db_ok ? 'pi pi-check-circle icon--ok' : 'pi pi-times-circle icon--fail'" />
            <span v-if="result.db_ok" class="conn-value">
              {{ result.db_latency_ms }}ms
            </span>
            <span v-else class="conn-value conn-value--error">
              {{ result.db_error ?? 'Failed' }}
            </span>
          </div>
        </div>
      </template>

    </div>

    <template #footer>
      <Button
          label="Test"
          icon="pi pi-play"
          :loading="loading"
          @click="run"
      />
      <Button label="Close" text @click="emit('close')" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Dialog from 'primevue/dialog'   // BLOCKER fix: именованный импорт PrimeVue 4
import Button from 'primevue/button'
import { nodesApi, type TestConnectionResult } from '@/api/nodes'

const props = defineProps<{
  nodeId: number
  clusterId: number
  nodeName: string
}>()
const emit = defineEmits<{ close: [] }>()

const visible = ref(true)
const loading = ref(false)
const result  = ref<TestConnectionResult | null>(null)

// Авто-запуск при открытии (ТЗ п.11.6: Ping инициируется сразу)
onMounted(run)

async function run() {
  loading.value = true
  result.value  = null
  try {
    result.value = await nodesApi.testConnection(props.clusterId, props.nodeId)
  } catch (err: any) {
    // MINOR fix: если SSH упал — DB N/A, как описано в ТЗ п.15.3
    result.value = {
      ssh_ok:         false,
      ssh_latency_ms: null,
      ssh_error:      err?.response?.data?.detail ?? err.message,
      db_ok:          false,
      db_latency_ms:  null,
      db_error:       'N/A (SSH failed)',
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* BLOCKER fix: убраны text-muted-color, text-success-color → scoped классы */
.hint-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-6) 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.conn-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-offset);
  border-radius: var(--radius-md);
}

.conn-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
}

.conn-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.conn-value {
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
}

.conn-value--error { color: var(--color-error); }

/* BLOCKER fix: убраны Tailwind-классы → scoped */
.icon--ok   { color: var(--color-success); }
.icon--fail { color: var(--color-error); }
</style>