<template>
  <Dialog
      v-model:visible="visible"
      :header="`Test connection — ${nodeName}`"
      modal
      :style="{ width: '420px' }"
      @hide="emit('close')"
  >
    <div class="space-y-4">
      <div v-if="!result && !loading" class="text-sm text-muted-color">
        Tests SSH and database connectivity to this node.
      </div>

      <div v-if="loading" class="py-6 text-center text-muted-color text-sm">
        <i class="pi pi-spin pi-spinner mr-2" /> Testing…
      </div>

      <template v-else-if="result">
        <!-- SSH row -->
        <div class="conn-row">
          <div class="conn-label">
            <i class="pi pi-terminal" />
            SSH
          </div>
          <div class="conn-status">
            <i
                :class="result.ssh_ok ? 'pi pi-check-circle text-success-color' : 'pi pi-times-circle text-error'"
            />
            <span v-if="result.ssh_ok" class="text-sm">
              {{ result.ssh_latency_ms }}ms
            </span>
            <span v-else class="text-sm text-error">
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
            <i
                :class="result.db_ok ? 'pi pi-check-circle text-success-color' : 'pi pi-times-circle text-error'"
            />
            <span v-if="result.db_ok" class="text-sm">
              {{ result.db_latency_ms }}ms
            </span>
            <span v-else class="text-sm text-error">
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
import { Dialog, Button } from 'primevue'
import { nodesApi, type TestConnectionResult } from '@/api/nodes'

const props = defineProps<{
  nodeId: number
  clusterId: number
  nodeName: string
}>()
const emit = defineEmits<{ close: [] }>()

const visible = ref(true)
const loading = ref(false)
const result = ref<TestConnectionResult | null>(null)

// Авто-запуск при открытии
onMounted(run)

async function run() {
  loading.value = true
  result.value = null
  try {
    result.value = await nodesApi.testConnection(props.clusterId, props.nodeId)
  } catch (err: any) {
    result.value = {
      ssh_ok: false,
      ssh_latency_ms: null,
      ssh_error: err?.response?.data?.detail ?? err.message,
      db_ok: false,
      db_latency_ms: null,
      db_error: null,
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.conn-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 0.75rem;
  background: var(--color-surface-offset);
  border-radius: var(--radius-md);
}
.conn-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
}
.conn-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.text-error { color: var(--color-error); }
.text-success-color { color: var(--color-success); }
</style>