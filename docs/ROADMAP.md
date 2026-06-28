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

### 3. First-class reference / transclusion node — **DESIGNED · (author decision)**

The open *architectural fork*. A node that references material defined elsewhere (a shared sub-graph,
a corpus graph) rather than copying it. High value for scale and for "scoping without recapitulation,"
but it **touches the protected core** (`egi_core_dau` + the §3.3 correspondence contract), so it is
not a safe additive build — it needs an author decision on whether to open the data model. See
[THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) recommendation (b).

### 4. Newcomer / EGIF-authoring on-ramp — **PARTIAL (stage 1 + stage 2(b) shipped 2026-06-28; only 2(a) plain-English door remains)**

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
- **Stage 2(a) (open):** Surface the already-built-but-UI-less **NL→logic front-end** (`POST /agon/propose-nl`,
  `src/nl_to_logic.py` — plain English → drawn candidate G, with the vocab-miss / fact-miss split) as a "describe
  it in plain English" door in Agon — the plain-English authoring half of stage 2.

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

## Long horizon — the named research frontier

13. **Second-order logic about the graphs themselves** — graphs of graphs, abstraction, predication of
    qualities. Explicitly named (in [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)) as *the*
    real frontier — **not** modal marks, **not** a Gamma tincture. Toe-in-the-water already exists:
    the φ-hole / schema node (`schema.py`) and the math fixtures track. This is the direction Arisbe
    grows *toward*, once the near-term spine is settled.

---

*Discharged tracks (for the record):* the freeform composition arc (steps 1–4); fold-to-define
(build A); the warrant-gradient / context-reflex / correspondence-chord / dragons UX threads; the
FOLIO/DLCore coverage levers; the OWL/RDF import breadth; the modality-without-Gamma and level-zero
doctrine passes; the web-presentation fidelity audit (2026-06-26). Full history lives in
`CURRENT_PLAN.md` and the project memory.
