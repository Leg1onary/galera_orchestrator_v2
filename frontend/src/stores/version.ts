import { defineStore } from 'pinia'
import { ref } from 'vue'
import { versionApi, type UpdateCheckInfo, type UpdateStatus } from '@/api/version'

export const useVersionStore = defineStore('version', () => {
  const currentVersion = ref<string>('...')
  const checkResult    = ref<UpdateCheckInfo | null>(null)
  const checking       = ref(false)

  async function loadVersion() {
    try {
      const data = await versionApi.getVersion()
      currentVersion.value = data.version
    } catch {
      currentVersion.value = 'unknown'
    }
  }

  async function checkUpdate() {
    if (checking.value) return
    checking.value = true
    checkResult.value = null
    try {
      checkResult.value = await versionApi.checkUpdate()
    } catch {
      checkResult.value = {
        status: 'registry_unavailable',
        current_version: currentVersion.value,
        message: 'Request failed — backend unreachable',
        checked_at: new Date().toISOString(),
      }
    } finally {
      checking.value = false
    }
  }

  return { currentVersion, checkResult, checking, loadVersion, checkUpdate }
})
