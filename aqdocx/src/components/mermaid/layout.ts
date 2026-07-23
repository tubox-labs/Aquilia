import type { FlowGraph, FlowNode, FlowEdge, Subgraph, SequenceDiagram, SequenceParticipant } from './parser'

export interface PositionedNode {
  node: FlowNode
  x: number
  y: number
  width: number
  height: number
}

export interface PositionedEdge {
  edge: FlowEdge
  pathD: string
  labelX: number
  labelY: number
  arrowAngle: number
}

export interface PositionedSubgraph {
  subgraph: Subgraph
  x: number
  y: number
  width: number
  height: number
}

export interface FlowLayoutResult {
  kind: 'flowchart'
  width: number
  height: number
  nodes: PositionedNode[]
  edges: PositionedEdge[]
  subgraphs: PositionedSubgraph[]
}

export interface PositionedParticipant {
  participant: SequenceParticipant
  x: number
  width: number
}

export interface PositionedSeqMessage {
  fromX: number
  toX: number
  y: number
  label: string
  isDashed: boolean
  isArrow: boolean
  direction: 'right' | 'left' | 'self'
}

export interface PositionedSeqNote {
  x: number
  y: number
  width: number
  height: number
  label: string
}

export interface SequenceLayoutResult {
  kind: 'sequence'
  width: number
  height: number
  participants: PositionedParticipant[]
  messages: PositionedSeqMessage[]
  notes: PositionedSeqNote[]
}

export type LayoutResult = FlowLayoutResult | SequenceLayoutResult

/**
 * Calculates node dimensions - comfortable, clear node box sizes
 */
function estimateNodeSize(node: FlowNode): { width: number; height: number } {
  const lines = node.label.split(/<br\s*\/?>|\n/i)
  const maxLineLen = lines.reduce((max, l) => Math.max(max, l.length), 0)

  // Generous text padding: 8.5px per char + 44px padding ensures text fits comfortably
  let width = Math.max(150, Math.ceil(maxLineLen * 8.5 + 44))
  let height = Math.max(48, lines.length * 20 + 28)

  if (node.shape === 'stadium' || node.shape === 'circle') {
    width += 28
  } else if (node.shape === 'diamond') {
    width += 44
    height += 24
  }

  return { width, height }
}

/**
 * Computes layout positions for a Flowgraph
 */
export function layoutFlowgraph(graph: FlowGraph): FlowLayoutResult {
  const isHorizontal = graph.direction === 'LR' || graph.direction === 'RL'

  const nodeMap = graph.nodes
  const nodeList = Array.from(nodeMap.values())

  if (nodeList.length === 0) {
    return {
      kind: 'flowchart',
      width: 450,
      height: 220,
      nodes: [],
      edges: [],
      subgraphs: [],
    }
  }

  // 1. Calculate ranks (levels) via topological depth search
  const inDegree = new Map<string, number>()
  const outEdges = new Map<string, string[]>()

  nodeList.forEach(n => {
    inDegree.set(n.id, 0)
    outEdges.set(n.id, [])
  })

  graph.edges.forEach(e => {
    if (inDegree.has(e.to)) {
      inDegree.set(e.to, (inDegree.get(e.to) || 0) + 1)
    }
    if (outEdges.has(e.from)) {
      outEdges.get(e.from)!.push(e.to)
    }
  })

  const levels = new Map<string, number>()
  const queue: string[] = []

  inDegree.forEach((deg, id) => {
    if (deg === 0) {
      queue.push(id)
      levels.set(id, 0)
    }
  })

  // Topological / BFS rank assignment
  let maxLevel = 0
  while (queue.length > 0) {
    const curr = queue.shift()!
    const currLevel = levels.get(curr) || 0

    const neighbors = outEdges.get(curr) || []
    neighbors.forEach(next => {
      const nextLevel = Math.max(levels.get(next) ?? 0, currLevel + 1)
      levels.set(next, nextLevel)
      if (nextLevel > maxLevel) maxLevel = nextLevel

      const newDeg = (inDegree.get(next) || 1) - 1
      inDegree.set(next, newDeg)
      if (newDeg <= 0) {
        queue.push(next)
      }
    })
  }

  // Assign remaining cycle/unreached nodes
  nodeList.forEach(n => {
    if (!levels.has(n.id)) {
      levels.set(n.id, 0)
    }
  })

  // Group nodes by level
  const rankGroups: FlowNode[][] = []
  for (let r = 0; r <= maxLevel; r++) {
    rankGroups.push([])
  }

  levels.forEach((lvl, id) => {
    const node = nodeMap.get(id)
    if (node && rankGroups[lvl]) {
      rankGroups[lvl].push(node)
    }
  })

  // Remove empty ranks
  const activeRanks = rankGroups.filter(g => g.length > 0)

  // 2. Compute coordinates for each rank
  const nodeSizes = new Map<string, { width: number; height: number }>()
  nodeList.forEach(n => {
    nodeSizes.set(n.id, estimateNodeSize(n))
  })

  const positionedNodes = new Map<string, PositionedNode>()

  const LEVEL_SPACING = isHorizontal ? 130 : 90
  const NODE_SPACING = isHorizontal ? 40 : 45
  const PADDING = 50

  let currentMainCoord = PADDING

  activeRanks.forEach((rankNodes) => {
    let rankCrossSize = 0
    let maxRankMainSize = 0

    rankNodes.forEach(node => {
      const size = nodeSizes.get(node.id)!
      const mainDim = isHorizontal ? size.width : size.height
      const crossDim = isHorizontal ? size.height : size.width

      if (mainDim > maxRankMainSize) maxRankMainSize = mainDim
      rankCrossSize += crossDim
    })

    rankCrossSize += (rankNodes.length - 1) * NODE_SPACING

    let currentCrossCoord = PADDING

    rankNodes.forEach(node => {
      const size = nodeSizes.get(node.id)!
      const crossDim = isHorizontal ? size.height : size.width

      const posX = isHorizontal ? currentMainCoord : currentCrossCoord
      const posY = isHorizontal ? currentCrossCoord : currentMainCoord

      positionedNodes.set(node.id, {
        node,
        x: posX,
        y: posY,
        width: size.width,
        height: size.height,
      })

      currentCrossCoord += crossDim + NODE_SPACING
    })

    currentMainCoord += maxRankMainSize + LEVEL_SPACING
  })

  const posNodeList = Array.from(positionedNodes.values())

  // Center levels relative to widest rank
  if (activeRanks.length > 0) {
    let maxCrossExtent = 0
    posNodeList.forEach(p => {
      const extent = isHorizontal ? p.y + p.height : p.x + p.width
      if (extent > maxCrossExtent) maxCrossExtent = extent
    })

    activeRanks.forEach(rankNodes => {
      let rankMin = Infinity
      let rankMax = -Infinity
      rankNodes.forEach(n => {
        const p = positionedNodes.get(n.id)!
        const val = isHorizontal ? p.y : p.x
        const dim = isHorizontal ? p.height : p.width
        if (val < rankMin) rankMin = val
        if (val + dim > rankMax) rankMax = val + dim
      })

      const rankExtent = rankMax - rankMin
      const offset = (maxCrossExtent - rankExtent) / 2 - rankMin

      if (offset > 0) {
        rankNodes.forEach(n => {
          const p = positionedNodes.get(n.id)!
          if (isHorizontal) {
            p.y += offset
          } else {
            p.x += offset
          }
        })
      }
    })
  }

  // 3. Compute Subgraph Bounding Boxes
  const positionedSubgraphs: PositionedSubgraph[] = graph.subgraphs.map(sub => {
    let minX = Infinity
    let minY = Infinity
    let maxX = -Infinity
    let maxY = -Infinity

    sub.nodeIds.forEach(id => {
      const p = positionedNodes.get(id)
      if (p) {
        minX = Math.min(minX, p.x)
        minY = Math.min(minY, p.y)
        maxX = Math.max(maxX, p.x + p.width)
        maxY = Math.max(maxY, p.y + p.height)
      }
    })

    const pad = 20
    return {
      subgraph: sub,
      x: minX - pad,
      y: minY - pad - 18,
      width: (maxX - minX) + pad * 2,
      height: (maxY - minY) + pad * 2 + 18,
    }
  })

  // 4. Compute Edge Paths & Label Positions
  const positionedEdges: PositionedEdge[] = graph.edges.map(edge => {
    const fromP = positionedNodes.get(edge.from)
    const toP = positionedNodes.get(edge.to)

    if (!fromP || !toP) {
      return {
        edge,
        pathD: '',
        labelX: 0,
        labelY: 0,
        arrowAngle: 0,
      }
    }

    let startX = fromP.x + fromP.width / 2
    let startY = fromP.y + fromP.height / 2
    let endX = toP.x + toP.width / 2
    let endY = toP.y + toP.height / 2

    if (isHorizontal) {
      if (toP.x >= fromP.x + fromP.width) {
        startX = fromP.x + fromP.width
        endX = toP.x
      } else if (fromP.x >= toP.x + toP.width) {
        startX = fromP.x
        endX = toP.x + toP.width
      }
    } else {
      if (toP.y >= fromP.y + fromP.height) {
        startY = fromP.y + fromP.height
        endY = toP.y
      } else if (fromP.y >= toP.y + toP.height) {
        startY = fromP.y
        endY = toP.y + toP.height
      }
    }

    let cp1X = startX
    let cp1Y = startY
    let cp2X = endX
    let cp2Y = endY

    const dx = Math.abs(endX - startX)
    const dy = Math.abs(endY - startY)

    if (isHorizontal) {
      const curveDist = Math.max(25, dx / 2)
      cp1X = startX + (endX >= startX ? curveDist : -curveDist)
      cp2X = endX - (endX >= startX ? curveDist : -curveDist)
    } else {
      const curveDist = Math.max(25, dy / 2)
      cp1Y = startY + (endY >= startY ? curveDist : -curveDist)
      cp2Y = endY - (endY >= startY ? curveDist : -curveDist)
    }

    const pathD = `M ${startX} ${startY} C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${endX} ${endY}`

    const labelX = (startX + endX) / 2
    const labelY = (startY + endY) / 2

    const arrowAngle = Math.atan2(endY - cp2Y, endX - cp2X) * (180 / Math.PI)

    return {
      edge,
      pathD,
      labelX,
      labelY,
      arrowAngle,
    }
  })

  // Calculate total canvas bounding box
  let totalW = 0
  let totalH = 0

  posNodeList.forEach(p => {
    if (p.x + p.width + PADDING > totalW) totalW = p.x + p.width + PADDING
    if (p.y + p.height + PADDING > totalH) totalH = p.y + p.height + PADDING
  })

  positionedSubgraphs.forEach(s => {
    if (s.x + s.width + PADDING > totalW) totalW = s.x + s.width + PADDING
    if (s.y + s.height + PADDING > totalH) totalH = s.y + s.height + PADDING
  })

  return {
    kind: 'flowchart',
    width: Math.max(450, totalW),
    height: Math.max(260, totalH),
    nodes: posNodeList,
    edges: positionedEdges,
    subgraphs: positionedSubgraphs,
  }
}

/**
 * Computes layout positions for a Sequence Diagram
 */
export function layoutSequenceDiagram(seq: SequenceDiagram): SequenceLayoutResult {
  const PARTICIPANT_GAP = 210
  const START_X = 110
  const HEADER_Y = 50
  const STEP_HEIGHT = 65

  const participantPositions = new Map<string, number>()
  const posParticipants: PositionedParticipant[] = seq.participants.map((p, idx) => {
    const x = START_X + idx * PARTICIPANT_GAP
    participantPositions.set(p.id, x)
    return {
      participant: p,
      x,
      width: 160,
    }
  })

  const messages: PositionedSeqMessage[] = []
  const notes: PositionedSeqNote[] = []

  let currentY = HEADER_Y + 45

  seq.items.forEach(item => {
    if (item.kind === 'message') {
      const fromX = participantPositions.get(item.data.from) ?? START_X
      const toX = participantPositions.get(item.data.to) ?? START_X
      const isSelf = item.data.from === item.data.to

      messages.push({
        fromX,
        toX,
        y: currentY,
        label: item.data.label,
        isDashed: item.data.isDashed,
        isArrow: item.data.isArrow,
        direction: isSelf ? 'self' : toX >= fromX ? 'right' : 'left',
      })
      currentY += STEP_HEIGHT
    } else if (item.kind === 'note') {
      const pIds = item.data.participants
      const firstX = participantPositions.get(pIds[0]) ?? START_X

      let noteX = firstX - 70
      let noteWidth = 140

      if (pIds.length > 1) {
        const lastX = participantPositions.get(pIds[pIds.length - 1]) ?? firstX
        noteX = Math.min(firstX, lastX) - 20
        noteWidth = Math.abs(lastX - firstX) + 40
      }

      notes.push({
        x: noteX,
        y: currentY - 15,
        width: noteWidth,
        height: 42,
        label: item.data.label,
      })
      currentY += STEP_HEIGHT
    }
  })

  const totalWidth = START_X + posParticipants.length * PARTICIPANT_GAP + 60
  const totalHeight = currentY + 60

  return {
    kind: 'sequence',
    width: Math.max(550, totalWidth),
    height: Math.max(300, totalHeight),
    participants: posParticipants,
    messages,
    notes,
  }
}
