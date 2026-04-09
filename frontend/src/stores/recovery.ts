import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { recoveryApi, type RecoveryScanResult, type NodeGrastate } from '@/api/recovery'
import { useWsStore } from '@/stores/ws'

export type WizardStep = 1 | 2 | 3 | 4

export const useRecoveryStore = defineStore('recovery', () => {
    // ── Wizard state ────────────────────────────────────────────────────────
    const step = ref<WizardStep>(1)
    const clusterId = ref<number | null>(null)

    // Step 1 — scan
    const scanResult = ref<RecoveryScanResult | null>(null)
    const scanning = ref(false)
    const scanError = ref<string | null>(null)

    // Step 2 — bootstrap selection
    const selectedBootstrapNodeId = ref<number | null>(null)
    const bootstrapForce = ref(false)
    const bootstrapping = ref(false)
    const bootstrapError = ref<string | null>(null)

    // Step 3 — rejoin
    const operationId = ref<string | null>(null)
    const progressPct = ref(0)
    const progressMessage = ref<string | null>(null)
    const operationState = ref<'pending' | 'running' | 'finished' | 'failed' | 'cancelled' | null>(null)
    const operationError = ref<string | null>(null)
    const cancelling = ref(false)

    // ── Computed ─────────────────────────────────────────────────────────────
    const recommendedNode = computed<NodeGrastate | null>(() => {
        if (!scanResult.value) return null
        const id = scanResult.value.recommended_bootstrap_node_id
        return scanResult.value.nodes.find((n) => n.node_id === id) ?? null
    })

    const reachableNodes = computed<NodeGrastate[]>(() =>
        scanResult.value?.nodes.filter((n) => n.reachable) ?? []
    )

    const nodesNeedingRejoin = computed<NodeGrastate[]>(() =>
        scanResult.value?.nodes.filter(
            (n) => n.node_id !== selectedBootstrapNodeId.value
        ) ?? []
    )

    // ── Actions ───────────────────────────────────────────────────────────────
    async function init(cId: number) {
        clusterId.value = cId
        reset()
        subscribeWs()
        // Polling-fallback: восстанавливаем прогресс если зашли во время активной операции
        try {
            const status = await recoveryApi.getStatus(cId)
            if (status.state === 'running' || status.state === 'pending') {
                operationId.value = status.operation_id
                operationState.value = status.state
                progressPct.value = status.progress_pct
                progressMessage.value = status.message
                step.value = 3
            }
        } catch {
            // 404 = нет активной операции, норма
        }
    }

    function reset() {
        step.value = 1
        scanResult.value = null
        scanning.value = false
        scanError.value = null
        selectedBootstrapNodeId.value = null
        bootstrapForce.value = false
        bootstrapping.value = false
        bootstrapError.value = null
        operationId.value = null
        progressPct.value = 0
        progressMessage.value = null
        operationState.value = null
        operationError.value = null
        cancelling.value = false
    }

    async function scan() {
        if (!clusterId.value) return
        scanning.value = true
        scanError.value = null
        try {
            scanResult.value = await recoveryApi.scan(clusterId.value)
            // Рекомендуем backend-выбор как дефолт
            selectedBootstrapNodeId.value = scanResult.value.recommended_bootstrap_node_id
        } catch (err: any) {
            scanError.value = err?.response?.data?.detail ?? err.message
        } finally {
            scanning.value = false
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
                bootstrapForce.value,
            )
            operationId.value = res.operation_id
            operationState.value = 'running'
            progressPct.value = 0
            step.value = 3
        } catch (err: any) {
            bootstrapError.value = err?.response?.data?.detail ?? err.message
        } finally {
            bootstrapping.value = false
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

    // ── WS subscription ───────────────────────────────────────────────────────
    let wsUnsub: (() => void) | null = null

    function subscribeWs() {
        const wsStore = useWsStore()
        wsUnsub?.()
        wsUnsub = wsStore.on((event) => {
            if (event.type === 'operation_started' && event.payload?.operation_type?.startsWith('recovery')) {
                operationState.value = 'running'
                progressPct.value = 0
            }
            if (event.type === 'operation_progress') {
                progressPct.value = event.payload?.progress_pct ?? progressPct.value
                progressMessage.value = event.payload?.message ?? null
            }
            if (event.type === 'operation_finished') {
                progressPct.value = 100
                progressMessage.value = event.payload?.message ?? 'Completed'
                if (event.payload?.success === false) {
                    operationState.value = 'failed'
                    operationError.value = event.payload?.error ?? 'Unknown error'
                } else {
                    operationState.value = 'finished'
                }
                step.value = 4
            }
            if (event.type === 'operation_cancelled') {
                operationState.value = 'cancelled'
                step.value = 4
            }
        })
    }

    function destroy() {
        wsUnsub?.()
        wsUnsub = null
        reset()
    }

    return {
        // state
        step, clusterId,
        scanResult, scanning, scanError,
        selectedBootstrapNodeId, bootstrapForce, bootstrapping, bootstrapError,
        operationId, progressPct, progressMessage, operationState, operationError,
        cancelling,
        // computed
        recommendedNode, reachableNodes, nodesNeedingRejoin,
        // actions
        init, reset, scan, startBootstrap, cancelOperation, destroy,
    }
})