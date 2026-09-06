# The exemplar arc: what three scholars will actually open

**Date:** 2026-09-06 · **Status:** specification, nothing built · **Rulings required**

Split from
[the readiness assessment](2026-09-06-readiness-for-external-review.md) at the
author's direction (its Q7): exemplar authoring is a different kind of work
from the engineering around it, and doing it inside a defect list would do it
badly.

---

## 1. Why this arc exists

The author's ruling on Q1 sets the bar: **no letter goes out until all three
recipients can find satisfaction**, because each will explore the whole of
Arisbe rather than only his own corner. Exemplars are what they will explore
with. The corpus holds 52 universes, 34 with real chains and 7 that branch —
a real archive. But measured against the four things the letters must
demonstrate, it is uneven, and it is thinnest exactly where the reader is most
expert.

The four demonstrands, from the author's Q3/Q4 rulings:

1. the **diachronic** UoD — a universe that evolves
2. the **calculus** — the six Dau rules, worked in steps
3. **ontology development** — domain modelling, and M changing
4. the **EPG** — and its effect on the model and on understanding

## 2. What the corpus already carries

Verified by reading every `history/chain.jsonl`.

| Demonstrand | State | Evidence |
|---|---|---|
| (1) diachronic | **strong** | `dialogue_swan_revision` 9 steps (5 PEEL, 3 ADMIT_TO_M, 1 REVISE_M), verdict FALSE→TRUE→TRUE→TRUE→FALSE; `dialogue_model_revision` 7; seven branching UoDs |
| (2) calculus | **thin** | longest proof chain 8 steps; **no chain exercises all six rules**; `theorem_praeclarum` reaches five of six (no ERA) |
| (3) ontology | **import only** | eight imported T-boxes each carry a 2-step residence chain (DC+, INS) and nothing more; `peirce_order_1881` alone shows assembly, six × ADMIT_TO_M |
| (4) EPG | **covered, with a caveat** | `swan_episode_unpacked` forks properly, but its six rules live as a `derivation` list inside one step's params on a working copy — recorded, not replayable |

Two further facts that bear on the letters:

- **`UI` is a derived rule, not one of Dau's six.** It appears in `barbara`
  (×2), `group_identity` (×6) and `swan_episode_unpacked` (×2). It is *sound* —
  `derived_rules.py:52` builds it from IT+ plus a join, Dau's iterate-and-join —
  and `proof_authoring.apply_derived` documents the collapse honestly. But the
  interface never says so, and `barbara` is among the likeliest first clicks.
- **The 14 literature UoDs carry slugs as titles.** "Sowa Cat On Mat", "Dau 2006
  P112 Ligature", "Peirce Cp 4 394 Man Mortal". Each has a rich CSL record in
  its `provenance.json` that renders further down the page. None has a chain,
  so the lens rack collapses and the chain player hides.

## 3. The design principle

**An exemplar is an argument, not a fixture.** Each one should answer a question
a specific reader will actually ask, in the order he will ask it, and should be
readable in Organon without explanation. That implies:

- a **real title and description**, not a slug;
- a **chain**, so the reader can step it — a static picture demonstrates nothing
  about a calculus;
- **provenance** with a citation where the source is a real text;
- **honest scope**: the exemplar should not claim more than it shows.

## 4. The proposed exemplars

Numbered E1–E7. Each names its reader, its demonstrand, and its acceptance test.

### E1 — The six-rule derivation *(calculus; Dau)*

One chain that applies **all six** rules — ERA, INS, IT+, IT−, DC+, DC− — to
reach a real conclusion, with each step annotated in Dau's vocabulary.

*Acceptance:* the recorded chain's rule multiset covers all six; every step
replays; §3.3 attests at each state; the reader can step it in Organon.

*Note:* this is the single most-requested missing artifact. It also feeds the
letter attachment directly through `export_peirce_chain_document`, which emits
one captioned TikZ figure per step.

### E2 — A substantive ligature exemplar *(calculus/Beta; Dau)*

A worked Beta derivation exercising lines of identity across cut boundaries —
the Ch. 16–17 material — rather than the incidental ligature work in
`group_identity`.

*Acceptance:* the chain manipulates a ligature across at least two cut levels
and the correspondence check holds at every state.

### E3 — Real chains and titles for the `dau_*` literature UoDs *(Dau)*

`dau_2006_p112_ligature` and `dau_theorem_proving` are bare graphs with
auto-generated titles. Give each a real name and description from its CSL
record, and a chain if the source supports one.

*Acceptance:* opening either shows a cited title, a description, and — where the
source warrants — a steppable chain.

### E4 — Surface the derived-rule expansion *(Dau; interface, not corpus)*

Show what `UI` collapses to. Either expand it on demand in the chain player, or
annotate the step with its constituent rules.

*Acceptance:* a reader who clicks a `UI` step learns it is IT+ plus a join, and
that `apply_derived` records it as one move for readability. Converts the most
likely Dau objection into a demonstration of rigour.

### E5 — An ontology *developed*, not imported *(ontology; Sowa)*

Take a small imported T-box and show it being corrected, extended, or refuted in
play: a subsumption added, a disjointness discovered, an over-general axiom
relinquished. This is the demonstrand with no adequate exemplar at all.

*Acceptance:* the chain carries ADMIT_TO_M and at least one RETRACT_FROM_M or
REVISE_M against a named ontology; `theory_query.entails` decides a theorem
before and after, and the answers differ.

*Open:* which ontology. `foaf_core` (3 relations) is too thin to show Sowa
anything; `sumo_upper` (26 classes, 43 subsumptions) is the substantial one.

### E6 — A two-player EPG inning *(EPG; Pietarinen)*

Every existing episode is single-voiced. Show an actual inning: alternating
moves, both territories, a real outcome, then the Agonothetes choosing a
disposition — the three strata of the readiness spec §6 end to end.

*Depends on* the eliminative register (Q5 ruling). A genuine inning wants the
*stuck* outcome to be reachable, and wants `erase-a-negative` to exist as one
move rather than two.

*Acceptance:* alternating recorded moves; an outcome that is not merely a
concede; a disposition applied to M; the whole thing replayable.

### E7 — Curate the 14 literature titles *(all three)*

Mechanical but high-yield: real names and descriptions from the CSL records
already present.

*Acceptance:* no UoD in `tomos/literature/` shows a title-cased slug.

## 5. Coverage check

| Demonstrand | Covered by |
|---|---|
| (1) diachronic | already strong; E5 and E6 deepen it |
| (2) calculus | E1, E2, E3, E4 |
| (3) ontology development | E5 |
| (4) EPG | E6 |

| Reader | Opens |
|---|---|
| Dau | E1, E2, E3, E4 |
| Sowa | E5, plus the existing `sumo_upper` / `colore_between` and CGIF round-trip |
| Pietarinen | E6, plus the existing `broken_cut_square` (Lowell 1903), `would_be_courses` (MS 490), `swan_episode_unpacked` |

## 6. Sequencing

E7 and E3 are curation and can land immediately. E1 is the highest-value single
artifact and is independent. E4 is an interface change. E2 needs a Beta
derivation designed. E5 needs an ontology chosen. **E6 is blocked** on the
eliminative register.

## 7. Open questions

- **X1.** Which conclusion should E1 derive? It wants to be short enough to
  step through and rich enough to need all six rules.
- **X2.** Which ontology for E5, and which axiom gets relinquished? The
  narrative matters more than the size.
- **X3.** Should E6 wait for the eliminative register, or ship first as a
  concede-terminated inning and gain the *stuck* outcome later?
- **X4.** Is a Peirce manuscript figure worth transcribing for Pietarinen —
  MS 514 is claimed in his draft letter but absent from the corpus — or should
  the letter drop the claim instead?
