<!--
  Универсальная форма для Create/Edit любой сущности.
  Принимает массив field-дескрипторов и начальные значения.
  Не знает о конкретной сущности — логика сохранения в parent.
-->
<template>
  <Dialog
      v-model:visible="visible"
      :header="title"
      modal
      :style="{ width: '460px' }"
      @hide="emit('cancel')"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div v-for="field in fields" :key="field.key" class="field-group">
        <label :for="field.key" class="field-label">
          {{ field.label }}
          <span v-if="field.required" class="text-error ml-0.5">*</span>
        </label>

        <!-- Text / password / number input -->
        <InputText
            v-if="field.type === 'text' || field.type === 'password' || !field.type"
            :id="field.key"
            v-model="form[field.key]"
            :type="field.type === 'password' ? 'password' : 'text'"
            :placeholder="field.placeholder ?? ''"
            :disabled="field.disabled"
            class="w-full"
            size="small"
        />

        <InputNumber
            v-else-if="field.type === 'number'"
            :id="field.key"
            v-model="form[field.key]"
            :min="field.min"
            :max="field.max"
            :placeholder="field.placeholder ?? ''"
            class="w-full"
            size="small"
        />

        <!-- Select/Dropdown -->
        <Select
            v-else-if="field.type === 'select'"
            :id="field.key"
            v-model="form[field.key]"
            :options="field.options ?? []"
            option-label="label"
            option-value="value"
            :placeholder="field.placeholder ?? 'Select…'"
            class="w-full"
            size="small"
        />

        <!-- Toggle -->
        <div v-else-if="field.type === 'toggle'" class="flex items-center gap-2">
          <ToggleSwitch
              :id="field.key"
              v-model="form[field.key]"
          />
          <span class="text-sm text-muted-color">{{ field.toggleLabel ?? '' }}</span>
        </div>

        <!-- Textarea -->
        <Textarea
            v-else-if="field.type === 'textarea'"
            :id="field.key"
            v-model="form[field.key]"
            :placeholder="field.placeholder ?? ''"
            rows="2"
            class="w-full"
            size="small"
        />

        <p v-if="field.hint" class="text-xs text-muted-color mt-1">{{ field.hint }}</p>
      </div>

      <!-- API error -->
      <div v-if="apiError" class="error-alert">
        <i class="pi pi-exclamation-circle" />
        {{ apiError }}
      </div>
    </form>

    <template #footer>
      <Button label="Cancel" text @click="emit('cancel')" />
      <Button
          :label="submitLabel"
          icon="pi pi-check"
          :loading="loading"
          @click="submit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import {
  Dialog, Button, InputText, InputNumber,
  Select, ToggleSwitch, Textarea,
} from 'primevue'

export interface FormField {
  key: string
  label: string
  type?: 'text' | 'password' | 'number' | 'select' | 'toggle' | 'textarea'
  required?: boolean
  disabled?: boolean
  placeholder?: string
  hint?: string
  min?: number
  max?: number
  options?: { label: string; value: unknown }[]
  toggleLabel?: string
}

const props = defineProps<{
  title: string
  fields: FormField[]
  initialValues?: Record<string, unknown>
  submitLabel?: string
  loading?: boolean
  apiError?: string | null
}>()

const emit = defineEmits<{
  submit: [values: Record<string, unknown>]
  cancel: []
}>()

const visible = ref(true)

// Инициализируем форму из initialValues или дефолтами
const form = reactive<Record<string, unknown>>({})

function initForm() {
  for (const field of props.fields) {
    form[field.key] = props.initialValues?.[field.key] ?? defaultFor(field)
  }
}
initForm()
watch(() => props.initialValues, initForm, { deep: true })

function defaultFor(f: FormField) {
  if (f.type === 'number') return f.min ?? 0
  if (f.type === 'toggle') return false
  return ''
}

function submit() {
  emit('submit', { ...form })
}
</script>

<style scoped>
.field-group { display: flex; flex-direction: column; gap: 0.25rem; }
.field-label { font-size: var(--text-sm); font-weight: 500; color: var(--color-text); }
.error-alert {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.625rem 0.75rem;
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}
.text-error { color: var(--color-error); }
</style>