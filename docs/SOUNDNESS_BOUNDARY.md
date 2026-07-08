# The Soundness Boundary — proven vs. tested vs. attested vs. argued

> A logician or evaluator's first question is not "does it work?" but *"on what
> does each guarantee rest?"* This page draws the line explicitly: which claims
> are **proven** (mathematics, by Dau's formalization), which are **machine-verified**
> (a test that fails if the claim is false), which are **attested at runtime**
> (checked at every boundary event, not just in CI), and which are **argued**
> (careful prose, not machine-checked). It disposes gap **G8** of
> [STORM_DOCS_AUDIT.md](STORM_DOCS_AUDIT.md). Externally re-checking these claims
> is the subject of prospect **R1** (proof certificates) — see the last section.

The guiding distinction of the whole project: **Arisbe attests *correspondence*,
not *truth*.** A graph that passes the correspondence check (§3.3) says "this picture and this proposition
denote the same mathematical object" — it says *nothing* about whether that
proposition is true. Truth is earned separately, through the Agon (testing) or a
warranting chain. Keep that in view while reading the table: the guarantees below
are guarantees of *formation and sound transformation*, not of correctness of
content.

## The four tiers

| Tier | What it means | If it's wrong… |
|---|---|---|
| **Proven** | A theorem of Frithjof Dau's formalization of Existential Graphs (the guarantor of correctness — non-negotiable bedrock). Arisbe *implements* it. | Mathematics is wrong (it isn't); or our implementation diverges from the proof — which the next tier catches. |
| **Machine-verified** | A property enforced by code and checked by a test that would fail if the property were violated. Runs in CI. | A red test. The mathematical-core suite must always be green. |
| **Attested at runtime** | Checked at every boundary event in production, not only in CI — refused, not merely logged. | A `CorrespondenceViolation` / `Regime3Violation` raised at the save/load/apply boundary; the write aborts. |
| **Argued** | Established by careful prose and worked examples, not by a machine check. Honest, load-bearing, but not certified. | A reader disagrees; it is a claim to be examined, and the docs invite that examination. |

## The matrix

| Claim | Tier | Rests on | Where |
|---|---|---|---|
| **The six transformation rules are sound** (ERA, INS, IT+, IT−, DC+, DC−) | **Proven** (Dau Ch. 14/15) + **machine-verified** (implementation) | Dau's soundness theorem; `formal_transformation_rules` + `rule_interaction` enforce preconditions | `formal_transformation_rules.py` → `test_beta_proof_exercises.py`, `test_logical_proof_exercises.py`, `test_rule_interaction.py` |
| **EG ↔ FOL are inter-translatable** (Φ/Ψ) | **Proven** (Dau Ch. 18) + **machine-verified** | Dau's translation adequacy; bidirectional Φ/Ψ tested | `chapter18_fopl_translation.py` → `test_tomos_parsing.py`, Ch.18 tests |
| **Rule application preserves well-formedness** | **Machine-verified** | Immutable EGI + `SubgraphClosureValidator` (Beta-aware: free outer-area vertices) | `subgraph_closure_validator.py` → `test_subgraph_closure_validation.py` |
| **A rule only fires on a legal subgraph** | **Machine-verified** | `RuleInteraction` protocol checks preconditions before applying | `rule_interaction.py` → `test_rule_interaction.py` |
| **IT− / goal detection is exact** | **Machine-verified** | NetworkX VF2 isomorphism | `graph_isomorphism_engine.py` → `test_graph_isomorphism_engine.py` |
| **Syntactic equivalence is decided correctly** | **Machine-verified** | Ch. 20 checker | `syntactic_equivalence_checker.py` → its tests |
| **Semantic validation agrees with an SMT solver** | **Machine-verified** | Z3 SMT encoding | `z3_semantic_validator.py` |
| **Linear ↔ graphical round-trips exactly** (EGIF/CGIF/CLIF) | **Machine-verified**, corpus-wide | `same_graph` over 87+ tomos examples | the parser/generator pairs → `test_tomos_parsing.py` |
| **The drawing reads back to the same EGI** | **Machine-verified**, corpus-wide + human geometry | `read(render(egi)) == egi` | `eg_reader.py` → `test_eg_reader.py` |
| **Picture and proposition denote the same object** (§3.3, the central invariant) | **Attested at runtime** | `attest_correspondence` — the six correspondence test shapes (LINEAR_GRAPHICAL_CORRESPONDENCE §7) (totality/injectivity, containment, incidence+arg-order, the 3-way identity incl. the topological crossing-multiset invariant, convention compliance) | `correspondence_attestation.py` → `test_correspondence_invariant.py`, `test_correspondence_attestation.py`; hooked into layout_service + save/load |
| **Presentation edits never change meaning** (regime 3) | **Attested at runtime** | `Regime3Violation` raised on any boundary crossing | `presentation_ops.py` → `test_presentation_ops.py` |
| **Attestation is deterministic** (no content-dependent coin-flip) | **Machine-verified** (as of the run-5 finding fix, F1⁵) | Global, sibling-aware, id-independent label placement shared by renderer + attest | `place_label_boxes` in `presentation_ops.py`; the Warner-Bros pair attests 20/20 across re-parses |
| **The peel is sound open-world** (three-valued Kleene) | **Machine-verified** | UNKNOWN is an honest abstention, never a false guess | `semantic_game.py` → `test_semantic_game.py` |
| **Materialization computes the least Herbrand model** (Horn fragment) | **Machine-verified** | Semi-naive fixpoint = the exact closure; non-Horn shapes skipped with an honest report | `model_materialization.py` → `test_model_materialization.py` |
| **A membrane never fabricates warrant** | **Argued** + partly machine-verified | Correspondence-not-truth: a resolved market/theory is low-warrant; the world's outcome is *data*, the calculus still decides | `resolving_membrane.py`, `MANIFEST_AND_MEANING.md`; ledger tests |
| **Fidelity to Peirce's intent** (three departures, with amendment) | **Argued** | Reasoned defense + adversarial self-examination | [FIDELITY_AND_DEPARTURES](FIDELITY_AND_DEPARTURES.md), [ADVERSARIAL_EXAMINATION](ADVERSARIAL_EXAMINATION.md) |
| **Modality needs no Gamma** | **Argued** + demonstrated | The diachronic DAG *is* the Kripke frame; ◇/□ read off trajectories | [MODALITY_WITHOUT_GAMMA](MODALITY_WITHOUT_GAMMA.md), [GAMMA_DEMONSTRATIONS](GAMMA_DEMONSTRATIONS.md) |

## What the tiers deliberately do **not** claim

- **Not truth.** §3.3 green ≠ "true." It means well-formed and faithfully drawn.
  (See [MANIFEST_AND_MEANING](MANIFEST_AND_MEANING.md): the blank sheet is the
  only unconditioned truth; everything else is posited at low warrant until it
  withstands the Agon.)
- **Not completeness of the model-checker.** The peel is *model-checking*, not
  inference; it decides truth-in-a-supplied-model, not validity. Validity over a
  theory is a separate, narrower tool (`theory_query.entails`, sound + Horn-complete).
- **Not that every linear form generates in every notation.** A graph that
  round-trips in EGIF may not (yet) generate cleanly in CGIF/CLIF; that failure
  is reported per-notation, never silently swallowed.
- **Not the web tier.** Auth, concurrency, and multi-tenancy are out of scope by
  design — see [DEPLOYMENT_AND_MULTIUSER](DEPLOYMENT_AND_MULTIUSER.md).

## What an external re-checker would need (prospect R1)

Today the machine-verified tier is verified *by our own tests*. A skeptical third
party who wanted to certify Arisbe's claims independently — without trusting our
test suite — would need three things, and the first two already exist:

1. **A prover-agnostic contract** stating the properties precisely, so a
   different implementation could be checked against the same spec. →
   [CORRESPONDENCE_CONTRACT.md](CORRESPONDENCE_CONTRACT.md) (the contract properties P1–P5, the six §7
   shapes, the failure taxonomy, the tomos dataset card, MIT-licensed).
2. **A callable referee** that reduces every claim to a re-checkable calculus
   artifact. → the **MCP verifier** (`check_egif` / `peel` / `apply_rule` /
   `validate_step` / `attest`), content-addressed so ids are stable across
   parses. See [MCP_VERIFIER.md](MCP_VERIFIER.md). *The LLM (or any external
   agent) argues; the calculus decides.*
3. **Proof certificates** — the open direction. A rule application currently
   *is* sound (Dau) and *is* checked (our test), but it does not yet emit a
   standalone, independently-checkable **certificate** of that step. Emitting one
   (e.g. a machine-checkable transcript a third-party verifier could replay
   without Arisbe) would move the "machine-verified" rows toward
   "externally-certified." This is prospect R1 in
   [PROSPECTS_MULTIPERSPECTIVE.md](PROSPECTS_MULTIPERSPECTIVE.md).

The honest summary: **the mathematics is proven, the implementation is
machine-verified and runtime-attested, and the philosophy is argued in the
open.** The remaining frontier is not "is it sound?" but "can a stranger confirm
that without trusting us?" — and that frontier is named, scoped, and half-built.

---
*Related:* [CAPABILITY_MAP](CAPABILITY_MAP.md) · [CORRESPONDENCE_CONTRACT](CORRESPONDENCE_CONTRACT.md) ·
[MCP_VERIFIER](MCP_VERIFIER.md) · [LINEAR_GRAPHICAL_CORRESPONDENCE](LINEAR_GRAPHICAL_CORRESPONDENCE.md) (the §3.3 contract) ·
[FIDELITY_AND_DEPARTURES](FIDELITY_AND_DEPARTURES.md).
