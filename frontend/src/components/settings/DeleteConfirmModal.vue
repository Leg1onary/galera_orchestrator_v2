<template>
  <Dialog
      v-model:visible="visible"
      header="Confirm deletion"
      modal
      :style="{ width: '380px' }"
      @hide="emit('cancel')"
  >
    <div class="flex gap-3 items-start">
      <i class="pi pi-exclamation-triangle text-xl mt-0.5" style="color: var(--color-error)" />
      <div>
        <p class="text-sm text-color mb-1">
          Delete <strong>{{ entityName }}</strong>?
        </p>
        <p class="text-sm text-muted-color">{{ warningText }}</p>
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
import { Dialog, Button } from 'primevue'

defineProps<{
  entityName: string
  warningText?: string
  loading?: boolean
}>()
const emit = defineEmits<{ confirm: []; cancel: [] }>()
const visible = ref(true)
</script>