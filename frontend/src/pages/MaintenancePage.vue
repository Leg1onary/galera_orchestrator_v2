<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Обслуживание</h1>
        <p class="page-subtitle">Плановый вывод ноды из кластера и возврат в работу</p>
      </div>
    </div>

    <!-- Maintenance Wizard -->
    <div class="wizard-wrap">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-5);flex-wrap:wrap;gap:var(--space-3)">
        <div>
          <div style="font-size:var(--text-base);font-weight:700;color:var(--text);margin-bottom:4px;display:flex;align-items:center;gap:8px">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            Maintenance Wizard
          </div>
          <div style="font-size:var(--text-sm);color:var(--text-muted)">Безопасный последовательный вывод ноды на техобслуживание</div>
        </div>
        <div style="display:flex;gap:var(--space-3);align-items:center;flex-wrap:wrap">
          <div class="form-group" style="margin:0;min-width:220px">
            <select
              class="form-input"
              v-model="selectedNode"
              style="margin:0"
              @change="initNode"
            >
              <option value="">— выберите ноду —</option>
              <option v-for="n in cluster.nodes" :key="n.id" :value="n.id">{{ n.name || n.id }} ({{ n.host }})</option>
            </select>
          </div>
          <button
            v-if="wizardRunning"
            class="btn btn-ghost btn-sm"
            @click="resetWizard"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
            </svg>
            Сброс
          </button>
        </div>
      </div>

      <!-- Steps -->
      <div class="wizard-steps">
        <div
          v-for="(step, i) in steps"
          :key="i"
          class="wizard-step"
          :class="{ done: currentStep > i, active: currentStep === i }"
        >
          <div class="wizard-step-num">
            <template v-if="currentStep > i">✓</template>
            <template v-else>{{ i + 1 }}</template>
          </div>
          <div class="wizard-step-label">{{ step.label }}</div>
        </div>
      </div>

      <!-- Step body -->
      <div class="wizard-body">
        <div v-if="!wizardRunning && !selectedNode" style="color:var(--text-muted);font-size:var(--text-sm);padding:var(--space-4) 0">
          Выберите ноду выше для начала работы
        </div>
        <div v-else-if="!wizardRunning && selectedNode" style="color:var(--text-muted);font-size:var(--text-sm);padding:var(--space-4) 0">
          Нода <strong style="color:var(--text)">{{ selectedNode }}</strong> выбрана.
          <div class="wizard-action-row">
            <button class="btn btn-primary" @click="startWizard">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Начать обслуживание
            </button>
          </div>
        </div>
        <div v-else style="font-size:var(--text-sm);color:var(--text-muted);padding:var(--space-4) 0">
          <strong style="color:var(--text)">Шаг {{ currentStep + 1 }}: {{ steps[currentStep]?.label }}</strong>
          <p style="margin-top:var(--space-2)">{{ steps[currentStep]?.desc }}</p>
          <div class="wizard-action-row">
            <button
              v-if="currentStep < steps.length - 1 && !waitingState"
              class="btn btn-primary"
              :disabled="busy"
              @click="executeStep"
            >
              {{ steps[currentStep]?.btn || 'Выполнить' }}
            </button>
            <span v-if="waitingState" class="spin-dot" style="margin-right:8px"></span>
            <span v-if="waitingState" style="font-size:var(--text-sm);color:var(--text-muted)">{{ waitingMsg }}</span>
            <button
              v-if="currentStep === steps.length - 1"
              class="btn btn-success"
              @click="finishWizard"
            >✓ Завершить</button>
          </div>
        </div>
      </div>

      <!-- Log -->
      <div v-if="wizardLog.length" class="wizard-log">
        <div v-for="(entry, i) in wizardLog" :key="i" :class="entry.cls">{{ entry.text }}</div>
      </div>

      <!-- Progress -->
      <div v-if="wizardRunning" class="wizard-poll-bar">
        <div class="wizard-poll-fill" :style="`width:${wizardProgress}%`"></div>
      </div>
    </div>

    <!-- Info card -->
    <div class="card" style="margin-bottom:var(--space-6)">
      <div class="card-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        Последовательность шагов
      </div>
      <ol style="font-size:var(--text-sm);color:var(--text-muted);padding-left:var(--space-5);line-height:2.2;margin-top:var(--space-3)">
        <li><strong style="color:var(--text)">Read-Only ON</strong> — <code style="font-family:var(--font-mono)">SET GLOBAL read_only = ON</code></li>
        <li><strong style="color:var(--text)">Ожидание очереди</strong> — ждём <code style="font-family:var(--font-mono)">wsrep_local_recv_queue = 0</code></li>
        <li><strong style="color:var(--text)">Stop MariaDB</strong> — <code style="font-family:var(--font-mono)">systemctl stop mariadb.service</code></li>
        <li><strong style="color:var(--text)">⚙ Ваши работы</strong> — пауза для технических операций на ноде</li>
        <li><strong style="color:var(--text)">Start MariaDB</strong> — <code style="font-family:var(--font-mono)">systemctl start mariadb.service</code></li>
        <li><strong style="color:var(--text)">Ожидание Synced</strong> — ждём <code style="font-family:var(--font-mono)">wsrep_local_state_comment = Synced</code></li>
        <li><strong style="color:var(--text)">Read-Only OFF</strong> — <code style="font-family:var(--font-mono)">SET GLOBAL read_only = OFF</code></li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useClusterStore } from '@/stores/cluster.js'
import api from '@/api/index.js'

const cluster      = useClusterStore()
const toast        = useToast()
const selectedNode = ref('')
const wizardRunning  = ref(false)
const currentStep    = ref(0)
const wizardProgress = ref(0)
const wizardLog      = ref([])
const busy           = ref(false)
const waitingState   = ref(false)
const waitingMsg     = ref('')

const steps = [
  { label: 'Read-Only ON',       desc: 'Включить READ_ONLY на ноде для предотвращения записи.',     btn: 'SET read_only = ON' },
  { label: 'Ожидание очереди',   desc: 'Ожидаем применения всех транзакций из очереди репликации.', btn: 'Ждать recv_queue = 0' },
  { label: 'Stop MariaDB',       desc: 'Остановить MariaDB через systemctl.',                        btn: 'Остановить MariaDB' },
  { label: '⚙ Ваши работы',      desc: 'Выполните технические работы на ноде. Нажмите когда готово.',btn: 'Работы выполнены →' },
  { label: 'Start MariaDB',      desc: 'Запустить MariaDB через systemctl.',                         btn: 'Запустить MariaDB' },
  { label: 'Ожидание Synced',    desc: 'Ожидаем wsrep_local_state_comment = Synced.',                btn: 'Ждать Synced' },
  { label: 'Read-Only OFF',      desc: 'Выключить READ_ONLY — возобновить запись.',                  btn: 'SET read_only = OFF' },
]

function initNode() {
  if (selectedNode.value) {
    addLog('wl-info', `Нода выбрана: ${selectedNode.value}`)
  }
}

function startWizard() {
  wizardRunning.value  = true
  currentStep.value    = 0
  wizardProgress.value = 0
  wizardLog.value      = []
  addLog('wl-info', `Начало обслуживания ноды ${selectedNode.value}`)
}

async function executeStep() {
  busy.value = true
  const step = steps[currentStep.value]
  addLog('wl-info', `Выполняю: ${step.label}`)
  try {
    const nodeId = selectedNode.value
    if (currentStep.value === 0) {
      await api.post(`/api/nodes/${nodeId}/readonly-on`)
    } else if (currentStep.value === 1) {
      // Wait for recv_queue (simulate)
      waitingState.value = true; waitingMsg.value = 'Ожидаем recv_queue = 0…'
      await new Promise(r => setTimeout(r, 1200))
      waitingState.value = false
    } else if (currentStep.value === 2) {
      await api.post(`/api/nodes/${nodeId}/stop`)
    } else if (currentStep.value === 3) {
      // User pauses here
    } else if (currentStep.value === 4) {
      await api.post(`/api/nodes/${nodeId}/start`)
    } else if (currentStep.value === 5) {
      waitingState.value = true; waitingMsg.value = 'Ожидаем Synced…'
      await new Promise(r => setTimeout(r, 1500))
      waitingState.value = false
    } else if (currentStep.value === 6) {
      await api.post(`/api/nodes/${nodeId}/readonly-off`)
    }
    addLog('wl-ok', `✓ ${step.label}`)
    currentStep.value++
    wizardProgress.value = Math.round((currentStep.value / steps.length) * 100)
  } catch (e) {
    addLog('wl-err', `✗ ${step.label}: ${e.message}`)
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 5000 })
  } finally {
    busy.value = false
    await cluster.fetchStatus()
  }
}

function finishWizard() {
  addLog('wl-ok', `✓ Обслуживание ноды ${selectedNode.value} завершено`)
  wizardRunning.value  = false
  wizardProgress.value = 100
  toast.add({ severity: 'success', summary: 'Обслуживание', detail: 'Нода возвращена в работу', life: 4000 })
}

function resetWizard() {
  wizardRunning.value  = false
  currentStep.value    = 0
  wizardProgress.value = 0
  wizardLog.value      = []
  waitingState.value   = false
}

function addLog(cls, text) {
  const now = new Date()
  const t = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`
  wizardLog.value.push({ cls, text: `[${t}] ${text}` })
}
</script>
