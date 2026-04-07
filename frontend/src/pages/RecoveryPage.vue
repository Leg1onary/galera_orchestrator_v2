<template>
  <div class="page-recovery">
    <Card class="mb-4">
      <template #header><div class="card-title"><i class="pi pi-refresh" />Bootstrap Wizard</div></template>
      <template #content>
        <p class="hint-text mb-3">Автоматически выберет кандидата с максимальным seqno и выполнит восстановление кластера.</p>

        <!-- seqno table -->
        <div v-if="seqnoData" class="seqno-table mb-3">
          <DataTable :value="seqnoData.nodes" size="small">
            <Column field="id" header="Нода" />
            <Column field="seqno" header="seqno" />
            <Column field="safe_to_bootstrap" header="safe_to_bootstrap" />
            <Column field="reachable" header="Доступна">
              <template #body="{ data }">
                <i :class="data.reachable ? 'pi pi-check-circle text-ok' : 'pi pi-times-circle text-error'" />
              </template>
            </Column>
          </DataTable>
        </div>

        <!-- Candidate override -->
        <div class="candidate-row mb-3">
          <label class="field-label">Кандидат (необязательно):</label>
          <Select :options="nodeIds" v-model="candidateId" placeholder="Авто-выбор"
            show-clear style="width:200px" size="small" />
        </div>

        <div class="action-row">
          <Button label="Получить seqno" icon="pi pi-list" outlined size="small"
            @click="getSeqno" :loading="loadingSeqno" />
          <Button label="Запустить Bootstrap" icon="pi pi-play" severity="warning" size="small"
            @click="runBootstrap" :loading="loadingBootstrap" />
        </div>

        <!-- Steps result -->
        <div v-if="bootstrapSteps.length" class="wizard-steps mt-4">
          <div v-for="step in bootstrapSteps" :key="step.step"
            class="wizard-step" :class="stepClass(step.status)">
            <span class="step-num">{{ step.step }}</span>
            <div>
              <div style="font-weight:600;font-size:13px">{{ step.message }}</div>
              <div v-if="step.node" style="font-size:11px;color:var(--color-text-muted)">{{ step.node }}</div>
            </div>
            <i class="pi ml-auto" :class="stepIcon(step.status)" />
          </div>
        </div>
      </template>
    </Card>

    <!-- Reset grastate -->
    <Card>
      <template #header><div class="card-title"><i class="pi pi-exclamation-triangle" />Сброс grastate</div></template>
      <template #content>
        <p class="hint-text mb-3">Сбросить safe_to_bootstrap=1 на выбранной ноде (граvsstate.dat).</p>
        <div class="action-row">
          <Select :options="nodeIds" v-model="resetNode" placeholder="Выберите ноду" style="width:200px" size="small" />
          <Button label="Reset grastate" icon="pi pi-undo" outlined severity="danger" size="small"
            @click="resetGrastate" :loading="loadingReset" :disabled="!resetNode" />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Select from 'primevue/select'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import api from '@/api'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()
const toast = useToast()

const seqnoData = ref(null)
const candidateId = ref(null)
const resetNode = ref(null)
const bootstrapSteps = ref([])
const loadingSeqno = ref(false)
const loadingBootstrap = ref(false)
const loadingReset = ref(false)

const nodeIds = computed(() => cluster.nodes.map(n => n.id))

async function getSeqno() {
  loadingSeqno.value = true
  try {
    const { data } = await api.post('/api/seqno')
    seqnoData.value = data
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || e.message, life: 4000 })
  } finally { loadingSeqno.value = false }
}

async function runBootstrap() {
  loadingBootstrap.value = true
  bootstrapSteps.value = []
  try {
    const payload = candidateId.value ? { candidate_id: candidateId.value } : {}
    const { data } = await api.post('/api/bootstrap/wizard', payload)
    bootstrapSteps.value = data.steps || []
    toast.add({ severity: data.ok ? 'success' : 'error', summary: 'Bootstrap', detail: `Кандидат: ${data.candidate_id}`, life: 4000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || e.message, life: 4000 })
  } finally { loadingBootstrap.value = false }
}

async function resetGrastate() {
  if (!resetNode.value) return
  loadingReset.value = true
  try {
    const { data } = await api.post(`/api/node/${resetNode.value}/reset-grastate`)
    toast.add({ severity: data.ok ? 'success' : 'error', summary: 'Reset grastate', detail: `${resetNode.value}: OK`, life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || e.message, life: 4000 })
  } finally { loadingReset.value = false }
}

function stepClass(status) {
  if (status === 'ok') return 'step-ok'
  if (status === 'error') return 'step-error'
  if (status === 'running') return 'step-active'
  return ''
}
function stepIcon(status) {
  if (status === 'ok') return 'pi-check-circle text-ok'
  if (status === 'error') return 'pi-times-circle text-error'
  return 'pi-spin pi-spinner'
}
</script>

<style scoped>
.page-recovery { display: flex; flex-direction: column; gap: 1rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-4 { margin-top: 1.25rem; }
.card-title { display: flex; align-items: center; gap: 0.5rem; font-size: 14px; font-weight: 600; padding: 0.875rem 1.25rem; }
.hint-text { font-size: 13px; color: var(--color-text-secondary); }
.candidate-row, .action-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.field-label { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); }
.text-ok    { color: var(--color-status-ok); }
.text-error { color: var(--color-status-error); }
.ml-auto { margin-left: auto; }
.seqno-table { border: 1px solid var(--color-border); border-radius: var(--radius-sm); overflow: hidden; }
</style>
