# Claude Code Implementation Brief: ELK Layout Engine for Arisbe

## Context

Arisbe is a formal reasoning environment for Peirce's Existential Graphs (EG).
The core logical model (`src/egi_core_dau.py`) is mature and well-tested (292 tests).
The GUI/diagram layout has been the bottleneck. The root problem — nested containment
with cross-boundary connections — is a solved problem in compound graph visualization.

**Decision**: Replace the current D3 force-directed layout (`unified_d3_engine.py` +
`unified_d3_worker.js`) with **ELK** (Eclipse Layout Kernel) via **elkjs**, which
natively handles hierarchical compound graphs with cross-boundary edge routing.

## Architecture

```
EGI (Python, immutable)
    ↓
elk_layout_engine.py  ← NEW: maps EGI → ELK JSON, calls elkjs, returns LayoutDTO
    ↓
elk_worker.js         ← NEW: Node.js script, reads ELK JSON from stdin, writes result to stdout
    ↓
LayoutDTO (Python)    ← EXISTING: same interface as unified_d3_engine.py
    ↓
Renderers (SVG, Qt, etc.) ← EXISTING: no changes needed
```

## Mapping: EGI → ELK

| EGI concept | ELK concept | Notes |
|------------|-------------|-------|
| Sheet (⊤) | Root group node | `id: sheet, children: [...]` |
| Cut | Group node (compound) | `id: cut_id`, contains its area contents |
| Vertex (generic `*x`) | Leaf node | `id: vertex_id, width: W, height: H` |
| Vertex (constant `"Socrates"`) | Leaf node | Label from `rho` mapping |
| Edge/predicate | Leaf node with ports | One port per argument position (from `nu`) |
| Ligature | ELK edge | Connects predicate port → vertex node, may cross groups |

### Key mapping details

- **Cuts nest recursively**: `area[cut_id]` contains the IDs of its children (vertices, edges, sub-cuts).
  Each cut becomes an ELK group node whose `children` array holds the ELK representations of those elements.
- **Predicates have ports**: An edge with `nu[edge_id] = (v1, v2, v3)` becomes a node with 3 ports.
  Each port connects via an ELK edge to the corresponding vertex.
- **Ligatures cross group boundaries**: ELK handles this natively — edges between nodes in
  different groups are routed through group borders automatically.

## Prerequisites

- [ ] Node.js installed (already available — used for existing D3 worker)
- [ ] Python 3.12+ with conda env `CGIF` (already configured)

---

## Implementation Checklist

### Phase 1: Infrastructure

- [ ] **Install elkjs**
  ```bash
  cd /Users/mjh/Sync/GitHub/Arisbe
  npm init -y  # Creates package.json at repo root (replaces archived one)
  npm install elkjs
  ```

- [ ] **Create `src/elk_worker.js`** — Node.js subprocess script
  - Reads ELK JSON graph from **stdin**
  - Runs `elk.layout(graph)` with the `layered` algorithm
  - Writes positioned result JSON to **stdout**
  - Exit code 0 on success, non-zero on error (error message to stderr)
  - Boilerplate below

- [ ] **Create `src/elk_layout_engine.py`** — Python orchestrator
  - Class `ELKLayoutEngine` with method `generate_layout(egi, style, layout_deltas=None) -> LayoutDTO`
  - Internal method `_egi_to_elk_graph(egi, style) -> dict` builds the ELK JSON
  - Internal method `_run_elk(elk_graph) -> dict` calls `elk_worker.js` via subprocess
  - Internal method `_elk_result_to_dto(result, egi) -> LayoutDTO` maps positioned output back
  - Returns the **same `LayoutDTO`** from `unified_d3_engine.py` (import it, don't duplicate)

### Phase 2: EGI → ELK Graph Translation (`_egi_to_elk_graph`)

- [ ] **Build recursive group hierarchy**
  - Start from `egi.sheet` — this becomes the root ELK node
  - For each area, collect its contents from `egi.area[area_id]`
  - Classify each element: vertex → leaf node, edge → node with ports, cut → recurse as child group
  - Use `style.cut_padding` for group node padding
  - Use `style.get_element_bounds()` for vertex/predicate node dimensions

- [ ] **Create ports on predicate nodes**
  - For each edge `e`, look up `egi.nu[e.id]` to get the vertex sequence
  - Create one port per argument: `{ id: "port_0", ... }` etc.
  - Port layout: use ELK's `FIXED_SIDE` or `FREE` port constraint

- [ ] **Create ELK edges for ligatures**
  - For each `(edge_id, vertex_seq)` in `egi.nu`:
    - For each `(port_index, vertex_id)` in vertex_seq:
      - Create ELK edge: `{ source: edge_id, sourcePort: port_i, target: vertex_id }`
  - ELK automatically routes these across group boundaries

- [ ] **Set ELK layout options on root**
  ```json
  {
    "elk.algorithm": "layered",
    "elk.hierarchyHandling": "INCLUDE_CHILDREN",
    "elk.layered.spacing.nodeNodeBetweenLayers": "50",
    "elk.spacing.nodeNode": "30",
    "elk.padding": "[top=20,left=20,bottom=20,right=20]",
    "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP"
  }
  ```
  These can be parameterized from the style system later.

### Phase 3: ELK Result → LayoutDTO (`_elk_result_to_dto`)

- [ ] **Walk the positioned ELK result** (recursive, same structure as input but with `x`, `y` added)
  - Vertex nodes → `LayoutDTO.vertex_positions[id] = Point(x, y)` (absolute coords)
  - Predicate nodes → `LayoutDTO.predicate_positions[id] = Point(x, y)`
  - Group nodes → `LayoutDTO.cut_bounds[id] = BoundingBox(x, y, x+width, y+height)`
  - Note: ELK returns positions **relative to parent**. You must accumulate parent offsets
    to convert to absolute coordinates.

- [ ] **Extract ligature paths from ELK edge routing**
  - ELK provides `sections[].startPoint`, `sections[].endPoint`, and `sections[].bendPoints`
  - Map these to `LigaturePath(predicate_id, vertex_id, points=(...))`

- [ ] **Compute viewport bounds** from the root node dimensions

### Phase 4: Tests

- [ ] **Create `tests/test_elk_layout_engine.py`**
  - Test `_egi_to_elk_graph` produces valid ELK JSON for:
    - Empty graph (just sheet)
    - Single predicate: `(Human "Socrates")`
    - Nested cuts: `~[ (Cat *x) ~[ (Animal x) ] ]`
    - Cross-boundary ligature: vertex in one cut, predicate in another
    - Complex corpus example: `corpus/graphs/sowa_cat_on_mat.egi.json`
  - Test full `generate_layout` round-trip returns a `LayoutDTO` with:
    - All vertices positioned
    - All predicates positioned
    - All cuts bounded
    - Ligature paths populated
    - No overlapping sibling cuts (basic sanity)

- [ ] **Verify backward compatibility**
  - `LayoutDTO` from ELK engine must be usable wherever the D3 `LayoutDTO` was used
  - Same imports: `from unified_d3_engine import LayoutDTO, Point, BoundingBox, LigaturePath`
    (or move DTO classes to a shared module)

### Phase 5: Integration

- [ ] **Move DTO classes to shared location** (optional but clean)
  - Extract `Point`, `BoundingBox`, `LigaturePath`, `LayoutDTO` from `unified_d3_engine.py`
    into `src/layout_dto.py`
  - Update imports in `unified_d3_engine.py` and `elk_layout_engine.py`
  - This way both engines share the same output type

- [ ] **Wire into style system**
  - Map `StyleSpecification` fields to ELK layout options:
    - `cut_padding` → ELK padding
    - `element_spacing` → ELK node spacing
    - `sibling_spacing` → ELK layer spacing
    - `ligature_clearance` → ELK edge spacing

---

## Boilerplate: `src/elk_worker.js`

```javascript
/**
 * ELK Layout Worker for Arisbe
 *
 * Reads an ELK JSON graph from stdin, runs layout, writes result to stdout.
 * Usage: echo '{"id":"root",...}' | node elk_worker.js
 */
const ELK = require('elkjs');

const elk = new ELK();

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', async () => {
  try {
    const graph = JSON.parse(input);
    const result = await elk.layout(graph);
    process.stdout.write(JSON.stringify(result));
    process.exit(0);
  } catch (err) {
    process.stderr.write(`ELK error: ${err.message}\n`);
    process.exit(1);
  }
});
```

## Boilerplate: `src/elk_layout_engine.py` (skeleton)

```python
"""
ELK-based layout engine for Arisbe EGI diagrams.

Replaces the D3 force-directed engine with ELK's hierarchical compound
graph layout, which natively handles nested containment (cuts) and
cross-boundary edge routing (ligatures).
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts, ElementID
from unified_d3_engine import LayoutDTO, Point, BoundingBox, LigaturePath
from style_loader import StyleSpecification


class ELKLayoutEngine:
    """Compound graph layout via elkjs subprocess."""

    ELK_WORKER = Path(__file__).parent / "elk_worker.js"

    def generate_layout(
        self,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        layout_deltas: Optional[Dict] = None,
    ) -> LayoutDTO:
        """Generate positioned layout for an EGI diagram."""
        elk_graph = self._egi_to_elk_graph(egi, style)
        positioned = self._run_elk(elk_graph)
        return self._elk_result_to_dto(positioned, egi)

    # --- EGI → ELK translation ---

    def _egi_to_elk_graph(self, egi, style) -> dict:
        """Convert EGI to ELK JSON graph."""
        # TODO: implement recursive group building
        raise NotImplementedError

    # --- Subprocess call ---

    def _run_elk(self, elk_graph: dict) -> dict:
        """Call elkjs via Node.js subprocess."""
        result = subprocess.run(
            ["node", str(self.ELK_WORKER)],
            input=json.dumps(elk_graph),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ELK layout failed: {result.stderr}")
        return json.loads(result.stdout)

    # --- ELK result → LayoutDTO ---

    def _elk_result_to_dto(self, elk_result: dict, egi) -> LayoutDTO:
        """Convert positioned ELK result to LayoutDTO."""
        # TODO: walk elk_result recursively, accumulate parent offsets
        raise NotImplementedError
```

## Existing Files Reference (DO NOT MODIFY unless noted)

| File | Role | Touch? |
|------|------|--------|
| `src/egi_core_dau.py` | Core EGI model (16 protected modules) | **NO** |
| `src/unified_d3_engine.py` | Current D3 layout engine (being replaced) | **READ ONLY** — import `LayoutDTO` classes |
| `src/style_loader.py` | Style system | **READ ONLY** — use `StyleSpecification` |
| `src/style_specification.py` | Style type definitions | **READ ONLY** |
| `styles/*.json` | Style definitions | **NO** |
| `src/egif_parser_dau.py` | EGIF parser (for test data) | **NO** |
| `src/egif_generator_dau.py` | EGIF generator (for test verification) | **NO** |
| `corpus/graphs/*.egi.json` | Test corpus graphs | **READ ONLY** — use in tests |

## Constraints

1. **Core protection**: Do not modify any of the 16 protected core modules in `src/`.
   Run `python tools/core_protection_system.py --report` if unsure.
2. **Test suite**: All 292 existing tests must continue to pass.
   Run `python -m pytest tests/ -q --timeout=120` to verify.
3. **Python path**: All source in `src/`, tests in `tests/`. Imports use
   `sys.path.insert(0, 'src')` or `PYTHONPATH=src`.
4. **Conda environment**: `conda activate CGIF` (Python 3.12.10).
5. **EGI immutability**: EGI objects are frozen dataclasses. Layout never mutates them.

## Success Criteria

1. `node src/elk_worker.js` accepts valid ELK JSON on stdin, returns positioned JSON on stdout
2. `ELKLayoutEngine().generate_layout(egi, style)` returns a complete `LayoutDTO`
3. The `LayoutDTO` contains positions for all vertices, predicates, cuts, and ligature paths
4. Layout correctly nests cuts inside their parents (no overlapping siblings)
5. Ligatures connecting elements across cut boundaries are routed through boundaries
6. All new tests pass; all 292 existing tests still pass
