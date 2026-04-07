<template>
  <div class="login-root" :data-theme="theme">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <svg viewBox="0 0 48 48" width="48" height="48" fill="none">
          <circle cx="24" cy="24" r="23" stroke="#3b82f6" stroke-width="2"/>
          <circle cx="12" cy="24" r="5" fill="#22c55e"/>
          <circle cx="36" cy="24" r="5" fill="#22c55e"/>
          <circle cx="24" cy="12" r="5" fill="#3b82f6"/>
          <line x1="17" y1="24" x2="31" y2="24" stroke="#3b82f6" stroke-width="2"/>
          <line x1="24" y1="12" x2="12" y2="24" stroke="#3b82f6" stroke-width="2"/>
          <line x1="24" y1="12" x2="36" y2="24" stroke="#3b82f6" stroke-width="2"/>
        </svg>
        <div>
          <h1 class="login-title">Galera Orchestrator</h1>
          <p class="login-subtitle">v2 — MariaDB Cluster Management</p>
        </div>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="field">
          <label class="field-label">Логин</label>
          <InputText v-model="username" placeholder="admin" autocomplete="username"
            :class="{ 'p-invalid': error }" class="w-full" />
        </div>
        <div class="field">
          <label class="field-label">Пароль</label>
          <Password v-model="password" placeholder="••••••••" :feedback="false"
            toggle-mask input-class="w-full" class="w-full"
            :class="{ 'p-invalid': error }" autocomplete="current-password" />
        </div>

        <Message v-if="error" severity="error" :closable="false" class="mt-2">{{ error }}</Message>

        <Button type="submit" label="Войти" icon="pi pi-sign-in"
          class="w-full mt-3" :loading="loading" />
      </form>

      <p class="login-hint">Galera Orchestrator v2 · Self-hosted</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useAuthStore } from '@/stores/auth'
import { useClusterStore } from '@/stores/cluster'

const auth = useAuthStore()
const cluster = useClusterStore()
const router = useRouter()
const route = useRoute()

const username = ref('admin')
const password = ref('')
const loading = ref(false)
const error = ref('')
const theme = computed(() => cluster.prefs.theme || 'dark')

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = 'Введите логин и пароль'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Неверный логин или пароль'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-root {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-bg-primary);
  padding: 1rem;
}
.login-card {
  width: 100%; max-width: 400px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 2rem;
  box-shadow: var(--shadow-elevated);
  animation: slide-up 0.3s ease;
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.login-logo {
  display: flex; align-items: center; gap: 1rem;
  margin-bottom: 2rem;
}
.login-title   { font-size: 1.125rem; font-weight: 700; color: var(--color-text-primary); }
.login-subtitle{ font-size: 12px; color: var(--color-text-muted); }
.login-form    { display: flex; flex-direction: column; gap: 1rem; }
.field         { display: flex; flex-direction: column; gap: 0.375rem; }
.field-label   { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); }
.login-hint    { margin-top: 1.5rem; text-align: center; font-size: 11px; color: var(--color-text-muted); }
</style>
