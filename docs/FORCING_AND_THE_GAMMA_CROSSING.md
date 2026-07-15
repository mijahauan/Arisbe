# Forcing and the gamma crossing — what Cohen's technique says about the frontier

> **Status: design-of-record memo (2026-07-13), not a book chapter.** Occasioned by
> Caterina & Gangle, *"Consequences of a Diagrammatic Representation of Paul Cohen's
> Forcing Technique Based on C.S. Peirce's Existential Graphs"* (in Magnani et al.,
> eds., *Model-Based Reasoning in Science & Technology*, SCI 314, Springer 2010,
> pp. 429–443), read while run 12 executes. Companion to the two second-order memos
> ([SECOND_ORDER_CORRESPONDENCE_CONTRACT](SECOND_ORDER_CORRESPONDENCE_CONTRACT.md),
> [SECOND_ORDER_CORE_OPENING](SECOND_ORDER_CORE_OPENING.md)) and to the modern-landscape
> survey ([SECOND_ORDER_LANDSCAPE_AND_POSITIONING](SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md),
> written the same day). It bears directly on the two author crossing decisions
> (A: the comprehension floor; B: opening the core for a graph-valued node).
> [CATEGORIES_AND_THE_THREE_PARTS](CATEGORIES_AND_THE_THREE_PARTS.md) (2026-07-15) gives
> the same two decisions their categorial footing — `(forces s φ)` read as hypostatic
> abstraction of a graph.

## §0 Why this memo

The paper models Cohen's forcing in Peirce's Existential Graphs: the forcing relation,
drawn at the β level, "lifts" into the modal assertions of EG-γ, and the authors read
this lifting as the abductive emergence of γ out of β. Arisbe has already taken two
positions on that terrain — *modality needs no Gamma* (the diachronic DAG is the Kripke
frame; [MODALITY_WITHOUT_GAMMA](MODALITY_WITHOUT_GAMMA.md)) and *the real frontier is
second-order* (graphs about graphs; [SECOND_ORDER_FRONTIER](SECOND_ORDER_FRONTIER.md)).
The paper turns out to ratify both, and to sharpen the two decisions still open. This
memo records the mapping exactly, the disanalogies honestly, and the guidance it yields.

## §1 The paper in brief

Cohen's technique, as the paper presents it (following Badiou's reconstruction):

- A countable transitive **ground model M** of ZF, and within it a poset of
  **conditions** C, where *every condition is dominated by two incompatible
  conditions* (the splitting property).
- **Correct sets** of conditions (filter-like); **dominations** (dense sets: every
  condition outside D is dominated by one inside).
- A **generic** G: a correct set meeting every domination in M — therefore
  *indiscernible from within M* (a property λ codable in M would be met and refuted
  along the way).
- **Names** µ, defined by transfinite induction *inside M*; **reference values**
  R_G(µ), fixed only relative to G; the extension **M[G] = {R_G(µ) : µ ∈ M}**.
- The **forcing relation** π ⊩ S — defined wholly within M — correlating with truth
  in the extension. Three mutually exclusive, exhaustive cases:

  | in M | in M[G] | the paper's γ reading |
  |---|---|---|
  | ∅ forces S | S true in **all** M[Gⱼ] | necessity |
  | some π ≠ ∅ forces S | S true in **some** M[Gⱼ] | contingency |
  | no π forces S | S true in **no** M[Gⱼ] | impossibility |

The authors draw the forcing relation as an ordinary β-level spot on the sheet (M) and
the three modal statuses as a covering sheet (M[G]) — Peirce's γ "book of separate
sheets, tacked together at points" — and propose the construction as a formal footing
for abduction (the generic = the creative excess a hypothesis reaches for; the forced
fragment = what the finite present state of enquiry controls).

## §2 The dictionary

The structural rhyme is exact, and every column on the Arisbe side already exists in
the codebase. (The letter collision is accidental but happy: the paper's M/G are the
ground model and the generic set; Arisbe's M/G are the domain model and the proposed
graph. The dictionary below disambiguates by context.)

| Cohen / the paper | Arisbe | where |
|---|---|---|
| condition poset (extends only; every condition split by two incompatible extensions) | the diachronic branching DAG: frozen, append-only states; a fork = two chain steps sharing `from_state_id` | `egi_transformation_history`, `tomos_service.TransformationChain` |
| the ground model M at a condition | the developing model M *at a state* | `agon_evolution` / the live-run carried M |
| π ⊩ S / ⊩ ~S / neither (decided within M) | the peel's three-valued verdict at a state: TRUE / FALSE / UNKNOWN | `semantic_game.Verdict3` |
| the three-case table (all / some / no extensions) | □φ / ◇φ∧¬□φ / ¬◇φ over reachable states — now named `settlement` (settled / open / excluded) | `modal_query` |
| the γ "book of sheets tacked together at points" | the branching history: sheets = states, tacked at shared `from_state_id`s | storyboard lens; `possible_and_necessary` exemplar |
| names µ (defined in M, denoting into the extension) | reference marks / quotations: a drawable device whose denotation outruns the present sheet | `reference_node.ReferenceMark`, `second_order_check.Quotation` |
| reference values R_G(µ) (fixed per generic) | trajectory-relative resolution: what a name resolves to *at a state / along a branch* — the S5 law | `second_order_check.check_quotation_at_states` |
| the generic G (meets every domination; indiscernible within M) | the world as the membranes deliver it — never held, only queried; the open-world horizon | `domain_oracle`, the membranes |
| dominations (dense sets) | the falsifying feeds: any M-definable over-generalization eventually meets its counterexample | `resolving_membrane`, the Challenger |
| adjoining a generic witness to decide a universal | `theory_query.entails`'s freeze-a-fresh-witness maneuver (arbitrary constants → materialize → check the head) | `theory_query` |
| Badiou's "finite fragment made up of the present state of the enquiries" | the warrant floor: M self-certifies a track record, never truth (*correspondence, not truth*) | doctrine, everywhere |

## §3 What the paper ratifies

**The modality decision.** The paper's three modal statuses are *derived* — computed
from β-level forcing facts plus the order structure of conditions — never primitively
asserted. That is exactly the doctrine of MODALITY_WITHOUT_GAMMA: modality is a
*reading* of the DAG (a quantifier over the frame Arisbe already maintains), not a
mark on the sheet. Cohen's construction is distinguished ancestry for the settled
decision: even in the hardest case classical mathematics offers — independence proofs
over ZF — the modal layer is fully determined by first-order relations one level down,
plus order. Nothing in the paper motivates reopening the broken cut as an *assertion*
device; if a drawn γ notation is ever wanted, it should be chrome rendering
forcing-status (like the standing badges), never an asserted mark.

**The second-order decision.** Look closely at the paper's own diagrams: the forcing
spot's argument is a *quoted statement* — `forces S₂(n_k)` is an ordinary relation
applied to a **name of a graph**. The paper's γ-lifting quietly concedes what
SECOND_ORDER_FRONTIER argues: the load-bearing crossing is not modality but
*aboutness* — graphs about graphs, use/mention, quotation. Cohen's names are the
mathematically serious version of the device Arisbe has been building as the
reference node and the quotation harness.

## §4 The honest disanalogies

Three places the analogy must not be over-read; each is load-bearing.

**(a) Forcing is monotone; Arisbe's M is not.** Cohen's conditions only ever extend,
and "π forces S" persists under extension. Arisbe's M revises non-monotonically
(retraction, disuse-decay, `challenge_to_M`), and even along a *derivation*, content
shrinks under erasure (ERA). The append-only object in Arisbe is the **DAG of states**,
not any state's content. Consequences: (i) any gamma-crossing machinery should hang
off the DAG (where `modal_query` already lives), not off M; (ii) the unconditionally
sound analogue of the three-case table is the **trajectory trichotomy** — now built as
`modal_query.settlement` (settled / open / excluded over reachable states); (iii) the
peel at a state is condition-local forcing *only on the enlargement-only fragment*
(no retraction, no decay) — treat "peel-TRUE now, therefore □ over extensions" as
valid only there.

**(b) The world is not guaranteed generic.** Genericity is the *lawless pole*: a G
that meets every domination refutes every M-definable regularity it lacks. The worlds
the membranes sample may instead be lawful. Gödel's constructible universe ("every set
is constructible" — the world fully discernible, deduction suffices) and Cohen's
generic extension (the world outruns every discernment, induction never closes) are
the two poles of an axis, and **the live-run arc is an instrument for locating a
domain on it**: `select_best` ranks theories by how much regularity the world actually
concedes; the knob-type law (AUTOMATED_ENDOPOREUTIC_GAME Part II §11.4) is a statement
about how a theory tracks a world partway up the axis; run 12's question — is the law
the game's or the weather's — is a question about two domains' positions on it. This
framing is recorded here as a *reading*, not a new instrument; a "discernment ratio"
metric is queued in §6.

**(c) The paper is programmatic.** The γ-lifting is an iconic gesture, not a calculus;
there is no soundness result, and the "correct set" presentation is filter-like
shorthand. The value for Arisbe is the skeleton (which is standard Cohen) and the
identification of the crossing devices — not a formal system to adopt.

## §5 Guidance for the two crossing decisions

**Decision A (the comprehension floor).** The minimal second-order vocabulary the
forcing skeleton needs is tiny and fully *predicative*: **{statement-name,
state/condition, forces}** — names of graphs one level down, names of DAG states, and
one relation between them. Every piece already has a mechanical semantics in the
codebase (quotation + `Verdict3` at a state + `settlement` over the frame). This
supports memo 1's default floor (predicative stratification with the enclosure
escape): the first useful second-order stratum is one step, names only what sits
strictly below it, and needs no impredicative comprehension at all. It also connects
to the schema hole ([SCHEMA_HOLE_CORRESPONDENCE](SCHEMA_HOLE_CORRESPONDENCE.md)): the
φ-hole is one step short of the statement-name this stratum licenses.

**Decision B (opening the core).** Memo 2's criterion: hold the native graph-valued
node until *a drawn, asserted, read-back-checkable second-order claim* is something
the project wants on the attested sheet. This memo nominates the candidate:

> **`(forces s φ)`** — "state s forces the graph φ" — with s a state-name, φ a
> quotation, and the relation's semantics *defined* by the existing machinery (the
> peel at s for the condition-local reading; `settlement` from s for the trajectory
> reading).

It is drawable (a β-level spot, exactly as the paper draws it), assertable, and its
S3 read-back is well-defined because the relation is decidable over finite objects.
**One caveat is mandatory** (argued fully in the landscape memo §4): `forces` must
enter as a *defined, grounded, decidable relation over finite quoted objects* — never
as an axiomatized primitive satisfying unrestricted reflection principles. Montague's
theorem (1963) shows that a necessity-like *predicate on sentence names* obeying
modest reflection schemas collapses into inconsistency; the definitional route, plus
the S1 enclosure rule for impredicative instances, is what keeps `(forces s φ)` on
the safe side of that result.

**The S5 law (built).** Cohen's R_G — a name's reference value fixed per generic —
generalizes the quotation harness with one law the name layer must satisfy:

> **S5 (trajectory-relative resolution; R_G functoriality).** A quotation whose
> resolution varies by state satisfies S1–S3 *at every state where it resolves*
> (quote-equals-quoted against that state's ground, attested one level down), and
> every non-resolving state is **named**, never silent — the per-state honest horizon.

Implemented additively in `second_order_check` (`check_quotation_at_states` /
`attest_quotation_trajectory` / `run_quotation_trajectory`), as quantification over
the existing per-state checks.

## §6 What this memo builds and queues

Built with this memo (all additive, geometry-free, no protected module):

1. **`modal_query.settlement`** — the three-case table as a named lens primitive:
   settled (□) / open (◇ ∧ ¬□) / excluded (¬◇) for a predicate at a state, over
   reachable states or leaves. The per-statement settled-vs-open join that
   `discourse_membrane.contested_contents` gestures at.
2. **S5 in `second_order_check`** — as above.
3. **The forcing exemplar** (`tools/build_forcing_conditions_demo.py` → corpus UoD
   `forcing_conditions`) — the paper's binary-sequence conditions as a small
   diachronic episode *in the revision register* (a condition-extension is a game
   move, not a deduction): trunk `(one "p1")`, `(one "p2")`; fork at p3 into
   incompatible `(one "p3")` / `(zero "p3")`; the correct-set property
   `~[ (zero *p) ]` as the audited proposal. Read through the modal lens (□one,
   ◇zero), the audit lens (the proposal's verdict per branch), and `settlement`.

Queued (author's call):

- A **discernment instrument** on the Gödel–Cohen axis (§4b): e.g. the fraction of a
  run's resolutions that M's standing laws forced versus arrived unforced — a
  metalearning reading, not a new referee.
- A **forcing-status chrome** rendering (derived, never asserted) if a drawn modal
  notation is ever wanted in the viewer.
- The `(forces s φ)` build itself — this is precisely crossing decision B, and it
  remains the author's.

## §7 References

- G. Caterina & R. Gangle, "Consequences of a Diagrammatic Representation of Paul
  Cohen's Forcing Technique Based on C.S. Peirce's Existential Graphs," in L. Magnani
  et al. (eds.), *Model-Based Reasoning in Science & Technology*, SCI 314, Springer
  (2010), 429–443.
- P. Cohen, *Set Theory and the Continuum Hypothesis*, Benjamin (1966; Dover 2008).
- T. Chow, "A beginner's guide to forcing," *Contemporary Mathematics* 479 (2009),
  25–40.
- A. Badiou, *Being and Event*, trans. O. Feltham, Continuum (2005).
- F. Zalamea, "Peirce's logic of continuity: Existential graphs and non-Cantorian
  continuum," *Review of Modern Logic* 9 (2003), 115–162.
- L. Kauffman, "The mathematics of Charles Sanders Peirce," *Cybernetics & Human
  Knowing* 8 (2001), 79–110.

Cross-references in this repo: the two second-order memos; the landscape survey
(SECOND_ORDER_LANDSCAPE_AND_POSITIONING); MODALITY_WITHOUT_GAMMA;
SECOND_ORDER_FRONTIER; MEANING_BY_HISTORY (dragon 9, ◇-is-not-□, the enclosure cap);
REFERENCE_AND_TRANSCLUSION_NODE; SCHEMA_HOLE_CORRESPONDENCE; and in `src/`:
`modal_query`, `semantic_game`, `theory_query`, `reference_node`,
`second_order_check`, `egi_transformation_history`.
