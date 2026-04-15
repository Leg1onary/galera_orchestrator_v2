<script setup lang="ts">
import { computed } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast }   from 'primevue/usetoast'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from '@/api/client'

interface ClusterEvent {
  id: number
  ts: string
  level: string
  source?: string | null
  message: string
  node_id?: number | null
  arbitrator_id?: number | null
  operation_id?: number | null
}

const props = defineProps<{
  events: ClusterEvent[]
  isLoading?: boolean
  clusterId: number
}>()

const confirm = useConfirm()
const toast   = useToast()
const qc      = useQueryClient()

const { mutate: clearLog, isPending: isClearing } = useMutation({
  mutationFn: () => api.delete(`/api/clusters/${props.clusterId}/log`),
  onSuccess: (res) => {
    const deleted = res.data?.deleted ?? 0
    toast.add({
      severity: 'success',
      summary:  'Log cleared',
      detail:   `Deleted ${deleted} event${deleted !== 1 ? 's' : ''}`,
      life:     3000,
    })
    qc.invalidateQueries({ queryKey: ['cluster', props.clusterId, 'log'] })
  },
  onError: () => {
    toast.add({
      severity: 'error',
      summary:  'Failed to clear log',
      life:     4000,
    })
  },
})

function confirmClear(event: MouseEvent) {
  confirm.require({
    target:      event.currentTarget as HTMLElement,
    message:     'Delete all log entries for this cluster?',
    icon:        'pi pi-exclamation-triangle',
    accept:      () => clearLog(),
    acceptLabel: 'Clear',
    rejectLabel: 'Cancel',
    acceptClass: 'p-button-danger p-button-sm',
    rejectClass: 'p-button-text p-button-sm',
  })
}

function normLevel(level: string): string {
  return (level ?? 'info').toLowerCase()
}

const LEVEL_CFG: Record<string, { icon: string; severity: string }> = {
  info:     { icon: 'pi pi-info-circle',          severity: 'info'    },
  warning:  { icon: 'pi pi-exclamation-triangle', severity: 'warn'    },
  error:    { icon: 'pi pi-times-circle',         severity: 'danger'  },
  critical: { icon: 'pi pi-exclamation-circle',   severity: 'danger'  },
}

function cfg(level: string) {
  return LEVEL_CFG[normLevel(level)] ?? LEVEL_CFG.info
}

function parseTs(ts: string): Date {
  if (!ts) return new Date(NaN)
  let s = ts.trim().replace(' ', 'T')
  s = s.replace(/[+-]00:?00$/, 'Z')
  if (!/Z$/i.test(s)) s += 'Z'
  return new Date(s)
}

function formatTs(ts: string): { date: string; time: string } {
  const d = parseTs(ts)
  if (isNaN(d.getTime())) return { date: '', time: '\u2014' }
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

const sortedEvents = computed(() =>
  [...props.events].sort((a, b) => parseTs(b.ts).getTime() - parseTs(a.ts).getTime())
)
</script>

<template>
  <div class="event-log">
    <div class="event-log-header">
      <div class="el-title-group">
        <span class="section-title">Event Log</span>
        <span v-if="props.events.length" class="el-count">{{ props.events.length }}</span>
      </div>
      <Button
        v-if="props.events.length"
        label="Clear"
        icon="pi pi-trash"
        size="small"
        severity="secondary"
        text
        :loading="isClearing"
        class="el-clear-btn"
        @click="confirmClear"
      />
    </div>

    <ConfirmPopup />

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
      :value="sortedEvents"
      class="el-timeline"
    >
      <template #marker="{ item }">
        <span :class="['el-marker', 'el-marker--' + normLevel(item.level)]">
          <i :class="cfg(item.level).icon" />
        </span>
      </template>

      <template #content="{ item }">
        <div class="el-item">
          <div class="el-item-head">
            <span class="el-time">
              <template v-if="formatTs(item.ts).date">
                <span class="el-date">{{ formatTs(item.ts).date }}</span>
                <span class="el-sep"> &middot; </span>
              </template>
              {{ formatTs(item.ts).time }}
            </span>
            <Tag
              v-if="item.source"
              :value="item.source"
              severity="secondary"
              class="el-source-tag"
            />
            <Tag
              v-if="item.node_id"
              :value="'node #' + item.node_id"
              severity="secondary"
              class="el-node-tag"
            />
            <Tag
              :value="normLevel(item.level)"
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
  padding: var(--space-4) var(--space-5);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.el-title-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.el-count {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-faint);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 1px 7px;
  line-height: 1.6;
}

.el-clear-btn {
  margin-right: calc(var(--space-2) * -1);
}

.el-skeleton {
  padding: var(--space-4) var(--space-5);
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
  padding: var(--space-4) var(--space-5) var(--space-2);
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
.el-marker--info     { background: color-mix(in oklch, #60a5fa 12%, transparent); color: #60a5fa; }
.el-marker--warning  { background: color-mix(in oklch, var(--color-degraded) 12%, transparent); color: var(--color-degraded); }
.el-marker--error    { background: color-mix(in oklch, var(--color-offline) 12%, transparent); color: var(--color-offline); }
.el-marker--critical { background: color-mix(in oklch, var(--color-offline) 15%, transparent); color: var(--color-offline); }

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

.el-source-tag,
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
