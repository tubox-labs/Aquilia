/**
 * Small, dependency-free floating-panel positioning engine.
 *
 * Handles: viewport-aware flip (top/bottom) + shift (left/right) clamping, nested
 * scroll-container tracking, and a stable "anchor" rect the panel is placed relative to.
 * Deliberately hand-rolled instead of pulling in @floating-ui — the placement logic
 * this component needs (flip + shift + viewport clamp for a single floating panel) is
 * small enough that a dependency isn't worth it.
 */

export type Placement = 'top' | 'bottom'
export type Align = 'start' | 'center'

export interface Rect {
  top: number
  left: number
  right: number
  bottom: number
  width: number
  height: number
}

export interface ComputedPosition {
  top: number
  left: number
  placement: Placement
  /** Horizontal offset (0-1) of the anchor's center within the panel, for the caret/pointer. */
  anchorOffsetRatio: number
}

const VIEWPORT_PADDING = 12
const ANCHOR_GAP = 10

export function rectFromDOMRect(rect: DOMRect): Rect {
  return {
    top: rect.top,
    left: rect.left,
    right: rect.right,
    bottom: rect.bottom,
    width: rect.width,
    height: rect.height,
  }
}

export function computePosition(
  anchor: Rect,
  panelSize: { width: number; height: number },
  viewport: { width: number; height: number },
  preferred: Placement = 'bottom',
): ComputedPosition {
  const spaceBelow = viewport.height - anchor.bottom - VIEWPORT_PADDING
  const spaceAbove = anchor.top - VIEWPORT_PADDING
  const fitsBelow = spaceBelow >= panelSize.height + ANCHOR_GAP
  const fitsAbove = spaceAbove >= panelSize.height + ANCHOR_GAP

  let placement: Placement = preferred
  if (preferred === 'bottom' && !fitsBelow && fitsAbove) placement = 'top'
  else if (preferred === 'top' && !fitsAbove && fitsBelow) placement = 'bottom'
  else if (!fitsBelow && !fitsAbove) {
    // Neither fits fully — pick whichever side has more room.
    placement = spaceAbove > spaceBelow ? 'top' : 'bottom'
  }

  const top =
    placement === 'bottom'
      ? Math.min(anchor.bottom + ANCHOR_GAP, viewport.height - VIEWPORT_PADDING - panelSize.height)
      : anchor.top - ANCHOR_GAP - panelSize.height

  const clampedTop = Math.max(VIEWPORT_PADDING, top)

  // Prefer aligning the panel's left edge with the anchor's left edge, then shift inward
  // to stay within the viewport.
  const idealLeft = anchor.left
  const maxLeft = viewport.width - VIEWPORT_PADDING - panelSize.width
  const minLeft = VIEWPORT_PADDING
  const left = Math.min(Math.max(idealLeft, minLeft), Math.max(minLeft, maxLeft))

  const anchorCenter = anchor.left + anchor.width / 2
  const anchorOffsetRatio = panelSize.width > 0 ? clamp((anchorCenter - left) / panelSize.width, 0.06, 0.94) : 0.5

  return { top: clampedTop, left, placement, anchorOffsetRatio }
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

/** Walk up the DOM to find every scrollable ancestor (for nested scroll-container tracking). */
export function getScrollParents(node: Element | null): Element[] {
  const parents: Element[] = []
  let current = node?.parentElement ?? null

  while (current) {
    const style = window.getComputedStyle(current)
    const overflow = `${style.overflow}${style.overflowY}${style.overflowX}`
    if (/(auto|scroll|overlay)/.test(overflow)) {
      parents.push(current)
    }
    current = current.parentElement
  }

  return parents
}
