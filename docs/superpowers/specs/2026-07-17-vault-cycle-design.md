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

## Stage V2 — the oracle (the interactive loop; open items below)

Forecast-before-ask (the resolving shape): Arisbe predicts the author's answer,
asks, scores the miss. The docket's wants become questions; the economy's cost unit
is **the author's time**. *Open, the author's:* the interruption budget and surface
(batched docket panel in Organon vs conversation here vs both), and whether the
reflexive stream ("how the author changes by interacting with Arisbe") is annotated
from day one (recommended: yes, as its own stream).

## RUN 13 — pre-registered priors (draft for the author's amendment before launch)

- **P1¹³ (retrodiction):** trained on notes through month *m*, the model's forecasts
  about month *m+1*'s activity (which clusters grow, which notes get revisited) beat
  a frequency baseline on a held-out slice.
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
  audit lens for at least one exemplar topic the author picks.

## Out of scope this cycle

The tutor loop's build (its own authorization); B-full; any web-lens work; any
modeling of third parties (their appearance in M is only as the author's relations,
metadata-level).

## Open items (the author's, non-blocking for the plan)

1. Third-party folders: keep metadata-only, or widen consent?
2. V2 interruption budget + surface.
3. P-priors: amend/replace before launch.
