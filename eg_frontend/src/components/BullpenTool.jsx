import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { 
  FileText, 
  Plus, 
  Target, 
  Code, 
  CheckCircle, 
  AlertCircle,
  Sparkles,
  Layers
} from 'lucide-react'

const API_BASE = '/api/eg'

const BullpenTool = ({ graphId, onGraphUpdate, onError }) => {
  const [clifText, setClifText] = useState('')
  const [templateName, setTemplateName] = useState('')
  const [predicateName, setPredicateName] = useState('')
  const [predicateArity, setPredicateArity] = useState('1')
  const [isLoading, setIsLoading] = useState(false)
  const [validationResult, setValidationResult] = useState(null)

  const createBlankSheet = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/bullpen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      
      if (response.ok) {
        const data = await response.json()
        onGraphUpdate(data.graph)
        setValidationResult({ success: true, message: 'Blank sheet created successfully' })
        onError(null)
      } else {
        const errorData = await response.json()
        onError(`Failed to create blank sheet: ${errorData.error}`)
      }
    } catch (err) {
      onError(`Network error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const createFromTemplate = async () => {
    if (!templateName.trim()) {
      onError('Please enter a template name')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/bullpen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_name: templateName })
      })
      
      if (response.ok) {
        const data = await response.json()
        onGraphUpdate(data.graph)
        setValidationResult({ success: true, message: `Template "${templateName}" applied successfully` })
        onError(null)
      } else {
        const errorData = await response.json()
        onError(`Failed to create from template: ${errorData.error}`)
      }
    } catch (err) {
      onError(`Network error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const parseClif = async () => {
    if (!graphId) {
      onError('No graph selected. Create a new graph first.')
      return
    }

    if (!clifText.trim()) {
      onError('Please enter CLIF text to parse')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/graphs/${graphId}/clif`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clif_text: clifText })
      })
      
      if (response.ok) {
        const data = await response.json()
        onGraphUpdate(data.graph)
        setValidationResult({ success: true, message: 'CLIF parsed successfully' })
        onError(null)
      } else {
        const errorData = await response.json()
        onError(`CLIF parsing failed: ${errorData.error}`)
        setValidationResult({ success: false, message: errorData.error })
      }
    } catch (err) {
      onError(`Network error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const generateClif = async () => {
    if (!graphId) {
      onError('No graph selected')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/graphs/${graphId}/clif`)
      
      if (response.ok) {
        const data = await response.json()
        setClifText(data.clif_text)
        setValidationResult({ success: true, message: 'CLIF generated successfully' })
        onError(null)
      } else {
        const errorData = await response.json()
        onError(`CLIF generation failed: ${errorData.error}`)
      }
    } catch (err) {
      onError(`Network error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const addPredicate = async () => {
    if (!graphId) {
      onError('No graph selected')
      return
    }

    if (!predicateName.trim()) {
      onError('Please enter a predicate name')
      return
    }

    // This would need to be implemented in the backend
    onError('Add predicate functionality not yet implemented in backend')
  }

  return (
    <div className="space-y-4">
      {/* Validation Result */}
      {validationResult && (
        <Alert variant={validationResult.success ? "default" : "destructive"}>
          <div className="flex items-center space-x-2">
            {validationResult.success ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <AlertDescription>{validationResult.message}</AlertDescription>
          </div>
        </Alert>
      )}

      {/* Quick Start */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Sparkles className="h-4 w-4" />
            <span>Quick Start</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button 
            onClick={createBlankSheet}
            disabled={isLoading}
            className="w-full"
            variant="outline"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Blank Sheet
          </Button>
          
          <div className="flex space-x-2">
            <Input
              placeholder="Template name"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              className="flex-1"
            />
            <Button 
              onClick={createFromTemplate}
              disabled={isLoading || !templateName.trim()}
              size="sm"
            >
              <Target className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* CLIF Integration */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Code className="h-4 w-4" />
            <span>CLIF Integration</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Parse CLIF text or generate from current graph
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            placeholder="Enter CLIF text here..."
            value={clifText}
            onChange={(e) => setClifText(e.target.value)}
            rows={4}
            className="font-mono text-sm"
          />
          
          <div className="flex space-x-2">
            <Button 
              onClick={parseClif}
              disabled={isLoading || !clifText.trim() || !graphId}
              size="sm"
              className="flex-1"
            >
              <FileText className="h-4 w-4 mr-2" />
              Parse CLIF
            </Button>
            <Button 
              onClick={generateClif}
              disabled={isLoading || !graphId}
              size="sm"
              variant="outline"
              className="flex-1"
            >
              Generate CLIF
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Manual Composition */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center space-x-2">
            <Layers className="h-4 w-4" />
            <span>Manual Composition</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Add individual elements to the graph
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="predicate-name" className="text-xs">Predicate Name</Label>
            <Input
              id="predicate-name"
              placeholder="e.g., Person, Loves"
              value={predicateName}
              onChange={(e) => setPredicateName(e.target.value)}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="predicate-arity" className="text-xs">Arity</Label>
            <Select value={predicateArity} onValueChange={setPredicateArity}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">0 (Proposition)</SelectItem>
                <SelectItem value="1">1 (Unary)</SelectItem>
                <SelectItem value="2">2 (Binary)</SelectItem>
                <SelectItem value="3">3 (Ternary)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Button 
            onClick={addPredicate}
            disabled={isLoading || !predicateName.trim() || !graphId}
            size="sm"
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Predicate
          </Button>
        </CardContent>
      </Card>

      {/* Templates */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Available Templates</CardTitle>
          <CardDescription className="text-xs">
            Common logical patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {[
              'universal_quantification',
              'existential_quantification', 
              'implication',
              'disjunction',
              'conjunction',
              'negation'
            ].map((template) => (
              <Button
                key={template}
                variant="ghost"
                size="sm"
                className="text-xs justify-start"
                onClick={() => setTemplateName(template)}
              >
                {template.replace('_', ' ')}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Status */}
      {graphId && (
        <div className="text-center">
          <Badge variant="secondary" className="text-xs font-mono">
            Working on: {graphId.slice(0, 8)}...
          </Badge>
        </div>
      )}
    </div>
  )
}

export default BullpenTool

