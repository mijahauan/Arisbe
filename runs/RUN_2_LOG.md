# Run 2 log — the change stream (recentchanges)

**Pre-registration:** [docs/AUTOMATED_ENDOPOREUTIC_GAME.md §12](../docs/AUTOMATED_ENDOPOREUTIC_GAME.md)
— priors P1′–P7′ **affirmed by the author 2026-07-02, pre-run** (including the reversal-is-a-
discovery commitment on P2′, the `!bot` scoping, and the 0.2 legibility threshold). Findings are
about the wiki-world's *human editorial activity* as represented, and about the game — never the
world. *Progression, not progress.*

**Driver:** `uv run python tools/run_live_wikidata.py --source recentchanges --runs-dir runs/run2 …`

## Session header

| field | value |
|---|---|
| date / operator | 2026-07-02 · author + Claude (supervised sitting) |
| source | recentchanges (`!bot`), ids_per_poll 8, per_entity_cap 25 |
| ttl · segment_cap · min_interval_s | 30 · 25 · 10.0 |
| stops configured | max_seconds 3600 · max_m 200 · STOP file |
| code version (git SHA) | 9baeca3 |
| stop-file / kill+resume | exercised in run 1 (same machinery); not re-exercised |

## P7′ first — the operational floor (gates everything below)

| check | expected | observed | pass? |
|---|---|---|---|
| legibility per poll | < 0.2 (label lag on fresh edits); sustained rise = degradation | 0.00–0.06 across 9 polls | ✓ |
| checkpoints §3.3-attest, side store | all | 21/21, no refusals | ✓ |
| \|M\| bounded; elapsed bounded (F1 rider) | ≈ ttl; oscillating, checkpoint-dominated | \|M\| 10–35 (ttl 30); elapsed 31–403 s oscillating with atoms | ✓ |
| continuation (each poll picks up at the last newest timestamp) | no gaps/repeats beyond revisits | continuation survived the **crash + resume** (F1′) | ✓ |
| statements_dropped / unparseable_dropped | counted | 630 capped, counted · unparseable 0 (the fixed lexer made the run-1 crasher class legal; the gate stood ready) | ✓ |

**Totals:** 2 sittings (split by the F1′ crash) · 21 segments · **439 rounds** · 9 polls ·
53 distinct entities · 21 checkpoints attested. **Determinism canary green** (offline replay =
439 `new_fact`, the live trajectory exactly).

## Priors P1′–P6′ — observed vs expected

| prior | instrument | expected | observed | meta-disposition | note |
|---|---|---|---|---|---|
| P1′ dispositions | digests | new_fact dominant; **retract_fact > 0**; redundancy ≫ run 1 (the revisit working) | 439/439 `new_fact`; retract **0**; redundancy **0** | **missed both sub-claims** → `challenge_to_M` against P1′ (see F2′) | the prior's implicit revisit-rate assumption was quantitatively naive |
| P2′ mechanism durability (**the run's question**) | `mechanism_principles` | overturns occur; consensus < 1.0 | consensus 1.0 (n=219) · reliable_source 1.0 (n=140) — **vacuous again**; 0 deprecated even *sampled* | untested → horizon (F2′ names the fix) | the revisit *mechanism* is proven (the offline headline test); the live revisit *rate* at this breadth is ≈ 0 |
| P3′ working set | digests | \|M\| ≈ ttl; decay concentrates on abandoned entities | \|M\| 10–35; with zero revisits, *every* entity is abandoned — decay is pure churn | confirmed (trivially) | |
| P4′ rulebook | `resolution_principles`/`gaps` | zero thrash/gaps; `true:negation` consistently inert | one principle (`false:ground → new_fact`, stability 1.0, support 439); gaps none; **no negation ever reached the loop** | confirmed → `redundancy` | the `true:negation` consistency question stays open — no evidence either way |
| P5′ dialog shape | `proposal_shape` | ground + negation; negation ≫ run 1 | ground **554/554**; negation 0 | half-missed (negation prediction fell with the revisit assumption) | folded into F2′ |
| P6′ poise | `poise_from_digests` | ● dominant; ○ read against redundancy | **21/21 ●**, episode-level 1.00, zero stumbles | confirmed → `redundancy` | the baseline replicates across sources |

## Findings (dated, disposed)

### F1′ — the change stream is dirtier than the settled surface, and one bad string killed a segment (2026-07-02)
prior: P7′ · evidence: segment 5 crashed with `Unterminated string` — isolated in one step via
the recorded polls (the canary again) to a URL value carrying `#pid=1`: the EGIF lexer's
comment stripper was **quote-blind**, so the `#` amputated its own line. Run 1's crawl never
surfaced this; the stream's fresh human edits did, 100 rounds in ·
meta-disposition: **`challenge_to_M` against the ingestion contract — relinquished and
replaced, twice over**: (1) the lexer's comment stripping is now quote-aware (`#` inside a
constant is content; real comments still strip; corpus round-trip suites green), and (2) the
membrane gained a **parse gate** (`parseable_disputes` — a dispute whose claim/ground-truth
does not parse is dropped **and counted**, `unparseable_dropped`, surfaced with ⚠ in the
digest), plus `_const` now neutralizes control characters (newlines/tabs in fresh edits).
why / what it changes: the never-poison principle now holds *mechanically* at the membrane —
whatever exotic string the live world produces next, an unattended run degrades by one counted
dispute, not by death. And the crash/resume design passed its first unplanned test: only the
in-flight segment was lost; `--resume` continued from segment 4's state with the stream's
continuation point intact.

### F2′ — the change stream is a firehose of novelty, not a conversation (2026-07-02)
priors: P1′/P2′/P5′ · evidence: **53 distinct entities across 7 recorded polls, zero seen
twice** — over ~75 minutes of stream time, sampling 8 of the top ~50 non-bot changes per poll,
no entity was re-edited *and* re-sampled. Hence zero redundancy, zero retracts, zero negations,
and P2′ vacuous a second time · meta-disposition: **`challenge_to_M` against P1′ as stated —
relinquished** and replaced by the arithmetic: Wikidata's non-bot edit stream is thousands of
distinct items per hour; the probability that a *sampled* item recurs in a short window is
≈ 0, so recency-selection alone is not the revisit it looked like at headline-test scale.
why / what it changes: **the passive membranes are now both characterized** — the crawl samples
the settled surface (run 1), the stream samples the novelty frontier (run 2), and *neither*
revisits. What revisiting requires is **M's own state directing the reaches**: re-poll the
entities whose facts M currently holds (the warm-set re-poll named in run 1's horizon). That is
not a tweak — it is precisely the **directed-engagement/tropism module of §4d** (the
economy-of-research ordering of reaches), which this run converts from a philosophical
commitment into an *empirically mandated* next build. The instruments' verdict, in one line:
*ingestion alone cannot test durability; only directed re-engagement can.*

### F3′ — the baseline replicates across sources (2026-07-02)
priors: P4′/P6′ · evidence: same single resolution principle at stability 1.0, zero
thrash/gaps/friction, poise 1.00 with zero stumbles — on a *different* membrane than run 1 ·
meta-disposition: confirmed → `theorem_registration`.
why / what it changes: the monological-ingestion baseline is now a *cross-source* regularity of
game-with-Wikidata, not an artifact of the crawl. Any departure from it in the LLM-roles or
tropism runs will be attributable to the new machinery, not to source variance.

## Horizon (carried forward — the arc pauses here for the alpha-docs track)

- **The warm-set re-poll / directed engagement** (F2′) — the §4d tropism module is now the
  empirically mandated route to exercising P2′ (mechanism durability). The first tropism the
  system needs is the humblest one: *re-check what you hold*. *(Design drafted 2026-07-02 for
  the re-entry session: `docs/AUTOMATED_ENDOPOREUTIC_GAME.md` §13 — increment-1 shape, run-3
  draft priors P1″–P7″, five open author decisions.)*
- **`true:negation` consistency** (P4′) — still no evidence either way; falls out free once
  revisits deliver denials against standing targets.
- **Rigidity-at-exhaustion + stumble recovery** — still unexercised (both runs stayed poised
  throughout); a deliberately small frontier would exercise the ○ pole.
- **Attest wall-clock residual** (run 1 F1) — unchanged, named.
- The arc **pauses here**; the alpha-release documentation track resumes (author's decision,
  2026-07-02). These four items are the re-entry points.
