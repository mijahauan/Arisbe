import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Label } from '@/components/ui/label.jsx'
import { 
  Users, 
  Play, 
  Square, 
  RotateCcw, 
  Crown,
  Shield,
  Swords,
  Trophy,
  Clock,
  Target
} from 'lucide-react'

const API_BASE = '/api/eg'

const GameInterface = ({ graphId, currentGraph, onError }) => {
  const [gameId, setGameId] = useState(null)
  const [gameState, setGameState] = useState('WAITING_FOR_THESIS')
  const [currentPlayer, setCurrentPlayer] = useState(null)
  const [domainModel, setDomainModel] = useState('default')
  const [isLoading, setIsLoading] = useState(false)
  const [gameHistory, setGameHistory] = useState([])

  const createGame = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/games`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain_model_name: domainModel })
      })
      
      if (response.ok) {
        const data = await response.json()
        setGameId(data.game_id)
        setGameState(data.state)
        setGameHistory([])
        onError(null)
      } else {
        const errorData = await response.json()
        onError(`Failed to create game: ${errorData.error}`)
      }
    } catch (err) {
      onError(`Network error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const startInning = async () => {
    if (!gameId || !graphId) {
      onError('Game and thesis graph required')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/games/${gameId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thesis_graph_id: graphId })
      })
      
      if (response.ok) {
        const data = await response.json()
        setGameState(data.state)
        setCurrentPlayer(data.current_player)
        setGameHistory(prev => [...prev, {
          action: 'start_inning',
          player: 'PROPOSER',
          timestamp: new Date().toISOString(),
          details: 'Inning started with thesis'
        }])
        onError(null)
      } else {
        const errorData = await response.json()
        onError(`Failed to start inning: ${errorData.error}`)
      }
    } catch (err) {
      onError(`Network error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const getStateDescription = (state) => {
    switch (state) {
      case 'WAITING_FOR_THESIS':
        return 'Waiting for a thesis to be proposed'
      case 'INNING_IN_PROGRESS':
        return 'Game inning is in progress'
      case 'PROPOSER_WINS':
        return 'Proposer has won the inning'
      case 'SKEPTIC_WINS':
        return 'Skeptic has won the inning'
      case 'DRAW_AND_EXTEND':
        return 'Draw and extend the domain model'
      default:
        return 'Unknown game state'
    }
  }

  const getPlayerIcon = (player) => {
    switch (player) {
      case 'PROPOSER': return <Crown className="h-4 w-4" />
      case 'SKEPTIC': return <Shield className="h-4 w-4" />
      default: return <Users className="h-4 w-4" />
    }
  }

  const getStateColor = (state) => {
    switch (state) {
      case 'WAITING_FOR_THESIS': return 'bg-yellow-500'
      case 'INNING_IN_PROGRESS': return 'bg-blue-500'
      case 'PROPOSER_WINS': return 'bg-green-500'
      case 'SKEPTIC_WINS': return 'bg-red-500'
      case 'DRAW_AND_EXTEND': return 'bg-purple-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-4">
      {/* Game Status */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Swords className="h-4 w-4" />
            <span>Endoporeutic Game</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Two-player logical validation game
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {gameId ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="text-xs font-mono">
                  Game: {gameId.slice(0, 8)}...
                </Badge>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${getStateColor(gameState)}`} />
                  <span className="text-xs text-slate-600">{gameState}</span>
                </div>
              </div>
              
              <div className="text-xs text-slate-600 p-2 bg-slate-50 rounded">
                {getStateDescription(gameState)}
              </div>
              
              {currentPlayer && (
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-slate-600">Current Player:</Label>
                  <Badge variant="secondary" className="text-xs">
                    <div className="flex items-center space-x-1">
                      {getPlayerIcon(currentPlayer)}
                      <span>{currentPlayer}</span>
                    </div>
                  </Badge>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-4 text-slate-500">
              <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No active game</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Game Controls */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Play className="h-4 w-4" />
            <span>Game Controls</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {!gameId ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="domain-model" className="text-xs">Domain Model</Label>
                <Select value={domainModel} onValueChange={setDomainModel}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default Model</SelectItem>
                    <SelectItem value="mathematics">Mathematics</SelectItem>
                    <SelectItem value="philosophy">Philosophy</SelectItem>
                    <SelectItem value="logic">Logic</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Button 
                onClick={createGame}
                disabled={isLoading}
                className="w-full"
              >
                <Play className="h-4 w-4 mr-2" />
                {isLoading ? 'Creating...' : 'Create New Game'}
              </Button>
            </>
          ) : (
            <div className="space-y-2">
              {gameState === 'WAITING_FOR_THESIS' && (
                <Button 
                  onClick={startInning}
                  disabled={isLoading || !graphId}
                  className="w-full"
                >
                  <Target className="h-4 w-4 mr-2" />
                  {isLoading ? 'Starting...' : 'Start Inning with Current Graph'}
                </Button>
              )}
              
              <Button 
                onClick={() => {
                  setGameId(null)
                  setGameState('WAITING_FOR_THESIS')
                  setCurrentPlayer(null)
                  setGameHistory([])
                }}
                variant="outline"
                size="sm"
                className="w-full"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset Game
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Game Rules */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Trophy className="h-4 w-4" />
            <span>Game Rules</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex items-start space-x-2">
              <Crown className="h-3 w-3 mt-0.5 text-yellow-600" />
              <div>
                <span className="font-semibold">Proposer:</span> Proposes a thesis graph and defends its validity
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <Shield className="h-3 w-3 mt-0.5 text-blue-600" />
              <div>
                <span className="font-semibold">Skeptic:</span> Challenges the thesis by finding counterexamples
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <Swords className="h-3 w-3 mt-0.5 text-red-600" />
              <div>
                <span className="font-semibold">Goal:</span> Determine if the thesis can be integrated into the domain model
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Game History */}
      {gameHistory.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center space-x-2">
              <Clock className="h-4 w-4" />
              <span>Game History</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-32 overflow-y-auto space-y-2">
              {gameHistory.map((entry, index) => (
                <div key={index} className="flex items-center space-x-2 text-xs">
                  {getPlayerIcon(entry.player)}
                  <span className="text-slate-600">{entry.details}</span>
                  <Badge variant="outline" className="text-xs">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status */}
      {!graphId && gameState === 'WAITING_FOR_THESIS' && (
        <Alert>
          <AlertDescription className="text-xs">
            Create or load a graph to use as a thesis for the game
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default GameInterface

