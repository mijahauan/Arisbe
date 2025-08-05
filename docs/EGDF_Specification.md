# Existential Graph Diagram Format (EGDF) Specification

## Version 1.0.0

### Overview

The Existential Graph Diagram Format (EGDF) is a JSON-based format that captures both the logical structure of Existential Graphs (via canonical EGI) and their visual arrangement for rendering and export. EGDF enables:

1. **Round-trip capability**: EGIF ↔ EGI ↔ EGDF ↔ EGI ↔ EGIF
2. **Visual arrangement preservation**: Capture specific spatial layouts (e.g., historical Peirce diagrams)
3. **Export capability**: Generate LaTeX (egpeirce.sty), PNG, SVG, and other formats
4. **Interactive editing**: Support GUI operations while maintaining logical integrity

### Design Principles

- **EGI as Canonical**: All EGDF must map to a valid EGI structure
- **Separation of Concerns**: Logical structure (EGI) is separate from visual layout (spatial primitives)
- **Dau Convention Compliance**: All visual elements follow Dau's formalization of Peircean conventions
- **Platform Independence**: Format is independent of rendering backend
- **Extensibility**: Support for future visual enhancements and export formats

## EGDF Structure

```json
{
  "format": "EGDF",
  "version": "1.0.0",
  "metadata": {
    "title": "Optional diagram title",
    "author": "Optional author",
    "created": "ISO 8601 timestamp",
    "modified": "ISO 8601 timestamp",
    "description": "Optional description",
    "source": "Optional source reference (e.g., 'Peirce MS 482')",
    "tags": ["optional", "tags"]
  },
  "canonical_egi": {
    // Complete EGI structure as canonical logical form
    "vertices": [...],
    "edges": [...],
    "cuts": [...],
    "area_map": {...},
    "nu_map": {...},
    "kappa_map": {...}
  },
  "visual_layout": {
    "canvas": {
      "width": 800,
      "height": 600,
      "background_color": "#ffffff",
      "coordinate_system": "cartesian" // or "polar"
    },
    "style_theme": {
      "name": "dau_standard",
      "identity_line_width": 8.0,
      "vertex_radius": 6.0,
      "cut_line_width": 1.0,
      "predicate_font_size": 12,
      "predicate_font_family": "serif"
    },
    "spatial_primitives": [
      // Visual elements with precise positioning
    ]
  },
  "export_settings": {
    "latex": {
      "package": "egpeirce",
      "scale_factor": 1.0,
      "coordinate_precision": 2,
      "custom_commands": []
    },
    "png": {
      "dpi": 300,
      "antialias": true
    },
    "svg": {
      "precision": 2,
      "embed_fonts": true
    }
  }
}
```

## Spatial Primitives

### Vertex Primitive
```json
{
  "type": "vertex",
  "id": "vertex_id",
  "egi_element_id": "corresponding_egi_vertex_id",
  "position": {"x": 100.0, "y": 200.0},
  "style_overrides": {
    "radius": 6.0,
    "fill_color": "#000000",
    "stroke_color": "#000000",
    "stroke_width": 1.0
  },
  "annotations": {
    "label": "Optional vertex label",
    "label_position": "top" // top, bottom, left, right
  }
}
```

### Identity Line Primitive
```json
{
  "type": "identity_line",
  "id": "line_id", 
  "egi_element_id": "corresponding_egi_edge_id",
  "coordinates": [
    {"x": 100.0, "y": 200.0},
    {"x": 150.0, "y": 250.0}
  ],
  "style_overrides": {
    "width": 8.0,
    "color": "#000000",
    "line_style": "solid" // solid, dashed, dotted
  },
  "connection_points": {
    "start": {
      "element_id": "vertex_1",
      "attachment": "center"
    },
    "end": {
      "element_id": "predicate_1", 
      "attachment": "periphery",
      "periphery_angle": 180.0 // angle on predicate periphery
    }
  }
}
```

### Predicate Primitive
```json
{
  "type": "predicate",
  "id": "predicate_id",
  "egi_element_id": "corresponding_egi_edge_id",
  "position": {"x": 200.0, "y": 200.0},
  "text": "Human",
  "style_overrides": {
    "font_size": 12,
    "font_family": "serif",
    "font_weight": "normal",
    "color": "#000000"
  },
  "bounding_box": {
    "width": 40.0,
    "height": 16.0
  },
  "argument_order": [
    {"vertex_id": "vertex_1", "position": 1}
  ]
}
```

### Cut Primitive
```json
{
  "type": "cut",
  "id": "cut_id",
  "egi_element_id": "corresponding_egi_cut_id", 
  "shape": "ellipse", // ellipse, rectangle, polygon
  "bounds": {
    "x": 50.0,
    "y": 50.0,
    "width": 300.0,
    "height": 200.0
  },
  "style_overrides": {
    "stroke_width": 1.0,
    "stroke_color": "#000000",
    "fill_color": "transparent",
    "line_style": "solid"
  },
  "containment": {
    "parent_cut_id": null, // or parent cut ID
    "contained_elements": ["vertex_1", "predicate_1"]
  }
}
```

## Round-Trip Operations

### EGIF → EGI → EGDF
1. Parse EGIF to canonical EGI structure
2. Apply layout algorithm to generate spatial primitives
3. Create EGDF with canonical EGI + computed layout

### EGDF → EGI → EGIF
1. Extract canonical EGI from EGDF
2. Validate EGI structure integrity
3. Generate EGIF from canonical EGI

### Visual Arrangement Preservation
- Spatial primitives capture exact positioning from user editing
- Layout algorithms can be bypassed for historical diagram replication
- Export formats preserve both logical and visual fidelity

## Export Format Support

### LaTeX (egpeirce.sty)
```latex
% Generated from EGDF
\begin{pspicture}(0,0)(8,6)
  \DefNodes{A}{\rnode{vertex1}{\textbullet}}
  \DefNodes{B}{\rnode{pred1}{Human}}
  \li{vertex1}{pred1}
  \scroll{...}{...}
\end{pspicture}
```

### Coordinate Mapping
- EGDF coordinates → egpeirce.sty coordinates
- Automatic scaling and positioning
- Preservation of relative arrangements

## Validation Rules

### Logical Consistency
1. All spatial primitives must reference valid EGI elements
2. Containment relationships must match EGI area_map
3. Connection points must respect nu_map argument order

### Visual Consistency  
1. Identity lines must connect vertices to predicate periphery (Dau convention)
2. Cuts must not overlap (strict containment hierarchy)
3. Elements must be positioned within their designated areas

### Export Compatibility
1. Coordinates must be within canvas bounds
2. Text elements must have valid font specifications
3. Colors must be in valid format for target export

## Implementation Guidelines

### Parser Requirements
- JSON schema validation for EGDF structure
- EGI extraction and validation
- Spatial primitive validation

### Renderer Requirements
- Platform-independent rendering interface
- Style theme application
- Export format generation

### Editor Requirements
- Real-time EGI validation during editing
- Constraint enforcement (Dau conventions)
- Undo/redo with EGDF state management

## Future Extensions

### Advanced Visual Elements
- Subgraph selection overlays (dotted boundaries)
- Animation sequences for transformations
- Interactive highlighting and annotations

### Additional Export Formats
- TikZ/PGF for LaTeX
- GraphML for graph analysis tools
- Interactive web formats (D3.js, etc.)

### Collaborative Features
- Version control integration
- Diff/merge support for diagram evolution
- Shared workspace synchronization

---

This specification provides the foundation for implementing Peirce's "moving pictures of thought" with mathematical rigor and practical utility for both academic research and educational applications.
