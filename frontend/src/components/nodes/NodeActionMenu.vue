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
import Button from 'primevue/button'
import Popover from 'primevue/popover'
import { useToast } from 'primevue/usetoast'
import { nodesApi, type NodeAction, type NodeListItem } from '@/api/nodes'
import { useOperationsStore } from '@/stores/operations'

const props = defineProps<{
  node: NodeListItem
  clusterId: number
}>()
const emit = defineEmits<{ actionDone: [] }>()

const popoverRef = ref()
const toast      = useToast()
const opsStore   = useOperationsStore()
const busy       = ref(false)

function toggle(e: Event) { popoverRef.value?.toggle(e) }

const ONLINE_STATES = ['SYNCED', 'DONOR', 'JOINER', 'DESYNCED'] as const

// Бэкенд возвращает wsrep_local_state_comment как "Synced", "Donor" и т..д. —
// нормализуем к uppercase перед сравнением, чтобы не зависеть от регистра.
const stateComment = computed(() =>
    (props.node.live?.wsrep_local_state_comment ?? '').toUpperCase().split('/')[0].trim()
)
const isOnline     = computed(() =>
    ONLINE_STATES.includes(stateComment.value as typeof ONLINE_STATES[number]),
)
const isOffline     = computed(() => !isOnline.value)
// NodeLiveData.readonly (не read_only) — см. api/nodes.ts
const isReadOnly    = computed(() => !!props.node.live?.readonly)
const isMaintenance = computed(() => !!props.node.maintenance)
const isSynced      = computed(() => stateComment.value === 'SYNCED')

const actionGroups = computed(() => [
  {
    label: 'State',
    items: [
      {
        key: 'set-readonly' as NodeAction,
        label: 'Set read-only',
        icon: 'pi pi-lock',
        disabled: isReadOnly.value || isOffline.value,
        danger: false,
      },
      {
        key: 'set-readwrite' as NodeAction,
        label: 'Set read-write',
        icon: 'pi pi-lock-open',
        disabled: !isReadOnly.value || isOffline.value,
        danger: false,
      },
      {
        key: (isMaintenance.value ? 'exit-maintenance' : 'enter-maintenance') as NodeAction,
        label: isMaintenance.value ? 'Exit maintenance' : 'Enter maintenance',
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
        disabled: isOnline.value,
        danger: false,
      },
      {
        key: 'rejoin-force' as NodeAction,
        label: 'Force rejoin',
        icon: 'pi pi-sign-in',
        disabled: isOnline.value && isSynced.value,
        danger: true,
      },
    ],
  },
])

async function run(action: NodeAction) {
  popoverRef.value?.hide()

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

    if (result.operation_id) {
      opsStore.setActiveOperation(props.clusterId, result.operation_id)
    }

    toast.add({
      severity: 'success',
      summary: 'Done',
      detail: result.message ?? `Action '${action}' accepted`,
      life: 3000,
    })
    emit('actionDone')
  } catch (err: any) {
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
