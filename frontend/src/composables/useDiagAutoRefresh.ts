// Shared composable для auto-refresh логики всех диагностических панелей
import { ref, computed, watch } from 'vue'

const DEFAULT_INTERVAL_MS = 15_000

export function useDiagAutoRefresh(props: { active: boolean }) {
    const autoRefresh = ref(false)

    // Включаем интервал только если панель активна И autoRefresh включён
    const refetchInterval = computed(() =>
        props.active && autoRefresh.value ? DEFAULT_INTERVAL_MS : false
    )

    // Выключаем autoRefresh при деактивации вкладки
    watch(
        () => props.active,
        (active) => { if (!active) autoRefresh.value = false },
    )

    return { autoRefresh, refetchInterval }
}