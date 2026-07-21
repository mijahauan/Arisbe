# Documentation Sweep — the fix half (Workstream B1, Phase B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (fresh implementer + task reviewer per batch, whole-branch review at the end). Steps use checkbox syntax.

**Goal:** Apply the audit docket's fixes — mechanical corrections, the approved EPG-role one-vision propagation, book membership, and readability — turning the 87-doc corpus into the consistent, current, publication-ready state workstream B exists to produce.

**Architecture:** The **work-list is the committed docket** [docs/superpowers/audits/2026-07-20-doc-sweep-docket.md](../audits/2026-07-20-doc-sweep-docket.md) — every finding carries `file:line` + a suggested FIX. This plan does **not** re-enumerate the 67 findings (DRY); each batch names the docket section it draws from. Design of record: [docs/superpowers/specs/2026-07-20-doc-sweep-design.md](../specs/2026-07-20-doc-sweep-design.md).

**Tech Stack:** Markdown; git; grep-grade verification; `quarto` for the book-membership check.

## Author rulings baked in (2026-07-20)

- **OQB2 — EPG vision: SUPERSEDED BY THE §3 RULING (2026-07-21). The canonical account is now
  `docs/THE_COMMENS_AND_THE_COMMUNITY.md` §3, NOT the docket §(iii) draft.** The author's
  authoritative 2026-07-20 ruling (written into §3, committed `48bed74`) replaces the docket's
  drafted vision on two load-bearing points: **(1)** the game has **TWO players only** — Graphist
  (the *proposal*) and Grapheus (the *Model M*) — yielding a **binary outcome**; there is **no
  "Grapheus-the-tester"** and **no referee** (the calculus guarantees every move legal; the peel
  *decides the binary outcome*, it does not referee conduct). Grapheus is simply the Model-M
  player — drop the "tester + defender, two functions" framing. **(2)** the **Agonothetes is NOT a
  player** in any register — it stands outside the two-sided play and, given the binary outcome +
  the agreed *taxonomy of fates*, **selects which fate applies as a risked choice**, bringing the
  episode into a posture of the functioning UoD *toward* the commens. In the automated game
  (`LLMAgonothetes`) the **fate-selection function is reified as an agent that acts on the
  outcome** — still not a third contestant. Task 6 **harmonizes the 10 divergent docs to §3**; the
  docket §(iii)'s per-doc reconciliation *clauses* are advisory context only and must be adapted
  to this vision (they were drafted against the now-superseded "tester+defender / reified-third-
  player" account). Implementation docs (agon_llm.py-describing) keep describing what the code
  does, but framed under §3 and cross-referencing it — never reasserting "referee"/"tester"/"third
  player" as doctrine. Genuine author-calls the docket flags (e.g. #9 BOOTSTRAP project-scale "does
  the outer game lack a judge") are **flagged, not decided**.
- **OQB1 — Book membership:** add **THE_COMMENS_AND_THE_COMMUNITY.md, THE_KYTOS.md, THE_MEASURE_OF_KNOWLEDGE.md, BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md** to `docs/_quarto.yml`. **TUTOR_LOOP.md — held** (do not add).
- **OQB3 — CLAUDE.md:** the fix plan **may edit CLAUDE.md** for clear factual drift (counts, shipped-vs-unbuilt), review-gated like any other fix.

## Global Constraints

- **Docs only; no `src/` change.** Fixes correct what a doc *says*, never change doctrine/meaning (spec non-goal). If a finding would require changing what a doc *claims* (not how clearly/currently it says it), the implementer **stops and flags** rather than rewriting.
- **Verify every staleness fix against the live repo** before applying it (the finding names the claim; the implementer confirms the current truth in `src/`/CLAUDE.md, then corrects). A staleness fix applied without a verification line in the report is rejected.
- **The "final"-family ban and the exact UoD/commens/mention-ascent vocabulary** hold in all edits.
- **One commit per batch**; commit trailer verbatim: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Do not touch** `runs/run13_console.txt` or any `docs/superpowers/audits/` file (the docket is the frozen record).

## Batches (SDD tasks, in order)

- [ ] **Task 1 — Book membership (docket §(iv); OQB1).** Add the 4 approved docs to `docs/_quarto.yml` in a sensible chapter location (a "Doctrine / recent" part, or beside their topical neighbors). Verify: `quarto render docs --to html` still succeeds (or the CI render-check), all 4 appear in the ToC, TUTOR_LOOP absent. One commit.

- [ ] **Task 2 — Dedup + the workstream-A deferred Minors (docket §(c)).** Conant–Ashby: keep the good-regulator theorem statement in the dedicated Conant–Ashby bullet (`CONTRIBUTION_AND_PRIOR_ART.md:296`), make the Cybernetics bullet (`:199`) cross-reference it instead of re-quoting. The "final standings" → "closing standings" reword in `ROADMAP.md`. (Venue notes: no action — author-decision, already marked.) Verify: the good-regulator quote appears once; ban-list clean. One commit.

- [ ] **Task 3 — Vocabulary-conformance (docket §(b)).** Apply the 2 vocabulary-drift fixes (UoD/commens/mention-ascent conformance in the named docs). Verify against the settled definitions. One commit.

- [ ] **Task 4 — Stale facts, book chapters (docket Tier-1 §(d) + the verified-clear items of Tier-2 §(i) for clusters A–D + CLAUDE.md).** Correct verified factual staleness in the book chapters and CLAUDE.md: the "automated Grapheus unbuilt" claims (`src/grapheus.py` shipped — 5 instances across GETTING_STARTED/ARISBE_FOR_SCHOLARS/arisbe_triad_architecture/RETURN_TO_DEVELOPMENT), the clockwise-placement "pending" (`src/clockwise_placement.py` shipped), CHAPTER18's nonexistent-test citations + "100% PRODUCTION READY" overclaim, IMPORT_EXPORT RDF/OWL "future"→shipped, CAPABILITY_MAP's missing bootstrap/vault subsystem + stale consolidation date + K2/K3 omissions, GLOSSARY "17 modules"→14, SECOND_ORDER_FRONTIER's crossing-is-open→ruled-and-shipped, the FIDELITY "live frontier"/"(superseded ⌜M⌝) candidate"→built framing, EXACT_CORRESPONDENCE/UoD_ARCHITECTURE/DAG_HISTORY self-contradicting status/checklists/"future enhancements", CORE_API_USAGE_GUIDE's 4 stale signatures. **Verify each against `src/`/CLAUDE.md before editing; flag any that need a framing rewrite rather than a fact correction.** Split into ≤3 commits by doc-group if large.

- [ ] **Task 5 — Stale facts, non-book docs (docket Tier-2 §(i) for clusters E–H).** AUTOMATED_GRAPHEUS "nothing built yet" header, the ADVERSARIAL_EXAMINATION open-ruling/disposition lags (already-ruled items), ELK_LAYOUT_IMPLEMENTATION_SUMMARY, PRODUCT_VISION/PROSPECTS run-history, VISION_AND_SCOPE musement/horizon "deferred"→built, the older layout/workflow-spec staleness. Verify each against the repo; flag framing rewrites. ≤2 commits.

- [ ] **Task 6 — EPG-role one-vision propagation to §3 (docket §(iii) targets; OQB2 as superseded above).** Harmonize the 10 divergent docs **to `THE_COMMENS_AND_THE_COMMUNITY.md` §3's ruling** (two players Graphist/Grapheus; binary outcome; no referee/no tester; Agonothetes not a player = the risked fate-selector, reified as an agent acting on the outcome only in the automated game). Each divergent doc gets a reconciliation clause + a cross-reference to §3 as canonical:
  - `UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md:235-240` — the Graphist/Grapheus polarity note, reframed as Graphist=proposal-side / Grapheus=Model-M-side (not attacker/defender of M).
  - `GLOSSARY.md:233-234` — Agonothetes "not a third player" is now **fully correct doctrine** (§3); add that the automated game *reifies the fate-selection function as an agent acting on the outcome*, still not a contestant.
  - `CAPABILITY_MAP.md:162` "Three LLM roles ... SHIPPED" — keep (accurate for the code) but cross-ref §3 so "three roles" (two players + the fate-selector-as-agent) doesn't read as "three players."
  - `AUTOMATED_GRAPHEUS.md` / `AUTOMATED_ENDOPOREUTIC_GAME.md` — register note: these describe the *automated implementation*; the mechanical peel decides the binary outcome (it is not a "referee" of legality and not a "Grapheus-the-tester" sub-role — §3); cross-ref §3.
  - `AUTOMATED_MODEL_DEVELOPMENT.md` — the "Skeptic"/"referee" naming: bridge to §3 (this names the mechanical peel that decides the outcome, not a Grapheus function and not a move-by-move referee).
  - `DOMAIN_ORACLE_AND_M.md:136` / `ENDOPOREUTIC_GAME_GUIDE.md:691-697` — settle "who chooses M" consistently (do not invent doctrine; if it needs an author ruling beyond §3, **flag**).
  - `TUTOR_LOOP.md:85-95` — "calculus as referee" mapped to §3's "the calculus decides the outcome, there is no conduct-referee."
  - `BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md:285` — "the world as a more generic Grapheus": reconcile with §3's model-of-never-instance-of; the "does the outer game lack a judge" question is an **author-call — flag, do not decide**.
  - `FIDELITY_ENDOPOREUTIC_CHECK.md:55-58` — cross-reference the §3 account as the canonical frame for the Pietarinen restatement.
  - Fix the `ENDOPOREUTIC_GAME_GUIDE.md:2115-2116` **Agonothetes-conflated-with-"the Commens"** vocabulary drift (docket §(iii) companion + §(b)): the Agonothetes *draws on* commens-level standards, it is not the commens; this aligns with §3 and THE_COMMENS §1's category-mistake warning.
  **Harmonize, do not delete** informative components (aliases, semiotic-triad, etymology in ENDOPOREUTIC_GAME_GUIDE are all compatible). Consider hosting the full harmonized account in `ENDOPOREUTIC_GAME_GUIDE.md` (the richest source) with a link back to `THE_COMMENS_AND_THE_COMMUNITY.md §3`. **Do not reassert "tester+defender" or "Agonothetes as a third player" as doctrine anywhere.** This is the delicate batch — thorough task-review against §3. ≤2 commits.

- [ ] **Task 7 — Readability (docket §(v)).** Name the target doc on the bare `§N` cross-doc references (FIDELITY_AND_DEPARTURES, ADVERSARIAL_EXAMINATION, EXEMPLARS, GAMMA_DEMONSTRATIONS, ALPHA_RELEASE_PLAN), per the house convention. The identical-opening-sentence across 3 on-ramp chapters: leave (confirmed intentional standalone-door design). One commit.

## Verification (whole-branch, prose-grade)

1. Re-run the pre-pass link-check → still zero broken links.
2. Every batch's staleness fixes carry a verification line (claim → confirmed current truth → correction).
3. The EPG one-vision reads consistently across the 10 docs **against §3** (no remaining flat contradiction; the two-players / binary-outcome / no-referee / Agonothetes-not-a-player account present and cross-referenced where the roles are described; no doc reasserts "tester+defender" or "Agonothetes as a third player" as doctrine).
4. `quarto render` succeeds with the 4 new chapters; TUTOR_LOOP not added.
5. No `src/` change; core-protection clean. Ban-list clean; vocabulary consistent.
6. The docket's Tier-1 all resolved; Tier-2 items resolved or consciously deferred with a reason.

## Notes for the executor

- The docket is the requirements; read the batch's docket section, not this plan, for the exact `file:line` + FIX of each finding.
- Staleness = correct the fact, not the framing. When a "fix" would change what the doc argues, stop and flag — that is the author's, per the spec's non-goal.
- Batches 1–3 and 7 are low-risk mechanical; 4–5 need per-finding verification; 6 (EPG propagation) is the one to review hardest.
