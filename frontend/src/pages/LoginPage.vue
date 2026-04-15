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
  <div class="login-root">

    <!-- Animated mesh background -->
    <div class="login-bg" aria-hidden="true">
      <!-- Radial glows -->
      <div class="glow glow-1" />
      <div class="glow glow-2" />
      <div class="glow glow-3" />

      <!-- Animated grid -->
      <svg class="grid-svg" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M 48 0 L 0 0 0 48" fill="none" stroke="rgba(45,212,191,0.05)" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <!-- Floating orbs -->
      <div class="orb orb-1" />
      <div class="orb orb-2" />
      <div class="orb orb-3" />
    </div>

    <!-- Card -->
    <div class="login-card anim-fade-in">

      <!-- Logo -->
      <div class="login-logo">
        <div class="logo-icon">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="14" stroke="#2dd4bf" stroke-width="1" opacity="0.3"/>
            <circle cx="16" cy="16" r="9"  stroke="#2dd4bf" stroke-width="1.2" opacity="0.6"/>
            <circle cx="16" cy="16" r="4"  fill="#2dd4bf"/>
            <circle cx="16" cy="16" r="4"  fill="#2dd4bf" opacity="0.4" style="filter: blur(4px)"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-name">Galera Orchestrator</span>
          <span class="logo-version">v2</span>
        </div>
      </div>

      <!-- Divider -->
      <div class="card-divider" />

      <!-- Heading -->
      <div class="login-heading">
        <h1 class="login-title">Welcome back</h1>
        <p class="login-sub">Sign in to manage your cluster</p>
      </div>

      <!-- Form -->
      <form class="login-form" @submit.prevent="submit" novalidate>

        <div class="field">
          <label class="field-label" for="login-username">
            <i class="pi pi-user" />
            Username
          </label>
          <InputText
            id="login-username"
            v-model="form.username"
            placeholder="admin"
            autocomplete="username"
            autofocus
            :disabled="loading"
            class="login-input"
          />
        </div>

        <div class="field">
          <label class="field-label" for="login-password">
            <i class="pi pi-lock" />
            Password
          </label>
          <Password
            id="login-password"
            v-model="form.password"
            :feedback="false"
            toggle-mask
            placeholder="••••••••"
            autocomplete="current-password"
            :disabled="loading"
            class="login-input"
          />
        </div>

        <!-- Error -->
        <Transition name="err">
          <div v-if="error" class="login-error" role="alert">
            <i class="pi pi-exclamation-circle" />
            {{ error }}
          </div>
        </Transition>

        <Button
          type="submit"
          label="Sign in"
          icon="pi pi-arrow-right"
          icon-pos="right"
          :loading="loading"
          :disabled="!form.username || !form.password || loading"
          class="login-submit"
        />
      </form>

      <!-- Footer -->
      <p class="login-footer">
        MariaDB Galera Cluster — Management Panel
      </p>
    </div>
  </div>
</template>

<style scoped>
/* ====== ROOT ====== */
.login-root {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  position: relative;
  overflow: hidden;
  padding: var(--space-4);
}

/* ====== BACKGROUND ====== */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.grid-svg {
  position: absolute;
  inset: 0;
  opacity: 1;
}

/* Radial glows */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.14;
  animation: glow-pulse 16s ease-in-out infinite;
}
.glow-1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, #0d9488, transparent 70%);
  top: -200px; left: -100px;
  animation-delay: 0s;
}
.glow-2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #1e40af, transparent 70%);
  bottom: -150px; right: -100px;
  animation-delay: -6s;
  opacity: 0.09;
}
.glow-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, var(--color-primary), transparent 70%);
  top: 40%; left: 60%;
  animation-delay: -10s;
  opacity: 0.06;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.14; }
  50%       { opacity: 0.22; }
}

/* Floating orbs */
.orb {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(45,212,191,0.1);
  animation: orb-drift ease-in-out infinite;
}
.orb-1 {
  width: 300px; height: 300px;
  top: 10%; left: 5%;
  animation-duration: 40s;
  animation-delay: 0s;
}
.orb-2 {
  width: 180px; height: 180px;
  bottom: 15%; right: 8%;
  animation-duration: 34s;
  animation-delay: -12s;
  border-color: rgba(45,212,191,0.06);
}
.orb-3 {
  width: 80px; height: 80px;
  top: 30%; right: 20%;
  animation-duration: 28s;
  animation-delay: -20s;
  border-color: rgba(45,212,191,0.14);
}

@keyframes orb-drift {
  0%, 100% { transform: translate(0, 0); }
  33%       { transform: translate(6px, -8px); }
  66%       { transform: translate(-4px, 5px); }
}

/* ====== CARD ====== */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  background: var(--color-surface);
  backdrop-filter: blur(24px) saturate(1.4);
  -webkit-backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid rgba(45, 212, 191, 0.13);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  box-shadow:
    0 0 0 1px rgba(45,212,191,0.05) inset,
    0 32px 64px rgba(0,0,0,0.55),
    0 0 80px rgba(13,148,136,0.08);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

/* ====== LOGO ====== */
.login-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  background: var(--color-primary-highlight);
  border: 1px solid rgba(45,212,191,0.22);
  border-radius: var(--radius-md);
  flex-shrink: 0;
  box-shadow: 0 0 16px rgba(45,212,191,0.1);
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-name {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.logo-version {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-primary);
  letter-spacing: 0.05em;
  font-weight: 500;
}

/* ====== DIVIDER ====== */
.card-divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(45,212,191,0.22) 30%,
    rgba(45,212,191,0.22) 70%,
    transparent
  );
  margin: calc(-1 * var(--space-2)) 0;
}

/* ====== HEADING ====== */
.login-heading { display: flex; flex-direction: column; gap: var(--space-1); }

.login-title {
  font-size: 1.65rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.028em;
  line-height: 1.1;
}

.login-sub {
  font-size: var(--text-sm);
  color: var(--color-text-faint);
  margin-top: var(--space-1);
}

/* ====== FORM ====== */
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
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}
.field-label .pi {
  font-size: 0.65rem;
  color: var(--color-primary);
}

.login-input { width: 100%; }

/* ====== ERROR ====== */
.login-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-offline);
  background: rgba(248,113,113,0.07);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  animation: shake 0.35s ease;
}
.login-error .pi { font-size: 0.75rem; flex-shrink: 0; }

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%       { transform: translateX(-5px); }
  40%       { transform: translateX(5px); }
  60%       { transform: translateX(-4px); }
  80%       { transform: translateX(3px); }
}

.err-enter-active, .err-leave-active { transition: all 0.22s ease; }
.err-enter-from, .err-leave-to { opacity: 0; transform: translateY(-6px); }

/* ====== SUBMIT ====== */
.login-submit {
  width: 100%;
  justify-content: center;
  margin-top: var(--space-1);
  background: linear-gradient(135deg, #0d9488, #0f766e) !important;
  border-color: transparent !important;
  color: #f0fdfa !important;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 0 20px rgba(13,148,136,0.28);
  transition: box-shadow 0.2s, opacity 0.2s, transform 0.15s;
}
.login-submit:hover:not(:disabled) {
  opacity: 0.92;
  transform: translateY(-1px);
  box-shadow: 0 0 36px rgba(13,148,136,0.42) !important;
}
.login-submit:active:not(:disabled) {
  transform: translateY(0);
}
.login-submit:disabled { opacity: 0.38; box-shadow: none !important; }

/* ====== FOOTER ====== */
.login-footer {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  text-align: center;
  letter-spacing: 0.03em;
  opacity: 0.6;
}

/* ====== PRIMEVUE OVERRIDES ====== */
:deep(.p-password) { width: 100%; }
:deep(.p-password .p-inputtext) { width: 100%; }

:deep(.login-input.p-inputtext),
:deep(.p-password .p-inputtext) {
  background: var(--color-surface-2) !important;
  border-color: var(--color-border) !important;
  color: var(--color-text) !important;
  padding-block: 0.75rem;
  padding-inline: 0.875rem;
  font-size: 0.9375rem;
  line-height: 1.5;
  border-radius: 10px;
  transition: border-color 0.18s, box-shadow 0.18s;
}
:deep(.login-input.p-inputtext:focus),
:deep(.p-password .p-inputtext:focus) {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px rgba(45,212,191,0.14) !important;
  outline: none !important;
}

:deep(.login-submit.p-button) {
  padding-block: 0.8rem;
  padding-inline: 1.5rem;
  font-size: 0.9375rem;
  line-height: 1.5;
  border-radius: 10px;
  min-height: 48px;
}
</style>
