<!--
  Универсальная форма для Create/Edit любой сущности.
  Принимает массив field-дескрипторов и начальные значения.
  Не знает о конкретной сущности — логика сохранения в parent.
  Монтировать через v-if. При cancel → emit('cancel') → родитель v-if=false.
-->
<template>
  <Dialog
      v-model:visible="visible"
      :header="title"
      modal
      :pt="{ root: { style: 'width: 460px' } }"
      @hide="emit('cancel')"
  >
    <!-- MINOR fix: только @submit.prevent, кнопка type=submit -->
    <form class="form-body" @submit.prevent="submit">
      <div v-for="field in fields" :key="field.key" class="field-group">
        <label :for="field.key" class="field-label">
          {{ field.label }}
          <!-- MAJOR fix: utility text-error ml-0.5 → scoped класс -->
          <span v-if="field.required" class="required-mark">*</span>
        </label>

        <InputText
            v-if="field.type === 'text' || field.type === 'password' || !field.type"
            :id="field.key"
            :model-value="form[field.key] as string"
            :type="field.type === 'password' ? 'password' : 'text'"
            :placeholder="field.placeholder ?? ''"
            :disabled="field.disabled"
            class="field-input"
            size="small"
            @update:model-value="form[field.key] = $event"
        />

        <InputNumber
            v-else-if="field.type === 'number'"
            :id="field.key"
            :model-value="form[field.key] as number"
            :min="field.min"
            :max="field.max"
            :placeholder="field.placeholder ?? ''"
            class="field-input"
            size="small"
            @update:model-value="form[field.key] = $event"
        />

        <Select
            v-else-if="field.type === 'select'"
            :id="field.key"
            v-model="form[field.key]"
            :options="field.options ?? []"
            option-label="label"
            option-value="value"
            :placeholder="field.placeholder ?? 'Select…'"
            class="field-input"
            size="small"
        />

        <!-- MAJOR fix: utility flex items-center gap-2 → scoped -->
        <div v-else-if="field.type === 'toggle'" class="toggle-row">
          <ToggleSwitch
              :id="field.key"
              :model-value="form[field.key] as boolean"
              @update:model-value="form[field.key] = $event"
          />
          <!-- MAJOR fix: text-sm text-muted-color → scoped -->
          <span v-if="field.toggleLabel" class="toggle-label">{{ field.toggleLabel }}</span>
        </div>

        <Textarea
            v-else-if="field.type === 'textarea'"
            :id="field.key"
            :model-value="form[field.key] as string"
            :placeholder="field.placeholder ?? ''"
            rows="2"
            class="field-input"
            size="small"
            @update:model-value="form[field.key] = $event"
        />

        <!-- MAJOR fix: text-xs text-muted-color mt-1 → scoped -->
        <p v-if="field.hint" class="field-hint">{{ field.hint }}</p>
      </div>

      <div v-if="apiError" class="error-alert">
        <i class="pi pi-exclamation-circle" />
        {{ apiError }}
      </div>
    </form>

    <template #footer>
      <Button label="Cancel" text @click="emit('cancel')" />
      <!-- MINOR fix: type=submit — форма обрабатывает через @submit.prevent -->
      <Button
          :label="submitLabel ?? 'Save'"
          icon="pi pi-check"
          type="submit"
          :loading="loading"
          @click="submit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
// BLOCKER fix: раздельные импорты
import Dialog       from 'primevue/dialog'
import Button       from 'primevue/button'
import InputText    from 'primevue/inputtext'
import InputNumber  from 'primevue/inputnumber'
import Select       from 'primevue/select'
import ToggleSwitch from 'primevue/toggleswitch'
import Textarea     from 'primevue/textarea'

export interface FormField {
  key:          string
  label:        string
  type?:        'text' | 'password' | 'number' | 'select' | 'toggle' | 'textarea'
  required?:    boolean
  disabled?:    boolean
  placeholder?: string
  hint?:        string
  min?:         number
  max?:         number
  options?:     { label: string; value: unknown }[]
  toggleLabel?: string
}

const props = defineProps<{
  title:          string
  fields:         FormField[]
  initialValues?: Record<string, unknown>
  submitLabel?:   string
  loading?:       boolean
  apiError?:      string | null
}>()

const emit = defineEmits<{
  submit: [values: Record<string, unknown>]
  cancel: []
}>()

const visible = ref(true)

const form = reactive<Record<string, unknown>>({})

function initForm() {
  for (const field of props.fields) {
    form[field.key] = props.initialValues?.[field.key] ?? defaultFor(field)
  }
}
initForm()

// MAJOR fix: не сбрасываем форму если она уже dirty.
// Инициализируем только при явной смене initialValues (например, смена редактируемой записи).
// { immediate: false } — при монтировании уже вызван initForm() выше.
watch(
    () => props.initialValues,
    (next, prev) => {
      // Сбрасываем только если поменялась запись (изменился id или весь объект null→object)
      const prevId = (prev as any)?.id
      const nextId = (next as any)?.id
      if (nextId !== prevId) initForm()
    },
    { deep: false },  // shallow — следим только за сменой ссылки/id
)

function defaultFor(f: FormField): unknown {
  if (f.type === 'number') return f.min ?? 0
  if (f.type === 'toggle') return false
  // MAJOR fix: select должен возвращать null чтобы показывал placeholder
  if (f.type === 'select') return null
  return ''
}

function submit() {
  emit('submit', { ...form })
}
</script>

<style scoped>
/* MAJOR fix: все utility классы → scoped */
.form-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.field-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
}
/* MINOR fix: required marker через класс */
.required-mark {
  color: var(--color-error);
  margin-left: 2px;
}
/* MAJOR fix: w-full → class на инпутах */
.field-input { width: 100%; }

.toggle-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.toggle-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.field-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}
</style>