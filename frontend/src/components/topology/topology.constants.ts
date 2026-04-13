// src/components/topology/topology.constants.ts
// All sizes in pixels.
// Used by TopologyCanvas, DCZone, TopoNodeCard, TopoArbitratorCard.
//
// NOTE: TopologyCanvas / DCZone / TopoNodeCard / TopoArbitratorCard are
// @deprecated — TopologyPage renders its own inline SVG (Variant A).
// These components are kept for reference and will be removed in a
// future refactor sprint.

// ── Node card ───────────────────────────────────────────────────────────────
export const CARD_W = 160
export const CARD_H = 64

// ── Arbitrator card ─────────────────────────────────────────────────────────
export const ARB_W = 96
export const ARB_H = 56

// ── Layout gaps ─────────────────────────────────────────────────────────────
export const NODE_GAP = 16
export const DC_PAD   = 20
export const DC_GAP   = 32

// ── Canvas margins ──────────────────────────────────────────────────────────
export const CANVAS_MARGIN = 24
export const NODE_START_Y  = 36   // header height inside DCZone

// ── Connectors ──────────────────────────────────────────────────────────────
export const CONN_STROKE      = 2
export const CONN_DASH_ACTIVE = 0
export const CONN_DASH_SYNC   = 6
