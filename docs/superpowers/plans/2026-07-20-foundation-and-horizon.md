# Foundation & Horizon (Workstream A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture the 2026-07-19/20 commens/community doctrine into a new doctrine doc, rewrite `docs/ROADMAP.md` as the four-workstream program, and add a minimal ripple set — **docs only, no code**.

**Architecture:** Three documentation deliverables per the approved spec [docs/superpowers/specs/2026-07-20-foundation-and-horizon-design.md](../specs/2026-07-20-foundation-and-horizon-design.md): (1) a new doctrine doc `docs/THE_COMMENS_AND_THE_COMMUNITY.md` with a visible `[ratified]`/`[flagged]` register and a closing Open-verdicts list; (2) a rewrite of `docs/ROADMAP.md` in place; (3) four small ripple edits so the new vocabulary isn't stranded. All wider harmonization is routed to sweep B (workstream B), not done here.

**Tech Stack:** Markdown; git; grep-based verification (no test suite, no `src/` change).

**The spec is the content source of truth.** Deliverable 1's 11-section list, Deliverable 2's structure, and Deliverable 3's four edits in the spec are the *complete* content specification. This plan sequences and verifies the build and cites the spec by section for prose content rather than duplicating ~2,500 words of doctrine (DRY). Read the spec section named in each step before writing.

## Global Constraints

- **Docs only.** No `src/` change; `tools/core_protection_system.py --report` must stay clean (trivially — nothing under `src/` is touched). No file added to `docs/_quarto.yml` (book membership is workstream B's decision).
- **Two registers, visibly distinct.** In the doctrine doc, every section carries a `*[ratified]*` (author stated/corrected it this sitting) or `*[flagged]*` (assistant elaboration, awaiting the author's verdict) tag; sections with a ratified spine and a flagged detail carry both and mark the flagged sentences in situ. **Every `[flagged]` item must also appear in the closing Open-verdicts list (§11).**
- **The "final"-family ban.** No touched doc may contain "final opinion", "converges to [truth]", or "the answer" as an *assertion* — only where the doctrine doc quotes them in §7 to forbid them. Use "tends", "the current best-attested", "open".
- **Exact vocabulary.** Use the doctrine doc's terms precisely everywhere: **UoD** = the internalized, attested model *inside the membrane*; **commens** = the un-possessed, participation-sustained social construct *outside* it (never "the corpus is the commens"). So workstream B starts from a conforming baseline.
- **Only the four ripple targets** are edited besides the two primary deliverables: `docs/GLOSSARY.md`, `docs/THE_KYTOS.md`, `docs/THE_MEASURE_OF_KNOWLEDGE.md`, `docs/CONTRIBUTION_AND_PRIOR_ART.md`. Anything else = defer to B.
- **Commit granularity.** One commit per task (three commits total). *This refines the spec's "doctrine + ripples in one commit" to one-commit-per-task — which strictly improves the spec's own stated rationale (each deliverable independently reviewable and revertible). Flagged here rather than silently changed.*
- **Commit trailer.** End every commit message with:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

## File Structure

- **Create:** `docs/THE_COMMENS_AND_THE_COMMUNITY.md` — the doctrine doc (epigraph + 11 tagged sections + cross-links). Task 1.
- **Modify:** `docs/GLOSSARY.md` — new **Commens** key-term entry (near World-scroll/Kytos); augment the **UoD** abbreviation entry (line ~61) with the per-instance/inside-the-membrane sense + doctrine-doc pointer. Task 2.
- **Modify:** `docs/THE_KYTOS.md` — one pointer paragraph appended to §4 (line ~88, "The quantitative frontier (West)"). Task 2.
- **Modify:** `docs/THE_MEASURE_OF_KNOWLEDGE.md` — one clause at guard 3 (line ~93, "Never a scalar over agents"). Task 2.
- **Modify:** `docs/CONTRIBUTION_AND_PRIOR_ART.md` — two concordance entries in §Concordances (line ~125). Task 2.
- **Modify:** `docs/ROADMAP.md` — full rewrite in place. Task 3.

---

## Task 1: The doctrine doc

**Files:**
- Create: `docs/THE_COMMENS_AND_THE_COMMUNITY.md`

**Interfaces:**
- Consumes: the spec's **Deliverable 1** section list (the complete content spec) and the new **Mention-ascent** GLOSSARY entry (already committed 2026-07-20) for the §8 cross-reference.
- Produces: the doctrine doc that Task 2's ripple edits cross-link and Task 3's ROADMAP cites as the program frame.

- [ ] **Step 1: Write the document head.** Create the file with: an H1 title `# The Commens and the Community`; a status line matching the house pattern (see `docs/THE_KYTOS.md` head — date `2026-07-20`, a one-line "design-of-record / doctrine" note, and *"Not in `_quarto.yml` — book membership deferred to workstream B"*); then the **epigraph** — Job 42:5–6 in Robert Alter's translation, as a Markdown blockquote:

```markdown
> By the hearing of the ear I heard You,
> and now my eye has seen You.
> Therefore do I recant, and I repent in dust and ashes.
>
> — Job 42:5–6, trans. Robert Alter
```

- [ ] **Step 2: Write sections 1–10** exactly per the spec's Deliverable 1 section list, in order, each as an H2 (`## 1 · The pair: UoD and commens`, etc.), each carrying its `*[ratified]*` / `*[flagged]*` tag on the heading line or first sentence. Reproduce the spec's content for each section faithfully (it is the requirements). Critical content anchors that must survive:
  - §1: the UoD/commens definitions; commens = **social construct sustained only by participation** ("if we don't participate, it disappears"), real-for-participants yet not pre-given, *open and precarious*; the corpus ≠ commens warning.
  - §3: institutionalization = reciprocal typification among *types of actors*, cannot occur in an individual; the three roles as a good-regulator *model* (Conant–Ashby), "model-of, never instance-of".
  - §7: the "final"-family ban-list stated here (the only licensed place those words appear, in quotes).
  - §8: cross-reference `[Mention-ascent](GLOSSARY.md#mention-ascent)` and the Dau Ch. 26 reduction argument.
  - §10: the entailment — solitary ceiling below the community's *by kind*; connection *sustains* the commens, withdrawal is *dissolving*.

- [ ] **Step 3: Write §11 — Open verdicts.** Gather every `[flagged]` item (from §§2, 3-detail, 4-coupling, 5-mapping, 6, 8-formulation, 9) as a numbered list, each a crisp yes/no or phrasing choice for the author's later ruling (per resolved OQ3).

- [ ] **Step 4: Add the cross-links-out line** near the head or foot: Markdown links to World-scroll, Kytos, Mention-ascent (all in `GLOSSARY.md`), and `THE_MEASURE_OF_KNOWLEDGE.md`, `BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md`, `MODALITY_WITHOUT_GAMMA.md`, `FIDELITY_A_PLAIN_ACCOUNT.md`, `CATEGORIES_AND_THE_THREE_PARTS.md`, `CONTRIBUTION_AND_PRIOR_ART.md`.

- [ ] **Step 5: Verify — tags.** Run:

```bash
grep -cE "\*\[ratified\]\*|\*\[flagged\]\*" docs/THE_COMMENS_AND_THE_COMMUNITY.md
```

Expected: ≥ 11 (each of the 11 sections tagged; sections with both tags count more). If any section heading lacks a tag, add it.

- [ ] **Step 6: Verify — flagged items all reach §11.** Manually confirm each `[flagged]` section is represented in the §11 Open-verdicts list (the flagged set is §§2, 3-detail, 4-coupling, 5-mapping, 6, 8-formulation, 9 → expect ~7 verdict entries). Fix omissions.

- [ ] **Step 7: Verify — ban-list.** Run:

```bash
grep -niE "final opinion|converges? to (the )?truth|\bthe answer\b" docs/THE_COMMENS_AND_THE_COMMUNITY.md
```

Expected: matches **only** inside §7's ban-list (where the words are quoted to forbid them). Any assertion-use elsewhere must be reworded.

- [ ] **Step 8: Verify — internal links resolve.** Run:

```bash
grep -oE "\]\(([A-Za-z0-9_./#-]+)\)" docs/THE_COMMENS_AND_THE_COMMUNITY.md \
  | sed -E 's/^\]\(//; s/\)$//' | sort -u \
  | while read -r t; do case "$t" in \#*) : ;; *#*) f="docs/${t%%#*}"; [ -e "$f" ] || echo "MISSING FILE: $t" ;; *) [ -e "docs/$t" ] || echo "MISSING: $t" ;; esac; done
```

Expected: no `MISSING` lines (same-doc `#anchor` links checked by eye — confirm each `#anchor` matches an H2 in this file or a real heading in the target).

- [ ] **Step 9: Commit.**

```bash
git add docs/THE_COMMENS_AND_THE_COMMUNITY.md
git commit -m "The commens/community doctrine committed as a standing doc: UoD vs the participation-sustained commens, roles as good-regulator model, no-final, thirdness kept operational

Author's spine ratified; assistant glosses flagged with a closing Open-verdicts
list (author to rule later per OQ3). Epigraph: Job 42:5-6 (Alter). Not yet in
the Quarto book (workstream B's call).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: The ripple set

**Files:**
- Modify: `docs/GLOSSARY.md`, `docs/THE_KYTOS.md`, `docs/THE_MEASURE_OF_KNOWLEDGE.md`, `docs/CONTRIBUTION_AND_PRIOR_ART.md`

**Interfaces:**
- Consumes: the doctrine doc from Task 1 (every ripple cross-links it) and the spec's **Deliverable 3**.
- Produces: the minimal in-place vocabulary so older docs point at the doctrine; everything else is B's.

- [ ] **Step 1: GLOSSARY — Commens entry.** In `docs/GLOSSARY.md`, add a new key-term entry near the M/community cluster (after `### World-scroll`, before `### The explicit M-steps…`):

```markdown
### Commens
**Commens** (Peirce, the 1906 Lady Welby letters — "all that is, and must be, well understood
between utterer and interpreter" for a sign to function) — the between/outside/before/after that
makes communication possible without being possessed: interacted-with, never internalized, and
**not an Arisbe structure** (it is *not* the attested corpus — that is the internalized
[UoD](#uod)). A **social construct** in Berger & Luckmann's sense: real-for-participants (it
confronts them with facticity, exceeds any one of them) yet **sustained only by participation** —
*if we do not participate, it disappears* — so it is open *and precarious*, continuously
reproduced rather than pre-given or timeless. Regulative, never to be operationalized. Genuine
institutionalization and the commens are **community-level emergents** (a change in kind, not
degree, above the single instance). See
[THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md),
[World-scroll](#world-scroll), [Kytos](#kytos-the-semiotic-cell),
[Mention-ascent](#mention-ascent).
```

- [ ] **Step 2: GLOSSARY — sharpen UoD.** In the existing `### UoD` abbreviation entry (line ~61), append a sentence naming the per-instance sense:

```markdown
As a *standing concept* (not only the abbreviation): a UoD is the immediately
accessible / controllable / **attested internal model inside the membrane** — what an Arisbe
instance thinks *with*, the internalized complement of the un-possessed
[Commens](#commens). See [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §1.
```

- [ ] **Step 3: THE_KYTOS pointer.** In `docs/THE_KYTOS.md`, append one paragraph to §4 (line ~88, "The quantitative frontier (West)"):

```markdown
**The measurable bridge to West (2026-07-20).** Each kytos carries a measurable S (UoD-management:
|M|, the K3 ratio, peel cost, decay TTL, admission rates) and A (interaction: import/export
throughput, proposal rate, horizon size) — the automaton's own decomposition — coupled by one
attention budget, whose *allocation* **poise** reads (rigidity = S starves A; thrash = A starves
S). Modeling S/A/allocation scaling across a community is how West becomes operational rather than
metaphorical. But the community rung is a change in *kind*: reciprocal typification, and therefore
genuine institutionalization and the [commens](GLOSSARY.md#commens), **cannot occur in an
individual** — the three EPG roles inside one instance *model* the institution (good regulator),
never *constitute* it. Full treatment:
[THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md).
```

- [ ] **Step 4: THE_MEASURE_OF_KNOWLEDGE clause.** In `docs/THE_MEASURE_OF_KNOWLEDGE.md`, at guard 3 ("Never a scalar over agents", line ~93), append one sentence giving the ground:

```markdown
The ground of this guard is the commens: there is **no commens-scaled denominator** to normalize
K across agents, because no agent possesses the commens (a participation-sustained social
construct, not a God's-eye given) — so an aggregate scalar has nothing to be a fraction *of*. See
[THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §2.
```

- [ ] **Step 5: CONTRIBUTION_AND_PRIOR_ART concordances.** In `docs/CONTRIBUTION_AND_PRIOR_ART.md`, add two entries to §Concordances (line ~125), matching the existing bullet style:

```markdown
- **Berger & Luckmann (*The Social Construction of Reality*, 1966).** Objectivation and
  internalization; institutionalization as **reciprocal typification of habitualized actions by
  types of actors** — which *cannot occur in an individual*. The concordance under Arisbe's
  UoD/commens distinction and the honesty guard that the automated EPG *models* an institution
  rather than being one. See [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md).
- **Conant & Ashby (the good-regulator theorem, 1970; requisite variety, 1956).** "Every good
  regulator of a system must be a model of that system." The concordance licensing the three EPG
  roles as an instance's internal model of the institution of inquiry — *model-of, never
  instance-of*. See [THE_COMMENS_AND_THE_COMMUNITY.md](THE_COMMENS_AND_THE_COMMUNITY.md) §3.
```

- [ ] **Step 6: Verify — each target cross-links the doctrine doc.** Run:

```bash
for f in docs/GLOSSARY.md docs/THE_KYTOS.md docs/THE_MEASURE_OF_KNOWLEDGE.md docs/CONTRIBUTION_AND_PRIOR_ART.md; do
  grep -q "THE_COMMENS_AND_THE_COMMUNITY.md" "$f" && echo "OK  $f" || echo "MISSING LINK  $f"; done
```

Expected: four `OK` lines.

- [ ] **Step 7: Verify — ban-list across the ripple edits.** Run:

```bash
grep -niE "final opinion|converges? to (the )?truth|\bthe answer\b" docs/GLOSSARY.md docs/THE_KYTOS.md docs/THE_MEASURE_OF_KNOWLEDGE.md docs/CONTRIBUTION_AND_PRIOR_ART.md
```

Expected: no new assertion-use introduced by these edits (pre-existing unrelated matches, if any, are out of scope for Task 2 and belong to sweep B — eyeball that the edits themselves added none).

- [ ] **Step 8: Commit.**

```bash
git add docs/GLOSSARY.md docs/THE_KYTOS.md docs/THE_MEASURE_OF_KNOWLEDGE.md docs/CONTRIBUTION_AND_PRIOR_ART.md
git commit -m "Ripple set: seat the commens/UoD vocabulary in GLOSSARY, KYTOS, MEASURE, and PRIOR_ART

A new Commens glossary entry + a sharpened UoD sense; the S/A-to-West measurable
bridge and the can't-institutionalize-in-an-individual cap pointered into KYTOS;
the vector-not-scalar guard grounded in the commens in MEASURE; Berger/Luckmann
and Conant-Ashby added as concordances. Each cross-links the doctrine doc. Wider
harmonization deferred to workstream B.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: The ROADMAP rewrite

**Files:**
- Modify: `docs/ROADMAP.md` (full rewrite in place)

**Interfaces:**
- Consumes: the spec's **Deliverable 2** structure; the doctrine doc (cited as the program frame); the current `docs/ROADMAP.md` (for the carried-forward items + discharged tail).
- Produces: the single canonical "what's next" doc organized by the four workstreams.

- [ ] **Step 1: Read the current ROADMAP** (`docs/ROADMAP.md`) to harvest the still-live items (#3 use-fork, #6 NL fast-follows, #7 EPG contest-UX, #8 tension, #9 layout-perf, #10 narration, #11 schema-drawing, #12 Departure-I, #13 B-full, #17 directed-engagement) and the done items for the discharged tail (#1, #2, #4, #5, #14, #15, #16).

- [ ] **Step 2: Rewrite the file** per the spec's Deliverable 2 structure, in this order: header note ("re-consolidated 2026-07-20; superseding the 2026-06-27 consolidation") → **Preamble** (the four workstreams by verb Share · Use · Run · Understand; the doctrine doc cited; the entailment stated up front) → **Workstream A — Understand** (this sub-project; shipped-when-committed; points at the doctrine doc's Open-verdicts) → **Workstream B — Share** (the sweep + the five publication-thesis candidates with venue notes; first-paper choice **(author decision)**) → **Workstream C — Run** (the membrane: UoD-per-instance made code-real, unify import/export into one seam / the gestured `ImportExportManager`, S/A instrumentation symmetry, payoff = Q-B/West experiment runnable; gate: rung-2 ethics pass) → **Workstream D — Use** (UX; first deliverable = the issue inventory; then tiered fixes under the Charter) → **Carried-forward items** (each keeping its old number, under its workstream, with an owner-decision tag or next action) → **Discharged tail** (done items, one line each, incl. mention-ascent ⓪+①, the automated-EPG arc, vault V0→V2a.2(2)) → **Standing runs** (RUN 13 in flight; RUN 12 disposed 2026-07-20 awaiting the author's priors ruling).

- [ ] **Step 3: Apply the two throughput rules.** Confirm every item has an owner-decision tag *or* a concrete next action, and that the doctrine vocabulary (UoD/commens, no "final") is used exactly.

- [ ] **Step 4: Verify — structure present.** Run:

```bash
grep -cE "^## Workstream [A-D]" docs/ROADMAP.md   # expect 4
grep -qE "Standing runs" docs/ROADMAP.md && echo "standing-runs OK" || echo "MISSING standing-runs"
grep -qE "superseding the 2026-06-27" docs/ROADMAP.md && echo "supersede-note OK" || echo "MISSING supersede-note"
```

Expected: `4`, `standing-runs OK`, `supersede-note OK`.

- [ ] **Step 5: Verify — carried numbers survive.** Run:

```bash
for n in 3 6 7 8 9 10 11 12 13 17; do grep -qE "#?$n[^0-9]" docs/ROADMAP.md || echo "carried item #$n MISSING"; done
```

Expected: no `MISSING` lines (each still-live old number appears in the rewrite).

- [ ] **Step 6: Verify — ban-list + doctrine-doc citation.** Run:

```bash
grep -niE "final opinion|converges? to (the )?truth|\bthe answer\b" docs/ROADMAP.md   # expect no assertion-use
grep -q "THE_COMMENS_AND_THE_COMMUNITY.md" docs/ROADMAP.md && echo "frame-cited OK" || echo "MISSING frame citation"
```

Expected: no ban-list assertion-use; `frame-cited OK`.

- [ ] **Step 7: Verify — cross-file sweep (all touched docs).** Run link-integrity across every file this plan touched and confirm the protected core is clean:

```bash
for f in docs/THE_COMMENS_AND_THE_COMMUNITY.md docs/ROADMAP.md docs/GLOSSARY.md docs/THE_KYTOS.md docs/THE_MEASURE_OF_KNOWLEDGE.md docs/CONTRIBUTION_AND_PRIOR_ART.md; do
  grep -oE "\]\(([A-Za-z0-9_./#-]+)\)" "$f" | sed -E 's/^\]\(//; s/\)$//' \
    | while read -r t; do case "$t" in \#*) : ;; *#*) g="docs/${t%%#*}"; [ -e "$g" ] || [ -e "${t%%#*}" ] || echo "$f -> MISSING ${t}" ;; *) [ -e "docs/$t" ] || [ -e "$t" ] || echo "$f -> MISSING ${t}" ;; esac; done
done
uv run python tools/core_protection_system.py --report >/dev/null 2>&1 && echo "core-protection OK" || echo "core-protection: check output"
```

Expected: no `MISSING` lines; `core-protection OK` (nothing under `src/` changed).

- [ ] **Step 8: Commit.**

```bash
git add docs/ROADMAP.md
git commit -m "ROADMAP re-consolidated as the four-workstream program (Share/Use/Run/Understand), superseding the 2026-06-27 spine

Rewritten in place around the doctrine doc's frame: connection outward as the
entailment, the four workstreams as its concrete forms, carried-forward items
kept under their old numbers, a discharged tail folding in the arcs the old
ROADMAP predated (automated-EPG, vault, mention-ascent), and a new Standing-runs
section (RUN 13 in flight; RUN 12 disposed, priors ruling the author's).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Notes for the executor

- **No test suite runs** — this workstream is prose. The "tests" are the grep-based verification steps; run them and read the output. Where a step says "eyeball", a human/agent read is the check.
- **Content lives in the spec.** Do not invent doctrine; transcribe and lightly polish the spec's Deliverable-1/2/3 content. If a spec sentence and this plan disagree, the **spec governs** — flag the discrepancy rather than guessing.
- **The flagged glosses stay flagged.** Do not "resolve" any `[flagged]` item into ratified doctrine; per OQ3 the author rules on them later. The one exception: if executing a step is *impossible* without a ruling, stop and ask (that is the "critical to proceed" carve-out).
- **Scope discipline.** Touch only the six named files. Any temptation to harmonize another doc = note it for workstream B, do not do it here.
