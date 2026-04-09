<template>
  <div class="doc-card" :class="`doc-card--${badge.toLowerCase()}`">
    <div class="doc-card__header">
      <span class="doc-card__title">{{ title }}</span>
      <Tag
          :value="BADGE_CONFIG[badge].label"
          :severity="BADGE_CONFIG[badge].severity as any"
          class="doc-card__badge"
      />
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
import { Tag, Button } from 'primevue'
import { BADGE_CONFIG, type DocBadge } from '@/data/docs'

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
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // clipboard blocked (non-https dev) — fall back silently
  }
}
</script>

<style scoped>
.doc-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: box-shadow var(--transition-interactive);
}
.doc-card:hover {
  box-shadow: var(--shadow-md);
}

/* Left accent bar by badge type */
.doc-card--danger  { border-left: 3px solid var(--color-error); }
.doc-card--warning { border-left: 3px solid var(--color-warning); }
.doc-card--safe    { border-left: 3px solid var(--color-success); }
.doc-card--action  { border-left: 3px solid var(--color-primary); }
.doc-card--info    { border-left: 3px solid var(--color-border); }

.doc-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.doc-card__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}
.doc-card__badge {
  flex-shrink: 0;
  font-size: var(--text-xs);
}

.doc-card__description {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.6;
  max-width: none; /* override base.css */
}

/* Code block */
.doc-card__code-block {
  background: var(--color-bg);
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
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  overflow-x: auto;
}

/* Note */
.doc-card__note {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--color-surface-offset);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
}
.doc-card__note-icon {
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--color-primary);
}
</style>