import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { recoveryApi, type RecoveryStatus } from '@/api/recovery'
import { useWsStore } from '@/stores/ws'
import type { NodeListItem } from '@/api/nodes'

export type WizardStep = 1 | 2 | 3 | 4

export type RecoveryOperationState =
    | 'pending'
    | 'running'
    | 'success'
    | 'failed'
    | 'cancel_requested'
    | 'cancelled'
    | null

export const useRecoveryStore = defineStore('recovery', () => {
    const step = ref<WizardStep>(1)
    const clusterId = ref<number | null>(null)

    const clusterStatus = ref<any | null>(null)
    const statusLoading = ref(false)
    const statusError = ref<string | null>(null)

    const selectedBootstrapNodeId = ref<number | null>(null)
    const bootstrapping = ref(false)
    const bootstrapError = ref<string | null>(null)

    const operationId = ref<number | null>(null)
    const progressPct = ref(0)
    const progressMessage = ref<string | null>(null)
    const operationState = ref<RecoveryOperationState>(null)
    const operationError = ref<string | null>(null)
    const cancelling = ref(false)

    // ── Computed ──────────────────────────────────────────────────────────
    const offlineNodes = computed<NodeListItem[]>(() =>
        clusterStatus.value?.nodes?.filter(
            (n: NodeListItem) =>
                n.wsrep_local_state_comment === null ||
                !n.wsrep_connected
        ) ?? []
    )

    const recommendedBootstrapNodeId = computed<number | null>(() =>
        clusterStatus.value?.recommended_bootstrap_node_id ?? null
    )

    const nodesNeedingRejoin = computed<NodeListItem[]>(() =>
        clusterStatus.value?.nodes?.filter(
            (n: NodeListItem) =>
                n.node_id !== selectedBootstrapNodeId.value &&
                (!n.wsrep_connected || n.wsrep_local_state_comment !== 'Synced')
        ) ?? []
    )

    // ── Actions ───────────────────────────────────────────────────────────────
    async function init(cId: number) {
        // Если кластер тот же — не сбрасываем стейт (сохраняем результаты скана)
        if (clusterId.value === cId) return

        // Смена кластера — полный сброс
        wsUnsub?.()
        wsUnsub = null
        clusterId.value = cId
        reset()
        subscribeWs()

        // Polling-fallback: восстанавливаем прогресс если зашли во время активной операции
        try {
            const status = await recoveryApi.getStatus(cId)
            const op = status.active_operation
            if (op && ['pending', 'running', 'cancel_requested'].includes(op.state)) {
                operationId.value = op.operation_id
                operationState.value = op.state as RecoveryOperationState
                progressPct.value = op.progress_pct ?? 0
                step.value = 3
            }
        } catch {
            // нет активной операции — норма
        }
    }

    function reset() {
        step.value = 1
        clusterStatus.value = null
        statusLoading.value = false
        statusError.value = null
        selectedBootstrapNodeId.value = null
        bootstrapping.value = false
        bootstrapError.value = null
        operationId.value = null
        progressPct.value = 0
        progressMessage.value = null
        operationState.value = null
        operationError.value = null
        cancelling.value = false
    }

    async function loadStatus() {
        if (!clusterId.value) return
        statusLoading.value = true
        statusError.value = null
        try {
            const { data } = await import('@/api/client').then(m =>
                m.api.get(`/api/clusters/${clusterId.value}/status`)
            )
            clusterStatus.value = data
            if (data.recommended_bootstrap_node_id) {
                selectedBootstrapNodeId.value = data.recommended_bootstrap_node_id
            }
        } catch (err: any) {
            statusError.value = err?.response?.data?.detail ?? err.message
        } finally {
            statusLoading.value = false
        }
    }

    async function startBootstrap() {
        if (!clusterId.value || !selectedBootstrapNodeId.value) return
        bootstrapping.value = true
        bootstrapError.value = null
        try {
            const res = await recoveryApi.bootstrap(
                clusterId.value,
                selectedBootstrapNodeId.value,
            )
            operationId.value = res.operation_id ?? null
            operationState.value = 'running'
            progressPct.value = 0
            step.value = 3
        } catch (err: any) {
            bootstrapError.value = err?.response?.data?.detail ?? err.message
        } finally {
            bootstrapping.value = false
        }
    }

    async function startRejoin(nodeId: number) {
        if (!clusterId.value) return
        try {
            const res = await recoveryApi.rejoin(clusterId.value, nodeId)
            operationId.value = res.operation_id ?? null
            operationState.value = 'running'
            step.value = 3
        } catch (err: any) {
            operationError.value = err?.response?.data?.detail ?? err.message
        }
    }

    async function cancelOperation() {
        if (!clusterId.value) return
        cancelling.value = true
        try {
            await recoveryApi.cancel(clusterId.value)
        } finally {
            cancelling.value = false
        }
    }

    // ── WS subscription ───────────────────────────────────────────────────
    let wsUnsub: (() => void) | null = null

    function subscribeWs() {
        const wsStore = useWsStore()
        wsUnsub = wsStore.on((event) => {
            if (
                event.event === 'operation_started' &&
                (event.payload?.type as string)?.startsWith('recovery')
            ) {
                operationState.value = 'running'
                progressPct.value = 0
                operationId.value = (event.payload?.id as number) ?? operationId.value
            }

            if (event.event === 'operation_progress') {
                progressPct.value = (event.payload?.progress_pct as number) ?? progressPct.value
                progressMessage.value = (event.payload?.message as string) ?? null
            }

            if (event.event === 'operation_finished') {
                const status = event.payload?.status as string
                progressMessage.value = (event.payload?.message as string) ?? 'Completed'

                if (status === 'cancelled' || status === 'cancel_requested') {
                    operationState.value = 'cancelled'
                } else if (status === 'failed') {
                    progressPct.value = 100
                    operationState.value = 'failed'
                    operationError.value = (event.payload?.error_message as string) ?? 'Unknown error'
                } else {
                    progressPct.value = 100
                    operationState.value = 'success'
                }
                step.value = 4
            }
        })
    }

    function goNext() {
        if (step.value < 4) step.value = (step.value + 1) as WizardStep
    }

    function goBack() {
        if (step.value > 1) step.value = (step.value - 1) as WizardStep
    }

    function goTo(n: WizardStep) {
        step.value = n
    }

    function destroy() {
        wsUnsub?.()
        wsUnsub = null
        reset()
        clusterId.value = null
    }

    return {
        step, clusterId,
        clusterStatus, statusLoading, statusError,
        selectedBootstrapNodeId, bootstrapping, bootstrapError,
        operationId, progressPct, progressMessage, operationState, operationError,
        cancelling,
        offlineNodes, recommendedBootstrapNodeId, nodesNeedingRejoin,
        init, reset, loadStatus, startBootstrap, startRejoin, cancelOperation, destroy,
        goNext, goBack, goTo,
    }
})
