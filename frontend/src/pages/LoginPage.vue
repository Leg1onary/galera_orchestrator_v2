<template>
  <div class="login-wrapper">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <div class="login-logo-icon">
          <svg width="22" height="22" viewBox="0 0 36 36" fill="none">
            <circle cx="13" cy="13" r="9" fill="none" stroke="#fff" stroke-width="2.5" opacity="0.85"/>
            <circle cx="23" cy="13" r="9" fill="none" stroke="#fff" stroke-width="2.5" opacity="0.6"/>
            <circle cx="18" cy="22" r="9" fill="none" stroke="#fff" stroke-width="2.5" opacity="0.45"/>
          </svg>
        </div>
        <div class="login-logo-text">
          <div class="login-logo-title">Galera Orchestrator</div>
          <div class="login-logo-sub">Cluster Management UI</div>
        </div>
      </div>

      <div class="login-heading">Вход</div>
      <div class="login-sub">Введите учётные данные для доступа к панели управления</div>

      <div v-if="auth.loginError" class="login-error">{{ auth.loginError }}</div>

      <form @submit.prevent="doLogin">
        <div class="login-field">
          <label for="loginUsername">Логин</label>
          <input
            id="loginUsername"
            v-model="username"
            type="text"
            autocomplete="username"
            placeholder="admin"
            spellcheck="false"
            @keydown.enter="doLogin"
          />
        </div>
        <div class="login-field">
          <label for="loginPassword">Пароль</label>
          <input
            id="loginPassword"
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="••••••••"
            @keydown.enter="doLogin"
          />
        </div>
        <button
          type="submit"
          class="login-btn"
          :disabled="auth.loading"
          :class="{ loading: auth.loading }"
        >
          {{ auth.loading ? 'Вход…' : 'Войти' }}
        </button>
      </form>

      <div class="login-footer">
        <a href="https://github.com/Leg1onary/galera_orchestrator" target="_blank" rel="noopener">GitHub</a>
        &nbsp;·&nbsp; Galera Orchestrator
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

const auth     = useAuthStore()
const router   = useRouter()
const username = ref('')
const password = ref('')

onMounted(() => {
  auth.clearError()
})

async function doLogin() {
  if (!username.value.trim()) return
  const ok = await auth.login(username.value.trim(), password.value)
  if (ok) {
    router.push({ name: 'overview' })
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  background: var(--bg);
}
.login-card {
  width: 100%; max-width: 400px;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  padding: 40px 36px 36px;
  box-shadow: var(--shadow-lg);
  animation: loginFadeIn .25s ease;
}
@keyframes loginFadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.login-logo {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 28px;
}
.login-logo-icon {
  width: 40px; height: 40px; border-radius: 8px;
  background: var(--primary);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.login-logo-text { line-height: 1.2; }
.login-logo-title {
  font-size: 15px; font-weight: 600;
  color: var(--text);
}
.login-logo-sub {
  font-size: 12px; color: var(--text-muted);
}
.login-heading {
  font-size: 22px; font-weight: 700;
  color: var(--text); margin-bottom: 6px;
}
.login-sub {
  font-size: 13px; color: var(--text-muted);
  margin-bottom: 28px;
}
.login-field { margin-bottom: 16px; }
.login-field label {
  display: block; font-size: 12px; font-weight: 500;
  color: var(--text-muted); margin-bottom: 6px; letter-spacing: .3px;
}
.login-field input {
  width: 100%; box-sizing: border-box;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 14px;
  font-size: 14px; color: var(--text);
  outline: none; transition: border-color .15s;
}
.login-field input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-dim);
}
.login-field input::placeholder { color: var(--text-faint); }
.login-error {
  background: var(--error-dim);
  border: 1px solid var(--error);
  border-radius: 6px; padding: 9px 12px;
  font-size: 13px; color: var(--error);
  margin-bottom: 16px;
}
.login-btn {
  width: 100%; padding: 11px;
  background: var(--primary); border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; color: #fff;
  cursor: pointer; transition: background .15s, opacity .15s;
}
.login-btn:hover { background: var(--primary-hover); }
.login-btn:disabled { opacity: .6; cursor: default; }
.login-footer {
  margin-top: 24px; text-align: center;
  font-size: 11px; color: var(--text-faint);
}
.login-footer a { color: var(--primary); text-decoration: none; }
.login-footer a:hover { text-decoration: underline; }
</style>
