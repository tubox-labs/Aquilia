import { useCallback, useLayoutEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  Copy,
  FileCode2,
  Info,
  Lightbulb,
  Sparkles,
  X,
} from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import { useDocPreview } from '../../context/DocPreviewContext'
import { getDocEntity } from '../../lib/docPreview/registry'
import { computePosition, getScrollParents, rectFromDOMRect, type ComputedPosition } from '../../lib/docPreview/position'
import { getEntityMeta } from './entityMeta'
import { SignatureLine } from './SignatureLine'
import { CodeBlock } from '../CodeBlock'
import type { DocNoteKind } from '../../lib/docPreview/types'

const PANEL_ID = 'aq-doc-preview'
const PANEL_DESC_ID = 'aq-doc-preview-desc'
const PANEL_WIDTH = 360

const NOTE_STYLES: Record<DocNoteKind, { icon: typeof Info; dark: string; light: string }> = {
  note: { icon: Info, dark: 'text-sky-300 bg-sky-500/10 border-sky-500/20', light: 'text-sky-700 bg-sky-50 border-sky-200' },
  warning: {
    icon: AlertTriangle,
    dark: 'text-amber-300 bg-amber-500/10 border-amber-500/20',
    light: 'text-amber-700 bg-amber-50 border-amber-200',
  },
  tip: {
    icon: Lightbulb,
    dark: 'text-aquilia-300 bg-aquilia-500/10 border-aquilia-500/20',
    light: 'text-aquilia-700 bg-aquilia-50 border-aquilia-200',
  },
}

const STATUS_LABEL: Record<string, string> = {
  stable: 'Stable',
  beta: 'Beta',
  experimental: 'Experimental',
  deprecated: 'Deprecated',
}

export function DocPreviewPanel() {
  const { entity, anchorEl, reason, panelRef, cancelHide, scheduleHide, hideImmediately, isTouch } = useDocPreview()
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const reducedMotion = useReducedMotion()

  const [position, setPosition] = useState<ComputedPosition | null>(null)

  useLayoutEffect(() => {
    if (!entity || !anchorEl) return

    let frame = 0
    const recompute = () => {
      const panelEl = panelRef.current
      if (!panelEl) return
      const anchorRect = rectFromDOMRect(anchorEl.getBoundingClientRect())
      const panelRect = panelEl.getBoundingClientRect()
      setPosition(
        computePosition(
          anchorRect,
          { width: panelRect.width, height: panelRect.height },
          { width: window.innerWidth, height: window.innerHeight },
        ),
      )
    }

    recompute()

    const onTrack = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(recompute)
    }

    const scrollParents = getScrollParents(anchorEl)
    window.addEventListener('scroll', onTrack, { passive: true })
    window.addEventListener('resize', onTrack)
    scrollParents.forEach((parent) => parent.addEventListener('scroll', onTrack, { passive: true }))

    const resizeObserver = new ResizeObserver(recompute)
    resizeObserver.observe(panelRef.current!)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('scroll', onTrack)
      window.removeEventListener('resize', onTrack)
      scrollParents.forEach((parent) => parent.removeEventListener('scroll', onTrack))
      resizeObserver.disconnect()
    }
  }, [entity, anchorEl, panelRef])

  const fallbackPosition = useMemo<ComputedPosition | null>(() => {
    if (!anchorEl) return null
    const rect = anchorEl.getBoundingClientRect()
    return { top: rect.bottom + 10, left: rect.left, placement: 'bottom', anchorOffsetRatio: 0.15 }
  }, [anchorEl])

  const resolvedPosition = position ?? fallbackPosition

  const handleCopySignature = useCallback(() => {
    if (entity?.signature) navigator.clipboard.writeText(entity.signature)
  }, [entity])

  if (typeof document === 'undefined') return null

  const meta = entity ? getEntityMeta(entity.type) : null
  const palette = meta ? (isDark ? meta.dark : meta.light) : null

  return createPortal(
    <AnimatePresence>
      {entity && resolvedPosition && (
        <motion.div
          key="doc-preview-panel"
          ref={panelRef}
          id={PANEL_ID}
          role="dialog"
          aria-label={entity.title}
          aria-describedby={PANEL_DESC_ID}
          tabIndex={-1}
          onPointerEnter={cancelHide}
          onPointerLeave={() => scheduleHide(entity.id, reason ?? 'hover')}
          className="fixed top-0 left-0 z-[130] print:hidden"
          style={{ width: `min(${PANEL_WIDTH}px, calc(100vw - 24px))`, willChange: 'transform, opacity' }}
          initial={reducedMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95, x: resolvedPosition.left, y: resolvedPosition.top + (resolvedPosition.placement === 'bottom' ? -6 : 6) }}
          animate={reducedMotion ? { opacity: 1 } : { opacity: 1, scale: 1, x: resolvedPosition.left, y: resolvedPosition.top }}
          exit={reducedMotion ? { opacity: 0 } : { opacity: 0, scale: 0.97, y: resolvedPosition.top + (resolvedPosition.placement === 'bottom' ? -4 : 4) }}
          transition={
            reducedMotion
              ? { duration: 0.1 }
              : { type: 'spring', stiffness: 460, damping: 36, mass: 0.7, opacity: { duration: 0.15 } }
          }
        >
          <div
            className={`relative rounded-2xl border overflow-hidden ${isDark ? 'border-white/10 bg-zinc-950' : 'border-gray-200/80 bg-white'}`}
            style={{
              boxShadow: isDark
                ? '0 24px 64px -12px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.03)'
                : '0 24px 64px -16px rgba(15, 23, 42, 0.22), 0 0 0 1px rgba(15, 23, 42, 0.02)',
            }}
          >

            <button
              type="button"
              onClick={() => hideImmediately()}
              aria-label="Close preview"
              className={`absolute top-3 right-3 z-10 p-1.5 rounded-full transition-opacity ${isTouch
                ? isDark
                  ? 'text-gray-300 bg-white/10'
                  : 'text-gray-500 bg-gray-100'
                : `opacity-40 hover:opacity-100 ${isDark ? 'text-gray-400 hover:bg-white/10' : 'text-gray-400 hover:bg-gray-100'}`
                }`}
            >
              <X className="w-3.5 h-3.5" />
            </button>

            <div className="relative px-4 pt-4 pb-3.5 max-h-[70vh] overflow-y-auto">
              {/* Header */}
              <div className="flex items-start gap-3 pr-6">
                {meta && (
                  <div className={`shrink-0 mt-0.5 w-8 h-8 rounded-lg border flex items-center justify-center ${palette?.bg} ${palette?.border}`}>
                    <meta.icon className={`w-4 h-4 ${palette?.text}`} />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <h3 className={`font-mono font-semibold text-[15px] leading-tight truncate ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      {entity.title}
                    </h3>
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap mt-1.5">
                    <span className={`text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded border ${palette?.bg} ${palette?.border} ${palette?.text}`}>
                      {meta?.label}
                    </span>
                    {entity.status && entity.status !== 'stable' && (
                      <span
                        className={`text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded border ${entity.status === 'deprecated'
                          ? isDark
                            ? 'bg-rose-500/10 border-rose-500/20 text-rose-300'
                            : 'bg-rose-50 border-rose-200 text-rose-700'
                          : isDark
                            ? 'bg-violet-500/10 border-violet-500/20 text-violet-300'
                            : 'bg-violet-50 border-violet-200 text-violet-700'
                          }`}
                      >
                        {STATUS_LABEL[entity.status]}
                      </span>
                    )}
                    {entity.version && (
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${isDark ? 'border-white/10 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                        {entity.version}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Deprecation notice */}
              {entity.deprecated && (
                <div className={`mt-3 rounded-lg border px-2.5 py-2 flex gap-2 ${isDark ? 'bg-rose-500/10 border-rose-500/20' : 'bg-rose-50 border-rose-200'}`}>
                  <AlertTriangle className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${isDark ? 'text-rose-300' : 'text-rose-600'}`} />
                  <p className={`text-xs leading-relaxed ${isDark ? 'text-rose-200' : 'text-rose-700'}`}>
                    {entity.deprecated.since && <strong>Deprecated since {entity.deprecated.since}. </strong>}
                    {entity.deprecated.message}
                    {entity.deprecated.replacement && (
                      <>
                        {' '}
                        Use <code className="font-mono">{entity.deprecated.replacement}</code> instead.
                      </>
                    )}
                  </p>
                </div>
              )}

              {/* Description */}
              <p id={PANEL_DESC_ID} className={`mt-3 text-[13px] leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                {entity.description}
              </p>

              {/* Signature */}
              {entity.signature && (
                <div className="mt-3">
                  <SignatureLine code={entity.signature} language={entity.language} isDark={isDark} />
                </div>
              )}

              {/* Parameters */}
              {entity.parameters && entity.parameters.length > 0 && (
                <div className="mt-3.5">
                  <SectionLabel isDark={isDark}>Parameters</SectionLabel>
                  <div className={`mt-1.5 rounded-lg border divide-y overflow-hidden ${isDark ? 'border-white/10 divide-white/5' : 'border-gray-200 divide-gray-100'}`}>
                    {entity.parameters.map((param) => (
                      <div key={param.name} className="px-2.5 py-1.5">
                        <div className="flex items-baseline gap-1.5 flex-wrap">
                          <code className={`font-mono text-xs font-medium ${isDark ? 'text-aquilia-300' : 'text-aquilia-700'}`}>{param.name}</code>
                          {param.type && <span className={`font-mono text-[11px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{param.type}</span>}
                          {param.optional && (
                            <span className={`text-[10px] px-1 rounded ${isDark ? 'bg-white/5 text-gray-500' : 'bg-gray-100 text-gray-500'}`}>optional</span>
                          )}
                          {param.default !== undefined && (
                            <span className={`text-[10px] font-mono ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>= {param.default}</span>
                          )}
                        </div>
                        {param.description && (
                          <p className={`text-[11.5px] mt-0.5 leading-snug ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{param.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Returns */}
              {entity.returns && (entity.returns.type || entity.returns.description) && (
                <div className="mt-3.5">
                  <SectionLabel isDark={isDark}>Returns</SectionLabel>
                  <div className="mt-1.5 flex items-baseline gap-1.5 flex-wrap">
                    {entity.returns.type && (
                      <code className={`font-mono text-xs font-medium ${isDark ? 'text-blue-300' : 'text-blue-700'}`}>{entity.returns.type}</code>
                    )}
                    {entity.returns.description && (
                      <span className={`text-[11.5px] ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{entity.returns.description}</span>
                    )}
                  </div>
                </div>
              )}

              {/* Example */}
              {entity.example && (
                <div className="mt-3.5">
                  <SectionLabel isDark={isDark}>{entity.example.title || 'Example'}</SectionLabel>
                  <div className="mt-1.5">
                    <CodeBlock code={entity.example.code} language={entity.example.language || entity.language || 'python'} showLineNumbers={false} compact />
                  </div>
                </div>
              )}

              {/* Notes */}
              {entity.notes && entity.notes.length > 0 && (
                <div className="mt-3.5 space-y-1.5">
                  {entity.notes.map((note, i) => {
                    const kind = note.kind || 'note'
                    const style = NOTE_STYLES[kind]
                    const NoteIcon = style.icon
                    return (
                      <div key={i} className={`rounded-lg border px-2.5 py-1.5 flex gap-2 ${isDark ? style.dark : style.light}`}>
                        <NoteIcon className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <p className="text-[11.5px] leading-relaxed">{note.text}</p>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Related entities */}
              {entity.related && entity.related.length > 0 && (
                <div className="mt-3.5">
                  <SectionLabel isDark={isDark}>Related</SectionLabel>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {entity.related.map((rel, i) => {
                      const target = rel.id ? getDocEntity(rel.id) : undefined
                      const RelIcon = target ? getEntityMeta(target.type).icon : Sparkles
                      const content = (
                        <>
                          <RelIcon className="w-3 h-3" />
                          {rel.label}
                        </>
                      )
                      const interactiveClassName = `inline-flex items-center gap-1 text-[11px] font-mono px-2 py-1 rounded-md border transition-colors ${isDark
                        ? 'border-white/10 text-gray-300 hover:border-aquilia-500/40 hover:text-aquilia-300 hover:bg-aquilia-500/5'
                        : 'border-gray-200 text-gray-600 hover:border-aquilia-300 hover:text-aquilia-700 hover:bg-aquilia-50'
                        }`
                      const staticClassName = `inline-flex items-center gap-1 text-[11px] font-mono px-2 py-1 rounded-md border ${isDark ? 'border-white/10 text-gray-400' : 'border-gray-200 text-gray-500'
                        }`

                      const linkHref = target?.docsHref ?? rel.href
                      if (linkHref) {
                        return (
                          <Link key={i} to={linkHref} className={interactiveClassName} onClick={() => hideImmediately()}>
                            {content}
                          </Link>
                        )
                      }
                      return (
                        <span key={i} className={staticClassName}>
                          {content}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Footer actions */}
              {(entity.signature || entity.docsHref || entity.source) && (
                <div className={`mt-4 pt-3 border-t flex items-center justify-between gap-3 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                  <div className="flex items-center gap-2 min-w-0">
                    {entity.source && (
                      <span className={`inline-flex items-center gap-1 text-[11px] font-mono truncate ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <FileCode2 className="w-3 h-3 shrink-0" />
                        <span className="truncate">
                          {entity.source.file}
                          {entity.source.line ? `:${entity.source.line}` : ''}
                        </span>
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {entity.signature && <CopySignatureButton onCopy={handleCopySignature} isDark={isDark} />}
                    {entity.docsHref && (
                      <Link
                        to={entity.docsHref}
                        onClick={() => hideImmediately()}
                        className={`inline-flex items-center gap-1 text-xs font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-700'
                          }`}
                      >
                        Full docs
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}

function SectionLabel({ children, isDark }: { children: React.ReactNode; isDark: boolean }) {
  return <div className={`text-[10px] font-semibold uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{children}</div>
}

function CopySignatureButton({ onCopy, isDark }: { onCopy: () => void; isDark: boolean }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      type="button"
      onClick={() => {
        onCopy()
        setCopied(true)
        setTimeout(() => setCopied(false), 1600)
      }}
      className={`inline-flex items-center gap-1 text-xs font-medium transition-colors ${copied
        ? 'text-aquilia-400'
        : isDark
          ? 'text-gray-400 hover:text-white'
          : 'text-gray-500 hover:text-gray-800'
        }`}
    >
      {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
      {copied ? 'Copied' : 'Copy signature'}
    </button>
  )
}
