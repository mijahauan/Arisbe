# EGDF: Platform Independence & Stylistic Flexibility

## EGDF's Role in the Complete Architecture

### Complete Flow with EGDF Integration

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    EGI      │    │  NetworkX   │    │    EGDF     │    │ Platform    │    │  Rendered   │
│ Mathematical│───▶│   Layout    │───▶│ Interchange │───▶│ Renderer    │───▶│   Visual    │
│  Structure  │    │ Optimization│    │   Format    │    │ (Qt/Web/    │    │   Output    │
│             │    │             │    │             │    │ LaTeX/SVG)  │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### EGDF as Platform-Independent Interchange

**EGDF serves as the universal format that:**
- ✅ **Encodes all spatial and logical structure** from NetworkX layout
- ✅ **Preserves cross-cut ligature information** 
- ✅ **Maintains area containment hierarchy**
- ✅ **Supports arbitrary style metadata**
- ✅ **Enables round-trip conversion** (EGI ↔ EGDF ↔ Visual)

## Detailed EGDF Integration Flow

### 1. EGI → NetworkX → EGDF

```python
# NetworkX layout produces positioned elements
networkx_result = {
    'vertices': {'v1': (100, 150), 'v2': (200, 250)},
    'predicates': {'e1': (150, 200)},
    'ligatures': [('v1', 'e1'), ('v2', 'e1')],  # Cross-cut ligatures
    'areas': {'cut1': {'bounds': (80, 130, 240, 270), 'contains': ['v1']}}
}

# Convert to EGDF (platform-independent format)
def create_egdf_from_networkx(egi, networkx_result):
    egdf = EGDFDocument()
    
    # Encode spatial primitives with logical structure
    for vertex_id, (x, y) in networkx_result['vertices'].items():
        egdf.add_primitive({
            'type': 'vertex',
            'id': vertex_id,
            'position': {'x': x, 'y': y},
            'logical_area': find_logical_parent(vertex_id, egi),
            'style_class': 'canonical_vertex'  # Style metadata
        })
    
    for pred_id, (x, y) in networkx_result['predicates'].items():
        egdf.add_primitive({
            'type': 'predicate',
            'id': pred_id,
            'position': {'x': x, 'y': y},
            'text': get_predicate_name(pred_id, egi),
            'logical_area': find_logical_parent(pred_id, egi),
            'style_class': 'canonical_predicate'
        })
    
    # Cross-cut ligatures with full routing information
    for vertex_id, pred_id in networkx_result['ligatures']:
        ligature_path = calculate_ligature_path(vertex_id, pred_id, networkx_result)
        egdf.add_primitive({
            'type': 'ligature',
            'connects': [vertex_id, pred_id],
            'path': ligature_path,  # Full routing across cuts
            'crosses_cuts': determines_if_crosses_cuts(vertex_id, pred_id, egi),
            'style_class': 'canonical_ligature'
        })
    
    # Area boundaries (cuts)
    for area_id, area_info in networkx_result['areas'].items():
        egdf.add_primitive({
            'type': 'cut',
            'id': area_id,
            'bounds': area_info['bounds'],
            'contains': area_info['contains'],
            'style_class': 'canonical_cut'
        })
    
    return egdf
```

### 2. EGDF → Platform Renderers

**EGDF enables multiple platform renderers:**

#### Qt Renderer (Interactive GUI)
```python
class QtEGDFRenderer:
    def render(self, egdf_doc, style_theme='canonical'):
        scene = QGraphicsScene()
        
        for primitive in egdf_doc.primitives:
            if primitive['type'] == 'vertex':
                item = self.create_qt_vertex(primitive, style_theme)
                scene.addItem(item)
                
            elif primitive['type'] == 'ligature':
                # Handle cross-cut ligatures
                item = self.create_qt_ligature(primitive, style_theme)
                scene.addItem(item)  # Not clipped by cuts
        
        return scene
    
    def create_qt_vertex(self, primitive, style_theme):
        style = self.get_style(primitive['style_class'], style_theme)
        item = QGraphicsEllipseItem(
            primitive['position']['x'] - style['radius'],
            primitive['position']['y'] - style['radius'],
            style['radius'] * 2,
            style['radius'] * 2
        )
        item.setBrush(QBrush(style['fill_color']))
        return item
```

#### Web/SVG Renderer (Browser Export)
```python
class SVGEGDFRenderer:
    def render(self, egdf_doc, style_theme='hand_drawn'):
        svg = SVGDocument()
        
        for primitive in egdf_doc.primitives:
            if primitive['type'] == 'vertex':
                style = self.get_style(primitive['style_class'], style_theme)
                svg.add_circle(
                    cx=primitive['position']['x'],
                    cy=primitive['position']['y'],
                    r=style['radius'],
                    fill=style['fill_color'],
                    stroke=style['stroke_color']
                )
                
            elif primitive['type'] == 'ligature':
                # Cross-cut ligatures work seamlessly
                path = primitive['path']
                svg.add_path(path, style=self.get_ligature_style(style_theme))
        
        return svg.to_string()
```

#### LaTeX/TikZ Renderer (Publication Export)
```python
class LaTeXEGDFRenderer:
    def render(self, egdf_doc, style_theme='publication'):
        latex = LaTeXDocument()
        
        for primitive in egdf_doc.primitives:
            if primitive['type'] == 'vertex':
                style = self.get_style(primitive['style_class'], style_theme)
                latex.add_command(f"\\node[{style['node_style']}] at ({primitive['position']['x']},{primitive['position']['y']}) {{}};")
                
            elif primitive['type'] == 'ligature':
                # Cross-cut ligatures in TikZ
                path = self.convert_path_to_tikz(primitive['path'])
                latex.add_command(f"\\draw[{style['line_style']}] {path};")
        
        return latex.to_string()
```

## Style Separation Architecture

### Style Themes as Metadata

```python
# Style themes define appearance without affecting logic
STYLE_THEMES = {
    'canonical': {
        'vertex': {
            'radius': 3,
            'fill_color': 'black',
            'stroke_color': 'black',
            'stroke_width': 1
        },
        'predicate': {
            'font_family': 'Times',
            'font_size': 12,
            'color': 'black'
        },
        'ligature': {
            'stroke_color': 'black',
            'stroke_width': 2,
            'style': 'solid'
        },
        'cut': {
            'stroke_color': 'black',
            'stroke_width': 2,
            'fill': 'transparent'
        }
    },
    
    'hand_drawn': {
        'vertex': {
            'radius': 4,
            'fill_color': '#2C3E50',
            'stroke_color': '#2C3E50',
            'stroke_width': 2
        },
        'ligature': {
            'stroke_color': '#2C3E50',
            'stroke_width': 3,
            'style': 'hand_drawn',  # Adds slight waviness
            'roughness': 0.1
        },
        'cut': {
            'stroke_color': '#2C3E50',
            'stroke_width': 2,
            'style': 'sketchy',  # Hand-drawn appearance
            'roughness': 0.15
        }
    },
    
    'publication': {
        'vertex': {
            'radius': 2,
            'fill_color': 'black',
            'stroke_color': 'black'
        },
        'predicate': {
            'font_family': 'Computer Modern',
            'font_size': 10,
            'color': 'black'
        },
        'ligature': {
            'stroke_color': 'black',
            'stroke_width': 1,
            'style': 'solid'
        }
    }
}
```

### Dynamic Style Application

```python
def apply_style_theme(egdf_doc, theme_name):
    """Apply style theme without modifying logical structure."""
    theme = STYLE_THEMES[theme_name]
    
    for primitive in egdf_doc.primitives:
        style_class = primitive['style_class']
        if style_class in theme:
            # Add style metadata, preserve logical structure
            primitive['style'] = theme[style_class]
    
    return egdf_doc

# Usage: Same EGDF, different visual appearance
canonical_egdf = create_egdf_from_networkx(egi, networkx_result)
hand_drawn_egdf = apply_style_theme(canonical_egdf.copy(), 'hand_drawn')
publication_egdf = apply_style_theme(canonical_egdf.copy(), 'publication')
```

## Platform Independence Benefits

### 1. **Cross-Platform Compatibility**
```python
# Same EGDF works on any platform
egdf_doc = create_egdf_from_egi(egi)

# Qt desktop application
qt_scene = QtEGDFRenderer().render(egdf_doc, 'canonical')

# Web browser
svg_output = SVGEGDFRenderer().render(egdf_doc, 'hand_drawn')

# LaTeX publication
latex_output = LaTeXEGDFRenderer().render(egdf_doc, 'publication')

# All preserve identical logical structure and spatial relationships
```

### 2. **Round-Trip Integrity**
```python
# Perfect round-trip: EGI → EGDF → EGI
original_egi = parse_egif('~[ ~[ (P "x") ] (Q "x") ]')
egdf_doc = create_egdf_from_egi(original_egi)
reconstructed_egi = extract_egi_from_egdf(egdf_doc)

assert egi_equivalent(original_egi, reconstructed_egi)  # ✅ Perfect preservation
```

### 3. **Style Flexibility**
```python
# Same logical content, different visual styles
base_egdf = create_egdf_from_egi(egi)

# Academic presentation
academic_visual = render_with_style(base_egdf, 'publication')

# Student-friendly version  
friendly_visual = render_with_style(base_egdf, 'hand_drawn')

# Interactive exploration
interactive_visual = render_with_style(base_egdf, 'canonical')
```

## Cross-Cut Ligature Preservation

**EGDF perfectly preserves cross-cut ligatures:**

```python
# Cross-cut ligature in EGDF
{
    'type': 'ligature',
    'id': 'ligature_x_P_Q',
    'connects': ['vertex_x', 'predicate_P', 'predicate_Q'],
    'path': [
        {'x': 150, 'y': 200},  # Start at vertex_x
        {'x': 120, 'y': 180},  # Route to predicate_P (inner cut)
        {'x': 150, 'y': 200},  # Back to vertex_x
        {'x': 180, 'y': 220}   # Route to predicate_Q (outer cut)
    ],
    'crosses_cuts': ['cut_inner'],  # Metadata about boundary crossings
    'logical_areas': ['sheet', 'cut_inner', 'sheet'],  # Area sequence
    'style_class': 'canonical_ligature'
}
```

This enables any renderer to correctly draw the cross-cut ligature while applying appropriate visual styling.

## Summary: EGDF's Critical Role

✅ **Platform Independence**: Same EGDF works on Qt, Web, LaTeX, mobile, etc.  
✅ **Style Separation**: Visual appearance independent of logical structure  
✅ **Cross-Cut Ligature Support**: Perfect preservation of complex routing  
✅ **Round-Trip Integrity**: EGI ↔ EGDF ↔ Visual with no information loss  
✅ **Extensibility**: New renderers and styles without changing core logic  

**EGDF is the universal interchange format that makes Arisbe truly platform-independent while enabling unlimited visual customization.**
