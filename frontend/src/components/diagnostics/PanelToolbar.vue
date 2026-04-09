<!-- Переиспользуемый тулбар для всех диагностических панелей -->
<template>
  <div class="panel-toolbar">
    <div class="panel-toolbar-left">
      <span class="panel-title">{{ title }}</span>
      <span v-if="fetchedAt" class="fetched-at">Updated {{ fetchedAt }}</span>
    </div>
    <div class="panel-toolbar-right">
      <slot />
      <div class="flex items-center gap-1">
        <ToggleSwitch
            :model-value="autoRefresh"
            size="small"
            v-tooltip="'Auto-refresh every 15s'"
            @update:model-value="emit('toggle-auto')"
        />
        <span class="text-xs text-muted-color">Auto</span>
      </div>
      <Button
          icon="pi pi-refresh"
          text
          rounded
          size="small"
          :loading="loading"
          aria-label="Refresh"
          @click="emit('refresh')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, ToggleSwitch } from 'primevue'

defineProps<{
  title: string
  loading?: boolean
  fetchedAt?: string | null
  autoRefresh?: boolean
}>()

const emit = defineEmits<{ refresh: []; 'toggle-auto': [] }>()
</script>

<style scoped>
.panel-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-divider);
}
.panel-toolbar-left { display: flex; align-items: baseline; gap: var(--space-3); }
.panel-toolbar-right { display: flex; align-items: center; gap: var(--space-2); }
.panel-title { font-size: var(--text-base); font-weight: 600; }
.fetched-at { font-size: var(--text-xs); color: var(--color-text-faint); }
</style>