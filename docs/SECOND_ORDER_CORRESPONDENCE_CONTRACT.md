# The Correspondence Contract, One Order Up — a second-order companion

**The §-for-§ restatement of [CORRESPONDENCE_CONTRACT.md](CORRESPONDENCE_CONTRACT.md)
for graphs whose subjects are graphs — the deliverable [SECOND_ORDER_FRONTIER.md](SECOND_ORDER_FRONTIER.md)
§"The recommendation" names as "the real engineering weight… the promise the whole
project is built on."**

> **What this is.** A *design-of-record*, not a shipped calculus. It states the
> contract second-order logic-as-a-picture must satisfy, restated property for
> property from the first-order contract, plus the one thing first order does not
> need: a **comprehension floor** (paradox control), drawn as a well-formedness
> rule on **sorts** rather than a symbolic type annotation. Every clause here is
> already *checkable* — the harness `src/second_order_check.py` runs the law on
> candidate quotations, and `tests/test_second_order_check.py` shows the falsifiers
> bite — so the frontier is **de-risked before the protected core is opened**,
> exactly as `reference_resolution_check` de-risked the reference node. Crossing the
> frontier (a native graph-valued node + a reader that recovers the sort off the
> drawing) remains an author decision; this earns it.
>
> *Created 2026-07-10. Companion to [SECOND_ORDER_FRONTIER.md](SECOND_ORDER_FRONTIER.md),
> [MEANING_BY_HISTORY.md](MEANING_BY_HISTORY.md), [SCHEMA_HOLE_CORRESPONDENCE.md](SCHEMA_HOLE_CORRESPONDENCE.md),
> [REFERENCE_AND_TRANSCLUSION_NODE.md](REFERENCE_AND_TRANSCLUSION_NODE.md).*
>
> **Vocabulary note.** This memo predates the 2026-07-20 mention-ascent rename and uses
> the earlier "second-order"/"the crossing" vocabulary throughout. See
> [GLOSSARY.md#mention-ascent](GLOSSARY.md#mention-ascent).

## 0. The design test (unchanged, raised one order)

The first-order contract's whole claim is **the picture *is* the proposition**
(§3.3). The frontier's design test is that claim one order up: **can the
second-order device be drawn, and read back off the drawing, so the picture *is* the
second-order proposition?** A guide that can only supply an off-sheet symbolic type
annotation fails; a guide whose control apparatus is iconic, drawable, and
readable-back passes. Everything below is judged by this, not by symbolic elegance.

## 1. The two objects, one order up

| | first order (the contract) | second order (this companion) |
|---|---|---|
| **logical object** | an EGI `(V, E, ν, ⊤, Cut, area, ρ)` — lines denote *individuals* | an EGI **+ a sort overlay**: a line may carry a second-order **sort** (*proposition* / *abstraction*), and a **quotation** attaches such a line to a whole graph `quoted` (Peirce's dotted line + dotted oval — the "graph of a graph"). The overlay sits *beside* the core (as `reference_node`'s mark does), so `egi_core_dau` is untouched until the author opens it. |
| **graphical object** | a layout (dot / oval-cut / heavy line positions) | the same, **+ the drawn sort-mark**: the dotted oval's contents (the quoted graph, itself drawn) and the sort of the attaching line. |

A quotation is modelled by `second_order_check.Quotation(name, sort, host, resolve,
quoted_ground, enclosed, impredicative, read_back)` — the host graph, the quoted
graph (on demand + an independent ground truth), whether the quoting line is drawn
*enclosed* under a cut, and whether the quote reaches the host's own level.

## 2. The correspondence properties, restated

Each first-order property (P1–P5) is restated for a quotation; the quoted graph is
required to satisfy the *whole* first-order contract one level down (the recursion),
and the sort-mark adds one obligation the reader must discharge.

- **P1′ Totality / injectivity of the sort-mark.** Every quoting line's sort and its
  quoted graph appear in the drawing, and no two distinct second-order devices map
  to the same mark. (P1 recurses on `quoted`.)
- **P2′ Containment of the quotation.** The dotted oval contains exactly the quoted
  graph and nothing else; the quoting line's **drawn enclosure** (which cuts it sits
  under) is authoritative — this is what S1 reads (below). (P2 recurses on `quoted`.)
- **P3′ Incidence + argument order into the oval.** A predicate whose blank is filled
  by a *proposition* (rather than a name) hooks the dotted oval in the argument
  position the ν-tuple records — the graph-of-a-graph is an ordinary incidence whose
  argument is a graph. (P3/P3′ recurse on `quoted`.)
- **P4′ Identity across the sort boundary.** A line that is *individual* at one end
  and enters a quoted graph keeps its identity discipline; a *proposition*-sorted
  line and an *individual*-sorted line are never conflated (the sort is part of what
  the three P4 identity checks certify).
- **P5′ Convention.** The dotted line / dotted oval / sort-tincture are committed
  projection conventions; a drawing that renders a proposition-line as a heavy
  (individual) line fails, exactly as a mis-drawn hook fails P5 today.

## 3. The one new thing — the comprehension floor (S1), drawn

First-order EG needs no paradox control; second-order does. Peirce supplies the
device but **not** the floor (no type theory, no stratification). The floor is
imported as a **drawable well-formedness rule on sorts**, not a symbolic annotation:

> **S1 (stratification).** An *impredicative* quote — one that names the host
> itself, or a graph at the host's own level or above (the self-referential / Liar
> case) — is well-formed **only when drawn *enclosed*** (under ≥ 1 cut), never flat
> on the sheet. A *predicative* quote (a strictly-lower graph, no reach-back) is
> always well-formed.

This is exactly field-guide **dragon 9** ([MEANING_BY_HISTORY.md](MEANING_BY_HISTORY.md))
made a formation rule: a self-assessment read off *one* history is at most ◇ (*some*
trajectory); asserting it flat misreads ◇ as □; it is legitimate only enclosed
(under a cut, as an antecedent one conditions on). The paradox floor and the
reflexive-telos guard are the **same drawn rule**.

**This is one chosen floor, not the only one.** Predicative stratification with an
enclosure-escape is the most Peirce-continuous ("vary the sort, not the rules"), and
it makes dragon 9 mechanical — but a ramified hierarchy, or an impredicative
fragment with a different guard, are live alternatives. *Author decision A: which
comprehension floor.* The harness parameterizes S1 so a different floor swaps in
without touching the rest.

## 4. The law — the second-order §3.3 (what the harness proves)

`RESOLVE ≡ INLINED-AND-ATTESTED`, one order up, is four checks (`check_quotation`):

| check | statement | first-order analogue |
|---|---|---|
| **S1 stratified** | the comprehension floor above — impredicative ⇒ enclosed | *(new: no first-order analogue)* |
| **S2 quote-equals-quoted-and-attested** | `same_graph(resolve(), quoted_ground)` **and** the quoted graph draws in full §3.3 one level down | R1 + R2 (reference) / §3.3 |
| **S3 read-back one order up** | the sort-marked drawing reads back the *same* `(sort, quoted)` device | §3.3 (the picture *is* the proposition) |
| **S4 honest horizon** | a quote the floor forbids, or one a resolver can't locate, is **named** | R4 |

S2's §3.3 half needs a layout engine (injected — the harness imports no geometry);
**S3's reader is the unbuilt frontier itself**, so it is injected too, and when
absent the harness *names* the skip rather than passing silently. So today the
harness proves S1, S2, and the *shape* of S3; building the reader is the crossing.

## 5. Regimes and failure taxonomy — unchanged in structure, extended in list

The three regimes (composition suspended / asserted mandatory / presentation-only
free) are **unchanged**: a sort nudge that changes no logic is regime-3; asserting a
quotation is regime-2 and must attest S1–S3. The failure taxonomy grows by four tags
— `stratification` (S1), `quote_mismatch` / `quoted_unattested` (S2), `read_back`
(S3) — beside the first-order tags; the regime structure does not change. This is the
"accommodate additively" the first-order contract already anticipated (§note there).

## 6. The marked departure (the method)

Per [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md):

- **Keep** — Peirce's device (dotted line, dotted oval, graph-of-a-graph),
  hypostatic abstraction as the ascent operator, and his method (vary the *sort*,
  not the rules).
- **Swap** — the *unfinished mechanism*: for the paradox control Peirce lacked,
  **S1 as a drawn sort-rule**, not a symbolic type calculus.
- **Flag** — the exact line: *Peirce leads to drawing a second-order claim (the
  device); he stops at which claims are well-formed (S1)*. S1 is the borrowed floor;
  no reader should mistake it for Peirce's own.

## 7. What is earned, and the two author decisions that remain

**Earned (this pass):** the law is *checkable* on real candidates before the core is
opened — `second_order_check.py` + 11 tests (falsifiers bite). The toe-in-water is
consistent with it: `definitions.py` (hypostatic abstraction in miniature, reversible
= a predicative quote), the reference node's *mention* branch (second-order naming,
paused here), and `schema.py` (the φ-hole *deliberately* stops short of a graph-valued
node — the very device S1 would license).

**Remaining — the crossing (author decisions):**
- **A. Which comprehension floor** (§3) — predicative-with-enclosure-escape is the
  default the harness encodes; ramified / other fragments swap in.
- **B. How much to open the core.** Overlay-forever (the sort layer stays beside
  `egi_core_dau`, like `reference_node`) vs. a native graph-valued node (a real core
  change + a §3.3 reader that recovers the sort off the drawing — S3 built). The
  harness works either way; B is the boundary between *preparing* the frontier and
  *crossing* it. **The full brief for B is [SECOND_ORDER_CORE_OPENING.md](SECOND_ORDER_CORE_OPENING.md)
  (memo 2)** — it shows the overlay is a strict prefix of the native node (so B is
  deferrable and reversible), that the hinge is S3 alone, and that B is the *same*
  core-opening decision as the reference node's deferred use/mention fork.

Until B is taken, this document is the contract and `second_order_check.py` is its
witness; the frontier is mapped, de-risked, and marked — not yet crossed.

*See also (2026-07-13):* [FORCING_AND_THE_GAMMA_CROSSING.md](FORCING_AND_THE_GAMMA_CROSSING.md)
— Cohen's forcing arrives at the same crossing devices and nominates `(forces s φ)`
as the first asserted second-order claim decision B waits for; it also adds law
**S5 (trajectory-relative resolution)** to the harness. And
[SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md](SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md)
— the modern-landscape survey placing this contract's defaults (predicative floor,
sortal layer) among the post-Peirce semantics and paradox-control results, with the
K3/grounded-partial refinement to decision A and conservativity-over-the-core as the
crossing invariant.
