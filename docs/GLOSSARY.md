# Arisbe — Glossary & Reading Order

> **What this is.** A compact glossary of the Peirce / Dau / Arisbe vocabulary the other spine
> documents assume, plus a suggested reading order by audience. For the full module/API map see
> [../CLAUDE.md](../CLAUDE.md).
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [CAPABILITY_MAP.md](CAPABILITY_MAP.md) ·
> [ROADMAP.md](ROADMAP.md).
>
> **Lost in the shorthand?** The **[Notation & reference numbers](#notation--reference-numbers)**
> section below decodes `§3.3`, `§7`, and the `Gx` / `Rx` / `Fⁿ` / `Pⁿ` tracking IDs — the one
> place the symbols are spelled out.

---

## Reading order by audience

**New user, just arriving (role-aware on-ramp):**
- [GETTING_STARTED.md](GETTING_STARTED.md) — assumes no logic background; a shared "five minutes" (run it,
  the three modes, your first graph), then a **door per reader**: newcomer / ontologist / logician /
  mathematician / Peirce scholar. Start here if you want to *use* Arisbe before reading the spine.

**New collaborator, orienting cold (≈30 min):**
1. [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) — what/why/scope/bedrock (this is the front door).
2. This glossary — pick up the vocabulary.
3. [FIDELITY_A_PLAIN_ACCOUNT.md](FIDELITY_A_PLAIN_ACCOUNT.md) — the project's stance, in plain language.
4. [CAPABILITY_MAP.md](CAPABILITY_MAP.md) — skim to see what exists.
5. [FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md) — the visual alphabet + common pitfalls.

**Contributor about to change code:**
1. [../CLAUDE.md](../CLAUDE.md) — module map, commands, invariants, test inventory.
2. [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) — **the central contract**;
   read before touching anything producing/consuming `(EGI, drawing)` pairs.
3. [CAPABILITY_MAP.md](CAPABILITY_MAP.md) — find the module + test home of what you're touching.
4. The relevant deep doc (each capability row points to one).

**Researcher / philosopher:**
1. [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) → [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) →
   [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) → [MEANING_BY_HISTORY.md](MEANING_BY_HISTORY.md).
2. [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) +
   [ADVERSARIAL_EXAMINATION.md](ADVERSARIAL_EXAMINATION.md) — the debt to Peirce and the examined departures.
3. [LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md),
   [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md),
   [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) — the doctrine frontier.

---

## Abbreviations

The acronyms the book uses, each expanded on first use and linked here. Headings are the
link targets (e.g. a first use renders *Existential Graph Instance ([EGI](GLOSSARY.md#egi))*).

### EG
**Existential Graph** — Peirce's diagrammatic logic; assertions drawn as marks on a sheet and
transformed as pictures. See [FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md).

### EGI
**Existential Graph Instance** — Dau's formal structure `(V, E, ν, ⊤, Cut, area, ρ)`; the immutable
data model. See *Terms → EGI* below and [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md).

### UoD
**Universe of Discourse** — the fundamental entity: a *diachronic* (evolving) reasoning process of
which an EGI is one synchronic frame. See [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md).

As a *standing concept* (not only the abbreviation): a UoD is the immediately
accessible / controllable / **attested internal model inside the membrane** — what an Arisbe
instance thinks *with*, the internalized complement of the un-possessed
[Commens](#commens). See [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §1.

### DAG
**Directed Acyclic Graph** — the shape of the branching transformation history. See
[DAG_HISTORY_ARCHITECTURE.md](DAG_HISTORY_ARCHITECTURE.md).

### EGIF
**Existential Graph Interchange Format** — Dau's linear notation for EGs. See
[IMPORT_EXPORT_FORMATS.md](IMPORT_EXPORT_FORMATS.md).

### CGIF
**Conceptual Graph Interchange Format** — the ISO/IEC 24707 conceptual-graph notation.

### CLIF
**Common Logic Interchange Format** — the Common Logic standard notation.

### FOPL
**First-Order Predicate Logic** — the symbolic logic Arisbe round-trips to/from EGs via Dau's
Φ / Ψ translation. See [CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION.md](CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION.md).
(*FOL* = First-Order Logic, the same fragment.)

### EPG
**Endoporeutic Game** — Peirce's outside-in dialogical reading of a graph, made operational in Agon.
See [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md).

### DRS
**Discourse Representation Structure** — a box of referents + conditions from Discourse
Representation Theory; in Arisbe a DRS *is* a Beta EG, the basis of the diagram↔narration check.
See [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10.

### DRT
**Discourse Representation Theory** — Kamp's dynamic semantics of discourse; the source of the
DRS and Centering notions Arisbe borrows for diagram↔narration.

### DTO
**Data Transfer Object** — the platform-independent `LayoutDTO` that carries a drawing between
the layout engines and the renderer. See [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md).

### ELK
**Eclipse Layout Kernel** — the cut-aware graph-layout engine that is Arisbe's default projection.

### DOI
**Degree of Interest** — the attention/scoping metric of the minimal in-view set (*not* "digital
object identifier"). See [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md).

### OWL
**Web Ontology Language** — a W3C ontology language; imported via OWL → CLIF → EGI. See
[EXTERNAL_SOURCES_AND_IMPORT.md](EXTERNAL_SOURCES_AND_IMPORT.md).

### RDF
**Resource Description Framework** — the W3C graph data model; rides the OWL import path.

### SUO-KIF
**Standard Upper Ontology Knowledge Interchange Format** — the SUMO dialect; ground axioms import to EGs.

### COLORE
**Common Logic Ontology Repository** — a Common-Logic ontology library; imports via its `cl-imports` closure.

### DL
**Description Logic** — the logic family of OWL/ontologies; its T-box axioms each map to an EG shape.

### T-box
**Terminological box** — the schema/vocabulary part of an ontology (class/role axioms), as opposed
to the **A-box** (assertional box, the individuals/facts).

### SMACOF
**Scaling by Majorizing a Complicated Function** — the stress-majorization method behind the
optional tension layout.

### the six transformation rules
**ERA** (erasure), **INS** (insertion), **IT+ / IT−** (iteration / deiteration), **DC+ / DC−**
(double-cut add / remove) — Dau's truth-preserving, Beta-aware rules; the correctness floor. See
[LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) and the transformation chapters.

---

## Notation & reference numbers

> **The one place the shorthand is decoded.** Arisbe's documents use three kinds of terse
> reference a newcomer can't be expected to track. Here is what each means and where its full
> description lives. **Rule of thumb: a bare "§N" always means a *section of the document you
> are reading*; a cross-document reference always names the document** — write
> "LINEAR_GRAPHICAL_CORRESPONDENCE §7", not a bare "§7".

### Named anchors — section numbers that are really *concepts*

A few section numbers are used so often they function as names. Prefer the name; the number is
just a bookmark into the anchor's home document.

| You'll see | Read it as | Full description |
|---|---|---|
| **§3.3** | *the correspondence check* — the runtime attestation that a drawing and its EGI denote the same object (`correspondence_attestation.attest_correspondence`); it attests **correspondence, not truth** | [LINEAR_GRAPHICAL_CORRESPONDENCE](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §3.3 |
| **§7** | *the six correspondence test shapes* — the properties any `(EGI, drawing)` pair must satisfy: totality/injectivity, containment, incidence + argument order, three-way identity, transformation invariance, regime-3 non-interference | [LINEAR_GRAPHICAL_CORRESPONDENCE](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §7 (realized in `test_correspondence_invariant.py`) |
| **Φ / Ψ** | Dau's bidirectional EGI ↔ first-order-logic translation | [CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION](CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION.md) |
| **the three regimes** | composition (1) · asserted/canonical (2) · presentation-only (3) | [VISION_AND_SCOPE](VISION_AND_SCOPE.md) §3 |

### Reference numbers — the project's own work-tracking IDs

These letter-number tags are **development tracking, not concepts**: they index findings, gaps,
and prospects in the lab-notebook documents. You never need them to understand Arisbe — but when
one appears, here is its register. **A letter is reused across registers** (both prospects and the
consolidate/adopt task track use "R"; both a run's priors and the correspondence contract use "P"),
so always read a tag in the document that introduces it.

| Tag | Meaning | Register |
|---|---|---|
| **G1, G2, …** | Documentation-gap numbers from the STORM cold-reader audit | [STORM_DOCS_AUDIT](STORM_DOCS_AUDIT.md) |
| **R1, R2, …** | Prospects — candidate future work | [PROSPECTS_MULTIPERSPECTIVE](PROSPECTS_MULTIPERSPECTIVE.md) |
| **D1, D2, …** | Disposals — how a gap was resolved | [STORM_DOCS_AUDIT](STORM_DOCS_AUDIT.md) |
| **F1, F2, … (e.g. F1⁷)** | Findings from a live run; the superscript is the run number | `runs/RUN_<n>_LOG.md` |
| **P1, P2, … (e.g. P2⁸)** | Pre-registered priors for a live run; superscript = run number. *(Separately, **P1–P5** in the correspondence contract are its five prover-agnostic properties.)* | `runs/RUN_<n>_LOG.md` · [CORRESPONDENCE_CONTRACT](CORRESPONDENCE_CONTRACT.md) |

### Common acronyms

The letter-acronyms (EGI, UoD, DTO, ELK, …) are in **[Abbreviations](#abbreviations)** just above.
**CI** = continuous integration (the automated test run that guards every change).

---

## Key terms

Concise, linkable entries for the specialized vocabulary the book uses (each introduced on first
use and linked here). The conceptual groupings below under *Terms* give fuller context.

### Peel
**Peel** — to read a graph *from the outside in* against a model M (the interpretation register's
core move), yielding a three-valued verdict plus a witness or counterexample. The term follows
**Sowa**: *"Graphist and Grapheus would take turns **peeling off** negations and mapping subgraphs
of g to M"* (Sowa 2011, *From Existential Graphs to Conceptual Graphs*). (Not, as far as we can
verify, Peirce's own word.) In the corpus every recorded verdict is an explicit, forever-recomputable
`PEEL` chain step — see [the explicit M-steps](#the-explicit-m-steps-peel-admit_to_m-retract_from_m-revise_m-and-the-episode-steps).

### Episode
**Episode** — one play of the Endoporeutic Game: *given a model M, then a proposition G* (peel →
decide). Previously called an "inning."

### Endoporeutic
**Endoporeutic** — Peirce's own word for reading a graph **from the outside in**, as a transaction
between a defender (Graphist) and a skeptic (Grapheus). Arisbe's Agon makes it operational.

### Dicisign and Argument
**Dicisign / Argument** — two of Peirce's classes of sign by the interpretant they call for (the
third trichotomy: **Rheme / Dicisign / Argument**). A **Dicisign** (or Dicent) asserts a
proposition — it is the kind of sign that is true or false. An **Argument** is a sign whose
interpretant presents it *as the conclusion of a lawful process*; it carries its own inferential
genesis. Two Existential Graphs identical in form assert the same Dicisign (proposition) but may be
different Arguments (reached by different derivations) — the distinction on which meaning-by-history
turns. See [MEANING_BY_HISTORY.md](MEANING_BY_HISTORY.md).

### Hypostatic abstraction
**Hypostatic abstraction** — Peirce's operation of turning a predicate into a subject ("hard" ⟶
"hardness"; a dyadic relation into a triadic one via an abstract intermediary), so that predicates
and propositions become objects one can quantify over. His route from first- to higher-order logic —
the ascent operator at the heart of the **[second-order frontier](SECOND_ORDER_FRONTIER.md)** —
realized in miniature and *reversibly* by `definitions.py` (a defined relation names a graph and
unfolds back). Widely read as an early anticipation of category theory.

### Reification
**Reification** (Berger & Luckmann, *The Social Construction of Reality*, 1966) — treating a
humanly produced, history-bound product as if it were a natural, given, authorless fact, forgetting
its genesis; made easy by **sedimentation** (long use effaces a meaning's path-bound origin). In
Arisbe the guarded-against case is *reifying a history*: lifting a telos a derivation-path merely
*implies* out of the diachronic record and scribing it on the blank sheet as an earned assertion —
the field guide's [dragon 9](FIELD_GUIDE_AND_DRAGONS.md). See [MEANING_BY_HISTORY.md](MEANING_BY_HISTORY.md).

### Agonothetes
**Agonothetes** (ἀγωνοθέτης, "organizer of the contest") — the game's **interpretant**: not a third
player but the function that turns a true/false outcome into an act of inquiry (a theorem
registered, a model revised, a hypothesis held).

### Scroll
**Scroll** — a nested double cut `~[ M ~[ P ] ]` reading "P given M"; the Alpha home of conditional
assertion.

### Kytos (the semiotic cell)
**Kytos** (κύτος, *vessel* — the root of "cell"; plural **kytē** (κύτη, third-declension neuter — as pathos → pathē)) — the recurring unit of
doubt-driven semiosis: a membrane (which both bounds and animates), an interior model M, the
doubt→probe→test→dispose→decay loop, a horizon of the not-yet-legible, and a budget with its
rates. One anatomy at many scales — atom, law, model, mechanism, project, person-model,
community — with the knowledge measure transporting across them. What a kytos hosts at
agentive levels is a **quasi-mind** (Peirce's *Prolegomena* term for any sufficiently unified
sign-system); the instructive contrast is Leibniz's windowless monad — the kytos is all
windows. Ratified 2026-07-19; design-of-record
[THE_KYTOS.md](THE_KYTOS.md). Umwelt / functional circle / Markov blanket remain
*concordances* (cited neighbors), never house vocabulary.

### World-scroll
**World-scroll** — the standing structure in which a domain model M resides: since the second
relocation (M-residence memo §9, ratified and built 2026-07-16), `~[ ~[cell] … ~[ ] ]` — M's
elements live in **cut-wrapped cells at level 2** (evenly-enclosed, *positive*: the register of
in-context agreement), siblings of at least one **empty cut** (the hold, and any scars — one kind),
whose presence keeps the outer negation vacuously true, so the standing structure asserts nothing.
Under the validity discipline nothing contingent stands at depth 0 — the sheet is the world's
level, carrying only what the calculus itself delivers. The change-asymmetry sits at the
fallibilist pole: **enlarging** M is one licensed **INS of a closed cell** into W (each admitted
batch its own cell); **retracting** — whether refutation-driven or disuse-fading, distinguished
only by the recorded disposition — is one licensed **ERA inside a cell** (erasure is sound at even
depth), the emptied husk standing as a visible scar; **full replacement** (the rare case — a husk
is a cut at odd depth, not ERA-licensed) remains the world-withdrawal triple ERA · DC+ · INS, the
DAG keeping the withdrawn world. Recognition is structural, never annotational
(`src/world_scroll.py`: one sheet cut whose children are all cuts, at least one empty); every
reader reaches M's content through `m_view` (the union of the cells' interiors; identity for a
bare sheet-level fixture). See
[M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md](M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md) §9.

### Commens
**Commens** (Peirce, the 1906 Lady Welby letters — "all that is, and must be, well understood
between utterer and interpreter" for a sign to function) — the between/outside/before/after that
makes communication possible without being possessed: interacted-with, never internalized, and
**not an Arisbe structure** (it is *not* the attested corpus — that is the internalized
[UoD](#uod)). A **social construct** in Berger & Luckmann's sense: real-for-participants (it
confronts them with facticity, exceeds any one of them) yet **sustained only by participation** —
*if we do not participate, it disappears* — so it is open *and precarious*, continuously
reproduced rather than pre-given or timeless. Regulative, never to be operationalized. Genuine
institutionalization and the commens are **community-level emergents** (a change in kind, not
degree, above the single instance). See
[THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md),
[World-scroll](#world-scroll), [Kytos](#kytos-the-semiotic-cell),
[Mention-ascent](#mention-ascent).

### The explicit M-steps: PEEL, ADMIT_TO_M, RETRACT_FROM_M, REVISE_M, and the episode steps
**PEEL / ADMIT_TO_M / RETRACT_FROM_M / REVISE_M / ENTERTAIN / DISCHARGE_TO_M / ABANDON_EPISODE**
— the explicit chain-step vocabulary (`src/m_steps.py`) by which the corpus (and, since sweep #2,
the live loops) records verdicts and M-modification, each step *earned at record time* (the
transform runs real Dau rules or a real evaluation; the parameters say what happened, never merely
assert it). **PEEL** records a peel actually run against the current state — proposal,
three-valued verdict, witness/counterexample — recomputable forever. **ADMIT_TO_M** is
enlargement: a genuine INS of a closed cell into the [world-scroll](#world-scroll), the warrant
riding on the step, not the ink. **RETRACT_FROM_M** is retraction: one licensed ERA inside a
cell, its `flavor` field distinguishing surprise from entropy (`pruned:disuse` — the *faded*
tense-flavor). **REVISE_M** is the challenge composite (ONE step: the executed ERA of the
impugned law + the INS of the anomaly's cell) or, in its rare world-withdrawal form, the executed
ERA · DC+ · INS triple. The **episode steps** (M-residence memo §10) conduct an EPG episode
wholly in ink: **ENTERTAIN** builds "if M then P" inside the agreed context (DC+ · IT+ of M ·
INS of `~[P]`, the empty inner cut — the *vacuity rider* — keeping the exhibit forceless; the
episode theorem: the DC+ must land in an even context at depth ≥ 2); **DISCHARGE_TO_M** is drawn
modus ponens (IT− of the premise copies · IT− of the rider against the standing hold · DC− — P
lands in M *derived, never inserted*), and under ruling (b) it **refuses to record without a
confirming PEEL to cite** (the ⊥-door makes the licence unconditional, so the earning rides on
the record); **ABANDON_EPISODE** is one licensed ERA of the whole exhibit. Guarded corpus-wide by
the standing gate `tests/test_corpus_polarity_discipline.py`, which recomputes every recorded
verdict, re-asserts every discharge citation, and refuses any silent M-change (the m_view
tripwire).

### Scribe
**Scribe** (verb) — to draw/assert a graph on the sheet (Peirce's term for inscribing a graph).

### Recto
**Recto** — the asserted face of the sheet (an evenly-enclosed, *positive* area). Its complement is
the **verso**.

### Verso
**Verso** — the negated face (an oddly-enclosed, *negative* area), one cut deeper than the recto.

### Tincture
**Tincture** — Peirce's Gamma colourings of areas (his modal/higher-order experiments). Arisbe
treats Gamma-as-modality as out of scope — and demonstrates the modal work carried instead by
the diachronic branching history, on Peirce's own figures
([GAMMA_DEMONSTRATIONS.md](GAMMA_DEMONSTRATIONS.md)).

### Mention-ascent
**Mention-ascent** (this term **retires the earlier name "the second-order crossing"**) —
Arisbe's scoped slice of Peirce's **Gamma**: the step from *using* a graph (scribing it, with
assertoric force) to *mentioning* one (naming it as an object another graph can talk about) —
"graphs about graphs." It is realized by a single **B-min quotation device**: a
proposition-sorted **name** drawn in the host, tied to a graph-valued **oval** holding the quoted
ink (`egi_core_dau` `sort`/`quotation` maps; `quotation_overlay.py`; the oval is *mention*, never
a negation). It is deliberately **not all of Gamma** — historical Gamma also bundles modality,
which Arisbe carries *without* any modal mark, read off the diachronic branching DAG (see
[Tincture](#tincture), [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)). The move is
**conservative over the Dau core**: the quotation layer licenses no new first-order theorem (the
A3 gate, `tests/test_second_order_conservativity.py`) — a quoted law is present *without force*
("asserted derives, quoted doesn't"). Its faithful shape is Peircean:
[hypostatic abstraction](#hypostatic-abstraction) turns a predicate into a subject, and in an EG
a subject is a line of identity — so the sorted name (the subject) tied to its oval (the exhibit)
reads truer than "the graph *is* the node." **Why the step is genuine, yet optional.** Dau's own
system-extensions — constants and functions as labels, relation-graph *query* markers
(*Mathematical Logic with Diagrams*, Ch. 23–25) — all stay **first-order** (Arisbe already
carries the constants case verbatim, as `rho`; a function's content lives as uniqueness laws in a
model M), so mention-ascent is the first move genuinely *past* them; and Ch. 26's reduction
thesis (teridentity plus the algebraic operations construct every finitary relation) is the
first-order result that makes the higher-order step **optional for expressiveness** — only
*iconicity*, not power, motivates going further. The open **reduction theorem** (Q-A, in the vein
of Peirce's [teridentity](#teridentity) result) would prove the dual: every stratified mention of
arbitrary depth composes from this one cut→vertex device. See
[SECOND_ORDER_CORE_OPENING.md](SECOND_ORDER_CORE_OPENING.md),
[CROSSING_DECISION_BRIEFS.md](CROSSING_DECISION_BRIEFS.md).

### Broken cut
**Broken cut** — Peirce's 1903 Gamma mark (a cut with "many little interruptions"): the graph on
its area is *contingent* — ◇¬. Arisbe draws no such mark; the same four modal statuses are read
off the branching derivation DAG (the `broken_cut_square` exemplar,
[GAMMA_DEMONSTRATIONS.md](GAMMA_DEMONSTRATIONS.md) §2).

### Would-be / de inesse
**Would-be** vs **de inesse** — Peirce's two readings of a conditional (*Prolegomena* 1906, CP
4.546): *de inesse* is the material conditional on one sheet ("too easily true" — it holds if the
antecedent merely never occurs); the *would-be* is the strict reading, a habit holding across
every course of experience. In Arisbe the would-be is □G over a branching DAG of courses (the
`would_be_courses` exemplar, [GAMMA_DEMONSTRATIONS.md](GAMMA_DEMONSTRATIONS.md) §4).

### Teridentity
**Teridentity** — a three-way point of identity: a branch where one line of identity meets two
others (three "hooks" at one spot).

### Floor
**Floor** — a baseline that may not be gone under. The *correctness floor* (Dau's calculus); the
*low-warrant floor* every import starts at; the *philosophical floor* (attest correspondence, not
truth).

### Membrane
**Membrane** — the boundary where the sheet meets the world — the one place error is corrected
(the Popperian image behind the low-warrant import discipline). In the *automated* Endoporeutic
Game the membrane is a concrete component: the proposer that carries outside claims into the
game, one per round. A **closed** membrane replays a fixed pool; an **open** membrane admits the
world — *raise-only* (dated discourse, with no way to check it against the world), *raise-and-resolve*
(predictions the world later settles), and *wiki-dispute* (edit wars ending in an editorial
resolution). See [AUTOMATED_ENDOPOREUTIC_GAME.md](AUTOMATED_ENDOPOREUTIC_GAME.md).

### Disposition
**Disposition** — the Agonothetes' ruling on what an episode's outcome *does to the record*: each
entry in the taxonomy (new_fact, generalization, challenge_to_M, redundancy, rejection, …) names a
structural move, and the model-revising subset carries its Peircean mode (induction / deduction /
abduction / convention). Nothing enters the model except under a disposition.

### Disuse-decay
**Disuse-decay** — the only bound on an unbounded sheet: a fact no round has re-delivered for a set
span is erased from the developing model M. **Atom-level** since 2026-07-03 (the affirmed rulebook:
the habit is the *fact* — `(place_of_birth Adam Cambridge)` — not the relation name, which is only
vocabulary; use = re-delivery, so one warm fact no longer keeps its name-siblings alive). Decay is
*not* evidence against a claim (it is excluded from durability statistics); it is the working-set
discipline that keeps a live run's per-round cost flat.

### Stickiness
**Stickiness** — whether a move survived to the end of a run: a generalization later relinquished
by play reads *not sticky* (durability evidence), while a fact erased by disuse-decay reads neither
sticky nor unsticky (no evidence either way). Stick-rates by resolution mechanism are how the game
learns *which kind of settling produces durable knowledge*.

### Poise
**Poise** — the automated game's health observable, read off windows of a run: engagement (still
taking the world in), settlement (dispositions stabilizing), absorption (stumbles recovered from).
Its failure poles are **rigidity** (nothing changes anything) and **thrash** (nothing settles).
Perspectival and comparative — never a target.

### Tropism
**Tropism** — the model's own state directing which sources to re-engage (empirically mandated by
live run 2, built 2026-07-02 as `tropism.py`): the **warm-set re-poll** revisits the entities
backing what M currently holds — decay-adjacent first — so a later denial can meet its
still-standing target. Passive ingestion never revisits, so without tropism the durability of
settled claims goes untested.

### Seam
**Seam** — the boundary between two Universes of Discourse, or the point where a reference/transclusion
crosses from one graph into another.

### Horizon
**Horizon** — what lies just beyond the part currently in view: open-world unknowns, or the part of a
model a graph does not touch — reported honestly, never silently dropped.

### Style ladder
**Style ladder** — how presentation is persisted: a default style → sparse hand-tuned exemplar
deltas → an extrapolated regularity crystallised onto untouched siblings.

### Warrant
**Warrant / standing** — a graph's epistemic status as a *gradient*: **posited** → **derived** →
**withstood**. Rises by surviving challenge; can fall. "Fact" = the last-standing trajectory, never
a property of the ink.

### Voidness
**Voidness** — the failure mode of an *integrity* (formation) breach: marks that embed no consistent
object at all — *"not even wrong"* (attributed to Wolfgang Pauli), as opposed to a graph that is
well-formed but false.

### Tomos
**Tomos** (Greek "volume") — the on-disk corpus of canonical EG examples (with EGIF/CGIF/CLIF/FOPL
variants) under `tomos/`; the source of truth and the round-trip test bed.

### Graphist
**Graphist** — the proposer's role in the Endoporeutic Game: the player who scribes a graph and
must defend it. In the automated game, the doubt-driven proposer. See
[ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md).

### Grapheus
**Grapheus** — the skeptic's role in the Endoporeutic Game: the authority for the model M who
contests the Graphist's proposal. Arisbe ships an automated Grapheus (minimax over the semantic
game). See [AUTOMATED_GRAPHEUS.md](AUTOMATED_GRAPHEUS.md).

### Horn rule
**Horn rule** — a law of the shape "if body then head" (`~[ B ~[ H ] ]`, range-restricted) that
forward-chaining can apply mechanically; the fragment of M that *materialization* turns into
plain facts so the syllogism works.

### Materialize
**Materialize** — forward-chain a model's Horn rules to their least fixed point, so a model
authored as *facts + rules* is testable as plain facts. A model is the facts; rules are a theory.

### Gate ① and gate ②
**Gate ① / gate ②** — the workshop's two one-way doors: gate ① *fixes the graph* (from clay to a
fixed meaning that changes only by the six rules); gate ② *fixes the chain* (the derivation is
complete and becomes read-only). Nothing passes either gate silently.

### Closure
**Closure (closed subgraph)** — a selection fit to be transformed as a unit: it contains every
element structurally inseparable from what was picked (a line of identity cannot be cut in half).
The rules act on closed selections only.

### Iteration and deiteration
**Iteration / deiteration** — the paired rules IT+ and IT−: iteration copies a subgraph into an
area nested inside its own; deiteration removes a copy that is governed by an identical original.

### Closed world
**Closed world** — reading a model as *asserted-complete*: what M does not assert is FALSE. The
open-world default instead reads a miss as UNKNOWN (an honest abstention). The Agon's
interpretation register offers both.

---

## Terms

### Peirce's Existential Graphs
- **Existential Graph (EG)** — Peirce's diagrammatic logic: assertions drawn as marks on a sheet, read
  and transformed as pictures. "Moving pictures of thought."
- **Sheet of assertion** — the blank surface; everything scribed on it is asserted. The **blank sheet**
  is the only unconditioned thing and asserts nothing (it withholds nothing → the empty conjunction =
  truth).
- **Cut** — a closed curve denoting negation; its interior is one level more deeply nested.
- **Polarity** — a region is *positive* (evenly enclosed) or *negative* (oddly enclosed). In Arisbe,
  polarity is named **in words, never by colour**.
- **Line of identity / ligature** — a heavy line asserting the identity of an individual; a **ligature**
  is a connected network of such lines (possibly crossing cuts).
- **Juxtaposition** — placing two graphs on the same area = conjunction.
- **Alpha / Beta / Gamma** — Peirce's three systems: **Alpha** = propositional (cut + juxtaposition);
  **Beta** = first-order (the line of identity); **Gamma** = his modal/higher-order experiments. Arisbe
  implements Alpha + Beta; it treats Gamma-as-modality as *out of scope* (the diachronic DAG already
  supplies the modal frame — see [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)).
- **Scroll** — a nested double-cut `cut[ M cut[ P ] ]` reading "P given M"; the Alpha home of
  conditional assertion.
- **Endoporeutic** — Peirce's own word for reading a graph **from the outside in**, as a transaction
  between a defender and a skeptic. Arisbe's Agon makes this operational.

### Dau's formalization
- **EGI (Existential Graph Instance)** — Dau's formal structure `(V, E, ν, ⊤, Cut, area, ρ)` carrying
  two co-resident graph structures over one element population: **cut-containment** (a tree) and
  **ligatures** (the W-partition, cutting across the hierarchy).
- **The six transformation rules** — ERA (erasure), INS (insertion), IT+/IT− (iteration /
  deiteration), DC+/DC− (double-cut add / remove). Truth-*preserving*, Beta-aware. The correctness floor.
- **Φ / Ψ** — Dau's bidirectional EGI ↔ FOPL translation (Chapter 18).

### Arisbe's architecture
- **UoD (Universe of Discourse)** — the fundamental entity: a *diachronic* (evolving) reasoning
  process. `State_n = (EGI_n, LayoutDeltas_n)`; history is a branching DAG.
- **Synchronic / diachronic** — a single EGI snapshot (synchronic, a photo) vs the evolving process
  (diachronic, the film).
- **The correspondence invariant** — picture and proposition denote the *same* mathematical object.
  Stated in [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md); §3.3 attests it at
  runtime. Attests **correspondence, not truth**.
- **The three regimes** — composition (1, invariant suspended), asserted/canonical (2, mandatory +
  attested), presentation-only (3, free but preserved by construction). See
  [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §3.
- **§3.3** — the section of the central contract specifying the runtime correspondence properties;
  also the name of the runtime check (`correspondence_attestation.attest_correspondence`).
- **The three modes** —
  - **Organon** ("instrument") — read-only archive / corpus browser / chain player.
  - **Ergasterion** ("workshop") — private editor; freeform draw-then-read composition; transformation
    practice; challenge mode; fold-to-define. Regime-1.
  - **Agon** ("contest") — the Endoporeutic Game arena: the *contest* register (hot-seat
    transformation game) and the *interpretation* register (given M, peel G).
- **Peel** — reading a graph outside-in against a model, the interpretation register's core move;
  yields a 3-valued Kleene verdict + witness/counterexample.
- **Oracle / M** — the ambient model. M is **queried, not held**: a thin `DomainOracle` answers
  `resolve`/`witness`/`match_atoms` against local EGIs (open-world).
- **Warrant / standing** — a graph's epistemic status as a *gradient*: **posited** ○ → **derived** ⛓
  → **withstood** ⚔. Rises by surviving challenge; can fall. "Fact" = the last-standing trajectory,
  never a property of the ink.
- **tomos / the corpus** — the on-disk library of 87+ canonical EG examples (with EGIF/CGIF/CLIF/FOPL
  variants) under `tomos/`; the source of truth and the round-trip test bed.
- **Regime-3 / presentation_ops** — the algebra of pure-appearance edits (move/reshape/reroute) that
  change the drawing but not the logic; boundary crossings raise `Regime3Violation`.
- **Protected core** — the 17 modules a pre-commit guard locks against inadvertent change (see
  [CAPABILITY_MAP.md](CAPABILITY_MAP.md) and [ROADMAP.md](ROADMAP.md) #1).
- **Dragon** — a "here be dragons" pitfall in [FIELD_GUIDE_AND_DRAGONS.md](FIELD_GUIDE_AND_DRAGONS.md);
  the drawable ones are challenge-mode targets.
