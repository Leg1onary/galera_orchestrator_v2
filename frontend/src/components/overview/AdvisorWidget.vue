<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { useClusterStore } from '@/stores/cluster'
import { advisorApi, type AdvisorSeverity, type AdvisorCard } from '@/api/advisor'

// PrimeVue 4
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Skeleton from 'primevue/skeleton'
import Divider from 'primevue/divider'

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

watch(clusterId, () => refetch())

const SEV_ORDER: AdvisorSeverity[] = ['critical', 'warn', 'info']

const SEV_META: Record<AdvisorSeverity, {
  label: string
  icon: string
  tagSeverity: string
  dotCls: string
}> = {
  critical: { label: 'Critical', icon: 'pi-times-circle',       tagSeverity: 'danger',    dotCls: 'dot-critical' },
  warn:     { label: 'Warning',  icon: 'pi-exclamation-circle', tagSeverity: 'warn',      dotCls: 'dot-warn' },
  info:     { label: 'Info',     icon: 'pi-info-circle',        tagSeverity: 'info',      dotCls: 'dot-info' },
}

const advisors   = computed(() => data.value?.advisors ?? [])
const hasIssues  = computed(() => advisors.value.length > 0)
const totalCount = computed(() => advisors.value.length)

const counts = computed(() => {
  const map: Record<AdvisorSeverity, number> = { critical: 0, warn: 0, info: 0 }
  for (const a of advisors.value) map[a.severity]++
  return map
})

const topCards = computed<AdvisorCard[]>(() =>
  [...advisors.value]
    .sort((a, b) => SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity))
    .slice(0, 3)
)

function openAdvisor() {
  router.push({ name: 'diagnostics', query: { tab: 'advisor' } })
}
</script>

<template>
  <!-- Loading skeleton -->
  <div v-if="isLoading" class="advisor-widget">
    <div class="widget-head">
      <div class="wh-left">
        <Skeleton width="5rem" height="1.1rem" border-radius="var(--radius-full)" />
        <Skeleton width="1.5rem" height="1.1rem" border-radius="var(--radius-full)" />
      </div>
      <Skeleton width="6rem" height="1.75rem" border-radius="var(--radius-md)" />
    </div>
    <div class="skeleton-rows">
      <div v-for="i in 3" :key="i" class="skeleton-row">
        <Skeleton shape="circle" size="0.5rem" />
        <div class="skeleton-row-body">
          <Skeleton width="55%" height="0.875rem" />
          <Skeleton width="80%" height="0.75rem" />
        </div>
      </div>
    </div>
  </div>

  <!-- Error / no cluster -->
  <div v-else-if="isError || !clusterId" class="advisor-widget advisor-widget--muted">
    <div class="state-row">
      <i class="pi pi-exclamation-circle state-icon state-icon--warn" />
      <span class="state-text">Не удалось загрузить данные Advisor</span>
      <Button
        icon="pi pi-refresh"
        size="small"
        text
        severity="secondary"
        @click="refetch"
        v-tooltip.top="'Retry'"
      />
    </div>
  </div>

  <!-- All good -->
  <div v-else-if="!hasIssues" class="advisor-widget advisor-widget--clean">
    <div class="state-row">
      <div class="clean-icon-wrap">
        <i class="pi pi-check-circle" />
      </div>
      <div class="clean-body">
        <span class="clean-title">Cluster is healthy</span>
        <span class="clean-sub">Нет рекомендаций Advisor</span>
      </div>
    </div>
  </div>

  <!-- Has issues -->
  <div v-else class="advisor-widget">

    <!-- Header -->
    <div class="widget-head">
      <div class="wh-left">
        <i class="pi pi-sparkles wh-icon" />
        <span class="wh-title">Advisor</span>
        <Tag
          :value="String(totalCount)"
          severity="secondary"
          rounded
          class="total-tag"
        />
      </div>

      <!-- Severity counters -->
      <div class="sev-tags">
        <Tag
          v-for="sev in SEV_ORDER"
          :key="sev"
          v-show="counts[sev] > 0"
          :icon="`pi ${SEV_META[sev].icon}`"
          :value="String(counts[sev])"
          :severity="SEV_META[sev].tagSeverity"
          rounded
          class="sev-tag"
          v-tooltip.top="SEV_META[sev].label"
        />
      </div>

      <Button
        label="Open Advisor"
        icon="pi pi-arrow-right"
        icon-pos="right"
        size="small"
        outlined
        severity="secondary"
        @click="openAdvisor"
        class="open-btn"
      />
    </div>

    <Divider class="widget-divider" />

    <!-- Top cards list -->
    <ul class="top-cards">
      <li
        v-for="(card, idx) in topCards"
        :key="card.id"
        class="top-card"
        @click="openAdvisor"
      >
        <!-- Severity indicator dot -->
        <span :class="['sev-dot', SEV_META[card.severity].dotCls]" />

        <!-- Card content -->
        <div class="card-body">
          <div class="card-top-row">
            <span class="card-title">{{ card.title }}</span>
            <Tag
              :value="card.category"
              severity="secondary"
              class="card-cat-tag"
            />
          </div>
          <span class="card-summary">{{ card.summary }}</span>
        </div>

        <!-- Arrow -->
        <i class="pi pi-chevron-right card-arrow" />
      </li>
    </ul>

    <!-- More hint -->
    <div v-if="totalCount > 3" class="more-row" @click="openAdvisor">
      <span>+{{ totalCount - 3 }} больше</span>
      <i class="pi pi-arrow-right" />
    </div>

  </div>
</template>

<style scoped>
/* ── Root ── */
.advisor-widget {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.advisor-widget--clean {
  border-color: color-mix(in oklch, var(--color-success) 30%, var(--color-border));
  background: color-mix(in oklch, var(--color-success) 4%, var(--color-surface));
}

.advisor-widget--muted {
  background: var(--color-surface-offset);
}

/* ── Skeleton ── */
.skeleton-rows {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.skeleton-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid rgba(255,255,255,0.04);
}
.skeleton-row-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

/* ── State rows (clean / error) ── */
.state-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
}
.state-icon { font-size: 1.1rem; }
.state-icon--warn { color: var(--color-warning); }
.state-text {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.clean-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--color-success-highlight);
  color: var(--color-success);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
}
.clean-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.clean-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-success);
}
.clean-sub {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* ── Widget head ── */
.widget-head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  flex-wrap: wrap;
}

.wh-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}
.wh-icon {
  font-size: 0.875rem;
  color: var(--color-primary);
}
.wh-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}
.total-tag { font-size: var(--text-xs) !important; padding: 3px 10px !important; }

.sev-tags {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex: 1;
  flex-wrap: wrap;
}
.sev-tag { font-size: var(--text-xs) !important; padding: 3px 10px !important; cursor: default; }

.open-btn {
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── Divider ── */
.widget-divider {
  margin: 0 !important;
}

/* ── Top cards ── */
.top-cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.top-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: background var(--transition-interactive);
  min-width: 0;
}
.top-card:last-child { border-bottom: none; }
.top-card:hover {
  background: var(--color-surface-offset);
}
.top-card:hover .card-arrow {
  color: var(--color-primary);
  transform: translateX(2px);
}

/* Severity dot — круглый индикатор без полоски */
.sev-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-critical { background: var(--color-error);   box-shadow: 0 0 0 2px var(--color-error-highlight); }
.dot-warn     { background: var(--color-warning); box-shadow: 0 0 0 2px var(--color-warning-highlight); }
.dot-info     { background: var(--color-blue);    box-shadow: 0 0 0 2px var(--color-blue-highlight); }

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.card-top-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}
.card-title {
  flex: 1;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-cat-tag { font-size: var(--text-xs) !important; padding: 3px 10px !important; flex-shrink: 0; }

.card-summary {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-arrow {
  flex-shrink: 0;
  font-size: 0.65rem;
  color: var(--color-text-faint);
  transition: color var(--transition-interactive), transform var(--transition-interactive);
}

/* ── More row ── */
.more-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-muted);
  border-top: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: color var(--transition-interactive), background var(--transition-interactive);
  background: var(--color-surface-offset);
}
.more-row:hover {
  color: var(--color-primary);
  background: var(--color-primary-highlight);
}
.more-row .pi { font-size: 0.65rem; }
</style>
