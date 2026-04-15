<template>
  <div class="panel-toolbar">
    <div class="toolbar-left">
      <span class="toolbar-title">{{ title }}</span>
      <span v-if="fetchedAt" class="toolbar-ts">
        <i class="pi pi-clock" />
        {{ fetchedAt }}
      </span>
    </div>

    <div class="toolbar-right">
      <slot />

      <div class="auto-row">
        <ToggleSwitch
            :model-value="autoRefresh"
            @update:model-value="emit('toggle-auto', $event)"
        />
        <span class="auto-label">Auto</span>
      </div>

      <button
          class="toolbar-btn"
          :class="{ 'toolbar-btn--spinning': loading }"
          :disabled="loading"
          v-tooltip="'Refresh now'"
          @click="emit('refresh')"
      >
        <i class="pi pi-refresh" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import ToggleSwitch from 'primevue/toggleswitch'

defineProps<{
  title:       string
  loading?:    boolean
  fetchedAt?:  string | null
  autoRefresh: boolean
}>()

const emit = defineEmits<{
  refresh:       []
  'toggle-auto': [value: boolean]
}>()
</script>

<style scoped>
.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  gap: var(--space-3);
  flex-wrap: wrap;
  min-height: 52px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1 1 auto;
  min-width: 0;
}

.toolbar-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toolbar-ts {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  white-space: nowrap;
  flex-shrink: 0;
}

.toolbar-ts .pi {
  font-size: 0.6rem;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  flex: 0 0 auto;
  min-width: 0;
}

.auto-row {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.auto-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

.toolbar-btn {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--color-surface-3);
  border-color: var(--color-border-hover);
  color: var(--color-text);
}

.toolbar-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.toolbar-btn--spinning .pi {
  animation: spin 700ms linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

:deep(.p-toggleswitch) {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
}

:deep(.p-toggleswitch-slider) {
  flex-shrink: 0;
}
</style>
