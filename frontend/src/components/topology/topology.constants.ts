// src/components/topology/topology.constants.ts
// Все размеры в пикселях. Используются в TopologyCanvas, DCZone,
// TopologyNodeBadge, TopologyArbitratorBadge для консистентного layout.

// ── Node card ───────────────────────────────────────────────────────────────
// ТЗ п.12.5: имя + статус-бейдж + RW/RO → минимум 2 строки контента
export const CARD_W = 160  // px
export const CARD_H = 64   // MAJOR fix: 48→64, влезает имя + badge + padding

// ── Arbitrator card ─────────────────────────────────────────────────────────
// ТЗ п.12.4: имя + state (online/degraded/offline)
export const ARB_W = 96    // MINOR fix: 80→96, имена типа "arb-node-1" не обрезаются
export const ARB_H = 56

// ── Layout gaps ─────────────────────────────────────────────────────────────
// MAJOR fix: единые константы чтобы TopologyCanvas и DCZone не хардкодили числа
export const NODE_GAP = 16  // px между карточками нод по вертикали
export const DC_PAD   = 20  // px внутренний padding DCZone
export const DC_GAP   = 32  // px между DC-зонами по горизонтали

// ── Connectors (SVG/Canvas lines) ────────────────────────────────────────────
// ТЗ п.12.4: линии между нодами — синхронизация/репликация
export const CONN_STROKE      = 2    // px ширина линии
export const CONN_DASH_ACTIVE = 0    // solid — активное соединение
export const CONN_DASH_SYNC   = 6    // dash — DONOR/JOINER sync в процессе