<script setup lang="ts">
import { computed } from 'vue'

interface ClusterEvent {
  id: number
  created_at: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  node_name?: string | null
}

const props = defineProps<{
  events: ClusterEvent[]
  isLoading?: boolean
}>()

const LEVEL_CONFIG: Record<string, { icon: string; cls: string }> = {
  info:     { icon: 'pi-info-circle', cls: 'info' },
  warning:  { icon: 'pi-exclamation-triangle', cls: 'warn' },
  error:    { icon: 'pi-times-circle', cls: 'error' },
  critical: { icon: 'pi-exclamation-circle', cls: 'critical' },
}

function levelConfig(level: string) {
  return LEVEL_CONFIG[level] ?? LEVEL_CONFIG.info
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
</script>

<template>
  <div class="event-log">
    <div class="event-log-header">
      <span class="section-title">Event Log</span>
      <span class="event-count text-faint text-xs" v-if="events.length">
        {{ events.length }} events
      </span>
    </div>

    <div v-if="isLoading" class="loading-state">
      <i class="pi pi-spin pi-spinner" />
      <span>Loading events&hellip;</span>
    </div>

    <div v-else-if="events.length === 0" class="el-empty">
      <i class="pi pi-check-circle" />
      <span>No events — all clear</span>
    </div>

    <div v-else class="el-list">
      <div
        v-for="ev in events"
        :key="ev.id"
        class="el-row"
        :class="'el-row--' + levelConfig(ev.level).cls"
      >
        <i :class="'pi ' + levelConfig(ev.level).icon" class="el-icon" aria-hidden="true" />
        <span class="el-time">{{ formatTime(ev.created_at) }}</span>
        <span class="el-node" v-if="ev.node_name">{{ ev.node_name }}</span>
        <span class="el-msg">{{ ev.message }}</span>
      </div>
    </div>
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

.event-count {
  font-family: var(--font-mono);
}

.el-empty {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-8) var(--space-5);
  color: var(--color-text-faint);
  font-size: var(--text-sm);
  justify-content: center;
}

.el-empty i { font-size: 0.9rem; color: var(--color-synced); }

.el-list {
  max-height: 320px;
  overflow-y: auto;
}

.el-row {
  display: grid;
  grid-template-columns: 14px 68px auto 1fr;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-5);
  border-bottom: 1px solid var(--color-border-muted);
  font-size: var(--text-xs);
  transition: background var(--transition-fast);
}

.el-row:last-child { border-bottom: none; }
.el-row:hover { background: var(--color-surface-2); }

.el-icon { font-size: 0.7rem; }

.el-row--info     .el-icon { color: var(--color-info); }
.el-row--warn     .el-icon { color: var(--color-warning); }
.el-row--error    .el-icon { color: var(--color-error); }
.el-row--critical .el-icon { color: var(--color-error); }

.el-time {
  font-family: var(--font-mono);
  color: var(--color-text-faint);
  white-space: nowrap;
}

.el-node {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.el-msg {
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
