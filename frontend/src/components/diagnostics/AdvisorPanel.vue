<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { advisorApi, type AdvisorCard, type AdvisorSeverity, type AdvisorCategory } from '@/api/advisor'
import PanelToolbar from './PanelToolbar.vue'
import { useRouter } from 'vue-router'

const props = defineProps<{ active: boolean }>()

const clusterStore = useClusterStore()
const router = useRouter()

const loading   = ref(false)
const error     = ref<string | null>(null)
const response  = ref<{ generated_at: string; advisors: AdvisorCard[] } | null>(null)
const fetched   = ref(false)

// ── Filters ──────────────────────────────────────────────────────────────────
const filterSeverity = ref<AdvisorSeverity | 'all'>('all')
const filterCategory = ref<AdvisorCategory | 'all'>('all')

// ── Meta ─────────────────────────────────────────────────────────────────────
const SEV_META: Record<AdvisorSeverity, { label: string; icon: string; cls: string; order: number }> = {
  critical: { label: 'Critical', icon: 'pi-times-circle',       cls: 'sev-critical', order: 0 },
  warn:     { label: 'Warning',  icon: 'pi-exclamation-circle', cls: 'sev-warn',     order: 1 },
  info:     { label: 'Info',     icon: 'pi-info-circle',        cls: 'sev-info',     order: 2 },
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

// ── Computed ──────────────────────────────────────────────────────────────────
const allAdvisors = computed(() => response.value?.advisors ?? [])

const availableCategories = computed(() => {
  const cats = new Set(allAdvisors.value.map((a) => a.category))
  return Array.from(cats)
})

const filtered = computed(() => {
  return allAdvisors.value
    .filter((a) => filterSeverity.value === 'all' || a.severity === filterSeverity.value)
    .filter((a) => filterCategory.value === 'all' || a.category === filterCategory.value)
})

const grouped = computed(() => {
  const groups: Record<AdvisorSeverity, AdvisorCard[]> = { critical: [], warn: [], info: [] }
  for (const card of filtered.value) {
    groups[card.severity].push(card)
  }
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

watch(() => props.active, (val) => { if (val && !fetched.value) load() })
watch(() => clusterStore.selectedClusterId, () => {
  fetched.value  = false
  response.value = null
  filterSeverity.value = 'all'
  filterCategory.value = 'all'
})

// ── Action handler ────────────────────────────────────────────────────────────
function handleAction(card: AdvisorCard) {
  const action = card.recommended_action
  if (!action) return
  const hint = action.ui_hint ?? ''
  // "open-diagnostics-tab:config-health" → navigate + set tab via query
  if (hint.startsWith('open-diagnostics-tab:')) {
    const tab = hint.replace('open-diagnostics-tab:', '')
    router.push({ path: '/diagnostics', query: { tab } })
  }
}

function hasAction(card: AdvisorCard) {
  const t = card.recommended_action?.action_type
  return t && t !== 'none' && t !== 'config_change'
}

function generatedAt(iso: string) {
  try { return new Date(iso).toLocaleString() } catch { return iso }
}
</script>

<template>
  <div class="advisor-panel">
    <PanelToolbar
      title="Advisor"
      description="Автоматический анализ кластера: конфигурация, репликация, транзакции, диск."
      icon="pi-lightbulb"
      :loading="loading"
      @refresh="load"
    />

    <!-- Error -->
    <div v-if="error" class="panel-error">
      <i class="pi pi-exclamation-triangle" />
      <span>{{ error }}</span>
    </div>

    <!-- Idle -->
    <div v-else-if="!fetched && !loading" class="panel-idle">
      <i class="pi pi-lightbulb" />
      <span>Нажми «Refresh» для запуска анализа</span>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="panel-loading">
      <i class="pi pi-spin pi-spinner" />
      <span>Анализируем кластер…</span>
    </div>

    <template v-else>
      <!-- Summary bar -->
      <div class="summary-bar">
        <div class="summary-counts">
          <span
            v-for="sev in (['critical','warn','info'] as AdvisorSeverity[])"
            :key="sev"
            :class="['count-chip', SEV_META[sev].cls, counts[sev] === 0 ? 'count-zero' : '']"
          >
            <i :class="['pi', SEV_META[sev].icon]" />
            {{ counts[sev] }} {{ SEV_META[sev].label }}
          </span>
        </div>
        <span v-if="response?.generated_at" class="gen-at">
          Обновлено: {{ generatedAt(response.generated_at) }}
        </span>
      </div>

      <!-- Filters -->
      <div class="filters-row">
        <div class="filter-group">
          <span class="filter-label">Severity:</span>
          <button
            v-for="opt in ['all', 'critical', 'warn', 'info']"
            :key="opt"
            :class="['filter-btn', filterSeverity === opt ? 'active' : '']"
            @click="filterSeverity = opt as any"
          >
            {{ opt === 'all' ? 'All' : SEV_META[opt as AdvisorSeverity].label }}
          </button>
        </div>
        <div v-if="availableCategories.length > 1" class="filter-group">
          <span class="filter-label">Category:</span>
          <button
            :class="['filter-btn', filterCategory === 'all' ? 'active' : '']"
            @click="filterCategory = 'all'"
          >All</button>
          <button
            v-for="cat in availableCategories"
            :key="cat"
            :class="['filter-btn', filterCategory === cat ? 'active' : '']"
            @click="filterCategory = cat as any"
          >
            {{ CAT_LABELS[cat] ?? cat }}
          </button>
        </div>
      </div>

      <!-- All good state -->
      <div v-if="allAdvisors.length === 0" class="all-good">
        <div class="all-good-icon"><i class="pi pi-check-circle" /></div>
        <div class="all-good-title">Всё в порядке</div>
        <div class="all-good-sub">Advisor не обнаружил проблем в текущем состоянии кластера.</div>
      </div>

      <!-- Filtered empty -->
      <div v-else-if="filtered.length === 0" class="all-good">
        <div class="all-good-icon"><i class="pi pi-filter-slash" /></div>
        <div class="all-good-title">Нет совпадений</div>
        <div class="all-good-sub">Попробуй изменить фильтры.</div>
      </div>

      <!-- Grouped cards -->
      <template v-else>
        <div v-for="group in grouped" :key="group.severity" class="sev-group">
          <div :class="['group-header', SEV_META[group.severity].cls]">
            <i :class="['pi', SEV_META[group.severity].icon]" />
            <span>{{ SEV_META[group.severity].label }}</span>
            <span class="group-count">{{ group.cards.length }}</span>
          </div>

          <div class="cards-list">
            <div v-for="card in group.cards" :key="card.id" :class="['advisor-card', SEV_META[card.severity].cls]">
              <div class="card-top">
                <div class="card-meta">
                  <span class="cat-badge">{{ CAT_LABELS[card.category] ?? card.category }}</span>
                  <span class="source-badge">{{ card.source }}</span>
                </div>
                <button
                  v-if="hasAction(card)"
                  class="action-btn"
                  @click="handleAction(card)"
                >
                  <i class="pi pi-arrow-right" />
                  Открыть панель
                </button>
              </div>

              <div class="card-title">{{ card.title }}</div>
              <div class="card-summary">{{ card.summary }}</div>

              <details v-if="card.details" class="card-details">
                <summary>Подробнее</summary>
                <div class="card-details-body">{{ card.details }}</div>
              </details>

              <div v-if="card.recommended_action?.description" class="card-rec">
                <i class="pi pi-info-circle" />
                <span>{{ card.recommended_action.description }}</span>
              </div>

              <div v-if="card.evidence?.node_ids?.length" class="card-evidence">
                <span class="ev-label">Ноды:</span>
                <span v-for="nid in card.evidence.node_ids" :key="nid" class="ev-node">{{ nid }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.advisor-panel { display: flex; flex-direction: column; gap: var(--space-5); }

.panel-error,
.panel-idle,
.panel-loading {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-6) var(--space-4);
  color: var(--color-text-muted); font-size: var(--text-sm);
}
.panel-error { color: var(--color-error); }

/* ── Summary bar ── */
.summary-bar {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.summary-counts { display: flex; gap: var(--space-2); flex-wrap: wrap; }
.count-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: var(--radius-full);
  font-size: var(--text-xs); font-weight: 600;
}
.count-zero { opacity: 0.4; }
.gen-at { font-size: var(--text-xs); color: var(--color-text-muted); }

/* ── Filters ── */
.filters-row { display: flex; gap: var(--space-5); flex-wrap: wrap; }
.filter-group { display: flex; align-items: center; gap: var(--space-1); flex-wrap: wrap; }
.filter-label { font-size: var(--text-xs); color: var(--color-text-muted); margin-right: var(--space-1); }
.filter-btn {
  font-size: var(--text-xs); padding: 3px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-interactive);
}
.filter-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }
.filter-btn.active {
  background: var(--color-primary-highlight);
  border-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

/* ── All good ── */
.all-good {
  display: flex; flex-direction: column; align-items: center; text-align: center;
  padding: var(--space-12) var(--space-8); gap: var(--space-3);
}
.all-good-icon {
  width: 52px; height: 52px; border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
  background: var(--color-success-highlight);
  color: var(--color-success); font-size: 1.4rem;
}
.all-good-title { font-size: var(--text-lg); font-weight: 700; color: var(--color-text); }
.all-good-sub { font-size: var(--text-sm); color: var(--color-text-muted); max-width: 40ch; }

/* ── Groups ── */
.sev-group { display: flex; flex-direction: column; gap: 0; }
.group-header {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs); font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  border: 1px solid var(--color-border); border-bottom: none;
}
.group-count {
  margin-left: auto;
  background: oklch(from var(--color-border) l c h / 0.5);
  padding: 1px 7px; border-radius: var(--radius-full);
  font-size: var(--text-xs);
}

/* ── Cards ── */
.cards-list {
  display: flex; flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--space-4);
}

.advisor-card {
  padding: var(--space-4);
  border-bottom: 1px solid oklch(from var(--color-border) l c h / 0.6);
  background: var(--color-surface);
  display: flex; flex-direction: column; gap: var(--space-2);
  transition: background var(--transition-interactive);
}
.advisor-card:last-child { border-bottom: none; }
.advisor-card:hover { background: var(--color-surface-2); }

/* Severity left accent */
.advisor-card.sev-critical { border-left: 3px solid var(--color-error); }
.advisor-card.sev-warn     { border-left: 3px solid var(--color-warning); }
.advisor-card.sev-info     { border-left: 3px solid var(--color-blue); }

.card-top {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-3);
}
.card-meta { display: flex; align-items: center; gap: var(--space-2); }
.cat-badge {
  font-size: var(--text-xs); padding: 2px 8px;
  border-radius: var(--radius-full);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted); font-weight: 500;
}
.source-badge {
  font-size: var(--text-xs); color: var(--color-text-faint);
  font-family: monospace;
}

.card-title { font-size: var(--text-sm); font-weight: 700; color: var(--color-text); line-height: 1.3; }
.card-summary { font-size: var(--text-sm); color: var(--color-text-muted); }

.card-details { margin-top: var(--space-1); }
.card-details summary {
  font-size: var(--text-xs); color: var(--color-primary); cursor: pointer;
  user-select: none;
}
.card-details-body {
  margin-top: var(--space-2);
  font-size: var(--text-xs); color: var(--color-text-muted);
  line-height: 1.6; white-space: pre-wrap;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-offset);
  border-radius: var(--radius-sm);
}

.card-rec {
  display: flex; align-items: flex-start; gap: var(--space-2);
  font-size: var(--text-xs); color: var(--color-text-muted);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-offset);
  border-radius: var(--radius-sm);
}
.card-rec .pi { color: var(--color-blue); flex-shrink: 0; margin-top: 2px; }

.card-evidence {
  display: flex; align-items: center; gap: var(--space-2);
  font-size: var(--text-xs);
}
.ev-label { color: var(--color-text-faint); }
.ev-node {
  padding: 1px 7px; border-radius: var(--radius-full);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  font-family: monospace; color: var(--color-text-muted);
}

.action-btn {
  display: inline-flex; align-items: center; gap: var(--space-2);
  font-size: var(--text-xs); font-weight: 600;
  padding: 4px 12px; border-radius: var(--radius-full);
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-highlight);
  cursor: pointer;
  transition: all var(--transition-interactive);
  flex-shrink: 0;
}
.action-btn:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

/* ── Severity color tokens (reuse from ConfigHealthPanel pattern) ── */
.sev-critical { color: var(--color-error);   background: var(--color-error-highlight); }
.sev-warn     { color: var(--color-warning); background: var(--color-warning-highlight); }
.sev-info     { color: var(--color-blue);    background: var(--color-blue-highlight); }

.group-header.sev-critical { color: var(--color-error);   background: color-mix(in oklch, var(--color-error-highlight) 60%, var(--color-surface-offset)); }
.group-header.sev-warn     { color: var(--color-warning); background: color-mix(in oklch, var(--color-warning-highlight) 60%, var(--color-surface-offset)); }
.group-header.sev-info     { color: var(--color-blue);    background: color-mix(in oklch, var(--color-blue-highlight) 60%, var(--color-surface-offset)); }
</style>
