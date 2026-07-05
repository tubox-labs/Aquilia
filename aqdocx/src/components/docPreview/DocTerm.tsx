import { useCallback, useEffect, useState, useSyncExternalStore, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react'
import { useTheme } from '../../context/ThemeContext'
import { useDocPreview } from '../../context/DocPreviewContext'
import { hasDocEntity, subscribeDocRegistry } from '../../lib/docPreview/registry'

interface DocTermProps {
  /** Id of a `DocEntityData` registered via `registerDocEntities()`. */
  id: string
  children: ReactNode
  className?: string
}

/**
 * Wraps any documented entity mention — `on_startup(ctx)`, `Router`, `@inject`,
 * `UserModel`, `aquilia run`, `Request` — and gives it hover/focus/tap preview
 * behavior driven entirely by data registered against `id`. If no entity is
 * registered for `id`, renders `children` unchanged (no interactivity, no crash) —
 * safe to sprinkle liberally through docs even before every entity has data.
 */
export function DocTerm({ id, children, className = '' }: DocTermProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const { entity, anchorEl, isTouch, show, scheduleHide, cancelHide, isElementInsidePanel } = useDocPreview()

  // A state-backed (rather than ref-backed) node reference — safe to read during render,
  // unlike `ref.current`, and lets `isActive` below re-evaluate whenever it changes.
  const [node, setNode] = useState<HTMLButtonElement | null>(null)
  const setRef = useCallback((el: HTMLButtonElement | null) => setNode(el), [])

  // Subscribes to registry changes so entities registered after this component's first
  // render (e.g. by a lazily-loaded route chunk) still light up without a page reload.
  const registered = useSyncExternalStore(subscribeDocRegistry, () => hasDocEntity(id))
  const isActive = registered && entity?.id === id && anchorEl === node

  useEffect(() => {
    if (!registered && import.meta.env.DEV) {
      console.warn(`[DocTerm] No doc entity registered for id "${id}" — rendering plain text.`)
    }
  }, [registered, id])

  if (!registered) {
    return <>{children}</>
  }

  const onPointerEnter = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (event.pointerType === 'touch') return
    if (node) show(id, node, 'hover')
  }

  const onPointerLeave = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (event.pointerType === 'touch') return
    scheduleHide(id, 'hover')
  }

  const onFocus = () => {
    if (node) show(id, node, 'focus')
  }

  const onBlur = (event: React.FocusEvent<HTMLButtonElement>) => {
    if (isElementInsidePanel(event.relatedTarget)) return
    scheduleHide(id, 'focus')
  }

  const onClick = () => {
    if (!isTouch) return
    if (isActive) {
      scheduleHide(id, 'hover')
      return
    }
    if (node) show(id, node, 'touch')
  }

  return (
    <button
      ref={setRef}
      type="button"
      onPointerEnter={onPointerEnter}
      onPointerLeave={onPointerLeave}
      onFocus={onFocus}
      onBlur={onBlur}
      onClick={onClick}
      onPointerDown={cancelHide}
      aria-haspopup="dialog"
      aria-expanded={isActive}
      aria-controls={isActive ? 'aq-doc-preview' : undefined}
      className={`doc-term font-mono transition-colors duration-150 cursor-help align-baseline border-b border-dashed ${isActive
        ? isDark
          ? 'border-aquilia-300 text-aquilia-300'
          : 'border-aquilia-600 text-aquilia-600'
        : isDark
          ? 'border-aquilia-400/30 text-aquilia-400 hover:text-aquilia-300 hover:border-aquilia-300/60'
          : 'border-aquilia-600/30 text-aquilia-600 hover:text-aquilia-500 hover:border-aquilia-500/60'
        } ${className}`}
      style={{ WebkitTapHighlightColor: 'transparent' }}
    >
      {children}
    </button>
  )
}
