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
  background: #0a0b0f;
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
  opacity: 0.18;
  animation: glow-pulse 8s ease-in-out infinite;
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
  animation-delay: 3s;
  opacity: 0.12;
}
.glow-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #2dd4bf, transparent 70%);
  top: 40%; left: 60%;
  animation-delay: 5s;
  opacity: 0.08;
}

@keyframes glow-pulse {
  0%, 100% { transform: scale(1);   opacity: 0.18; }
  50%       { transform: scale(1.1); opacity: 0.25; }
}

/* Floating orbs */
.orb {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(45,212,191,0.15);
  animation: orb-float linear infinite;
}
.orb-1 {
  width: 300px; height: 300px;
  top: 10%; left: 5%;
  animation-duration: 20s;
  animation-delay: 0s;
}
.orb-2 {
  width: 180px; height: 180px;
  bottom: 15%; right: 8%;
  animation-duration: 15s;
  animation-delay: -5s;
  border-color: rgba(45,212,191,0.08);
}
.orb-3 {
  width: 80px; height: 80px;
  top: 30%; right: 20%;
  animation-duration: 12s;
  animation-delay: -8s;
  border-color: rgba(45,212,191,0.2);
}

@keyframes orb-float {
  0%   { transform: translate(0, 0) rotate(0deg); }
  25%  { transform: translate(10px, -15px) rotate(90deg); }
  50%  { transform: translate(20px, 0px) rotate(180deg); }
  75%  { transform: translate(10px, 15px) rotate(270deg); }
  100% { transform: translate(0, 0) rotate(360deg); }
}

/* ====== CARD ====== */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  background: rgba(15, 16, 21, 0.85);
  backdrop-filter: blur(24px) saturate(1.4);
  -webkit-backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid rgba(45, 212, 191, 0.12);
  border-radius: 20px;
  padding: var(--space-8);
  box-shadow:
    0 0 0 1px rgba(45,212,191,0.04) inset,
    0 32px 64px rgba(0,0,0,0.6),
    0 0 80px rgba(13,148,136,0.08);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
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
  width: 44px;
  height: 44px;
  background: rgba(45,212,191,0.07);
  border: 1px solid rgba(45,212,191,0.2);
  border-radius: 12px;
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.logo-name {
  font-size: var(--text-sm);
  font-weight: 700;
  color: #e4e4e7;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.logo-version {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: #2dd4bf;
  letter-spacing: 0.05em;
  font-weight: 500;
}

/* ====== DIVIDER ====== */
.card-divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(45,212,191,0.2) 30%,
    rgba(45,212,191,0.2) 70%,
    transparent
  );
  margin: calc(-1 * var(--space-2)) 0;
}

/* ====== HEADING ====== */
.login-heading { display: flex; flex-direction: column; gap: var(--space-1); }

.login-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #f4f4f5;
  letter-spacing: -0.025em;
  line-height: 1.1;
}

.login-sub {
  font-size: var(--text-sm);
  color: #52525b;
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
  color: #71717a;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}
.field-label .pi { font-size: 0.65rem; color: #2dd4bf; }

.login-input { width: 100%; }

/* ====== ERROR ====== */
.login-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: #f87171;
  background: rgba(248,113,113,0.07);
  border: 1px solid rgba(248,113,113,0.18);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
}
.login-error .pi { font-size: 0.75rem; }

.err-enter-active, .err-leave-active { transition: all 0.2s ease; }
.err-enter-from, .err-leave-to { opacity: 0; transform: translateY(-4px); }

/* ====== SUBMIT ====== */
.login-submit {
  width: 100%;
  justify-content: center;
  margin-top: var(--space-1);
  /* override ghost → solid teal for the primary CTA on login */
  background: linear-gradient(135deg, #0d9488, #0f766e) !important;
  border-color: transparent !important;
  color: #f0fdfa !important;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 0 24px rgba(13,148,136,0.3);
  transition: box-shadow 0.2s, opacity 0.2s;
}
.login-submit:hover:not(:disabled) {
  opacity: 0.9;
  box-shadow: 0 0 36px rgba(13,148,136,0.45) !important;
}
.login-submit:disabled { opacity: 0.4; box-shadow: none !important; }

/* ====== FOOTER ====== */
.login-footer {
  font-size: var(--text-xs);
  color: #3f3f46;
  text-align: center;
  letter-spacing: 0.03em;
}

/* PrimeVue Password wrapper */
:deep(.p-password) { width: 100%; }
:deep(.p-password .p-inputtext) { width: 100%; }
</style>
