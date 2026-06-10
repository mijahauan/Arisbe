# Current Plan

**Last Updated**: 2026-06-10 — exact-correspondence **Phases 1, 2, 3a & 3b shipped**
(exact cut containment + exact ligature crossing + predicate label-box containment +
no improper occlusion); active arc = the exact-correspondence engine + freeform
composition. History below condensed 2026-06-10 (detail lives in git, the docs, and
memory).

---

## ▶ NEXT SESSION — start here

**Designated next task: label-aware ligature routing — the constructive half of
Phase 3b's deferred occlusion check.** (Thread A below; Phases 1, 2, 3a, 3b done.)
After that, Phase 3c (clockwise placement, the largest Phase-3 piece) and the
appetite-driven menu (Thread B, the math tasks) remain open.

### Label-aware ligature routing (the designated next task)
*Phase 3b shipped two occlusion checks green corpus-wide (text-on-text overlap;
vertex/constant label no-straddle). It **deferred** the third property — a line of
identity the label is **not** incident to running through its box — because that
check needs a constructive partner or it red-flags honest layouts. It is a genuine
occlusion: it found a real strike-through (a ligature drawn through the middle of
"Person") in the shared-vertex fan-in after IT+ on `roberts_domain_modeling`.*

**The task:** route non-incident ligatures *around* label boxes (the plan's
"layout/routing treat label boxes as obstacles"), then re-add the §3.3 check so the
two land together green. Routing must stay **sound** — a detour may not enter a
forbidden cut (the crossing-sequence attestation backstops it). The shared-vertex
fan-in (N predicates → one line-of-identity vertex, the lines crossing intervening
boxes) is the motivating case.

**Building blocks in hand (from 3b):** `presentation_ops.path_intersects_box` (the
obstacle test — Liang–Barsky clip + strict interior, so an edge graze reads legible),
`predicate_label_box` / cut-aware `vertex_label_box` (the box extents to avoid), and
`reroute_ligature` (regime-3 detour that already refuses boundary crossings). Entry
points: the layout/routing path (`elk_layout_engine` / `layout_service`) for the
detour; `correspondence_attestation.py` (re-add check #3 beside the two 3b checks —
the commented note there names it). Verify: full §3.3 corpus + transformation suite
green (the `roberts_domain_modeling` IT+ case is the regression to clear).

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
  - **3b — no improper occlusion — DONE** (2026-06-10): two §3.3 properties green
    corpus-wide — text-on-text overlap (`boxes_overlap`) and vertex/constant label
    no-straddle (cut-aware `vertex_label_box`, factored out of the renderer as the
    single source of truth, the way 3a factored `predicate_label_box`; renderer draws
    text centred in that box). Surfaced + fixed one real straddle ("Socrates" at a
    cut edge in `peirce_cp_4_394_man_mortal`). The third property (non-incident
    ligature through a box) is **deferred** with its constructive partner — see the
    designated next task above; `path_intersects_box` is the primitive in hand.
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

- **2026-06-10** — Exact-correspondence **Phase 3b** (no improper occlusion): two
  §3.3 properties green corpus-wide — text-on-text label overlap (`boxes_overlap`)
  and vertex/constant label no-straddle (cut-aware `vertex_label_box`, the renderer's
  placement factored into one source of truth; text drawn centred in the box). Fixed
  a real straddle ("Socrates" at a cut edge). The non-incident-ligature property is
  deferred with its routing partner (`path_intersects_box` primitive in hand).
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
