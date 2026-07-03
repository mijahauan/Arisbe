# Rate and Intelligibility

*Design note. Playback rate as the third axis of the in-view set — pre-registered hypotheses
and the UX rules they would earn, written **before** any spectator surface is built.*

**Status:** design note, 2026-07-03, drafted during the supervised run-3 sitting (crawl +
tropism). **Companion to** [`THE_MINIMAL_IN_VIEW_SET.md`](THE_MINIMAL_IN_VIEW_SET.md) (the
doctrine this extends — its §9 D-rules govern *co-presence*; the R-rules below govern
*succession*), [`ADAPTIVE_SCOPE_VIEWER.md`](ADAPTIVE_SCOPE_VIEWER.md) (the spatial LOD
machinery and the attestation style the temporal fog must inherit), and
[`AUTOMATED_ENDOPOREUTIC_GAME.md`](AUTOMATED_ENDOPOREUTIC_GAME.md) §4d/§13 (poise and the
tropism — the game-side machinery this doc mirrors on the reader's side). Method follows the
§11/§12/§13 discipline: hypotheses are registered here, bound to instruments that already
exist, before the build that would test them.

---

## 1. The claim

Stepping frame-by-frame through a movie yields only a hint of its dynamism, direction, and
force. For a reasoning process the analogous loss is not merely kinesthetic — it is
**categorical**. A single state of M shows Secondness: what stands scribed, which cuts
enclose what, a law written as a scroll. What no single state can show is whether that law is
*alive* — holding under re-engagement, absorbing newcomers, about to fall. That is habit,
Peirce's Thirdness, and it is constitutively a rate phenomenon: a regularity exists only
*across* states, never in one.

Run 3 is the concrete demonstration. Its character — the `non_revising` hum of habits holding
under warm re-poll, disuse-decay chewing the trailing edge, the working set pinned by
re-engagement rather than arrival order — appears in **no checkpoint**. It is entirely in the
succession. A viewer that can only frame-step (or only stack frames in space) makes the run's
most important properties invisible.

So display rate is not cosmetic. **Rate determines which logical categories are perceptible.**
"Moving pictures of thought," taken seriously, means the movie — not the stack of stills.

## 2. Position in the doctrine — the third axis

`THE_MINIMAL_IN_VIEW_SET.md` bounds what a reader can hold in view along two axes, both
selected by *what bears on the issue at hand*:

| axis | rules | mechanism | selects |
|---|---|---|---|
| **scope** (synchronic space) | §9 S-rules | adaptive-scope quotient + `attest_overview` | which *elements* are drawn |
| **co-presence** (diachrony displayed as space) | §9 D-rules | storyboard / time-stack lens | which *states* stand side by side |
| **rate** (succession) — *this doc* | R-rules, §5 | dwell policy + temporal placeholders | which *transitions* get dwell |

Note that the existing D-rules are still space-shaped: they decide how much history to lay
out, i.e. they flatten time into space. Rate is the genuinely temporal completion — attention
allocated *in* time. D2 already gestures at it ("inference lives in the movement"); the
R-rules make the movement itself the display medium.

**The mirror that vindicates the shape.** As of run 3 the *player* carries exactly this
machinery: the tropism is attention (directed re-engagement with what M holds warm),
disuse-decay is forgetting (the working-set bound on an unbounded sheet). Bounded agent,
unbounded record — identically the reader's problem with a run's history. The spectator
surface is the **reader's tropism**: a warm set of what to keep in view, a fog for what to
release, a rate policy for what deserves dwell. When the doctrine written for the reader and
the mechanism the game evolved for the player converge on one shape, that is the strongest
signal a design principle gives.

## 3. Ground truth comes free

Every hypothesis below is testable **without expert annotation**, because the game already
records machine ground truth for the properties a reader is asked to perceive:

- **dispositions** per round (`RoundOutcome` — revising vs `non_revising`);
- **stickiness / durability** per episode (`agon_metalearning.episodes_from`, decay-aware);
- **poise** per window (`poise_report` — engagement / settlement / absorption);
- **the ledger** (which relations are warm; what decay took);
- **the chain** itself (the fact of record every playback must reconcile to).

A reader's judgments are scored against the run's recorded facts — the same move as the
diagram↔narration scorer (`THE_MINIMAL_IN_VIEW_SET.md` §10): admissible because the machine
side of the correspondence is already attested.

## 4. The hypotheses (pre-registered)

Each is stated with its instrument and its falsifier. The first test corpus is the run-3
checkpoint sequence + episode record; N=1 author trials are directional only (§7).

**H1 — Categorical imperceptibility (the core claim).** A reader shown any single checkpoint,
or free frame-stepping through the sequence, cannot reliably distinguish a *live* law (held
under re-engagement) from a *dead* one (never re-engaged, or about to be relinquished) —
while a reader shown event-paced playback can. *Instrument:* stickiness/durability records as
ground truth; task = classify standing laws live/dead. *Falsifier:* still-readers match
movie-readers. If falsified, §1's claim is decoration and rate is mere comfort.

**H2 — Registration is a precondition, not polish.** Playback whose frames are independently
laid out (no pinning, no deltas, no camera hold) destroys change detection — everything
moves, so nothing is seen to move. Playback over registered frames (④a pins, presentation
deltas, the time-stack lens's rigid similarity registration — which already cut survivor
drift 45.9 → 11.9 world units on the Praeclarum chain) preserves it. *Instrument:* same
chain rendered both ways; task = name what changed at each step; measure accuracy + latency.
*Falsifier:* no difference. If confirmed, the ④a continuity investment is retroactively a
perceptual theorem, not a nicety.

**H3 — Disposition-weighted dwell ≈ constant information rate.** Event-paced playback with
dwell proportional to disposition weight (revising ≫ non-revising) yields better recall of a
run's revising events and more accurate run summaries than clock-paced uniform playback of
the *same total duration*. *Instrument:* disposition record as ground truth; task = recount
the run's events and their order. *Falsifier:* uniform playback equals or beats weighted.

**H4 — Texture, not elision.** Compressing redundancy stretches to *zero* (skipping them)
impairs the reader's judgment of habit *strength* — how settled M is — relative to
compressing them to a perceptible texture (a pulse without layout change, plus a count).
The hum carries information even when no frame differs. *Instrument:* ledger/stickiness as
ground truth; task = rank standing relations by settledness. *Falsifier:* skip-readers rank
as accurately as texture-readers.

**H5 — Temporal fog must be counted to be honest.** Readers given counted temporal
placeholders ("×25, all redundancy") reconstruct run statistics (length, redundancy
fraction, event density) accurately; silent elision produces systematic underestimates.
*Instrument:* digests as ground truth. *Falsifier:* elision-readers reconstruct as well.
This is the perceptual form of the standing **no-silent-caps** rule (`statements_dropped` is
counted; so must skipped time be).

**H6 — Rate is a LOD axis (temporal semantic zoom).** Properties readable at segment scale
(poise: engagement, settlement, absorption) are unreadable at round scale, and vice versa
(a single retraction's mechanics). A reader with a rate-zoom (round ↔ segment ↔ run) recovers
both; any fixed rate forces a choice. *Instrument:* questions pitched at each scale against
poise/disposition records. *Falsifier:* one fixed rate answers both scales as well as the
zoom does.

## 5. The UX rules the hypotheses would earn

Each rule is tagged with the hypothesis that vindicates it — if the hypothesis falls, the
rule falls with it. All are **regime-3** (presentation): dwell policy is style; the chain
remains the fact of record.

- **R1 — Event-paced master clock** (H3). The playback clock ticks on dispositions, not
  wall-time or round count. A round is milliseconds; the meaningful pulse is the move.
- **R2 — Disposition-weighted dwell table** (H3). `challenge_to_M` / retraction ≫
  `generalization` ≫ `new_fact` ≫ `non_revising`. The weights are a style knob (like
  `?tension`), user-adjustable, never fabricating drama the chain doesn't contain.
- **R3 — Redundancy compresses to texture, never to nothing** (H4). A `non_revising` stretch
  renders as a pulse without layout change plus a running count — the habit-holding hum stays
  perceptible. Skipping it silently is both a perceptual loss and an honesty violation.
- **R4 — Registration is mandatory in playback** (H2). Frames must be pinned/registered
  (④a pins, deltas, camera hold; the time-stack lens's rigid similarity fit is the proven
  mechanism). An unregistered movie is flicker, not motion.
- **R5 — Temporal placeholders are attested** (H5). Every compression carries its count, and
  what the playback shows *plus declares hidden* must equal the chain — `attest_overview`'s
  temporal twin. A movie that skips must say what it skipped.
- **R6 — One lens, three coupled LOD axes** (H6). Rate-zoom couples to spatial scope and
  in-view selection: zooming out in time (round → segment → run) should coarsen space in
  step (atom → region → M-silhouette), so "this atom appeared" and "this region churned all
  hour" are two positions of one control.
- **R7 — Rate never becomes a target.** The poise honesty clauses apply verbatim: dwell
  weights and playback statistics are perspectival instruments for a *reader*, never an
  objective for the run. Optimizing a run to "look dramatic" is the Goodhart failure §7
  guards against.

## 6. Where this lands (build path, for affirmation — not yet affirmed)

1. **Carrier:** the spectator surface — a read-only store wire (Organon accepting a run's
   checkpoint side store, e.g. `?store=runs/run3/checkpoints`) with a trailing
   latest-segment view. Small, display-side, regime-3; the §11 side-store discipline is
   preserved because the wire is read-only and never promotes.
2. **First corpus:** the run-3 filmstrip (checkpoint sequence rendered frame-per-segment) +
   its episode/digest record — sufficient material for H1/H3/H4/H5 author-trials before any
   formal study.
3. **Layout budget rider:** a Wikidata-shaped M costs minutes to lay out (run-1 F1; the
   hub-degree worst case), so live viewing *trails* the run by a segment — acceptable for
   watching, and itself an argument for R6's coarse-first rendering at wide temporal zoom.
4. **Order:** hypotheses first (this doc), carrier second, dwell policy (R1–R3) third,
   coupled zoom (R6) last. Each rule ships only with the instrument that can falsify it.

## 7. Honest limits

- These are perceptual hypotheses about human readers. The game's records supply ground
  truth for *scoring*, but N=1 author trials establish direction, not conclusions; treat
  early results the way §10 of the in-view doc treats its prototype scorer.
- The dwell table (R2) encodes an editorial judgment about what matters. Keeping it a
  visible, adjustable style knob — never a hidden default tuned to please — is what keeps
  playback on the presentation side of the regime boundary.
- Nothing here touches §3.3 or the calculus: every frame shown is an attested (EGI, drawing)
  pair; rate only chooses *when* the reader sees it. The new obligation this doc proposes is
  R5's — the honesty of the *gaps between* frames.
