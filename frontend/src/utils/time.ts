export function formatRelative(isoStr: string | null | undefined): string {
    if (!isoStr) return '—'
    const ts = new Date(isoStr).getTime()
    if (isNaN(ts)) return '—'
    const diff = Math.floor((Date.now() - ts) / 1000)
    if (diff < 5)     return 'just now'
    if (diff < 60)    return `${diff} sec before`
    if (diff < 3600)  return `${Math.floor(diff / 60)} min before`
    if (diff < 86400) return `${Math.floor(diff / 3600)} h before`
    return `${Math.floor(diff / 86400)} day(s) before`
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

/**
 * formatDateTime — форматирует ISO-строку в читаемую дату+время.
 * Используется в SlowQueryPanel и других компонентах.
 * Пример: '2026-04-10T10:22:00Z' → '10.04.2026 10:22:00'
 */
export function formatDateTime(isoStr: string | null | undefined): string {
    if (!isoStr) return '—'
    const d = new Date(isoStr)
    if (isNaN(d.getTime())) return '—'
    const pad = (n: number) => String(n).padStart(2, '0')
    return [
        `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`,
        `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`,
    ].join(' ')
}
