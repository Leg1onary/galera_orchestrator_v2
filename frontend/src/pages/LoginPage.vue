<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router    = useRouter()
const authStore = useAuthStore()

const form    = reactive({ username: '', password: '' })
const error   = ref<string | null>(null)
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) return
  loading.value = true
  error.value   = null
  try {
    await authStore.login(form.username, form.password)
    router.push({ name: 'overview' })
  } catch {
    error.value = 'Invalid credentials'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card anim-fade-in">

      <!-- Logo -->
      <div class="login-logo">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <circle cx="16" cy="16" r="14" stroke="#2dd4bf" stroke-width="1.5" opacity="0.25"/>
          <circle cx="16" cy="16" r="9"  stroke="#2dd4bf" stroke-width="1.5" opacity="0.55"/>
          <circle cx="16" cy="16" r="4"  fill="#2dd4bf"/>
        </svg>
        <span class="login-product">Galera Orchestrator</span>
      </div>

      <h1 class="login-title">Sign in</h1>
      <p class="login-sub">Access your cluster control panel</p>

      <form class="login-form" @submit.prevent="submit" novalidate>
        <div class="field">
          <label class="field-label" for="login-username">Username</label>
          <InputText
            id="login-username"
            v-model="form.username"
            placeholder="admin"
            autocomplete="username"
            autofocus
            :disabled="loading"
            class="w-full"
          />
        </div>

        <div class="field">
          <label class="field-label" for="login-password">Password</label>
          <Password
            id="login-password"
            v-model="form.password"
            :feedback="false"
            toggle-mask
            placeholder="••••••••"
            autocomplete="current-password"
            :disabled="loading"
            class="w-full"
          />
        </div>

        <div v-if="error" class="login-error" role="alert">
          <i class="pi pi-exclamation-circle" />
          {{ error }}
        </div>

        <Button
          type="submit"
          label="Sign in"
          :loading="loading"
          :disabled="!form.username || !form.password || loading"
          class="w-full login-submit"
        />
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: var(--space-4);
}

.login-card {
  width: 100%;
  max-width: 360px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-1);
}

.login-product {
  font-size: var(--text-sm);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--color-text);
}

.login-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  margin-bottom: calc(-1 * var(--space-4));
}

.login-sub {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
}

.login-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-error);
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
}

.login-error i { font-size: 0.8rem; }

.login-submit {
  margin-top: var(--space-1);
  width: 100%;
  justify-content: center;
}

:deep(.p-password) { width: 100%; }
:deep(.p-password .p-inputtext) { width: 100%; }
</style>
