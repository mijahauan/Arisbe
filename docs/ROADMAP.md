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

### 1. Settle the "protected core" question — **DECISION PARTLY TAKEN (2026-06-27)**

> **✅ Done — option (a) "keep + extend":** `correspondence_attestation.py`, `presentation_ops.py`, and
> `natural_layout.py` added to the protected set (now **20** modules) — the §3.3 enforcers now require
> authorization to change. *(The corpus-wide `test_correspondence_*` suites were intentionally NOT added
> to the fast pre-commit gate: they generate ELK layouts and run for minutes, busting the gate's <30s
> budget / 180s timeout. They run in full CI; at commit time the invariant is guarded by the module
> protection. A small in-gate smoke check is possible future work.)*
> **Still open (author's values call):** whether to *also trim* the I/O parsers / thin ligature
> modules (option b), or eventually *replace* the name-match speed-bump with a CODEOWNERS-style bedrock
> note + tests-as-spec (option c). The findings that motivate those options remain below.

The re-audit (2026-06-27) produced these findings:

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

### 2. Render-M UI — ground/legend panel + relevant-neighborhood M-render — **DESIGNED**

The safe near-term build the in-view-set work teed up. Two parts, both *extend shipped code* (no core
change):
- **(d) a ground/legend panel** — surface the ambient model M's vocabulary/legend beside a proposal so
  a reader can see what the terms mean without leaving the board.
- **(c) a relevant-neighborhood M-render** — draw the *part of M the proposal touches* (vocabulary-
  bounded), not all of M, governed by the minimal-in-view rules (Relevance capped ~4 chunks).

Backed by `domain_oracle` + the overview/adaptive-scope machinery already in place. See
[THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) (recommendations (d) + (c)).

### 3. First-class reference / transclusion node — **DESIGNED · (author decision)**

The open *architectural fork*. A node that references material defined elsewhere (a shared sub-graph,
a corpus graph) rather than copying it. High value for scale and for "scoping without recapitulation,"
but it **touches the protected core** (`egi_core_dau` + the §3.3 correspondence contract), so it is
not a safe additive build — it needs an author decision on whether to open the data model. See
[THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) recommendation (b).

### 4. Newcomer / EGIF-authoring on-ramp — **DESIGNED (longstanding UX arc)**

The largest open UX arc (first flagged 2026-06-24, reaffirmed since). A non-logician can now *read* a
lit Agon verdict and land on a worked example, but still cannot easily *author* their own M/G — jargon
is thrown cold at `index.html` and the Agon/Ergasterion setup. Wants: gentle on-ramps, guided
authoring, a path from plain language to a well-formed graph. Partly enabled by the NL→logic
front-end (G) and challenge mode.

---

## Backlog (one-liners)

5. **Context-reflex overlay docking** — FRONTIER · *marked for reconsideration*. The reflex floats
   absolute top-left over every board (can occlude a left-heavy drawing). Revisit: dock-as-column vs
   auto-dim-on-overlap vs leave. (`web_viewer/js/context-reflex.js`, all three modes.)

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
