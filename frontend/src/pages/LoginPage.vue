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
  if (!username.value.trim() || !password.value) return
  error.value = null
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    const rawRedirect = route.query.redirect as string | undefined
    const redirect =
      rawRedirect && rawRedirect.startsWith('/') && !rawRedirect.startsWith('//')
        ? rawRedirect
        : '/'
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
    <!-- Background grid pattern -->
    <div class="login-bg" aria-hidden="true">
      <div class="login-bg-glow login-bg-glow--1" />
      <div class="login-bg-glow login-bg-glow--2" />
      <svg class="login-bg-grid" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(45,212,191,0.05)" stroke-width="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
    </div>

    <div class="login-card anim-fade-in">
      <!-- Logo -->
      <div class="login-logo">
        <svg class="login-logo-mark" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="20,3 37,12 37,28 20,37 3,28 3,12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <polygon points="20,9 31,15.5 31,24.5 20,31 9,24.5 9,15.5" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-width="1" stroke-linejoin="round"/>
          <circle cx="20" cy="20" r="3.5" fill="currentColor"/>
        </svg>
        <div class="login-logo-text">
          <span class="login-title">Galera Orchestrator</span>
          <span class="login-subtitle">MariaDB Galera Cluster</span>
        </div>
      </div>

      <!-- Divider -->
      <div class="login-divider" />

      <!-- Form -->
      <form class="login-form" @submit.prevent="submit" novalidate>
        <div class="field">
          <label for="username">Логин</label>
          <InputText
              id="username"
              v-model="username"
              autocomplete="username"
              :disabled="loading"
              placeholder="admin"
              fluid
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
              fluid
          />
        </div>

        <Transition name="error-slide">
          <div v-if="error" class="login-error">
            <i class="pi pi-exclamation-triangle" />
            {{ error }}
          </div>
        </Transition>

        <Button
            type="submit"
            :loading="loading"
            label="Войти"
            fluid
            class="login-btn"
        />
      </form>
    </div>
  </div>
</template>

<style scoped>
/* ── Page ── */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  position: relative;
  overflow: hidden;
}

/* ── Background ── */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.login-bg-grid {
  width: 100%; height: 100%;
  position: absolute; inset: 0;
}

.login-bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
}

.login-bg-glow--1 {
  width: 600px; height: 400px;
  top: -100px; left: -100px;
  background: radial-gradient(circle, rgba(45,212,191,0.07) 0%, transparent 70%);
}

.login-bg-glow--2 {
  width: 500px; height: 400px;
  bottom: -80px; right: -60px;
  background: radial-gradient(circle, rgba(56,189,248,0.05) 0%, transparent 70%);
}

/* ── Card ── */
.login-card {
  position: relative;
  z-index: 10;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-8) var(--space-8);
  width: 100%;
  max-width: 360px;
  box-shadow:
    0 0 0 1px rgba(45,212,191,0.06),
    0 20px 60px rgba(0,0,0,0.5),
    0 4px 16px rgba(0,0,0,0.3);
}

/* Subtle top glow on card */
.login-card::before {
  content: '';
  position: absolute;
  top: 0; left: 20px; right: 20px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(45,212,191,0.5), transparent);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

/* ── Logo ── */
.login-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.login-logo-mark {
  width: 36px;
  height: 36px;
  color: var(--color-primary);
  filter: drop-shadow(0 0 10px rgba(45,212,191,0.5));
  flex-shrink: 0;
}

.login-logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.login-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.2;
}

.login-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* ── Divider ── */
.login-divider {
  height: 1px;
  background: var(--color-border-muted);
  margin-bottom: var(--space-6);
}

/* ── Form ── */
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

label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-muted);
}

/* PrimeVue fluid inputs */
:deep(.p-inputtext)      { width: 100%; }
:deep(.p-password)       { width: 100%; }
:deep(.p-password input) { width: 100%; }

/* ── Error ── */
.login-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.login-error i { font-size: 0.875rem; flex-shrink: 0; }

/* ── Login button ── */
:deep(.login-btn) {
  width: 100%;
  font-weight: 600;
  font-size: var(--text-sm);
  padding: var(--space-3) var(--space-4);
  background: rgba(45,212,191,0.12) !important;
  border: 1px solid rgba(45,212,191,0.35) !important;
  color: var(--color-primary) !important;
  border-radius: var(--radius-md) !important;
  transition: all var(--transition-normal) !important;
  box-shadow: none !important;
}

:deep(.login-btn:hover) {
  background: rgba(45,212,191,0.2) !important;
  border-color: rgba(45,212,191,0.55) !important;
  color: #5eead4 !important;
  box-shadow: 0 0 16px rgba(45,212,191,0.15) !important;
}

/* ── Error slide transition ── */
.error-slide-enter-active,
.error-slide-leave-active {
  transition: all 200ms var(--ease-out-expo);
}
.error-slide-enter-from,
.error-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
