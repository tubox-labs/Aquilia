import React, { useState, useRef, useId, useMemo, useEffect, useCallback } from 'react'
import { Copy, Check, Code, Eye, ZoomIn, ZoomOut, RotateCcw, AlertCircle, Move } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { parseMermaid } from './mermaid/parser'
import { layoutFlowgraph, layoutSequenceDiagram } from './mermaid/layout'
import type { FlowLayoutResult, SequenceLayoutResult, PositionedNode } from './mermaid/layout'

interface MermaidDiagramProps {
  chart: string
  title?: string
}

export function MermaidDiagram({ chart, title }: MermaidDiagramProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [showRaw, setShowRaw] = useState<boolean>(false)
  const [copied, setCopied] = useState<boolean>(false)

  // Pan & Zoom gesture states
  const [zoom, setZoom] = useState<number>(1)
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState<boolean>(false)

  // Refs for tracking gestures & non-passive wheel events
  const containerRef = useRef<HTMLDivElement>(null)
  const pointerStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const initialPanRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const touchDistanceRef = useRef<number | null>(null)
  const initialZoomRef = useRef<number>(1)
  const touchCenterRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })

  const rawId = useId()
  const uniqueId = `aquilia-mermaid-${rawId.replace(/[^a-zA-Z0-9]/g, '')}`

  // Parse and calculate layout
  const layout = useMemo(() => {
    try {
      const parsed = parseMermaid(chart)
      if (parsed.type === 'sequence') {
        return layoutSequenceDiagram(parsed)
      }
      return layoutFlowgraph(parsed)
    } catch (err) {
      console.warn('Aquilia Mermaid Parser error:', err)
      return null
    }
  }, [chart])

  const handleCopy = () => {
    navigator.clipboard.writeText(chart)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleZoomIn = () => setZoom(prev => Math.min(2.5, prev + 0.15))
  const handleZoomOut = () => setZoom(prev => Math.max(0.4, prev - 0.15))
  const handleReset = useCallback(() => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }, [])

  /* ========================================================================= */
  /* NON-PASSIVE EVENT LISTENERS: Lock browser page zoom & scroll              */
  /* ========================================================================= */
  useEffect(() => {
    const el = containerRef.current
    if (!el || showRaw) return

    // Prevent browser webpage zoom when cursor is over diagram box
    const handleNativeWheel = (e: WheelEvent) => {
      e.preventDefault()
      e.stopPropagation()

      if (e.ctrlKey || e.metaKey) {
        // Zoom diagram inside box
        const delta = e.deltaY < 0 ? 0.12 : -0.12
        setZoom(prev => Math.max(0.4, Math.min(2.5, prev + delta)))
      } else {
        // Pan diagram inside box
        setPan(prev => ({
          x: prev.x - e.deltaX * 0.8,
          y: prev.y - e.deltaY * 0.8,
        }))
      }
    }

    // Prevent touch pinch from zooming whole browser viewport
    const handleNativeTouchMove = (e: TouchEvent) => {
      if (e.touches.length >= 2) {
        e.preventDefault()
      }
    }

    el.addEventListener('wheel', handleNativeWheel, { passive: false })
    el.addEventListener('touchmove', handleNativeTouchMove, { passive: false })

    return () => {
      el.removeEventListener('wheel', handleNativeWheel)
      el.removeEventListener('touchmove', handleNativeTouchMove)
    }
  }, [showRaw])

  /* ========================================================================= */
  /* GESTURE HANDLERS: Pointer Drag & Multi-Touch Gestures                     */
  /* ========================================================================= */

  // Pointer Down (Mouse click drag / Pointer touch)
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (showRaw || !layout) return
    setIsDragging(true)
    pointerStartRef.current = { x: e.clientX, y: e.clientY }
    initialPanRef.current = { ...pan }
    if (containerRef.current) {
      containerRef.current.setPointerCapture(e.pointerId)
    }
  }

  // Pointer Move (Panning inside box)
  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return
    const dx = e.clientX - pointerStartRef.current.x
    const dy = e.clientY - pointerStartRef.current.y
    setPan({
      x: initialPanRef.current.x + dx,
      y: initialPanRef.current.y + dy,
    })
  }

  // Pointer Up
  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDragging) {
      setIsDragging(false)
      if (containerRef.current && containerRef.current.hasPointerCapture(e.pointerId)) {
        containerRef.current.releasePointerCapture(e.pointerId)
      }
    }
  }

  // Touch Start (3-Finger Pan & Pinch-to-Zoom)
  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    if (showRaw || !layout) return

    const touches = e.touches
    if (touches.length >= 1) {
      let sumX = 0
      let sumY = 0
      for (let i = 0; i < touches.length; i++) {
        sumX += touches[i].clientX
        sumY += touches[i].clientY
      }
      const centerX = sumX / touches.length
      const centerY = sumY / touches.length

      touchCenterRef.current = { x: centerX, y: centerY }
      initialPanRef.current = { ...pan }

      if (touches.length === 2) {
        const t1 = touches[0]
        const t2 = touches[1]
        const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY)
        touchDistanceRef.current = dist
        initialZoomRef.current = zoom
      } else {
        touchDistanceRef.current = null
      }
    }
  }

  // Touch Move (Pan / Pinch inside box)
  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    if (showRaw || !layout) return

    const touches = e.touches
    if (touches.length >= 1) {
      if (touches.length === 2 && touchDistanceRef.current !== null) {
        const t1 = touches[0]
        const t2 = touches[1]
        const currentDist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY)
        const scaleChange = currentDist / touchDistanceRef.current
        const newZoom = Math.max(0.4, Math.min(2.5, initialZoomRef.current * scaleChange))
        setZoom(newZoom)
      }

      let sumX = 0
      let sumY = 0
      for (let i = 0; i < touches.length; i++) {
        sumX += touches[i].clientX
        sumY += touches[i].clientY
      }
      const currentCenterX = sumX / touches.length
      const currentCenterY = sumY / touches.length

      const dx = currentCenterX - touchCenterRef.current.x
      const dy = currentCenterY - touchCenterRef.current.y

      setPan({
        x: initialPanRef.current.x + dx,
        y: initialPanRef.current.y + dy,
      })
    }
  }

  const handleTouchEnd = () => {
    touchDistanceRef.current = null
  }

  // Double Click (Toggle Zoom reset)
  const handleDoubleClick = () => {
    if (zoom !== 1 || pan.x !== 0 || pan.y !== 0) {
      handleReset()
    } else {
      setZoom(1.4)
    }
  }

  return (
    <div className={`my-6 overflow-hidden rounded-xl border transition-all duration-200 ${
      isDark 
        ? 'border-zinc-800 bg-zinc-950/90 text-zinc-100' 
        : 'border-zinc-200 bg-white text-zinc-900 shadow-sm'
    }`}>
      {/* Top Diagram Toolbar */}
      <div className={`flex items-center justify-between px-4 py-2.5 border-b text-xs font-medium ${
        isDark ? 'border-zinc-800 bg-zinc-900/60 text-zinc-300' : 'border-zinc-200 bg-zinc-50 text-zinc-700'
      }`}>
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-xs tracking-wide text-zinc-300 dark:text-zinc-300">
            {title || 'Diagram'}
          </span>
          <span className="hidden sm:inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-zinc-800/60 text-[10px] text-zinc-400">
            <Move className="w-2.5 h-2.5 text-aquilia-400 mr-0.5" />
            <span>3-Finger / Drag Pan & Zoom</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Zoom & Reset controls */}
          {!showRaw && layout && (
            <div className={`flex items-center space-x-1 px-2 py-0.5 rounded border text-[11px] ${
              isDark ? 'border-zinc-800 bg-zinc-900 text-zinc-400' : 'border-zinc-200 bg-zinc-100 text-zinc-600'
            }`}>
              <button
                onClick={handleZoomOut}
                className="p-0.5 hover:text-white transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="w-8 text-center font-mono text-[10px]">{Math.round(zoom * 100)}%</span>
              <button
                onClick={handleZoomIn}
                className="p-0.5 hover:text-white transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={handleReset}
                className="p-0.5 hover:text-white transition-colors border-l pl-1.5 ml-0.5 border-zinc-800 flex items-center space-x-0.5"
                title="Reset View & Position"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
            </div>
          )}

          <button
            onClick={() => setShowRaw(!showRaw)}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border text-xs transition-colors ${
              isDark 
                ? 'border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800' 
                : 'border-zinc-200 bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
            }`}
            title={showRaw ? 'View Diagram' : 'View Code'}
          >
            {showRaw ? <Eye className="w-3.5 h-3.5" /> : <Code className="w-3.5 h-3.5" />}
            <span>{showRaw ? 'Diagram' : 'Code'}</span>
          </button>

          <button
            onClick={handleCopy}
            className={`p-1 rounded border transition-colors ${
              isDark 
                ? 'border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-400' 
                : 'border-zinc-200 bg-zinc-100 hover:bg-zinc-200 text-zinc-600'
            }`}
            title="Copy Code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Diagram Canvas Box */}
      <div 
        ref={containerRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onDoubleClick={handleDoubleClick}
        className={`relative p-6 flex justify-center items-center overflow-hidden min-h-[180px] select-none touch-none ${
          isDragging ? 'cursor-grabbing' : 'cursor-grab'
        }`}
      >
        {showRaw && (
          <pre className={`w-full p-4 rounded-lg text-xs font-mono overflow-x-auto ${
            isDark ? 'bg-zinc-900 text-zinc-300 border border-zinc-800' : 'bg-zinc-100 text-zinc-800'
          }`}>
            {chart}
          </pre>
        )}

        {!showRaw && !layout && (
          <div className="w-full">
            <div className={`flex items-center space-x-2 p-3 rounded-lg mb-3 text-xs ${
              isDark ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20' : 'bg-zinc-100 text-zinc-700 border border-zinc-200'
            }`}>
              <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>Unable to render diagram visually. Showing source code:</span>
            </div>
            <pre className={`p-4 rounded-lg text-xs font-mono overflow-x-auto ${
              isDark ? 'bg-zinc-900 text-zinc-300 border border-zinc-800' : 'bg-zinc-100 text-zinc-800'
            }`}>
              {chart}
            </pre>
          </div>
        )}

        {!showRaw && layout && (
          <div 
            className="transition-transform duration-75 ease-out flex justify-center items-center overflow-visible"
            style={{ 
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, 
              transformOrigin: 'center center' 
            }}
          >
            {layout.kind === 'flowchart' ? (
              <FlowchartRenderer layout={layout} isDark={isDark} uniqueId={uniqueId} />
            ) : (
              <SequenceRenderer layout={layout} isDark={isDark} uniqueId={uniqueId} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Flowchart SVG Renderer (Classic, clean Mermaid styling - 1:1 scale)
 */
function FlowchartRenderer({ layout, isDark, uniqueId }: { layout: FlowLayoutResult; isDark: boolean; uniqueId: string }) {
  return (
    <svg
      width={layout.width}
      height={layout.height}
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ width: `${layout.width}px`, height: `${layout.height}px` }}
      className="overflow-visible block mx-auto shrink-0"
    >
      <defs>
        {/* Simple Arrow Marker */}
        <marker
          id={`${uniqueId}-arrow`}
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill={isDark ? '#94a3b8' : '#64748b'} />
        </marker>
      </defs>

      {/* Render Subgraphs */}
      {layout.subgraphs.map((sub, idx) => (
        <g key={`sub-${sub.subgraph.id}-${idx}`}>
          <rect
            x={sub.x}
            y={sub.y}
            width={sub.width}
            height={sub.height}
            rx="8"
            ry="8"
            fill={isDark ? 'rgba(30, 41, 59, 0.4)' : 'rgba(248, 250, 252, 0.8)'}
            stroke={isDark ? '#334155' : '#cbd5e1'}
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
          <text
            x={sub.x + 12}
            y={sub.y + 16}
            fill={isDark ? '#94a3b8' : '#64748b'}
            fontSize="11"
            fontWeight="600"
            fontFamily="Inter, system-ui, sans-serif"
          >
            {sub.subgraph.title}
          </text>
        </g>
      ))}

      {/* Render Edges */}
      {layout.edges.map((e, idx) => {
        const strokeColor = isDark ? '#94a3b8' : '#64748b'
        const markerUrl = `url(#${uniqueId}-arrow)`

        return (
          <g key={`edge-${idx}`}>
            <path
              d={e.pathD}
              fill="none"
              stroke={strokeColor}
              strokeWidth={e.edge.style === 'thick' ? '2.5' : '1.5'}
              strokeDasharray={e.edge.style === 'dashed' ? '5 4' : undefined}
              markerEnd={e.edge.hasArrow ? markerUrl : undefined}
            />
            {e.edge.label && (
              <g transform={`translate(${e.labelX}, ${e.labelY})`}>
                <rect
                  x={-(e.edge.label.length * 3.6 + 8)}
                  y="-10"
                  width={e.edge.label.length * 7.2 + 16}
                  height="20"
                  rx="4"
                  fill={isDark ? '#0f172a' : '#ffffff'}
                  stroke={isDark ? '#334155' : '#e2e8f0'}
                  strokeWidth="1"
                />
                <text
                  x="0"
                  y="3"
                  textAnchor="middle"
                  fill={isDark ? '#cbd5e1' : '#475569'}
                  fontSize="11"
                  fontWeight="500"
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {e.edge.label}
                </text>
              </g>
            )}
          </g>
        )
      })}

      {/* Render Nodes (Text completely enclosed inside node boxes) */}
      {layout.nodes.map((posNode) => (
        <NodeItem key={posNode.node.id} posNode={posNode} isDark={isDark} />
      ))}
    </svg>
  )
}

/**
 * Single Node SVG Component
 */
function NodeItem({ posNode, isDark }: { posNode: PositionedNode; isDark: boolean }) {
  const { node, x, y, width, height } = posNode

  let fill = isDark ? '#1e293b' : '#f8fafc'
  let stroke = isDark ? '#475569' : '#cbd5e1'
  let textColor = isDark ? '#f8fafc' : '#0f172a'

  if (node.style) {
    if (node.style.fill) fill = node.style.fill
    if (node.style.stroke) stroke = node.style.stroke
    if (node.style.color) textColor = node.style.color
  } else if (node.className) {
    const cName = node.className.toLowerCase()
    if (cName.includes('phase')) {
      fill = isDark ? '#2e1065' : '#f3e8ff'
      stroke = isDark ? '#7c3aed' : '#a855f7'
      textColor = isDark ? '#f3e8ff' : '#4c1d95'
    } else if (cName.includes('success')) {
      fill = isDark ? '#064e3b' : '#ecfdf5'
      stroke = isDark ? '#10b981' : '#059669'
      textColor = isDark ? '#dcfce7' : '#064e3b'
    } else if (cName.includes('fail') || cName.includes('error')) {
      fill = isDark ? '#450a0a' : '#fef2f2'
      stroke = isDark ? '#ef4444' : '#dc2626'
      textColor = isDark ? '#fee2e2' : '#7f1d1d'
    }
  }

  const lines = node.label.split(/<br\s*\/?>|\n/i)

  return (
    <g transform={`translate(${x}, ${y})`}>
      {/* Node Shapes */}
      {node.shape === 'stadium' || node.shape === 'round' ? (
        <rect
          x="0"
          y="0"
          width={width}
          height={height}
          rx={height / 2}
          ry={height / 2}
          fill={fill}
          stroke={stroke}
          strokeWidth="1.5"
        />
      ) : node.shape === 'circle' ? (
        <circle
          cx={width / 2}
          cy={height / 2}
          r={Math.min(width, height) / 2}
          fill={fill}
          stroke={stroke}
          strokeWidth="1.5"
        />
      ) : node.shape === 'diamond' ? (
        <polygon
          points={`${width / 2},0 ${width},${height / 2} ${width / 2},${height} 0,${height / 2}`}
          fill={fill}
          stroke={stroke}
          strokeWidth="1.5"
        />
      ) : node.shape === 'cylinder' ? (
        <g>
          <path
            d={`M 0 10 A ${width / 2} 8 0 0 0 ${width} 10 V ${height - 10} A ${width / 2} 8 0 0 1 0 ${height - 10} Z`}
            fill={fill}
            stroke={stroke}
            strokeWidth="1.5"
          />
          <ellipse
            cx={width / 2}
            cy="10"
            rx={width / 2}
            ry="8"
            fill={fill}
            stroke={stroke}
            strokeWidth="1.5"
          />
        </g>
      ) : (
        /* Regular Mermaid Rectangle */
        <rect
          x="0"
          y="0"
          width={width}
          height={height}
          rx="6"
          ry="6"
          fill={fill}
          stroke={stroke}
          strokeWidth="1.5"
        />
      )}

      {/* Node Text Label */}
      <text
        x={width / 2}
        y={height / 2 - ((lines.length - 1) * 8)}
        textAnchor="middle"
        dominantBaseline="central"
        fill={textColor}
        fontSize="11.5"
        fontWeight="500"
        fontFamily="Inter, system-ui, -apple-system, sans-serif"
      >
        {lines.map((line, idx) => (
          <tspan key={idx} x={width / 2} dy={idx === 0 ? 0 : 16}>
            {line}
          </tspan>
        ))}
      </text>
    </g>
  )
}

/**
 * Sequence Diagram Renderer
 */
function SequenceRenderer({ layout, isDark, uniqueId }: { layout: SequenceLayoutResult; isDark: boolean; uniqueId: string }) {
  return (
    <svg
      width={layout.width}
      height={layout.height}
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ width: `${layout.width}px`, height: `${layout.height}px` }}
      className="overflow-visible block mx-auto shrink-0"
    >
      <defs>
        <marker
          id={`${uniqueId}-seq-arrow`}
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill={isDark ? '#94a3b8' : '#64748b'} />
        </marker>
      </defs>

      {/* Lifelines & Participant Cards */}
      {layout.participants.map((p, idx) => (
        <g key={`part-${p.participant.id}-${idx}`}>
          <line
            x1={p.x}
            y1={65}
            x2={p.x}
            y2={layout.height - 45}
            stroke={isDark ? '#334155' : '#cbd5e1'}
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />

          {/* Top Header Card */}
          <g transform={`translate(${p.x - p.width / 2}, 25)`}>
            <rect
              x="0"
              y="0"
              width={p.width}
              height="36"
              rx="6"
              fill={isDark ? '#1e293b' : '#f8fafc'}
              stroke={isDark ? '#475569' : '#cbd5e1'}
              strokeWidth="1.5"
            />
            <text
              x={p.width / 2}
              y="18"
              textAnchor="middle"
              dominantBaseline="central"
              fill={isDark ? '#f8fafc' : '#0f172a'}
              fontSize="11.5"
              fontWeight="500"
              fontFamily="Inter, system-ui, sans-serif"
            >
              {p.participant.label}
            </text>
          </g>

          {/* Bottom Footer Card */}
          <g transform={`translate(${p.x - p.width / 2}, ${layout.height - 40})`}>
            <rect
              x="0"
              y="0"
              width={p.width}
              height="32"
              rx="6"
              fill={isDark ? '#1e293b' : '#f8fafc'}
              stroke={isDark ? '#475569' : '#cbd5e1'}
              strokeWidth="1.5"
            />
            <text
              x={p.width / 2}
              y="16"
              textAnchor="middle"
              dominantBaseline="central"
              fill={isDark ? '#94a3b8' : '#64748b'}
              fontSize="11"
              fontWeight="500"
              fontFamily="Inter, system-ui, sans-serif"
            >
              {p.participant.label}
            </text>
          </g>
        </g>
      ))}

      {/* Render Messages */}
      {layout.messages.map((m, idx) => {
        const strokeColor = isDark ? '#94a3b8' : '#64748b'
        const markerUrl = `url(#${uniqueId}-seq-arrow)`

        return (
          <g key={`msg-${idx}`}>
            <line
              x1={m.fromX}
              y1={m.y}
              x2={m.toX}
              y2={m.y}
              stroke={strokeColor}
              strokeWidth="1.5"
              strokeDasharray={m.isDashed ? '5 4' : undefined}
              markerEnd={m.isArrow ? markerUrl : undefined}
            />
            <g transform={`translate(${(m.fromX + m.toX) / 2}, ${m.y - 11})`}>
              <rect
                x={-(m.label.length * 3.6 + 8)}
                y="-9"
                width={m.label.length * 7.2 + 16}
                height="18"
                rx="4"
                fill={isDark ? '#0f172a' : '#ffffff'}
                stroke={isDark ? '#334155' : '#e2e8f0'}
                strokeWidth="1"
              />
              <text
                x="0"
                y="2.5"
                textAnchor="middle"
                fill={isDark ? '#cbd5e1' : '#475569'}
                fontSize="11"
                fontWeight="500"
                fontFamily="Inter, system-ui, sans-serif"
              >
                {m.label}
              </text>
            </g>
          </g>
        )
      })}

      {/* Render Notes */}
      {layout.notes.map((n, idx) => (
        <g key={`note-${idx}`} transform={`translate(${n.x}, ${n.y})`}>
          <rect
            x="0"
            y="0"
            width={n.width}
            height={n.height}
            rx="6"
            fill={isDark ? '#2e1065' : '#f3e8ff'}
            stroke={isDark ? '#7c3aed' : '#a855f7'}
            strokeWidth="1.25"
          />
          <text
            x={n.width / 2}
            y={n.height / 2}
            textAnchor="middle"
            dominantBaseline="central"
            fill={isDark ? '#d8b4fe' : '#6b21a8'}
            fontSize="11"
            fontWeight="500"
            fontFamily="Inter, system-ui, sans-serif"
          >
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  )
}
