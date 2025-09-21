# Arisbe Style System Guide

## Overview

The Arisbe Style System provides platform-independent styling for Existential Graph diagrams. Styles are defined in JSON format and control all visual aspects of diagram rendering while maintaining mathematical correctness and spatial-logical correspondence.

## Table of Contents

1. [Style Architecture](#style-architecture)
2. [Style Definition Format](#style-definition-format)
3. [Built-in Styles](#built-in-styles)
4. [Creating Custom Styles](#creating-custom-styles)
5. [Integration with Layout Engine](#integration-with-layout-engine)
6. [Optional Features](#optional-features)
7. [Transformation Support](#transformation-support)
8. [Validation and Testing](#validation-and-testing)

## Style Architecture

### Platform Independence
- **JSON-based**: No platform-specific dependencies (Qt, SVG, etc.)
- **Renderer-agnostic**: Works with any rendering backend
- **Layout-integrated**: Styles affect spatial calculations in the layout engine

### Polarity Convention
The style system follows standard EG polarity conventions:
- **Even polarity (0, 2, 4, ...)**: Positive contexts → Unshaded/transparent
- **Odd polarity (1, 3, 5, ...)**: Negative contexts → Light shading

```
Sheet (level 0) → Even polarity → Unshaded
├─ Cut (level 1) → Odd polarity → Shaded
   ├─ Cut (level 2) → Even polarity → Unshaded
      └─ Cut (level 3) → Odd polarity → Shaded
```

## Style Definition Format

### Required Fields

```json
{
  "style_name": "unique-identifier",
  "version": "1.0.0",
  "description": "Human-readable description",
  
  "global": {
    "font_family": "Times New Roman",
    "font_size": 12,
    "background_color": "#FFFFFF"
  },
  
  "layout": {
    "element_spacing": 40.0,
    "cut_padding": 20.0,
    "sibling_spacing": 30.0
  },
  
  "vertex": {
    "radius": 3.0,
    "fill_color": "#000000"
  },
  
  "cut": {
    "shape": "rounded_rectangle",
    "line_width": 2.0,
    "line_color": "#000000"
  },
  
  "ligature": {
    "line_width": 2.0,
    "color": "#000000"
  }
}
```

### Complete Field Reference

#### Global Settings
- `font_family`: Font family name (string)
- `font_size`: Base font size in points (number)
- `font_weight`: "normal", "bold", or "light"
- `background_color`: Hex color or rgba() string

#### Layout Parameters
These affect spatial calculations in the layout engine:
- `element_spacing`: Minimum space between elements (number)
- `cut_padding`: Internal padding within cuts (number)
- `sibling_spacing`: Space between sibling cuts (number)
- `diagram_margin`: Outer margin around entire diagram (number)
- `text_margin`: Margin around text elements (number)
- `ligature_clearance`: Clearance around ligatures (number)
- `grid_snap`: Snap elements to grid (boolean)
- `alignment_grid_size`: Grid size for snapping (number)
- `organic_variation`: Allow organic positioning variation (boolean)

#### Vertex Styling
- `radius`: Dot radius in pixels (number)
- `fill_color`: Dot fill color (string)
- `border_color`: Dot border color (string)
- `border_width`: Dot border width (number)
- `rendering_mode`: "dot_only", "label_only", or "dot_and_label"
- `style`: "regular", "slightly_irregular", or "hand_drawn"
- `label_font_size`: Font size for vertex labels (number)
- `label_color`: Color for vertex labels (string)
- `label_offset`: [x, y] offset from dot center (array)
- `label_padding`: [x, y] padding around label text (array)
- `superscript_font_size`: Font size for quantifier superscripts (number)
- `superscript_color`: Color for superscripts (string)
- `superscript_offset`: [x, y] offset for superscripts (array)

#### Predicate Styling
- `identity_line_width`: Width of predicate identity lines (number)
- `identity_line_color`: Color of identity lines (string)
- `identity_cap_style`: "round", "square", or "butt"
- `label_box_background`: Background color for predicate labels (string)
- `label_box_border_color`: Border color for label boxes (string)
- `label_box_border_width`: Border width for label boxes (number)
- `label_box_padding`: [x, y] padding inside label boxes (array)
- `label_font_size`: Font size for predicate labels (number)
- `label_color`: Color for predicate text (string)
- `char_width_estimate`: Estimated character width for layout (number)
- `height_estimate`: Estimated text height for layout (number)
- `even_polarity_fill`: Fill color for predicates in even polarity areas (string)
- `odd_polarity_fill`: Fill color for predicates in odd polarity areas (string)

#### Cut Styling
- `shape`: "rectangle", "rounded_rectangle", "oval", or "circle"
- `corner_radius`: Radius for rounded corners (number)
- `line_width`: Cut border line width (number)
- `line_color`: Cut border color (string)
- `even_polarity_fill`: Fill color for even polarity cuts (string)
- `odd_polarity_fill`: Fill color for odd polarity cuts (string)
- `nesting_margin`: Margin between nested cuts (number)
- `depth_indication`: Show depth indicators (boolean)
- `hand_drawn_variation`: Amount of hand-drawn variation 0-1 (number)

#### Ligature Styling
- `line_width`: Ligature line width (number)
- `color`: Ligature color (string)
- `cap_style`: "round", "square", or "butt"
- `routing_mode`: "direct", "orthogonal", "manhattan", "bezier", or "organic"
- `curvature`: Curvature amount 0-1 for curved routing (number)
- `orthogonal_bias`: "h_first", "v_first", or "natural"
- `min_length`: Minimum ligature length (number)
- `border_overlap`: Overlap with element borders (number)
- `approach_margin`: Margin when approaching elements (number)
- `hand_drawn_variation`: Hand-drawn variation 0-1 (number)

## Built-in Styles

### 1. DAU-Compliant (Default)
**File**: `styles/dau-compliant@1.0.json`

Mathematical precision based on Dau's treatise:
- Rounded rectangles for cuts
- Times New Roman typography
- Clean, formal appearance
- Even polarity: transparent
- Odd polarity: light gray (`rgba(0,0,0,0.08)`)

### 2. Peirce-Authentic
**File**: `styles/peirce-authentic@1.0.json`

Authentic reproduction of Peirce's hand-drawn conventions:
- Oval cuts with hand-drawn variation
- Serif typography
- Organic ligature routing
- Even polarity: transparent
- Odd polarity: very light gray (`rgba(0,0,0,0.04)`)

### 3. Sowa-Compliant
**File**: `styles/sowa-compliant@1.0.json`

Conceptual graph conventions:
- Oval cuts (no rectangles)
- Grid-aligned layout
- Arity numbers enabled by default
- Even polarity: transparent
- Odd polarity: light blue (`rgba(0,100,200,0.1)`)

## Creating Custom Styles

### Step 1: Copy Base Template
Start with an existing style that's closest to your needs:

```bash
cp styles/dau-compliant@1.0.json styles/my-custom-style@1.0.json
```

### Step 2: Update Metadata
```json
{
  "style_name": "my-custom-style",
  "version": "1.0.0",
  "description": "My custom style description",
  // ... rest of style
}
```

### Step 3: Modify Visual Properties
Focus on these key areas:
- **Colors**: Background, fills, borders
- **Typography**: Font family, sizes
- **Shapes**: Cut shapes, corner radius
- **Spacing**: Layout parameters that affect spatial calculations

### Step 4: Test Integration
```python
from src.style_loader import StyleLoader
from src.layout_engine_styled import StyleAwareLayoutEngine

# Load your custom style
style_loader = StyleLoader()
custom_style = style_loader.load_style("my-custom-style@1.0")

# Test with layout engine
engine = StyleAwareLayoutEngine(custom_style)
layout = engine.compute_layout(egi)
```

### Step 5: Validate Schema
```bash
# Validate against schema
python -c "
import json
import jsonschema

with open('styles/style_schema.json') as f:
    schema = json.load(f)
    
with open('styles/my-custom-style@1.0.json') as f:
    style = json.load(f)
    
jsonschema.validate(style, schema)
print('✅ Style is valid!')
"
```

## Integration with Layout Engine

### Style-Aware Spatial Calculations
The layout engine uses style parameters for:

1. **Element Sizing**:
   ```python
   vertex_diameter = style.vertex.radius * 2
   predicate_bounds = (style.predicate.char_width_estimate * len(text), 
                      style.predicate.height_estimate)
   ```

2. **Spacing Calculations**:
   ```python
   area_width = content_width + 2 * style.layout.cut_padding
   sibling_offset = style.layout.sibling_spacing
   ```

3. **Text Layout**:
   ```python
   label_position = vertex_position + style.vertex.label_offset
   text_bounds = estimate_text_size(text, style.global.font_size)
   ```

### Iron-Clad Guarantees Maintained
Regardless of style parameters, the layout engine maintains:
- ✅ Spatial-logical correspondence
- ✅ Complete element coverage
- ✅ Proper containment relationships
- ✅ No overlapping violations

## Optional Features

### Alternating Shading
```json
"alternating_shading": {
  "enabled": true,
  "even_polarity_color": "transparent",
  "odd_polarity_color": "rgba(0,0,0,0.08)",
  "start_level": 0,
  "fade_with_depth": false
}
```

### Arity Numbers
Display connection counts for each vertex:
```json
"arity_numbers": {
  "enabled": true,
  "font_size": 8,
  "color": "#666666",
  "position": "top_right",
  "offset": [2, -2]
}
```

### Variable Labels
Show variable names from linear forms:
```json
"variable_labels": {
  "enabled": true,
  "font_size": 9,
  "color": "#0066CC",
  "format": "subscript",
  "show_for": ["unnamed_vertices"]
}
```

## Transformation Support

### Double Cut Highlighting
For transformation operations:
```json
"double_cut_highlight": {
  "enabled": false,  // Enable when needed
  "border_color": "#FF6600",
  "border_style": "dashed",
  "label": {
    "text": "DC",
    "position": "top_left"
  }
}
```

### Isomorphic Graph Highlighting
For subgraph matching:
```json
"isomorphic_highlight": {
  "enabled": false,  // Enable when needed
  "primary_color": "#00AA00",
  "secondary_color": "#66DD66",
  "connection_lines": {
    "enabled": true,
    "style": "dotted"
  }
}
```

### Collapsed Context Indication
For depth-restricted views:
```json
"collapsed_context": {
  "enabled": false,  // Enable when needed
  "indicator_symbol": "⋯",
  "tooltip_text": "Collapsed context (depth {level}+)"
}
```

## Validation and Testing

### Schema Validation
All styles must conform to `styles/style_schema.json`:
```bash
python tools/validate_style.py styles/my-style@1.0.json
```

### Layout Engine Testing
Test style integration:
```bash
python -m pytest tests/test_style_integration.py -v
```

### Visual Regression Testing
Generate test diagrams:
```bash
python tools/generate_style_samples.py --style my-style@1.0
```

## Best Practices

### 1. Naming Conventions
- Use kebab-case: `my-custom-style`
- Include version: `@1.0.0`
- Be descriptive: `peirce-authentic` not `style1`

### 2. Color Choices
- Use hex colors for consistency: `#000000`
- Use rgba() for transparency: `rgba(0,0,0,0.08)`
- Follow polarity conventions for shading

### 3. Spacing Parameters
- Consider text size when setting spacing
- Test with complex nested diagrams
- Ensure readability at different zoom levels

### 4. Typography
- Choose web-safe fonts or provide fallbacks
- Consider character width estimates for layout
- Test with various predicate name lengths

### 5. Platform Compatibility
- Avoid platform-specific features
- Test rendering on different backends
- Use standard color formats

## Troubleshooting

### Common Issues

**Style not loading**:
- Check JSON syntax with validator
- Verify all required fields are present
- Ensure file naming follows convention

**Layout problems**:
- Check spacing parameters aren't too small
- Verify text size estimates are reasonable
- Test with various diagram complexities

**Rendering issues**:
- Ensure colors are in valid format
- Check that shape names are from allowed enum
- Verify numeric values are within valid ranges

### Debug Tools
```bash
# Validate style file
python tools/validate_style.py styles/my-style@1.0.json

# Test layout integration
python tools/test_style_layout.py --style my-style@1.0 --egif "test case"

# Generate visual samples
python tools/style_preview.py --style my-style@1.0
```

## Contributing

When contributing new styles or modifications:

1. **Follow the schema**: Validate against `style_schema.json`
2. **Test thoroughly**: Include test cases for complex diagrams
3. **Document changes**: Update this guide if adding new features
4. **Maintain compatibility**: Don't break existing styles
5. **Consider accessibility**: Ensure good contrast and readability

## File Locations

```
styles/
├── style_schema.json           # JSON schema definition
├── dau-compliant@1.0.json     # Default style
├── peirce-authentic@1.0.json  # Peirce style
├── sowa-compliant@1.0.json    # Sowa style
└── [custom-styles]            # User-defined styles

src/
├── style_loader.py            # Style loading utilities
├── layout_engine_styled.py    # Style-aware layout engine
└── style_integration.py       # Integration helpers

docs/
└── STYLE_SYSTEM_GUIDE.md      # This guide
```

---

**The Arisbe Style System provides complete control over diagram appearance while maintaining mathematical correctness and spatial-logical correspondence.**
