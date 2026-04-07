<template>
  <header class="app-header">
    <!-- Mode toggle -->
    <div class="header-group">
      <button class="mode-btn" :class="cluster.isMock ? 'mode-mock' : 'mode-real'"
        @click="handleModeToggle" :disabled="modeLoading" v-tooltip.bottom="'Переключить Mock / Real'">
        <i class="pi pi-circle-fill" style="font-size:8px" />
        {{ cluster.isMock ? 'MOCK' : 'REAL' }}
      </button>
    </div>

    <!-- Contour selector (real mode only) -->
    <div class="header-group contour-bar" v-if="!cluster.isMock">
      <button v-for="c in cluster.contourList" :key="c"
        class="contour-btn"
        :class="{ active: cluster.selection.contour === c }"
        @click="selectContour(c)">
        {{ c.toUpperCase() }}
      </button>
      <Select
        v-if="cluster.currentContourClusters.length > 1"
        :options="cluster.currentContourClusters"
        v-model="selectedClusterName"
        @change="onClusterChange"
        placeholder="Кластер"
        class="cluster-select"
        size="small"
      />
    </div>

    <!-- Spacer -->
    <div class="header-spacer" />

    <!-- Poll interval -->
    <div class="header-group">
      <label class="header-label">Интервал:</label>
      <Select
        :options="pollOptions" option-label="label" option-value="value"
        v-model="pollInterval" @change="savePollInterval"
        class="poll-select" size="small"
      />
    </div>

    <!-- Refresh -->
    <Button icon="pi pi-refresh" text size="small"
      @click="refresh" :loading="cluster.loading"
      v-tooltip.bottom="'Обновить'" />

    <!-- Theme -->
    <Button :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'" text size="small"
      @click="toggleTheme" v-tooltip.bottom="isDark ? 'Светлая тема' : 'Тёмная тема'" />

    <!-- Logout -->
    <Button v-if="auth.authEnabled" icon="pi pi-sign-out" text size="small"
      severity="secondary" @click="handleLogout" v-tooltip.bottom="'Выйти'" />
  </header>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Select from 'primevue/select'
import { useAuthStore } from '@/stores/auth'
import { useClusterStore } from '@/stores/cluster'

const auth = useAuthStore()
const cluster = useClusterStore()
const router = useRouter()
const toast = useToast()

const modeLoading = ref(false)
const isDark = computed(() => (cluster.prefs.theme || 'dark') === 'dark')

const pollOptions = [
  { label: '2s',  value: 2 },
  { label: '5s',  value: 5 },
  { label: '10s', value: 10 },
  { label: '30s', value: 30 },
  { label: '60s', value: 60 },
]
const pollInterval = ref(cluster.prefs.poll_interval || 5)
watch(() => cluster.prefs.poll_interval, v => { pollInterval.value = v })

const selectedClusterName = computed(() => {
  const clusters = cluster.currentContourClusters
  return clusters[cluster.selection.cluster_index] || clusters[0]
})

async function handleModeToggle() {
  modeLoading.value = true
  try { await cluster.toggleMode() }
  catch { toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось переключить режим', life: 3000 }) }
  finally { modeLoading.value = false }
}

async function selectContour(c) {
  await cluster.selectContour(c, 0)
}

async function onClusterChange(e) {
  const idx = cluster.currentContourClusters.indexOf(e.value)
  if (idx >= 0) await cluster.selectCluster(idx)
}

async function refresh() {
  await cluster.fetchStatus()
  toast.add({ severity: 'info', summary: 'Обновлено', life: 1500 })
}

function toggleTheme() {
  const next = isDark.value ? 'light' : 'dark'
  cluster.savePrefs({ ...cluster.prefs, theme: next })
}

async function savePollInterval() {
  await cluster.savePrefs({ ...cluster.prefs, poll_interval: pollInterval.value })
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header { position: sticky; top: 0; z-index: 100; }

.header-group { display: flex; align-items: center; gap: 0.375rem; }
.header-spacer { flex: 1; }
.header-label { font-size: 11px; color: var(--color-text-muted); white-space: nowrap; }

.mode-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: var(--radius-sm);
  font-size: 11px; font-weight: 700; letter-spacing: 0.06em;
  border: 1px solid transparent; cursor: pointer;
  transition: all var(--transition-fast);
}
.mode-mock { background: rgba(59,130,246,.15); color: #60a5fa; border-color: rgba(59,130,246,.3); }
.mode-real { background: rgba(34,197,94,.15);  color: #4ade80; border-color: rgba(34,197,94,.3); }
.mode-btn:hover { filter: brightness(1.15); }

.contour-btn {
  padding: 3px 10px; border-radius: var(--radius-sm);
  font-size: 11px; font-weight: 600;
  background: transparent; border: 1px solid var(--color-border);
  color: var(--color-text-muted); cursor: pointer;
  transition: all var(--transition-fast);
}
.contour-btn.active { background: var(--color-accent-light); color: var(--color-accent-primary); border-color: rgba(59,130,246,.4); }
.contour-btn:hover:not(.active) { background: var(--color-bg-elevated); }

.cluster-select { width: 140px; font-size: 12px; }
.poll-select    { width: 70px; font-size: 12px; }
</style>
