<template>
  <div class="doc-card">
    <div class="doc-card__header">
      <span class="doc-card__title">{{ title }}</span>
      <span class="doc-card__badge" :class="`doc-card__badge--${badge.toLowerCase()}`">
        {{ badge }}
      </span>
    </div>

    <p class="doc-card__description">{{ description }}</p>

    <div v-if="props.code" class="doc-card__code-block">
      <div class="doc-card__code-toolbar">
        <span class="doc-card__code-lang">bash</span>
        <Button
            :icon="copied ? 'pi pi-check' : 'pi pi-copy'"
            text
            rounded
            size="small"
            class="doc-card__copy-btn"
            :class="{ 'doc-card__copy-btn--done': copied }"
            v-tooltip="copied ? 'Скопировано!' : 'Скопировать'"
            @click="handleCopy"
        />
      </div>
      <pre class="doc-card__code"><code>{{ props.code }}</code></pre>
    </div>

    <div v-if="props.note" class="doc-card__note">
      <i class="pi pi-info-circle doc-card__note-icon" />
      <span>{{ props.note }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Button } from 'primevue'
import { type DocBadge } from '@/data/docs'

const props = defineProps<{
  title: string
  badge: DocBadge
  description: string
  code?: string
  note?: string
}>()

const copied = ref(false)

async function handleCopy() {
  if (!props.code) return
  try {
    await navigator.clipboard.writeText(props.code)
  } catch {
    const el = document.createElement('textarea')
    el.value = props.code
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<style scoped>
.doc-card {
  background: var(--color-surface);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  transition: box-shadow 200ms ease, border-color 200ms ease, transform 200ms ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25), 0 1px 2px rgba(0,0,0,0.3);
}
.doc-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.4), 0 2px 6px rgba(0,0,0,0.3);
  border-color: rgba(45,212,191,0.15);
  transform: translateY(-1px);
}

/* ── Header ── */
.doc-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.doc-card__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}

/* ── Badge ── */
.doc-card__badge {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  line-height: 1;
}

.doc-card__badge--safe {
  background: rgba(68,215,128,0.12);
  color: #4ade80;
  border: 1px solid rgba(68,215,128,0.25);
}
.doc-card__badge--danger {
  background: rgba(248,113,113,0.12);
  color: #f87171;
  border: 1px solid rgba(248,113,113,0.25);
}
.doc-card__badge--warning {
  background: rgba(251,191,36,0.12);
  color: #fbbf24;
  border: 1px solid rgba(251,191,36,0.25);
}
.doc-card__badge--action {
  background: rgba(45,212,191,0.1);
  color: #2dd4bf;
  border: 1px solid rgba(45,212,191,0.22);
}
.doc-card__badge--info {
  background: rgba(148,163,184,0.1);
  color: #94a3b8;
  border: 1px solid rgba(148,163,184,0.2);
}

/* ── Description ── */
.doc-card__description {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.6;
  max-width: none;
}

/* ── Code block ── */
.doc-card__code-block {
  background: #0d0e12;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.doc-card__code-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-1) var(--space-3);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  background: rgba(255,255,255,0.02);
}
.doc-card__code-lang {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-family: var(--font-mono, monospace);
}
.doc-card__copy-btn {
  color: var(--color-text-faint) !important;
}
.doc-card__copy-btn--done {
  color: var(--color-success) !important;
}
.doc-card__code {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-xs);
  font-family: var(--font-mono, 'JetBrains Mono', 'Fira Code', monospace);
  color: #a5f3fc;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  overflow-x: auto;
}

/* ── Note ── */
.doc-card__note {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: rgba(45,212,191,0.04);
  border: 1px solid rgba(45,212,191,0.1);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  line-height: 1.5;
}
.doc-card__note-icon {
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--color-primary);
  font-size: 0.75rem;
}
</style>
