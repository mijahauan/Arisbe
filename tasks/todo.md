# Tropism module — increment 1 (§13, affirmed 2026-07-02) — DONE

Author affirmed all five §13 decisions as drafted: (1) policy + `source.inject(ids)`;
(2) decay-adjacent first; (3) `warm_fraction` 0.5 fixed for run 3; (4) run 3 = crawl + tropism;
(5) ambiguous labels skip + count.

- [x] §13 heading + affirmation note in docs/AUTOMATED_ENDOPOREUTIC_GAME.md
- [x] src/tropism.py — `reverse_labels` + `WarmSetTropism.reaches` (decay-adjacent first;
      ambiguous/unmapped counted)
- [x] src/wikidata_source.py — `inject(ids)` (front-of-queue, _seen-exempt, counted, persisted;
      fixed load_state queue-verbatim bug the round-trip test exposed) + `known_labels()`
- [x] src/live_runner.py — `LiveRunner(tropism=)` consulted at the poll boundary
- [x] tools/run_live_wikidata.py — `--warm-fraction`, non_revising/warm counters in digests,
      uod_id from runs-dir name
- [x] tests/test_tropism.py — 18 tests incl. both headlines (non-revising re-delivery; the P2
      event: deprecation meets standing target on a warm re-reach)
- [x] Suites: tropism 18, arc neighbors 82, full suite green (13 batch failures = browser-E2E
      contention, all pass in isolation on both main and the diff)
- [x] Currency: CAPABILITY_MAP §H, GLOSSARY, VISION, EGG guide; runs/RUN_3_LOG.md skeleton;
      CURRENT_PLAN + memory

## Review
Increment 1 is the §13 design verbatim; the one deviation is documentation-level — the panel
records a warm re-delivery as a non-revising round (disposition None), so P1″'s "redundancy"
instrument is the digest's `non_revising` count (noted in §13's affirmation paragraph and
RUN_3_LOG). Next session: run 3 live.
