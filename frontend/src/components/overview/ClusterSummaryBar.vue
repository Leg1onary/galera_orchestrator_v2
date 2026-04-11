<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  totalNodes: number
  syncedNodes: number
  clusterStatus: string | null
  clusterSize: number | null
  flowControlPaused: number | null
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), { isLoading: false })

// Backend _calc_cluster_status() returns 'healthy' | 'degraded' | 'critical'
// (see ТЗ п.7.1). Map directly — no wsrep_cluster_status parsing needed here.
const healthState = computed(() => {
  const s = props.clusterStatus?.toLowerCase()
  if (s === 'healthy')  return 'healthy'
  if (s === 'degraded') return 'degraded'
  if (s === 'critical') return 'critical'
  return 'unknown'
})

const HEALTH_MAP = {
  healthy:  { label: 'Healthy',  severity: 'success',   icon: 'pi pi-check-circle' },
  degraded: { label: 'Degraded', severity: 'warn',      icon: 'pi pi-exclamation-triangle' },
  critical: { label: 'Critical', severity: 'danger',    icon: 'pi pi-times-circle' },
  unknown:  { label: 'Unknown',  severity: 'secondary', icon: 'pi pi-question-circle' },
} as const

const healthCfg = computed(() => HEALTH_MAP[healthState.value])

const meterValues = computed(() => {
  if (props.totalNodes === 0) return []
  const syncedPct = Math.round((props.syncedNodes / props.totalNodes) * 100)
  const others    = 100 - syncedPct
  const result = [
    { label: 'Synced', color: 'var(--color-synced)', value: syncedPct },
  ]
  if (others > 0) {
    result.push({ label: 'Other', color: 'var(--color-degraded)', value: others })
  }
  return result
})

const flowWarn = computed(() => (props.flowControlPaused ?? 0) > 0)
</script>

<template>
  <div class="csb anim-fade-in">

    <!-- Cluster health tag -->
    <div class="csb-item csb-item--main">
      <span class="csb-label">Cluster</span>
      <div v-if="props.isLoading">
        <Skeleton height="1.5rem" width="90px" />
      </div>
      <Tag
        v-else
        :value="healthCfg.label"
        :severity="healthCfg.severity"
        :icon="healthCfg.icon"
        class="csb-tag"
      />
    </div>

    <div class="csb-divider" />

    <!-- Nodes synced with MeterGroup -->
    <div class="csb-item csb-item--wide">
      <span class="csb-label">Synced</span>
      <div v-if="props.isLoading">
        <Skeleton height="1rem" width="120px" />
      </div>
      <div v-else class="csb-meter-wrap">
        <span class="csb-val">{{ syncedNodes }}<span class="csb-total">/{{ totalNodes }}</span></span>
        <MeterGroup
          :value="meterValues"
          class="csb-meter"
          :pt="{ meters: { style: 'height: 4px; border-radius: 99px' }, meter: { style: 'border-radius: 99px' } }"
        />
      </div>
    </div>

    <div class="csb-divider" />

    <!-- Primary component -->
    <div class="csb-item">
      <span class="csb-label">Component</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="70px" /></div>
      <span v-else class="csb-val csb-val--mono">{{ clusterStatus ?? '\u2014' }}</span>
    </div>

    <div class="csb-divider" />

    <!-- wsrep cluster size -->
    <div class="csb-item">
      <span class="csb-label">wsrep size</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="40px" /></div>
      <span v-else class="csb-val csb-val--mono">{{ clusterSize ?? '\u2014' }}</span>
    </div>

    <div class="csb-divider" />

    <!-- Flow control -->
    <div class="csb-item">
      <span class="csb-label">Flow ctrl</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="60px" /></div>
      <Tag
        v-else
        :value="flowControlPaused !== null ? flowControlPaused.toFixed(3) : '\u2014'"
        :severity="flowWarn ? 'warn' : 'secondary'"
        :icon="flowWarn ? 'pi pi-exclamation-triangle' : undefined"
        class="csb-tag csb-tag--mono"
      />
    </div>
  </div>
</template>

<style scoped>
.csb {
  display: flex;
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  /* компактный padding, но с нормальной высотой */
  padding: var(--space-4) var(--space-5);
  gap: var(--space-5);
  overflow-x: auto;
  flex-wrap: nowrap;
}

.csb-item {
  display: flex;
  flex-direction: column;
  /* ключевой момент: достаточный gap между label и value */
  gap: var(--space-2);
  min-width: max-content;
}
.csb-item--main  { min-width: 120px; }
.csb-item--wide  { min-width: 160px; }

.csb-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-faint);
  font-weight: 600;
  /* небольшой верхний отступ чтобы label не прилипал к краю */
  padding-top: 2px;
}

.csb-val {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
}
.csb-val--mono { font-family: var(--font-mono); }

.csb-total {
  color: var(--color-text-muted);
  font-weight: 500;
}

.csb-tag { font-size: var(--text-xs) !important; }
.csb-tag--mono :deep(.p-tag-value) { font-family: var(--font-mono); }

.csb-meter-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.csb-meter {
  width: 120px;
}

:deep(.p-metergroup-label-list) { display: none; }

.csb-divider {
  width: 1px;
  height: 36px;
  background: var(--color-border);
  flex-shrink: 0;
  opacity: 0.6;
}
</style>
