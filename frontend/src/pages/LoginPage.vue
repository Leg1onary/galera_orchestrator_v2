<!-- ТЗ раздел 17: форма логина, JWT в httpOnly cookie, редирект после логина -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const error = ref<string | null>(null)
const loading = ref(false)

async function submit() {
  error.value = null
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: any) {
    error.value =
        e?.response?.status === 401
            ? 'Неверный логин или пароль'
            : 'Ошибка сервера. Попробуйте позже.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <span class="logo-icon">⬡</span>
        <h1>Galera Orchestrator</h1>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <div class="field">
          <label for="username">Логин</label>
          <InputText
              id="username"
              v-model="username"
              autocomplete="username"
              :disabled="loading"
              placeholder="admin"
          />
        </div>

        <div class="field">
          <label for="password">Пароль</label>
          <Password
              id="password"
              v-model="password"
              :feedback="false"
              toggle-mask
              autocomplete="current-password"
              :disabled="loading"
              input-class="w-full"
          />
        </div>

        <Message v-if="error" severity="error" :closable="false">
          {{ error }}
        </Message>

        <Button
            type="submit"
            label="Войти"
            class="w-full"
            :loading="loading"
        />
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f1117;   /* ← хардкод вместо --p-surface-ground */
}

.login-card {
  background: #1a1f2e;
  border: 1px solid #2a3040;
  border-radius: 12px;
  padding: 2.5rem 2rem;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 8px 32px rgb(0 0 0 / 0.4);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.logo-icon {
  font-size: 1.75rem;
  color: #4ade80;
}

h1 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: #e2e8f0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #94a3b8;
}

/* PrimeVue InputText на всю ширину */
:deep(.p-inputtext) {
  width: 100%;
}

/* PrimeVue Password wrapper на всю ширину */
:deep(.p-password) {
  width: 100%;
}
:deep(.p-password input) {
  width: 100%;
}
</style>