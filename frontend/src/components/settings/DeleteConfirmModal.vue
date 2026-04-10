<!--
  Использование: монтировать через v-if.
  При cancel/confirm — emit, родитель размонтирует через v-if.
  visible=true intentionally — Dialog показывается сразу при монтировании.
-->
<template>
  <Dialog
      v-model:visible="visible"
      header="Confirm deletion"
      modal
      :pt="{ root: { style: 'width: 380px' } }"
      @hide="emit('cancel')"
  >
    <!-- MAJOR fix: utility классы → scoped -->
    <div class="confirm-body">
      <i class="pi pi-exclamation-triangle confirm-icon" />
      <div class="confirm-text">
        <p class="confirm-entity">
          Delete <strong>{{ entityName }}</strong>?
        </p>
        <!-- MINOR fix: v-if чтобы не рендерить пустой p -->
        <p v-if="warningText" class="confirm-warning">{{ warningText }}</p>
      </div>
    </div>

    <template #footer>
      <Button label="Cancel" text @click="emit('cancel')" />
      <Button
          label="Delete"
          icon="pi pi-trash"
          severity="danger"
          :loading="loading"
          @click="emit('confirm')"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
// BLOCKER fix: раздельные импорты
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

defineProps<{
  entityName:   string
  warningText?: string
  loading?:     boolean
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()

// visible=true: компонент монтируется уже открытым.
// Закрытие через @hide → emit('cancel') → родитель делает v-if=false.
const visible = ref(true)
</script>

<style scoped>
/* MAJOR fix: utility классы → scoped */
.confirm-body {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}
.confirm-icon {
  font-size: var(--text-xl);
  margin-top: 2px;
  flex-shrink: 0;
  /* MINOR fix: цвет через класс, не inline style */
  color: var(--color-error);
}
.confirm-text    { display: flex; flex-direction: column; gap: var(--space-1); }
.confirm-entity  { font-size: var(--text-sm); color: var(--color-text); }
.confirm-warning { font-size: var(--text-sm); color: var(--color-text-muted); }
</style>