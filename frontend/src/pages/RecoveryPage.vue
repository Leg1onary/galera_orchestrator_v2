<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Recovery</h1>
        <p class="page-subtitle">Инструменты восстановления кластера и нод</p>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(440px,1fr));gap:var(--space-6);margin-bottom:var(--space-8)">

      <!-- Bootstrap Wizard (full width) -->
      <div class="wizard-wrap" style="grid-column:1/-1">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-5);flex-wrap:wrap;gap:var(--space-3)">
          <div>
            <div style="font-size:var(--text-base);font-weight:700;color:var(--text);margin-bottom:4px;display:flex;align-items:center;gap:8px">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              Bootstrap Wizard
            </div>
            <div style="font-size:var(--text-sm);color:var(--text-muted)">Пошаговое восстановление кластера после полного отказа</div>
          </div>
          <div style="display:flex;gap:var(--space-2);align-items:center">
            <button
              v-if="!wizardRunning && !wizardDone"
              class="btn btn-primary"
              :disabled="wizardLoading"
              @click="startWizard"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Запустить Wizard
            </button>
            <button
              v-if="wizardRunning || wizardDone"
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
            v-for="(step, i) in wizardSteps"
            :key="i"
            class="wizard-step"
            :class="{ done: wizardStep > i, active: wizardStep === i }"
          >
            <div class="wizard-step-num">
              <template v-if="wizardStep > i">✓</template>
              <template v-else>{{ i+1 }}</template>
            </div>
            <div class="wizard-step-label">{{ step }}</div>
          </div>
        </div>

        <!-- Wizard body -->
        <div class="wizard-body">
          <div v-if="!wizardRunning && !wizardDone" style="color:var(--text-muted);font-size:var(--text-sm);padding:var(--space-4) 0">
            Нажмите «Запустить Wizard» — пошаговое восстановление с вызовами API
          </div>
          <div v-else-if="wizardLoading" style="font-size:var(--text-sm);color:var(--text-muted);padding:var(--space-4) 0;display:flex;align-items:center;gap:8px">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" opacity=".3"/><path d="M21 12a9 9 0 0 0-9-9"/></svg>
            Выполняется...
          </div>
          <div v-else-if="wizardDone" style="font-size:var(--text-sm);color:var(--text-muted);padding:var(--space-4) 0">
            <strong style="color:var(--success)">✓ Bootstrap завершён</strong>
            <p style="margin-top:var(--space-2)">Кластер восстановлен. Нажмите «Сброс» для повтора.</p>
          </div>
          <div v-else style="font-size:var(--text-sm);color:var(--text-muted);padding:var(--space-4) 0">
            <strong style="color:var(--text)">Шаг {{ wizardStep + 1 }}: {{ wizardSteps[wizardStep] }}</strong>
            <p style="margin-top:var(--space-2)">{{ wizardStepDesc[wizardStep] }}</p>
            <div v-if="wizardCandidateId" style="margin-top:var(--space-2);padding:var(--space-2) var(--space-3);background:var(--surface-2);border-radius:var(--radius-sm);font-family:var(--font-mono);font-size:var(--text-xs)">
              Кандидат: {{ wizardCandidateId }}
            </div>
          </div>
        </div>

        <!-- Wizard log -->
        <div v-if="wizardLog.length" class="wizard-log">
          <div v-for="(entry, i) in wizardLog" :key="i" :class="entry.cls">{{ entry.text }}</div>
        </div>

        <!-- Progress bar -->
        <div v-if="wizardRunning || wizardDone" class="wizard-poll-bar">
          <div class="wizard-poll-fill" :style="`width:${wizardProgress}%`"></div>
        </div>
      </div>

      <!-- Rejoin -->
      <div class="form-section">
        <div class="form-section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--info)" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
          </svg>
          Rejoin ноды в кластер
        </div>
        <p class="text-sm text-muted" style="margin-bottom:var(--space-4)">
          Переподключить упавшую ноду к работающему кластеру. Нода получит SST или IST от донора автоматически.
        </p>
        <div class="form-group">
          <label class="form-label">Нода для Rejoin</label>
          <select class="form-input" v-model="rejoinNode">
            <option value="">— выберите ноду —</option>
            <option v-for="n in cluster.nodes" :key="n.id" :value="n.id">{{ n.name || n.id }} ({{ n.host }})</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Метод синхронизации</label>
          <select class="form-input" v-model="rejoinMethod">
            <option value="auto">Авто (SST если нужно)</option>
            <option value="ist">Только IST</option>
            <option value="sst">Принудительный SST</option>
          </select>
        </div>
        <button
          class="btn btn-primary btn-lg"
          style="width:100%"
          :disabled="!rejoinNode"
          @click="doRejoin"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
          </svg>
          Rejoin Node
        </button>
      </div>

      <!-- SST Donor -->
      <div class="form-section">
        <div class="form-section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.36 12a19.79 19.79 0 0 1-3.07-8.63A2 2 0 0 1 3.27 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
          Принудительный донор SST
        </div>
        <p class="text-sm text-muted" style="margin-bottom:var(--space-4)">
          По умолчанию Galera сам выбирает донора. Укажите ноду явно, чтобы не перегружать основной сервер при SST.
        </p>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              Нода-реципиент
              <br><span style="font-size:var(--text-xs);color:var(--text-muted);font-weight:400">(кто получает данные)</span>
            </label>
            <select class="form-input" v-model="sstRecipient">
              <option value="">— выберите ноду —</option>
              <option v-for="n in cluster.nodes" :key="n.id" :value="n.id">{{ n.name || n.id }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">
              Донор
              <br><span style="font-size:var(--text-xs);color:var(--text-muted);font-weight:400">(кто отдаёт данные)</span>
            </label>
            <select class="form-input" v-model="sstDonor">
              <option value="">— выберите донора —</option>
              <option v-for="n in cluster.nodes" :key="n.id" :value="n.id">{{ n.name || n.id }}</option>
            </select>
          </div>
        </div>
        <button
          class="btn btn-success"
          style="width:100%"
          :disabled="!sstRecipient || !sstDonor"
          @click="setSstDonor"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M5 9l7-7 7 7"/>
            <path d="M12 2v14"/>
          </svg>
          Установить донора (wsrep_sst_donor)
        </button>
      </div>
    </div>

    <!-- Playbooks -->
    <h2 class="card-title" style="font-size:var(--text-lg);margin-bottom:var(--space-5)">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      Playbooks
    </h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:var(--space-4)">
      <div class="card">
        <div class="card-title" style="color:var(--error)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="2" width="20" height="8" rx="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
          </svg>
          Node Down
        </div>
        <ol style="font-size:var(--text-sm);color:var(--text-muted);padding-left:var(--space-5);line-height:2">
          <li>Проверить wsrep_cluster_size на живой ноде</li>
          <li>Если size=1 — кластер non-Primary</li>
          <li>Исправить сеть / поднять сервис</li>
          <li>Нода автоматически сделает IST</li>
          <li>Проверить wsrep_local_state_comment = Synced</li>
        </ol>
      </div>
      <div class="card">
        <div class="card-title" style="color:var(--warning)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94"/>
          </svg>
          Full Cluster Crash
        </div>
        <ol style="font-size:var(--text-sm);color:var(--text-muted);padding-left:var(--space-5);line-height:2">
          <li>Найти ноду с наибольшим <code style="font-family:var(--font-mono)">seqno</code> в grastate.dat</li>
          <li>На ней выполнить <code style="font-family:var(--font-mono)">galera_new_cluster</code></li>
          <li>Запустить <code style="font-family:var(--font-mono)">mariadb.service</code> на остальных нодах</li>
          <li>Дождаться IST/SST синхронизации</li>
        </ol>
      </div>
      <div class="card">
        <div class="card-title" style="color:var(--info)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
          </svg>
          Split-Brain (2 ноды)
        </div>
        <ol style="font-size:var(--text-sm);color:var(--text-muted);padding-left:var(--space-5);line-height:2">
          <li>Оба узла считают себя Primary</li>
          <li>Остановить MariaDB на одной ноде</li>
          <li>Проверить данные — выбрать «правильную» ноду</li>
          <li>Перезапустить отставшую через Rejoin</li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useClusterStore } from '@/stores/cluster.js'
import api from '@/api/index.js'

const cluster       = useClusterStore()
const toast         = useToast()
const rejoinNode    = ref('')
const rejoinMethod  = ref('auto')
const sstRecipient  = ref('')
const sstDonor      = ref('')

// Bootstrap wizard state
const wizardRunning    = ref(false)
const wizardDone       = ref(false)
const wizardLoading    = ref(false)
const wizardStep       = ref(0)
const wizardProgress   = ref(0)
const wizardLog        = ref([])
const wizardCandidateId = ref(null)

const wizardSteps = [
  'Проверка состояния',
  'Wsrep-recover',
  'Выбор кандидата',
  'Bootstrap ноды',
  'Запуск остальных',
  'Ожидание Synced',
  'Готово',
]
const wizardStepDesc = [
  'Проверяем состояние всех нод кластера через SSH и DB.',
  'Запускаем mysqld --wsrep-recover на всех нодах для определения seqno.',
  'Нода с наибольшим seqno станет кандидатом для bootstrap.',
  'Выполняем galera_new_cluster на выбранной ноде.',
  'Запускаем mariadb.service на остальных нодах последовательно.',
  'Ожидаем wsrep_local_state_comment = Synced на всех нодах.',
  'Кластер восстановлен. Все ноды синхронизированы.',
]

function addWizardLog(cls, text) {
  wizardLog.value.push({ cls, text })
}

function _setStep(i) {
  wizardStep.value     = i
  wizardProgress.value = Math.round((i / (wizardSteps.length - 1)) * 100)
}

async function startWizard() {
  wizardRunning.value     = true
  wizardDone.value        = false
  wizardLoading.value     = true
  wizardStep.value        = 0
  wizardProgress.value    = 0
  wizardLog.value         = [{ cls: 'wl-info', text: '[INFO] Bootstrap Wizard запущен' }]
  wizardCandidateId.value = null

  try {
    // Step 1: read seqno from all nodes
    _setStep(0)
    addWizardLog('wl-info', '[1] Чтение grastate.dat на всех нодах...')
    const seqResp = await api.post('/api/seqno', {})
    const seqNodes = seqResp.data?.nodes || []
    seqNodes.forEach(n => {
      const mark = n.reachable ? 'wl-ok' : 'wl-warn'
      addWizardLog(mark, `  ${n.id}: seqno=${n.seqno} safe_to_bootstrap=${n.safe_to_bootstrap} reachable=${n.reachable}`)
    })

    // Step 2: wsrep-recover
    _setStep(1)
    addWizardLog('wl-info', '[2] Запуск wsrep-recover на всех нодах...')
    const recoverResp = await api.post('/api/wsrep-recover-all')
    const recoverNodes = recoverResp.data?.nodes || []
    recoverNodes.forEach(n => {
      addWizardLog(n.ok ? 'wl-ok' : 'wl-warn', `  ${n.node_id}: seqno=${n.seqno}`)
    })

    // Step 3: pick candidate (highest seqno from wsrep-recover, fallback to seqno read)
    _setStep(2)
    let candidateId = null
    let maxSeq = -2
    const allSeqs = recoverNodes.length ? recoverNodes : seqNodes
    for (const n of allSeqs) {
      const s = typeof n.seqno === 'string'
        ? parseInt((n.seqno || '').split(':').pop(), 10)
        : (n.seqno || -1)
      if (s > maxSeq) { maxSeq = s; candidateId = n.node_id || n.id }
    }
    // safe_to_bootstrap=1 overrides seqno choice
    const safeNode = seqNodes.find(n => n.safe_to_bootstrap === 1)
    if (safeNode) candidateId = safeNode.id
    wizardCandidateId.value = candidateId
    addWizardLog('wl-ok', `[3] Кандидат для bootstrap: ${candidateId} (seqno=${maxSeq})`)

    // Steps 4-6: call bootstrap wizard endpoint
    _setStep(3)
    addWizardLog('wl-info', `[4] Запуск galera_new_cluster на ${candidateId}...`)
    const bootResp = await api.post('/api/bootstrap/wizard', { candidate_id: candidateId })
    const steps = bootResp.data?.steps || []
    steps.forEach(s => {
      const cls = s.status === 'ok' || s.status === 'done' ? 'wl-ok'
                : s.status === 'warn' ? 'wl-warn' : 'wl-error'
      addWizardLog(cls, `  [${s.step}] ${s.message}`)
    })
    _setStep(4)
    _setStep(5)

    if (!bootResp.data?.ok) {
      addWizardLog('wl-error', '[ERROR] Bootstrap завершился с ошибкой')
      toast.add({ severity: 'error', summary: 'Bootstrap', detail: 'Bootstrap завершился с ошибкой', life: 6000 })
    } else {
      _setStep(6)
      addWizardLog('wl-ok', '✓ Bootstrap завершён успешно')
      wizardDone.value = true
      toast.add({ severity: 'success', summary: 'Bootstrap', detail: 'Wizard завершён успешно', life: 4000 })
      await cluster.fetchStatus()
    }
  } catch (e) {
    addWizardLog('wl-error', `[ERROR] ${e.message}`)
    toast.add({ severity: 'error', summary: 'Bootstrap Wizard', detail: e.message, life: 6000 })
  } finally {
    wizardLoading.value = false
    wizardRunning.value = !wizardDone.value
  }
}

function resetWizard() {
  wizardRunning.value     = false
  wizardDone.value        = false
  wizardLoading.value     = false
  wizardStep.value        = 0
  wizardProgress.value    = 0
  wizardLog.value         = []
  wizardCandidateId.value = null
}

// FIX: was /api/nodes/{id}/rejoin (404) — correct path is /api/node/{id}/rejoin
async function doRejoin() {
  if (!rejoinNode.value) return
  try {
    const resp = await api.post(`/api/node/${rejoinNode.value}/rejoin`)
    toast.add({ severity: 'success', summary: 'Rejoin', detail: resp.data?.msg || 'Запущен', life: 4000 })
    cluster.addLog('INFO', `Rejoin ${rejoinNode.value} (${rejoinMethod.value})`)
    await cluster.fetchStatus()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка Rejoin', detail: String(e.message), life: 5000 })
  }
}

// FIX: was /api/sst-donor with wrong body — correct is /api/node/{recipient}/sst-donor
async function setSstDonor() {
  if (!sstRecipient.value || !sstDonor.value) return
  try {
    const resp = await api.post(`/api/node/${sstRecipient.value}/sst-donor`, {
      donor_id: sstDonor.value,
    })
    toast.add({ severity: 'success', summary: 'SST Донор', detail: resp.data?.msg || 'Установлен', life: 4000 })
    cluster.addLog('INFO', `SST донор: ${sstDonor.value} → ${sstRecipient.value}`)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: String(e.message), life: 5000 })
  }
}
</script>
