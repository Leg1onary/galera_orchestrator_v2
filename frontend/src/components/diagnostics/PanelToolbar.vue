<!-- Переиспользуемый тулбар для всех диагностических панелей -->
<template>
  <div class="panel-toolbar">
    <div class="panel-toolbar-left">
      <span class="panel-title">{{ title }}</span>
      <span v-if="fetchedAt" class="fetched-at">Updated {{ fetchedAt }}</span>
    </div>
    <div class="panel-toolbar-right">
      <slot />
      <div class="auto-toggle">
        <ToggleSwitch
            :model-value="autoRefresh"
            size="small"
            v-tooltip="'Auto-refresh every 15s'"
            @update:model-value="emit('toggle-auto', $event)"
        />
        <span class="auto-label">Auto</span>
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
// BLOCKER fix: раздельные импорты
import Button       from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'

defineProps<{
  title:        string
  loading?:     boolean
  fetchedAt?:   string | null
  autoRefresh?: boolean
}>()

// MAJOR fix: toggle-auto передаёт новое значение
const emit = defineEmits<{
  refresh:       []
  'toggle-auto': [value: boolean]
}>()
</script>

<style scoped>
.panel-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-divider);
}
.panel-toolbar-left  { display: flex; align-items: baseline; gap: var(--space-3); }
.panel-toolbar-right { display: flex; align-items: center; gap: var(--space-2); }

/* MAJOR fix: заменяем Tailwind flex/gap/text-xs/text-muted-color */
.auto-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}
.auto-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.panel-title { font-size: var(--text-base); font-weight: 600; }
.fetched-at  { font-size: var(--text-xs); color: var(--color-text-faint); }
</style>