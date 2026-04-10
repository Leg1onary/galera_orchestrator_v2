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

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-GB', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}
</script>

<template>
  <div class="event-log">
    <div class="event-log-header">
      <span class="section-title">Event Log</span>
      <span v-if="props.events.length" class="el-count">{{ props.events.length }} events</span>
    </div>

    <!-- Loading -->
    <div v-if="props.isLoading" class="el-skeleton">
      <div v-for="i in 4" :key="i" class="el-sk-row">
        <Skeleton shape="circle" size="2rem" />
        <div class="el-sk-lines">
          <Skeleton height="0.7rem" width="5rem" />
          <Skeleton height="0.7rem" width="14rem" />
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="props.events.length === 0" class="el-empty">
      <i class="pi pi-check-circle" />
      <span>No events — all clear</span>
    </div>

    <!-- Timeline -->
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
            <span class="el-time">{{ formatTime(item.created_at) }}</span>
            <Tag
              v-if="item.node_name"
              :value="item.node_name"
              severity="secondary"
              class="el-node-tag"
            />
            <Tag
              :value="item.level"
              :severity="cfg(item.level).severity === 'warn' ? 'warn' : cfg(item.level).severity"
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
  border-bottom: 1px solid var(--color-border-muted);
}

.el-count {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
}

/* Skeleton */
.el-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
}
.el-sk-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.el-sk-lines {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
}

/* Empty */
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

/* Timeline */
.el-timeline {
  padding: var(--space-4) var(--space-5);
  max-height: 360px;
  overflow-y: auto;
}

/* Marker */
.el-marker {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.el-marker--info     { background: rgba(96,165,250,0.12); color: var(--color-info, #60a5fa); }
.el-marker--warning  { background: rgba(251,146,60,0.12); color: var(--color-degraded); }
.el-marker--error    { background: rgba(248,113,113,0.12); color: var(--color-offline); }
.el-marker--critical { background: rgba(248,113,113,0.15); color: var(--color-offline); }

/* Item */
.el-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding-bottom: var(--space-3);
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
}
</style>
