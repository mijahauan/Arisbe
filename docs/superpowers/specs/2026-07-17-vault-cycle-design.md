# The Vault Cycle — World #2: the Author According to Arisbe (design spec)

**Date:** 2026-07-17 · **Status:** design for author review, pre-plan ·
**Design-of-record context:** BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3 (the socket; rung 1
built and criteria-disposed on the arithmetic world) · THE_MEASURE_OF_KNOWLEDGE (the
measure this cycle's M is scored by) · the author's rulings of 2026-07-17 (below).

## The author's rulings (baked in)

1. **The framing (the author's correction, verbatim in substance):** M is **the author
   according to Arisbe** — the author and their notes stand *outside* the membrane as
   the world being modeled; the author's own world-model appears *inside* M only as
   **attributed components**. The model's purpose: **reduce Arisbe's doubt about who
   the author is.**
2. **Staging:** metadata-first (offline, deterministic, no API), content-reading
   second, the interactive oracle third.
3. **API consent: GIVEN** — for modeling the author, content-level reading included.
   Scope wrinkle discovered post-consent: `People/`, `Kith_Kin/`, `Household/` hold
   third-party content; **default = metadata-only for those folders** (no API content
   reading) until the author explicitly widens the consent.
4. **Vault:** `/Users/mjh/Documents/Vorago`. Recon (2026-07-17, metadata only): 1,014
   md notes · ~1.06M words · 3,457 wikilinks · 161 frontmatter notes · mtimes 2024-03
   → 2026-07 · 73 PDFs · ~1,400 images · 59 canvas files · `Clippings/` present.
   **The journal (the author's clarification, 2026-07-17):**
   `Personal/Journal-20230228/Journal.md` — 23,233 lines / ~418k words, **1,583
   date-headed entries spanning 1930 → 2023-11** (per-decade: 1930s 2 · 1950s 1 ·
   1960s 3 · 1970s 38 · 1980s 271 · 1990s 112 · 2000s 131 · 2010s 601 · 2020s 422;
   2 malformed date-lines to be flagged, never silently mis-dated). Sequential entry
   was the author's main recording method before Obsidian — this file, not the
   Obsidian mtimes, is the **longitudinal spine**: the diachronic record is ~50 years
   of writing, not 27 months.
5. **Provenance is inquiry, not precondition** (the author's insight): whether a note
   or part of its content originates elsewhere is itself a subject of Arisbe's study
   of the author — `(authored ...)` vs `(collected ...)` are *hypotheses* carrying
   evidence (folder priors like `Clippings/`, style, link density, clipping markers),
   disposed through the loop like any claim.

## Architectural commitments (from the framing)

- **Use/mention as the spine.** The author's assertions enter M as **quoted,
  attributed cells** — `(asserted "author" ⌜P⌝)` with the B-min quotation machinery
  (proposition-sorted names, opaque ovals, the A3 gate guaranteeing quoted content
  licenses nothing). Arisbe adopting some P of the author's into its own
  world-component is an **explicit episode** (entertain → test → discharge), never a
  silent slide from "said" to "so."
- **Even the author's errors are veridical data**: `(asserted "author" ⌜P⌝)` stays
  true-about-the-author regardless of P's fate. The author's answers are **ground
  truth about the author by construction**; they carry no warrant about the world
  except what testing earns.
- **The measure reads as character**: K1 = the record of predicting the author; K2
  separates disposition from mood (what survives decay across 27 months is trait);
  K3 = compression — the few habits deriving many observations, the person's
  character as the Horn core (Peirce: a person is a bundle of habits); K4 = the
  currently-live habits.
- **Guards** (all ratified doctrine, one new): vector-not-scalar over persons (Doubt
  4's clause — a person-model never condenses to a score of the person); custody
  local-first, the author's own; **predict, never pre-empt** (the new guard: the
  author-model may forecast the author's proposals but never pre-judge them — the
  method-gate stays blind to identity, including the modeled author's).

## Stage V0 — the metadata membrane (offline, deterministic, CI-safe; no API)

**New module `src/vault_world.py`** (+ `tools/` driver later): a `VaultSource` reading
the vault **without leaving the machine**:

- **Facts (first-order, unquoted — activity evidence, not content):**
  `(note "n")` · `(in_folder "n" "dir")` · `(links "a" "b")` (wikilinks) ·
  `(tagged "n" "t")` · `(modified "n" "YYYY-MM")` (frontmatter date when present,
  mtime fallback — the diachrony) · `(kind "n" "md|pdf|canvas|image")` ·
  `(collected_prior "n")` for `Clippings/` (a *prior*, not a verdict — feeds ruling 5).
- **The journal reader (entry-level; still metadata):** split `Journal.md` on its
  date-line convention (`^YYYY-MM[-DD]`) into entries →
  `(journal_entry "j/1983-07-04")` · `(entry_date "j/…" "1983-07")` · entry length.
  **Two timelines, held apart:** the date-line is an **event-time claim**; the
  **writing-time** is a *hypothesis* (contemporaneous vs retrospective entry — the
  pre-birth 1930s entries prove the distinction; which periods were written live vs
  reconstructed is itself a discriminating question about the author, prime oracle
  material for V2). Malformed date-lines → flagged to the horizon, counted.
- **Probes** (the `ProbeDirectedFeed` pattern, feed-seeding extracted per the
  carried-to-vault list): `scan_folder` (cheap) · `read_note_metadata` ·
  `follow_links(n)` (the crawl shape) · `date_window(period)` (diachronic slices) ·
  hunt-shaped probes for standing hypotheses (e.g. provenance tests). Costs scale
  with note size; severity high for hypothesis-discriminating probes.
- **The horizon register — BUILT HERE** (deferred to this stage by design): PDFs,
  images, canvas files, and web clips enter the horizon as *not-yet-legible*,
  retained with counted size, re-attempted when a later stage (V1's reader) can
  voice them. Nothing silently dropped.
- **Carried-to-vault fixes land first**: the docket/frontier dispatch branch
  count-or-refuse (never silently discard — it goes live here); feed-seeding
  extraction; the yield-attribution comment honored if probe_budget > 1.
- **Bounds**: ttl/decay in atom units per the live-runner pattern; `range_cap`
  analogue = notes-per-segment; drops counted. |M| target modest (the vault is 1k
  notes; the model need not hold them all — decay keeps the *engaged* slice).
- **Replay**: every poll journaled; the run replays offline (the determinism canary).

**V0's claims are already about the author**: "the author's attention shifted from
topic-cluster A to B after 2025-06" (link/date structure); "these clusters are
collected, not authored" (provenance hypotheses); "the author returns to note n on a
~k-week cycle."

## Stage V1 — content reading (API per consent; third-party folders excluded by default)

The `nl_to_logic` path (quarantine-hardened) reads authored-note content into
**quoted attributions**: `(asserted "author" ⌜...⌝ )` cells, dated. Provenance
inquiry goes live (does this passage read as the author's voice or a clipping?).
Dis-quotation only by episode. LLM roles optional and staged (mechanical panel
first, per the standing pattern).

**V1 design notes (added 2026-07-18, from the author's prompts):**
- **Community detection as meso-scale attention** (the author's graphify observation):
  the author runs `graphify --update` as "spatial memory" over the code repo; the same
  move serves the loop — communities over the vault's wikilink graph give the docket
  *region-level* wants (a thin, doubt-worthy cluster is `attention_brief` writ large),
  computed locally and deterministically. The loop's existing spatial memory (`m_view`,
  the hierarchical index, canonical signatures) is element-level; graph communities are
  its missing meso-scale.
- **The Arisbe repo as a second evidence source about the author** (the author's
  observation): the project's own docs, commits, and run logs carry the author's hand,
  interests, values, and directives — already dated, sourced, and disposed, i.e.
  membrane-shaped without NL parsing (commit metadata + doc structure are V0-grade;
  doc content is V1-grade). A candidate leg after the vault, feeding both this cycle's
  M and the eventual reflexive Universe of Discourse.

## Stage V2 — the oracle (V2a RULED 2026-07-18: the Obsidian-native surface)

Forecast-before-ask (the resolving shape): Arisbe predicts the author's answer,
asks, scores the miss. The docket's wants become questions; the economy's cost unit
is **the author's time**. **The author ratified all four V2a recommendations
(2026-07-18):**

1. **Surface = the vault itself.** Arisbe writes questions notes into exactly ONE
   folder (`Arisbe/`), each with `authored_by: arisbe` frontmatter; the next poll
   reads answers back **through the same membrane**. Arisbe-ink is excluded from
   author-evidence by provenance; the author's `**A:**` text enters M as quoted
   attributed cells (`(asserted "author" ⌜…⌝)`, provenance `oracle-answer`) —
   banked unparsed via the quotation machinery (mention-not-use), so V2a needs no
   API; interpretation is V1's explicit-episode job. This is the first true
   action-arm act: Arisbe writing into the world it models, under standing consent,
   contained to one folder. A deleted questions note = a wave-off, honest. (The web
   docket panel is V2b, later, for quick confirms.)
2. **Budget = per-note, pull-only**: ≤5 questions per note, ≤1 reflective; tiers
   quick-confirm / short-answer / reflective, severity must justify tier; a new note
   only when the prior is substantially answered or waved off; **the knob lives in
   the note's frontmatter** (`budget: {max: 5, reflective: 1}`, author-editable).
   No push, ever.
3. **Seal-then-reveal**: the forecast's plaintext lives in the gitignored side-store;
   only its SHA-256 commitment appears in the question block; the next note's
   `## Reveals` section prints plaintext + hash + hit/miss after the answer is read —
   the seal is *checkable*, not promised. Ask-time and answer-time held apart (the
   two-timeline discipline, third appearance).
4. **Decline/silence are first-class**: `declined` = veridical data, its want decays
   (no re-asking); silence ages the want; a question-kind repeatedly yielding silence
   decays as a kind (the noisy-TV guard turned inward). Counted-never-dropped
   throughout. **Reflexive stream from day one**: the whole exchange lives in
   `Arisbe/`, so "how the author changes by interacting with Arisbe" accumulates in
   the corpus automatically, provenance-marked.

**V2a build list** (small, offline, deterministic): question-renderer (docket wants →
markdown note), answer-parser (`**A:**` + declined/ignored states), hash-commitment
seal + reveal, the provenance-exclusion rule in the reader, ledger wiring
(forecast-vs-answer → the author-model's K1).

## The oracle doctrine — five author theses (2026-07-18)

The author's, in formulation the assistant's — five commitments the V2a design
encodes, named here so the build is read as doctrine, not just mechanism.

1. **The reservoir, not the queue.** Machine question-generation outruns human
   answering by orders of magnitude; the docket is a counted, never-dropped
   reservoir of which the budget surfaces a handful — triage under asymmetry is
   the economy's whole job.
2. **The landscape shifts by recomputation.** An answer changes M; the next cycle
   regenerates candidates from the changed M, so mooted question-lines vanish and
   new ones arise without dependency bookkeeping.
3. **Latency-indifference.** The author's answer rate may vary freely; wants age
   but persist; silence lowers priority, never deletes; an unanswered note pauses
   the flow. The system is structurally incapable of impatience.
4. **The bilateral loop.** The author's engagement depends on their model of
   Arisbe; Arisbe earns answers with question quality (P2¹³) and by showing its
   conjectures. Two models co-evolve; the engagement rate is set by the weaker
   one. Corollary — **the rate economy**: four rates (world change, machine
   processing, author answers, decay) govern the regime; ttl and the budget are
   the two rate-matching knobs the system owns; poise is the observable of their
   ratios. And the halting dual: a closed Arisbe either crystallizes (no decay —
   Conway's still-life) or evaporates (decay — the faded blank); the membrane
   both bounds AND animates (Peircean Secondness: the world never lets us alone).
5. **The interlocutor criterion** (quote the author): *"When I can legitimately,
   and in no way differently than when asking another person, ask Arisbe 'what do
   you want to know?' and Arisbe answers meaningfully, then Arisbe (or any similar
   agent) is an equal interlocutor."* The oracle notes are the first concrete
   answer surface for that question — the docket read aloud with its reasons;
   "meaningfully" is P2¹³'s bar; "equal" stays inside Doubt 4's rail
   (admission-as-fellow-inquirer, never worth). The author's follow-up gloss,
   verbatim: *"Equal not in any competence sense, but simply in the sense that,
   in a Rorty way of looking at it, we stand together as players of the game —
   with our particular skills, we risk, we try, we imagine, we aid, we wonder,
   we long, we fear, and in solidarity, we do our best."* This is the solidarity
   half of the Concordances chapter's middle position
   (`docs/CONTRIBUTION_AND_PRIOR_ART.md` §"Concordances"): solidarity supplies
   standing, the calculus supplies validity.

## RUN 13 — pre-registered priors (draft for the author's amendment before launch)

- **P1¹³ (retrodiction):** trained on notes through month *m*, the model's forecasts
  about month *m+1*'s activity (which clusters grow, which notes get revisited) beat
  a frequency baseline on a held-out slice — and, at the journal's scale, trained
  through year *y*, forecasts about year *y+1*'s entry rhythm and recurring themes
  beat the same baseline across at least two decades of held-out spans.
- **P2¹³ (legible questions):** the docket generates questions about the author that
  the author rates non-trivial at better than a stated base rate (author-judged
  sample per segment).
- **P3¹³ (bounds hold):** decay bounds |M| with per-round cost flat across the full
  vault scale; horizon counted, never silently dropped.
- **P4¹³ (provenance inquiry works):** the loop's authored-vs-collected verdicts
  agree with the author's own judgment on a sampled subset (the author as ground
  truth about the author), with `Clippings/` recovered without being told its
  meaning.
- **P5¹³ (diachrony legible):** a topic's treatment-over-time reads correctly in the
  audit lens for at least one exemplar topic the author picks — with the journal's
  50-year span as the K2 showcase: at least one **disposition** (a habit standing
  across decades) and one **mood** (a state that faded) legibly separated by the
  decay clock.

## Out of scope this cycle

The tutor loop's build (its own authorization); B-full; any web-lens work; any
modeling of third parties (their appearance in M is only as the author's relations,
metadata-level).

## Open items (the author's, non-blocking for the plan)

1. Third-party folders: keep metadata-only, or widen consent?
2. V2 interruption budget + surface.
3. P-priors: amend/replace before launch.

## V0 build record (2026-07-18)

Stage V0 (the metadata membrane) built via subagent-driven execution, eight TDD tasks,
per-task adversarial review, commits `402ab0e..c792a07`. **Modules:** `src/probe_feed.py`
(the socket base extracted from the rung-1 arithmetic feed — the drain-refill propose
loop, model-delta yield reading via `m_view`, the FIFO/scatter baseline choosers,
`replay_choices`, and the **count-or-refuse dispatch rule** — a chosen want the feed
cannot voice is refused and counted in `self.refused`, never silently dropped, now live);
`src/vault_world.py` — `VaultWorld` (the reader: `notes`/`note_facts`/`folder_listing_facts`/
`attachment_items`/`probe_cost`, structure-only per the custody constraint — path, folder,
frontmatter date/tags, wikilinks, size/mtime, never body content) + the journal reader
(`journal_paths`/`journal_entries`/`journal_facts`/`journal_horizon_items`, the two
timelines held apart — event-time a claim, writing-time absent by design, malformed
date-lines flagged to the horizon rather than mis-dated) + `VaultFeed` (the socket's
fourth `Proposer` consumer, the journal seeded at severity 8.0 so the author's own
datelined voice outranks a folder scan). The **horizon register** (designed in Task 2,
deferred to this stage by the spec above) is live: attachments (PDF/image/canvas) and
malformed journal date-lines register as `HorizonItem`s at seed time, retained/counted/
re-attemptable, nothing silently dropped. **The root-bucket fix:** Task 5's adversarial
review caught that `_top_dir` returned `""` for a root-level note, and `""` is falsy —
`top_dirs()` built `{self._top_dir(n) for n in self.notes()}` and a falsy top silently
dropped out of that set, so root-level notes were never scanned, never read, never
horizoned. Fixed by `ROOT_BUCKET = "(root)"`, a genuine non-empty bucket name flowing
uniformly through every `_top_dir` consumer (commit `3f98c6c`, same-session fix-loop —
the bug found and closed inside Task 5, not carried to a later task).

**Custody** verified adversarially in review, not merely asserted: the `SENTINELBODY`
sentinel word planted in the fixture's note bodies and journal entries is asserted
absent from every emission across the Task 3/4/5 review diffs; the driver's only
`print` (Task 7) was grepped line-by-line to confirm its digest carries counts and
kind/reason-keyed tallies only, never a note id, title, or path; `git check-ignore -v`
confirmed `runs/run13/` (and everything under it) matches the whole-directory
`.gitignore` rule; and this task independently re-checked `git log --all` for
`runs/run13/*` and for the `SENTINELBODY` sentinel across all of `runs/*` history —
both empty, nothing vault-derived has ever been tracked.

**Test counts:** `test_vault_world.py` 13 · `test_probe_feed.py` 2 · (carried, unchanged)
`test_attention_economy.py` 19 · `test_arithmetic_world.py` 20. Full suite (2026-07-18):
**3712 passed, 137 skipped, 1 xfailed, 0 failed** (1325.98s / 0:22:05) — no regressions
from the arithmetic-stage baseline.

**Carried-forward Minors** (none blocking, none silently swallowing data):
- The `_refill` outstanding-read cap of 5 is correctly wired (verified in isolation) but
  never exercised end-to-end by the fixture drive — the fixture's whole note set fits
  under the cap in one scan pass, so the severity-2.0 linked-note boost never fires
  against a full window. Will bite on a vault where discovery outpaces the cap.
- The journal file is also a plain `.md` note, so `Personal/.../Journal.md` is scanned
  and read as an ordinary note *in addition to* being probed via its dedicated `journal`
  want — a double-want by design of the existing reader API, not a bug (no double-refusal
  risk; both executions succeed independently).
- `Horizon.register`'s dedup-vs-cap ordering is tested at "dedup while under cap" and
  "new ref while at cap" but not at "duplicate ref submitted after the horizon is
  already full" — untested, not known-broken.

**Post-review fixes (2026-07-18)** — the final whole-branch review (one Important +
two riders), applied in one commit:
- **Journal entry ids namespaced per file** (Important): `journal_facts` built
  `eid = f"j:L{line_no}"` with no file component, while `journal_paths()` globs
  `Journal*.md` vault-wide — a second Journal-prefixed file would silently merge its
  `j:L1` with the main journal's, conflating timelines. Fixed:
  `eid = f"{_const(relpath)}#L{line_no}"` (e.g.
  `Personal/Journal-x/Journal.md#L1`); `journal_horizon_items`'s refs carry the same
  convention. A second fixture journal (`Personal/Journal-x/Journal-old.md`) proves the
  two files' entry ids are disjoint (`test_journal_ids_namespaced_per_file`).
- **Case-variant `.MD` files no longer invisible** (rider): `_attachment_paths`'s
  `.md` exclusion is now case-SENSITIVE (`p.suffix != ".md"`, was `.lower() != ".md"`),
  so a file like `Note.MD` — already invisible to `notes()`'s case-sensitive
  `rglob("*.md")` — now reaches the horizon instead of being dropped by both registers
  at once (`reason="case_variant_md"`, distinguished from ordinary binaries). Fixture:
  `attachments/ODD.MD` (`test_case_variant_md_reaches_the_horizon`).
- **Driver double-nesting retired** (rider, formerly a carried Minor above):
  `tools/run_vault_v0.py` now constructs `TomosService(runs_dir)` directly —
  `TomosService` already appends its own `universes/` layer, so the old
  `TomosService(runs_dir / "universes")` produced `universes/universes/...`. Verified
  by a fresh `--fixture --rounds 10` smoke run: single `universes/` level, digest
  printed, exit 0.

`test_vault_world.py` is now 15 (13 + 2 new, both above).

**RUN 13 awaits the author's launch:**
`uv run python tools/run_vault_v0.py --rounds 200 --segments 3`

## V2a.1 build record (2026-07-18)

V2a.1 (the oracle notes loop) built via subagent-driven execution, four TDD tasks,
per-task review, on top of Stage V0/V1. **Modules:** `src/oracle_notes.py` (new) —
`QuestionCandidate` + `seal` + `candidates_from_run` (four deterministic sources:
provenance/Clippings, multi-journal, horizon, the standing writing-time reflective)
+ `render_note`/`select_within_budget` (budget-enforced markdown rendering, qid
recovery via an invisible `<!-- qid: ... -->` comment) + `parse_note`/`score`
(the author's edits recovered from raw markdown; a deliberately modest
case-insensitive substring heuristic, named as such) + `OracleLedger` (JSONL
`forecasts.jsonl`/`outcomes.jsonl`, `asked_ever` the standing-question suppressor,
`build_reveals` joining answers to sealed forecasts) + `conjectures_section` (a
plain-English gloss of each admitted law, `eg_to_english` preferred, a structural
fallback regex, an honest placeholder beyond that). **Reader exclusion** in
`src/vault_world.py`: an `authored_by: arisbe` note emits only `(arisbe_note "id")`
from both `note_facts` and `folder_listing_facts` — Arisbe's own ink never becomes
author-evidence about its own author. **Driver wiring** in `tools/run_vault_v0.py`:
`_run_oracle`, called once after the LAST segment only — resolve/create the oracle
dir (`<root>/Arisbe/` real-vault mode, `<runs_dir>/arisbe_notes/` fixture mode);
read the newest prior note (if any), record every answer/decline/ignore into the
ledger, build reveals, adopt the (possibly author-edited) budget knob; block on a
previous note that isn't yet substantially answered and hasn't been waved off;
otherwise build candidates (suppressing anything ever asked), budget-select,
render (with reveals + conjectures from the final segment's `known_laws`/
`discoveries`), write, and record each asked question. `--note-date` is the one
new CLI flag — the single sanctioned wall-clock read in `main`, injectable for
tests. Two review-mandated guards, both driver-level: **never write a note with
zero questions** (`oracle: no questions this cycle`, printed and skipped rather
than emitting an empty file — the natural outcome once a small/closed vault's
candidate pool is fully `asked_ever`-exhausted, exercised end-to-end by the
fixture); and **an unparsable budget knob is announced, not silently guessed**
(`oracle: budget knob unparsed - using defaults`, backed by a new
`ParsedNote.budget_parsed` field). Numbers-only stdout discipline extended, not
loosened: the only path ever printed is the note's *vault-relative* name
(`Arisbe/Questions-<date>.md`), never a filesystem path — in `--fixture` mode the
note physically lives under `--runs-dir`, never under the checked-in fixture tree.

**A real defect found by the end-to-end test, not by the unit tests:** the fixture's
own `Clippings/saved page.md` has a space in its filename, so its qid
(`prov:Clippings/saved page.md`) carries a space too — `_QBLOCK_RE`'s original
`(?P<qid>\S+)` capture silently failed to match that whole question block (it fell
through as unparsed stray prose, its answer unrecoverable) whenever a real vault
path contains whitespace, which real vault paths routinely do. Tasks 1–3's unit
tests never exercised this because their hand-built qids (`"q1"`, `"prov:<id>"`
over synthetic short ids) never contained a space. Fixed: the qid group is now
`[^\n]+?` (non-greedy up to the literal `" -->"`), with a regression test
(`test_qid_containing_a_space_is_recovered`) pinning the fix directly. This is the
argument, in miniature, for why Task 4's end-to-end test drives the actual fixture
through the actual driver rather than only synthetic candidates.

**Test counts:** `test_oracle_notes.py` 18 (4 render/candidates + 3 parse/budget +
1 score + 2 ledger + 3 conjectures + 2 substantially-answered + 3 end-to-end,
Task 4's class covering: the answer→outcome→reveal→exhaustion cycle against the
real fixture and the review-mandated zero-questions guard; a seeded low-budget
note leaving a genuine remainder for a second note with reveals; the
unparsed-budget-knob warning) · `test_vault_world.py` 22 (15 carried + the Task 3
reader-exclusion class + one more). Both green together with
`test_attention_economy.py` (19) and `test_probe_feed.py` (2) — no shared-fixture
interference. Full suite run once, foreground, at the end of Task 4 (see the
session's commit for the verbatim tally).

**Deferred to V2a.2** (named, not silently dropped): banking an answered forecast
into M as a quoted attributed cell (`(asserted "author" ⌜…⌝)`, provenance
`oracle-answer`) via the quotation machinery — V2a.1 only banks answers in the
run's side-store (the ledger) with marker facts, M itself is untouched by an
answer; multi-paragraph answers (the Task 2 review's stated priority — the current
parser recovers only the first paragraph of an answer that itself contains a blank
line, a documented heuristic limit, not a claim of full prose understanding); and
real NL interpretation of an answer's content (today's `score` is a deliberately
modest case-insensitive substring match, named as such in its own docstring).

**V2a.2 — ✅ AUTHORIZED 2026-07-19 (the author), in this order:** (1) multi-paragraph
answers (the review's priority — the author's reflective answers will be
multi-paragraph); (2) quotation-cell banking of answers into M (the B-min use case —
and one of the two named wake-sources for the B-full gate); (3) answer
NL-interpretation by explicit episode. **Timing:** the build starts after RUN 13
produces its first real questions note and the author has answered once — one real
round informs the parser fix.
