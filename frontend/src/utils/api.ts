// src/utils/api.ts
export function extractApiError(err: unknown): string {
    if (err && typeof err === 'object') {
        const e = err as any
        return e?.response?.data?.detail ?? e?.message ?? 'Unknown error'
    }
    return String(err)
}