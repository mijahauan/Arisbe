# ELK Layout Engine Implementation Summary

**Date**: 2026-04-01
**Status**: ✅ Complete and validated — **historical snapshot at 2026-04-01.** `src/elk_layout_engine.py`
has grown substantially since (395 → ~1300 lines): ligature-anchor rebuild
(`rebuild_ligature_anchors`), tension-order wiring (`TENSION_LAYOUT.md`), the exact bbox
quick-reject + visibility-graph optimizations in the ligature router (`CLAUDE.md`'s `src/`
module list has the current line-by-line account). Read this document for the original
architecture and rationale; for current state see CLAUDE.md's `elk_layout_engine.py` entry and
`docs/CAPABILITY_MAP.md`.

## Overview

Successfully implemented a production-ready layout engine for Arisbe EGI diagrams using ELK (Eclipse Layout Kernel) with custom cut-aware ligature routing that respects existential graph semantics.

## What Was Implemented

### 1. Core ELK Integration (`src/elk_layout_engine.py`)

- **ELK subprocess orchestration**: Python calls Node.js worker (`src/elk_worker.js`) with ELK JSON, receives positioned graph
- **EGI → ELK graph conversion**: Maps EGI structure to ELK's hierarchical compound graph format
  - Vertices and predicates → ELK nodes
  - Cuts → ELK group nodes (containers)
  - Area hierarchy → ELK parent-child nesting
  - Ligatures → ELK edges (for layout influence only, not routing)
- **Platform-independent output**: Returns `LayoutDTO` with positioned elements, compatible with any renderer

### 2. Cut-Aware Ligature Routing

**Problem**: ELK's edge routing is ignorant of EG area containment semantics — it routes through unrelated areas, producing logically nonsensical diagrams.

**Solution**: Custom geometric routing that respects Peirce's "excised plane" model:

- **Authorized cut detection**: For each ligature, compute which cuts it may cross by walking the area hierarchy from predicate's area to vertex's area. Only cuts on this path are authorized.
- **Obstacle avoidance**: All other cuts are spatial obstacles the ligature must route around.
- **Three-tier routing strategy**:
  1. **Straight line** if no unauthorized crossings
  2. **L-shaped detour** around combined bbox of crossed obstacles (tries 4 directions, picks shortest valid)
  3. **Visibility graph fallback** (Dijkstra through padded corners) for complex configurations

**Key methods**:
- `_authorized_cuts()`: Returns cuts a ligature may cross based on area hierarchy
- `_route_avoiding_cuts()`: Computes polyline path avoiding unauthorized cuts
- `_route_via_visibility_graph()`: Shortest path through obstacle field
- `_seg_crosses_rect()`, `_segs_intersect()`: Geometric primitives

### 3. Polarity-Based Area Shading (`src/simple_svg_renderer.py`)

- **Alternating shading**: Odd-depth cuts (negative areas) get light gray fill, even-depth cuts get opaque white fill
- **Depth-ordered rendering**: Cuts sorted by nesting depth (shallowest first) so white fills properly cover gray parent fills
- **Visual semantics**: Polarity is immediately visible — gray = negated context

### 4. SVG Renderer Enhancements

- **Predicate hook attachment**: Ligatures attach at predicate label boundary (ray-cast intersection with bbox), not center
- **Polyline ligature paths**: Renderer handles multi-point paths from routing algorithm
- **Robust element sizing**: Text measurement for predicates, configurable vertex radius

### 5. Testing and Validation

- **20 passing tests** in `tests/test_elk_layout_engine.py`:
  - EGI → ELK structural conversion
  - Full round-trip layout generation
  - LayoutDTO completeness
  - Backward compatibility
- **Gallery validation**: 20 diagrams rendered (13 test cases, 5 corpus examples, 2 domain models)
- **Visual inspection**: All corpus examples render correctly, domain models show proper cut avoidance

## Architecture

```
EGI (logical structure)
  ↓
ELKLayoutEngine._egi_to_elk_graph()
  ↓
ELK JSON → elk_worker.js (Node.js subprocess) → Positioned ELK JSON
  ↓
ELKLayoutEngine._elk_result_to_dto()
  ├─ Extract node positions
  ├─ Compute cut bounds
  └─ Build ligature paths (custom routing)
  ↓
LayoutDTO (platform-independent)
  ↓
SimpleSVGRenderer.render()
  ↓
SVG diagram
```

## Files Modified/Created

**New files**:
- `src/elk_layout_engine.py` (395 lines) — core layout engine
- `src/elk_worker.js` (25 lines) — Node.js ELK subprocess
- `src/layout_dto.py` (65 lines) — platform-independent data structures
- `tests/test_elk_layout_engine.py` (302 lines) — comprehensive test suite
- `tools/render_svg_gallery.py` (104 lines) — batch rendering script
- `output/svg_gallery/index.html` (79 lines) — gallery viewer
- `docs/ELK_IMPLEMENTATION_BRIEF.md` (250 lines) — implementation guide

**Modified files**:
- `src/simple_svg_renderer.py` — polarity shading, polyline ligatures
- `package.json` — added `elkjs` dependency

## Key Design Decisions

1. **ELK for node positioning only**: ELK's hierarchical layout is excellent for nested containment but its edge routing doesn't understand EG semantics. We use ELK to position nodes, then compute ligature paths ourselves.

2. **Geometric routing over graph routing**: Ligature paths are computed as geometric polylines through 2D space, not as graph edges. This allows obstacle avoidance while respecting area hierarchy authorization.

3. **Platform-independent LayoutDTO**: Separates layout computation from rendering. The same LayoutDTO can drive SVG, Qt, web canvas, or any other renderer.

4. **Immutable EGI, mutable layout**: EGI structure is frozen. Layout deltas (user position overrides) are separate and composable.

## Performance

- **ELK subprocess**: ~1-2s for typical diagrams (10-50 elements)
- **Ligature routing**: <100ms even for complex obstacle fields
- **SVG generation**: <100ms
- **Total latency**: ~1-2s for full layout + render cycle

## Known edge cases

Findings from the ligature edge-case audit (Issue #5, May 2026; see
`tests/test_elk_ligature_edge_cases.py`):

### 1. Cross-cut Beta ligatures (lines of identity)

Tested with `(P *x) ~[ (Q x) ~[ (R x) ] ] ~[ (S *y) ]` (one shared vertex,
two nested cuts, plus an unrelated sibling cut) and a three-level chain
`(P *x) ~[ (Q x) ~[ (R x) ~[ (S x) ] ] ]`.  Two geometric properties
hold on every ligature produced:

- The polyline crosses each enclosing cut boundary **exactly once** (no
  spurious re-entry).
- The polyline does not intersect the bounding box of any unrelated cut.

No regressions found — the cut-aware routing (`_authorized_cuts` plus
`_route_avoiding_cuts`) handles the audited shapes correctly.  Deeper
chains (5+ levels) and wider sibling configurations remain untested by
this audit.

### 2. Large-EGI performance — stdout pipe truncation (fixed)

**Bug surfaced.**  Before the fix, EGIs above roughly 240 sheet-level
elements raised `json.JSONDecodeError: Unterminated string starting at:
line 1 column 65528` — consistently at the macOS 64 KB pipe-buffer
boundary.  Root cause was in `src/elk_worker.js`:

```js
// before
process.stdout.write(JSON.stringify(result));
process.exit(0);
```

`process.exit(0)` does not wait for stdout to flush.  When the result
exceeded the OS pipe buffer the tail of the write was discarded.  The
fix is one line — use the callback form of `write` so `exit` runs only
after the buffer drains:

```js
// after
process.stdout.write(JSON.stringify(result), () => process.exit(0));
```

Empirically verified: post-fix, 300-element and 900-element layouts
complete cleanly.  A regression test
(`TestLargeEGIPerformance::test_layout_above_pipe_buffer_threshold`)
exercises 300 elements; the latency-budget test exercises 150 elements
within 5 s (typical actual time: ~0.2 s).

### 3. Dense n-ary relations

Tested with `(R *x *y *z) (S x y z) (T x y z) (U x y z)` — four ternary
predicates sharing the same vertex triple, producing 12 ligature paths
that all converge on three shared vertices.  Assertion: no two distinct
ligature paths contain collinear-overlapping segments (i.e. visually
stacked lines).  Passes — bundles fan out from each shared vertex
rather than stacking.

Single-point intersections between distinct ligatures still occur (and
are geometrically unavoidable when many predicates fan in to a small
vertex set).  Reducing visual crossing count is a layout-quality issue,
not a correctness one, and is out of scope for this audit.

## Known Limitations

1. **No incremental layout** (as of this 2026-04-01 snapshot): every layout was computed from
   scratch, so unchanged elements didn't automatically hold their positions. **Superseded**:
   `TRANSFORMATION_WORKFLOW_SPEC.md` §5 item ④a (pin-and-place, shipped 2026-06-06) and the
   opt-in `tension_engine.py` (`TensionLayoutEngine`, `?engine=tension`) both address layout
   stability across transformation sequences.

2. **No layout templates**: Structurally similar graphs (e.g., two implications) don't automatically share visual patterns (also deferred).

3. **ELK configuration is basic**: Using default "layered" algorithm. Could be tuned with more sophisticated ELK options for specific diagram types.

## Next Steps

The layout engine is production-ready for static diagram rendering. Future enhancements:

1. **Layout stability system**: Position anchoring across transformation sequences
2. **Structural layout templates**: Canonical arrangements for common logical patterns
3. **Interactive web viewer**: Pan/zoom, element selection, transformation workflows
4. **Layout quality tuning**: Refine ELK spacing/padding parameters

## Testing

Run tests:
```bash
python -m pytest tests/test_elk_layout_engine.py -v
```

Generate gallery:
```bash
python tools/render_svg_gallery.py
open output/svg_gallery/index.html
```

## Dependencies

- **Python**: `subprocess`, `json`, `pathlib`, `heapq`, `math`
- **Node.js**: `elkjs@^0.11.1`
- **Existing Arisbe modules**: `egi_core_dau`, `layout_dto`, `style_loader`, `simple_svg_renderer`

## References

- ELK documentation: https://www.eclipse.org/elk/
- Dau (2006): *The Logic System of Concept Graphs with Negation* — area containment semantics
- Peirce's existential graphs — "excised plane" model of cuts
