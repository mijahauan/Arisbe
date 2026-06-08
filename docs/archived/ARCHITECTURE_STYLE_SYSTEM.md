# Style Architecture - Platform-Independent Rendering

> **⚠️ RETIRED (2026-06-08).** This Dec-2025 architecture note describes the
> Qt rendering pipeline (`gui_clean`, `qt_diagram_renderer.py`,
> `unified_d3_engine.py`) that was archived to `archive/qt-gui-2025/` in May
> 2026, and proposes TODOs against it. The live style system is documented in
> [STYLE_SYSTEM_GUIDE.md](../STYLE_SYSTEM_GUIDE.md) (the single canonical style
> doc); the live layout/render path is `elk_layout_engine.py` →
> `simple_svg_renderer.py` consuming a `StyleSpecification` from `style_loader`.
> Kept for historical reference.

## Overview

The Arisbe style system ensures **identical visual output** across all rendering backends (SVG, Qt, future web/mobile), with style as **data** stored with each UoD diagram.

## Design Principles

1. **Style is Data, Not Code** - No hardcoded visual properties in renderers
2. **Single Source of Truth** - LayoutDTO carries embedded style specification
3. **Platform Independence** - Same DTO → identical visual output (except interactivity)
4. **User Choice** - Style selected in Organon, stored with UoD metadata
5. **Historical Accuracy** - Support authentic Peirce, Dau, and Sowa conventions

---

## Complete Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. ORGANON (User Selection + Persistence)                           │
│                                                                      │
│    User browses tomos → Selects UoD                                 │
│    UoD.metadata.style_name = "peirce-authentic@1.0"                 │
│                                                                      │
│    [ ] Style Selector Dropdown (TODO)                               │
│        ├─ dau-compliant@1.0 (default - current Ergasterion look)   │
│        ├─ peirce-authentic@1.0 (hand-drawn, organic)               │
│        └─ sowa-conceptual@1.0 (modern, technical)                  │
│                                                                      │
│    ✓ Stored in: uod.meta.json → "style_name": "peirce-..."         │
└───────────────────┬──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 2. DIAGRAM CONTROLLER (Style Injection)                             │
│                                                                      │
│    organon_mode.py:                                                  │
│        style_loader = StyleLoader()                                  │
│        style_spec = style_loader.load_style(uod.metadata.style_name)│
│        controller.load_egi(egi, style=style_spec)                    │
│                                                                      │
│    diagram_controller.py:                                            │
│        self.current_style = style_spec  # Store for re-layout       │
│        self.layout_engine.compute_layout(egi, style=style_spec)      │
└───────────────────┬──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 3. LAYOUT ENGINE (Style-Aware Computation)                          │
│                                                                      │
│    unified_d3_engine.py / definitive_egi_layout_engine.py:           │
│                                                                      │
│    Uses style for spatial calculations:                              │
│        • Element spacing: style.element_spacing                      │
│        • Cut padding: style.cut_padding                              │
│        • Ligature clearance: style.ligature_clearance                │
│        • Font metrics: style.predicate_char_width, font_size         │
│                                                                      │
│    Produces:                                                         │
│        LayoutDTO(                                                    │
│            vertex_positions = {...},                                 │
│            predicate_positions = {...},                              │
│            cut_bounds = {...},                                       │
│            ligature_paths = {...},                                   │
│            style = style_spec  ← EMBEDDED IN DTO                     │
│        )                                                             │
└───────────────────┬──────────────────────────────────────────────────┘
                    ↓
            ┌───────┴────────┐
            ↓                ↓
┌──────────────────────┐  ┌──────────────────────────────────────────┐
│ 4a. SVG RENDERER     │  │ 4b. QT RENDERER                          │
│ (Organon - Static)   │  │ (Ergasterion - Interactive)              │
│                      │  │                                          │
│ simple_svg_renderer  │  │ qt_diagram_renderer                      │
│                      │  │                                          │
│ Reads dto.style:     │  │ Reads dto.style:                         │
│ ✓ ligature_line_width│  │ ✓ ligature_line_width                    │
│ ✓ cut_line_width     │  │ ✓ cut_line_width                         │
│ ✓ vertex_radius      │  │ ✓ vertex_radius                          │
│ ✓ cut_corner_radius  │  │ ✓ cut_corner_radius                      │
│ ✓ font_family        │  │ ✓ font_family                            │
│ ✓ font_size          │  │ ✓ font_size                              │
│                      │  │                                          │
│ NO HARDCODING!       │  │ NO HARDCODING!                           │
└──────────────────────┘  └──────────────────────────────────────────┘
```

---

## File Structure

```
styles/
├── dau-compliant@1.0.json        # Default - current Ergasterion appearance
├── peirce-authentic@1.0.json     # Peirce's hand-drawn conventions
└── sowa-conceptual@1.0.json      # Modern conceptual graphs style

src/
├── style_loader.py               # Loads JSON → StyleSpecification
├── universe_of_discourse.py      # UoDMetadata.style_name (NEW)
├── diagram_controller.py         # Injects style → layout engine
└── unified_d3_engine.py          # Uses style for spacing/sizing

src/gui_clean/
├── organon/organon_mode.py       # Loads style from UoD
├── ergasterion/ergasterion_mode.py  # Loads style from UoD
└── common/
    ├── qt_diagram_renderer.py    # Reads dto.style (NEEDS FIX)
    └── simple_svg_renderer.py    # Reads dto.style (✓ already correct)
```

---

## Style JSON Schema

Based on `peirce-authentic@1.0.json`:

```json
{
  "style_name": "peirce-authentic",
  "version": "1.0.0",
  "description": "Authentic reproduction of Peirce's hand-drawn EG conventions",
  
  "global": {
    "font_family": "serif",
    "font_size": 11,
    "font_weight": "normal"
  },
  
  "layout": {
    "element_spacing": 35.0,      // Used by layout engine
    "cut_padding": 15.0,           // Used by layout engine
    "ligature_clearance": 6.0      // Used by layout engine
  },
  
  "vertex": {
    "radius": 2.0,                 // Renderer reads this
    "fill_color": "#000000"
  },
  
  "cut": {
    "shape": "oval",               // "oval" or "rectangle"
    "corner_radius": 12,           // For rounded rectangles
    "line_width": 1.5              // Renderer reads this
  },
  
  "ligature": {
    "line_width": 1.8,             // Renderer reads this
    "color": "#000000",
    "cap_style": "round"
  },
  
  "predicate": {
    "label_font_size": 11,
    "char_width_estimate": 6.5,    // Layout engine uses this
    "height_estimate": 13.0        // Layout engine uses this
  }
}
```

---

## Required Changes

### ✅ DONE:

1. **UoD Metadata** - Added `style_name: str` field
2. **Organon Loading** - Reads style from UoD, passes to controller
3. **Ergasterion Loading** - Reads style from UoD, passes to controller

### ⚠️ TODO:

1. **Qt Renderer Hardcoding** - Remove hardcoded `pen.setWidth(2.5)` etc.
   - File: `src/qt_diagram_renderer.py`
   - Lines: 69, 87, 95, 152, 187, 213
   - Fix: Replace with `dto.style.ligature_line_width`, etc.

2. **Organon Style Selector UI** - Add dropdown in metadata panel
   - File: `src/gui_clean/organon/metadata_panel.py`
   - Add: QComboBox with available styles
   - Action: Update `uod.metadata.style_name` on change

3. **Style Validator** - Ensure JSON schemas are valid
   - Create: `src/style_validator.py`
   - Validates: Required fields, value ranges, color formats

4. **Create Missing Styles**:
   - `styles/dau-compliant@1.0.json` (copy current defaults)
   - `styles/sowa-conceptual@1.0.json` (modern, technical)

---

## Migration Path

### Phase 1: Fix Qt Renderer (CRITICAL)
- Remove all hardcoded `pen.setWidth()` calls
- Read from `dto.style.*` instead
- Test: Both renderers produce identical output

### Phase 2: UI for Style Selection
- Add style dropdown in Organon metadata panel
- Allow user to change style, see preview
- Save to UoD metadata on change

### Phase 3: Complete Style Library
- Finalize dau-compliant@1.0.json
- Create peirce-authentic@1.0.json
- Create sowa-conceptual@1.0.json
- Add style preview thumbnails

### Phase 4: Advanced Features
- Style inheritance (base + overrides)
- Per-element style overrides
- Export custom styles
- Style marketplace/sharing

---

## Testing Strategy

### Visual Parity Test:
```python
# Load same EGI in both renderers
dto = controller.get_renderable_dto()

# Render to SVG
svg_output = SimpleSVGRenderer().render_to_svg(dto, egi)

# Render to Qt
qt_scene = QtDiagramRenderer().render_to_scene(dto, egi)

# Export Qt scene to SVG for comparison
qt_svg_output = export_scene_to_svg(qt_scene)

# Compare (should be pixel-identical except interactivity)
assert svg_matches(svg_output, qt_svg_output, tolerance=1px)
```

### Style Switching Test:
```python
# Load with Dau style
controller.load_egi(egi, style=load_style("dau-compliant@1.0"))
dto_dau = controller.get_renderable_dto()

# Load with Peirce style
controller.load_egi(egi, style=load_style("peirce-authentic@1.0"))
dto_peirce = controller.get_renderable_dto()

# Verify different line widths
assert dto_dau.style.ligature_line_width != dto_peirce.style.ligature_line_width
```

---

## Benefits

1. **Platform Independence** - Add new renderers (web canvas, mobile) trivially
2. **Historical Accuracy** - Authentic Peirce/Dau/Sowa conventions
3. **User Control** - Choose visual style per diagram
4. **Maintainability** - Change styles without touching code
5. **Consistency** - Guaranteed identical appearance across all views

---

## Next Steps

1. Fix `qt_diagram_renderer.py` hardcoding (30 min)
2. Test visual parity between SVG/Qt (1 hour)
3. Add style selector UI in Organon (2 hours)
4. Create complete style library (4 hours)
5. Document style customization guide (1 hour)

**Estimated Total:** 8.5 hours

---

## Notes

- Style name format: `{tradition}-{variant}@{version}`
- Example: `"peirce-authentic@1.0"`, `"dau-textbook@2.1"`
- Version allows future evolution without breaking old diagrams
- Default fallback: `"dau-compliant@1.0"` if style not found
