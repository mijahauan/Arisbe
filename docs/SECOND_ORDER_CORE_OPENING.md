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

> **DECISION B TAKEN (the author, 2026-07-16 — CROSSING_DECISION_BRIEFS).** The
> frontier is crossed, exemplar-first: rather than holding B for an awaited
> demonstrated need, the need is *established* by fitting exemplar cases chosen to
> illustrate graphs-about-graphs clearly and robustly. **Both nominees get ink** —
> `(superseded ⌜M⌝ reason)` and `(forces s φ)` (Montague rider binding). Staging as
> this memo ordered: overlay first, then **B-min**, then **B-full following B-min**;
> taken jointly with the reference-node increment-2 use/mention fork (one core
> opening, both riders). Decision A was ratified the same day (predicative floor,
> split-level, conservativity as the crossing invariant — the corpus-level
> no-new-first-order-theorems check joins the crossing's verification).

> **Stage ⓪ BUILT (2026-07-15).** The overlay stratum of §5 step 1 is in the
> codebase: `src/quotation_overlay.py` (`QuotationMark` beside the EGI +
> `quotations.json` persistence + the resolver seam + boundary hooks into this
> memo's law) and the dotted-oval render glyph (`simple_svg_renderer`'s
> `quotation_marks=`, pure chrome, off by default) — no protected module
> touched. The three blessed exemplars are in the corpus, S1/S2/S4/S5-attested
> at build time with the real layout engine and S3 skip-named:
> `swan_third_tense` (the withdrawn law as exhibit, S5 naming s4–s7),
> `forcing_forces` (`(forces s φ)` under the Montague rider, the trichotomy as
> trajectory-relative resolution), `peirce_law_commentary` (cross-UoD mention
> with the real citation). Builder `tools/build_quotation_exemplars.py`; tests
> `tests/test_quotation_overlay.py`. Next rung: ① B-min (the authorized core
> opening — sort-on-incidence, `with_quotation`, the second-order reader → S3
> checked, the A3 conservativity gate, the mention/use fork's core half).

> **Stage ① B-min BUILT (2026-07-16 — the authorized core opening).** The one
> genuine protected-core edit, exactly as §5 step 2 ordered, authorized by the
> author's crossing verdicts and executed under `.core_modification_authorized`:
>
> * **Sort-on-incidence + graph-valued area** — `RelationalGraphWithCuts` gains
>   two parallel maps in the `ρ` pattern (both default-empty; a first-order
>   graph is bit-identical): `sort` (vertex → `proposition`/`abstraction`) and
>   `quotation` (quotation-cut → quoting-vertex — Sowa's proposition-typed
>   context, a cut flagged as *holding* a quoted graph rather than negating).
>   Validated: same-area attachment, one oval per name, no
>   quotation-in-quotation (a named B-min limit). New constructors
>   `with_sort` / `with_quotation_binding` (convert existing ink) /
>   `with_quotation` (fresh name + empty oval) / `without_quotation` (the only
>   sanctioned unquoting — atomic; piecemeal removal refuses).
> * **The six rules sort-preserving + the quotation boundary opaque** — one
>   shared `_rebuild_graph` forwards `alphabet`/`rho`/`sort`/`quotation`
>   through every rule (repairing the historical DC−/ERA/IT± alphabet/rho
>   drop — author-ratified; the alphabet *grows* to cover lawfully introduced
>   vocabulary rather than closing the language), and
>   `_refuse_quotation_boundary` enforces mention-not-use: no rule operates
>   inside an oval; ERA takes the whole exhibit or nothing; DC− refuses a
>   dotted oval as either half of a double cut; IT± refuse the apparatus
>   entirely (deep — a plain cut enclosing an exhibit won't copy). IT−
>   matching and `same_graph` treat a sorted line / quotation area as never
>   matching an unsorted twin / a negation.
> * **The committed drawn convention + the second-order READER → S3 CHECKED** —
>   `LayoutDTO.cut_stroke`/`vertex_sorts` carry the dotted-oval stroke and the
>   sort badge (the `order_label` idiom: set by
>   `eg_reader.assign_second_order_marks` in both engines, drawn by
>   `simple_svg_renderer`, read back geometrically by `read_drawing` with
>   one-to-one oval↔name pairing); §3.3 gains the committed-convention
>   totality check (`correspondence_attestation`, active only on non-empty
>   maps). `src/second_order_reader.py` supplies the harness's `read_back`
>   injection point (`read_quotation_back`) and the regime-2 boundary hook
>   (`attest_served_quotations`, wired beside `attest_correspondence` in
>   `layout_service`). **S3 flips from skip-named to checked** on
>   `swan_third_tense` and `forcing_forces`; the cross-UoD mention's
>   quoted-half stays an honestly named horizon (an oval cannot inline
>   another universe).
> * **The A3 conservativity gate** — `tests/test_second_order_conservativity.py`,
>   three tiers: corpus-wide invisibility-when-unused (byte-identical JSON,
>   canonical order unchanged), erasure projection (`project_first_order`;
>   the quoted law licenses *nothing* — asserted it derives, quoted it does
>   not; the peel/materializer/modal readings all skip ovals), rules
>   restraint (every boundary refusal + the linear-form refusal).
> * **Linear forms refuse loudly** — `SecondOrderNotInLinearForm`
>   (`src/second_order_limits.py`) in all three generators; corpus surfaces
>   (`linear_forms` service) show the **first-order projection + the named
>   limit**. No sort syntax is invented at B-min (author-ratified).
> * **The mention fork's core half discharged** — `peirce_law_commentary`'s
>   name is core-sorted (`sort_step`; drawn badge, §3.3-total); *use* remains
>   scroll-only, and the deferral is pinned as a test
>   (`tests/test_use_mention_fork.py`).
> * **Exemplars re-expressed** — each scribing is an explicit `QUOTE` chain
>   step (registered neutral in `proof_character`: a mention asserts nothing);
>   the swan's law and the three φ are now drawn *in* their hosts inside
>   committed dotted ovals; S5 trajectories unchanged (s4–s7; the trichotomy).
>
> Tests: `test_second_order_core` (27) · `test_rules_second_order` (18) ·
> `test_second_order_reader` (12, falsifiers pinned) ·
> `test_second_order_conservativity` (10) · `test_use_mention_fork` (6) +
> the extended `test_quotation_overlay` (39). Named limits: no linear sort
> syntax; no quotation-in-quotation; no IT± of exhibits; cross-UoD mention
> S3 = sort-half only. Next rung: ② **B-full** (native graph-valued element
> kind, ν-hookable blank, P3′/P5′), which follows B-min per verdict B5.
