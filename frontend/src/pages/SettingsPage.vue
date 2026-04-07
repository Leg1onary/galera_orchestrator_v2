<template>
  <div class="page-settings">
    <Tabs :value="activeTab" @update:value="activeTab = $event">
      <TabList>
        <Tab value="clusters">Кластеры</Tab>
        <Tab value="nodes">Ноды</Tab>
        <Tab value="arbitrators">Арбитры</Tab>
        <Tab value="db">DB Credentials</Tab>
        <Tab value="yaml">YAML Preview</Tab>
      </TabList>
      <TabPanels>

        <!-- Clusters -->
        <TabPanel value="clusters">
          <div class="settings-section">
            <p class="hint-text mb-3">Управление кластерами в контурах. Активный кластер нельзя удалить.</p>

            <!-- Create cluster -->
            <div class="create-cluster mb-4">
              <h4 class="settings-sub-title">Создать кластер</h4>
              <div class="form-row">
                <InputText v-model="newClusterName" placeholder="Название кластера" size="small" style="width:200px" />
                <Select :options="cluster.contourList" v-model="newClusterContour"
                  placeholder="Контур" size="small" style="width:120px" />
                <Button label="Создать" icon="pi pi-plus" size="small" outlined
                  @click="createCluster" :disabled="!newClusterName || !newClusterContour" />
              </div>
            </div>

            <!-- Cluster list -->
            <div v-for="(clusters, contour) in cluster.contours" :key="contour" class="mb-3">
              <h4 class="contour-label">{{ contour.toUpperCase() }}</h4>
              <div v-for="(clName, idx) in clusters" :key="idx" class="cluster-row">
                <span class="cluster-name">{{ clName }}</span>
                <span v-if="isActive(contour, idx)" class="badge badge-real">ACTIVE</span>
                <div class="cluster-actions">
                  <Button icon="pi pi-pencil" size="small" text @click="renameCluster(contour, idx, clName)" />
                  <Button icon="pi pi-trash" size="small" text severity="danger"
                    :disabled="isActive(contour, idx)"
                    @click="deleteCluster(contour, idx)" />
                </div>
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- Nodes -->
        <TabPanel value="nodes">
          <div class="settings-section">
            <p class="hint-text mb-3">Ноды активного кластера: {{ cluster.clusterName }}</p>
            <div class="nodes-list mb-4">
              <div v-for="node in configNodes" :key="node.id" class="config-node-row">
                <span class="mono">{{ node.id }}</span>
                <span>{{ node.host }}:{{ node.port }}</span>
                <span class="nc-dc">{{ node.dc }}</span>
                <span :class="node.enabled ? 'text-ok' : 'text-muted'">{{ node.enabled ? 'enabled' : 'disabled' }}</span>
                <Button icon="pi pi-trash" size="small" text severity="danger"
                  @click="deleteNode(node.id)" />
              </div>
            </div>

            <h4 class="settings-sub-title">Добавить ноду</h4>
            <div class="add-node-form">
              <div v-for="f in nodeFields" :key="f.key" class="form-field">
                <label class="field-label">{{ f.label }}</label>
                <InputText v-if="f.type !== 'number'" v-model="newNode[f.key]"
                  :placeholder="f.placeholder" size="small" />
                <InputNumber v-else v-model="newNode[f.key]" :placeholder="f.placeholder"
                  size="small" :use-grouping="false" />
              </div>
              <Button label="Добавить ноду" icon="pi pi-plus" outlined size="small"
                @click="addNode" class="mt-2" />
            </div>
          </div>
        </TabPanel>

        <!-- Arbitrators -->
        <TabPanel value="arbitrators">
          <div class="settings-section">
            <div class="nodes-list mb-4">
              <div v-for="arb in configArbs" :key="arb.id" class="config-node-row">
                <span class="mono">{{ arb.id }}</span>
                <span>{{ arb.host }}:{{ arb.ssh_port }}</span>
                <span class="nc-dc">{{ arb.dc }}</span>
                <Button icon="pi pi-trash" size="small" text severity="danger"
                  @click="deleteArb(arb.id)" />
              </div>
            </div>

            <h4 class="settings-sub-title">Добавить арбитра</h4>
            <div class="add-node-form">
              <div class="form-field"><label class="field-label">ID</label><InputText v-model="newArb.id" placeholder="arb01" size="small" /></div>
              <div class="form-field"><label class="field-label">Host</label><InputText v-model="newArb.host" placeholder="192.168.1.12" size="small" /></div>
              <div class="form-field"><label class="field-label">SSH Port</label><InputNumber v-model="newArb.ssh_port" :placeholder="22" size="small" :use-grouping="false" /></div>
              <div class="form-field"><label class="field-label">SSH User</label><InputText v-model="newArb.ssh_user" placeholder="root" size="small" /></div>
              <div class="form-field"><label class="field-label">SSH Key</label><InputText v-model="newArb.ssh_key" placeholder="/root/.ssh/id_rsa" size="small" /></div>
              <div class="form-field"><label class="field-label">DC</label><InputText v-model="newArb.dc" placeholder="DC1" size="small" /></div>
              <Button label="Добавить арбитра" icon="pi pi-plus" outlined size="small"
                @click="addArb" class="mt-2" />
            </div>
          </div>
        </TabPanel>

        <!-- DB -->
        <TabPanel value="db">
          <div class="settings-section">
            <p class="hint-text mb-3">Глобальные учётные данные для подключения к MariaDB.</p>
            <div class="add-node-form">
              <div class="form-field"><label class="field-label">User</label><InputText v-model="dbUser" placeholder="monitor_user" size="small" /></div>
              <div class="form-field"><label class="field-label">Password</label><Password v-model="dbPass" :feedback="false" size="small" /></div>
              <Button label="Сохранить" icon="pi pi-save" size="small" @click="saveDB" class="mt-2" />
            </div>
          </div>
        </TabPanel>

        <!-- YAML -->
        <TabPanel value="yaml">
          <div class="tab-toolbar">
            <Button label="Обновить конфиг" icon="pi pi-refresh" outlined size="small"
              @click="reloadConfig" :loading="loadingReload" />
            <Button label="Скопировать" icon="pi pi-copy" text size="small"
              @click="copyYaml" :disabled="!yamlContent" />
          </div>
          <pre class="yaml-preview mt-3" v-if="yamlContent">{{ yamlContent }}</pre>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useClipboard } from '@vueuse/core'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Button from 'primevue/button'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Password from 'primevue/password'
import api from '@/api'
import { useClusterStore } from '@/stores/cluster'

const cluster = useClusterStore()
const toast = useToast()
const confirm = useConfirm()
const activeTab = ref('clusters')

const { copy } = useClipboard()
async function copyYaml() {
  await copy(yamlContent.value)
  toast.add({ severity: 'success', summary: 'Скопировано', life: 1500 })
}

const yamlContent = ref('')
const loadingReload = ref(false)

const configNodes = computed(() => cluster.nodes || [])
const configArbs  = computed(() => cluster.arbitrators || [])

const newClusterName    = ref('')
const newClusterContour = ref('')

const dbUser = ref('')
const dbPass = ref('')

const newNode = ref({ id:'', name:'', host:'', port: 3306, ssh_port: 22, ssh_user:'root', ssh_key:'/root/.ssh/id_rsa', dc:'DC1', enabled:true })
const newArb  = ref({ id:'', host:'', ssh_port: 22, ssh_user:'root', ssh_key:'/root/.ssh/id_rsa', dc:'DC1', enabled:true })

const nodeFields = [
  { key:'id',       label:'ID',        placeholder:'gc01',               type:'text' },
  { key:'name',     label:'Name',      placeholder:'gc01',               type:'text' },
  { key:'host',     label:'Host',      placeholder:'192.168.1.10',       type:'text' },
  { key:'port',     label:'Port',      placeholder:'3306',               type:'number' },
  { key:'ssh_port', label:'SSH Port',  placeholder:'22',                 type:'number' },
  { key:'ssh_user', label:'SSH User',  placeholder:'root',               type:'text' },
  { key:'ssh_key',  label:'SSH Key',   placeholder:'/root/.ssh/id_rsa', type:'text' },
  { key:'dc',       label:'DC',        placeholder:'DC1',                type:'text' },
]

function isActive(contour, idx) {
  return cluster.selection.contour === contour && cluster.selection.cluster_index === idx
}

async function createCluster() {
  try {
    await api.post('/api/contours/cluster', { contour: newClusterContour.value, name: newClusterName.value })
    await cluster.fetchContours()
    toast.add({ severity: 'success', summary: 'Создан', detail: newClusterName.value, life: 2500 })
    newClusterName.value = ''; newClusterContour.value = ''
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
}

async function renameCluster(contour, idx, old) {
  const name = prompt(`Новое название (было: ${old})`, old)
  if (!name || name === old) return
  try {
    await api.patch(`/api/contours/${contour}/cluster/${idx}`, { name })
    await cluster.fetchContours()
    toast.add({ severity: 'success', summary: 'Переименован', life: 2000 })
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
}

async function deleteCluster(contour, idx) {
  confirm.require({
    message: `Удалить кластер ${cluster.contours[contour][idx]}?`,
    header: 'Подтверждение',
    icon: 'pi pi-exclamation-triangle',
    acceptSeverity: 'danger',
    accept: async () => {
      await api.delete(`/api/contours/${contour}/cluster/${idx}`)
      await cluster.fetchContours()
      toast.add({ severity: 'info', summary: 'Удалён', life: 2000 })
    }
  })
}

async function addNode() {
  try {
    await api.post('/api/config/node', newNode.value)
    await cluster.fetchStatus()
    toast.add({ severity: 'success', summary: 'Нода добавлена', life: 2000 })
    newNode.value = { id:'', name:'', host:'', port: 3306, ssh_port: 22, ssh_user:'root', ssh_key:'/root/.ssh/id_rsa', dc:'DC1', enabled:true }
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.response?.data?.detail || e.message, life: 3000 }) }
}

async function deleteNode(nodeId) {
  confirm.require({
    message: `Удалить ноду ${nodeId}?`,
    header: 'Подтверждение',
    icon: 'pi pi-exclamation-triangle',
    acceptSeverity: 'danger',
    accept: async () => {
      await api.delete(`/api/config/node/${nodeId}`)
      await cluster.fetchStatus()
      toast.add({ severity: 'info', summary: 'Удалена', life: 2000 })
    }
  })
}

async function addArb() {
  try {
    await api.post('/api/config/arbitrator', newArb.value)
    await cluster.fetchStatus()
    toast.add({ severity: 'success', summary: 'Арбитр добавлен', life: 2000 })
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
}

async function deleteArb(arbId) {
  try {
    await api.delete(`/api/config/arbitrator/${arbId}`)
    await cluster.fetchStatus()
    toast.add({ severity: 'info', summary: 'Удалён', life: 2000 })
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
}

async function saveDB() {
  try {
    await api.post('/api/config/db', { user: dbUser.value, password: dbPass.value })
    toast.add({ severity: 'success', summary: 'Сохранено', life: 2000 })
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
}

async function reloadConfig() {
  loadingReload.value = true
  try {
    await api.post('/api/config/reload')
    const { data } = await api.get('/api/config')
    yamlContent.value = JSON.stringify(data, null, 2)
    toast.add({ severity: 'success', summary: 'Конфиг перезагружен', life: 2000 })
  } catch (e) { toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 3000 }) }
  finally { loadingReload.value = false }
}

onMounted(async () => {
  const { data } = await api.get('/api/config')
  yamlContent.value = JSON.stringify(data, null, 2)
  dbUser.value = data.db?.user || ''
})
</script>

<style scoped>
.page-settings { display: flex; flex-direction: column; }
.settings-section { padding: 0.75rem 0; }
.hint-text { font-size: 13px; color: var(--color-text-secondary); }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }

.settings-sub-title { font-size: 13px; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 0.5rem; }
.contour-label { font-size: 11px; font-weight: 700; color: var(--color-text-muted); letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.375rem; }

.cluster-row {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
}
.cluster-name { flex: 1; font-size: 13px; font-weight: 500; }
.cluster-actions { display: flex; gap: 2px; }

.nodes-list { display: flex; flex-direction: column; gap: 4px; }
.config-node-row {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 13px;
}
.nc-dc { font-size: 10px; background: var(--color-bg-elevated); border: 1px solid var(--color-border); border-radius: 3px; padding: 1px 5px; color: var(--color-text-muted); }

.add-node-form { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: flex-start; }
.form-field { display: flex; flex-direction: column; gap: 3px; }
.field-label { font-size: 11px; font-weight: 600; color: var(--color-text-muted); }
.form-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.tab-toolbar { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; padding: 0.75rem 0; }

.text-ok   { color: var(--color-status-ok); font-size: 12px; }
.text-muted{ color: var(--color-text-muted); font-size: 12px; }
.mono { font-family: var(--font-mono); font-size: 12px; }
</style>
