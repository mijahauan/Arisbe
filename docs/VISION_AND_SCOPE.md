# Arisbe — Vision & Scope

> **What this is.** A thin top-down orientation to the whole project, carried in **two strata**:
> the *instrument* (what Arisbe is, the one problem it exists to solve, what stands as bedrock and
> non-negotiable, who it serves, what falls in and out of scope) and the *program* (what the author
> proposes the instrument is for at the largest scale — voiced as a proposition, graded, open to
> refutation). It stays deliberately short and **links out** to the deep docs rather than restating
> them. Read this first; then follow the pointers.
>
> **Companion documents:** [CAPABILITY_MAP.md](CAPABILITY_MAP.md) (what works today, where it lives,
> what guards it) · [ROADMAP.md](ROADMAP.md) (what's next, in order) · [GLOSSARY.md](GLOSSARY.md)
> (terms + a reading order by audience). **New here?** [GETTING_STARTED.md](GETTING_STARTED.md) provides the
> layered, role-aware on-ramp (assumes no logic background, then branches by expertise). For the
> developer-facing module map and commands, see [../CLAUDE.md](../CLAUDE.md).
>
> *Last consolidated: 2026-07-02; restructured into two strata 2026-07-26.*

---

## The two strata, and the load-order

*(Author's ruling, 2026-07-26: the vision is **stratified, not replaced**.)*

- **Stratum I — the instrument** (§1–§7): what Arisbe is and the commitments that make it
  trustworthy — doing logic in pictures, Dau's bedrock, the correspondence check (§3.3 of
  [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md)), the three
  regimes, the earned-record discipline. Unchanged in substance.
- **Stratum II — the program** (§8): what the author proposes this instrument amounts to at
  the largest scale — voiced not as claims of the project but as **a proposition scribed
  into a wider game**, graded point by point.

**The load-order is a rule, not a mood: the instrument licenses the program, never the
reverse.** No Stratum II ambition may bend a Stratum I commitment. A reader who wants only a
rigorous Existential Graph environment may stop at the end of Stratum I and lose nothing.

---

## Stratum I — the instrument

## 1. What Arisbe is

Arisbe offers an environment for **doing logic in pictures, not pictures of logic** — Charles Sanders
Peirce's "moving pictures of thought" made operational. You draw and transform Existential Graphs
([EGs](GLOSSARY.md#eg)) directly; the picture *is* the reasoning, not an illustration of reasoning done elsewhere.

Peirce supplies the **aim**; Frithjof Dau's formalization stands as the **guarantor of correctness**.
Arisbe does not try to improve Peirce's calculus. It implements Dau's rigorous formalization of Alpha
(the cut, the sheet, juxtaposition) and Beta (the line of identity) faithfully, and builds outward from
that bedrock. (See [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) for the debt to Peirce and the
three places Arisbe consciously departs, each examined adversarially and surviving with amendment.)

The fundamental entity is **not a static diagram** but the **Universe of Discourse ([UoD](GLOSSARY.md#uod))**,
a *diachronic* (evolving) process of reasoning. A single EG amounts to a *synchronic* snapshot (a photograph)
within that larger film. See [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md).

---

## 2. The central problem — correspondence

The one engineering-and-research problem the whole codebase exists to solve:

> **The inerrant correspondence between an EG's linear written form and its graphical drawn form** —
> picture and proposition denoting the *same mathematical object* across every transformation, every
> layout regeneration, every user edit, every round-trip.

When the two come apart, the system has failed its central purpose — *not because the logic is wrong*
(Dau guarantees that) *but because the picture and the proposition have parted*. This contract stands
**stated, tested, and runtime-attested**:

- **Stated** — [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md), the central
  contract. Read it before touching anything that produces or consumes an `(EGI, drawing)` pair.
- **Tested** — `tests/test_correspondence_invariant.py` (the six correspondence test shapes (LINEAR_GRAPHICAL_CORRESPONDENCE §7) against the corpus).
- **Attested at runtime** — `correspondence_attestation.attest_correspondence(egi, dto)` raises
  `CorrespondenceViolation`; the web serving and save/load boundaries call it.

One discipline governs all of this: **correspondence is attested, never truth.** The correspondence check (§3.3) certifies that *this linear
form and this drawing denote the same graph*. That amounts to internal consistency, *not* a claim that either
holds true of the world. A correspondence failure signals not falsehood but *[voidness](GLOSSARY.md#voidness)* (Pauli's "not even
wrong"). Truth settles elsewhere — in use, in the Agon. See
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md).

A third correspondence has recently joined the doctrine: **diagram ↔ narration** (a narrated proof is
a chain of Discourse Representation Structures ([DRSs](GLOSSARY.md#drs)), and a DRS *is* a Beta EG). It serves as a measurement/validation lens; the UI
does not surface it yet — see [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10.

---

## 3. Bedrock — the non-negotiables

**No one** may trade these commitments away. Everything else remains negotiable engineering.

1. **Dau's calculus is the correctness [floor](GLOSSARY.md#floor) (the baseline that may not be gone under).** All six transformation rules (ERA, INS, IT+, IT−,
   DC+, DC−) run in full compliance, Beta-aware. The mathematical core test suite must
   always pass; a failing core test signals a real correctness defect, not test noise.

2. **The Existential Graph Instance ([EGI](GLOSSARY.md#egi)) is immutable.** State advances only by constructing a new graph (`.with_vertex()`,
   `.with_edge()`), never by mutation. Provenance therefore stays append-only, and the history forms a directed acyclic graph ([DAG](GLOSSARY.md#dag)).

3. **A step and its warrant are the same act.** You cannot make a change and *then* check it: the only
   way to advance the chain is to apply a rule, and a rule will not apply unless its preconditions
   hold. The move *is* its proof of soundness. See [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md).

4. **The correspondence invariant, scoped to three regimes** (below). Mandatory where things are
   asserted; suspended where things are merely entertained.

5. **We attest correspondence, never truth.** [Warrant](GLOSSARY.md#warrant) runs as a *gradient* (posited → derived → withstood)
   that rises by surviving challenge and can fall; "fact" names the defeasible status of the
   last-standing trajectory, never a glow in the ink. No mark bears actuality.

### The three regimes (the scope of the invariant)

| Regime | Where | Invariant |
|--------|-------|-----------|
| **1 — composition** | Ergasterion drafts (freeform drawing) | **Suspended on purpose** — the freedom to scramble and recombine is how inquiry probes. |
| **2 — asserted / canonical** | Agon, Organon, every rule application | **Mandatory, runtime-attested** (§3.3). |
| **3 — presentation-only** | restyling, re-layout, nudging | **Free, but preserved by construction** via the `presentation_ops` API (boundary crossings raise `Regime3Violation`). |

### The "protected core" mechanism — and an open decision

A pre-commit guard (`tools/core_protection_system.py`) blocks edits to **17 named modules** unless
`.core_modification_authorized` is present, coupled to "the math core suite must pass." It serves as
a deliberate authorization speed-bump, guarding Dau's formalization from inadvertent change.

A re-audit this pass (2026-06-27) found, and the author then acted:
- The "16 vs 17" count drift the prior handoff worried about was **already reconciled** — the report
  prints the full set, matching CLAUDE.md. No ghosts remain: every protected member has a live importer.
- **The mechanism did not guard the central invariant.** `correspondence_attestation.py` and
  `presentation_ops.py` *enforce* the correspondence the protection exists to defend, and they rank as
  the two **most-imported** modules in `src/` (28 and 31 importers) — yet they stood **unprotected**.
- The real guard lies in the **core test subset** (the fast gate), not the name-match speed-bump.

→ **Decision taken (2026-06-27):** *(a, "keep + extend")* the author **added**
`correspondence_attestation.py`, `presentation_ops.py`, and `natural_layout.py` to the protected set — so
the §3.3 enforcers now require authorization to change; *(b, "trim")* he **removed** the six
EGIF/CGIF/CLIF parsers/generators as application-level I/O the calculus doesn't import (corpus round-trip
tests in CI guard them instead). Net **17 → 14** modules, now the genuine calculus core. *(c, "replace
with a CODEOWNERS-style note") he declined:* CODEOWNERS routes PR reviews and would not fire in a solo, no-PR workflow — instead
the protected set's inline comments now **double as the bedrock note**, one artifact that both documents
*and* enforces. We keep the pre-commit gate because its real job in an AI-assisted solo workflow — making
an inadvertent edit to the calculus impossible to miss — is one neither a doc-note nor CODEOWNERS can do.
*(The corpus-wide `test_correspondence_*` suites stayed **out** of the fast gate: minutes-long, far
past its <30s budget; they run in CI, and the module protection guards the invariant at commit
time.)* See [ROADMAP.md](ROADMAP.md) #1.

---

## 4. Who it is for

Condensed personas (the fuller narrative lives in [ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) and
[ARISBE_FOR_SCHOLARS.md](ARISBE_FOR_SCHOLARS.md)):

- **The teacher** — walks a class through a proof in **Organon** (read-only archive), stepping the
  chain of semiosis with per-move rule + narration.
- **The student** — composes freehand in **Ergasterion** (workshop): draw marks, fix them into a
  graph, practice transformations, and learn correspondence by being graded against a target
  (challenge mode).
- **The researcher / domain expert** — contests a claim in **Agon**: pick a model M, [peel](GLOSSARY.md#peel) (reading it from the outside in against the model) a
  proposition G against it, get a verdict + witness/counterexample, or ask "in what domain does G
  hold?" (the inverse pivot).
- **The logician** — round-trips a form across modes and across four linear notations (Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)) / Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)) /
  Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)) / First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl))), trusting that the same proposition stays recognizable everywhere.
- **The scholar** — transcribes a historical graph with provenance, faithful to a community across
  history rather than cured into one consistent whole.

---

## 5. Scope

### In scope (and shipped — see [CAPABILITY_MAP.md](CAPABILITY_MAP.md))
Alpha + Beta EGs in Dau's formalization; the six transformation rules; the diachronic UoD + branching
DAG history; four round-tripped linear formats; the correspondence machinery (coordinate-free layout,
§3.3 attestation, regime-3 presentation algebra, drawn→EG reading); the three web modes; freeform
draw-then-read composition; the [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game (contest + interpretation registers); ontology/Web Ontology Language ([OWL](GLOSSARY.md#owl))/
Resource Description Framework ([RDF](GLOSSARY.md#rdf)) import as a *bridge*; an NL→logic front-end where "the LLM proposes, Arisbe disposes"; the *automated* Endoporeutic Game — the game played autonomously (LLM roles argue, the calculus decides) against live external sources (Wikidata), with the model M revising through play (see [CAPABILITY_MAP.md](CAPABILITY_MAP.md) §H).

### Out of scope — deliberate, with reasons
- **Gamma as a *modal* extension.** Not a problem Arisbe needs to solve: the diachronic DAG (worlds =
  sheets, accessibility = legal transition) *is* the drawn Kripke frame, so □/◇ become ordinary Beta
  quantifiers drawn rather than hidden. The **real** frontier lies in *second-order logic about the graphs
  themselves*, not modal marks. See [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md).
- **Reading a raster image** (photo/scan/hand-drawn ink → EGI). The hard inverse problem, explicitly
  deferred. (Note: reading a *structured* freeform drawing — typed marks on the canvas — **is** in
  scope and shipped; only pixels stay out.) See [EXACT_CORRESPONDENCE.md](EXACT_CORRESPONDENCE.md).
- **The Qt desktop GUI.** We archived it to `archive/qt-gui-2025/` (May 2026); the web app now serves as
  the canonical UI.

### Deferred — wanted, not yet built
Manchester OWL syntax (no maintained Python parser); the tropism's **musement pole** and
horizon-as-register (the irritation pole — the warm-set re-poll — shipped 2026-07-02 as
`tropism.py`; live run 3 pending); Gamma *[tinctures](GLOSSARY.md#tincture)* (Peirce's Gamma colourings) as a
non-load-bearing map symbol (channels reserved, forward-compatible by construction); the layout-perf
frontier for very large ontologies. These live in [ROADMAP.md](ROADMAP.md).

### When to reach for something else — the honest anti-pitch

Arisbe offers a first-order diagrammatic logic environment whose distinctive value lies in *the
picture being the logic* — an inerrant, runtime-attested correspondence between a drawn
graph and its meaning, over a diachronic model that revises under dialogue and evidence. It
is deliberately **not** a general proof assistant or a production reasoner; honest
scoping serves an adopter better than a broad claim:

- **For dependent types, higher-order mathematics, or large automated proof** (mathlib-scale
  formalization, tactic/hammer automation, a machine-checked archive): use **Lean/mathlib,
  Coq/Rocq, or Isabelle**. Arisbe's calculus is Alpha+Beta = first-order logic with identity;
  it offers legibility and a gentle two-rule symmetry, not expressive reach or proof search.
- **For temporal specification and bounded model-finding with counterexample traces**
  (protocols, concurrency, invariants over state): use **TLA+ or Alloy**. Arisbe's semantic
  game does open-world, three-valued model-*checking* over a Horn fragment, not temporal
  model-finding.
- **For large-scale ontology classification and DL reasoning** (10⁵–10⁶ axioms, full OWL 2
  DL, `unsatisfiable`-class detection at scale): use a **production reasoner via
  Protégé/ROBOT** (ELK, HermiT, Pellet). Arisbe imports a Horn-shaped fragment and reports
  what it cannot draw; its ceiling is thousands of atoms, not millions, and its layout layer
  is an authoring/explanation surface, not the reasoner.

What Arisbe uniquely offers *instead*, and where it serves as the right tool: a working notation in
which humans read and manipulate first-order logic **as pictures** with a machine-checked
guarantee that the picture cannot lie about its logic; a diachronic record where "fact" names
the defeasible last-standing trajectory and which attests every revision; and a dialogical
game in which a claim earns standing by withstanding challenge, played by humans or by LLMs
under an incorruptible mechanical referee. For teaching quantifier scope and negation, for
scholarly reproduction of Peirce's graphs, for auditing how a model's verdicts changed as
evidence arrived, and for giving an LLM agent a checkable diagrammatic verifier — reach for
Arisbe. (Several of these adjacencies stand as *bridges under consideration* rather than
walls — see [PROSPECTS_MULTIPERSPECTIVE.md](PROSPECTS_MULTIPERSPECTIVE.md), where the
proof-assistant and ontology communities ask for exactly this interoperation.)

---

## 6. Governing principles

The invariants a contributor should internalize before changing anything:

- **Immutability** — never mutate an EGI; construct a new one.
- **Correspondence-or-suspend** — assert nothing whose picture and proposition have not been
  attested to match; suspend the invariant only in regime-1 composition.
- **Attest, don't assert** — the system certifies correspondence, not truth.
- **Polarity in words, not hue** — Arisbe names a region's positive/negative polarity in words and
  never smuggles it in by colour (colour would invite reading actuality off the ink).
- **Warrant is a gradient** — posited / derived / withstood; it rises and falls; nothing stands exempt
  from being drawn back under a cut and challenged again.
- **The blank sheet is the only unconditioned thing** — and it asserts nothing. No contingent
  proposition sits unenclosed on the [recto](GLOSSARY.md#recto) (the asserted side of the sheet); every given enters under a cut, built from the blank by
  legal nesting. See [LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md).
- **Local is primary, GitHub is backup** — the corpus on disk holds the source of truth; pushes serve
  as backup, not collaboration.
- **No direct workshop → corpus route** — a graph reaches the attested corpus *only* by being tested
  through Agon, or as a style-only reprojection of an already-attested graph.

---

## 7. The system at a glance

```
Universe of Discourse (diachronic): State_n = (EGI_n, LayoutDeltas_n) + DAG history
        │
        ├── EGI  ── immutable RelationalGraphWithCuts (V, E, ν, ⊤, Cut, area, ρ)
        │          cut-containment (tree) + ligatures (W-partition)
        │
        ├── linear forms  ── EGIF · CGIF · CLIF · FOPL · JSON  (round-trip tested)
        │
        ├── correspondence layer ── natural_layout → ELK / tension → SVG; §3.3 attested
        │
        └── three modes (web app: src/web_api + src/web_viewer):
            Organon      "instrument" — read-only archive / browser / player
            Ergasterion  "workshop"   — compose, transform, challenge, define
            Agon         "contest"    — Endoporeutic Game: contest + interpretation
```

The full annotated module map, the commands, and the test inventory live in
[../CLAUDE.md](../CLAUDE.md). For the architecture deep-dives, read
[UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md) and
[DAG_HISTORY_ARCHITECTURE.md](DAG_HISTORY_ARCHITECTURE.md).

---

## Stratum II — the program

## 8. The program — a proposition scribed into the wider game

### The voice this stratum is written in

Stratum II does not stand as a platform of assertions. It is **a proposition scribed into the wider
Endoporeutic Game (EPG)** — the game in which Arisbe itself plays as the proposal, and the
traditions and communities named below stand as the other players. That framing entered on
2026-07-17 as a licensing device (the corollary "Arisbe itself as a proposition in the wider
EPG" — [BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md](BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md) §4,
walking through the door [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md)'s corollary
on the larger game deliberately left open). The author's ruling of 2026-07-26 promotes it to
**self-description**: *"this fundamentally describes my view of what we're doing."* The
consequences run through everything below:

- **The vision proposes; it does not assert.** The proposition holds to the same posture as
  any model M inside the loop: correspondence with the record, never truth.
- **The pre-registered priors and run logs are peels already played** — moves of this very
  game, on the record in `runs/`.
- **Refutation is a lawful, invited move** — a competent refutation would be the game
  *working*, not the game lost.
- **The grades (below) are the proposition's warrant annotations** — its earned, revisable
  standing, never a glow in the ink.
- **Publication and outreach are voicing the doubt to competent interlocutors** — not
  decoration but the only route to a judgment the project cannot make for itself, since
  judgment is objectivated, never owned
  ([THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §2(c)).

### The nexus thesis

**Arisbe proposes:** the operational Peirce core — *signs + sound transformation + earned
record* — supplies the common formal substrate that a family of twentieth-century traditions
lacked. Those traditions run as **tributaries**, partial views of Peirce's own program. Each
found a real phenomenon; each went without the substrate on which its finding could be
scribed, transformed soundly, and held to a record. It makes a strong thesis — which is
exactly why it comes voiced as a proposition and graded point by point rather than flattened
into one claim. The claim-by-claim examination lives in
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md), §"The graded concordance map".

### The five tributaries

1. **Conway and artificial life — open-endedness.** Where the Game of Life runs closed, fixed
   rules, Arisbe's sheet stays open and *negotiated*: a generation plays as a round of the game,
   and the only bound comes as selection from outside the membrane. *[machinery built-and-gated — the
   automated Agon loop and its live membranes,
   [AUTOMATED_MODEL_DEVELOPMENT.md](AUTOMATED_MODEL_DEVELOPMENT.md); the open-endedness
   reading itself queued-conjecture — not yet a measured claim.]*
2. **West's *Scale* — the scaling of knowledge systems.** West's scalar optimand (energy)
   becomes a vector (the knowledge measure), and one part of the question becomes measurable:
   the E-series (E1–E3c, closed 2026-07-27) ran against pre-registered priors — partitioning a
   maintenance workload across bounded units cut total upkeep ~5.2× under a size-charging cost
   meter, with the magnitude turning far more on the coordinator's scan discipline (a 25× spread
   at the largest size) than on the partition itself (`runs/WEST_E1_LOG.md`,
   `runs/WEST_E2_LOG.md`); self-partitioning converging
   to an interior granularity N=3 from all 36 starts, 19 distinct optima (21 known once
   E3c's symmetry-breaking rider added two more), one dominant cost
   family carrying 75% of the attractor mass, the balanced partition stranded in a
   positive-measure dear basin, not on a knife-edge (`runs/WEST_E3B_LOG.md`,
   `runs/WEST_E3C_LOG.md`). The units of that harness accumulate and forget without
   reasoning or exchanging content, so West's scaling law proper — a community's rate against
   its size — remains the open prospect, not a result
   ([WEST_IN_KYTE_PROGRAM.md](WEST_IN_KYTE_PROGRAM.md) §8). *[measured-with-priors —
   [WEST_IN_KYTE_PROGRAM.md](WEST_IN_KYTE_PROGRAM.md).]*
3. **Berger & Luckmann — objectivation across membranes.** What confronts participants as
   facticity is sustained only by participation; ratified into house doctrine as *judgment is
   objectivated, never owned* ([THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md)
   §2(c)). *[ratified-doctrine.]*
4. **The AlternativeSet unification.** Erotetics, truth maintenance, attention, and
   threat-response read as one structure, deliberation as holding alternatives, carried as
   an index over real chain steps, re-checkable forever. This tributary holds a special
   position among the five: it also forms the **joint** where the others meet (next subsection).
   *[built-and-gated — `alternative_index` / `alternative_trace` / `alternative_survey` under
   the standing corpus gate;
   [ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md).]*
5. **The deliberative-interval reading of agency.** Freedom read as the determined considering
   between branching-at-doubt and licensed resolution — the interval the diachronic record
   actually draws. *[ratified-doctrine — examined at
   [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md) Examination VI, Unit IV
   (2026-07-27), and ratified with four additions: irreducibility-as-ground; responsibility
   earned cumulatively by record, never by origin; the forecast/foretell guard; accounting
   sufficient-not-exhaustive. Its *measurement* remains ahead (the reflexive-run candidate).]*

### The unification joint — where the trains meet

The AlternativeSet arc closed (2026-07-26) as more than tributary №4 of the list above: it
forms the **joint at which six of the project's own trains of thought arrive as one structure**.
That unification — several strong trains not previously presented together — itself counts
among the program's principal findings:

- **Erotetics** — the question as a first-class object of the record (the interrogative
  {atom, denial} pair, born from a peel's own UNKNOWN);
- **The attention economy** — severity, cost, and decay priced on the *standing question*
  (`wants_from_alternatives`, the temperament dial);
- **Modality** — the ◇-contested branch survey: what the diachronic DAG's reachable futures
  disagree about becomes a held alternative
  ([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md));
- **The deliberative interval** — the interval's *considering* is exactly the trace and
  record ink (ratified at Examination VI, Unit IV);
- **Mention-ascent** — index-over-ink is the QuotationMark pattern applied to deliberation:
  the record *points* at gate-checked steps, holds nothing, and re-derives forever;
- **Hope** — Examination VI's addition: the Golden Rule's imagination is a
  hypothetical-kind alternative — *hope is the gap between the record and the
  entertained-better, held as action-guiding*
  ([THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §12(d)).

One structure carries all six because each amounts to a way of *holding alternatives against a
record*: what differs is only how a record **emerged** (a peel's UNKNOWN, a thin-spot survey,
a branch survey) and what settles it (licensed ink, never fiat). The law that guards it
(AS1–AS4: the index resolves; the trace recomputes; resolution is licensed; the horizon is
honest) serves as the deliberative organ's law in [THE_KYTOS.md](THE_KYTOS.md).

### The connective doctrine — synechism

Continuity does not stand as a sixth tributary; it serves as the **medium the five flow in** —
the reason one anatomy recurs across scales rather than five separate stories needing five
separate glues.
The full treatment (including the continuity ledger of the codebase's own discretizations)
lives in [SYNECHISM_AND_CONTINUITY.md](SYNECHISM_AND_CONTINUITY.md), §"The continuity ledger".

### The recurring unit — the kytos

The unit that recurs across the tributaries' scales — membrane, interior model, doubt-loop,
horizon, budget and rates, decay — bears the name **kytos**, the semiotic cell.
[THE_KYTOS.md](THE_KYTOS.md) gives its anatomy. At agentive levels it hosts a Peircean
quasi-mind.

### The grading discipline

Four grades, never flattened into one flat claim:

| Grade | Meaning |
|---|---|
| **built-and-gated** | shipped in the codebase, guarded by a standing test gate |
| **measured-with-priors** | run against pre-registered priors, verdicts on the record |
| **ratified-doctrine** | the author's ruled doctrine, carried in a design-of-record |
| **queued-conjecture** | named and held, deliberately not yet examined |

The grades serve as the proposition's **warrant annotations** — they record where each strand
currently stands, never what it is worth. The most exposed phrase in the program's vicinity — an
"operational model of consciousness / free will" — stands as **queued-conjecture** and remains
so; nothing in this stratum asserts it.

### The commens rung — examined, and what remains open

This section formerly held several threads queued: the four-doubts set (grown to six threads),
ethics-negotiated-in-the-commens, and free will with the predestination disposal. All of them
met **examination and ruling at the commens rung** (2026-07-27,
[ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md) Examination VI), and the rulings
folded where they belong: the marks doctrine, ethics-as-negotiated-apportionment, givenness
and the exit boundary, the Golden Rule membrane-poised, and the veil's two modes and grades
in [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §12; the
deliberative interval in the tributary grading above; levels-as-marks in
[SYNECHISM_AND_CONTINUITY.md](SYNECHISM_AND_CONTINUITY.md).

What stays open, named here per the grading discipline: THE_COMMENS §11's flagged verdicts 1, 2,
and 6 (the rulings touched them; none resolved them); the supermultitudinous frontier
(SYNECHISM_AND_CONTINUITY, untouched); the two **named-not-modeled determinants**
(identity/plausibility-structure maintenance, and the physical substrate —
[THE_KYTOS.md](THE_KYTOS.md) §5); and the queued **reflexive run** (a kytos modeling itself
— design sitting first). Folding any of these in now would count as a grade violation.

---

## 9. Trajectory

*(2026-07-26.)* The consolidation-era items this section used to narrate — the protected-core
question, render-M, the reference/transclusion node, the newcomer on-ramp — now stand discharged;
see [ROADMAP.md](ROADMAP.md)'s Discharged tail. The structural re-consolidation this section
previously announced as pending — splitting this document into two strata, the instrument and
the program — **landed 2026-07-26, in this rewrite**. Day-to-day sequencing lives under
ROADMAP's four workstreams (**Understand · Share · Run · Use**).

---

## 10. How this spine is maintained

This document and its two companions serve as a **consolidation** of material otherwise distributed
across `docs/`, `tests/`, and the session log. They stay thin by design:

- **VISION_AND_SCOPE** changes only when a *commitment* changes (a new non-negotiable, a scope
  decision, a principle).
- **Stratum II changes only when the author rules a program-level commitment** — a new
  tributary, a grade change, a change of voice. Only the author's ruling promotes a grade or
  adds a tributary.
- **CAPABILITY_MAP** functions as a living table — update the relevant row when a capability ships
  or its status changes.
- **ROADMAP** holds the working backlog — re-order and prune as priorities move.

`CURRENT_PLAN.md` remains the chronological session log / working handoff; this spine is the
*structural* view that the log does not aim to provide.
