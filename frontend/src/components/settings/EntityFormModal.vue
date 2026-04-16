<!--
  Universal Create/Edit form modal.
  Parent passes field descriptors + initial values.
  No knowledge of specific entity — save logic lives in parent.
  Mount via v-if. On cancel → emit('cancel') → parent sets v-if=false.
-->
<template>
  <!-- Backdrop -->
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="emit('cancel')">
      <div class="modal" role="dialog" :aria-label="title">
        <!-- Header -->
        <div class="modal__header">
          <h2 class="modal__title">{{ title }}</h2>
          <button class="modal__close" @click="emit('cancel')" aria-label="Close">
            <i class="pi pi-times" />
          </button>
        </div>

        <!-- Body -->
        <form class="modal__body" @submit.prevent="submit">
          <div v-for="field in fields" :key="field.key" class="field-group">
            <label :for="field.key" class="field-label">
              {{ field.label }}
              <span v-if="field.required" class="required-mark">*</span>
            </label>

            <!-- text / password -->
            <InputText
              v-if="field.type === 'text' || field.type === 'password' || !field.type"
              :id="field.key"
              :type="field.type === 'password' ? 'password' : 'text'"
              :placeholder="field.placeholder ?? ''"
              :disabled="field.disabled"
              :model-value="form[field.key] as string"
              class="field-primevue"
              @update:model-value="form[field.key] = $event"
            />

            <!-- number -->
            <!-- fix #4: store null for empty number, not 0 -->
            <InputNumber
              v-else-if="field.type === 'number'"
              :id="field.key"
              :min="field.min"
              :max="field.max"
              :placeholder="field.placeholder ?? ''"
              :model-value="(form[field.key] as number | null)"
              :use-grouping="false"
              class="field-primevue"
              @update:model-value="form[field.key] = $event ?? null"
            />

            <!-- select -->
            <Select
              v-else-if="field.type === 'select'"
              :id="field.key"
              :model-value="form[field.key]"
              :options="field.options ?? []"
              option-label="label"
              option-value="value"
              :placeholder="field.placeholder ?? '— Select —'"
              class="field-primevue"
              @update:model-value="form[field.key] = $event"
            />

            <!-- toggle -->
            <div v-else-if="field.type === 'toggle'" class="toggle-row">
              <ToggleSwitch
                :id="field.key"
                :model-value="form[field.key] as boolean"
                @update:model-value="form[field.key] = $event"
              />
              <span v-if="field.toggleLabel" class="toggle-label">{{ field.toggleLabel }}</span>
            </div>

            <!-- textarea -->
            <Textarea
              v-else-if="field.type === 'textarea'"
              :id="field.key"
              :placeholder="field.placeholder ?? ''"
              :model-value="form[field.key] as string"
              :rows="3"
              class="field-primevue"
              auto-resize
              @update:model-value="form[field.key] = $event"
            />

            <p v-if="field.hint" class="field-hint">{{ field.hint }}</p>

            <!-- fix #15: inline required validation error -->
            <p v-if="validationErrors[field.key]" class="field-error">{{ validationErrors[field.key] }}</p>
          </div>

          <!-- API error -->
          <div v-if="apiError" class="modal__api-error">
            <i class="pi pi-exclamation-circle" />
            {{ apiError }}
          </div>

          <!-- Footer -->
          <div class="modal__footer">
            <Button
              type="button"
              label="Cancel"
              severity="secondary"
              :disabled="loading"
              @click="emit('cancel')"
            />
            <Button
              type="submit"
              :label="loading ? 'Saving…' : (submitLabel ?? 'Save')"
              :loading="loading"
              :disabled="loading"
            />
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { reactive, ref, watch, watchEffect } from 'vue'
import InputText   from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select      from 'primevue/select'
import ToggleSwitch from 'primevue/toggleswitch'
import Textarea    from 'primevue/textarea'
import Button      from 'primevue/button'

export type FormField = {
  key:          string
  label:        string
  type?:        'text' | 'password' | 'number' | 'select' | 'toggle' | 'textarea'
  required?:    boolean
  placeholder?: string
  disabled?:    boolean
  hint?:        string
  toggleLabel?: string
  options?:     { label: string; value: string | number | boolean | null }[]
  min?:         number
  max?:         number
}

const props = defineProps<{
  title:          string
  fields:         FormField[]
  initialValues?: Record<string, unknown>
  loading?:       boolean
  apiError?:      string | null
  submitLabel?:   string
}>()

const emit = defineEmits<{
  submit: [values: Record<string, unknown>]
  cancel: []
}>()

const form             = reactive<Record<string, unknown>>({})
const validationErrors = ref<Record<string, string>>({})

function initForm() {
  if (!props.fields || !Array.isArray(props.fields)) return
  for (const field of props.fields) {
    const initial = props.initialValues?.[field.key]
    form[field.key] = initial !== undefined && initial !== null
        ? initial
        : field.type === 'number' ? null
            : field.type === 'toggle' ? false
                : ''
  }
  validationErrors.value = {}
}

// Один watchEffect вместо initForm() + двух watch()
watchEffect(() => {
  if (props.fields?.length) initForm()
})

//const form             = reactive<Record<string, unknown>>({})
//const validationErrors = ref<Record<string, string>>({})

//function initForm() {
  // fix #3: re-init on fields change too
//  for (const field of props.fields) {
//    const initial = props.initialValues?.[field.key]
//    form[field.key] = initial !== undefined && initial !== null
//      ? initial
//      field.type === 'number'  ? null
//      : field.type === 'toggle'  ? false
//      : ''
//  }
//  validationErrors.value = {}
//}

// fix into function
//initForm()
// fix #3: watch both initialValues and fields
//watch(() => props.initialValues, initForm, { deep: true })
//watch(() => props.fields,        initForm, { deep: true })

function validate(): boolean {
  const errors: Record<string, string> = {}
  for (const field of props.fields) {
    if (!field.required) continue
    const val = form[field.key]
    if (val === null || val === undefined || val === '') {
      errors[field.key] = `${field.label} is required`
    }
  }
  validationErrors.value = errors
  return Object.keys(errors).length === 0
}

function submit() {
  if (!validate()) return
  emit('submit', { ...form })
}
</script>

<style scoped>
/* ── Backdrop ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: var(--space-4);
}

/* ── Modal box ── */
.modal {
  background: #1a1b22;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 480px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6), 0 4px 16px rgba(0,0,0,0.4);
  overflow: hidden;
  animation: modal-in 180ms cubic-bezier(0.16,1,0.3,1);
}

@keyframes modal-in {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to   { opacity: 1; transform: scale(1)   translateY(0);    }
}

/* ── Header ── */
.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.modal__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}
.modal__close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--color-text-faint);
  cursor: pointer;
  transition: all 150ms ease;
  font-size: 0.75rem;
}
.modal__close:hover {
  color: var(--color-text);
  background: rgba(255,255,255,0.06);
}

/* ── Body (form) ── */
.modal__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6);
  max-height: 70vh;
  overflow-y: auto;
}

/* ── Field group ── */
.field-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 3px;
}

.required-mark {
  color: #f87171;
  font-size: 0.75rem;
  line-height: 1;
}

/* ── PrimeVue field full-width ── */
.field-primevue {
  width: 100%;
}

/* ── Toggle switch row ── */
.toggle-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.toggle-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* ── Hint ── */
.field-hint {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  line-height: 1.5;
  max-width: none;
}

/* ── Field validation error ── */
.field-error {
  font-size: var(--text-xs);
  color: #f87171;
  line-height: 1.4;
}

/* ── API error banner ── */
.modal__api-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  color: #f87171;
}
.modal__api-error .pi { font-size: 0.85rem; flex-shrink: 0; }

/* ── Footer ── */
.modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-2);
  border-top: 1px solid rgba(255,255,255,0.05);
  margin-top: var(--space-2);
}

/* ── PrimeVue Textarea override (full-width) ── */
:deep(.p-textarea) {
  width: 100%;
  resize: vertical;
  min-height: 76px;
}

/* ── PrimeVue InputNumber full-width ── */
:deep(.field-primevue.p-inputnumber) {
  width: 100%;
}
:deep(.field-primevue.p-inputnumber .p-inputnumber-input) {
  width: 100%;
}

/* ── PrimeVue Select full-width ── */
:deep(.field-primevue.p-select) {
  width: 100%;
}
</style>
