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
        <span class="doc-card__code-lang">{{ props.codeLang ?? 'bash' }}</span>
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
import { type DocBadge } from '@/data/docs'

const props = defineProps<{
  title: string
  badge: DocBadge
  description: string
  code?: string
  codeLang?: string
  note?: string
}>()

const copied = ref(false)

function legacyCopy(text: string) {
  try {
    const el = document.createElement('textarea')
    el.value = text
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand?.('copy')
    document.body.removeChild(el)
  } catch {
    // no-op
  }
}

async function handleCopy() {
  if (!props.code) return
  const text = props.code
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      legacyCopy(text)
    }
  } else {
    legacyCopy(text)
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<style scoped>
.doc-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  transition: box-shadow 200ms ease, border-color 200ms ease;
  box-shadow: var(--shadow-sm);
}
.doc-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-hover);
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
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  line-height: 1;
}

.doc-card__badge--safe {
  background: var(--color-synced-dim);
  color: var(--color-synced);
  border: 1px solid var(--color-synced-glow);
}
.doc-card__badge--danger {
  background: var(--color-offline-dim);
  color: var(--color-offline);
  border: 1px solid var(--color-offline-glow);
}
.doc-card__badge--warning {
  background: var(--color-readonly-dim);
  color: var(--color-readonly);
  border: 1px solid rgba(251,191,36,0.25);
}
.doc-card__badge--action {
  background: var(--color-primary-dim);
  color: var(--color-primary);
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
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.doc-card__code-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-1) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-4);
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
  color: var(--color-info);
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
  background: var(--color-primary-dim);
  border: 1px solid var(--color-border-hover);
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
