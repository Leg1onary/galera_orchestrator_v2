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
            <input
              v-if="field.type === 'text' || field.type === 'password' || !field.type"
              :id="field.key"
              :type="field.type === 'password' ? 'password' : 'text'"
              :placeholder="field.placeholder ?? ''"
              :disabled="field.disabled"
              :value="form[field.key] as string"
              class="field-input"
              @input="form[field.key] = ($event.target as HTMLInputElement).value"
            />

            <!-- number -->
            <input
              v-else-if="field.type === 'number'"
              :id="field.key"
              type="number"
              :min="field.min"
              :max="field.max"
              :placeholder="field.placeholder ?? ''"
              :value="form[field.key] as number"
              class="field-input"
              @input="form[field.key] = Number(($event.target as HTMLInputElement).value)"
            />

            <!-- select -->
            <select
              v-else-if="field.type === 'select'"
              :id="field.key"
              v-model="form[field.key]"
              class="field-input field-input--select"
            >
              <option v-if="field.placeholder" value="" disabled>{{ field.placeholder }}</option>
              <option
                v-for="opt in field.options ?? []"
                :key="opt.value"
                :value="opt.value"
              >{{ opt.label }}</option>
            </select>

            <!-- toggle -->
            <div v-else-if="field.type === 'toggle'" class="toggle-row">
              <label class="toggle-switch">
                <input
                  type="checkbox"
                  :id="field.key"
                  :checked="form[field.key] as boolean"
                  @change="form[field.key] = ($event.target as HTMLInputElement).checked"
                />
                <span class="toggle-thumb" />
              </label>
              <span v-if="field.toggleLabel" class="toggle-label">{{ field.toggleLabel }}</span>
            </div>

            <!-- textarea -->
            <textarea
              v-else-if="field.type === 'textarea'"
              :id="field.key"
              :placeholder="field.placeholder ?? ''"
              :value="form[field.key] as string"
              rows="3"
              class="field-input field-input--textarea"
              @input="form[field.key] = ($event.target as HTMLTextAreaElement).value"
            />

            <p v-if="field.hint" class="field-hint">{{ field.hint }}</p>
          </div>

          <!-- API error -->
          <div v-if="apiError" class="modal__api-error">
            <i class="pi pi-exclamation-circle" />
            {{ apiError }}
          </div>

          <!-- Footer -->
          <div class="modal__footer">
            <button type="button" class="btn-cancel" @click="emit('cancel')" :disabled="loading">Cancel</button>
            <button type="submit" class="btn-submit" :disabled="loading">
              <i v-if="loading" class="pi pi-spin pi-spinner" style="font-size:0.85rem" />
              {{ loading ? 'Saving…' : submitLabel }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

export type FormField = {
  key:          string
  label:        string
  type?:        'text' | 'password' | 'number' | 'select' | 'toggle' | 'textarea'
  required?:    boolean
  placeholder?: string
  disabled?:    boolean
  hint?:        string
  toggleLabel?: string
  options?:     { label: string; value: string | number | boolean }[]
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

const form = reactive<Record<string, unknown>>({})

function initForm() {
  for (const field of props.fields) {
    form[field.key] = props.initialValues?.[field.key] ?? (
      field.type === 'number'  ? 0 :
      field.type === 'toggle'  ? false :
      ''
    )
  }
}

initForm()
watch(() => props.initialValues, initForm, { deep: true })

function submit() {
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

/* ── Inputs ── */
.field-input {
  width: 100%;
  background: #0f1015;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-family: inherit;
  padding: var(--space-2) var(--space-3);
  line-height: 1.5;
  outline: none;
  transition: border-color 150ms ease, box-shadow 150ms ease;
  -webkit-appearance: none;
  appearance: none;
  box-sizing: border-box;
}
.field-input::placeholder { color: var(--color-text-faint); }
.field-input:focus {
  border-color: rgba(45,212,191,0.45);
  box-shadow: 0 0 0 3px rgba(45,212,191,0.08);
}
.field-input:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.field-input--select {
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' fill='none'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236b7280' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 2rem;
}
select option { background: #1a1b22; color: var(--color-text); }

.field-input--textarea {
  resize: vertical;
  min-height: 76px;
  line-height: 1.6;
}

/* ── Toggle switch ── */
.toggle-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  cursor: pointer;
}
.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}
.toggle-thumb {
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0.1);
  border-radius: var(--radius-full);
  transition: background 150ms ease;
}
.toggle-thumb::before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform 150ms ease;
}
.toggle-switch input:checked + .toggle-thumb {
  background: rgba(45,212,191,0.8);
}
.toggle-switch input:checked + .toggle-thumb::before {
  transform: translateX(18px);
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

.btn-cancel {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  font-family: inherit;
  color: var(--color-text-muted);
  background: transparent;
  border: 1px solid rgba(255,255,255,0.08);
  cursor: pointer;
  transition: all 150ms ease;
}
.btn-cancel:hover:not(:disabled) {
  color: var(--color-text);
  background: rgba(255,255,255,0.05);
}
.btn-cancel:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-submit {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  font-family: inherit;
  color: #0d1117;
  background: #2dd4bf;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}
.btn-submit:hover:not(:disabled) {
  background: #5eead4;
}
.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
