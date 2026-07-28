# Reproducing Peirce's Hand-Drawn Graphs in Print

Arisbe can recreate Peirce's hand-drawn existential graphs, from his notebooks and
the *Collected Papers*, as publication-ready LaTeX. A scholar transcribes or draws
the graph, adjusts its arrangement to match the original, and exports pure TikZ that
compiles with plain `pdflatex`: oval cuts, heavy lines of identity, hooks, the
hand-drawn waver, and the citation stamped under the figure. The output drops into
papers, dissertations, and textbooks as scalable vector graphics. And unlike a
hand-coded figure, the picture stands *wedded to the graph*. Arisbe generates it
from the same attested (EGI, layout) pair the rest of the machinery reasons over,
so the figure and the proposition cannot drift apart.

---

## Two Workflows

### **Workflow A: Text-First (Transcription → Visual)**

**User Journey:**

1. Scholar transcribes Peirce's diagram to linear form (Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)), Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)), Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)), or First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl)))
2. Loads into Arisbe → parses to Existential Graph Instance ([EGI](GLOSSARY.md#egi)) model
3. Layout engine applies Peirce style → initial spatial arrangement
4. Scholar manually adjusts in Ergasterion to match Peirce's original spatial layout
5. Export to LaTeX (TikZ) → publication-ready vector graphics

**Example:**
```
Peirce MS 280 (1903)
Hand-written: "If a man is wise, then if he is rich, he is happy"

↓ Transcribe to EGIF
~[ (man *x) (wise x) ~[ (rich x) ~[ (happy x) ] ] ]

  Two nested scrolls (Peirce's "if … then" = ~[ A ~[ B ] ]):
    if (man & wise) then ( if rich then happy )
  The man is one line of identity (*x), the same "he" running
  through man · wise · rich · happy.

↓ Load into Arisbe
Creates EGI: 1 line of identity (the man), 4 relations
(man, wise, rich, happy), 3 nested cuts (the two scrolls +
the inner negation of "happy").
Reads (Φ): ¬(man(x) ∧ wise(x) ∧ ¬(rich(x) ∧ ¬happy(x)))
        ≡ ∀x. man(x) ∧ wise(x) ∧ rich(x) → happy(x)

↓ Layout with peirce-authentic@1.0
Auto-positions elements using Peirce conventions: oval cuts in
nesting order, the heavy line of identity branching to each hook.

↓ Manual adjustment in Ergasterion
Match Peirce's actual spatial arrangement from the notebook
(regime-3 nudges only — the EGI, and its meaning, are untouched).

↓ Export to LaTeX (authentic-Peirce TikZ, via peirce_latex.py + arisbe-eg.sty)
\begin{tikzpicture}[x=0.75pt,y=-0.75pt]
  \egset{cut width=1.50pt, loi width=2.00pt, dot radius=1.50pt}
  \egcut{118.21}{182.24}{77.41pt}{125.43pt}{black!6}  % outer: if (man & wise) then …
  \egcut{98.71}{182.24}{37.99pt}{47.57pt}{none}       % middle: … if rich then …
  \egcut{96.21}{156.24}{23.41pt}{12.01pt}{black!6}    % inner: … then happy
  % the man — one continuous heavy line of identity branching to each predicate hook
  \egloi{(141.81,83.81) -- (186.36,156.64)}   % → man
  \egloi{(136.76,280.67) -- (186.36,156.64)}  % → wise
  \egloi{(122.20,207.26) -- (186.36,156.64)}  % → rich
  \egloi{(115.46,156.33) -- (186.36,156.64)}  % → happy
  \egdot{186.36}{156.64}                       % the branch point (teridentity)
  \egpred{136.61}{75.31}{man}
  \egpred{133.36}{289.17}{wise}
  \egpred{111.43}{215.76}{rich}
  \egpred{96.21}{156.24}{happy}
\end{tikzpicture}
```

*(The TikZ above is the exporter's actual output for this graph — every
oval is a `cut_bounds` from the §3.3-attested layout, every `\egloi` runs
from the man's vertex to a predicate hook, so the printed picture provably
denotes the same EGI. See [`src/peirce_latex.py`](../src/peirce_latex.py).)*

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

## The pieces, and where they live

| Piece | Where it lives |
|---|---|
| LaTeX export (Organon export panel) | `web_viewer/organon.html` → the `peirce-tikz` format (Organon only — see "Deliberately not built" for why not Ergasterion) |
| The exporter itself | `peirce_latex.export_peirce_latex(dto, egi)` — a pure function of the attested `LayoutDTO` (Data Transfer Object ([DTO](GLOSSARY.md#dto))) |
| Peirce fidelity (waver / ink) | `peirce_latex.py` + `tex/arisbe-eg.sty`: hand-drawn waver, organic ligature routing, crossing bridges, iconic [scroll](GLOSSARY.md#scroll) (a nested double cut — "if … then") glyph |
| Transcription formats | `egif_parser_dau.py`, `cgif_parser_dau.py`, `clif_parser_dau.py`, `chapter18_fopl_translation.py` — production, round-trip tested |
| Drawing mode | `web_viewer/js/freeform-canvas.js` + `drawing_to_egi.py` (draw-then-read, Graph↔Argument lock) |
| Citation generator | `scholarly_citation.py` → author-date line + BibTeX; `GET /export/citation` |
| Batch export (appendix of figures) | `export_service.export_peirce_document` + `POST /export/document`; the per-proof-step companion is `export_peirce_chain` + `POST /export/chain` |
| Citation under the figure | `export_peirce_latex(..., caption=…)` + the export `cite` flag / Organon's **"cite" checkbox** |

### The citation path in detail

**The citation generator, surfaced in the export.** A corpus Universe of Discourse ([UoD](GLOSSARY.md#uod)) already carries
its source in the typed **provenance** bundle ([provenance.py](../src/provenance.py))
(`theorem_source` = where the proposition comes from, `method_sources`, a transcribed
`proof_source`) plus an optional `bibliography.json`. [`scholarly_citation.py`](../src/scholarly_citation.py)
turns that into the two forms a scholar needs:

- a **human author-date citation** — *"Peirce, C. S. (1903). MS 280. In Writings of
  Charles S. Peirce, Vol. 6, p. 12."* — and
- a **BibTeX entry** (`@unpublished{peirceMS280, …}`), the CSL `type` mapped to the
  right entry type.

It **fabricates nothing**: an absent field is omitted, and a graph with no recorded
source honestly reports `has_source: false` (an original Arisbe graph has nothing
external to cite). Exposed at `GET /export/citation?uod_id=…`, and — the load-bearing
join with the export — `POST /export` with `cite: true` (or the **"cite" checkbox** in
Organon's export panel) stamps the citation as a `\footnotesize` caption **under** the
authentic-Peirce figure. The caption is ink *outside* the `tikzpicture`, so `cut_bounds`
and the correspondence check (§3.3) are untouched (the tikzpicture body is byte-identical with or without it).

**Batch export (an appendix of figures).** `export_peirce_document` assembles
several corpus UoDs into one authentic-Peirce LaTeX document, each a captioned figure
(name + its citation), reusing the same figure-stacking as the worked-chain document.
`POST /export/document` takes a list of `uod_ids` and honestly reports any it skipped.
(The single-derivation companion, `export_peirce_chain` / `POST /export/chain`, already
existed — one figure per proof step.)

### Deliberately not built (and why)

- **Export from Ergasterion:** the scholarly export lives in **Organon**, the attested
  archive — by the mode contract a graph reaches the citable corpus only through Agon,
  so a regime-1 Ergasterion *draft* has no provenance to cite and "publication-ready"
  would misrepresent its standing. Export a graph by sending it to the corpus first.
- **Handwriting font / ink-bleed:** the hand-drawn *waver* and round-capped heavy
  lines already evoke ink; a matched handwriting font is cosmetic and niche.
- **A separate template library:** the seeded corpus exemplars + the in-app primer
  already give a scholar canonical graphs to start from; a separate
  `tomos/templates/peirce/` would duplicate them.
- **Overlay comparison against the original scan:** genuinely unbuilt, but niche — it
  needs an original-scan upload path and a fade slider, a sizeable UI feature for a
  narrow verification use; revisit if a scholar asks.

---

## Example Output

The **actual** output of the authentic-Peirce path (`peirce-tikz`, `cite: true`) for
the corpus graph `peirce_cp_4_394_man_mortal` — the man–mortal scroll, `(Human *x) ~[
(Mortal x) ]` with the constant *Socrates*:

**Generated LaTeX:**

```latex
\documentclass[border=8pt,varwidth=12cm]{standalone}
\usepackage{tikz}                 % + the arisbe-eg macros, inlined for a self-contained file
\begin{document}
\begin{tikzpicture}[x=0.75pt,y=-0.75pt]
  \egset{cut width=1.50pt, loi width=2.00pt, dot radius=1.50pt}
  \egcut{133.72}{78.43}{89.04pt}{47.57pt}{black!6}   % outer cut (the scroll)
  \egcut{88.42}{52.43}{26.87pt}{12.01pt}{none}        % inner cut
  % scroll: outer=c_abe14f9e inner=c_ddf31f9b
  \egloi{(110.92,52.99) -- (182.04,54.76)}            % heavy line of identity (Socrates),
  \egloi{(116.44,103.45) -- (182.04,54.76)}            %   branching to Human and into the cut
  \egconst{188.04}{54.76}{Socrates}
  \egpred{104.99}{111.95}{Human}
  \egpred{88.42}{52.43}{Mortal}
\end{tikzpicture}
\par\medskip
\noindent\footnotesize Peirce, Charles Sanders (1931). Collected Papers of Charles
  Sanders Peirce. p. 4.394. the man–mortal scroll (CP 4.394)
\end{document}
```

Every oval is a `cut_bounds` from the §3.3-attested `LayoutDTO`, every `\egloi` runs
from the constant's vertex to a predicate hook, and the `\footnotesize` line is the
**scholarly citation** built from the UoD's provenance (`scholarly_citation.citation_for`)
— so the printed figure provably denotes the EGI *and* carries its attribution.
`\usepackage{tikz}` is the only hard dependency; the `arisbe-eg` macros are inlined.

**Compiled Result:** a tightly-cropped, publication-ready vector PDF (the `article`
class is the automatic fallback on minimal TeX installs without `standalone.cls`).

**Run it yourself** (from the repository root; verified 2026-07-27 — the export
produces a `.tex` that `pdflatex` compiles to a PDF with no packages beyond `tikz`):

```bash
uv run python -c '
import sys; from pathlib import Path
sys.path.insert(0, "src")
from tomos_service import TomosService
from peirce_latex import export_peirce_latex
from web_api.services.layout_service import generate_layout

svc = TomosService(Path("tomos"))
egi = svc.load_uod("peirce_cp_4_394_man_mortal").current_egi
dto, _ = generate_layout(egi, style_name="peirce-authentic@1.0")   # attests the correspondence check
tex = export_peirce_latex(dto, egi, standalone=True, document_class="article")
Path("man_mortal.tex").write_text(tex)
print("wrote man_mortal.tex")
'
pdflatex -interaction=nonstopmode man_mortal.tex   # -> man_mortal.pdf
```

(Pass `document_class="standalone"` for the border-cropped figure if your TeX
install has `standalone.cls`; the running web app serves the same export at
`POST /export` with format `peirce-tikz`.)

---

## Related Work

- **John Sowa's CGIF Tools** - Conceptual graph interchange format
- **Norman Roberts' EG Software** - Historical EG visualization
- **Logic LaTeX Packages** - `prooftrees`, `logicproof`, `bussproofs`
- **Historical Notation Projects** - Frege notation in LaTeX, Russell's *Principia* recreation

