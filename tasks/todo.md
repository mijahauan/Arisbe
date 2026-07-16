# Stage ⓪ — the Quotation overlay stratum (2026-07-15 session)

The crossing's first build rung (CURRENT_PLAN item -1; SECOND_ORDER_CORE_OPENING §5.1;
verdicts A1–A4 + B taken 2026-07-16). **No core change; main; additive.**

Deliverable: the first drawable, S1/S2/S4/S5-attested quotations in corpus exemplars,
S3 skip-named, S4 horizon honest. The overlay is the strict prefix B-min promotes.

## Plan

- [x] 1. `src/quotation_overlay.py` — `QuotationMark` (serialisable overlay beside the
      EGI, mirroring `reference_node.ReferenceMark`): sort (proposition/abstraction),
      target, enclosed, impredicative override, origin, warrant="low"; to/from_dict.
      Resolver seam (state-of-a-UoD / corpus-UoD / inline-EGIF targets) →
      `quotation_candidate` bridges to `second_order_check.Quotation`;
      `attest_quotation_mark` / `run_quotation_mark` boundary hooks (S5 via
      per-state candidates).
- [x] 2. Dotted-oval render glyph in `simple_svg_renderer` (`quotation_marks=`,
      pure chrome, off by default — the exact shape of the reference 1b glyph);
      prove it changes no attested DTO geometry.
- [x] 3. Exemplar (i): swan third tense — `(superseded ⌜M_swan_law⌝ …)` overlay on
      `dialogue_swan_revision`; predicative (quoted state strictly below); S5
      trajectory attest across the revision chain.
- [x] 4. Exemplar (ii): `(forces s φ)` on `forcing_conditions` — the settled/open/
      excluded trichotomy as per-state quotations (Montague rider: defined via the
      peel/modal machinery, never axiomatized); S5.
- [x] 5. Exemplar (iii): cross-UoD **mention** — a commentary UoD naming `peirce_law`
      as object (scholarly-citation use; the increment-2 fork's mention side,
      overlay-only so no co-assertion hazard).
- [x] 6. `tests/test_quotation_overlay.py` — 28 tests green (round-trip, S1
      impredicative-flat refusal + structural self-quote detection, exemplars
      re-attest with real ELK, S5 falsifier naming the state, S3 in honest_limits,
      glyph geometry-neutrality, persistence). Quality gate + core protection green;
      corpus gates green (polarity, correspondence invariant, peirce-latex,
      eg_reader, organon routes, tomos parsing); Quarto book 42/42. Full suite run
      pending completion at wrap.
- [x] 7. Docs: CURRENT_PLAN ▶▶ fourth-sitting block + item -1 "⓪ BUILT"; CLAUDE.md
      module + test entries; SECOND_ORDER_CORE_OPENING §7 build note; CAPABILITY_MAP
      §I row (+ reference-node row cross-link); EXEMPLARS §7.

Deferred (named): S3 read-back (IS stage ①); lens surfacing of the exhibits
(audit-lens shelf / modal forcing ink) + web wiring of the glyph (reference_marks
is equally unwired — one web seam for both later).

## Review

Stage ⓪ of the crossing is built, additive, on main. The overlay module mirrors
reference_node exactly (mark beside the EGI, resolver seam, boundary hooks); its
one doctrinal refinement is that S1's enclosure is computed from the drawn host,
never stored. The three blessed exemplars are corpus records attested at build
time — the builder refuses to save what does not recompute — and each saved
verdict re-attests in tests. Surprises: (a) the polarity gate forced the design
into commentary UoDs housed in standing world-scrolls (which turned out
philosophically exact for present-without-force); (b) CANONICAL_PATTERN UoDs
save under tomos/literature/, so the glyph export had to resolve the entry path
through the service rather than assume universes/. Next rung: ① B-min — an
authorized protected-core opening (sort-on-incidence + with_quotation + the
second-order reader; S3 flips to checked; A3 conservativity gate; the
use/mention fork's core half rides the same opening).
