import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Label } from '@/components/ui/label.jsx'
import { 
  Search, 
  Layers, 
  Focus, 
  Eye, 
  Target,
  Compass,
  Map,
  ZoomIn
} from 'lucide-react'

const API_BASE = '/api/eg'

const ExplorationTool = ({ graphId, currentGraph, onError }) => {
  const [scopeType, setScopeType] = useState('area_only')
  const [focusItemId, setFocusItemId] = useState('')
  const [explorationResult, setExplorationResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const exploreGraph = async () => {
    if (!graphId) {
      onError('No graph selected')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/exploration/${graphId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scope_type: scopeType,
          focus_item_id: focusItemId || undefined
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setExplorationResult(data.view)
        onError(null)
      } else {
        const errorData = await response.json()
        onError(`Exploration failed: ${errorData.error}`)
      }
    } catch (err) {
      onError(`Network error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const getAvailableItems = () => {
    if (!currentGraph) return []
    
    const items = []
    
    // Add contexts
    if (currentGraph.contexts) {
      currentGraph.contexts.forEach(ctx => {
        items.push({
          id: ctx.id,
          type: 'context',
          label: `Context (depth ${ctx.depth})`
        })
      })
    }
    
    // Add nodes
    if (currentGraph.nodes) {
      currentGraph.nodes.forEach(node => {
        items.push({
          id: node.id,
          type: 'node',
          label: `Node: ${node.predicate || 'Unnamed'}`
        })
      })
    }
    
    // Add edges
    if (currentGraph.edges) {
      currentGraph.edges.forEach(edge => {
        items.push({
          id: edge.id,
          type: 'edge',
          label: `Edge: ${edge.edge_type}`
        })
      })
    }
    
    // Add ligatures
    if (currentGraph.ligatures) {
      currentGraph.ligatures.forEach(lig => {
        items.push({
          id: lig.id,
          type: 'ligature',
          label: 'Ligature'
        })
      })
    }
    
    return items
  }

  const getScopeDescription = (scope) => {
    switch (scope) {
      case 'area_only':
        return 'Show only objects in the focused area'
      case 'context_complete':
        return 'Show all nested content (zoom all the way in)'
      case 'level_limited':
        return 'Show 1-3 levels down (graduated zoom)'
      case 'containing':
        return 'Show containing contexts (zoom out)'
      default:
        return 'Unknown scope type'
    }
  }

  const getItemTypeIcon = (type) => {
    switch (type) {
      case 'context': return <Layers className="h-3 w-3" />
      case 'node': return <Target className="h-3 w-3" />
      case 'edge': return <Focus className="h-3 w-3" />
      case 'ligature': return <Compass className="h-3 w-3" />
      default: return <Search className="h-3 w-3" />
    }
  }

  const availableItems = getAvailableItems()

  return (
    <div className="space-y-4">
      {/* Scope Selection */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Eye className="h-4 w-4" />
            <span>Exploration Scope</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Choose how much of the graph to examine
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="scope-type" className="text-xs">Scope Type</Label>
            <Select value={scopeType} onValueChange={setScopeType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="area_only">Area Only</SelectItem>
                <SelectItem value="context_complete">Context Complete</SelectItem>
                <SelectItem value="level_limited">Level Limited</SelectItem>
                <SelectItem value="containing">Containing</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="text-xs text-slate-600 p-2 bg-slate-50 rounded">
            {getScopeDescription(scopeType)}
          </div>
        </CardContent>
      </Card>

      {/* Focus Selection */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Target className="h-4 w-4" />
            <span>Focus Item</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Select an item to focus exploration on
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="focus-item" className="text-xs">Focus Item (Optional)</Label>
            <Select value={focusItemId} onValueChange={setFocusItemId}>
              <SelectTrigger>
                <SelectValue placeholder="Select item to focus on..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No focus (full view)</SelectItem>
                {availableItems.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    <div className="flex items-center space-x-2">
                      {getItemTypeIcon(item.type)}
                      <span>{item.label}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {availableItems.length === 0 && (
            <div className="text-xs text-slate-500 text-center py-2">
              No items available for focus
            </div>
          )}
        </CardContent>
      </Card>

      {/* Explore Button */}
      <Button 
        onClick={exploreGraph}
        disabled={isLoading || !graphId}
        className="w-full"
      >
        <Search className="h-4 w-4 mr-2" />
        {isLoading ? 'Exploring...' : 'Explore Graph'}
      </Button>

      {/* Exploration Results */}
      {explorationResult && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center space-x-2">
              <Map className="h-4 w-4" />
              <span>Exploration Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <Label className="text-xs text-slate-600">Scope Type</Label>
                <Badge variant="outline" className="text-xs">
                  {explorationResult.scope_type}
                </Badge>
              </div>
              
              {explorationResult.focus_item && (
                <div>
                  <Label className="text-xs text-slate-600">Focus Item</Label>
                  <Badge variant="secondary" className="text-xs font-mono">
                    {explorationResult.focus_item.slice(0, 8)}...
                  </Badge>
                </div>
              )}
            </div>
            
            <div className="space-y-2">
              <Label className="text-xs text-slate-600">Visible Items</Label>
              <div className="max-h-32 overflow-y-auto">
                {explorationResult.visible_items && explorationResult.visible_items.length > 0 ? (
                  <div className="space-y-1">
                    {explorationResult.visible_items.map((itemId, index) => (
                      <Badge 
                        key={itemId} 
                        variant="outline" 
                        className="text-xs font-mono mr-1 mb-1"
                      >
                        {itemId.slice(0, 8)}...
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 text-center py-2">
                    No visible items
                  </div>
                )}
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-xs text-slate-600">Context Hierarchy</Label>
              <div className="max-h-24 overflow-y-auto">
                {explorationResult.context_hierarchy && explorationResult.context_hierarchy.length > 0 ? (
                  <div className="space-y-1">
                    {explorationResult.context_hierarchy.map((contextId, index) => (
                      <div key={contextId} className="flex items-center space-x-2 text-xs">
                        <span className="text-slate-500">Level {index}:</span>
                        <Badge variant="secondary" className="text-xs font-mono">
                          {contextId.slice(0, 8)}...
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 text-center py-2">
                    No context hierarchy
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Quick Exploration</CardTitle>
          <CardDescription className="text-xs">
            Common exploration patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs justify-start"
              onClick={() => {
                setScopeType('area_only')
                setFocusItemId('')
              }}
            >
              <ZoomIn className="h-3 w-3 mr-2" />
              Full Overview
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs justify-start"
              onClick={() => {
                setScopeType('context_complete')
                setFocusItemId('')
              }}
            >
              <Layers className="h-3 w-3 mr-2" />
              Deep Dive
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs justify-start"
              onClick={() => {
                setScopeType('containing')
                setFocusItemId('')
              }}
            >
              <Compass className="h-3 w-3 mr-2" />
              Zoom Out
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Status */}
      {graphId && (
        <div className="text-center">
          <Badge variant="secondary" className="text-xs font-mono">
            Exploring: {graphId.slice(0, 8)}...
          </Badge>
        </div>
      )}
    </div>
  )
}

export default ExplorationTool

