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

    // Per-node loading flags: maintenance toggle
    const nodeActionLoading = ref<Record<number, boolean>>({})
    // Per-node loading flags: desync/resync
    const nodeDesyncLoading = ref<Record<number, boolean>>({})

    // ── Rolling restart wizard ──────────────────────────────────────────────────
    const wizardOpen     = ref(false)
    const wizardStep     = ref<RRWizardStep>(1)
    const nodeOrder      = ref<number[]>([])
    const waitTimeoutSec = ref(300)

    const operationId = ref<number | null>(null)
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
            ? nodes.value.find((n) => n.id === rrStatus.value!.current_node_id) ?? null
            : null
    )

    const operationRunning = computed(() =>
        rrStatus.value?.state === 'running' || rrStatus.value?.state === 'pending'
    )

    // ── WS subscription ─────────────────────────────────────────────────────────
    const wsUnsub = ref<(() => void) | null>(null)

    function subscribeWs() {
        const wsStore = useWsStore()
        wsUnsub.value?.()

        wsUnsub.value = wsStore.on((event) => {
            if (event.event === 'operation_progress' && rrStatus.value) {
                const p      = event.payload as Record<string, unknown>
                const detail = (p.detail ?? {}) as Record<string, unknown>
                const incomingNodeId = detail.node_id as number | undefined

                const prevCompleted  = rrStatus.value.completed_node_ids
                const prevCurrentId  = rrStatus.value.current_node_id
                const newCompleted =
                    incomingNodeId !== undefined &&
                    prevCurrentId  !== null &&
                    incomingNodeId !== prevCurrentId
                        ? [...prevCompleted, prevCurrentId]
                        : prevCompleted

                rrStatus.value = {
                    ...rrStatus.value,
                    state:              'running',
                    message:            (p.message as string) ?? rrStatus.value.message,
                    current_node_id:    incomingNodeId         ?? rrStatus.value.current_node_id,
                    completed_node_ids: newCompleted,
                    progress_pct: nodes.value.length > 0
                        ? Math.round((newCompleted.length / nodes.value.length) * 100)
                        : rrStatus.value.progress_pct,
                }
            }

            if (event.event === 'operation_finished' && rrStatus.value) {
                const p      = event.payload as Record<string, unknown>
                const status = p.status as string

                const normalizedState: RollingRestartStatus['state'] =
                    status === 'failed'    ? 'failed'
                        : status === 'cancelled' ? 'cancelled'
                            : 'finished'

                const allNodeIds = nodes.value.map((n) => n.id)

                rrStatus.value = {
                    ...rrStatus.value,
                    state:              normalizedState,
                    progress_pct:       normalizedState === 'finished' ? 100 : rrStatus.value.progress_pct,
                    completed_node_ids: normalizedState === 'finished'
                        ? allNodeIds
                        : rrStatus.value.completed_node_ids,
                    error:       (p.error_message as string) ?? null,
                    finished_at: new Date().toISOString(),
                }
                wizardStep.value = 3
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

        try {
            const status = await maintenanceApi.getStatus(cId)
            const op     = status.active_operation
            if (op && ['pending', 'running', 'cancel_requested'].includes(op.status)) {
                operationId.value = op.id
                rrStatus.value = {
                    operation_id:       op.id,
                    state:              op.status as RollingRestartStatus['state'],
                    current_node_id:    null,
                    completed_node_ids: [],
                    failed_node_id:     null,
                    progress_pct:       0,
                    message:            null,
                    error:              op.error_message ?? null,
                    started_at:         op.started_at    ?? null,
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
        nodeActionLoading.value[nodeId] = true
        try {
            if (enter) {
                await maintenanceApi.enterMaintenance(clusterId.value, nodeId)
            } else {
                await maintenanceApi.exitMaintenance(clusterId.value, nodeId)
            }
            await loadNodes()
        } finally {
            nodeActionLoading.value[nodeId] = false
        }
    }

    async function toggleDesync(nodeId: number, desync: boolean) {
        if (!clusterId.value) return
        nodeDesyncLoading.value[nodeId] = true
        try {
            if (desync) {
                await maintenanceApi.desyncNode(clusterId.value, nodeId)
            } else {
                await maintenanceApi.resyncNode(clusterId.value, nodeId)
            }
            await loadNodes()
        } finally {
            nodeDesyncLoading.value[nodeId] = false
        }
    }

    function openWizard() {
        wizardOpen.value    = true
        wizardStep.value    = 1
        rrStatus.value      = null
        operationId.value   = null
        nodeOrder.value = enabledNodes.value.map((n) => n.id)
    }

    function closeWizard() {
        if (operationRunning.value) return
        wizardOpen.value  = false
        wizardStep.value  = 1
        rrStatus.value    = null
        operationId.value = null
    }

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
        clusterId, nodes, nodesLoading, nodesError,
        nodeActionLoading, nodeDesyncLoading,
        wizardOpen, wizardStep,
        nodeOrder, waitTimeoutSec,
        operationId, rrStatus, cancelling,
        // computed
        enabledNodes, hasDrift, currentRestartNode, operationRunning,
        // actions
        init, destroy, loadNodes,
        toggleMaintenance, toggleDesync,
        openWizard, closeWizard, resetWizard,
        startRollingRestart, cancelOperation,
    }
})
