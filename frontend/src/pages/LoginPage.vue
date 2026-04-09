<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo / branding -->
      <div class="login-header">
        <div class="login-logo" aria-hidden="true">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="40" rx="8" fill="#1e2436"/>
            <!-- Simplified Galera cluster icon: three connected nodes -->
            <circle cx="20" cy="10" r="4" fill="#38b2ac"/>
            <circle cx="10" cy="28" r="4" fill="#38b2ac"/>
            <circle cx="30" cy="28" r="4" fill="#38b2ac"/>
            <line x1="20" y1="14" x2="10" y2="24" stroke="#38b2ac" stroke-width="1.5" stroke-opacity="0.7"/>
            <line x1="20" y1="14" x2="30" y2="24" stroke="#38b2ac" stroke-width="1.5" stroke-opacity="0.7"/>
            <line x1="14" y1="28" x2="26" y2="28" stroke="#38b2ac" stroke-width="1.5" stroke-opacity="0.7"/>
          </svg>
        </div>
        <h1 class="login-title">Galera Orchestrator</h1>
        <p class="login-subtitle">v2 — Cluster Management Panel</p>
      </div>

      <!-- Login form -->
      <form class="login-form" @submit.prevent="handleSubmit" novalidate>
        <!-- Error banner -->
        <div v-if="errorMessage" class="login-error" role="alert" aria-live="polite">
          <span class="login-error-icon" aria-hidden="true">⚠</span>
          {{ errorMessage }}
        </div>

        <!-- Username field -->
        <div class="form-group">
          <label for="username" class="form-label">Username</label>
          <input
              id="username"
              v-model="form.username"
              type="text"
              class="form-input"
              :class="{ 'form-input--error': fieldErrors.username }"
              autocomplete="username"
              autocapitalize="none"
              spellcheck="false"
              placeholder="admin"
              :disabled="loading"
              @input="clearErrors"
          />
          <span v-if="fieldErrors.username" class="form-field-error">
            {{ fieldErrors.username }}
          </span>
        </div>

        <!-- Password field -->
        <div class="form-group">
          <label for="password" class="form-label">Password</label>
          <div class="password-wrapper">
            <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input password-input"
                :class="{ 'form-input--error': fieldErrors.password }"
                autocomplete="current-password"
                placeholder="••••••••"
                :disabled="loading"
                @input="clearErrors"
            />
            <button
                type="button"
                class="password-toggle"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                :disabled="loading"
                @click="showPassword = !showPassword"
            >
              {{ showPassword ? '👁' : '👁‍🗨' }}
            </button>
          </div>
          <span v-if="fieldErrors.password" class="form-field-error">
            {{ fieldErrors.password }}
          </span>
        </div>

        <!-- Submit button -->
        <button
            type="submit"
            class="btn-login"
            :disabled="loading"
            :aria-busy="loading"
        >
          <span v-if="loading" class="btn-spinner" aria-hidden="true" />
          <span>{{ loading ? 'Signing in…' : 'Sign in' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form state
const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)
const errorMessage = ref('')
const fieldErrors = reactive({ username: '', password: '' })
const showPassword = ref(false)

function clearErrors() {
  errorMessage.value = ''
  fieldErrors.username = ''
  fieldErrors.password = ''
}

function validateForm() {
  let valid = true
  if (!form.username.trim()) {
    fieldErrors.username = 'Username is required'
    valid = false
  }
  if (!form.password) {
    fieldErrors.password = 'Password is required'
    valid = false
  }
  return valid
}

async function handleSubmit() {
  clearErrors()

  if (!validateForm()) return

  loading.value = true

  try {
    await authStore.login({
      username: form.username.trim(),
      password: form.password,
    })

    // Redirect to intended destination or home
    const redirectTo = route.query.redirect || '/'
    await router.push(redirectTo)
  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail

    if (status === 401) {
      errorMessage.value = 'Invalid username or password'
    } else if (status >= 500) {
      errorMessage.value = 'Server error. Please try again later.'
    } else if (detail) {
      errorMessage.value = String(detail)
    } else {
      errorMessage.value = 'Login failed. Check your connection.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg);
  padding: var(--space-4);
}

.login-card {
  width: 100%;
  max-width: 400px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
}

/* Header */
.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
  text-align: center;
}

.login-logo {
  flex-shrink: 0;
}

.login-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.login-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* Error banner */
.login-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: #fca5a5;
  font-size: var(--text-sm);
  margin-bottom: var(--space-5);
}

.login-error-icon {
  flex-shrink: 0;
  font-style: normal;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background-color: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-base);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.form-input::placeholder {
  color: var(--color-text-faint);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-dim);
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-input--error {
  border-color: var(--color-error);
}

.form-input--error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}

.form-field-error {
  font-size: var(--text-xs);
  color: #fca5a5;
}

/* Password field */
.password-wrapper {
  position: relative;
}

.password-input {
  padding-right: 3rem;
}

.password-toggle {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: var(--text-base);
  line-height: 1;
  padding: var(--space-1);
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast);
}

.password-toggle:hover {
  color: var(--color-text);
}

.password-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Submit button */
.btn-login {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background-color: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  margin-top: var(--space-2);
}

.btn-login:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading spinner */
.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>