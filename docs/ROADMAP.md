# Arisbe — Roadmap

> **What this is.** One sequenced backlog, consolidating the "open tracks" and frontiers that were
> scattered across `CURRENT_PLAN.md` and the project memory. The top items carry near-term design
> intent; the tail is one-liners. Re-order and prune as priorities move — this is the focus lever, not
> a contract.
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [CAPABILITY_MAP.md](CAPABILITY_MAP.md) ·
> [GLOSSARY.md](GLOSSARY.md).
>
> *Last consolidated: 2026-06-27.* Items marked **(author decision)** need a call only the author can
> make; the rest are buildable once sequenced.

**Maturity of each item** mirrors [CAPABILITY_MAP.md](CAPABILITY_MAP.md): DESIGNED = specced not
built; FRONTIER = built but an edge remains; DECISION = a choice precedes any build.

---

## Near-term (with design intent)

### 1. Settle the "protected core" question — **✅ DECISION TAKEN & EXECUTED (2026-06-27)**

> **(a) keep + extend:** added the three §3.3 enforcers (`correspondence_attestation`, `presentation_ops`,
> `natural_layout`) — they now require authorization to change.
> **(b) trim:** removed the six EGIF/CGIF/CLIF parsers/generators — application-level I/O the calculus
> doesn't import; guarded by corpus round-trip tests in CI. **Net 17 → 14 modules** (the genuine calculus
> core). The thin ligature modules and `hierarchical_index` were *kept* — still load-bearing.
> **(c) replace with CODEOWNERS — declined:** CODEOWNERS routes PR reviews and does nothing in a solo,
> no-PR workflow; the protected set's inline comments now double as the bedrock note (it documents *and*
> enforces). The gate is kept because its real value here is an **AI tripwire** on the calculus —
> something neither a doc-note nor CODEOWNERS can provide.
> *(The corpus-wide `test_correspondence_*` suites were NOT added to the fast gate: minutes-long ELK
> layout, busts the <30s budget / 180s timeout; they run in full CI. A small in-gate smoke check is
> possible future work.)*

The re-audit (2026-06-27) that motivated the decision:

- **Count drift resolved.** The gate reports **17** modules, matching CLAUDE.md. No ghosts: every
  protected member has a live importer.
- **The mechanism does not guard the central invariant.** `correspondence_attestation.py` (28
  importers) and `presentation_ops.py` (31 importers) are the *most-imported* modules in `src/`, wired
  into the serving + save/load boundaries — yet **unprotected**. By the protection's own rationale
  (guard what enforces the invariant) they belong in the set. `natural_layout.py` is a weaker but
  defensible third.
- **The list disagrees with the real guard.** The substantive guard is the ~150-test core subset, not
  the name-match speed-bump. The fast gate does **not** currently include
  `test_correspondence_invariant` / `test_correspondence_attestation`, so the central invariant isn't
  in it.
- **Architectural distinction surfaced.** The math core (data model + six rules + closure/isomorphism
  validators) does **not** depend on the linear parsers/generators — those are application-level I/O
  (the one exception: `rule_interaction` parses EGIF *insert text* as a convenience). CGIF/CLIF are
  most clearly "I/O, not calculus."
- **Two thinly-held members:** `ligature_manipulation_rules` + `single_object_ligature_detector` are
  each held by a single non-test consumer (`chapter17_soundness_evaluation`).

**Options to choose among:**
- **(a) Keep + extend** — add `correspondence_attestation` + `presentation_ops` (+ maybe
  `natural_layout`) to the set; add the correspondence tests to the fast gate. Smallest change,
  closes the real gap.
- **(b) Keep + trim** — also drop the I/O parsers/generators (and/or the thin ligature modules) to
  leave a tight "calculus + invariant" core.
- **(c) Replace** — retire the name-match speed-bump for a CODEOWNERS-style **bedrock note** (names
  the non-negotiable modules + *why*) and let the test subset enforce. Least to maintain for a solo
  author; loses the `.core_modification_authorized` intentionality ritual.

Recommendation: at minimum **(a)** — the central invariant should not sit unguarded. The keep-vs-
replace question is a values call. *Outcome updates [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §3.*

### 2. Render-M UI — ground/legend panel + relevant-neighborhood M-render — **✅ DONE 2026-06-28**

Shipped in the Agon interpretation register, both parts, read-only chrome (M drawn, never asserted):
- **(d) the ground/legend** — `m_render.vocabulary_overlap`: the panel lists how G's and M's vocabularies
  meet (shared / G-only = the addressability gap / M-only = context beyond G), so a reader sees what the
  terms mean without leaving the board.
- **(c) the relevant-neighborhood M-render** — `m_render.m_fragment`: draws only the part of M the proposal
  *touches* — seed = M's sheet atoms whose relation/individual G uses, then one hop along the same
  individual / line of identity, budget-capped (~a handful); the rest is reported as a **horizon** ("+N
  more facts beyond view"). Materialized (forward-chained) facts render too.

New module `src/m_render.py` (pure, unit-testable); wired into `_interpret_payload` (`render_m` block) and
drawn in `agon.html` (legend + a small M-fragment board in the reading strip). Tests: `test_m_render.py`
(6), `test_agon_interpretation.py` (+3 route), `test_agon_e2e.py` (+1 browser). See
[THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) (recommendations (d) + (c)).

### 3. First-class reference / transclusion node — **increment 1 SHIPPED (2026-06-29) · increment 2 = the cross-UoD fork (author decision)**

> **Increment 1 (intra-UoD) shipped 2026-06-29, fully additive, core-protection CLEAN:** `src/reference_node.py`
> (a **Form-2 reference edge** + an overlay `ReferenceMark` + the `ReferenceResolver` seam with
> `DefinitionReferenceResolver`/`ChainReferenceResolver` + the `attest_reference` boundary hook + `reference_horizon`)
> and the **render glyph** in `simple_svg_renderer` (`reference_marks=` → a dashed spot + "+N beyond view" badge,
> default-off, no §3.3 change). Tests: `test_reference_node.py` (11) + `test_reference_glyph.py` (3); 95 corpus-wide
> §3.3/render tests confirm zero regression. See [REFERENCE_AND_TRANSCLUSION_NODE.md](REFERENCE_AND_TRANSCLUSION_NODE.md).
> **Increment 2 — cross-UoD — is the author decision below:** it is *not* "more reference" but a **use / mention**
> fork (DoR §4½/§7): **use** = governed import via the scroll `~[ B ~[ G ] ]` (B conditioned, LOW/attributed warrant,
> never the transparent double-cut co-assertion that would merge universes); **mention** = second-order naming, B
> drawn as the read-only "fourth thing" (`m_render`). **Paused here on the 2nd-order frontier (#13) by author choice.**

The open *architectural fork*. A node that references material defined elsewhere (a shared sub-graph,
a corpus graph) rather than copying it. High value for scale and for "scoping without recapitulation,"
but it **touches the protected core** (`egi_core_dau` + the §3.3 correspondence contract), so it is
not a safe additive build — it needs an author decision on whether to open the data model. See
[THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) recommendation (b) + §12's three decisions.

**De-risk done (2026-06-29):** before opening the core, the law a reference node must satisfy —
`RESOLVE ≡ INLINED-AND-ATTESTED` (§12 decision 3, an `attest_reference` analogous to `attest_overview`)
— is now **prototyped and proven on real graphs without any core change**:
`src/reference_resolution_check.py` + `tools/run_reference_resolution_check.py` +
`tests/test_reference_resolution_check.py` (11). Checks R1 resolve-equals-inline (`same_graph`),
R2 resolved-is-§3.3-attested, R3 recoverable (`fold`, where an inverse exists), R4 honest horizon
(unresolved named). PASS on definition references (Power Set, Infinity) **and** a transclusion
reference (cl-imports model); falsifiers bite. The key finding: `definitions.py` is *the reference
node in miniature* (defined edge → body elsewhere; `expand`/`fold` ⇒ resolve/refold), so the
remaining decision is **form + recoverability, not correctness of resolution** — see
[[project_reference_node_validation_harness]] / the memory note. The three §12 decisions (form:
element vs edge vs overlay · calculus-entry under level-0 doctrine · the attestation contract) are now
taken in a **design-of-record — [REFERENCE_AND_TRANSCLUSION_NODE.md](REFERENCE_AND_TRANSCLUSION_NODE.md)**:
Form 2 (a relation-shaped reference *edge* generalizing the definition node), **additive-first**
(increment 1 touches no protected module — generalize the resolver to corpus-UoD-by-name, reference
glyph, provenance in the overlay), with the **second-order-frontier invariant** banked (keep references
in the `splice`/port/expansion family so definition/schema/reference stay one mechanism). Awaiting the
author's go-ahead on increment 1.

### 4. Newcomer / EGIF-authoring on-ramp — **DONE (stages 1 + 2(a) + 2(b) all shipped 2026-06-28)**

The largest open UX arc (first flagged 2026-06-24, reaffirmed since). The author reframed it (2026-06-28):
a newcomer's journey is **Organon → Ergasterion → Agon**, and a proposed G is *picked from Organon* or
*composed in Ergasterion* before it reaches the arena — so the on-ramp is first about that **flow**, not a
from-scratch EGIF box. Audience: "both, in sequence" (carry-a-graph first, then notation/plain-English authoring).

- **✅ Stage 1 (2026-06-28):** the corpus is now a source of *proposals*, not only of models. Organon's single
  "Use in Agon" (which hardcoded the graph into the **M** slot) split into **"⚔ Propose in Agon"** (the graph
  → proposal G; the learner's path) + **"⚖ as model M"** (the prior behavior). Fixed a real bug: Agon's async
  worked-example default was clobbering an incoming `?proposal_egif`/`?model_egif`; the deliberate hand-off now
  wins. Ergasterion's "Send to Agon" mirrored the same two verbs (**⚔ Propose in Agon** / **⚖ as model M**) for
  full carry-a-graph symmetry. (`organon.html` + `ergasterion.html` + `agon.html` + 1 Organon E2E; core-protection
  CLEAN.)
- **✅ Stage 2(b) (2026-06-28):** the guided **"first graph" primer** — the in-app front door to the Field Guide
  ([FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md)) for the notation learner. New shared
  `web_viewer/js/primer.js` overlay (loaded on all three mode pages + the home door): the four marks in plain
  sight, the EGIF key table, and the **worked first graphs drawn by the real engine** (`GET /primer/examples` →
  `src/web_api/routes/primer.py` renders cat-on-mat / the human→mortal scroll / the empty cut through
  `generate_layout` so the picture↔proposition correspondence is *shown*, not described), the five drawable
  dragons each deep-linking into Ergasterion challenge mode (`?challenge=🐉N`, new param handler), and
  where-to-practice. Reached by a "New here? — start with the marks" link auto-injected into the shared mode-nav
  and a green "New here?" door on the home page. (`primer.py` + `primer.js` + `index/organon/ergasterion/agon.html`
  + `test_primer_route.py` (3) + `test_primer_e2e.py` (5); core-protection CLEAN, additive.)
- **✅ Stage 2(a) (2026-06-28):** the **plain-English authoring door** in Agon's setup — surfaced the
  already-built-but-UI-less **NL→logic front-end** (`POST /agon/propose-nl`, `src/nl_to_logic.py`). A
  "…or describe G in plain English" textarea + **✶ Translate to a proposal G** button posts the description
  (with the chosen M, whose signature hints the translation) → the page fills the Proposal G field from the
  drafted EGIF and shows the **reading** (`read as <FOL>`), the **vocabulary-miss** (terms M can't even address —
  "not even wrong") distinct from the **fact-miss** (the peel's verdict), and honest non-results (unmappable /
  malformed / translator-absent all return `parsed:false` with the reason, fail-soft, never an error). Purely
  additive (`agon.html` only) + 2 Agon E2E (network-stubbed for determinism); core-protection CLEAN. *LLM
  proposes, Arisbe disposes* — the LLM never touches the EGI, nothing is asserted (LOW warrant; earns warrant
  only by withstanding Agon).

---

## Backlog (one-liners)

5. **Context-reflex overlay docking** — ✅ **DONE 2026-06-28** (chose **auto-dim-on-overlap**). The
   reflex floated absolute top-left over every board and could occlude a left-heavy/frame-filling
   drawing. Now: when the open panel overlaps the drawn extent (`.svg-pan-zoom_viewport` rect) it
   recedes to a faint "Context" chip and its body becomes click-through, so the picture shows and
   nothing under it is unreachable; hover/focus restores it. Self-contained in
   `web_viewer/js/context-reflex.js` (all three modes); zero regression when there's no overlap.

6. **NL→logic fast-follows** — DESIGNED. (a) Multi-candidate disambiguation (G1,G2,G3 ranked *by
   verdict* — the distinctively-Peircean "disambiguate by interpretation, not parser confidence").
   (b) LOW-warrant `/import/admit` persistence of a tested proposal carrying its NL+LLM provenance.

7. **Endoporeutic Game deferred frontier** — PARTIAL→. Fuller semantic-layer integration into the
   contest UX and a dynamically-learned model M (the V1 arena is hot-seat). See
   [AUTOMATED_GRAPHEUS.md](AUTOMATED_GRAPHEUS.md).

8. **Tension layout frontier** — FRONTIER. Branch points, multiple threads, non-monotone ligatures
   (single collinear threads done, 10/11). See [TENSION_LAYOUT.md](TENSION_LAYOUT.md) §9–§10.

9. **Layout-perf frontier** — PARTIAL. Super-linear layout beyond ~127 axioms; the 130-cut COLORE
   density closure imports as data but stays undrawn. The display-side answer is the adaptive-scope /
   semantic-zoom "map app" lens. See [ADAPTIVE_SCOPE_VIEWER.md](ADAPTIVE_SCOPE_VIEWER.md).

10. **Diagram↔narration — next falsifications** — FRONTIER. The scorer is a prototype (8 chains/35
    steps). Next: a narration corpus (inter-narrator agreement), an LLM bridge (free narration), macro
    sub-step expansion (the D4 squash residual), metric-3 chapter-boundary on a branching DAG. See
    [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10. *Then consider surfacing in-view
    findings in the viewer.*

11. **Schema-drawing / §3.3 for the schema node** — FRONTIER. The graph-with-holes schema layer is
    built; drawing it and attesting its correspondence is the open edge (the math track is otherwise
    complete).

12. **Doctrine: Departure I reflexive-diagonal argument** — the one open joint held "at parity" in
    [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md). A standing intellectual thread, not a build.

---

## Chosen next — tidy-up tracks (author-set 2026-06-29, paused before reference-node increment 2)

The reference / transclusion node reached the **second-order frontier** (increment 1 shipped; increment 2 =
the cross-UoD use/mention fork, an author decision — #3). The author chose to **pause there** and tidy a
few things first:

14. **LaTeX export path** — for the **Peirce Edition Project** use case. **Phase 1 SHIPPED (2026-06-29).**
    A geometric Dau/Sowa TikZ exporter already existed; the new **authentic-Peirce** path reimplements the
    *function* of Jukka Nikulainen's `egpeirce.sty` (oval cuts, scrolls, heavy lines of identity, hooks,
    argument order) in **pure TikZ that compiles with plain pdflatex** — no PSTricks. Two improvements over
    egpeirce: it is **wedded to the EGI** (drives off the §3.3-attested `LayoutDTO`, so the printed picture
    provably denotes the graph, every element id traced in a comment) and it is **delta-faithful** ("export
    what you *adjusted* to see" — regime-3 nudges thread through, the PEP transcribe-then-tune path).
    Deliverables: `src/tex/arisbe-eg.sty` (a modern, hand-authorable semantic macro package — the egpeirce
    replacement), `src/peirce_latex.py` (the exporter), `peirce-tikz` format in `export_service`, and
    `tests/test_peirce_latex.py` (corpus totality+traceability over all 29 UoDs, reader-faithfulness on a
    representative subset + a falsifier, **actual pdflatex compilation** of a curated handful, the PEP delta
    path). **Phase 2 SHIPPED (2026-06-29), three of four items:** (a) the **iconic self-continuing scroll
    glyph** — `~[A ~[B]]` drawn as the outer cut with a downward neck that crosses itself and wraps the inner
    oval; opt-in (`scroll_glyph=`), **ink-only** so `cut_bounds`/§3.3/`read_drawing` are untouched (like the
    hand-drawn waver and bridges); (b) **worked-chain → multi-figure LaTeX document** (`export_peirce_chain` +
    `POST /export/chain` + `export_peirce_chain_document`) — a reasoning episode in print, one captioned figure
    per step; (c) **HTTP route deltas** — `ExportRequest.deltas` + `scroll_glyph` thread regime-3 adjustments
    and the glyph through `/export`. (d) the **drawing→EGI learning loop** (`layout_learning.py`):
    `arrangement_deltas` recovers the regime-3 deltas between Arisbe's canonical layout and a human-drawn
    arrangement of the same EGI (the inverse of `apply_deltas`), and `generalize_arrangement` crystallises them
    onto untouched siblings via the existing style ladder — so a replica drawn in Peirce's hand teaches the
    Peirce-style spec. **#14 is now complete.** Only a thin UI surface remains optional (an Ergasterion route that
    feeds the freeform canvas's drawn DTO into the loop, and a session-export convenience route).

15. **Start-up guidance for new users — layered + tailored by expertise — ✅ DONE (2026-06-29).**
    [GETTING_STARTED.md](GETTING_STARTED.md): a written, role-aware on-ramp that assumes *no* math/logic
    background (a shared "five minutes" — run it, the three modes, your first graph, the *attest
    correspondence not truth* discipline), then **branches** to a door per reader — newcomer, **ontologist**,
    **logician**, **mathematician**, **Peirce scholar** — each with *what to read first / do first / your
    frontier*, and a one-screen map. Complements the shipped in-app primer / Field Guide (newcomer on-ramp #4)
    rather than restating; audience-layered the way `VISION_AND_SCOPE` / `GLOSSARY` already are. Linked from the
    spine front-matter + GLOSSARY reading order + CLAUDE.md.

16. **External-sources & import documentation — ✅ DONE (2026-06-29).**
    [EXTERNAL_SOURCES_AND_IMPORT.md](EXTERNAL_SOURCES_AND_IMPORT.md): the consolidating map of how outside
    information gets *in* — the low-warrant **floor** (attest correspondence, not truth; no fabricated
    citation), the **two families** (formal files: OWL/RDF/SUO-KIF/CLIF/COLORE → CLIF → EGI translators wrapped
    as `kind=ontology` UoDs, with the honest skip-report and function-relationalisation; human-read material:
    the `/import` linear-form doorway + NL→logic + the future reading desk), the **tool/module map**, the
    loop-closing *import-as-M* theorem query, and the forward edges. Pulls together what was scattered across
    [CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md), [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md),
    [IMPORT_EXPORT_FORMATS.md](IMPORT_EXPORT_FORMATS.md), the OWL/RDF importers, and `cl_import_resolver`.

---

## Long horizon — the named research frontier

13. **Second-order logic about the graphs themselves** — graphs of graphs, abstraction, predication of
    qualities. Explicitly named (in [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)) as *the*
    real frontier — **not** modal marks, **not** a Gamma tincture. Toe-in-the-water already exists:
    the φ-hole / schema node (`schema.py`) and the math fixtures track. This is the direction Arisbe
    grows *toward*, once the near-term spine is settled. **Mapped (2026-07-08) in
    [SECOND_ORDER_FRONTIER.md](SECOND_ORDER_FRONTIER.md):** how far Peirce's Gamma-as-second-order
    leads, where his manuscripts trail off (comprehension / paradox control), and the governing rule
    that the crossing must be *drawn* (§3.3 one order up) — with a recommended sortal layer completing
    Peirce's own tinctures, and the departure marked. **Prep begun (2026-07-10) — the frontier
    de-risked the way increment 1 was:** the correspondence contract one order up is written
    ([SECOND_ORDER_CORRESPONDENCE_CONTRACT.md](SECOND_ORDER_CORRESPONDENCE_CONTRACT.md), P1–P5 + the
    law S1–S4), and a checker runs it on candidate quotations *without touching the protected core*
    (`src/second_order_check.py` + `tests/test_second_order_check.py`, falsifiers biting; the paradox
    floor S1 = dragon 9 drawn as an enclosure rule). What remains — the *crossing* — is two author
    decisions: **which comprehension floor**, and **how much to open the core** (overlay-forever vs.
    a native graph-valued node + a sort-reader that recovers S3 off the drawing).

---

*Discharged tracks (for the record):* the freeform composition arc (steps 1–4); fold-to-define
(build A); the warrant-gradient / context-reflex / correspondence-chord / dragons UX threads; the
FOLIO/DLCore coverage levers; the OWL/RDF import breadth; the modality-without-Gamma and level-zero
doctrine passes; the web-presentation fidelity audit (2026-06-26). Full history lives in
`CURRENT_PLAN.md` and the project memory.
