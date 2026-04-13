import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { versionApi, type UpdateCheckInfo } from '@/api/version'

const UPDATE_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000 // 24h

export const useVersionStore = defineStore('version', () => {
  const currentVersion  = ref<string>('...')
  const updateInfo      = ref<UpdateCheckInfo | null>(null)
  const lastChecked     = ref<number | null>(null)
  const checking        = ref(false)

  const updateAvailable = computed(() => updateInfo.value?.update_available ?? false)
  const checkError      = computed(() => updateInfo.value?.error ?? null)

  async function loadVersion() {
    try {
      const data = await versionApi.getVersion()
      currentVersion.value = data.version
    } catch {
      currentVersion.value = 'unknown'
    }
  }

  async function checkUpdate(force = false) {
    const now = Date.now()
    if (!force && lastChecked.value && now - lastChecked.value < UPDATE_CHECK_INTERVAL_MS) {
      return
    }
    if (checking.value) return
    checking.value = true
    try {
      updateInfo.value = await versionApi.checkUpdate()
      lastChecked.value = now
    } catch {
      // silently ignore — network may be isolated
    } finally {
      checking.value = false
    }
  }

  return {
    currentVersion,
    updateInfo,
    updateAvailable,
    checkError,
    checking,
    loadVersion,
    checkUpdate,
  }
})
