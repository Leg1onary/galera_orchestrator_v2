<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Настройки</h1>
        <p class="page-subtitle">Конфигурация нод кластера, подключения и параметры системы</p>
      </div>
      <button class="btn btn-primary" @click="showAddNodeModal = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Добавить ноду
      </button>
    </div>

    <!-- Nodes list -->
    <div class="form-section">
      <div class="form-section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="2" width="20" height="8" rx="2"/>
          <rect x="2" y="14" width="20" height="8" rx="2"/>
        </svg>
        Ноды кластера
      </div>
      <div v-if="!cluster.nodes.length" style="color:var(--text-muted);font-size:var(--text-sm);padding:var(--space-4)">
        Нет нод. Добавьте первую ноду через кнопку выше.
      </div>
      <div class="node-list">
        <div v-for="node in cluster.nodes" :key="node.id" class="node-list-item">
          <div class="nli-info">
            <div class="nli-name">{{ node.name || node.id }}</div>
            <div class="nli-host">{{ node.host }}:{{ node.port || 3306 }} · SSH :{{ node.ssh_port || 22 }}</div>
          </div>
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
            <span v-if="node.dc" class="dc-badge">{{ node.dc }}</span>
            <span class="nli-role-badge" :class="node.online ? 'badge-synced' : 'badge-offline'">
              {{ node.online ? (node.state || 'Online') : 'Offline' }}
            </span>
            <span v-if="node.read_only" class="nli-role-badge badge-warn">R/O</span>
          </div>
          <div style="display:flex;gap:6px">
            <button class="btn btn-ghost btn-sm" @click="editNode(node)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              Редактировать
            </button>
            <button class="btn btn-danger btn-sm" @click="confirmRemoveNode(node)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
              </svg>
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Arbitrators list -->
    <div class="form-section">
      <div class="form-section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/>
        </svg>
        Арбитры (garbd)
        <button class="btn btn-ghost btn-sm" style="margin-left:auto" @click="showAddArbModal = true">+ Добавить арбитр</button>
      </div>
      <div v-if="!cluster.arbitrators.length" style="color:var(--text-muted);font-size:var(--text-sm);padding:var(--space-4)">
        Нет арбитраторов.
      </div>
      <div class="node-list">
        <div v-for="arb in cluster.arbitrators" :key="arb.id" class="node-list-item">
          <div class="nli-info">
            <div class="nli-name">{{ arb.id || arb.host }}</div>
            <div class="nli-host">{{ arb.host }} · SSH :{{ arb.ssh_port || 22 }} · DC: {{ arb.dc || '—' }}</div>
          </div>
          <span class="nli-role-badge" :class="arb.online ? 'badge-synced' : 'badge-offline'">
            {{ arb.online ? 'RUNNING' : 'DOWN' }}
          </span>
          <div style="display:flex;gap:6px">
            <button class="btn btn-ghost btn-sm" @click="editArbitrator(arb)">Редактировать</button>
            <button class="btn btn-danger btn-sm" @click="confirmRemoveArb(arb)">Удалить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- General settings -->
    <div class="form-section">
      <div class="form-section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>
        </svg>
        Общие настройки
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Имя кластера</label>
          <input class="form-input" type="text" v-model="clusterName" placeholder="galera_cluster">
        </div>
        <div class="form-group">
          <label class="form-label">API URL <span>опц.</span></label>
          <input class="form-input" type="text" v-model="apiUrl" placeholder="http://localhost:8000">
          <p class="form-hint">Пусто = автоопределение из window.location</p>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">DB пользователь</label>
          <input class="form-input" type="text" v-model="dbUser" placeholder="galera_monitor">
        </div>
        <div class="form-group">
          <label class="form-label">DB пароль</label>
          <input class="form-input" type="password" v-model="dbPass" placeholder="••••••••">
        </div>
      </div>
      <button class="btn btn-primary" @click="saveSettings">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
          <polyline points="17 21 17 13 7 13 7 21"/>
          <polyline points="7 3 7 8 15 8"/>
        </svg>
        Сохранить настройки
      </button>
    </div>

    <!-- Add Node Modal -->
    <Dialog v-model:visible="showAddNodeModal" header="Добавить ноду" :modal="true" style="width:560px">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Имя ноды (ID)</label>
          <input class="form-input" type="text" v-model="newNode.id" placeholder="gc01">
        </div>
        <div class="form-group">
          <label class="form-label">IP-адрес / hostname</label>
          <input class="form-input" type="text" v-model="newNode.host" placeholder="192.168.1.10">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Порт MariaDB</label>
          <input class="form-input" type="number" v-model="newNode.port" value="3306">
        </div>
        <div class="form-group">
          <label class="form-label">SSH порт</label>
          <input class="form-input" type="number" v-model="newNode.ssh_port" value="22">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">SSH пользователь</label>
          <input class="form-input" type="text" v-model="newNode.ssh_user" value="root">
        </div>
        <div class="form-group">
          <label class="form-label">Датацентр (DC)</label>
          <input class="form-input" type="text" v-model="newNode.dc" placeholder="DC1">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">SSH ключ (путь)</label>
        <input class="form-input" type="text" v-model="newNode.ssh_key" placeholder="~/.ssh/id_rsa">
      </div>
      <template #footer>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button class="btn btn-ghost" @click="showAddNodeModal = false">Отмена</button>
          <button class="btn btn-primary" @click="addNode">Добавить</button>
        </div>
      </template>
    </Dialog>

    <!-- Add Arbitrator Modal -->
    <Dialog v-model:visible="showAddArbModal" header="Добавить арбитр (garbd)" :modal="true" style="width:480px">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">IP-адрес арбитра</label>
          <input class="form-input" type="text" v-model="newArb.host" placeholder="10.0.0.13">
        </div>
        <div class="form-group">
          <label class="form-label">SSH порт</label>
          <input class="form-input" type="number" v-model="newArb.ssh_port" value="22">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Датацентр (DC)</label>
          <input class="form-input" type="text" v-model="newArb.dc" placeholder="DC1">
        </div>
        <div class="form-group">
          <label class="form-label">ID арбитра <span>опц.</span></label>
          <input class="form-input" type="text" v-model="newArb.id" placeholder="arb01 (авто)">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Адрес для gcomm</label>
        <input class="form-input" type="text" v-model="newArb.gcomm" placeholder="gcomm://10.0.0.11:4567,10.0.0.12:4567">
      </div>
      <template #footer>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button class="btn btn-ghost" @click="showAddArbModal = false">Отмена</button>
          <button class="btn btn-primary" @click="addArbitrator">Добавить арбитр</button>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Dialog from 'primevue/dialog'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { useClusterStore } from '@/stores/cluster.js'
import api from '@/api/index.js'

const cluster = useClusterStore()
const toast   = useToast()
const confirm = useConfirm()

// Modals
const showAddNodeModal = ref(false)
const showAddArbModal  = ref(false)

// New node form
const newNode = ref({ id: '', host: '', port: 3306, ssh_port: 22, ssh_user: 'root', dc: 'DC1', ssh_key: '~/.ssh/id_rsa' })

// New arb form
const newArb  = ref({ id: '', host: '', ssh_port: 22, dc: 'DC1', gcomm: '' })

// General settings
const clusterName = ref('')
const apiUrl      = ref('')
const dbUser      = ref('')
const dbPass      = ref('')

async function addNode() {
  if (!newNode.value.host) return
  try {
    await api.post('/api/nodes', newNode.value)
    toast.add({ severity: 'success', summary: 'Нода добавлена', life: 3000 })
    showAddNodeModal.value = false
    newNode.value = { id: '', host: '', port: 3306, ssh_port: 22, ssh_user: 'root', dc: 'DC1', ssh_key: '~/.ssh/id_rsa' }
    await cluster.fetchStatus()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 5000 })
  }
}

async function addArbitrator() {
  if (!newArb.value.host) return
  try {
    await api.post('/api/arbitrators', newArb.value)
    toast.add({ severity: 'success', summary: 'Арбитр добавлен', life: 3000 })
    showAddArbModal.value = false
    newArb.value = { id: '', host: '', ssh_port: 22, dc: 'DC1', gcomm: '' }
    await cluster.fetchStatus()
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 5000 })
  }
}

function editNode(node) {
  toast.add({ severity: 'info', summary: 'Редактирование', detail: `Редактирование ноды ${node.id} — в разработке`, life: 3000 })
}

function editArbitrator(arb) {
  toast.add({ severity: 'info', summary: 'Редактирование', detail: `Редактирование арбитра ${arb.id} — в разработке`, life: 3000 })
}

function confirmRemoveNode(node) {
  confirm.require({
    message: `Удалить ноду "${node.name || node.id}"?`,
    header: 'Подтверждение',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await api.delete(`/api/nodes/${node.id}`)
        toast.add({ severity: 'success', summary: 'Нода удалена', life: 3000 })
        await cluster.fetchStatus()
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 5000 })
      }
    }
  })
}

function confirmRemoveArb(arb) {
  confirm.require({
    message: `Удалить арбитр "${arb.id || arb.host}"?`,
    header: 'Подтверждение',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await api.delete(`/api/arbitrators/${arb.id}`)
        toast.add({ severity: 'success', summary: 'Арбитр удалён', life: 3000 })
        await cluster.fetchStatus()
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 5000 })
      }
    }
  })
}

async function saveSettings() {
  try {
    await api.post('/api/config', {
      cluster_name: clusterName.value,
      api_url: apiUrl.value,
      db_user: dbUser.value,
      db_pass: dbPass.value,
    })
    toast.add({ severity: 'success', summary: 'Сохранено', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: e.message, life: 5000 })
  }
}
</script>
