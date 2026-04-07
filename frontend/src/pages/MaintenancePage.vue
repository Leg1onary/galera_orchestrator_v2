<template>
  <div class="page-maintenance">
    <!-- Maintenance Wizard -->
    <Card class="mb-4">
      <template #header><div class="card-title"><i class="pi pi-wrench" />Maintenance Wizard</div></template>
      <template #content>
        <p class="hint-text mb-3">7-шаговый процесс безопасного обслуживания ноды без простоя кластера.</p>

        <div class="wizard-setup mb-3">
          <label class="field-label">Нода для обслуживания:</label>
          <Select :options="nodeIds" v-model="targetNode" placeholder="Выберите ноду"
            style="width:200px" size="small" :disabled="running" />
          <Button :label="running ? 'Остановить' : 'Запустить'"
            :icon="running ? 'pi pi-stop' : 'pi pi-play'"
            :severity="running ? 'danger' : 'success'" size="small"
            @click="running ? stopWizard() : startWizard()"
            :disabled="!targetNode" />
        </div>

        <div class="wizard-steps">
          <div v-for="(step, idx) in steps" :key="idx"
            class="wizard-step" :class="stepClass(idx)">
            <span class="step-num">{{ idx + 1 }}</span>
            <div class="step-body">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-desc">{{ step.desc }}</div>
              <div v-if="currentStep === idx && step.needConfirm && !stepConfirmed" class="mt-2">
                <Button label="Работы выполнены — продолжить"
                  icon="pi pi-check" severity="success" size="small"
                  @click="confirmStep" />
              </div>
              <div v-if="stepResults[idx]" class="step-result" :class="stepResults[idx].ok ? 'result-ok' : 'result-error'">
                {{ stepResults[idx].msg }}
              </div>
            </div>
            <i class="pi ml-auto" :class="stepIcon(idx)" />
          </div>
        </div>
      </template>
    </Card>

    <!-- SST Monitor -->
    <Card>
      <template #header><div class="card-title"><i class="pi pi-chart-bar" />SST Progress Monitor</div></template>
      <template #content>
        <div class="sst-toolbar mb-3">
          <Select :options="nodeIds" v-model="sstNode" placeholder="Нода" style="width:180px" size="small" />
          <Button label="Старт мониторинга" icon="pi pi-play" outlined size="small"
            @click="startSST" :disabled="!sstNode || sstRunning" />
          <Button label="Стоп" icon="pi pi-stop" outlined size="small" severity="danger"
            @click="stopSST" :disabled="!sstRunning" />
        </div>
        <div v-if="sstStatus" class="sst-info">
          <div class="sst-row"><span>Прогресс:</span><ProgressBar :value="sstStatus.progress || 0" /></div>
          <div class="sst-row"><span>Скорость:</span><span class="mono">{{ sstStatus.speed || '—' }}</span></div>
          <div class="sst-row"><span>Статус:</span><span>{{ sstStatus.state || '—' }}</span></div>
        </div>
        <div v-else-if="sstRunning" class="hint-text">Опрос… ожидание данных</div>
        <div v-else class="hint-text">Выберите ноду и запустите мониторинг</div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useIntervalFn } from '@vueuse/core'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Select from 'primevue/select'
import ProgressBar from 'primevue/progressbar'
import api from '@/api'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()
const toast = useToast()

const targetNode = ref(null)
const nodeIds = computed(() => cluster.nodes.map(n => n.id))

const running = ref(false)
const currentStep = ref(-1)
const stepConfirmed = ref(false)
const stepResults = ref({})
let aborted = false

const steps = [
  { title: '1. R/O ON',   desc: 'SET GLOBAL read_only=1',       action: 'set_read_only',  needConfirm: false },
  { title: '2. Дренаж',   desc: 'Ожидание wsrep_local_recv_queue = 0', action: null,        needConfirm: false },
  { title: '3. Stop',     desc: 'systemctl stop mariadb',        action: 'stop',           needConfirm: false },
  { title: '4. Работы',   desc: 'Ваши работы на ноде',           action: null,             needConfirm: true },
  { title: '5. Start',    desc: 'systemctl start mariadb',       action: 'start',          needConfirm: false },
  { title: '6. Synced',   desc: 'Ожидание wsrep_local_state_comment = Synced', action: null, needConfirm: false },
  { title: '7. R/W ON',   desc: 'SET GLOBAL read_only=0',        action: 'set_read_write', needConfirm: false },
]

function stepClass(idx) {
  if (idx < currentStep.value) return 'step-ok'
  if (idx === currentStep.value) return 'step-active'
  return ''
}
function stepIcon(idx) {
  if (stepResults.value[idx]?.ok === false) return 'pi-times-circle text-error'
  if (idx < currentStep.value || stepResults.value[idx]?.ok) return 'pi-check-circle text-ok'
  if (idx === currentStep.value && running.value) return 'pi-spin pi-spinner'
  return ''
}

async function startWizard() {
  if (!targetNode.value) return
  running.value = true
  aborted = false
  currentStep.value = 0
  stepResults.value = {}
  stepConfirmed.value = false

  for (let i = 0; i < steps.length; i++) {
    if (aborted) break
    currentStep.value = i
    const step = steps[i]

    if (step.action) {
      try {
        const { data } = await api.post(`/api/node/${targetNode.value}/action`, { action: step.action })
        stepResults.value[i] = { ok: true, msg: data.msg || 'OK' }
      } catch (e) {
        stepResults.value[i] = { ok: false, msg: e.response?.data?.detail || e.message }
        toast.add({ severity: 'error', summary: `Шаг ${i+1} ошибка`, detail: stepResults.value[i].msg, life: 5000 })
        break
      }
    } else if (step.needConfirm) {
      // Wait for user confirmation
      await waitForConfirm()
      if (aborted) break
      stepResults.value[i] = { ok: true, msg: 'Подтверждено' }
    } else {
      // Polling step
      await pollStep(i, step.title)
      if (aborted) break
    }

    await new Promise(r => setTimeout(r, 500))
  }

  if (!aborted) {
    currentStep.value = steps.length
    toast.add({ severity: 'success', summary: 'Maintenance завершён', life: 3000 })
  }
  running.value = false
}

function waitForConfirm() {
  stepConfirmed.value = false
  return new Promise(resolve => {
    const interval = setInterval(() => {
      if (stepConfirmed.value || aborted) { clearInterval(interval); resolve() }
    }, 300)
  })
}

async function pollStep(idx, title) {
  for (let attempts = 0; attempts < 60; attempts++) {
    if (aborted) return
    await new Promise(r => setTimeout(r, 3000))
    await cluster.fetchStatus()
    // Step 2: drain, Step 6: wait synced
    if (idx === 1) {
      const node = cluster.nodes.find(n => n.id === targetNode.value)
      if (node && parseInt(node.wsrep_local_recv_queue) === 0) {
        stepResults.value[idx] = { ok: true, msg: 'recv_queue = 0' }; return
      }
    }
    if (idx === 5) {
      const node = cluster.nodes.find(n => n.id === targetNode.value)
      if (node?.wsrep_local_state_comment === 'Synced') {
        stepResults.value[idx] = { ok: true, msg: 'Synced' }; return
      }
    }
  }
  stepResults.value[idx] = { ok: true, msg: 'timeout — continue' }
}

function confirmStep() { stepConfirmed.value = true }
function stopWizard() { aborted = true; running.value = false }

// SST monitor — useIntervalFn заменяет ручной setInterval
const sstNode = ref(null)
const sstRunning = ref(false)
const sstStatus = ref(null)

const { pause: pauseSST, resume: resumeSST } = useIntervalFn(async () => {
  if (!sstNode.value) return
  try {
    const { data } = await api.get(`/api/node/${sstNode.value}/sst-status`)
    sstStatus.value = data
  } catch {}
}, 3000, { immediate: false })

function startSST() {
  if (!sstNode.value) return
  sstRunning.value = true
  resumeSST()
}

function stopSST() {
  sstRunning.value = false
  pauseSST()
}
</script>

<style scoped>
.page-maintenance { display: flex; flex-direction: column; gap: 1rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-2 { margin-top: 0.5rem; }
.card-title { display: flex; align-items: center; gap: 0.5rem; font-size: 14px; font-weight: 600; padding: 0.875rem 1.25rem; }
.hint-text { font-size: 13px; color: var(--color-text-secondary); }
.wizard-setup { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.field-label { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); }
.step-body { flex: 1; min-width: 0; }
.step-title { font-weight: 600; font-size: 13px; }
.step-desc  { font-size: 12px; color: var(--color-text-muted); }
.step-result { font-size: 12px; margin-top: 4px; }
.result-ok    { color: var(--color-status-ok); }
.result-error { color: var(--color-status-error); }
.ml-auto { margin-left: auto; }
.text-ok    { color: var(--color-status-ok); }
.text-error { color: var(--color-status-error); }
.sst-toolbar { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.sst-info { display: flex; flex-direction: column; gap: 0.5rem; }
.sst-row { display: flex; align-items: center; gap: 0.75rem; font-size: 13px; }
.sst-row > span:first-child { color: var(--color-text-muted); min-width: 80px; }
.mono { font-family: var(--font-mono); }
</style>
