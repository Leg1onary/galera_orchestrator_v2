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
    // ── Cluster context ─────────────────────────────────────────────────────────
    const clusterId = ref<number | null>(null)

    // ── Node maintenance state ──────────────────────────────────────────────────
    const nodes         = ref<MaintenanceNodeState[]>([])
    const nodesLoading  = ref(false)
    const nodesError    = ref<string | null>(null)

    // Per-node loading flags
    const nodeActionLoading = ref<Record<number, boolean>>({})

    // ── Rolling restart wizard ──────────────────────────────────────────────────
    const wizardOpen     = ref(false)
    const wizardStep     = ref<RRWizardStep>(1)
    const nodeOrder      = ref<number[]>([])
    const waitTimeoutSec = ref(300)

    const operationId = ref<string | null>(null)
    const rrStatus    = ref<RollingRestartStatus | null>(null)
    const cancelling  = ref(false)

    // ── Computed ────────────────────────────────────────────────────────────────
    const enabledNodes = computed(() =>
        nodes.value.filter((n) => n.enabled)
    )

    const hasDrift = computed(() =>
        nodes.value.some((n) => n.maintenance_drift)
    )

    const currentRestartNode = computed(() =>
        rrStatus.value?.current_node_id
            // BLOCKER fix: n.id вместо n.node_id
            ? nodes.value.find((n) => n.id === rrStatus.value!.current_node_id) ?? null
            : null
    )

    const operationRunning = computed(() =>
        rrStatus.value?.state === 'running' || rrStatus.value?.state === 'pending'
    )

    // ── WS subscription — ref чтобы не терять при HMR ──────────────────────────
    // MAJOR fix: ref вместо module-level let
    const wsUnsub = ref<(() => void) | null>(null)

    function subscribeWs() {
        const wsStore = useWsStore()
        wsUnsub.value?.()

        wsUnsub.value = wsStore.on((event) => {
            if (event.event === 'operation_progress' && rrStatus.value) {
                const p = event.payload as Record<string, unknown>
                rrStatus.value = {
                    ...rrStatus.value,
                    state:              'running',
                    progress_pct:       (p.progress_pct       as number)   ?? rrStatus.value.progress_pct,
                    message:            (p.message            as string)   ?? rrStatus.value.message,
                    current_node_id:    (p.current_node_id    as number)   ?? rrStatus.value.current_node_id,
                    completed_node_ids: (p.completed_node_ids as number[]) ?? rrStatus.value.completed_node_ids,
                }
            }

            if (event.event === 'operation_finished' && rrStatus.value) {
                const p      = event.payload as Record<string, unknown>
                const status = p.status as string

                rrStatus.value = {
                    ...rrStatus.value,
                    // BLOCKER fix: 'finished' вместо 'success' — соответствует RollingRestartStatus['state'] и Step3
                    state:       status === 'failed' ? 'failed' : status === 'cancelled' ? 'cancelled' : 'finished',
                    progress_pct: 100,
                    error:        (p.error_message as string) ?? null,
                    finished_at:  new Date().toISOString(),
                }
                wizardStep.value = 3
                // MINOR fix: catch вместо fire-and-forget
                loadNodes().catch(console.error)
            }

            if (event.event === 'node_state_changed' && !nodesLoading.value) {
                loadNodes().catch(console.error)
            }
        })
    }

    // ── Actions ─────────────────────────────────────────────────────────────────
    async function init(cId: number) {
        wsUnsub.value?.()
        clusterId.value     = cId
        nodeOrder.value     = []
        wizardOpen.value    = false
        wizardStep.value    = 1
        rrStatus.value      = null
        operationId.value   = null

        subscribeWs()
        await loadNodes()

        // Восстановление состояния при заходе во время активной операции (ТЗ п.14)
        try {
            const status = await maintenanceApi.getStatus(cId)
            const op     = status.active_operation
            if (op && ['pending', 'running', 'cancel_requested'].includes(op.status)) {
                operationId.value = op.id
                rrStatus.value = {
                    operation_id:       op.id,
                    state:              op.status as RollingRestartStatus['state'],
                    current_node_id:    op.current_node_id    ?? null,
                    completed_node_ids: op.completed_node_ids ?? [],
                    failed_node_id:     op.failed_node_id     ?? null,
                    progress_pct:       op.progress_pct       ?? 0,
                    message:            op.message            ?? null,
                    error:              op.error_message      ?? null,
                    started_at:         op.started_at         ?? null,
                    finished_at:        null,
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
        nodesError.value   = null
        try {
            nodes.value = await maintenanceApi.listNodes(clusterId.value)
            if (nodeOrder.value.length === 0) {
                // BLOCKER fix: n.id вместо n.node_id
                nodeOrder.value = enabledNodes.value.map((n) => n.id)
            }
        } catch (err: any) {
            nodesError.value = err?.response?.data?.detail ?? err.message
        } finally {
            nodesLoading.value = false
        }
    }

    async function toggleMaintenance(nodeId: number, enter: boolean) {
        if (!clusterId.value) return
        // MAJOR fix: прямая мутация вместо spread — реактивность не теряется
        nodeActionLoading.value[nodeId] = true
        try {
            if (enter) {
                await maintenanceApi.enterMaintenance(clusterId.value, nodeId)
            } else {
                await maintenanceApi.exitMaintenance(clusterId.value, nodeId)
            }
            await loadNodes()
        } catch (err) {
            throw err
        } finally {
            nodeActionLoading.value[nodeId] = false
        }
    }

    function openWizard() {
        wizardOpen.value    = true
        wizardStep.value    = 1
        rrStatus.value      = null
        operationId.value   = null
        // BLOCKER fix: n.id вместо n.node_id
        nodeOrder.value = enabledNodes.value.map((n) => n.id)
    }

    function closeWizard() {
        if (operationRunning.value) return
        wizardOpen.value  = false
        wizardStep.value  = 1
        // MINOR fix: сброс чтобы при повторном openWizard не было стейла
        rrStatus.value    = null
        operationId.value = null
    }

    // BLOCKER fix: добавлен resetWizard() — вызывается из Step3 "Run again"
    function resetWizard() {
        wizardStep.value    = 1
        rrStatus.value      = null
        operationId.value   = null
        nodeOrder.value     = enabledNodes.value.map((n) => n.id)
    }

    async function startRollingRestart() {
        if (!clusterId.value) return
        const res = await maintenanceApi.startRollingRestart(clusterId.value, {
            node_order:        nodeOrder.value,
            wait_timeout_sec:  waitTimeoutSec.value,
        })
        operationId.value = res.operation_id
        rrStatus.value = {
            operation_id:       res.operation_id,
            state:              'pending',
            current_node_id:    null,
            completed_node_ids: [],
            failed_node_id:     null,
            progress_pct:       0,
            message:            'Starting…',
            error:              null,
            started_at:         null,
            finished_at:        null,
        }
        wizardStep.value = 2
        // ошибка пробрасывается наверх — try/catch в компоненте
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

    function destroy() {
        wsUnsub.value?.()
        wsUnsub.value = null
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
        toggleMaintenance, openWizard, closeWizard, resetWizard,
        startRollingRestart, cancelOperation,
    }
})