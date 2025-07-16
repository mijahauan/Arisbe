import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Card, CardContent } from '@/components/ui/card.jsx'
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Move, 
  Circle, 
  Square,
  Minus,
  Plus
} from 'lucide-react'

const GraphVisualization = ({ graph, graphId, onGraphUpdate, onError }) => {
  const svgRef = useRef(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [selectedItem, setSelectedItem] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  // Reset view when graph changes
  useEffect(() => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setSelectedItem(null)
  }, [graphId])

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 3))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.3))
  }

  const handleReset = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setSelectedItem(null)
  }

  const renderContext = (context, index) => {
    const x = 50 + (index % 3) * 150
    const y = 50 + Math.floor(index / 3) * 100
    const width = 120
    const height = 80
    
    // Determine context style based on polarity
    const isPositive = context.polarity === 'positive'
    const strokeColor = isPositive ? '#3b82f6' : '#ef4444'
    const fillColor = isPositive ? '#dbeafe' : '#fee2e2'
    const strokeWidth = context.depth === 0 ? 3 : 2
    
    return (
      <g key={context.id}>
        {/* Context boundary */}
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={fillColor}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={context.depth > 0 ? "5,5" : "none"}
          rx={8}
          className="cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => setSelectedItem({ type: 'context', id: context.id, data: context })}
        />
        
        {/* Context label */}
        <text
          x={x + 5}
          y={y + 15}
          fontSize="10"
          fill={strokeColor}
          className="font-mono"
        >
          {context.depth === 0 ? 'Root' : `Ctx-${context.depth}`}
        </text>
        
        {/* Polarity indicator */}
        <circle
          cx={x + width - 15}
          cy={y + 15}
          r={6}
          fill={isPositive ? '#10b981' : '#f59e0b'}
          className="opacity-70"
        />
        <text
          x={x + width - 15}
          y={y + 19}
          fontSize="8"
          fill="white"
          textAnchor="middle"
          className="font-bold"
        >
          {isPositive ? '+' : '-'}
        </text>
      </g>
    )
  }

  const renderNode = (node, index) => {
    const x = 80 + (index % 4) * 100
    const y = 200 + Math.floor(index / 4) * 60
    
    return (
      <g key={node.id}>
        {/* Node circle */}
        <circle
          cx={x}
          cy={y}
          r={20}
          fill="#f8fafc"
          stroke="#475569"
          strokeWidth={2}
          className="cursor-pointer hover:fill-blue-50 transition-colors"
          onClick={() => setSelectedItem({ type: 'node', id: node.id, data: node })}
        />
        
        {/* Node label */}
        <text
          x={x}
          y={y + 4}
          fontSize="10"
          textAnchor="middle"
          fill="#1e293b"
          className="font-semibold pointer-events-none"
        >
          {node.predicate || 'P'}
        </text>
        
        {/* Arity indicator */}
        {node.arity > 0 && (
          <text
            x={x + 15}
            y={y - 15}
            fontSize="8"
            fill="#64748b"
            className="font-mono"
          >
            {node.arity}
          </text>
        )}
      </g>
    )
  }

  const renderEdge = (edge, index) => {
    const x1 = 100 + (index % 3) * 120
    const y1 = 350
    const x2 = x1 + 80
    const y2 = y1
    
    return (
      <g key={edge.id}>
        {/* Edge line */}
        <line
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="#6366f1"
          strokeWidth={2}
          className="cursor-pointer hover:stroke-indigo-400 transition-colors"
          onClick={() => setSelectedItem({ type: 'edge', id: edge.id, data: edge })}
        />
        
        {/* Edge type indicator */}
        <rect
          x={x1 + 30}
          y={y1 - 8}
          width={20}
          height={16}
          fill="#6366f1"
          rx={4}
        />
        <text
          x={x1 + 40}
          y={y1 + 4}
          fontSize="8"
          textAnchor="middle"
          fill="white"
          className="font-bold pointer-events-none"
        >
          {edge.edge_type === 'cut' ? 'C' : 'E'}
        </text>
      </g>
    )
  }

  const renderLigature = (ligature, index) => {
    const startX = 120 + (index % 2) * 200
    const startY = 450
    const endX = startX + 100
    const endY = startY + 30
    
    return (
      <g key={ligature.id}>
        {/* Ligature path */}
        <path
          d={`M ${startX} ${startY} Q ${startX + 50} ${startY - 20} ${endX} ${endY}`}
          fill="none"
          stroke="#ec4899"
          strokeWidth={3}
          strokeDasharray="3,3"
          className="cursor-pointer hover:stroke-pink-400 transition-colors"
          onClick={() => setSelectedItem({ type: 'ligature', id: ligature.id, data: ligature })}
        />
        
        {/* Ligature endpoints */}
        <circle cx={startX} cy={startY} r={4} fill="#ec4899" />
        <circle cx={endX} cy={endY} r={4} fill="#ec4899" />
        
        {/* Ligature label */}
        <text
          x={startX + 50}
          y={startY - 30}
          fontSize="9"
          textAnchor="middle"
          fill="#be185d"
          className="font-semibold"
        >
          Identity
        </text>
      </g>
    )
  }

  const renderEmptyState = () => (
    <g>
      <rect
        x="50"
        y="50"
        width="400"
        height="300"
        fill="#f8fafc"
        stroke="#e2e8f0"
        strokeWidth="2"
        strokeDasharray="10,5"
        rx="8"
      />
      <text
        x="250"
        y="180"
        textAnchor="middle"
        fontSize="16"
        fill="#64748b"
        className="font-semibold"
      >
        Empty Sheet of Assertion
      </text>
      <text
        x="250"
        y="200"
        textAnchor="middle"
        fontSize="12"
        fill="#94a3b8"
      >
        Create a new graph or load an existing one
      </text>
      <Circle className="mx-auto" size={32} color="#cbd5e1" x="234" y="220" />
    </g>
  )

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b bg-slate-50">
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomIn}
            disabled={zoom >= 3}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomOut}
            disabled={zoom <= 0.3}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
          <Badge variant="secondary" className="text-xs font-mono">
            {Math.round(zoom * 100)}%
          </Badge>
        </div>
        
        {graph && (
          <div className="flex items-center space-x-2 text-sm text-slate-600">
            <span>Contexts: {graph.contexts?.length || 0}</span>
            <span>Nodes: {graph.nodes?.length || 0}</span>
            <span>Edges: {graph.edges?.length || 0}</span>
            <span>Ligatures: {graph.ligatures?.length || 0}</span>
          </div>
        )}
      </div>

      {/* SVG Canvas */}
      <div className="flex-1 overflow-hidden bg-white">
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="0 0 500 500"
          className="border-0"
          style={{
            transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
            transformOrigin: 'center center'
          }}
        >
          {/* Grid background */}
          <defs>
            <pattern
              id="grid"
              width="20"
              height="20"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 20 0 L 0 0 0 20"
                fill="none"
                stroke="#f1f5f9"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Render graph elements */}
          {graph ? (
            <>
              {/* Contexts */}
              {graph.contexts?.map((context, index) => renderContext(context, index))}
              
              {/* Nodes */}
              {graph.nodes?.map((node, index) => renderNode(node, index))}
              
              {/* Edges */}
              {graph.edges?.map((edge, index) => renderEdge(edge, index))}
              
              {/* Ligatures */}
              {graph.ligatures?.map((ligature, index) => renderLigature(ligature, index))}
            </>
          ) : (
            renderEmptyState()
          )}
        </svg>
      </div>

      {/* Selection Info */}
      {selectedItem && (
        <div className="p-3 border-t bg-slate-50">
          <div className="flex items-center justify-between">
            <div>
              <Badge variant="outline" className="mb-1">
                {selectedItem.type}
              </Badge>
              <p className="text-sm font-mono text-slate-600">
                ID: {selectedItem.id.slice(0, 8)}...
              </p>
              {selectedItem.data.predicate && (
                <p className="text-sm text-slate-700">
                  Predicate: {selectedItem.data.predicate}
                </p>
              )}
              {selectedItem.data.polarity && (
                <p className="text-sm text-slate-700">
                  Polarity: {selectedItem.data.polarity}
                </p>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedItem(null)}
            >
              ×
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default GraphVisualization

