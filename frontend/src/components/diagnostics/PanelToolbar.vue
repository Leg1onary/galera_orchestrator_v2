<template>
  <div class="panel-toolbar">
    <div class="toolbar-left">
      <h2 class="toolbar-title">{{ title }}</h2>
      <span v-if="fetchedAt" class="toolbar-ts">
        <i class="pi pi-clock" />
        {{ fetchedAt }}
      </span>
    </div>

    <div class="toolbar-right">
      <!-- slot: node select, filters, etc. -->
      <slot />

      <!-- auto-refresh toggle -->
      <div class="auto-row">
        <ToggleSwitch
            :model-value="autoRefresh"
            size="small"
            @update:model-value="emit('toggle-auto', $event)"
        />
        <span class="auto-label">Auto</span>
      </div>

      <!-- manual refresh -->
      <Button
          icon="pi pi-refresh"
          text
          rounded
          size="small"
          :loading="loading"
          v-tooltip="'Refresh now'"
          @click="emit('refresh')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import Button       from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'

defineProps<{
  title:       string
  loading?:    boolean
  fetchedAt?:  string | null
  autoRefresh: boolean
}>()

const emit = defineEmits<{
  refresh:      []
  'toggle-auto': [value: boolean]
}>()
</script>

<style scoped>
.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-offset);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  gap: var(--space-4);
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.toolbar-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}
.toolbar-ts {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  font-variant-numeric: tabular-nums;
}
.toolbar-ts .pi { font-size: 0.65rem; }

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.auto-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.auto-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: 500;
}
</style>
