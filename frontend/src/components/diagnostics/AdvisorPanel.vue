<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { advisorApi, type AdvisorCard, type AdvisorSeverity, type AdvisorCategory } from '@/api/advisor'
import PanelToolbar from './PanelToolbar.vue'
import { useRouter } from 'vue-router'

// PrimeVue 4
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Panel from 'primevue/panel'
import SelectButton from 'primevue/selectbutton'
import Message from 'primevue/message'
import Divider from 'primevue/divider'

const props = defineProps<{ active: boolean }>()

const clusterStore = useClusterStore()
const router = useRouter()

const loading   = ref(false)
const error     = ref<string | null>(null)
const response  = ref<{ generated_at: string; advisors: AdvisorCard[] } | null>(null)
const fetched   = ref(false)
const autoRefresh = ref(false)
let autoTimer: ReturnType<typeof setInterval> | null = null

// ── Filters ──────────────────────────────────────────────────────────────────
const filterSeverity = ref<AdvisorSeverity | 'all'>('all')

// ── Meta ─────────────────────────────────────────────────────────────────────
const SEV_META: Record<AdvisorSeverity, {
  label: string; icon: string; tagSeverity: string; order: number
}> = {
  critical: { label: 'Critical', icon: 'pi-times-circle',       tagSeverity: 'danger',   order: 0 },
  warn:     { label: 'Warning',  icon: 'pi-exclamation-circle', tagSeverity: 'warn',     order: 1 },
  info:     { label: 'Info',     icon: 'pi-info-circle',        tagSeverity: 'info',     order: 2 },
}

const CAT_LABELS: Record<string, string> = {
  config:       'Config',
  performance:  'Performance',
  replication:  'Replication',
  availability: 'Availability',
  storage:      'Storage',
  sst:          'SST',
  maintenance:  'Maintenance',
  security:     'Security',
}

const CAT_ICONS: Record<string, string> = {
  config:       'pi-shield',
  performance:  'pi-chart-bar',
  replication:  'pi-sync',
  availability: 'pi-server',
  storage:      'pi-database',
  sst:          'pi-download',
  maintenance:  'pi-wrench',
  security:     'pi-lock',
}

// ── SelectButton options ──────────────────────────────────────────────────────
const sevFilterOptions = computed(() => [
  { label: 'All', value: 'all' },
  ...(['critical', 'warn', 'info'] as AdvisorSeverity[]).map(s => ({
    label: SEV_META[s].label,
    value: s,
  }))
])

// ── Computed ──────────────────────────────────────────────────────────────────
const allAdvisors = computed(() => response.value?.advisors ?? [])

const filtered = computed(() =>
  allAdvisors.value.filter(
    (a) => filterSeverity.value === 'all' || a.severity === filterSeverity.value
  )
)

const grouped = computed(() => {
  const groups: Record<AdvisorSeverity, AdvisorCard[]> = { critical: [], warn: [], info: [] }
  for (const card of filtered.value) groups[card.severity].push(card)
  return (Object.keys(groups) as AdvisorSeverity[])
    .filter((s) => groups[s].length > 0)
    .map((s) => ({ severity: s, cards: groups[s] }))
})

const counts = computed(() => ({
  critical: allAdvisors.value.filter((a) => a.severity === 'critical').length,
  warn:     allAdvisors.value.filter((a) => a.severity === 'warn').length,
  info:     allAdvisors.value.filter((a) => a.severity === 'info').length,
}))

// ── Load ─────────────────────────────────────────────────────────────────────
async function load() {
  const cid = clusterStore.selectedClusterId
  if (!cid) return
  loading.value = true
  error.value   = null
  try {
    const res = await advisorApi.getAdvisor(cid)
    response.value = { generated_at: res.generated_at, advisors: res.advisors }
    fetched.value  = true
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

function toggleAuto(val: boolean) {
  autoRefresh.value = val
  if (val) {
    load()
    autoTimer = setInterval(load, 30_000)
  } else {
    if (autoTimer) { clearInterval(autoTimer); autoTimer = null }
  }
}

watch(() => props.active, (val) => { if (val && !fetched.value) load() })
watch(() => clusterStore.selectedClusterId, () => {
  fetched.value  = false
  response.value = null
  filterSeverity.value = 'all'
})

// ── Action handler ────────────────────────────────────────────────────────────
function handleAction(card: AdvisorCard) {
  const hint = card.recommended_action?.ui_hint ?? ''
  if (hint.startsWith('open-diagnostics-tab:')) {
    router.push({ path: '/diagnostics', query: { tab: hint.replace('open-diagnostics-tab:', '') } })
  }
}

function hasAction(card: AdvisorCard) {
  const t = card.recommended_action?.action_type
  return t && t !== 'none' && t !== 'config_change'
}

function generatedAt(iso: string) {
  try { return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'medium' }) }
  catch { return iso }
}
</script>

<template>
  <div class="advisor-panel">
    <PanelToolbar
      title="Advisor"
      :loading="loading"
      :auto-refresh="autoRefresh"
      :fetched-at="response?.generated_at ? generatedAt(response.generated_at) : null"
      @refresh="load"
      @toggle-auto="toggleAuto"
    />

    <!-- Error -->
    <Message v-if="error" severity="error" :closable="false" class="adv-message">
      <div class="msg-content">
        <i class="pi pi-exclamation-triangle" />
        <span>{{ error }}</span>
      </div>
    </Message>

    <!-- Idle -->
    <div v-else-if="!fetched && !loading" class="state-placeholder">
      <div class="placeholder-icon">
        <i class="pi pi-lightbulb" />
      </div>
      <p class="placeholder-title">Advisor не запущен</p>
      <p class="placeholder-sub">Нажми Refresh для запуска автоматического анализа кластера</p>
      <Button label="Запустить анализ" icon="pi pi-play" @click="load" size="small" />
    </div>

    <!-- Loading -->
    <div v-else-if="loading && !fetched" class="state-placeholder">
      <div class="placeholder-icon loading-icon">
        <i class="pi pi-spin pi-spinner" />
      </div>
      <p class="placeholder-title">Анализируем кластер…</p>
      <p class="placeholder-sub">Проверяем конфигурацию, репликацию, транзакции</p>
    </div>

    <template v-else>
      <!-- ── Summary counts ── -->
      <div class="summary-bar">
        <div class="summary-counts">
          <div
            v-for="sev in (['critical','warn','info'] as AdvisorSeverity[])"
            :key="sev"
            :class="['count-stat', `count-stat--${sev}`, counts[sev] === 0 ? 'count-stat--zero' : '']"
          >
            <i :class="['pi', SEV_META[sev].icon, 'stat-icon']" />
            <span class="stat-num">{{ counts[sev] }}</span>
            <span class="stat-label">{{ SEV_META[sev].label }}</span>
          </div>
        </div>

        <!-- Severity filter via SelectButton -->
        <div class="summary-filter">
          <SelectButton
            v-model="filterSeverity"
            :options="sevFilterOptions"
            option-label="label"
            option-value="value"
            size="small"
            :allow-empty="false"
          />
        </div>
      </div>

      <!-- All good -->
      <div v-if="allAdvisors.length === 0" class="state-placeholder state-placeholder--success">
        <div class="placeholder-icon placeholder-icon--success">
          <i class="pi pi-check-circle" />
        </div>
        <p class="placeholder-title">Всё в порядке 🎉</p>
        <p class="placeholder-sub">Advisor не обнаружил проблем в текущем состоянии кластера.</p>
      </div>

      <!-- Filtered empty -->
      <div v-else-if="filtered.length === 0" class="state-placeholder">
        <div class="placeholder-icon">
          <i class="pi pi-filter-slash" />
        </div>
        <p class="placeholder-title">Нет совпадений</p>
        <p class="placeholder-sub">Попробуй изменить фильтр по severity.</p>
      </div>

      <!-- ── Grouped cards ── -->
      <template v-else>
        <div v-for="group in grouped" :key="group.severity" class="sev-section">

          <!-- Group header row -->
          <div :class="['group-label', `group-label--${group.severity}`]">
            <i :class="['pi', SEV_META[group.severity].icon]" />
            <span>{{ SEV_META[group.severity].label }}</span>
            <Tag
              :value="String(group.cards.length)"
              :severity="SEV_META[group.severity].tagSeverity"
              rounded
              class="group-count-tag"
            />
          </div>

          <!-- Cards -->
          <div class="cards-stack">
            <Panel
              v-for="card in group.cards"
              :key="card.id"
              :toggleable="!!card.details || !!card.recommended_action?.description"
              :collapsed="true"
              :class="['advisor-card-panel', `adv-${card.severity}`]"
            >
              <!-- Panel header slot -->
              <template #header>
                <div class="card-header-inner">
                  <!-- Left: category + source -->
                  <div class="card-header-left">
                    <Tag
                      :value="CAT_LABELS[card.category] ?? card.category"
                      :icon="`pi ${CAT_ICONS[card.category] ?? 'pi-tag'}`"
                      severity="secondary"
                      class="cat-tag"
                    />
                    <span class="source-text">{{ card.source }}</span>
                  </div>
                  <!-- Center: title + summary -->
                  <div class="card-header-body">
                    <span class="card-title">{{ card.title }}</span>
                    <span class="card-summary">{{ card.summary }}</span>
                  </div>
                  <!-- Right: node chips + action btn -->
                  <div class="card-header-right">
                    <div v-if="card.evidence?.node_ids?.length" class="node-chips">
                      <Tag
                        v-for="nid in card.evidence.node_ids"
                        :key="nid"
                        :value="`Node ${nid}`"
                        severity="secondary"
                        rounded
                        class="node-tag"
                      />
                    </div>
                    <Button
                      v-if="hasAction(card)"
                      icon="pi pi-arrow-right"
                      label="Открыть"
                      size="small"
                      text
                      @click.stop="handleAction(card)"
                      class="action-btn"
                    />
                  </div>
                </div>
              </template>

              <!-- Expanded content -->
              <div v-if="card.details || card.recommended_action?.description" class="card-expanded">
                <div v-if="card.details" class="detail-block">
                  <div class="detail-label">
                    <i class="pi pi-align-left" />
                    Подробности
                  </div>
                  <pre class="detail-pre">{{ card.details }}</pre>
                </div>

                <Divider v-if="card.details && card.recommended_action?.description" class="exp-divider" />

                <div v-if="card.recommended_action?.description" class="rec-block">
                  <div class="detail-label">
                    <i class="pi pi-lightbulb" />
                    Рекомендация
                  </div>
                  <p class="rec-text">{{ card.recommended_action.description }}</p>
                </div>
              </div>
            </Panel>
          </div>

        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.advisor-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── Message ── */
.adv-message { width: 100%; }
.msg-content { display: flex; align-items: center; gap: var(--space-2); }

/* ── Placeholder states ── */
.state-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-16) var(--space-8);
  gap: var(--space-3);
}
.placeholder-icon {
  width: 56px; height: 56px;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-offset);
  color: var(--color-text-muted);
  font-size: 1.5rem;
  margin-bottom: var(--space-1);
}
.placeholder-icon--success {
  background: var(--color-success-highlight);
  color: var(--color-success);
}
.loading-icon { color: var(--color-primary); background: var(--color-primary-highlight); }
.placeholder-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}
.placeholder-sub {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  max-width: 44ch;
  margin: 0;
}

/* ── Summary bar ── */
.summary-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.summary-counts {
  display: flex;
  gap: var(--space-4);
}

.count-stat {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-lg);
  border: 1px solid transparent;
}
.count-stat--zero { opacity: 0.35; }

.count-stat--critical {
  background: var(--color-error-highlight);
  border-color: color-mix(in oklch, var(--color-error) 25%, transparent);
  color: var(--color-error);
}
.count-stat--warn {
  background: var(--color-warning-highlight);
  border-color: color-mix(in oklch, var(--color-warning) 25%, transparent);
  color: var(--color-warning);
}
.count-stat--info {
  background: var(--color-blue-highlight);
  border-color: color-mix(in oklch, var(--color-blue) 25%, transparent);
  color: var(--color-blue);
}

.stat-icon { font-size: 0.875rem; }
.stat-num { font-size: var(--text-base); font-weight: 700; font-variant-numeric: tabular-nums; }
.stat-label { font-size: var(--text-xs); font-weight: 500; opacity: 0.85; }

/* ── SelectButton filter ── */
.summary-filter { flex-shrink: 0; }

/* ── Severity section ── */
.sev-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.group-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.group-label--critical { color: var(--color-error); }
.group-label--warn     { color: var(--color-warning); }
.group-label--info     { color: var(--color-blue); }
.group-count-tag { font-size: 11px !important; }

/* ── Cards stack ── */
.cards-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* ── Panel overrides ── */
.advisor-card-panel {
  border-radius: var(--radius-lg) !important;
  overflow: hidden;
}

/* Severity left-bar via box-shadow on root */
.adv-critical :deep(.p-panel) { box-shadow: inset 3px 0 0 var(--color-error); }
.adv-warn     :deep(.p-panel) { box-shadow: inset 3px 0 0 var(--color-warning); }
.adv-info     :deep(.p-panel) { box-shadow: inset 3px 0 0 var(--color-blue); }

:deep(.p-panel-header) {
  padding: var(--space-3) var(--space-4) !important;
  background: var(--color-surface) !important;
}
:deep(.p-panel-content) {
  padding: var(--space-3) var(--space-4) var(--space-4) !important;
  background: var(--color-surface-offset) !important;
}
:deep(.p-panel-toggle-button) {
  width: 28px !important;
  height: 28px !important;
  flex-shrink: 0;
}

/* ── Card header inner layout ── */
.card-header-inner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-width: 0;
  flex: 1;
}

.card-header-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-1);
  flex-shrink: 0;
  min-width: 90px;
}
.cat-tag { font-size: 11px !important; }
.source-text {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-family: monospace;
  white-space: nowrap;
}

.card-header-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}
.card-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-summary {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}
.node-chips {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
}
.node-tag { font-size: 10px !important; }
.action-btn { flex-shrink: 0; }

/* ── Expanded content ── */
.card-expanded {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.exp-divider { margin: var(--space-1) 0 !important; }

.detail-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: var(--space-2);
}
.detail-label .pi { color: var(--color-primary); }

.detail-pre {
  font-size: var(--text-xs);
  font-family: monospace;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  margin: 0;
}
.rec-text {
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: 1.5;
  margin: 0;
}
</style>
