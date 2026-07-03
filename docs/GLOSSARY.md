# Arisbe — Glossary & Reading Order

> **What this is.** A compact glossary of the Peirce / Dau / Arisbe vocabulary the other spine
> documents assume, plus a suggested reading order by audience. For the full module/API map see
> [../CLAUDE.md](../CLAUDE.md).
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [CAPABILITY_MAP.md](CAPABILITY_MAP.md) ·
> [ROADMAP.md](ROADMAP.md).

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
   [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md).
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

## Key terms

Concise, linkable entries for the specialized vocabulary the book uses (each introduced on first
use and linked here). The conceptual groupings below under *Terms* give fuller context.

### Peel
**Peel** — to read a graph *from the outside in* against a model M (the interpretation register's
core move), yielding a three-valued verdict plus a witness or counterexample. The term follows
**Sowa**: *"Graphist and Grapheus would take turns **peeling off** negations and mapping subgraphs
of g to M"* (Sowa 2011, *From Existential Graphs to Conceptual Graphs*). (Not, as far as we can
verify, Peirce's own word.)

### Episode
**Episode** — one play of the Endoporeutic Game: *given a model M, then a proposition G* (peel →
decide). Previously called an "inning."

### Endoporeutic
**Endoporeutic** — Peirce's own word for reading a graph **from the outside in**, as a transaction
between a defender (Graphist) and a skeptic (Grapheus). Arisbe's Agon makes it operational.

### Agonothetes
**Agonothetes** (ἀγωνοθέτης, "organizer of the contest") — the game's **interpretant**: not a third
player but the function that turns a true/false outcome into an act of inquiry (a theorem
registered, a model revised, a hypothesis held).

### Scroll
**Scroll** — a nested double cut `~[ M ~[ P ] ]` reading "P given M"; the Alpha home of conditional
assertion.

### Scribe
**Scribe** (verb) — to draw/assert a graph on the sheet (Peirce's term for inscribing a graph).

### Recto
**Recto** — the asserted face of the sheet (an evenly-enclosed, *positive* area). Its complement is
the **verso**.

### Verso
**Verso** — the negated face (an oddly-enclosed, *negative* area), one cut deeper than the recto.

### Tincture
**Tincture** — Peirce's Gamma colourings of areas (his modal/higher-order experiments). Arisbe
treats Gamma-as-modality as out of scope.

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
