# Arisbe — Glossary & Reading Order

> **What this is.** A compact glossary of the Peirce / Dau / Arisbe vocabulary the other spine
> documents assume, plus a suggested reading order by audience. For the full module/API map see
> [../CLAUDE.md](../CLAUDE.md).
>
> **Companions:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) · [CAPABILITY_MAP.md](CAPABILITY_MAP.md) ·
> [ROADMAP.md](ROADMAP.md).

---

## Reading order by audience

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
