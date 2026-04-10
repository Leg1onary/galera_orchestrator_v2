<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import ProgressSpinner from 'primevue/progressspinner'
import { formatRelative } from '@/utils/time'
import type { EventLogEntry } from '@/stores/events'

const props = defineProps<{
  entries: EventLogEntry[]
  loading: boolean
}>()

const listEl = ref<HTMLElement | null>(null)

// Авто-скролл вверх при новом событии (список — новые сверху)
watch(
    () => props.entries.length,
    async () => {
      await nextTick()
      listEl.value?.scrollTo({ top: 0, behavior: 'smooth' })
    },
)

// ТЗ 10.5: лимит применяется на уровне eventsStore (event_log_limit из system_settings).
// Компонент отображает всё что пришло — caller отвечает за обрезку.
const levelClass: Record<string, string> = {
  INFO:  'info',
  WARN:  'warn',
  ERROR: 'error',
}
</script>

<template>
  <div class="event-log-wrap">
    <div v-if="loading" class="log-state">
      <ProgressSpinner style="width: 24px; height: 24px" />
    </div>
    <div v-else-if="!entries.length" class="log-state log-empty">
      Нет событий
    </div>
    <ul v-else ref="listEl" class="log-list">
      <li
          v-for="e in entries"
          :key="e.id"
          :class="['log-entry', levelClass[e.level] ?? 'info']"
      >
        <span class="log-ts">{{ formatRelative(e.ts) }}</span>
        <span class="log-level">{{ e.level }}</span>
        <span class="log-source">{{ e.source }}</span>
        <span class="log-msg">{{ e.message }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.event-log-wrap {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.log-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.log-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 320px;
  overflow-y: auto;
}

.log-entry {
  display: grid;
  grid-template-columns: 70px 46px minmax(80px, 100px) 1fr;
  align-items: baseline;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-xs);
  border-bottom: 1px solid var(--color-border);
  font-variant-numeric: tabular-nums;
}

.log-entry.warn  { background: var(--color-warning-highlight); }
.log-entry.error { background: var(--color-error-highlight); }

.log-ts     { color: var(--color-text-muted); }
.log-source { color: var(--color-text-muted); }
.log-msg    { color: var(--color-text); }

.log-level { font-weight: 600; }
.log-entry.info  .log-level { color: var(--color-blue); }
.log-entry.warn  .log-level { color: var(--color-gold); }
.log-entry.error .log-level { color: var(--color-notification); }
</style>
