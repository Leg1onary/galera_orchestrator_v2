import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
    maintenanceApi,
    type MaintenanceNodeState,
    type RollingRestartStatus,
} from '@/api/maintenance'
import { useWsStore } from '@/stores/ws'

export type RRWizardStep = 1 | 2 | 3

export const useMaintenanceStore = defineStore('maintenance', () => {
    // ── Cluster context ───────────────────────────────────────────────────────
    const clusterId = ref<number | null>(null)

    // ── Node maintenance state ────────────────────────────────────────────────
    const nodes = ref<MaintenanceNodeState[]>([])
    const nodesLoading = ref(false)
    const nodesError = ref<string | null>(null)

    // Per-node loading flags (enter/exit maintenance)
    const nodeActionLoading = ref<Record<number, boolean>>({})

    // ── Rolling restart wizard ────────────────────────────────────────────────
    const wizardOpen = ref(false)
    const wizardStep = ref<RRWizardStep>(1)

    // Step 1 config
    const nodeOrder = ref<number[]>([])          // node_ids в порядке рестарта
    const waitTimeoutSec = ref(300)

    // Step 2 progress (из WS + polling fallback)
    const operationId = ref<string | null>(null)
    const rrStatus = ref<RollingRestartStatus | null>(null)
    const cancelling = ref(false)

    // ── Computed ──────────────────────────────────────────────────────────────
    const enabledNodes = computed(() =>
        nodes.value.filter((n) => n.enabled)
    )

    const hasDrift = computed(() =>
        nodes.value.some((n) => n.maintenance_drift)
    )

    const currentRestartNode = computed(() =>
        rrStatus.value?.current_node_id
            ? nodes.value.find((n) => n.node_id === rrStatus.value!.current_node_id) ?? null
            : null
    )

    const operationRunning = computed(() =>
        rrStatus.value?.state === 'running' || rrStatus.value?.state === 'pending'
    )

    // ── Actions ───────────────────────────────────────────────────────────────
    async function init(cId: number) {
        wsUnsub?.() // явная отписка перед reset
        clusterId.value = cId
        nodeOrder.value = []
        wizardOpen.value = false
        wizardStep.value = 1
        rrStatus.value = null
        operationId.value = null
        subscribeWs()
        await loadNodes()

        // [MAJOR FIX] Polling fallback: восстанавливаем состояние при заходе во время активной операции
        // ТЗ п.14: если rolling restart уже идёт — открываем wizard на Step 2
        try {
            const status = await maintenanceApi.getStatus(cId)
            const op = status.active_operation
            if (op && ['pending', 'running', 'cancel_requested'].includes(op.status)) {
                operationId.value = op.id
                rrStatus.value = {
                    operation_id: op.id,
                    state: op.status as RollingRestartStatus['state'],
                    current_node_id: op.current_node_id ?? null,
                    completed_node_ids: op.completed_node_ids ?? [],
                    failed_node_id: op.failed_node_id ?? null,
                    progress_pct: op.progress_pct ?? 0,
                    message: op.message ?? null,
                    error: op.error_message ?? null,
                    started_at: op.started_at ?? null,
                    finished_at: null,
                }
                wizardOpen.value = true
                wizardStep.value = 2
            }
        } catch {
            // нет активной операции — норма
        }
    }

    async function loadNodes() {
        if (!clusterId.value) return
        nodesLoading.value = true
        nodesError.value = null
        try {
            nodes.value = await maintenanceApi.listNodes(clusterId.value)
            // Устанавливаем дефолтный порядок если ещё не задан
            if (nodeOrder.value.length === 0) {
                nodeOrder.value = enabledNodes.value.map((n) => n.node_id)
            }
        } catch (err: any) {
            nodesError.value = err?.response?.data?.detail ?? err.message
        } finally {
            nodesLoading.value = false
        }
    }

    async function toggleMaintenance(nodeId: number, enter: boolean) {
        if (!clusterId.value) return
        nodeActionLoading.value = { ...nodeActionLoading.value, [nodeId]: true }
        try {
            if (enter) {
                await maintenanceApi.enterMaintenance(clusterId.value, nodeId)
            } else {
                await maintenanceApi.exitMaintenance(clusterId.value, nodeId)
            }
            await loadNodes()
        } catch (err) {
            // [MAJOR FIX] пробрасываем — UI должен показать ошибку
            throw err
        } finally {
            nodeActionLoading.value = { ...nodeActionLoading.value, [nodeId]: false }
        }
    }

    function openWizard() {
        wizardOpen.value = true
        wizardStep.value = 1
        rrStatus.value = null
        // Сбрасываем порядок на текущие enabled ноды
        nodeOrder.value = enabledNodes.value.map((n) => n.node_id)
    }

    function closeWizard() {
        if (operationRunning.value) return  // нельзя закрыть во время операции
        wizardOpen.value = false
        wizardStep.value = 1
    }

    async function startRollingRestart() {
        if (!clusterId.value) return
        try {
            const res = await maintenanceApi.startRollingRestart(clusterId.value, {
                node_order: nodeOrder.value,
                wait_timeout_sec: waitTimeoutSec.value,
            })
            operationId.value = res.operation_id
            rrStatus.value = {
                operation_id: res.operation_id,
                state: 'pending',
                current_node_id: null,
                completed_node_ids: [],
                failed_node_id: null,
                progress_pct: 0,
                message: 'Starting…',
                error: null,
                started_at: null,
                finished_at: null,
            }
            wizardStep.value = 2
        } catch (err: any) {
            throw err  // пробрасываем в компонент для показа ошибки
        }
    }

    async function cancelOperation() {
        if (!clusterId.value) return
        cancelling.value = true
        try {
            await maintenanceApi.cancel(clusterId.value)
        } finally {
            cancelling.value = false
        }
    }

    // ── WS subscription ───────────────────────────────────────────────────────
    let wsUnsub: (() => void) | null = null

    function subscribeWs() {
        const wsStore = useWsStore()
        wsUnsub?.()
        wsUnsub = wsStore.on((event) => {
            if (event.event === 'operation_progress' && rrStatus.value) {
                rrStatus.value = {
                    ...rrStatus.value,
                    state: 'running',
                    progress_pct: (event.payload?.progress_pct as number) ?? rrStatus.value.progress_pct,
                    message: (event.payload?.message as string) ?? rrStatus.value.message,
                    current_node_id: (event.payload?.current_node_id as number) ?? rrStatus.value.current_node_id,
                    completed_node_ids: (event.payload?.completed_node_ids as number[]) ?? rrStatus.value.completed_node_ids,
                }
            }

            if (event.event === 'operation_finished' && rrStatus.value) {
                // [BLOCKER FIX] читаем payload.status как строку, не payload.success как bool
                // [BLOCKER FIX] operation_cancelled не существует — обрабатываем здесь
                const status = event.payload?.status as string

                rrStatus.value = {
                    ...rrStatus.value,
                    // [BLOCKER FIX] 'success' вместо 'finished'
                    state: status === 'failed'
                        ? 'failed'
                        : status === 'cancelled'
                            ? 'cancelled'
                            : 'success',
                    progress_pct: 100,
                    error: (event.payload?.error_message as string) ?? null,
                    finished_at: new Date().toISOString(),
                }
                wizardStep.value = 3
                loadNodes()
            }

            // [MAJOR FIX] debounce через nodesLoading guard — не спамим запросами
            if (event.event === 'node_state_changed' && !nodesLoading.value) {
                loadNodes()
            }
        })
    }

    function destroy() {
        wsUnsub?.()
        wsUnsub = null
    }

    return {
        // state
        clusterId, nodes, nodesLoading, nodesError, nodeActionLoading,
        wizardOpen, wizardStep,
        nodeOrder, waitTimeoutSec,
        operationId, rrStatus, cancelling,
        // computed
        enabledNodes, hasDrift, currentRestartNode, operationRunning,
        // actions
        init, destroy, loadNodes,
        toggleMaintenance, openWizard, closeWizard,
        startRollingRestart, cancelOperation,
    }
})