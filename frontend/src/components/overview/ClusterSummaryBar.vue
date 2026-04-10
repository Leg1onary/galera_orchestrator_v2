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

const healthState = computed(() => {
  if (!props.clusterStatus) return 'unknown'
  const s = props.clusterStatus.toUpperCase()
  if (s === 'PRIMARY' && props.syncedNodes === props.totalNodes) return 'healthy'
  if (s === 'PRIMARY') return 'degraded'
  return 'critical'
})

const healthConfig = computed(() => {
  const map: Record<string, { label: string; cls: string }> = {
    healthy:  { label: 'Healthy',  cls: 'healthy' },
    degraded: { label: 'Degraded', cls: 'degraded' },
    critical: { label: 'Critical', cls: 'critical' },
    unknown:  { label: 'Unknown',  cls: 'unknown' },
  }
  return map[healthState.value]
})

const syncRatio = computed(() =>
  props.totalNodes > 0 ? props.syncedNodes / props.totalNodes : 0
)
</script>

<template>
  <div class="csb anim-fade-in">
    <!-- Cluster health -->
    <div class="csb-item csb-item--main">
      <span class="csb-label">Cluster</span>
      <div :class="['csb-health', 'csb-health--' + healthConfig.cls]">
        <span class="csb-dot" />
        <span class="csb-health-text">{{ healthConfig.label }}</span>
      </div>
    </div>

    <div class="csb-divider" />

    <!-- Nodes synced -->
    <div class="csb-item">
      <span class="csb-label">Synced</span>
      <div class="csb-synced">
        <span class="csb-val">{{ syncedNodes }}<span class="csb-total">/{{ totalNodes }}</span></span>
        <!-- mini progress bar -->
        <div class="csb-progress" aria-hidden="true">
          <div
            class="csb-progress-fill"
            :class="syncRatio === 1 ? 'csb-progress-fill--full' : 'csb-progress-fill--partial'"
            :style="{ width: (syncRatio * 100) + '%' }"
          />
        </div>
      </div>
    </div>

    <div class="csb-divider" />

    <!-- Primary component -->
    <div class="csb-item">
      <span class="csb-label">Component</span>
      <span class="csb-val csb-val--mono">{{ clusterStatus ?? '—' }}</span>
    </div>

    <div class="csb-divider" />

    <!-- Cluster size -->
    <div class="csb-item">
      <span class="csb-label">wsrep size</span>
      <span class="csb-val csb-val--mono">{{ clusterSize ?? '—' }}</span>
    </div>

    <div class="csb-divider" />

    <!-- Flow control -->
    <div class="csb-item">
      <span class="csb-label">Flow ctrl</span>
      <span
        class="csb-val csb-val--mono"
        :class="(flowControlPaused ?? 0) > 0 ? 'csb-val--warn' : ''"
      >
        {{ flowControlPaused !== null ? flowControlPaused.toFixed(3) : '—' }}
      </span>
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
  padding: var(--space-3) var(--space-5);
  gap: var(--space-3);
  overflow-x: auto;
}

.csb-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: max-content;
}

.csb-item--main { min-width: 120px; }

.csb-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-faint);
  font-weight: 500;
}

.csb-val {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--color-text);
}

.csb-val--mono { font-family: var(--font-mono); }
.csb-val--warn { color: var(--color-degraded); }

.csb-synced {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.csb-total {
  color: var(--color-text-muted);
  font-weight: 500;
}

.csb-progress {
  width: 80px;
  height: 3px;
  background: var(--color-surface-3);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.csb-progress-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
}

.csb-progress-fill--full    { background: var(--color-synced); }
.csb-progress-fill--partial { background: var(--color-degraded); }

.csb-divider {
  width: 1px;
  height: 32px;
  background: var(--color-border-muted);
  flex-shrink: 0;
}

.csb-health {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-md);
  font-weight: 700;
}

.csb-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.csb-health--healthy  { color: var(--color-synced); }
.csb-health--degraded { color: var(--color-degraded); }
.csb-health--critical { color: var(--color-offline); }
.csb-health--unknown  { color: var(--color-text-muted); }

.csb-health-text { color: var(--color-text); }
</style>
