export function formatRelative(isoStr: string | null | undefined): string {
    if (!isoStr) return '—'
    const ts = new Date(isoStr).getTime()
    if (isNaN(ts)) return '—'               // MAJOR fix: guard NaN
    const diff = Math.floor((Date.now() - ts) / 1000)
    if (diff < 5)     return 'только что'   // MINOR fix: ru locale
    if (diff < 60)    return `${diff} с назад`
    if (diff < 3600)  return `${Math.floor(diff / 60)} мин назад`
    if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`
    return `${Math.floor(diff / 86400)} д назад`
}

export function formatUptime(seconds: number | null | undefined): string {
    if (seconds == null || isNaN(seconds)) return '—'
    const d = Math.floor(seconds / 86400)
    const h = Math.floor((seconds % 86400) / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    if (d > 0) return `${d}д ${h}ч`
    if (h > 0) return `${h}ч ${m}м`
    return `${m}м`
}