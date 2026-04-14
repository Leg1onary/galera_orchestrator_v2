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
          <button type="button" class="btn-cancel" @click="emit('cancel')" :disabled="loading">
            Cancel
          </button>
          <button type="button" class="btn-delete" @click="emit('confirm')" :disabled="loading">
            <i v-if="loading" class="pi pi-spin pi-spinner" style="font-size:0.85rem" />
            <i v-else class="pi pi-trash" style="font-size:0.85rem" />
            {{ loading ? 'Deleting…' : 'Delete' }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
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

.btn-cancel {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm); font-weight: 500; font-family: inherit;
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

.btn-delete {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm); font-weight: 600; font-family: inherit;
  color: #fff;
  background: rgba(248,113,113,0.15);
  border: 1px solid rgba(248,113,113,0.3);
  cursor: pointer;
  transition: all 150ms ease;
}
.btn-delete:hover:not(:disabled) {
  background: rgba(248,113,113,0.25);
  border-color: rgba(248,113,113,0.5);
  color: #fca5a5;
}
.btn-delete:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
