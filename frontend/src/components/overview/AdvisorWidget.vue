<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { useClusterStore } from '@/stores/cluster'
import { advisorApi, type AdvisorSeverity, type AdvisorCard } from '@/api/advisor'

const router       = useRouter()
const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['advisor-widget', clusterId.value]),
  queryFn:  () => advisorApi.getAdvisor(clusterId.value!, 'info'),
  enabled:  computed(() => !!clusterId.value),
  staleTime: 60_000,
  refetchInterval: 120_000,
})

// При смене кластера — сбрасываем кэш
watch(clusterId, () => refetch())

const SEV_ORDER: AdvisorSeverity[] = ['critical', 'warn', 'info']

const SEV_META: Record<AdvisorSeverity, { label: string; icon: string; cls: string }> = {
  critical: { label: 'Critical', icon: 'pi-exclamation-circle', cls: 'sev-critical' },
  warn:     { label: 'Warning',  icon: 'pi-exclamation-triangle', cls: 'sev-warn' },
  info:     { label: 'Info',     icon: 'pi-info-circle',          cls: 'sev-info' },
}

const advisors = computed(() => data.value?.advisors ?? [])

// Счётчики по severity
const counts = computed(() => {
  const map: Record<AdvisorSeverity, number> = { critical: 0, warn: 0, info: 0 }
  for (const a of advisors.value) map[a.severity]++
  return map
})

// Топ-3 карточки: сначала critical, потом warn, потом info
const topCards = computed<AdvisorCard[]>(() => {
  const sorted = [...advisors.value].sort(
    (a, b) => SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity)
  )
  return sorted.slice(0, 3)
})

const hasIssues = computed(() => advisors.value.length > 0)
const totalCount = computed(() => advisors.value.length)

function openAdvisor() {
  router.push({ name: 'diagnostics', query: { tab: 'advisor' } })
}
</script>

<template>
  <div v-if="!isLoading && !isError && clusterId" class="advisor-widget" :class="{ 'is-clean': !hasIssues }">

    <!-- ALL GOOD -->
    <div v-if="!hasIssues" class="widget-clean">
      <i class="pi pi-check-circle" />
      <span>No advisor recommendations — cluster looks healthy</span>
    </div>

    <!-- HAS ISSUES -->
    <template v-else>
      <div class="widget-header">
        <div class="widget-title">
          <i class="pi pi-sparkles" />
          <span>Advisor</span>
          <span class="total-badge">{{ totalCount }}</span>
        </div>

        <div class="sev-counters">
          <span
            v-for="sev in SEV_ORDER"
            :key="sev"
            v-show="counts[sev] > 0"
            :class="['sev-chip', SEV_META[sev].cls]"
          >
            <i :class="['pi', SEV_META[sev].icon]" />
            {{ counts[sev] }} {{ SEV_META[sev].label }}
          </span>
        </div>

        <button class="open-btn" @click="openAdvisor">
          Open Advisor
          <i class="pi pi-arrow-right" />
        </button>
      </div>

      <ul class="top-cards">
        <li
          v-for="card in topCards"
          :key="card.id"
          class="top-card"
          :class="'border-' + card.severity"
        >
          <span :class="['card-sev-dot', 'dot-' + card.severity]" />
          <div class="card-body">
            <span class="card-title">{{ card.title }}</span>
            <span class="card-summary">{{ card.summary }}</span>
          </div>
          <button class="card-link" @click="openAdvisor" :title="'See in Advisor'">
            <i class="pi pi-external-link" />
          </button>
        </li>
      </ul>

      <div v-if="totalCount > 3" class="more-hint" @click="openAdvisor">
        +{{ totalCount - 3 }} more — open full Advisor panel
      </div>
    </template>

  </div>
</template>

<style scoped>
.advisor-widget {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
  transition: border-color var(--transition-interactive);
}

.advisor-widget.is-clean {
  border-color: var(--color-success-highlight);
  background: color-mix(in oklch, var(--color-success) 4%, var(--color-surface));
}

/* --- CLEAN STATE --- */
.widget-clean {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-success);
}
.widget-clean .pi { font-size: 1rem; }

/* --- HEADER --- */
.widget-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.widget-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  flex-shrink: 0;
}

.total-badge {
  font-size: var(--text-xs);
  font-weight: 700;
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 1px 7px;
  color: var(--color-text-muted);
  font-family: var(--font-mono, monospace);
}

.sev-counters {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  flex-wrap: wrap;
}

.sev-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.sev-critical { color: var(--color-error);   background: var(--color-error-highlight); }
.sev-warn     { color: var(--color-warning); background: var(--color-warning-highlight); }
.sev-info     { color: var(--color-blue);    background: var(--color-blue-highlight); }

.open-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-primary);
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  background: transparent;
  transition: background var(--transition-interactive), color var(--transition-interactive);
  white-space: nowrap;
  flex-shrink: 0;
}
.open-btn:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

/* --- TOP CARDS --- */
.top-cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.top-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid oklch(from var(--color-border) l c h / 0.5);
  cursor: pointer;
  transition: background var(--transition-interactive);
}
.top-card:last-child { border-bottom: none; }
.top-card:hover { background: var(--color-surface-offset); }

.border-critical { border-left: 3px solid transparent; border-left-color: var(--color-error); }
.border-warn      { border-left: 3px solid transparent; border-left-color: var(--color-warning); }
.border-info      { border-left: 3px solid transparent; border-left-color: var(--color-blue); }

.card-sev-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}
.dot-critical { background: var(--color-error); }
.dot-warn     { background: var(--color-warning); }
.dot-info     { background: var(--color-blue); }

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-summary {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-link {
  flex-shrink: 0;
  color: var(--color-text-faint);
  padding: var(--space-1);
  border-radius: var(--radius-sm);
  transition: color var(--transition-interactive);
}
.card-link:hover { color: var(--color-primary); }

/* --- MORE HINT --- */
.more-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  padding: var(--space-2) var(--space-4);
  cursor: pointer;
  border-top: 1px solid oklch(from var(--color-border) l c h / 0.5);
  transition: color var(--transition-interactive);
  text-align: center;
}
.more-hint:hover { color: var(--color-primary); }
</style>
