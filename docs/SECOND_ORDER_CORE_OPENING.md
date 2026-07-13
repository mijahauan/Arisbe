# Opening the core for a graph-valued node — the increment-2 author decision

**Memo 2 of the second-order prep. The companion to
[SECOND_ORDER_CORRESPONDENCE_CONTRACT.md](SECOND_ORDER_CORRESPONDENCE_CONTRACT.md)
(memo 1, which states the law) — this one states the *build decision* the law's §7
defers as "author decision B: how much to open the core."**

> **What this is.** A *design-of-record for a decision*, not a build. Memo 1 proved
> the second-order law (`RESOLVE ≡ INLINED-AND-ATTESTED`, one order up) is checkable
> before the protected core is opened — `src/second_order_check.py` runs S1–S4 on
> candidate quotations and the falsifiers bite. What memo 1 leaves open is *decision
> B*: does the sort layer stay an **overlay beside `egi_core_dau` forever** (the
> `reference_node` precedent), or does the core gain a **native graph-valued node**
> plus a reader that recovers the sort off the drawing (S3 built — the frontier
> actually crossed)? This memo lays the two options side by side, states what each
> concretely costs and buys, shows the overlay is a **strict prefix** of the native
> node (so the decision is deferrable and reversible), and recommends the sequencing.
> The decision itself remains the author's.
>
> *Created 2026-07-10. Companion to memo 1, [SECOND_ORDER_FRONTIER.md](SECOND_ORDER_FRONTIER.md),
> [REFERENCE_AND_TRANSCLUSION_NODE.md](REFERENCE_AND_TRANSCLUSION_NODE.md) (the increment
> model this memo copies), [SCHEMA_HOLE_CORRESPONDENCE.md](SCHEMA_HOLE_CORRESPONDENCE.md)
> (the φ-hole that deliberately stops one step short of the node this memo would add).*

## 0. The decision, in one line

**Overlay-forever** (option A) keeps `egi_core_dau` untouched: a quotation is a mark
*beside* the graph, exactly as `reference_node`'s `ReferenceMark` is. **Native node**
(option B) makes a quotation a *first-class element of the EGI* whose sort a §3.3
reader recovers from the drawing. A is *preparing* the frontier; B is *crossing* it.
The hinge between them is **one property: S3 (read-back)** — and nothing else.

## 1. What "opening the core" concretely means

The protected data model is `RelationalGraphWithCuts(V, E, ν, ⊤, Cut, area, ρ)`
([egi_core_dau.py](../src/egi_core_dau.py), immutable, 14-module protected set). A
line today denotes an *individual*; a quoted graph today has **no core element** —
in the harness it lives only in the overlay `Quotation(name, sort, host, resolve,
quoted_ground, …)`. "Opening the core" means giving the EGI a way to say *this line's
subject is a graph, of sort `proposition`/`abstraction`* as structure the core
carries, not as a dict kept beside it. Concretely, exactly one of:

- **(B-min) a sort field on the incidence** — `ρ` (or a parallel `sort` map) gains a
  second-order sort for a line, and a graph-valued *area* (Sowa's proposition-typed
  context: a cut flagged as holding a quoted graph rather than a negation). Additive
  to the tuple, but a protected-core edit and a new immutability constructor
  (`with_quotation(...)` beside `with_vertex`/`with_edge`).
- **(B-full) a native graph-valued node** — a new element kind whose value *is* a
  `RelationalGraphWithCuts`, with `ν` able to hook a predicate blank to it (P3′). The
  richer of the two; the one Peirce's dotted oval most literally is.

Either B-variant is the "one genuine protected-core touch" the reference-node doc
already anticipated for its own *mention* branch ([REFERENCE_AND_TRANSCLUSION_NODE.md](REFERENCE_AND_TRANSCLUSION_NODE.md)
§7). **That is not a coincidence — see §6.**

## 2. Option A — overlay-forever (the `reference_node` precedent)

The sort layer stays a serialisable overlay keyed by element id, beside the core,
never inside it — the shape `reference_node.ReferenceMark` already ships and
`second_order_check.Quotation` already models.

- **Buys:** zero protected-core risk; ships today; every *predicative* second-order
  device that does real work is already expressible — `definitions.py` (hypostatic
  abstraction in miniature, a reversible predicative quote), the reference node's
  *mention* branch (second-order naming as an overlay pointer), a schema's φ-hole
  (metalinguistic, [SCHEMA_HOLE_CORRESPONDENCE.md](SCHEMA_HOLE_CORRESPONDENCE.md)).
  S1, S2, S4 all check on the overlay — the paradox floor, the object-recovers
  guarantee, and the honest horizon **all hold without opening the core.**
- **Costs / where it strains:** **S3 cannot be built faithfully.** Read-back
  (§3.3-raised: *the sort-marked picture IS the second-order proposition*) requires a
  reader that recovers `(sort, quoted)` **from the drawing alone**. An overlay is by
  definition *not* in the drawing — the sort lives beside the picture, so a reader
  handed only the picture cannot recover it. Under A, S3 stays permanently injected /
  skip-named (`read_back=None` → `honest_limits`), exactly as it is today. An
  *asserted* second-order quotation (regime 2) would therefore attest S1+S2 but never
  S3 — a genuine, honestly-named gap, not a bug.

**A is correct and complete for everything except an asserted, drawn-and-read-back
second-order claim.** It is the whole frontier *minus the crossing*.

## 3. Option B — native node + the sort-reader (the crossing)

The EGI carries the sort; a reader recovers it off the drawing.

- **Buys:** **S3 becomes buildable** — the reader (`read_drawing`'s second-order
  sibling) recovers the dotted-oval contents and the quoting line's sort from geometry
  alone, and `check_quotation` runs S3 for real instead of skip-naming it. This is
  "the picture *is* the second-order proposition" discharged, not promised — the one
  thing memo 1 §4 calls "the unbuilt frontier itself." An asserted second-order
  quotation can then attest the *full* S1–S3, so regime-2 second-order assertion
  becomes sound-and-attested rather than sound-with-a-named-gap.
- **Costs:** a protected-core edit (authorised, `.core_modification_authorized`) + a
  new immutability constructor + the reader itself (the substantive build) + the sort
  must survive every transformation rule (a `ρ`-sort is one more thing the six Dau
  rules must preserve — the harness's S-tags become runtime obligations like §3.3).
  The renderer gains the dotted line / dotted oval / sort-tincture as *committed*
  projection conventions (P5′), not optional chrome.

## 4. The hinge is S3, and only S3

Everything in memo 1's law except S3 is *regime- and location-agnostic*: S1
(stratification) reads the drawn enclosure, which the overlay already records; S2
(quote-equals-quoted-and-attested) recurses the first-order §3.3 on the quoted graph,
which draws whether or not its *sort* is in the core; S4 (honest horizon) is a report.
**S3 alone requires the sort to be in the drawing**, because S3 *is* the claim that
the drawing carries it. So the entire overlay-vs-native decision reduces to one
question: **do we need asserted second-order claims to attest read-back, or is
"sound + S1/S2-attested + S3-named-as-open" enough?** If the corpus never asserts a
second-order quotation (only *entertains* them, or uses only predicative/definitional
ones that fold away), A suffices forever. B is worth its core touch exactly when a
*drawn, asserted, read-back-checkable* second-order claim is a thing the project wants
on the attested sheet.

## 5. What each requires — the build order (should B be taken)

Copied from the reference-node model (additive-first, core later), because it worked:

1. **Ship A first, regardless.** The overlay `Quotation` + S1/S2/S4 + a render glyph
   for the dotted oval (pure chrome, no DTO/§3.3 change, off by default — the exact
   shape of `reference_node`'s increment-1b glyph). This banks every predicative
   device and makes the frontier *usable* while the S3 question stays open. No
   protected-core edit.
2. **Only if B:** open the core minimally (B-min preferred — a sort on the incidence +
   a graph-valued area — before B-full's new element kind), add `with_quotation`,
   make the six rules sort-preserving (new rule-interaction tests), and build the
   second-order reader. S3 flips from skip-named to checked; the harness's `read_back`
   injection point receives the real reader.
3. **Attest.** `attest_quotation` (already in the harness) becomes the regime-2
   boundary hook, beside `attest_correspondence` — a served, asserted second-order
   (EGI, drawing) pair now verifies S1–S3 the way `layout_service` verifies §3.3.

## 6. A and B are the *same* core-opening decision as the reference-node fork

The reference node's deferred **use/mention fork**
([REFERENCE_AND_TRANSCLUSION_NODE.md](REFERENCE_AND_TRANSCLUSION_NODE.md) §7) names its
increment-2 core touch as "the **mention** (second-order naming) branch." That branch
*is* a quotation: to *mention* a graph (name it without asserting it) is to carry a
graph-valued subject — precisely option B here. So **decision B and the reference
node's increment-2 gate are one decision seen from two doors.** Whichever is taken
first pays the core-opening cost once; the other rides it. This memo and the
reference-node §7 should be decided together, not twice.

## 7. Recommendation

**Ship A now; hold B for a demonstrated need.** Rationale:

- A is *strictly* a prefix of B (the overlay is what B promotes; nothing built for A
  is thrown away — the `Quotation` model, the glyph, S1/S2/S4 all carry forward), so
  starting with A forecloses nothing and the decision stays reversible — the exact
  property that made `reference_node` increment 1 the right first slice.
- B's whole marginal value is S3 on an **asserted** second-order claim. Until the
  corpus wants to *assert and draw-read-back* a graph-about-a-graph (not merely
  entertain, define, or mention-via-overlay one), that value is unrealised and the
  core touch is unamortised. The honest position is memo 1's: the frontier is
  *mapped, de-risked, and marked* — cross it when an asserted second-order claim earns
  the core change, not before.
- When B *is* taken, take it as **one** decision with the reference-node mention fork
  (§6), and start at B-min (sort-on-incidence) before B-full (native element kind).

**Author decision B remains open by design.** This memo is its brief; memo 1 is its
law; `second_order_check.py` is the witness that the law already holds on candidates.
Decision **A (which comprehension floor)** is orthogonal and composes with either
option — the harness parameterises S1 so the floor swaps in without touching this
overlay-vs-native axis at all.

*See also (2026-07-13):* the criterion above — "an asserted second-order claim earns
the core change" — now has a **named nominee**:
[FORCING_AND_THE_GAMMA_CROSSING.md](FORCING_AND_THE_GAMMA_CROSSING.md) §5 proposes
`(forces s φ)` (state s forces the quoted graph φ), drawable as a β-level spot with
its S3 read-back semantics already defined by the peel + `modal_query`, and — per
[SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md](SECOND_ORDER_LANDSCAPE_AND_POSITIONING.md)
§4 (Montague's theorem) — admissible only as a *defined, grounded, decidable*
relation, never an axiomatized primitive. Decision B remains open; the nominee is
what it would be exercised on.
