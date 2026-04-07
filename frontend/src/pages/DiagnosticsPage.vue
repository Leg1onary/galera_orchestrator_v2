<template>
  <div class="page-diagnostics">
    <Tabs :value="activeTab" @update:value="activeTab = $event">
      <TabList>
        <Tab value="processlist">Process List</Tab>
        <Tab value="innodb">InnoDB Status</Tab>
        <Tab value="check">Check-All</Tab>
        <Tab value="syshealth">System Health</Tab>
        <Tab value="galera-cnf">galera.cnf</Tab>
        <Tab value="eventlog">Event Log</Tab>
      </TabList>

      <!-- Process List -->
      <TabPanels>
        <TabPanel value="processlist">
          <div class="tab-toolbar">
            <Select :options="nodeIds" v-model="plNode" placeholder="Нода" style="width:180px" size="small" />
            <Button label="Получить" icon="pi pi-refresh" outlined size="small"
              @click="fetchProcessList" :loading="loadingPL" :disabled="!plNode" />
          </div>
          <DataTable v-if="processList.length" :value="processList" size="small" scrollable scroll-height="400px" class="mt-3">
            <Column field="Id" header="ID" style="width:60px" />
            <Column field="User" header="User" />
            <Column field="Host" header="Host" />
            <Column field="db" header="DB" />
            <Column field="Command" header="Command" />
            <Column field="Time" header="Time" style="width:70px" />
            <Column field="State" header="State" />
            <Column field="Info" header="Query" style="max-width:300px">
              <template #body="{ data }">
                <span class="mono" style="font-size:11px;word-break:break-all">{{ data.Info }}</span>
              </template>
            </Column>
            <Column header="" style="width:80px">
              <template #body="{ data }">
                <Button icon="pi pi-times" size="small" text severity="danger"
                  @click="killQuery(data.Id)" v-tooltip="'Kill'" />
              </template>
            </Column>
          </DataTable>
          <div v-else-if="!loadingPL" class="empty-state">Выберите ноду и нажмите «Получить»</div>
        </TabPanel>

        <!-- InnoDB Status -->
        <TabPanel value="innodb">
          <div class="tab-toolbar">
            <Select :options="nodeIds" v-model="innoNode" placeholder="Нода" style="width:180px" size="small" />
            <Button label="Получить" icon="pi pi-refresh" outlined size="small"
              @click="fetchInnoDB" :loading="loadingInnoDB" :disabled="!innoNode" />
          </div>
          <div v-if="innodbStatus" class="copy-wrap mt-3">
            <Button icon="pi pi-copy" size="small" text @click="copyToClipboard(innodbStatus)"
              v-tooltip="'Скопировать'" class="copy-btn" />
            <pre class="yaml-preview">{{ innodbStatus }}</pre>
          </div>
          <div v-else class="empty-state">Выберите ноду</div>
        </TabPanel>

        <!-- Check All -->
        <TabPanel value="check">
          <div class="tab-toolbar">
            <Button label="Запустить проверку" icon="pi pi-play" outlined size="small"
              @click="runCheckAll" :loading="loadingCheck" />
          </div>
          <div v-if="checkResults.length" class="check-results mt-3">
            <div v-for="(r, i) in checkResults" :key="i" class="check-row">
              <i class="pi" :class="r.ok ? 'pi-check-circle text-ok' : 'pi-times-circle text-error'" />
              <div>
                <div class="check-title">{{ r.check }}</div>
                <div class="check-msg">{{ r.message }}</div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">Нажмите «Запустить проверку»</div>
        </TabPanel>

        <!-- System Health -->
        <TabPanel value="syshealth">
          <div class="tab-toolbar">
            <Button label="Получить" icon="pi pi-refresh" outlined size="small"
              @click="fetchSysHealth" :loading="loadingSysHealth" />
          </div>
          <div v-if="sysHealth.length" class="sys-health mt-3">
            <div v-for="h in sysHealth" :key="h.node_id" class="sys-card">
              <div class="sys-name">{{ h.node_id }}</div>
              <table class="metric-table">
                <tr><td>CPU</td><td class="mono">{{ h.cpu }}</td></tr>
                <tr><td>RAM</td><td class="mono">{{ h.ram }}</td></tr>
                <tr><td>Disk</td><td class="mono">{{ h.disk }}</td></tr>
              </table>
            </div>
          </div>
          <div v-else class="empty-state">Нажмите «Получить»</div>
        </TabPanel>

        <!-- galera.cnf compare -->
        <TabPanel value="galera-cnf">
          <div class="tab-toolbar">
            <Button label="Сравнить" icon="pi pi-arrows-h" outlined size="small"
              @click="compareGaleraCnf" :loading="loadingGalera" />
          </div>
          <div v-if="galeraCompare" class="copy-wrap mt-3">
            <Button icon="pi pi-copy" size="small" text @click="copyToClipboard(galeraCompare)"
              v-tooltip="'Скопировать'" class="copy-btn" />
            <pre class="yaml-preview">{{ galeraCompare }}</pre>
          </div>
          <div v-else class="empty-state">Нажмите «Сравнить»</div>
        </TabPanel>

        <!-- Event Log -->
        <TabPanel value="eventlog">
          <div class="tab-toolbar">
            <Button label="Обновить" icon="pi pi-refresh" text size="small" @click="cluster.fetchLogs()" />
            <Button label="Очистить" icon="pi pi-trash" text size="small" severity="danger"
              @click="cluster.clearLogs()" />
          </div>
          <div class="event-log mt-3">
            <div v-for="(ev, i) in cluster.logs" :key="i" class="log-row">
              <span class="log-ts mono">{{ formatTs(ev.ts) }}</span>
              <span class="log-level" :class="`level-${(ev.level||'info').toLowerCase()}`">{{ ev.level || 'INFO' }}</span>
              <span class="log-msg">{{ ev.message }}</span>
            </div>
            <div v-if="!cluster.logs.length" class="empty-state">Лог пуст</div>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useClipboard } from '@vueuse/core'
import { useToast } from 'primevue/usetoast'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Button from 'primevue/button'
import Select from 'primevue/select'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import api from '@/api'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()
const toast = useToast()
const activeTab = ref('processlist')

// ── useClipboard — копирование вывода InnoDB/YAML в буфер ─────────
const { copy, copied } = useClipboard()
async function copyToClipboard(text) {
  await copy(text)
  toast.add({ severity: 'success', summary: 'Скопировано', life: 1500 })
}

const nodeIds = computed(() => cluster.nodes.map(n => n.id))

// Process list
const plNode = ref(null)
const processList = ref([])
const loadingPL = ref(false)
async function fetchProcessList() {
  loadingPL.value = true
  try {
    const { data } = await api.get(`/api/node/${plNode.value}/processlist`)
    processList.value = data.processes || []
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 })
  } finally { loadingPL.value = false }
}
async function killQuery(id) {
  try {
    await api.post(`/api/node/${plNode.value}/kill-query`, { query_id: id })
    toast.add({ severity: 'success', summary: 'Killed', detail: `Query ${id}`, life: 2000 })
    fetchProcessList()
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
}

// InnoDB
const innoNode = ref(null)
const innodbStatus = ref('')
const loadingInnoDB = ref(false)
async function fetchInnoDB() {
  loadingInnoDB.value = true
  try {
    const { data } = await api.get(`/api/node/${innoNode.value}/innodb-status`)
    innodbStatus.value = data.raw || data.status || JSON.stringify(data, null, 2)
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
  finally { loadingInnoDB.value = false }
}

// Check all
const checkResults = ref([])
const loadingCheck = ref(false)
async function runCheckAll() {
  loadingCheck.value = true
  try {
    const { data } = await api.get('/api/diagnostics/check-all')
    checkResults.value = data.checks || []
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
  finally { loadingCheck.value = false }
}

// System health
const sysHealth = ref([])
const loadingSysHealth = ref(false)
async function fetchSysHealth() {
  loadingSysHealth.value = true
  try {
    const { data } = await api.get('/api/diagnostics/system-health')
    sysHealth.value = data.nodes || []
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
  finally { loadingSysHealth.value = false }
}

// galera.cnf
const galeraCompare = ref('')
const loadingGalera = ref(false)
async function compareGaleraCnf() {
  loadingGalera.value = true
  try {
    const { data } = await api.get('/api/config/compare-galera-cnf')
    galeraCompare.value = data.diff || data.result || JSON.stringify(data, null, 2)
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
  finally { loadingGalera.value = false }
}

function formatTs(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('ru-RU')
}
</script>

<style scoped>
.page-diagnostics { display: flex; flex-direction: column; }
.tab-toolbar { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; padding: 0.75rem 0; }
.mt-3 { margin-top: 0.75rem; }
.empty-state { padding: 2rem 0; text-align: center; color: var(--color-text-muted); font-size: 13px; }
.copy-wrap { position: relative; }
.copy-btn { position: absolute; top: 0.5rem; right: 0.5rem; z-index: 1; opacity: 0.6; }
.copy-wrap:hover .copy-btn { opacity: 1; }

.check-results { display: flex; flex-direction: column; gap: 0.5rem; }
.check-row { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.75rem; background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-sm); }
.check-title { font-weight: 600; font-size: 13px; }
.check-msg { font-size: 12px; color: var(--color-text-muted); }
.text-ok    { color: var(--color-status-ok); }
.text-error { color: var(--color-status-error); }

.sys-health { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.sys-card { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 1rem; }
.sys-name { font-weight: 700; margin-bottom: 0.5rem; }

.event-log { display: flex; flex-direction: column; gap: 4px; max-height: 450px; overflow-y: auto; }
.log-row { display: flex; gap: 0.75rem; font-size: 12px; align-items: baseline; padding: 3px 6px; border-radius: 3px; }
.log-row:hover { background: var(--color-bg-elevated); }
.log-ts { color: var(--color-text-muted); flex-shrink: 0; width: 60px; }
.log-level { flex-shrink: 0; width: 45px; font-weight: 700; font-size: 10px; text-transform: uppercase; }
.level-error, .level-err { color: var(--color-status-error); }
.level-warn { color: var(--color-status-warn); }
.level-info { color: var(--color-status-info); }
.log-msg { color: var(--color-text-secondary); }
.mono { font-family: var(--font-mono); }
</style>
