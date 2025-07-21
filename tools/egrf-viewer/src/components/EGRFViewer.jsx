import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, Download, Eye, FileText, Zap } from 'lucide-react';

// Import example files directly
import simpleExampleData from '../assets/simple_example.egrf?raw';
import complexExampleData from '../assets/complex_example.egrf?raw';
import simpleCorrectedData from '../assets/simple_corrected.egrf?raw';
import complexCorrectedData from '../assets/complex_corrected.egrf?raw';
import simpleProperlyCorrectedData from '../assets/simple_properly_corrected.egrf?raw';
import simpleAlignedData from '../assets/simple_aligned_connections.egrf?raw';
import generatedData from '../assets/generated_from_eg_cl_manus2.egrf?raw';

const EGRFViewer = () => {
  const [egrfData, setEgrfData] = useState(null);
  const [error, setError] = useState(null);
  const [selectedExample, setSelectedExample] = useState(null);
  const fileInputRef = useRef(null);

  const loadExample = (exampleName) => {
    try {
      let data;
      if (exampleName === 'simple') {
        data = JSON.parse(simpleExampleData);
        setSelectedExample('simple_example.egrf');
      } else if (exampleName === 'complex') {
        data = JSON.parse(complexExampleData);
        setSelectedExample('complex_example.egrf');
      } else if (exampleName === 'simple_corrected') {
        data = JSON.parse(simpleCorrectedData);
        setSelectedExample('simple_corrected.egrf');
      } else if (exampleName === 'complex_corrected') {
        data = JSON.parse(complexCorrectedData);
        setSelectedExample('complex_corrected.egrf');
      } else if (exampleName === 'simple_properly_corrected') {
        data = JSON.parse(simpleProperlyCorrectedData);
        setSelectedExample('simple_properly_corrected.egrf');
      } else if (exampleName === 'simple_aligned') {
        data = JSON.parse(simpleAlignedData);
        setSelectedExample('simple_aligned_connections.egrf');
      } else if (exampleName === 'generated') {
        data = JSON.parse(generatedData);
        setSelectedExample('generated_from_eg_cl_manus2.egrf');
      }
      
      setEgrfData(data);
      setError(null);
    } catch (err) {
      setError(`Failed to load example: ${err.message}`);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          setEgrfData(data);
          setSelectedExample(file.name);
          setError(null);
        } catch (err) {
          setError(`Invalid EGRF file: ${err.message}`);
        }
      };
      reader.readAsText(file);
    }
  };

  const downloadSVG = () => {
    if (!egrfData) return;
    
    const svgElement = document.getElementById('egrf-svg');
    const svgData = new XMLSerializer().serializeToString(svgElement);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    
    const downloadLink = document.createElement('a');
    downloadLink.href = svgUrl;
    downloadLink.download = `${egrfData.metadata?.title || 'egrf-graph'}.svg`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(svgUrl);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">EGRF Viewer</h1>
          <p className="text-muted-foreground text-lg">
            Existential Graph Rendering Format - Visual demonstration of Peirce's logical notation
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Control Panel */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Load EGRF File
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Example Files</h3>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => loadExample('simple')}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Simple: Socrates is Mortal
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => loadExample('complex')}
                    >
                      <Zap className="w-4 h-4 mr-2" />
                      Complex: Nested Contexts
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">Corrected Examples (Proper Ligatures)</h3>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      className="w-full justify-start bg-green-50 border-green-200 hover:bg-green-100"
                      onClick={() => loadExample('simple_aligned')}
                    >
                      <Eye className="w-4 h-4 mr-2 text-green-600" />
                      ✓ Simple: Aligned Connections
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start bg-green-50 border-green-200 hover:bg-green-100"
                      onClick={() => loadExample('complex_corrected')}
                    >
                      <Eye className="w-4 h-4 mr-2 text-green-600" />
                      ✓ Complex: With Ligatures
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">Generated from EG-CL-Manus2</h3>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      className="w-full justify-start bg-blue-50 border-blue-200 hover:bg-blue-100"
                      onClick={() => loadExample('generated')}
                    >
                      <Zap className="w-4 h-4 mr-2 text-blue-600" />
                      🔄 Auto-Generated Example
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">Upload Custom File</h3>
                  <input
                    type="file"
                    accept=".egrf,.json"
                    onChange={handleFileUpload}
                    ref={fileInputRef}
                    className="hidden"
                  />
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload EGRF File
                  </Button>
                </div>

                {egrfData && (
                  <div className="border-t pt-4">
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={downloadSVG}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download as SVG
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Metadata Panel */}
            {egrfData && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Graph Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div><strong>Title:</strong> {egrfData.metadata?.title || 'Untitled'}</div>
                    <div><strong>Format:</strong> {egrfData.format} v{egrfData.version}</div>
                    <div><strong>Entities:</strong> {egrfData.entities?.length || 0}</div>
                    <div><strong>Predicates:</strong> {egrfData.predicates?.length || 0}</div>
                    <div><strong>Contexts:</strong> {egrfData.contexts?.length || 0}</div>
                    {egrfData.semantics?.logical_form?.clif_equivalent && (
                      <div className="mt-4">
                        <strong>CLIF:</strong>
                        <code className="block mt-1 p-2 bg-muted rounded text-xs">
                          {egrfData.semantics.logical_form.clif_equivalent}
                        </code>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Visualization Panel */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Visual Representation</CardTitle>
              </CardHeader>
              <CardContent>
                {error && (
                  <div className="bg-destructive/10 border border-destructive/20 rounded p-4 mb-4">
                    <p className="text-destructive">{error}</p>
                  </div>
                )}

                {!egrfData && !error && (
                  <div className="flex items-center justify-center h-96 bg-muted/20 rounded border-2 border-dashed">
                    <div className="text-center">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-muted-foreground">
                        Load an EGRF file to see the visual representation
                      </p>
                    </div>
                  </div>
                )}

                {egrfData && (
                  <div className="border rounded p-4 bg-white">
                    <EGRFRenderer data={egrfData} />
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

const EGRFRenderer = ({ data }) => {
  if (!data) return null;

  const canvas = data.canvas || { width: 800, height: 600 };
  const entities = data.entities || [];
  const predicates = data.predicates || [];
  const contexts = data.contexts || [];
  const ligatures = data.ligatures || [];

  return (
    <svg
      id="egrf-svg"
      width={canvas.width}
      height={canvas.height}
      viewBox={`0 0 ${canvas.width} ${canvas.height}`}
      className="border"
      style={{ backgroundColor: canvas.background || '#ffffff' }}
    >
      {/* Grid */}
      {canvas.grid?.enabled && (
        <defs>
          <pattern
            id="grid"
            width={canvas.grid.size || 20}
            height={canvas.grid.size || 20}
            patternUnits="userSpaceOnUse"
          >
            <path
              d={`M ${canvas.grid.size || 20} 0 L 0 0 0 ${canvas.grid.size || 20}`}
              fill="none"
              stroke={canvas.grid.color || '#f0f0f0'}
              strokeWidth="1"
            />
          </pattern>
        </defs>
      )}
      
      {canvas.grid?.enabled && (
        <rect width="100%" height="100%" fill="url(#grid)" />
      )}

      {/* Render contexts (cuts) first so they appear behind other elements */}
      {contexts
        .filter(ctx => ctx.visual && ctx.type !== 'root' && ctx.type !== 'sheet_of_assertion')
        .map(context => (
          <g key={context.id}>
            <ellipse
              cx={context.visual.bounds.x + context.visual.bounds.width / 2}
              cy={context.visual.bounds.y + context.visual.bounds.height / 2}
              rx={context.visual.bounds.width / 2}
              ry={context.visual.bounds.height / 2}
              fill={context.visual.fill?.color || '#f0f0f0'}
              fillOpacity={context.visual.fill?.opacity || 0.3}
              stroke={context.visual.stroke?.color || '#666666'}
              strokeWidth={context.visual.stroke?.width || 2}
              strokeDasharray={context.visual.stroke?.style === 'dashed' ? '5,5' : 'none'}
            />
          </g>
        ))}

      {/* Render entities (lines of identity) */}
      {entities.map(entity => (
        <g key={entity.id}>
          {entity.visual?.path && entity.visual.path.length > 1 && (
            <polyline
              points={entity.visual.path.map(p => `${p.x},${p.y}`).join(' ')}
              fill="none"
              stroke={entity.visual.stroke?.color || '#000000'}
              strokeWidth={entity.visual.stroke?.width || 3}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray={entity.visual.stroke?.style === 'dashed' ? '5,5' : 'none'}
            />
          )}
          
          {/* Entity labels */}
          {entity.labels?.map((label, idx) => (
            <text
              key={idx}
              x={label.position.x}
              y={label.position.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={label.font?.size || 12}
              fontFamily={label.font?.family || 'Arial'}
              fontWeight={label.font?.weight || 'normal'}
              fill={label.font?.color || '#000000'}
              style={{ userSelect: 'none' }}
            >
              {label.text}
            </text>
          ))}
        </g>
      ))}

      {/* Render predicates */}
      {predicates.map(predicate => (
        <g key={predicate.id}>
          <ellipse
            cx={predicate.visual?.position?.x || 0}
            cy={predicate.visual?.position?.y || 0}
            rx={(predicate.visual?.size?.width || 60) / 2}
            ry={(predicate.visual?.size?.height || 30) / 2}
            fill={predicate.visual?.fill?.color || '#ffffff'}
            fillOpacity={predicate.visual?.fill?.opacity || 1}
            stroke={predicate.visual?.stroke?.color || '#000000'}
            strokeWidth={predicate.visual?.stroke?.width || 2}
          />
          
          {/* Predicate labels */}
          {predicate.labels?.map((label, idx) => (
            <text
              key={idx}
              x={label.position.x}
              y={label.position.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={label.font?.size || 12}
              fontFamily={label.font?.family || 'Arial'}
              fontWeight={label.font?.weight || 'normal'}
              fill={label.font?.color || '#000000'}
              style={{ userSelect: 'none' }}
            >
              {label.text}
            </text>
          ))}

          {/* Connection points - show where entities connect to predicates */}
          {predicate.connections?.map((conn, idx) => (
            <g key={idx}>
              {/* Small circle to mark connection point */}
              <circle
                cx={conn.connection_point.x}
                cy={conn.connection_point.y}
                r="3"
                fill={conn.style?.stroke?.color || '#000000'}
                stroke="#ffffff"
                strokeWidth="1"
              />
            </g>
          ))}
        </g>
      ))}

      {/* Render ligatures (identity connections between entities) */}
      {ligatures.map(ligature => (
        <g key={ligature.id}>
          {ligature.visual?.path && ligature.visual.path.length > 1 && (
            <polyline
              points={ligature.visual.path.map(p => `${p.x},${p.y}`).join(' ')}
              fill="none"
              stroke={ligature.visual.stroke?.color || '#0066cc'}
              strokeWidth={ligature.visual.stroke?.width || 2}
              strokeDasharray="3,3"
              strokeLinecap="round"
            />
          )}
          
          {/* Ligature markers */}
          {ligature.visual?.markers && (
            <>
              {/* Start marker */}
              {ligature.visual.path && ligature.visual.path.length > 0 && (
                <circle
                  cx={ligature.visual.path[0].x}
                  cy={ligature.visual.path[0].y}
                  r={ligature.visual.markers.start?.size || 3}
                  fill={ligature.visual.stroke?.color || '#0066cc'}
                />
              )}
              {/* End marker */}
              {ligature.visual.path && ligature.visual.path.length > 1 && (
                <circle
                  cx={ligature.visual.path[ligature.visual.path.length - 1].x}
                  cy={ligature.visual.path[ligature.visual.path.length - 1].y}
                  r={ligature.visual.markers.end?.size || 3}
                  fill={ligature.visual.stroke?.color || '#0066cc'}
                />
              )}
            </>
          )}
        </g>
      ))}
    </svg>
  );
};

export default EGRFViewer;

