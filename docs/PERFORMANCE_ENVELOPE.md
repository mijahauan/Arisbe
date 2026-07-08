# Performance Envelope — how big, how fast, where the walls are

> This is the single place the real numbers live. They were previously scattered
> across dated run logs and the capability map; here they are collected, with the
> shape of the input that governs each. Disposes gap **G7** of
> [STORM_DOCS_AUDIT.md](STORM_DOCS_AUDIT.md).

**The one thing to understand first:** Arisbe's costs scale with the *shape* of
the graph, not just its size. A 50-element chain is cheap; a 50-element
**star** (one individual touched by many relations — the Wikidata-entity shape)
was, before the fixes below, catastrophic. Every performance wall we hit was a
wrong-complexity algorithm exposed by a hub-shaped input, and every one was
fixed by making the algorithm exact-but-cheaper — never by approximating.

## The interactive envelope (what stays responsive)

| Operation | Comfortable | Degrades at | Governing dimension | Notes |
|---|---|---|---|---|
| **Parse / generate** (EGIF/CGIF/CLIF) | hundreds of atoms | — | atoms | `canonical_signature` hash-consed (below); a 200-atom hub sheet generates in **3.3 ms**. |
| **Coordinate-free structure** (`/structure`) | 250+ cuts | — | cuts | O(n), no geometry; returns the 250-cut SUMO taxonomy in **milliseconds**. |
| **ELK layout + render** | ~tens of cuts / ~100 atoms | deep nesting, very wide areas | cuts × nesting | The default drawing path. See the walls below for the pathological shapes. |
| **§3.3 attestation** | ~200 atoms | machine-scale label lengths | atoms × label length | Occlusion checks read label boxes; long constant labels were the F1⁵ coin-flip (fixed). |
| **Ligature routing** | ~200 atoms, five hubs deg 20–25 | — (after the fix) | hub degree | Visibility-graph router; see the 160× fix below. |
| **Peel / model-check one G** | small M | large materialized M | \|M\| (facts) | Forward-chains M's Horn fragment each call; see the live-run wall. |
| **One live-game round** | \|M\| ≈ tens | \|M\| in the hundreds | \|M\| | Super-linear; bounded operationally by disuse-decay (below). |

For anything past "comfortable," the honest move is to reach for the
coordinate-free `/structure` route (which never lays out geometry) or the
adaptive-scope overview lens, not to force a full ELK draw.

## The walls we hit — and how each was removed

Each of these was a real, measured pathology on a hub-shaped input, fixed by an
**exact** algorithm change (bit-identical or provably-equal output), not an
approximation. This is the project's performance doctrine: *own the
dimensionality, don't round it off.*

| Wall | Before | After | Fix | Date |
|---|---|---|---|---|
| **Canonical signature** (generator coloring) | 200-atom hub sheet: **15.7 s** | **3.3 ms** (~4800×) | Hash-consed colors; refinement stops at partition stabilization. Canonicality unchanged. | 2026-07-03 |
| **Ligature router — bbox reject** | ~50-atom star M: **452 s** | **3.2 s** (~140×) | Exact bounding-box quick-reject in `_seg_crosses_rect`; strict inequalities, **routes bit-identical**. | 2026-07-02 |
| **Ligature router — visibility graph** | run3\_seg17 (135 atoms, five hubs deg 20–25): **> 10 min** | **3.8 s** (**> 160×**) | Separation short-circuit + uniform-grid obstacle culling + lazy A\*. Exact shortest paths (tie-breaks may differ). | 2026-07-03 |
| **Materializer round-compute** (live game) | O(\|M\|²) rebuild per round | O(\|Δ\|·\|M\|) | Semi-naive Datalog delta iteration + `IncrementalMaterializer` caching across rounds (same closure). | 2026-07-03 |

## Known-heavy shapes (still real limits)

Not everything is fixed to instant. These are the honest remaining costs:

- **ELK on a deep/wide taxonomy.** A 250-cut ontology (SUMO upper) **chokes ELK
  at ~74 s** for a full drawing. The mitigation is real and shipped: the
  coordinate-free `/structure` route returns the same taxonomy in milliseconds
  because it produces *structure*, not a picture; and the adaptive-scope overview
  lens collapses deep cuts into placeholders. Draw the whole thing only when you
  need the whole picture.
- **A large persistent M in a live game is flat but heavy.** Round compute is
  now flat (no super-linear tail), but a *persistent* ~1,000-atom model costs
  **~3–10 min per checkpoint segment** (layout + attest + peel at that scale) —
  finding F2ᵇ from run 5b. Flat ≠ cheap. This is why the live runner
  **checkpoints and prunes** rather than holding the whole proof chain in RAM.

## Live-run throughput (measured, field conditions)

From the executed Wikidata runs (`runs/RUN_*_LOG.md`):

- **Round throughput:** ~4 ms/round at \|M\| ≈ 25 → ~1.1 s/round at \|M\| ≈ 250
  (super-linear in \|M\|; the peel forward-chains M each round).
- **Field peak:** a measured live window reached **17.8 rounds/s**
  (~102 rounds/poll, ~32× run 4's rate) — *pacing-limited* (polls ~5.75 s apart
  for API etiquette), not compute-limited, once the compute walls above were
  removed.
- **What keeps it bounded:** disuse-decay caps \|M\| (atom-level TTL) so per-round
  cost, memory, and disk stay flat across an arbitrarily long run; segments are
  checkpointed and the in-RAM chain is dropped. See
  [runs/OPERATIONS.md](../runs/OPERATIONS.md) for the operator's view.

## How to reproduce / measure

- The pathological fixtures live in the run logs and the ligature edge-case
  tests; `tests/test_elk_ligature_edge_cases.py` exercises the router.
- For your own graph: time `/structure` (cheap, structural) vs a full ELK draw
  (`/organon/uods/{id}`) to see where the geometry cost lands for *your* shape.
- The live-run numbers come from `SegmentDigest.elapsed_s` in the run logs — the
  operator's per-segment wall-clock, glossed in
  [runs/OPERATIONS.md](../runs/OPERATIONS.md).

---
*Related:* [CAPABILITY_MAP](CAPABILITY_MAP.md) (what works + what guards it) ·
[SOUNDNESS_BOUNDARY](SOUNDNESS_BOUNDARY.md) · [runs/OPERATIONS.md](../runs/OPERATIONS.md) ·
`runs/RUN_*_LOG.md` (the dated lab notebooks these numbers come from).
