<script setup lang="ts">
interface ClusterEvent {
  id: number
  created_at: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  node_name?: string | null
}

const props = defineProps<{ events: ClusterEvent[]; isLoading?: boolean }>()

const LEVEL_CFG: Record<string, { icon: string; severity: string }> = {
  info:     { icon: 'pi pi-info-circle',          severity: 'info' },
  warning:  { icon: 'pi pi-exclamation-triangle', severity: 'warn' },
  error:    { icon: 'pi pi-times-circle',         severity: 'danger' },
  critical: { icon: 'pi pi-exclamation-circle',   severity: 'danger' },
}

function cfg(level: string) {
  return LEVEL_CFG[level] ?? LEVEL_CFG.info
}

function parseDate(iso: string): Date {
  if (!iso) return new Date(NaN)
  const normalized = iso.trim().replace(/([+-]\d{2}:\d{2}|Z)$/, 'Z')
  const d = new Date(normalized)
  if (!isNaN(d.getTime())) return d
  return new Date(iso)
}

function formatTs(iso: string): { date: string; time: string } {
  // DEBUG: убрать после диагностики
  console.log('[EventLog] raw created_at:', JSON.stringify(iso), '| type:', typeof iso)
  const normalized = iso?.trim().replace(/([+-]\d{2}:\d{2}|Z)$/, 'Z')
  console.log('[EventLog] normalized:', normalized, '| new Date():', new Date(normalized).toString())

  const d = parseDate(iso)
  if (isNaN(d.getTime())) return { date: '', time: '—' }

  const time = d.toLocaleTimeString('en-GB', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })

  const today = new Date()
  const isToday =
    d.getUTCFullYear() === today.getUTCFullYear() &&
    d.getUTCMonth()    === today.getUTCMonth() &&
    d.getUTCDate()     === today.getUTCDate()

  const date = isToday
    ? ''
    : d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })

  return { date, time }
}
</script>

<template>
  <div class="event-log">
    <div class="event-log-header">
      <span class="section-title">Event Log</span>
      <span v-if="props.events.length" class="el-count">{{ props.events.length }} events</span>
    </div>

    <div v-if="props.isLoading" class="el-skeleton">
      <div v-for="i in 4" :key="i" class="el-sk-row">
        <Skeleton shape="circle" size="2rem" />
        <div class="el-sk-lines">
          <Skeleton height="0.7rem" width="5rem" />
          <Skeleton height="0.7rem" width="14rem" />
        </div>
      </div>
    </div>

    <div v-else-if="props.events.length === 0" class="el-empty">
      <i class="pi pi-check-circle" />
      <span>No events — all clear</span>
    </div>

    <Timeline
      v-else
      :value="props.events"
      class="el-timeline"
    >
      <template #marker="{ item }">
        <span :class="['el-marker', 'el-marker--' + item.level]">
          <i :class="cfg(item.level).icon" />
        </span>
      </template>

      <template #content="{ item }">
        <div class="el-item">
          <div class="el-item-head">
            <span class="el-time">
              <template v-if="formatTs(item.created_at).date">
                <span class="el-date">{{ formatTs(item.created_at).date }}</span>
                <span class="el-sep"> · </span>
              </template>
              {{ formatTs(item.created_at).time }}
            </span>
            <Tag
              v-if="item.node_name"
              :value="item.node_name"
              severity="secondary"
              class="el-node-tag"
            />
            <Tag
              :value="item.level"
              :severity="cfg(item.level).severity"
              class="el-level-tag"
            />
          </div>
          <p class="el-msg">{{ item.message }}</p>
        </div>
      </template>
    </Timeline>
  </div>
</template>

<style scoped>
.event-log {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.event-log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.el-count {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
}
.el-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
}
.el-sk-row { display: flex; align-items: center; gap: var(--space-3); }
.el-sk-lines { display: flex; flex-direction: column; gap: var(--space-2); flex: 1; }
.el-empty {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-8) var(--space-5);
  color: var(--color-text-faint);
  font-size: var(--text-sm);
  justify-content: center;
}
.el-empty i { color: var(--color-synced); font-size: 0.9rem; }
.el-timeline {
  padding: var(--space-3) var(--space-4);
  max-height: 360px;
  overflow-y: auto;
}
:deep(.p-timeline-event) {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  min-height: unset;
}
:deep(.p-timeline-event-opposite) {
  display: none !important;
  flex: 0 !important;
  padding: 0 !important;
}
:deep(.p-timeline-event-separator) {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 0 0 auto;
  gap: 0;
}
:deep(.p-timeline-event-connector) {
  flex-grow: 0 !important;
  height: 16px !important;
  min-height: unset !important;
  width: 1px;
  background: var(--color-border);
  margin: 2px 0;
}
:deep(.p-timeline-event-content) {
  flex: 1 1 0;
  min-width: 0;
  padding: 0 0 var(--space-2) 0;
}
.el-marker {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 0.7rem;
  flex-shrink: 0;
}
.el-marker--info     { background: rgba(96,165,250,0.12);  color: #60a5fa; }
.el-marker--warning  { background: rgba(251,146,60,0.12);  color: var(--color-degraded); }
.el-marker--error    { background: rgba(248,113,113,0.12); color: var(--color-offline); }
.el-marker--critical { background: rgba(248,113,113,0.15); color: var(--color-offline); }
.el-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding-bottom: var(--space-1);
  width: 100%;
}
.el-item-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}
.el-time {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  white-space: nowrap;
}
.el-date { color: var(--color-text-muted); }
.el-sep  { color: var(--color-text-faint); opacity: 0.5; }
.el-node-tag,
.el-level-tag {
  font-size: 0.6rem !important;
  padding: 1px 5px !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.el-msg {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.5;
  max-width: 100%;
}
</style>
