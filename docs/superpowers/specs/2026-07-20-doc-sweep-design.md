# Workstream B — the Documentation Sweep (design spec)

**Date:** 2026-07-20 · **Status:** design for author review, pre-plan ·
**Sub-project B1 of the four-workstream program** (Understand · **Share** · Run · Use). This spec
builds **B1 (the sweep)** only. **B2** — the publication *choice* (author decision) + writing a
paper (a separate future authoring cycle) — is deferred; B1 surfaces the choice, does not make it.

## What this is

Workstream B is "Share": make the corpus legible enough to be *taken up* by people who weren't
here while it was made — the concrete form of the connection-outward entailment
([THE_COMMENS_AND_THE_COMMUNITY.md](../../THE_COMMENS_AND_THE_COMMUNITY.md) §10). The 2026-07-20
scoping exploration found the corpus **already largely disciplined** — 142 md files, but the "final
opinion" hits are almost all legitimate Peirce-*discussion* (the FIDELITY/EXAMINATION docs critique
the final opinion; they embody the no-"final" discipline, not violate it), the bare "final" uses are
mostly benign, and `institutionaliz` is used correctly. So B1 is a **targeted audit-and-tune**, not a
mass rewrite: find the real defects, fix the mechanical ones, surface the judgment calls.

## Author rulings baked in (2026-07-20)

1. **Audit-first, targeted** — a doc audit produces a findings docket before any fix; scoped to real
   defects, not a blanket pass.
2. **Scope = all 87 top-level `docs/*.md`, tiered** — the ~42 Quarto-book chapters get the deep read;
   the ~45 non-book deep docs get a lighter pass. `archived/`, `_book/` (generated), and
   `superpowers/` (dated working records) are out of scope by nature.
3. **Fix boundary = auto-fix mechanical, surface judgment** — I fix clear verifiable defects (dead
   links, claims contradicted by current code, duplicate phrasings, vocabulary drift, the three
   deferred Minors), each review-gated; I bring judgment calls (borderline overclaims, Quarto-book
   membership, substantive readability rewrites) to the author as a decision list. **Meaning-affecting
   edits are never auto-applied.**
4. **Mechanism = Approach 1** — a mechanical pre-pass + parallel cluster-auditors → merged tiered
   docket → SDD-style tiered fixes.
5. **Named-entity consistency is a first-class dimension** (the author's example, 2026-07-20): the
   three EPG roles — **Graphist / Grapheus / Agonothetes** — are described differently across
   `AUTOMATED_MODEL_DEVELOPMENT.md`, `AUTOMATED_ENDOPOREUTIC_GAME.md`, `ENDOPOREUTIC_GAME_GUIDE.md`,
   and the `agon_*` module bullets. The audit must find such drift; the **canonical frame** is the
   doctrine doc §3 (roles as a good-regulator *model* of the institution: proposer / defender / judge)
   + the `agon_llm` account in CLAUDE.md. **The resolution is harmonization into one vision, not
   deletion** (the author's clarification, 2026-07-20): each variant description carries *informative
   components*, so the fix **synthesizes** a unified canonical account that absorbs the informative
   parts of each variant, seated in the doctrine §3 frame, then propagates it — it does not pick one
   description and discard the rest.

## Scope

**In:** the 87 top-level `docs/*.md`. **Deep tier** = the ~42 book chapters (in `docs/_quarto.yml`).
**Light tier** = the ~45 non-book top-level docs. **Out:** `docs/archived/`, `docs/_book/`
(generated — never hand-edit), `docs/superpowers/**` (dated specs/plans/audits), `docs/references/`,
and non-prose subdirs (`assets/`, `styles/`, `coherence/`, `derived/`). Also out: `README.md`,
`CLAUDE.md`, `CURRENT_PLAN.md` at repo root are **in** the audit's *reference* set (auditors may read
them to judge staleness) but edits to them are **light/opt-in** — CLAUDE.md is the module map and
changes there are higher-stakes; flag CLAUDE.md findings as judgment.

## The audit dimensions

Each finding is tagged `file:line · dimension · severity(Critical/Important/Minor) · mechanical|judgment · suggested-fix`.

1. **dead-refs** *(mechanical)* — broken markdown links (file/anchor target absent); references to
   renamed/removed things (leftover "second-order crossing" → "mention-ascent"; the archived Qt GUI /
   `unified_d3` cited as live; other renames).
2. **staleness** *(judgment)* — a claim that looks contradicted by current code/state (old counts,
   superseded decisions, a feature described as absent that now exists or vice-versa). Flagged for
   verification against CLAUDE.md / the code, **never assumed** — the auditor names the claim and why
   it looks stale; the fix is applied only once verified.
3. **overclaim** *(judgment)* — an *asserted* terminus (the "final"-family AS ASSERTION, not as
   discussion of Peirce's doctrine), a *flagged*-gloss presented as *settled*, or `institutionalize`
   misused (claiming an individual/one instance institutionalizes). The assert-vs-discuss distinction
   is the core judgment; most "final opinion" hits are legitimate discussion and are **not** findings.
4. **named-entity consistency** *(judgment, flagship = the three EPG roles)* — a named entity
   (a role, a module, a defined term) described inconsistently across docs. Measured against the
   canonical frame where one exists (the EPG roles → doctrine doc §3 + CLAUDE.md `agon_llm`).
   **Resolution where the variants carry complementary informative components (the EPG roles):
   harmonize into one vision** — synthesize a canonical account absorbing each variant's informative
   parts (seated in the doctrine frame), then propagate; do *not* pick one and delete the rest.
   (Contrast dimension 6, dedup, which is for *pure* redundancy — the same content restated.)
5. **vocabulary drift** *(mechanical-ish)* — old/inconsistent use of the settled terms (UoD as the
   per-instance internalized model; commens; mention-ascent). Bring touched docs into conformance.
6. **dedup** *(judgment)* — the same concept phrased differently in ≥2 docs (e.g. Conant–Ashby stated
   twice in `CONTRIBUTION_AND_PRIOR_ART.md`). Resolution = pick one canonical statement, point the
   others at it. This is for *pure* redundancy (the same content restated); where the variants carry
   *complementary* informative components, that is dimension 4 (harmonize into one vision), not dedup.
7. **readability** *(judgment, book tier only)* — dense unexplained shorthand, a bare `§N`
   cross-doc reference (the doc convention: name the target doc), a shorthand not expanded on first
   use in a book chapter.

**Tier discipline:** book chapters → all seven dimensions. Non-book → dimensions 1, 2, 5 only.

## The mechanism (Approach 1)

**Phase 0 — mechanical pre-pass** (controller-run, no subagents): a link-checker over all 87 docs
(extract every `](target)`; verify file/anchor exists) + grep candidate-lists ("final"-family,
the vocabulary terms, "second-order crossing", `unified_d3`/Qt, the three EPG role names). Output →
`docs/superpowers/audits/2026-07-20-doc-sweep-prepass.md`, handed to the auditors so they don't spend
tokens re-finding grep-able defects.

**Phase 1 — cluster-auditors** (parallel Agent subagents, sonnet): shard the 87 docs into ~7
topic-grouped clusters (~12 each), book and non-book kept separable so the depth instruction differs.
Each auditor reads its cluster + its pre-pass slice, applies its tier's dimensions, and writes
structured findings to a per-cluster file. Auditors **propose** fixes; they do not edit docs.

**Phase 2 — merge + cross-cutting pass**: merge the per-cluster findings into one **docket**
(`docs/superpowers/audits/2026-07-20-doc-sweep-docket.md`), then one cross-cutting subagent over the
merged findings + candidate lists catches dedup + named-entity + vocabulary drift that spans clusters
(the EPG-role drift is exactly this — it only shows when several docs are compared). The docket is
organized **Tier 1 mechanical** vs **Tier 2 judgment**, each by severity, with the judgment set
gathering the borderline overclaims, the **book-membership recommendations**, and the substantive
readability rewrites.

**Phase 3 — tiered mechanical fixes** (SDD-style, implementer + reviewer per batch), grouped:
(a) dead-refs; (b) vocabulary-conformance; (c) the three deferred Minors + Conant–Ashby dedup;
(d) named-entity **harmonization** — the OQB2-confirmed *synthesized* EPG-role vision propagated across
the agon docs (a judgment-confirmed authoring step, not a mechanical swap — it waits on the author's
confirmation of the synthesized account); (e) Quarto-book membership (per the author's ruling from the
surfaced list). Each batch = one small commit.

**Phase 4 — surface judgment**: the Tier-2 decision list to the author. Rulings applied as a
follow-up batch or deferred.

## Deliverables

1. The committed **audit docket** (+ pre-pass) — the "what was actually wrong" record; itself a
   connect-outward provenance artifact.
2. The **mechanical fix commits** (Phase 3 batches).
3. The **Tier-2 decision list** surfaced to the author (book membership, borderline overclaims,
   readability), with rulings applied or deferred.

## Verification (prose-grade; no test suite)

1. **Link-checker re-run** over the touched docs returns zero broken file/anchor targets.
2. **Vocabulary conformance:** touched docs use UoD/commens/mention-ascent per the doctrine doc; no
   leftover "second-order crossing" in a live (non-historical) assertion.
3. **No new overclaim:** the fixes introduce no asserted terminus and present no flagged gloss as
   settled (spot-grep + the reviewer's read).
4. **EPG-role consistency:** the three roles' one-line descriptions in the touched docs match the
   canonical form (doctrine §3 / CLAUDE.md) — the flagship named-entity fix verified explicitly.
5. **Docket mechanical tier all resolved** (each Tier-1 finding marked fixed or consciously deferred
   with a reason).
6. **Core-protection clean** (docs-only; no `src/` change).
7. **Quarto still renders** if the book set changed (the CI render-check / `quarto render`), and the
   new doctrine doc's membership matches the author's ruling.

## Non-goals (routed onward, not dropped)

- **B2:** the publication first-paper choice (author decision) and paper-writing (a separate future
  authoring sub-project). B1 surfaces the five candidate theses + a book-membership recommendation;
  it does not choose.
- **Doctrine change:** this is a *legibility* sweep. A finding that proposes changing what a doc
  *claims* (not how clearly it says it) is always a Tier-2 judgment call for the author — never an
  auto-fix. The sweep makes the corpus say what it already means, more consistently; it does not
  re-litigate meaning.

## Open questions for the author (surfaced during/after the audit, not blocking the build)

- **OQB1 — Quarto-book membership.** Which recent top-level docs join the published book
  (`THE_COMMENS_AND_THE_COMMUNITY`, `THE_KYTOS`, `THE_MEASURE_OF_KNOWLEDGE`,
  `BOOTSTRAP_AND_DIRECTED_ENGAGEMENT`, `TUTOR_LOOP`, …)? The audit will recommend; the author rules.
- **OQB2 — The harmonized EPG-role vision.** The audit will propose a single *synthesized* account of
  Graphist/Grapheus/Agonothetes that **harmonizes the informative components** from each doc's current
  description, seated in the doctrine §3 frame; the author confirms/edits it before batch (d)
  propagates it. Harmonize into one vision — not pick-one-and-delete.
- **OQB3 — CLAUDE.md edits.** Whether CLAUDE.md (the module map) may be edited for consistency, or
  only flagged. *(Default: flag as judgment; edit only on explicit ruling.)*
