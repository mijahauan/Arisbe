# Feature: Scholarly Reproduction of Peirce's Hand-Drawn EGs

## Use Case

**Goal:** Enable academics to recreate Peirce's hand-drawn existential graphs from his notebooks in publication-ready LaTeX format for scholarly publications.

**Users:** Peirce scholars, logic historians, semiotics researchers, philosophy academics

**Output:** LaTeX documents using TikZ/pgf that can be included in academic papers, dissertations, and textbooks.

---

## Two Workflows

### **Workflow A: Text-First (Transcription → Visual)**

**User Journey:**
1. Scholar transcribes Peirce's diagram to linear form (EGIF, CGIF, CLIF, or FOPL)
2. Loads into Arisbe → parses to EGI model
3. Layout engine applies Peirce style → initial spatial arrangement
4. Scholar manually adjusts in Ergasterion to match Peirce's original spatial layout
5. Export to LaTeX (TikZ) → publication-ready vector graphics

**Example:**
```
Peirce MS 280 (1903)
Hand-written: "If a man is wise, then if he is rich, he is happy"

↓ Transcribe to EGIF
*x *y (Cat x) (Mat y) (On x y)

↓ Load into Arisbe
Creates EGI: 2 vertices (Cat, Mat), 1 relation (On)

↓ Layout with peirce-authentic@1.0
Auto-positions elements using Peirce conventions

↓ Manual adjustment in Ergasterion
Match Peirce's actual spatial arrangement from notebook

↓ Export to LaTeX
\begin{tikzpicture}
  \draw[line width=1.8pt] (oval cut)...
  \fill (3.2, 5.1) circle [radius=2pt] node[anchor=west] {Cat};
  ...
\end{tikzpicture}
```

### **Workflow B: Drawing-First (Visual → Text)**

**User Journey:**
1. Scholar opens Ergasterion in "Peirce Drawing Mode"
2. Manually draws graph mimicking Peirce's notebook diagram
   - Place vertices (identity lines)
   - Draw ovals (cuts)
   - Add labels
   - Connect ligatures
3. System generates EGI model from drawing
4. System generates EGIF/linear forms
5. Export to LaTeX (TikZ)

**Example:**
```
Scholar viewing Peirce MS 514 (1909)

↓ Draw in Ergasterion (Peirce style)
[User manually places elements to match notebook]

↓ System generates EGI
Extracts: V, E, Cut, area, nu mappings

↓ System generates EGIF
*x *y (Cat x) (Mat y) (On x y)

↓ Export to LaTeX
\begin{tikzpicture}... (matches drawing)
```

---

## Required Features

### ✅ Already Implemented

1. **EGI Core Model** - Formal representation of existential graphs
2. **EGIF Parser** - Converts linear form → EGI
3. **Layout Engine** - Spatial arrangement with style support
4. **Peirce Style Spec** - `peirce-authentic@1.0.json` exists
5. **TikZ Exporter** - `export/tikz_exporter.py` generates LaTeX
6. **Manual Positioning** - Ergasterion supports drag/drop element placement

### ⚠️ Needs Implementation/Enhancement

#### High Priority:

**1. LaTeX Export Integration in Organon/Ergasterion**
- **Current:** Only SVG export button
- **Need:** "Export LaTeX..." button
- **Location:** `organon_mode.py` line 104-107, `ergasterion_mode.py`
- **Implementation:**
  ```python
  def _on_export_latex(self):
      file_path = QFileDialog.getSaveFileName(
          self, "Export to LaTeX", 
          f"{self.egi_name}.tex",
          "LaTeX (*.tex)"
      )
      if file_path:
          dto = self.controller.get_renderable_dto()
          from export.tikz_exporter import generate_tikz
          # Convert DTO to render commands
          tikz_output = generate_tikz(render_commands, standalone=True)
          Path(file_path).write_text(tikz_output)
  ```

**2. DTO → TikZ Render Commands Bridge**
- **Current:** TikZ exporter expects "render commands" format
- **Need:** Convert `LayoutDTO` → TikZ render commands
- **Missing Link:** Adapter between unified DTO and old render command format
- **File:** Create `src/export/dto_to_tikz_adapter.py`

**3. Peirce Style Fidelity Enhancements**
- **Current:** Basic Peirce conventions in JSON
- **Need:** More authentic details:
  - Hand-drawn line variation (slight wobble)
  - Ink bleed effect (thicker at endpoints)
  - Oval shape irregularity
  - Font matching Peirce's handwriting
- **File:** Enhance `styles/peirce-authentic@1.0.json`

#### Medium Priority:

**4. CGIF/CLIF/FOPL Parsers**
- **Current:** Only EGIF parser implemented
- **Need:** Parse Sowa's CGIF, Common Logic CLIF, FOPL
- **Benefit:** Scholars can use any linear notation format
- **Files:** Create `src/parsers/cgif_parser.py`, `clif_parser.py`, `fopl_parser.py`

**5. Drawing Mode in Ergasterion**
- **Current:** Transformation mode only (apply formal rules)
- **Need:** Free drawing mode (no rule validation)
- **UI:** Mode toggle: [Transformation] / [Drawing]
- **Behavior:** In drawing mode, allow any placement without checking graph-theoretic validity

**6. Template Library**
- **Current:** Start from scratch
- **Need:** Pre-made templates of common Peirce diagrams
- **Examples:**
  - Simple conditional (MS 280)
  - Nested implications (MS 514)
  - Quantifier structure (MS 669)
- **Storage:** `tomos/templates/peirce/`

**7. Citation Generator**
- **Current:** Manual citation entry
- **Need:** Auto-generate proper citations
- **Format:** "Peirce, C.S. (1903). MS 280, p. 12. In *Writings of Charles S. Peirce*, Vol. 6."
- **Integration:** Metadata panel → "Generate Citation" button

#### Low Priority:

**8. Overlay Comparison Mode**
- **Need:** Overlay Peirce's original image with Arisbe recreation
- **UI:** Transparency slider to fade between original and recreation
- **Benefit:** Verify spatial accuracy

**9. Batch Export**
- **Need:** Export multiple diagrams at once
- **Format:** Single LaTeX document with all diagrams
- **Use Case:** Creating appendix of all Peirce diagrams for a paper

**10. Historical Context Annotations**
- **Need:** Add scholarly notes to diagrams
- **Format:** LaTeX footnotes/margin notes
- **Content:** "This diagram appears in MS 514 and represents Peirce's treatment of..."

---

## Implementation Phases

### Phase 1: Core Export (2-3 hours)
- [x] TikZ exporter exists
- [ ] Create DTO → TikZ adapter
- [ ] Add "Export LaTeX..." button to Organon
- [ ] Add "Export LaTeX..." button to Ergasterion
- [ ] Test roundtrip: EGIF → Layout → LaTeX → compile

### Phase 2: Style Refinement (4-6 hours)
- [ ] Enhance `peirce-authentic@1.0.json`
- [ ] Add hand-drawn variation parameters
- [ ] Test with actual Peirce diagrams (MS 280, 514, 669)
- [ ] Create style guide documentation

### Phase 3: Parser Extensions (8-10 hours)
- [ ] Implement CGIF parser
- [ ] Implement CLIF parser
- [ ] Implement FOPL parser
- [ ] Unified parser interface

### Phase 4: Drawing Mode (10-15 hours)
- [ ] Mode toggle in Ergasterion UI
- [ ] Disable formal rule validation in drawing mode
- [ ] Free-form element creation
- [ ] Reverse generation (Drawing → EGI)

### Phase 5: Scholarly Features (6-8 hours)
- [ ] Template library
- [ ] Citation generator
- [ ] Batch export
- [ ] Documentation for scholars

---

## Example Output

**Input EGIF:**
```
*x *y (Cat x) (Mat y) (On x y)
```

**Generated LaTeX:**
```latex
\documentclass[tikz]{standalone}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}[x=1pt,y=1pt]

% Sheet (background)
\draw[line width=1.8pt,rounded corners=12pt] 
  (10, 10) rectangle (180, 120);

% Ligatures (hand-drawn style with slight curve)
\draw[line width=1.8pt,line cap=round] 
  (45, 85) .. controls (50, 75) .. (55, 65);

% Vertices (spots with labels)
\fill (30, 90) circle [radius=2pt] 
  node[anchor=west,font=\fontsize{11}{13}\selectfont] {Cat};
\fill (70, 90) circle [radius=2pt] 
  node[anchor=west,font=\fontsize{11}{13}\selectfont] {Mat};

% Predicate (relation label)
\node[font=\fontsize{11}{13}\selectfont] at (50, 60) {On};

\end{tikzpicture}
\end{document}
```

**Compiled Result:** Vector graphic matching Peirce's hand-drawn style

---

## Benefits

1. **Academic Rigor** - Faithful reproduction of historical diagrams
2. **Publication Quality** - Vector graphics scale perfectly in LaTeX
3. **Workflow Efficiency** - Faster than manual TikZ coding
4. **Scholarly Citation** - Proper attribution and documentation
5. **Research Tool** - Experiment with variations of Peirce's diagrams
6. **Educational** - Students can recreate and understand Peirce's notation

---

## Documentation Needs

1. **Tutorial:** "Recreating Peirce MS 280 in Arisbe"
2. **Style Guide:** Peirce's EG conventions (vertex placement, ligature routing, cut shapes)
3. **LaTeX Integration:** How to include exported diagrams in papers
4. **Parser Reference:** Which notation format to use when
5. **Template Gallery:** Common Peirce diagram patterns

---

## Related Work

- **John Sowa's CGIF Tools** - Conceptual graph interchange format
- **Norman Roberts' EG Software** - Historical EG visualization
- **Logic LaTeX Packages** - `prooftrees`, `logicproof`, `bussproofs`
- **Historical Notation Projects** - Frege notation in LaTeX, Russell's *Principia* recreation

---

## Success Criteria

✅ Scholar can:
1. Transcribe Peirce's diagram from notebook to EGIF
2. Load into Arisbe with Peirce style
3. Manually adjust to match Peirce's spatial layout
4. Export publication-ready LaTeX
5. Compile to PDF and include in academic paper

✅ Output quality:
- Visually faithful to Peirce's hand-drawn style
- Vector graphics (scalable without loss)
- Proper line weights, curves, and spacing
- LaTeX-compatible (compiles without errors)

---

## Timeline Estimate

**Minimal Viable (Phase 1):** 2-3 hours
**Production Ready (Phases 1-2):** 6-9 hours
**Full Feature Set (Phases 1-5):** 36-47 hours

**Next Immediate Steps:**
1. Create DTO → TikZ adapter (1 hour)
2. Add export buttons (30 min)
3. Test with one Peirce diagram (1 hour)
4. Document workflow (30 min)
