// composables/useDiagAutoRefresh.ts
import { ref, computed, watch, type Ref } from 'vue'

export function useDiagAutoRefresh(
    // MAJOR fix: принимаем Ref<boolean> вместо plain object
    active: Ref<boolean>,
    // MAJOR fix: интервал из system_settings, не хардкод
    intervalMs: Ref<number>,
) {
    const autoRefresh = ref(false)

    const refetchInterval = computed(() =>
        active.value && autoRefresh.value ? intervalMs.value : false,
    )

    // MAJOR fix: reactive watch через Ref<boolean>
    watch(active, (isActive) => {
        if (!isActive) autoRefresh.value = false
    })

    return { autoRefresh, refetchInterval }
}