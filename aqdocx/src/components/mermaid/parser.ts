export type DiagramType = 'flowchart' | 'sequence' | 'unknown'

export interface StyleDef {
  fill?: string
  stroke?: string
  strokeWidth?: string
  color?: string
  borderRadius?: string
}

export type NodeShape = 
  | 'rectangle' 
  | 'round' 
  | 'stadium' 
  | 'subroutine' 
  | 'cylinder' 
  | 'circle' 
  | 'asymmetric' 
  | 'diamond' 
  | 'hexagon'

export interface FlowNode {
  id: string
  label: string
  shape: NodeShape
  className?: string
  style?: StyleDef
  subgraphId?: string
}

export type EdgeStyle = 'solid' | 'dashed' | 'thick'

export interface FlowEdge {
  from: string
  to: string
  label?: string
  style: EdgeStyle
  hasArrow: boolean
}

export interface Subgraph {
  id: string
  title: string
  nodeIds: string[]
}

export interface FlowGraph {
  type: 'flowchart'
  direction: 'TD' | 'LR' | 'BT' | 'RL'
  nodes: Map<string, FlowNode>
  edges: FlowEdge[]
  subgraphs: Subgraph[]
  classDefs: Map<string, StyleDef>
}

export interface SequenceParticipant {
  id: string
  label: string
}

export interface SequenceMessage {
  from: string
  to: string
  label: string
  isDashed: boolean
  isArrow: boolean
}

export interface SequenceNote {
  participants: string[]
  label: string
  position: 'over' | 'left' | 'right'
}

export interface SequenceItemMessage {
  kind: 'message'
  data: SequenceMessage
}

export interface SequenceItemNote {
  kind: 'note'
  data: SequenceNote
}

export type SequenceItem = SequenceItemMessage | SequenceItemNote

export interface SequenceDiagram {
  type: 'sequence'
  participants: SequenceParticipant[]
  items: SequenceItem[]
}

export type ParsedDiagram = FlowGraph | SequenceDiagram

/**
 * Pre-processes and sanitizes raw mermaid chart text.
 */
export function sanitizeMermaidText(code: string): string {
  let cleaned = code.trim()

  // Strip backtick blocks if present
  cleaned = cleaned.replace(/^```\s*mermaid\s*/i, '').replace(/```\s*$/, '').trim()
  if (cleaned.startsWith('mermaid\n') || cleaned.startsWith('mermaid\r\n')) {
    cleaned = cleaned.replace(/^mermaid\r?\n/, '').trim()
  }

  // Normalize quotes and entities
  cleaned = cleaned
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2015]/g, '-')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/\u00A0/g, ' ')
    .replace(/&gt;/g, '>')
    .replace(/&lt;/g, '<')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')

  return cleaned
}

/**
 * Parses style string into a StyleDef object
 * e.g., "fill:#2a2b36,stroke:#7c3aed,stroke-width:2px,color:#fff;"
 */
function parseStyleDef(styleStr: string): StyleDef {
  const styles: StyleDef = {}
  const pairs = styleStr.split(/[,;]/)
  for (const pair of pairs) {
    const [key, val] = pair.split(':').map(s => s?.trim())
    if (!key || !val) continue
    const k = key.toLowerCase()
    if (k === 'fill' || k === 'background') styles.fill = val
    else if (k === 'stroke') styles.stroke = val
    else if (k === 'stroke-width') styles.strokeWidth = val
    else if (k === 'color') styles.color = val
    else if (k === 'border-radius' || k === 'rx') styles.borderRadius = val
  }
  return styles
}

/**
 * Helper to parse a node definition string like:
 * RawData[Inbound Raw Data]:::phase
 * PhaseCast[Phase 1: Cast<br/>Type Coercion]
 * NodeId(["Label"])
 */
function extractNodeDetails(rawToken: string): {
  id: string
  label?: string
  shape?: NodeShape
  className?: string
} {
  let token = rawToken.trim()
  let className: string | undefined

  // Extract trailing :::className
  const classMatch = token.match(/^(.*?):::([A-Za-z0-9_-]+)$/)
  if (classMatch) {
    token = classMatch[1].trim()
    className = classMatch[2]
  }

  // Detect shape patterns
  // Stadium: Id([Label])
  let m = token.match(/^([A-Za-z0-9_.-]+)\(\[\s*([\s\S]*?)\s*\]\)$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'stadium', className }

  // Subroutine: Id[[Label]]
  m = token.match(/^([A-Za-z0-9_.-]+)\[\[\s*([\s\S]*?)\s*\]\]$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'subroutine', className }

  // Cylinder: Id[(Label)]
  m = token.match(/^([A-Za-z0-9_.-]+)\[\(\s*([\s\S]*?)\s*\)\]$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'cylinder', className }

  // Circle: Id((Label))
  m = token.match(/^([A-Za-z0-9_.-]+)\(\(\s*([\s\S]*?)\s*\)\)$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'circle', className }

  // Hexagon: Id{{Label}}
  m = token.match(/^([A-Za-z0-9_.-]+)\{\{\s*([\s\S]*?)\s*\}\}$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'hexagon', className }

  // Diamond: Id{Label}
  m = token.match(/^([A-Za-z0-9_.-]+)\{\s*([\s\S]*?)\s*\}$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'diamond', className }

  // Asymmetric: Id>Label]
  m = token.match(/^([A-Za-z0-9_.-]+)>\s*([\s\S]*?)\s*\]$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'asymmetric', className }

  // Rounded: Id(Label)
  m = token.match(/^([A-Za-z0-9_.-]+)\(\s*([\s\S]*?)\s*\)$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'round', className }

  // Rectangle: Id[Label]
  m = token.match(/^([A-Za-z0-9_.-]+)\[\s*([\s\S]*?)\s*\]$/)
  if (m) return { id: m[1], label: cleanLabel(m[2]), shape: 'rectangle', className }

  // Plain Id
  return { id: token, shape: 'rectangle', className }
}

function cleanLabel(raw: string): string {
  let label = raw.trim()
  if ((label.startsWith('"') && label.endsWith('"')) || (label.startsWith("'") && label.endsWith("'"))) {
    label = label.slice(1, -1)
  }
  return label
}

/**
 * Main parse entrypoint
 */
export function parseMermaid(chartText: string): ParsedDiagram {
  const cleanCode = sanitizeMermaidText(chartText)
  const lines = cleanCode.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0 && !l.startsWith('%%'))

  if (lines.length === 0) {
    return {
      type: 'flowchart',
      direction: 'TD',
      nodes: new Map(),
      edges: [],
      subgraphs: [],
      classDefs: new Map(),
    }
  }

  const header = lines[0]

  if (/^sequenceDiagram/i.test(header)) {
    return parseSequenceDiagram(lines)
  }

  return parseFlowchart(lines)
}

/**
 * Parses sequence diagrams
 */
function parseSequenceDiagram(lines: string[]): SequenceDiagram {
  const participantsMap = new Map<string, string>()
  const items: SequenceItem[] = []

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i]
    if (line.startsWith('autonumber')) continue

    // participant ID as Label or participant ID
    const partMatch = line.match(/^participant\s+([A-Za-z0-9_.-]+)(?:\s+as\s+(.+))?$/i)
    if (partMatch) {
      const id = partMatch[1]
      const label = cleanLabel(partMatch[2] || id)
      participantsMap.set(id, label)
      continue
    }

    // Note over B: text or Note over B,S: text or Note left of B: text
    const noteMatch = line.match(/^Note\s+(over|left of|right of)\s+([A-Za-z0-9_,.-]+):\s*(.+)$/i)
    if (noteMatch) {
      const posType = noteMatch[1].toLowerCase()
      const rawParts = noteMatch[2].split(',').map(s => s.trim())
      const text = noteMatch[3].trim()

      rawParts.forEach(p => {
        if (!participantsMap.has(p)) participantsMap.set(p, p)
      })

      const position: 'over' | 'left' | 'right' = posType.includes('left') ? 'left' : posType.includes('right') ? 'right' : 'over'

      items.push({
        kind: 'note',
        data: {
          participants: rawParts,
          label: text,
          position,
        },
      })
      continue
    }

    // Arrow Messages: From->>To: Label, From-->>To: Label, From->To: Label, From-->To: Label
    const msgMatch = line.match(/^([A-Za-z0-9_.-]+)\s*(-{1,2}>+|-x|--x)\s*([A-Za-z0-9_.-]+):\s*(.+)$/)
    if (msgMatch) {
      const from = msgMatch[1]
      const arrowOp = msgMatch[2]
      const to = msgMatch[3]
      const label = msgMatch[4].trim()

      if (!participantsMap.has(from)) participantsMap.set(from, from)
      if (!participantsMap.has(to)) participantsMap.set(to, to)

      const isDashed = arrowOp.includes('--')
      const isArrow = true

      items.push({
        kind: 'message',
        data: { from, to, label, isDashed, isArrow },
      })
      continue
    }
  }

  const participants: SequenceParticipant[] = Array.from(participantsMap.entries()).map(([id, label]) => ({
    id,
    label,
  }))

  return {
    type: 'sequence',
    participants,
    items,
  }
}

/**
 * Parses flowcharts / graphs
 */
function parseFlowchart(lines: string[]): FlowGraph {
  let direction: 'TD' | 'LR' | 'BT' | 'RL' = 'TD'

  const firstLine = lines[0]
  const dirMatch = firstLine.match(/^(?:graph|flowchart)\s+(TD|LR|BT|RL|TB)/i)
  if (dirMatch) {
    const rawDir = dirMatch[1].toUpperCase()
    direction = rawDir === 'TB' ? 'TD' : (rawDir as any)
  }

  const nodes = new Map<string, FlowNode>()
  const edges: FlowEdge[] = []
  const classDefs = new Map<string, StyleDef>()
  const subgraphs: Subgraph[] = []

  let currentSubgraph: Subgraph | null = null

  const getOrCreateNode = (id: string, initialLabel?: string, shape?: NodeShape, className?: string): FlowNode => {
    const existing = nodes.get(id)
    if (existing) {
      if (initialLabel && initialLabel !== id) existing.label = initialLabel
      if (shape) existing.shape = shape
      if (className) existing.className = className
      if (currentSubgraph && !existing.subgraphId) existing.subgraphId = currentSubgraph.id
      return existing
    }

    const node: FlowNode = {
      id,
      label: initialLabel || id,
      shape: shape || 'rectangle',
      className,
      subgraphId: currentSubgraph?.id,
    }
    nodes.set(id, node)
    if (currentSubgraph) {
      currentSubgraph.nodeIds.push(id)
    }
    return node
  }

  for (let i = (dirMatch ? 1 : 0); i < lines.length; i++) {
    const line = lines[i]

    // Subgraph start
    const subMatch = line.match(/^subgraph\s+([A-Za-z0-9_.-]+)?\s*(?:\["?([^"\]]+)"?\])?/i)
    if (subMatch) {
      const subId = subMatch[1] || `sub_${subgraphs.length}`
      const subTitle = subMatch[2] || subMatch[1] || `Subgraph ${subgraphs.length + 1}`
      currentSubgraph = { id: subId, title: subTitle, nodeIds: [] }
      subgraphs.push(currentSubgraph)
      continue
    }

    // Subgraph end
    if (/^end$/i.test(line)) {
      currentSubgraph = null
      continue
    }

    // classDef parsing: classDef phase fill:#2a2b36,stroke:#7c3aed,stroke-width:2px,color:#fff;
    const classDefMatch = line.match(/^classDef\s+([A-Za-z0-9_-]+)\s+(.+)$/i)
    if (classDefMatch) {
      const cName = classDefMatch[1]
      const styleObj = parseStyleDef(classDefMatch[2])
      classDefs.set(cName, styleObj)
      continue
    }

    // class assignment: class Node1,Node2 phase
    const classAssignMatch = line.match(/^class\s+([A-Za-z0-9_,.-]+)\s+([A-Za-z0-9_-]+)$/i)
    if (classAssignMatch) {
      const ids = classAssignMatch[1].split(',').map(s => s.trim())
      const cName = classAssignMatch[2]
      ids.forEach(id => {
        const node = getOrCreateNode(id)
        node.className = cName
      })
      continue
    }

    let hasEdgeMatch = false

    // We tokenize edges line by line
    // e.g. A[Label] -->|Cast Error| B[Next]:::fail
    const edgeTokens = line.split(/\s*(-->|-\.->|==>|---|-->(?:\|[^|\n\r]+\|)|-\.->(?:\|[^|\n\r]+\|)|==>(?:\|[^|\n\r]+\|)|---(?:\|[^|\n\r]+\|))\s*/)

    if (edgeTokens.length >= 3) {
      for (let k = 0; k < edgeTokens.length - 2; k += 2) {
        const leftStr = edgeTokens[k].trim()
        const opStr = edgeTokens[k + 1]?.trim()
        const rightStr = edgeTokens[k + 2]?.trim()

        if (!leftStr || !opStr || !rightStr) continue

        const leftDetails = extractNodeDetails(leftStr)
        const rightDetails = extractNodeDetails(rightStr)

        const fromNode = getOrCreateNode(leftDetails.id, leftDetails.label, leftDetails.shape, leftDetails.className)
        const toNode = getOrCreateNode(rightDetails.id, rightDetails.label, rightDetails.shape, rightDetails.className)

        // Parse edge operator & label
        let label: string | undefined
        let style: EdgeStyle = 'solid'
        let hasArrow = true

        let cleanOp = opStr
        const labelInOpMatch = opStr.match(/^(-->|-\.->|==>|---)\|([^|]+)\|$/)
        if (labelInOpMatch) {
          cleanOp = labelInOpMatch[1]
          label = cleanLabel(labelInOpMatch[2])
        }

        if (cleanOp.includes('-.->')) {
          style = 'dashed'
        } else if (cleanOp.includes('==>')) {
          style = 'thick'
        } else if (cleanOp.includes('---')) {
          style = 'solid'
          hasArrow = false
        }

        edges.push({
          from: fromNode.id,
          to: toNode.id,
          label,
          style,
          hasArrow,
        })
        hasEdgeMatch = true
      }
    }

    if (!hasEdgeMatch) {
      // Standalone node definition on line
      const details = extractNodeDetails(line)
      if (details.id && !details.id.includes(' ')) {
        getOrCreateNode(details.id, details.label, details.shape, details.className)
      }
    }
  }

  // Apply classDefs to nodes if present
  nodes.forEach(node => {
    if (node.className && classDefs.has(node.className)) {
      node.style = classDefs.get(node.className)
    }
  })

  return {
    type: 'flowchart',
    direction,
    nodes,
    edges,
    subgraphs,
    classDefs,
  }
}
