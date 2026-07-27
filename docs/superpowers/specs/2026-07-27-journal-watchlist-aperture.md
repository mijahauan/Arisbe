# The Journal Watchlist Aperture (V2b-lite) — pre-registered design

**Date:** 2026-07-27. **Authorized by the author, same date** — ruling on RUN 13's F7¹³
(the content-distribution finding): *"Let's try option 3 first based on terms. It will be
interesting to see how much referencing simple terms will enable in modeling."*

**What this opens, stated plainly.** The first content-bearing channel onto the author's
journal: the machine may scan journal entry text **for an author-declared term list only**.
This is a deliberate, ruled widening of the V0 custody line (path/folder/frontmatter/tags/
wikilinks = structure; prose = never read). The widening is a *lens, not a leak*: nothing
becomes an atom that the author did not name in advance.

## Custody contract

1. The machine reads entry text solely to test membership of **watchlist terms** —
   whole-word, case-insensitive. No other token of prose is ever read into any structure.
2. Emitted atoms: `(mentions "<entry-id>" "<term>")` — the term as the author wrote it in
   the watchlist. Event-time joins ride the existing pinned `(entry_date …)` atoms.
3. A term longer than the 40-char bounded-constant invariant is **refused and counted**
   (count-or-refuse), never silently truncated.
4. The watchlist lives in the vault, author-editable in Obsidian:
   `<root>/Arisbe/Watchlist.md`. Format: `##` headers name term **groups** (e.g.
   `## disposition`, `## mood`); markdown list items under a header are that group's
   terms. The group names are the author's; the machine treats them opaquely.
5. Console digests stay aggregate-only: `watchlist_terms`, `watchlist_refused`,
   `mentions_atoms`, `entries_with_mentions` — never per-term counts, never entry ids.
   Per-term evidence lives only in M (the gitignored store), read locally.
6. `mentions` joins `JOURNAL_SPINE_RELATIONS` — **pinned from disuse-decay** (the same
   F4¹³ bedrock ruling: the spine is the standing longitudinal tier; its size is finite,
   ≤ |entries| × |terms|).

## Mechanics

- The scan rides the **existing single journal-file read** (the F3¹³ batch machinery):
  each entry's text span is tested against the watchlist as its batch is prepared; the
  batch's parseable conjunction gains the entry's `mentions` atoms. One file read, no new
  want kind, no economy change.
- The driver (`tools/run_vault_v0.py`) gains `--watchlist <path>` (default:
  `<root>/Arisbe/Watchlist.md` if present, else the channel is closed — absence of the
  file means the aperture stays shut; no flag, no scan).
- Fixture: a synthetic journal with planted terms across synthetic decades; the checked-in
  fixture tree is never edited in place (the vault-world custody test pattern, incl. a
  `SENTINELBODY`-style canary that a non-watchlist token never appears in any atom).

## Pre-registered priors (set before any real-vault scan; per-decade rates, not raw
counts — entry density varies by decade, so all reads are mentions ÷ entries-in-decade)

- **PW1 (the mood cutoff — the K2 mood half of P5¹³).** The author's testimony: a
  Christian worldview inhabited in youth, "largely abandoned about 20–30 years ago"
  (≈ 1996–2006). Operationalized: the **mood group's** per-entry mention rate over
  decades ≤ 1990s is at least **5×** its rate over decades ≥ 2010s (or the latter is
  zero). Pass = the aperture reads the life's shape from terms alone.
- **PW2 (the disposition spread — the K2 disposition half).** The **disposition group's**
  per-entry rate is nonzero in **≥ 3 distinct decades, including at least one of
  {2010s, 2020s}**.
- **PW3 (bounds hold under the aperture).** The pinned mentions tier is finite and the
  digest observables stay flat across rounds (the aperture adds read-time work only);
  refused terms counted, never dropped silently.
- **O1 (open observable, not a prior — the author's stated curiosity).** **Coverage**:
  the fraction of journal entries carrying ≥ 1 watchlist hit, reported per decade. "How
  much does referencing simple terms enable in modeling" — reported, not judged.

**Falsifiability note.** PW1/PW2 are calibrated by the author's own testimony, so either
outcome is informative: a failed PW1 means the term-lens is too weak to carry the life's
shape (aperture finding) *or* the testimony misremembers the timeline (a genuinely
interesting biographical finding) — the disposal must say which reading the author takes.

## Run plan

1. Build + fixture verification (TDD; suite green) — this sitting.
2. The watchlist itself is **authored by the author** (candidate list proposed in-session
   for editing; the machine never invents terms).
3. Real-vault run: a journal-focused segment (`--rounds 60` suffices — the ~40 journal
   batches are seeded at severity 8.0 and chosen early), author-launched or delegated
   explicitly. Digest + per-decade rate table (terms aggregated by group) → PW1–PW3
   disposal, author ruling, logged in RUN_13_LOG.
4. P5¹³ linkage: PW1+PW2 passing gives the mood/disposition separation **in event time**
   — the journal's 50-year span carrying it, as the original prior intended. Whether that
   satisfies P5¹³'s letter ("reads correctly in the audit lens") or its spirit read
   through the event-time lens is the author's disposal to make, honestly noted.
