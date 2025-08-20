# EGI ↔ NetworkX-Qt Pipeline Flow

## Complete Bidirectional Architecture

### Forward Flow: EGI → Canonical EG Drawing

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EGI           │    │   NetworkX      │    │   Qt Scene      │    │   Canonical     │
│   Mathematical  │───▶│   Global Graph  │───▶│   Containment   │───▶│   EG Drawing    │
│   Structure     │    │   + Layout      │    │   Tree          │    │   (Visual)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Reverse Flow: Visual Interaction → EGI

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User          │    │   Qt Event      │    │   EGI           │    │   Re-render     │
│   Interaction   │───▶│   System        │───▶│   Operations    │───▶│   Pipeline      │
│   (Drag/Edit)   │    │   (Capture)     │    │   (Transform)   │    │   (Update)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Detailed Step-by-Step Flow

### 1. EGI → NetworkX Global Graph

**Input**: `RelationalGraphWithCuts` (EGI)
- Vertices: `egi.V` (quantifiers, constants)
- Predicates: `egi.E` (relations)
- Ligatures: `egi.nu` (ν mapping - argument connections)
- Cuts: `egi.Cut` (logical areas/contexts)

**Process**: `NetworkXQtLayoutEngine._create_networkx_layouts()`
```python
# Create single global NetworkX graph
G = nx.Graph()

# Add all vertices and predicates as nodes
for vertex in egi.V:
    G.add_node(vertex.id, node_type='vertex', area=find_logical_parent(vertex.id))

for edge in egi.E:
    G.add_node(edge.id, node_type='predicate', area=find_logical_parent(edge.id))

# Add ligatures as edges (can cross cut boundaries)
for edge_id, vertex_mappings in egi.nu.items():
    for vertex_id in vertex_mappings:
        G.add_edge(vertex_id, edge_id, ligature=True)
```

**Output**: Global NetworkX graph with area-constrained positioning

### 2. NetworkX Layout → Qt Scene Containment

**Input**: NetworkX graph + area positions
**Process**: `NetworkXQtLayoutEngine._build_qt_containment_with_positions()`

```python
# Create Qt containment hierarchy
scene = QGraphicsScene()

# Create area containers (cuts as QGraphicsRectItem)
for cut in egi.Cut:
    cut_item = QGraphicsRectItem(cut_bounds)
    scene.addItem(cut_item)

# Place elements in correct Qt parent-child hierarchy
for element_id, position in networkx_positions.items():
    element_item = create_qt_item(element_id, position)
    parent_area = find_logical_parent(element_id)
    parent_item = get_qt_container(parent_area)
    element_item.setParentItem(parent_item)  # Qt containment
```

**Output**: Qt scene graph with proper containment hierarchy

### 3. Qt Scene → Canonical EG Drawing

**Input**: Qt scene graph with positioned elements
**Process**: `AreaBasedDauRenderer.render_to_scene()`

```python
# Apply Dau/Peirce canonical conventions
for element in layout_result.elements:
    if element.element_type == 'vertex':
        # Render as small circle/dot
        render_vertex_canonical(element)
    elif element.element_type == 'predicate':
        # Render as text with proper typography
        render_predicate_canonical(element)
    elif element.element_type == 'ligature':
        # Render as rectilinear identity line
        render_ligature_canonical(element)
    elif element.element_type == 'cut':
        # Render as closed curve (rectangle/oval)
        render_cut_canonical(element)
```

**Output**: Canonical EG drawing following Dau/Peirce conventions

### 4. User Interaction → Qt Events

**Input**: Mouse/keyboard interaction on visual elements
**Process**: Qt event system captures interactions

```python
# Qt graphics items handle events
class InteractiveVertexItem(QGraphicsEllipseItem):
    def mousePressEvent(self, event):
        # Capture vertex selection/drag start
        
    def mouseMoveEvent(self, event):
        # Update vertex position during drag
        
    def mouseReleaseEvent(self, event):
        # Complete vertex movement, trigger EGI update
```

### 5. Qt Events → EGI Operations

**Input**: Qt interaction events
**Process**: Map visual changes to EGI transformations

```python
# Transform visual changes to EGI operations
def handle_vertex_moved(vertex_id, new_position):
    # Check if movement crosses logical boundaries
    new_area = determine_logical_area(new_position)
    old_area = find_current_area(vertex_id)
    
    if new_area != old_area:
        # This is a logical transformation, not just visual
        egi_operation = create_area_transfer_operation(vertex_id, old_area, new_area)
        apply_egi_transformation(egi_operation)
    else:
        # Pure visual adjustment within same logical area
        update_visual_position_only(vertex_id, new_position)
```

### 6. EGI Update → Re-render Pipeline

**Input**: Modified EGI structure
**Process**: Complete pipeline refresh

```python
def update_after_egi_change(modified_egi):
    # Re-run complete pipeline
    layout_result = networkx_qt_engine.create_layout_from_egi(modified_egi)
    dau_renderer.render_to_scene(scene, layout_result)
    
    # Update chiron (EGIF display)
    update_egif_chiron(modified_egi)
```

## Key Architectural Principles

### 1. **Separation of Concerns**
- **EGI**: Pure mathematical/logical structure
- **NetworkX**: Spatial optimization and layout
- **Qt**: Visual containment and interaction
- **Dau Renderer**: Canonical appearance conventions

### 2. **Cross-Cut Ligature Handling**
- **Global NetworkX graph** captures all ligatures
- **Area-constrained positioning** keeps elements in logical areas
- **Qt parent-child hierarchy** provides visual containment
- **Ligatures span freely** between areas as required

### 3. **Bidirectional Integrity**
- **Forward**: EGI → Visual (deterministic rendering)
- **Reverse**: Visual → EGI (validated transformations)
- **Round-trip**: EGI → Visual → EGI (preserves structure)

### 4. **Interactive Constraints**
- **Visual movements** within areas are free
- **Cross-area movements** trigger logical transformations
- **Invalid operations** are prevented or flagged
- **Real-time feedback** through chiron and visual cues

## Implementation Status

✅ **NetworkX-Qt hybrid engine** implemented
✅ **Cross-cut ligature support** validated
✅ **Area-constrained positioning** working
✅ **Qt containment hierarchy** established
✅ **Canonical rendering pipeline** integrated
⏳ **Interactive transformation system** (next phase)
⏳ **Bidirectional validation** (next phase)

## Example: Canonical Implication Flow

```
EGI: ~[ ~[ (P "x") ] (Q "x") ]
 ↓
NetworkX: Global graph with vertex "x" connected to P and Q
 ↓
Qt: P in inner cut container, Q in outer cut container, ligatures span
 ↓
Visual: Canonical implication diagram with cross-cut identity line
 ↓
User drags vertex "x"
 ↓
Qt: Captures drag event, determines new logical area
 ↓
EGI: Updates vertex containment if area changed
 ↓
Re-render: Complete pipeline refresh with updated structure
```

This architecture ensures **mathematical rigor** (EGI), **optimal layout** (NetworkX), **visual containment** (Qt), and **canonical appearance** (Dau renderer) work together seamlessly.
