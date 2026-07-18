# Run 13 log — the vault cycle, World #2: the author according to Arisbe — PRE-REGISTERED 2026-07-18

**Pre-registration.** Priors below are copied **verbatim** from the design spec
(`docs/superpowers/specs/2026-07-17-vault-cycle-design.md`, "RUN 13 — pre-registered
priors"), before any run against the real vault. Stage V0 (the metadata membrane —
`src/vault_world.py`, `src/probe_feed.py`, the `Horizon` register in
`src/attention_economy.py`) is fixture-verified; the driver is `tools/run_vault_v0.py`.
Launching RUN 13 against the real vault (`/Users/mjh/Documents/Vorago`) is the author's
own act, not something CI or an agent does.

## Pre-registered priors (verbatim from the spec)

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

## Findings

*(none yet — this section fills in only after a real-vault run the author has reviewed.)*

## Custody note

Model artifacts driven from the real vault (UoDs, chains, and anything else
`tools/run_vault_v0.py` writes) live under `runs/run13/`, which `.gitignore` excludes in
full — nothing derived from the real vault ever enters git. The driver's per-segment
stdout digest is numbers only (counts, snapshot dicts keyed by kind/reason, |M|) and
never carries a note id, title, or path, so even a captured console log stays
custody-safe. Only aggregates the author has personally reviewed are ever copied by
hand into this log — this file carries no data from an actual run yet.
