<!--
  Confirm deletion modal — нативная реализация без PrimeVue Dialog.
  Монтируется через v-if, закрывается через emit('cancel') / emit('confirm').
-->
<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="emit('cancel')">
      <!-- fix #12: role=alertdialog for destructive confirm -->
      <div class="modal" role="alertdialog" aria-labelledby="delete-modal-title" aria-modal="true">

        <!-- Header -->
        <div class="modal__header">
          <h2 id="delete-modal-title" class="modal__title">Confirm deletion</h2>
          <button class="modal__close" @click="emit('cancel')" aria-label="Close">
            <i class="pi pi-times" />
          </button>
        </div>

        <!-- Body -->
        <div class="modal__body">
          <div class="confirm-row">
            <i class="pi pi-exclamation-triangle confirm-icon" />
            <div class="confirm-text">
              <p class="confirm-entity">
                Delete <strong>{{ entityName }}</strong>?
              </p>
              <p v-if="warningText" class="confirm-warning">{{ warningText }}</p>
            </div>
          </div>
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
            type="button"
            :label="loading ? 'Deleting…' : 'Delete'"
            severity="danger"
            :icon="loading ? undefined : 'pi pi-trash'"
            :loading="loading"
            :disabled="loading"
            @click="emit('confirm')"
          />
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import Button from 'primevue/button'

defineProps<{
  entityName:   string
  warningText?: string
  loading?:     boolean
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()
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
  max-width: 380px;
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
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
  border: none; background: transparent;
  color: var(--color-text-faint);
  cursor: pointer;
  transition: all 150ms ease;
  font-size: 0.75rem;
}
.modal__close:hover {
  color: var(--color-text);
  background: rgba(255,255,255,0.06);
}

/* ── Body ── */
.modal__body {
  padding: var(--space-6);
}

.confirm-row {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.confirm-icon {
  font-size: 1.2rem;
  margin-top: 1px;
  flex-shrink: 0;
  color: #f87171;
}

.confirm-text    { display: flex; flex-direction: column; gap: var(--space-1); }
.confirm-entity  { font-size: var(--text-sm); color: var(--color-text); }
.confirm-warning { font-size: var(--text-sm); color: var(--color-text-muted); }

/* ── Footer ── */
.modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid rgba(255,255,255,0.05);
}
</style>
