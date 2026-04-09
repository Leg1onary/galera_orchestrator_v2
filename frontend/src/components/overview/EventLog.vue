<!-- src/components/overview/EventLog.vue -->
<!-- ТЗ 10.5: список событий, авто-скролл вниз при новых -->
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { EventLogEntry } from '@/stores/events'

const props = defineProps<{ entries: EventLogEntry[]; loading: boolean }>()
const listEl = ref<HTMLElement | null>(null)

// Авто-скролл при появлении нового события (prepend — скролл вверх)
watch(() => props.entries.length, async () => {
  await nextTick()
  listEl.value?.scrollTo({ top: 0, behavior: 'smooth' })
})

const levelClass: Record<string, string> = { INFO: 'info', WARN: 'warn', ERROR: 'error' }
</script>
<template>
  <div class="event-log-wrap">
    <div v-if="loading" class="log-loading">
      <ProgressSpinner style="width:24px;height:24px" />
    </div>
    <div v-else-if="!entries.length" class="log-empty">
      Нет событий
    </div>
    <ul v-else ref="listEl" class="log-list">
      <li v-for="e in entries" :key="e.id" :class="['log-entry', levelClass[e.level]]">
        <span class="log-ts">{{ new Date(e.ts).toLocaleTimeString() }}</span>
        <span class="log-level">{{ e.level }}</span>
        <span class="log-source">{{ e.source }}</span>
        <span class="log-msg">{{ e.message }}</span>
      </li>
    </ul>
  </div>
</template>
<style scoped>
.event-log-wrap { background: var(--surface-card); border: 1px solid var(--surface-border); border-radius: 8px; overflow: hidden; }
.log-loading, .log-empty { display:flex; align-items:center; justify-content:center; padding:2rem; color:var(--text-color-secondary); font-size:0.875rem; }
.log-list { list-style:none; margin:0; padding:0; max-height:320px; overflow-y:auto; }
.log-entry { display:grid; grid-template-columns:70px 46px 90px 1fr; align-items:baseline; gap:0.5rem; padding:4px 12px; font-size:0.78rem; border-bottom:1px solid var(--surface-border); font-variant-numeric:tabular-nums; }
.log-entry.warn  { background: color-mix(in srgb, #f59e0b 6%, transparent); }
.log-entry.error { background: color-mix(in srgb, #ef4444 7%, transparent); }
.log-ts { color:var(--text-color-secondary); }
.log-level { font-weight:600; }
.log-entry.info  .log-level { color:var(--blue-500); }
.log-entry.warn  .log-level { color:var(--yellow-600); }
.log-entry.error .log-level { color:var(--red-500); }
.log-source { color:var(--text-color-secondary); }
.log-msg { color:var(--text-color); }
</style>