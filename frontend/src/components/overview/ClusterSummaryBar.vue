<script setup lang="ts">
import { computed } from 'vue'
import { useOperationsStore } from '@/stores/operations'

interface Props {
  totalNodes:        number
  syncedNodes:       number
  clusterStatus:     string | null
  clusterSize:       number | null
  flowControlPaused: number | null
  maintenanceNodes:  number
  maxRecvQueue:      number | null
  clusterId:         number
  isLoading?:        boolean
}

const props = withDefaults(defineProps<Props>(), { isLoading: false })

const opsStore = useOperationsStore()

// ── Health ────────────────────────────────────────────────────────────────────
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

// ── Meter ─────────────────────────────────────────────────────────────────────
const meterValues = computed(() => {
  if (props.totalNodes === 0) return []
  const syncedPct = Math.round((props.syncedNodes / props.totalNodes) * 100)
  const others    = 100 - syncedPct
  const result = [
    { label: 'Synced', color: 'var(--color-synced)', value: syncedPct },
  ]
  if (others > 0) result.push({ label: 'Other', color: 'var(--color-degraded)', value: others })
  return result
})

// ── Flow control ──────────────────────────────────────────────────────────────
const flowWarn         = computed(() => (props.flowControlPaused ?? 0) > 0)
const flowDisplay      = computed(() =>
  props.flowControlPaused !== null ? props.flowControlPaused.toFixed(3) : '\u2014'
)

// ── Recv queue ────────────────────────────────────────────────────────────────
const recvQueueWarn    = computed(() => (props.maxRecvQueue ?? 0) > 0)
const recvQueueDisplay = computed(() =>
  props.maxRecvQueue !== null ? String(props.maxRecvQueue) : '\u2014'
)

// ── Active operation ──────────────────────────────────────────────────────────
// activeOperation — без аргумента: стор сам знает selectedClusterId
const activeOp = computed(() => opsStore.activeOperation)

const OP_LABEL: Record<string, string> = {
  'recovery-bootstrap': 'Bootstrap',
  'recovery-rejoin':    'Rejoin',
  'rolling-restart':    'Rolling restart',
  'node-action':        'Node action',
}

const opLabel = computed(() => {
  const op = activeOp.value
  if (!op) return null
  return OP_LABEL[op.type] ?? op.type
})

const opStatus  = computed(() => activeOp.value?.status ?? null)
const opRunning = computed(() =>
  opStatus.value != null && ['pending', 'running', 'cancel_requested'].includes(opStatus.value)
)

const showOp = computed(() => !props.isLoading && !!activeOp.value && !!opLabel.value)
</script>

<template>
  <div class="csb anim-fade-in">

    <!-- 1. Cluster health -->
    <div class="csb-item csb-item--main">
      <span class="csb-label">Cluster</span>
      <div v-if="props.isLoading"><Skeleton height="1.5rem" width="90px" /></div>
      <Tag
        v-else
        :value="healthCfg.label"
        :severity="healthCfg.severity"
        :icon="healthCfg.icon"
        class="csb-tag"
      />
    </div>

    <div class="csb-divider" />

    <!-- 2. Synced nodes -->
    <div class="csb-item csb-item--wide">
      <span class="csb-label">Synced</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="120px" /></div>
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

    <!-- 3. Component -->
    <div class="csb-item">
      <span class="csb-label">Component</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="70px" /></div>
      <span v-else class="csb-val csb-val--mono">{{ clusterStatus ?? '\u2014' }}</span>
    </div>

    <div class="csb-divider" />

    <!-- 4. wsrep size -->
    <div class="csb-item">
      <span class="csb-label">wsrep size</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="40px" /></div>
      <span v-else class="csb-val csb-val--mono">{{ clusterSize ?? '\u2014' }}</span>
    </div>

    <div class="csb-divider" />

    <!-- 5. Flow control -->
    <div class="csb-item">
      <span class="csb-label">Flow ctrl</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="60px" /></div>
      <Tag
        v-else
        :value="flowDisplay"
        :severity="flowWarn ? 'warn' : 'secondary'"
        :icon="flowWarn ? 'pi pi-exclamation-triangle' : undefined"
        class="csb-tag csb-tag--mono"
      />
    </div>

    <div class="csb-divider" />

    <!-- 6. Recv queue -->
    <div class="csb-item">
      <span class="csb-label">Recv queue</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="50px" /></div>
      <Tag
        v-else
        :value="recvQueueDisplay"
        :severity="recvQueueWarn ? 'warn' : 'secondary'"
        :icon="recvQueueWarn ? 'pi pi-exclamation-triangle' : undefined"
        class="csb-tag csb-tag--mono"
      />
    </div>

    <div class="csb-divider" />

    <!-- 7. Maintenance -->
    <div class="csb-item">
      <span class="csb-label">Maint</span>
      <div v-if="props.isLoading"><Skeleton height="1rem" width="40px" /></div>
      <div v-else class="csb-maint" :class="maintenanceNodes > 0 ? 'csb-maint--active' : ''">
        <i class="pi pi-wrench csb-maint-icon" />
        <span class="csb-val csb-val--mono">{{ maintenanceNodes }}</span>
      </div>
    </div>

    <!-- 8. Active operation -->
    <Transition name="csb-op-slide">
      <div v-if="showOp" class="csb-op-wrap">
        <div class="csb-divider" />
        <div class="csb-item csb-item--op">
          <span class="csb-label">Operation</span>
          <div class="csb-op" :class="opRunning ? 'csb-op--running' : 'csb-op--done'">
            <i :class="opRunning ? 'pi pi-spin pi-spinner csb-op-icon' : 'pi pi-check-circle csb-op-icon'" />
            <div class="csb-op-text">
              <span class="csb-op-name">{{ opLabel }}</span>
              <span class="csb-op-status">{{ opStatus }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.csb {
  display: flex;
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
  gap: var(--space-5);
  overflow-x: auto;
  flex-wrap: nowrap;
}

.csb-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: max-content;
}
.csb-item--main { min-width: 120px; }
.csb-item--wide { min-width: 160px; }
.csb-item--op   { min-width: 140px; }

.csb-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-faint);
  font-weight: 600;
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

.csb-tag       { font-size: var(--text-xs) !important; }
.csb-tag--mono :deep(.p-tag-value) { font-family: var(--font-mono); }

.csb-meter-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.csb-meter { width: 120px; }
:deep(.p-metergroup-label-list) { display: none; }

.csb-divider {
  width: 1px;
  height: 36px;
  background: var(--color-border);
  flex-shrink: 0;
  opacity: 0.6;
}

/* ── Maintenance ── */
.csb-maint {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-text-faint);
}
.csb-maint-icon { font-size: 0.75rem; }
.csb-maint--active { color: var(--color-warning); }
.csb-maint--active .csb-val { color: var(--color-warning); }

/* ── Active Operation ── */
.csb-op-wrap { display: contents; }

.csb-op {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.csb-op-icon { font-size: 0.85rem; flex-shrink: 0; }
.csb-op-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.csb-op-name {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}
.csb-op-status {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 600;
  line-height: 1;
}

.csb-op--running .csb-op-icon   { color: var(--color-primary); }
.csb-op--running .csb-op-status { color: var(--color-primary); }

.csb-op--done .csb-op-icon   { color: var(--color-synced); }
.csb-op--done .csb-op-status { color: var(--color-text-faint); }

/* ── Slide-in transition ── */
.csb-op-slide-enter-active {
  transition: opacity 220ms ease, transform 220ms cubic-bezier(0.16, 1, 0.3, 1);
}
.csb-op-slide-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.csb-op-slide-enter-from,
.csb-op-slide-leave-to {
  opacity: 0;
  transform: translateX(10px);
}
</style>
