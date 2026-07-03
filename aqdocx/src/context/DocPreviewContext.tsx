import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from 'react'
import { useLocation } from 'react-router-dom'
import { getDocEntity } from '../lib/docPreview/registry'
import type { DocEntityData } from '../lib/docPreview/types'

export type DocPreviewOpenReason = 'hover' | 'focus' | 'touch'

interface DocPreviewState {
  entity: DocEntityData | null
  anchorEl: HTMLElement | null
  reason: DocPreviewOpenReason | null
}

interface DocPreviewContextValue extends DocPreviewState {
  isTouch: boolean
  panelRef: RefObject<HTMLDivElement | null>
  show: (id: string, anchorEl: HTMLElement, reason: DocPreviewOpenReason) => void
  scheduleHide: (id: string, reason: DocPreviewOpenReason) => void
  cancelHide: () => void
  hideImmediately: (opts?: { refocusTrigger?: boolean }) => void
  isElementInsidePanel: (el: EventTarget | null) => boolean
}

const DocPreviewContext = createContext<DocPreviewContextValue | null>(null)

const HOVER_OPEN_DELAY_MS = 150
const HOVER_SWITCH_DELAY_MS = 45
const HOVER_CLOSE_DELAY_MS = 220

export function DocPreviewProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DocPreviewState>({ entity: null, anchorEl: null, reason: null })
  const stateRef = useRef(state)
  stateRef.current = state

  const panelRef = useRef<HTMLDivElement | null>(null)
  const lastAnchorRef = useRef<HTMLElement | null>(null)
  const openTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const isTouch = useMemo(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return false
    return window.matchMedia('(hover: none) and (pointer: coarse)').matches
  }, [])

  const clearTimers = useCallback(() => {
    if (openTimer.current) {
      clearTimeout(openTimer.current)
      openTimer.current = null
    }
    if (hideTimer.current) {
      clearTimeout(hideTimer.current)
      hideTimer.current = null
    }
  }, [])

  const isElementInsidePanel = useCallback((el: EventTarget | null) => {
    if (!(el instanceof Node)) return false
    return !!panelRef.current?.contains(el)
  }, [])

  const hideImmediately = useCallback(
    (opts?: { refocusTrigger?: boolean }) => {
      clearTimers()
      setState({ entity: null, anchorEl: null, reason: null })
      if (opts?.refocusTrigger) {
        lastAnchorRef.current?.focus?.()
      }
    },
    [clearTimers],
  )

  const show = useCallback(
    (id: string, anchorEl: HTMLElement, reason: DocPreviewOpenReason) => {
      const entity = getDocEntity(id)
      if (!entity) return

      if (hideTimer.current) {
        clearTimeout(hideTimer.current)
        hideTimer.current = null
      }

      lastAnchorRef.current = anchorEl

      if (reason === 'focus' || reason === 'touch') {
        if (openTimer.current) {
          clearTimeout(openTimer.current)
          openTimer.current = null
        }
        setState({ entity, anchorEl, reason })
        return
      }

      // Hover: already showing something → switch fast. Nothing showing → wait for
      // hover intent so casual cursor pass-throughs don't trigger a panel.
      const wasOpen = stateRef.current.entity !== null
      const delay = wasOpen ? HOVER_SWITCH_DELAY_MS : HOVER_OPEN_DELAY_MS

      if (openTimer.current) clearTimeout(openTimer.current)
      openTimer.current = setTimeout(() => {
        openTimer.current = null
        setState({ entity, anchorEl, reason })
      }, delay)
    },
    [],
  )

  const scheduleHide = useCallback(
    (id: string, reason: DocPreviewOpenReason) => {
      if (openTimer.current) {
        clearTimeout(openTimer.current)
        openTimer.current = null
      }

      if (reason === 'focus') {
        // Keyboard users get an immediate close on blur (handled by the caller checking
        // that focus didn't move into the panel itself).
        if (stateRef.current.entity?.id === id) {
          setState({ entity: null, anchorEl: null, reason: null })
        }
        return
      }

      if (reason === 'touch') return // touch dismissal is handled by outside-tap/Escape

      if (hideTimer.current) clearTimeout(hideTimer.current)
      hideTimer.current = setTimeout(() => {
        hideTimer.current = null
        if (stateRef.current.entity?.id === id) {
          setState({ entity: null, anchorEl: null, reason: null })
        }
      }, HOVER_CLOSE_DELAY_MS)
    },
    [],
  )

  const cancelHide = useCallback(() => {
    if (hideTimer.current) {
      clearTimeout(hideTimer.current)
      hideTimer.current = null
    }
  }, [])

  // Escape closes and returns focus to the trigger.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && stateRef.current.entity) {
        hideImmediately({ refocusTrigger: stateRef.current.reason === 'focus' })
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [hideImmediately])

  // Tap outside closes touch-opened panels.
  useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      const current = stateRef.current
      if (current.reason !== 'touch' || !current.entity) return
      const target = event.target
      if (isElementInsidePanel(target)) return
      if (current.anchorEl && target instanceof Node && current.anchorEl.contains(target)) return
      hideImmediately()
    }
    document.addEventListener('pointerdown', onPointerDown, true)
    return () => document.removeEventListener('pointerdown', onPointerDown, true)
  }, [hideImmediately, isElementInsidePanel])

  // Navigating to a new page always closes any open preview.
  const location = useLocation()
  useEffect(() => {
    hideImmediately()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname])

  useEffect(() => clearTimers, [clearTimers])

  const value = useMemo<DocPreviewContextValue>(
    () => ({
      ...state,
      isTouch,
      panelRef,
      show,
      scheduleHide,
      cancelHide,
      hideImmediately,
      isElementInsidePanel,
    }),
    [state, isTouch, show, scheduleHide, cancelHide, hideImmediately, isElementInsidePanel],
  )

  return <DocPreviewContext.Provider value={value}>{children}</DocPreviewContext.Provider>
}

export function useDocPreview(): DocPreviewContextValue {
  const ctx = useContext(DocPreviewContext)
  if (!ctx) {
    throw new Error('useDocPreview must be used within a DocPreviewProvider')
  }
  return ctx
}
