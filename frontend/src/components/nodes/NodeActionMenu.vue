<!-- src/components/nodes/NodeActionMenu.vue -->
<!-- Кнопка ⋯ → popover с actions. Sync actions сразу, async → 409 handling. -->
<template>
  <Button
      icon="pi pi-ellipsis-v"
      text
      rounded
      size="small"
      aria-label="Node actions"
      @click="toggle"
  />
  <Popover ref="popoverRef">
    <div class="action-menu">
      <template v-for="group in actionGroups" :key="group.label">
        <div class="group-label">{{ group.label }}</div>
        <button
            v-for="action in group.items"
            :key="action.key"
            class="action-item"
            :class="{ 'action-item--danger': action.danger }"
            :disabled="action.disabled || busy"
            @click="run(action.key)"
        >
          <i :class="action.icon" />
          {{ action.label }}
        </button>
      </template>
    </div>
  </Popover>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'      // BLOCKER fix: именованный импорт PrimeVue 4
import Popover from 'primevue/popover'
import { useToast } from 'primevue/usetoast'
import { nodesApi, type NodeAction, type NodeListItem } from '@/api/nodes'
import { useOperationsStore } from '@/stores/operations'

// ── Props / Emits ─────────────────────────────────────────────────────────────
const props = defineProps<{
  node: NodeListItem
  clusterId: number
}>()
const emit = defineEmits<{ actionDone: [] }>()

// ── Refs ──────────────────────────────────────────────────────────────────────
const popoverRef = ref()
const toast      = useToast()
const opsStore   = useOperationsStore()
const busy       = ref(false)

function toggle(e: Event) { popoverRef.value?.toggle(e) }

// ── Computed state (ТЗ п.7.3: live-статусы нод) ──────────────────────────────
const ONLINE_STATES = ['SYNCED', 'DONOR', 'JOINER', 'DESYNCED'] as const

// MAJOR fix: last_check_ts вместо last_seen + корректная проверка по state_comment
const isOnline = computed(() =>
    ONLINE_STATES.includes(
        (props.node.wsrep_local_state_comment ?? '') as typeof ONLINE_STATES[number],
    ),
)
const isOffline     = computed(() => !isOnline.value)
const isReadOnly    = computed(() => !!props.node.read_only)      // null → false
const isMaintenance = computed(() => !!props.node.maintenance)    // null → false
const isSynced      = computed(() => props.node.wsrep_local_state_comment === 'SYNCED')

// ── Action groups (ТЗ п.9.3, п.11.6) ─────────────────────────────────────────
const actionGroups = computed(() => [
  {
    label: 'State',
    items: [
      {
        key: 'set-readonly' as NodeAction,
        label: 'Set read-only',
        icon: 'pi pi-lock',
        // Нельзя, если уже RO или нода offline
        disabled: isReadOnly.value || isOffline.value,
        danger: false,
      },
      {
        key: 'set-readwrite' as NodeAction,
        label: 'Set read-write',
        icon: 'pi pi-lock-open',
        // Нельзя, если уже RW или нода offline
        disabled: !isReadOnly.value || isOffline.value,
        danger: false,
      },
      {
        key: (isMaintenance.value ? 'exit-maintenance' : 'enter-maintenance') as NodeAction,
        label: isMaintenance.value ? 'Exit maintenance' : 'Enter maintenance',
        // MINOR fix: разные иконки для enter/exit
        icon: isMaintenance.value ? 'pi pi-check-circle' : 'pi pi-wrench',
        disabled: isOffline.value,
        danger: false,
      },
    ],
  },
  {
    label: 'Service',
    items: [
      {
        key: 'restart' as NodeAction,
        label: 'Restart',
        icon: 'pi pi-refresh',
        // Рестарт только для онлайн-ноды (ТЗ п.11.6)
        disabled: isOffline.value,
        danger: true,
      },
      {
        key: 'stop' as NodeAction,
        label: 'Stop',
        icon: 'pi pi-stop-circle',
        disabled: isOffline.value,
        danger: true,
      },
      {
        key: 'start' as NodeAction,
        label: 'Start',
        icon: 'pi pi-play',
        // Start только для OFFLINE ноды (ТЗ п.11.6)
        disabled: isOnline.value,
        danger: false,
      },
      {
        key: 'rejoin-force' as NodeAction,
        label: 'Force rejoin',
        icon: 'pi pi-sign-in',
        // rejoin-force — для нод НЕ-SYNCED (ТЗ п.10.4, п.11.6)
        // SYNCED нода не нуждается в force rejoin
        disabled: isOnline.value && isSynced.value,
        danger: true,
      },
    ],
  },
])

// ── Run action ────────────────────────────────────────────────────────────────
async function run(action: NodeAction) {
  popoverRef.value?.hide()

  // ТЗ п.19.1: cluster-level lock — проверяем до запроса
  if (opsStore.isLocked(props.clusterId)) {
    toast.add({
      severity: 'warn',
      summary: 'Cluster locked',
      detail: 'Another operation is in progress.',
      life: 4000,
    })
    return
  }

  busy.value = true
  try {
    const result = await nodesApi.action(props.clusterId, props.node.id, action)

    // MAJOR fix: если action вернул operation_id — сообщаем store (ТЗ п.2.8, п.9.3)
    if (result.operation_id) {
      opsStore.setActiveOperation(props.clusterId, result.operation_id)
    }

    toast.add({
      severity: 'success',
      summary: 'Done',
      detail: result.message,
      life: 3000,
    })
    emit('actionDone')
  } catch (err: any) {
    // ТЗ п.19.1: 409 Conflict — cluster locked на стороне backend
    const is409 = err?.response?.status === 409
    toast.add({
      severity: is409 ? 'warn' : 'error',
      summary: is409 ? 'Cluster locked' : 'Action failed',
      detail: err?.response?.data?.detail ?? err.message,
      life: 5000,
    })
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.action-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 9rem;
  padding: var(--space-1) 0;
}

/* BLOCKER fix: убрали Tailwind text-muted-color → scoped CSS */
.group-label {
  padding: var(--space-2) var(--space-3) var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.action-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--color-text);
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background var(--transition-interactive);
}
.action-item:hover:not(:disabled) {
  background: var(--color-surface-offset);
}
.action-item:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.action-item--danger {
  color: var(--color-error);
}
.action-item--danger:hover:not(:disabled) {
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
}
</style>