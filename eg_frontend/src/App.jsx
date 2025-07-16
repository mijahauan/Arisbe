import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  Play, 
  Square, 
  RotateCcw, 
  Eye, 
  Zap, 
  Search, 
  FileText, 
  Settings,
  Users,
  Brain,
  Target,
  Layers
} from 'lucide-react'
import GraphVisualization from './components/GraphVisualization.jsx'
import GameInterface from './components/GameInterface.jsx'
import BullpenTool from './components/BullpenTool.jsx'
import ExplorationTool from './components/ExplorationTool.jsx'
import './App.css'

const API_BASE = '/api/eg'

function App() {
  const [activeTab, setActiveTab] = useState('bullpen')
  const [currentGraph, setCurrentGraph] = useState(null)
  const [graphId, setGraphId] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [error, setError] = useState(null)

  // Test backend connection on startup
  useEffect(() => {
    testConnection()
  }, [])

  const testConnection = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`)
      if (response.ok) {
        setConnectionStatus('connected')
        setError(null)
      } else {
        setConnectionStatus('error')
        setError('Backend connection failed')
      }
    } catch (err) {
      setConnectionStatus('error')
      setError(`Connection error: ${err.message}`)
    }
  }

  const createNewGraph = async () => {
    try {
      const response = await fetch(`${API_BASE}/graphs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        const data = await response.json()
        setGraphId(data.graph_id)
        setCurrentGraph(data.graph)
        setError(null)
      } else {
        const errorData = await response.json()
        setError(`Failed to create graph: ${errorData.error}`)
      }
    } catch (err) {
      setError(`Network error: ${err.message}`)
    }
  }

  const loadGraph = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/graphs/${id}`)
      
      if (response.ok) {
        const data = await response.json()
        setGraphId(id)
        setCurrentGraph(data.graph)
        setError(null)
      } else {
        const errorData = await response.json()
        setError(`Failed to load graph: ${errorData.error}`)
      }
    } catch (err) {
      setError(`Network error: ${err.message}`)
    }
  }

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-yellow-500'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Brain className="h-8 w-8 text-blue-600" />
                <h1 className="text-2xl font-bold text-slate-900">
                  Existential Graphs
                </h1>
              </div>
              <Badge variant="outline" className="text-xs">
                Phase 5B
              </Badge>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${getConnectionStatusColor()}`} />
                <span className="text-sm text-slate-600 capitalize">
                  {connectionStatus}
                </span>
              </div>
              
              {/* Graph Info */}
              {graphId && (
                <Badge variant="secondary" className="font-mono text-xs">
                  Graph: {graphId.slice(0, 8)}...
                </Badge>
              )}
              
              <Button 
                onClick={createNewGraph}
                size="sm"
                className="bg-blue-600 hover:bg-blue-700"
              >
                New Graph
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Panel - Tools */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>Tools & Operations</span>
                </CardTitle>
                <CardDescription>
                  Create, explore, and transform existential graphs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="bullpen" className="text-xs">
                      <Target className="h-4 w-4" />
                    </TabsTrigger>
                    <TabsTrigger value="exploration" className="text-xs">
                      <Search className="h-4 w-4" />
                    </TabsTrigger>
                    <TabsTrigger value="lookahead" className="text-xs">
                      <Eye className="h-4 w-4" />
                    </TabsTrigger>
                    <TabsTrigger value="game" className="text-xs">
                      <Users className="h-4 w-4" />
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="bullpen" className="mt-4">
                    <BullpenTool 
                      graphId={graphId}
                      onGraphUpdate={setCurrentGraph}
                      onError={setError}
                    />
                  </TabsContent>
                  
                  <TabsContent value="exploration" className="mt-4">
                    <ExplorationTool 
                      graphId={graphId}
                      currentGraph={currentGraph}
                      onError={setError}
                    />
                  </TabsContent>
                  
                  <TabsContent value="lookahead" className="mt-4">
                    <div className="space-y-4">
                      <div className="text-center py-8 text-slate-500">
                        <Zap className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>Look Ahead Tool</p>
                        <p className="text-sm">Preview transformations</p>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="game" className="mt-4">
                    <GameInterface 
                      graphId={graphId}
                      currentGraph={currentGraph}
                      onError={setError}
                    />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
          
          {/* Right Panel - Visualization */}
          <div className="lg:col-span-2">
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Layers className="h-5 w-5" />
                  <span>Graph Visualization</span>
                </CardTitle>
                <CardDescription>
                  Interactive existential graph display
                </CardDescription>
              </CardHeader>
              <CardContent className="h-96">
                <GraphVisualization 
                  graph={currentGraph}
                  graphId={graphId}
                  onGraphUpdate={setCurrentGraph}
                  onError={setError}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App

