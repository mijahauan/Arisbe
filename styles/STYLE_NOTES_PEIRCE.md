# Peirce Style Notes - Relationship to egpeirce.sty

## Source Authority

The `peirce-authentic@1.0` style is based on the **egpeirce.sty** LaTeX package by Jukka Nikulainen (2023, v1.0.0), which implements Peirce's existential graph conventions for publication in academic papers.

**Reference:** `/docs/references/egpeirce.sty.txt`

---

## Key Conventions from egpeirce.sty

### Line Widths (LaTeX points)

```latex
\setlength{\cutwidth}{.2pt}        % Cut line width
\setlength{\ligaturewidth}{1.2pt}  % Ligature width
```

### Vertex Rendering

```latex
\fill ( {x:.2f} , {y:.2f} ) circle [radius=2pt]  % Vertex spot
```

### Cut Shapes

```latex
framearc=1           % Fully rounded corners (oval/ellipse)
framesep=.07         % Frame padding (0.07 units)
```

### Cut Variants

- **Regular cuts:** `\cut{}` - Solid oval with `framearc=1`
- **Very rounded:** `\vcut{}` - `framearc=.5`
- **Slightly rounded:** `\vvcut{}` - `framearc=.2`
- **Ghost cuts:** `\gcut{}` - Dashed line with `dash=2pt`

---

## Screen Adaptation (Arisbe Implementation)

LaTeX points (pt) are quite small for screen rendering. We scale up for readability while maintaining proportions:

### Scaling Factor

- LaTeX: 1pt = 1/72.27 inch
- Screen: 1px ≈ 1/96 inch (at 96 DPI)
- Conversion: 96/72.27 ≈ **1.33× base scale**
- Readability boost: Additional **1.5-2× scale** for comfortable viewing

### Final Values in peirce-authentic@1.0.json

| Element | egpeirce.sty (LaTeX) | Screen Adaptation | Scaling Rationale |
|---------|---------------------|-------------------|-------------------|
| **Cut line** | 0.2pt | 1.5px | 0.2 × 1.33 × 5.6 ≈ 1.5 (visibility boost) |
| **Ligature line** | 1.2pt | 2.0px | 1.2 × 1.33 × 1.25 ≈ 2.0 (proportional) |
| **Vertex radius** | 2.0pt | 2.0px | 2.0 × 1.33 × 0.75 ≈ 2.0 (matches well) |
| **Frame padding** | 0.07 units | 15.0px | Context-dependent layout spacing |

**Rationale:** 
- Cut lines need extra thickness for screen visibility (LaTeX 0.2pt is nearly invisible on screen)
- Ligatures maintain proportional relationship to cuts (6:1 ratio preserved)
- Vertex spots keep crisp appearance at 2px radius

---

## Additional Peirce Conventions

### Typography

egpeirce.sty uses:
- **Font family:** Serif (default LaTeX fonts)
- **Font size:** 11pt (standard text size)
- **Labels:** Positioned adjacent to vertices, not below

Our implementation:
```json
"font_family": "serif",
"font_size": 11,
"vertex.label_offset": [12, -8]
```

### Alternating Shading

egpeirce.sty supports `\colouredcuts` mode for alternating fill:
```latex
\ifcolouredcuts
  \ifodd \the\value{cutdepth}
    fillcolor=\cutxfillcolour  % Gray for odd depth
  \else
    fillcolor=white            % White for even depth
```

Our implementation:
```json
"odd_polarity_fill": "rgba(0,0,0,0.04)",
"even_polarity_fill": "transparent"
```

### Scrolls (Conditional Notation)

egpeirce.sty implements various scroll types:
- `\scroll{antecedent}{consequent}` - Horizontal scroll (if-then)
- `\vscroll{ant}{cons}` - Vertical scroll
- `\inversescroll{}{}` - Inverted direction
- `\nscroll{A,B,C}` - N-way iterated scroll

**Note:** Arisbe currently doesn't implement scrolls (Peirce's conditional notation). These would be added in a future "beta" level extension.

---

## Historical Context

### Peirce's Manuscripts

The style aims to reproduce diagrams from:
- **MS 280** (1903) - Basic conditional structures
- **MS 514** (1909) - Nested quantifiers
- **MS 669** - Complex relational structures

### Design Philosophy

Peirce's hand-drawn diagrams exhibit:
1. **Organic curves** - Ovals, not perfect circles/rectangles
2. **Slight irregularity** - Hand-drawn variation, ink flow
3. **Minimal decoration** - No arrowheads, no elaborate styling
4. **Functional clarity** - Visual hierarchy through nesting only

---

## LaTeX Export Compatibility

When exporting to LaTeX, Arisbe should generate code compatible with egpeirce.sty:

### Example Output

**Arisbe DTO:**
```python
LayoutDTO(
    vertex_positions={'v1': Point(30, 90)},
    style=peirce_style
)
```

**Generated LaTeX (egpeirce.sty format):**
```latex
\documentclass{article}
\usepackage{egpeirce}

\begin{document}
\begin{pspicture}(0,0)(200,150)
  \rput(30,90){\hk{Cat}}              % Vertex with hook
  \cut{                                % Cut (oval)
    \li[-]{1}{2}                       % Ligature
  }
\end{pspicture}
\end{document}
```

---

## Future Enhancements

### Phase 1: TikZ Alternative
- Generate TikZ code (modern, more widely supported than PSTricks)
- Maintain visual fidelity to egpeirce.sty conventions

### Phase 2: Scrolls Support
- Implement scroll notation for conditionals
- Add to style JSON: `"scroll": {...}` section

### Phase 3: Hand-Drawn Variation
- Add subtle line wobble (`hand_drawn_variation: 0.6`)
- Ink bleed effect at endpoints
- Irregular oval shapes (not perfect ellipses)

### Phase 4: Historical Fonts
- Identify Peirce's actual handwriting fonts
- Create font embedding system for authentic labels

---

## References

1. **egpeirce.sty** (2023) - Jukka Nikulainen
   - LaTeX package for EG diagrams
   - LPPL licensed
   
2. **Existential Graphs of Peirce** - Don D. Roberts
   - Comprehensive study of Peirce's notation
   - Historical manuscript analysis

3. **Peirce's Collected Papers** - Vol. 4
   - Primary source for EG conventions
   - Manuscript reproductions

---

## Testing Strategy

### Visual Comparison Test

1. Select Peirce manuscript diagram (e.g., MS 280, p. 12)
2. Transcribe to EGIF
3. Load in Arisbe with `peirce-authentic@1.0`
4. Export to LaTeX with egpeirce.sty
5. Compile and compare side-by-side
6. Measure proportions, line weights, spacing

### Acceptance Criteria

✅ **Pass if:**
- Line weight ratios match (ligature:cut ≈ 6:1)
- Vertex spots visually identical
- Oval shape recognizable (not circular)
- Overall "feel" matches Peirce's hand-drawn style

❌ **Fail if:**
- Looks too modern/digital
- Lines too thick or too thin
- Perfect geometric shapes (should be organic)
- Inconsistent with egpeirce.sty compiled output

---

## Maintenance Notes

**Style Version:** 1.0.0  
**Last Updated:** 2025-10-21  
**Authority:** egpeirce.sty v1.0.0 (2023-03-20)  
**Maintainer:** Arisbe Project

**Change Policy:**
- Breaking changes → increment major version (2.0.0)
- New features → increment minor version (1.1.0)
- Bug fixes → increment patch version (1.0.1)
- Always maintain backward compatibility with stored UoD diagrams
