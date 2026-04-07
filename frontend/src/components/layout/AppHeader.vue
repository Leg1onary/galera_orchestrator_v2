<template>
  <header class="app-header">
    <!-- Logo -->
    <router-link to="/overview" class="logo">
      <svg class="logo-galera-svg" width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Galera Orchestrator">
        <circle cx="13" cy="13" r="9" fill="none" stroke="#3b82f6" stroke-width="2" opacity="0.9"/>
        <circle cx="23" cy="13" r="9" fill="none" stroke="#22c55e" stroke-width="2" opacity="0.9"/>
        <circle cx="18" cy="22" r="9" fill="none" stroke="#f59e0b" stroke-width="2" opacity="0.9"/>
        <text x="18" y="20" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="8.5" font-weight="700" fill="white" letter-spacing="-0.5">GO</text>
      </svg>
      <div>
        <div class="logo-text">Galera Orchestrator</div>
        <div class="logo-sub">MariaDB Galera Cluster</div>
      </div>
    </router-link>

    <div class="header-spacer"></div>

    <div style="display:flex;align-items:center;gap:var(--space-3);flex-wrap:wrap;min-width:0">

      <!-- ENV switcher TEST/PROD — only in REAL mode -->
      <div
        v-if="cluster.isReal"
        style="display:flex;align-items:center;gap:3px;background:var(--surface-2);border:1px solid var(--border);border-radius:var(--radius-full);padding:3px"
      >
        <button
          :style="contourBtnStyle('test')"
          class="btn btn-sm"
          @click="cluster.selectContour('test')"
        >TEST</button>
        <button
          :style="contourBtnStyle('prod')"
          class="btn btn-sm"
          @click="cluster.selectContour('prod')"
        >PROD</button>
      </div>

      <!-- Cluster status badge -->
      <div class="cluster-badge">
        <span class="status-dot" :class="cluster.clusterStatusClass"></span>
        <span>{{ clusterBadgeText }}</span>
      </div>

      <!-- MOCK / REAL toggle -->
      <div
        style="display:flex;align-items:center;gap:3px;background:var(--surface-2);border:1px solid var(--border);border-radius:var(--radius-full);padding:3px"
        title="Режим: Mock — симуляция, Real — реальные данные"
      >
        <button
          :style="modeBtnStyle('mock')"
          class="btn btn-sm"
          @click="cluster.setDataMode('mock')"
        >MOCK</button>
        <button
          :style="modeBtnStyle('real')"
          class="btn btn-sm"
          @click="cluster.setDataMode('real')"
        >REAL</button>
      </div>

      <!-- Poll interval + refresh -->
      <div style="display:flex;align-items:center;gap:var(--space-2);padding-left:var(--space-3);border-left:1px solid rgba(255,255,255,0.12)">
        <span style="font-size:0.72rem;color:var(--text-muted);white-space:nowrap">Опрос:</span>
        <select
          class="form-input"
          style="width:76px;padding:2px 6px;font-size:0.72rem;height:28px"
          :value="cluster.pollInterval"
          @change="e => cluster.setPollInterval(Number(e.target.value))"
        >
          <option value="2">2 сек</option>
          <option value="5">5 сек</option>
          <option value="10">10 сек</option>
          <option value="30">30 сек</option>
          <option value="60">60 сек</option>
        </select>
        <button
          class="btn btn-ghost"
          style="padding:2px 10px;font-size:0.72rem;height:28px;display:flex;align-items:center;gap:4px"
          @click="cluster.fetchStatus()"
          title="Обновить сейчас"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
          </svg>
          Обновить
        </button>
        <span v-if="cluster.loading" class="spin-dot"></span>
        <span v-if="cluster.lastUpdate" style="font-size:0.72rem;color:var(--text-muted)">{{ lastUpdateStr }}</span>
      </div>
    </div>

    <!-- Theme toggle -->
    <button class="theme-btn" @click="toggleTheme" title="Переключить тему">
      <svg v-if="isDark" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
    </button>

    <!-- Logout — only when auth enabled -->
    <button
      v-if="auth.authEnabled"
      class="theme-btn"
      @click="auth.logout()"
      title="Выйти"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
        <polyline points="16 17 21 12 16 7"/>
        <line x1="21" y1="12" x2="9" y2="12"/>
      </svg>
    </button>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useClusterStore } from '@/stores/cluster.js'
import { useAuthStore }    from '@/stores/auth.js'

const cluster = useClusterStore()
const auth    = useAuthStore()

// ── Theme ─────────────────────────────────────────────────────────
const LS_THEME = 'galera_theme'
const isDark = ref(
  (localStorage.getItem(LS_THEME) || 'dark') === 'dark'
)

function toggleTheme() {
  isDark.value = !isDark.value
  const t = isDark.value ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', t)
  localStorage.setItem(LS_THEME, t)
}

// ── Cluster badge text ────────────────────────────────────────────
const clusterBadgeText = computed(() => {
  const name    = cluster.contour.toUpperCase()
  const size    = cluster.status?.cluster_size || cluster.nodes.length
  const synced  = cluster.nodesSynced
  const arbTot  = cluster.arbitrators.length
  const arbOn   = cluster.arbOnline
  const status  = cluster.status?.wsrep_cluster_status ||
    (cluster.nodes[0]?.wsrep_cluster_status) || 'Primary'

  let txt = `${name} · ${status} · ${synced}/${size}`
  if (arbTot > 0) txt += ` · arb ${arbOn}/${arbTot}`
  return txt
})

// ── Button styles ─────────────────────────────────────────────────
function modeBtnStyle(mode) {
  const active = cluster.dataMode === mode
  if (active) {
    const bg = mode === 'mock' ? 'var(--warning)' : 'var(--success)'
    return `height:26px;padding:0 10px;font-size:0.72rem;border-radius:9999px;font-weight:700;background:${bg};color:#fff`
  }
  return 'height:26px;padding:0 10px;font-size:0.72rem;border-radius:9999px;font-weight:700;background:transparent;color:var(--text-muted)'
}

function contourBtnStyle(c) {
  const active = cluster.contour === c
  if (active) {
    const bg = c === 'prod' ? '#6daa45' : 'var(--primary)'
    return `height:26px;padding:0 10px;font-size:0.72rem;border-radius:9999px;font-weight:700;background:${bg};color:#fff`
  }
  return 'height:26px;padding:0 10px;font-size:0.72rem;border-radius:9999px;font-weight:700;background:transparent;color:var(--text-muted)'
}

// ── Last update time string ───────────────────────────────────────
const lastUpdateStr = computed(() => {
  if (!cluster.lastUpdate) return '—'
  const d = cluster.lastUpdate
  const h = String(d.getHours()).padStart(2,'0')
  const m = String(d.getMinutes()).padStart(2,'0')
  const s = String(d.getSeconds()).padStart(2,'0')
  return `${h}:${m}:${s}`
})
</script>
