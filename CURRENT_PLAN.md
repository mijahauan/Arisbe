# Current Plan

**Last Updated**: 2026-06-10 — exact-correspondence **Phases 1, 2 & 3a shipped**
(exact cut containment + exact ligature crossing + predicate label-box containment);
active arc = the exact-correspondence engine + freeform composition. History below
condensed 2026-06-10 (detail lives in git, the docs, and memory).

---

## ▶ NEXT SESSION — start here

**Designated next task: Exact-correspondence Phase 3b — "no improper occlusion."**
(Thread A below; Phases 1, 2, 3a are done.) After 3b, the appetite-driven menu
(Thread B, the math tasks) is still open.

### Phase 3b — no improper occlusion (the designated next task)
*§3.3 gains a "marks don't overlap each other / cut lines illegibly" check — an
occluded or bisected label can't be recovered by the reader, so correspondence
breaks. The constructive side: layout/routing treat label boxes as obstacles.*

**Building blocks in hand (from 3a):** `presentation_ops.predicate_label_box`
(predicate extent, single source of truth) and `box_intrudes_cut` (box-vs-cut
intrusion). 3a already forbids a *predicate* box straddling a cut boundary.

**The design crux — resolve first, it's an author call:**
- **Vertex/constant label placement is renderer-internal and direction-adaptive.**
  `simple_svg_renderer` (~L367–410) places a vertex label to the right of the dot,
  or, if a ligature leaves eastward, in the *freest angular gap* between incident
  ligatures. This geometry is **not in the DTO**. To check vertex-label occlusion
  §3.3 needs that box — so first factor the placement into a shared
  `vertex_label_box(...)` (the way 3a factored `predicate_label_box`) **or** carry
  the box in the DTO. Harder than the predicate case (depends on incident ligature
  angles). This also closes the gap 3a left open (constant = labeled dot).
- **What counts as "improper"?** Propose: (1) two *text* boxes (predicate/vertex
  labels) must not overlap — text-on-text is illegible; (2) a label box must not be
  *bisected* by a cut boundary stroke (for predicates this is 3a's no-straddle;
  extend to vertex labels). Likely *acceptable* (don't flag): a label box merely
  touched by a ligature line it's incident to. Get the author's read on where the
  line is before coding the check.

**Entry points:** `correspondence_attestation.py` (add an occlusion block beside the
3a extent block); `presentation_ops.py` (the shared box/overlap helpers — a
`boxes_overlap` is trivial; `vertex_label_box` is the real work);
`simple_svg_renderer.py` ~L367–410 (the placement to factor out). Verify the same
way 3a did: full §3.3 corpus surface green (the engine should keep labels clear; any
real overlap it produces is a finding, not a spurious failure). `docs/
EXACT_CORRESPONDENCE.md` Phase 3 has the 3a/3b/3c breakdown.

### Thread A — the exact-correspondence engine (`docs/EXACT_CORRESPONDENCE.md`)
*Delete the geometry proxy: a cut **is** its drawn curve; containment / crossing /
extents are exact facts about the literal picture; the browser is the client-side
arbiter; the logic stays coordinate-free.*

- **Phase 1 — exact cut containment — DONE** (`629a161`): `point_in_cut`/
  `bounds_in_cut` test the rounded rectangle the renderer draws (corner radius), so
  the corner void is gone. Threaded through `eg_reader` + `correspondence_attestation`;
  zero regression (482 §3.3 tests).
- **Phase 2 — exact ligature crossing — DONE** (2026-06-10): `count_cut_crossings`
  takes the corner radius and counts crossings against the rounded rectangle the
  renderer draws (edges inset by the radius + four corner arcs —
  `_rounded_rect_secant_crossings`), so a ligature grazing a rounded-away corner
  reads *outside* (not a spurious cut entry). Attestation threads `cut_radius`; 457
  §3.3 tests green, new unit tests pin corner-graze / straddle / pass-through.
  *Still open:* chosen-crossing-point *placement* in the renderer (a routing concern,
  deferred).
- **Phase 3 — label/numeral extents.** Three sub-pieces:
  - **3a — label-box containment / no straddle — DONE** (2026-06-10):
    `presentation_ops.predicate_label_box` is the single source of truth (renderer
    draws from it; §3.3 tests it). A predicate's containment is its drawn label box —
    wholly inside ancestor cuts, wholly outside others (`box_intrudes_cut`), no
    straddle. Vertices stay dots. 521 §3.3 tests green corpus-wide.
  - **3b (next) — no improper occlusion.** §3.3 "marks don't overlap each other / cut
    lines illegibly"; layout treats label boxes as obstacles; covers constant/
    vertex-label placement.
  - **3c — clockwise placement as the order carrier** → numerals become a toggleable
    presentation-only annotation. The largest piece (hook placement + clockwise reader).
- **Phase 4 — DTO carries the cut polyline + browser `isPointInPath` hit-testing**
  (needed once cuts are human-drawn; unblocks the freeform canvas).

### Thread B — freeform composition + challenge mode (`docs/FREEFORM_COMPOSITION_AND_LEARNING.md`)
*Composition becomes freeform drawing (typed marks at free positions, no live EGI);
the picture is read into a sign only at gate ① (`read_drawing` → EGI → validity →
"what it says"). Then challenge mode: show a linear form, draw it freehand, grade
with `same_graph` + a legible EGI diff — correspondence learned by doing.*

Reader **de-risk is DONE** (`read_drawing` is sound on human geometry; gaps are only
snapping + validity, pinned in `tests/test_eg_reader.py::test_freeform_*`). Build
order: (1) snapping + fix-time validity pass (depends on Phase-1 exact containment,
now in); (2) the freeform drawing canvas (replace the composing-phase typed
`composition_ops` with place/drag/erase on a free `LayoutDTO`; live forms silent
until fix); (3) the legible EGI diff (align by label+role, diff area-tree +
incidence/order — reused by validity *and* challenge mode); (4) challenge mode over
the tomos corpus. Building (4) *is* the ongoing stress test of (1).

*Scope boundary (load-bearing): Arisbe reads **structured placement, not pixels**.
Reading a raster image (photo/scan/freehand) is deferred — likely a hand-off to
external AI that emits a structured placement into the same pipeline.*

### Ready-to-pick math tasks (independent, both unprotected)
- **∀x scaffold tactic** — `universal_generalization` in `src/derived_rules.py`,
  closing `∀x∀y∃z plus` (parametric totality already proven). Sound-by-construction
  recipe in `docs/UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md` §2–§3 (the dual-rule
  approach is provably unsound — use the scaffold).
- **Selection-driven `fold`** — `fold_selection` in `src/definitions.py`: iso-match a
  drawn body to a definition and contract it (sound gate = selection ≅ body, ports
  aligned). `docs/DEFINITION_NODE.md` "Open / next".

---

## Backlog (queued, lower priority)

- **Schema generator — shared ambient parameter** so `instance_of_schema` can
  generate the hand-written induction instance (φ threaded through all hole
  occurrences); assert `same_graph` to the hand-written one.
- **CG / ISO 24707 conformance write-up** for the definition node (marked-parameter
  syntax, contraction/expansion) — cite alongside the fixtures.
- **Corpus-import the math theories** — ZFC + Peirce 1881 as real UoDs (schemas +
  definitions store them finitely; the R7 horizon).
- **Gamma frontier** — predicate/property quantification, modality / the broken cut
  (the schema drew the map).
- **Publish-to-Organon as an unattested record** (composition spec §5.3) — a
  mode-contract question for the author; disposition today = vault (scratch) or Agon.
- **Agon depth** — semantic layer, auto-Grapheus, dynamic move set (deferred from V1).
- *(optional, PROTECTED)* widen `HeavyDotInsertionRule` to Dau's any-context rule.

---

## Recently shipped (newest first — detail in git / docs / memory)

- **2026-06-10** — Exact-correspondence **Phase 3a** (label-box containment): a
  predicate's containment is its drawn label box, not the anchor point
  (`predicate_label_box` single source of truth — renderer draws it, §3.3 tests it;
  `box_intrudes_cut` forbids straddling into non-ancestor cuts). 521 §3.3 green.
- **2026-06-10** — Exact-correspondence **Phase 2** (exact ligature crossing): the
  crossing test reads off the same rounded-rect boundary as Phase 1's containment
  (`count_cut_crossings` corner-radius-aware; `_rounded_rect_secant_crossings` /
  `_seg_arc_crossings`), closing the crossing-side of the corner void. 457 §3.3 green.
- **2026-06-10** — Exact-correspondence Phase 1 (exact cut containment) +
  architecture doc + scope boundary. Ergasterion review: keep-in-view camera;
  composition reconceived as **synchronic** (no `compose.*` steps; chain begins at
  gate ①) then as **freeform draw-then-read**; `read_drawing` de-risked.
  Docs: `EXACT_CORRESPONDENCE.md`, `FREEFORM_COMPOSITION_AND_LEARNING.md`,
  `DEVIN_SETUP.md`.
- **2026-06-09** — Cut-level `IT-`/`ERA` in the engine; **parametric totality of
  addition** assembled (∀Y∃z plus(x,Y,z)). Dau ∀x homework (scaffold tactic).
  Hole/schema §3.3 (a hole corresponds). Definition-node local reversible
  `expand_at`/`fold` (Borges-map guardrail). Composition workflow built (palette, two
  fixings, per-branch phases). Docs: `UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md`,
  `SCHEMA_HOLE_CORRESPONDENCE.md`, `DEFINITION_NODE.md`, `COMPOSITION_WORKFLOW_SPEC.md`.
- **2026-06-08/09** — Recursion fixtures + the induction arc; graph-with-holes schema
  node + definition layer (`schema.py`, `definitions.py`, `eg_splice.py`); math
  fixtures (ZFC + Peirce 1881). Organon import build: provenance/annotation layer, 3
  fixtures, corpus retrofit (`CORPUS_AND_IMPORT_MODEL.md`). Ontology import.
- **2026-06-06/07** — Tension layout engine (`TENSION_LAYOUT.md`); presentation-delta
  / style ladder (`PRESENTATION_DELTAS_AND_STYLE.md`); four-beat transformation
  grammar complete for all six rules (`TRANSFORMATION_WORKFLOW_SPEC.md`); Settle
  editing surface; NaturalLayout — "own the dimensionality".
- **2026-06-01/03** — All three web modes live (Organon / Ergasterion / Agon);
  runtime §3.3 correspondence attestation; the drawn→EG reader (`eg_reader`);
  Peirce visual-fidelity tiers (oval cuts, hand-drawn wobble, TikZ parity);
  import doorway (low-warrant) + export arc; `MANIFEST_AND_MEANING.md`,
  `CHAIN_OF_SEMIOSIS.md`.

---

## Notes on workflow

Primary development is local, on `main`; GitHub is backup, not a collaboration
surface. No PR ceremony (single developer, single site): commit to `main`, push to
back up. Feature branches are optional backup points, fast-forwarded into `main`
rather than merged via PR. The pre-commit quality gate runs the core suite; the full
suite (`uv run pytest tests/ -q`) is ~11 min. Protected core modules need
`touch .core_modification_authorized` (gitignored); the active threads above are all
unprotected.
