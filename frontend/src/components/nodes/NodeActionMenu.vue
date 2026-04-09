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
    <div class="flex flex-col gap-1 min-w-36 py-1">
      <template v-for="group in actionGroups" :key="group.label">
        <div class="px-3 pt-2 pb-1 text-xs text-muted-color uppercase tracking-wide">
          {{ group.label }}
        </div>
        <button
            v-for="action in group.items"
            :key="action.key"
            class="action-item"
            :class="{ 'action-item--danger': action.danger }"
            :disabled="action.disabled || busy"
            @click="run(action.key)"
        >
          <i :class="action.icon" class="text-sm" />
          {{ action.label }}
        </button>
      </template>
    </div>
  </Popover>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button, Popover, useToast } from 'primevue'
import { nodesApi, type NodeAction, type NodeListItem } from '@/api/nodes'
import { useOperationsStore } from '@/stores/operations'

const props = defineProps<{ node: NodeListItem; clusterId: number }>()
const emit = defineEmits<{ actionDone: [] }>()

const popoverRef = ref()
const toast = useToast()
const opsStore = useOperationsStore()
const busy = ref(false)

function toggle(e: Event) { popoverRef.value?.toggle(e) }

const isMaintenance = computed(() => props.node.maintenance)
const isReadOnly = computed(() => props.node.read_only)
const isOnline = computed(
    () => props.node.wsrep_connected && props.node.last_seen
)

const actionGroups = computed(() => [
  {
    label: 'State',
    items: [
      {
        key: 'set-readonly' as NodeAction,
        label: 'Set read-only',
        icon: 'pi pi-lock',
        disabled: isReadOnly.value || !isOnline.value,
        danger: false,
      },
      {
        key: 'set-readwrite' as NodeAction,
        label: 'Set read-write',
        icon: 'pi pi-lock-open',
        disabled: !isReadOnly.value || !isOnline.value,
        danger: false,
      },
      {
        key: isMaintenance.value ? 'exit-maintenance' : 'enter-maintenance' as NodeAction,
        label: isMaintenance.value ? 'Exit maintenance' : 'Enter maintenance',
        icon: isMaintenance.value ? 'pi pi-wrench' : 'pi pi-wrench',
        disabled: !isOnline.value,
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
        disabled: !isOnline.value,
        danger: true,
      },
      {
        key: 'stop' as NodeAction,
        label: 'Stop',
        icon: 'pi pi-stop-circle',
        disabled: !isOnline.value,
        danger: true,
      },
      {
        key: 'start' as NodeAction,
        label: 'Start',
        icon: 'pi pi-play',
        disabled: !!isOnline.value,
        danger: false,
      },
      {
        key: 'rejoin-force' as NodeAction,
        label: 'Force rejoin',
        icon: 'pi pi-sign-in',
        disabled: !!isOnline.value,
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
    toast.add({
      severity: 'success',
      summary: 'Done',
      detail: result.message,
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
.action-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
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
.action-item:hover:not(:disabled) { background: var(--color-surface-offset); }
.action-item:disabled { opacity: 0.4; cursor: not-allowed; }
.action-item--danger { color: var(--color-error); }
.action-item--danger:hover:not(:disabled) {
  background: color-mix(in oklch, var(--color-error) 10%, transparent);
}
</style>