# ProofSerializer — EGI Transformation History Serialization

`src/proof_serializer.py`

## Overview

`ProofSerializer` converts an `EGITransformationHistory` to and from portable
formats so that proofs, game sessions, and transformation sequences can be
saved, shared, and inspected outside a live Arisbe session.

```
EGITransformationHistory
        │
        ├── ProofSerializer.to_json(h)   → JSON string  (machine-readable)
        ├── ProofSerializer.to_text(h)   → plain text   (human-readable)
        └── ProofSerializer.from_json(s) → EGITransformationHistory
```

The JSON output is **self-contained**: every state carries its EGIF string, so
any EGI can be reconstructed without access to the original session.

---

## API

### `ProofSerializer.to_json(history, indent=2) → str`

Serializes the full history as a JSON string.

| Parameter | Type | Description |
|---|---|---|
| `history` | `EGITransformationHistory` | History to serialize |
| `indent` | `int` | JSON indentation (default 2) |

**Returns**: UTF-8 JSON string.

---

### `ProofSerializer.to_text(history) → str`

Renders the **main linear path** (root → current state) as a human-readable
proof listing.

```
=== Proof ===

Step 0 — Initial state
  *x (Human x)

Step 1 — DC+
  ~[~[*x (Human x)]]

Step 2 — DC+
  ~[~[~[~[*x (Human x)]]]]
```

Only the main path is shown; alternative branches are omitted.

---

### `ProofSerializer.from_json(json_str) → EGITransformationHistory`

Reconstructs an `EGITransformationHistory` from a JSON string produced by
`to_json`.

| Parameter | Type | Description |
|---|---|---|
| `json_str` | `str` | JSON string from `to_json` |

**Returns**: A fresh `EGITransformationHistory` with all states and
transformation steps reconstructed.

**Raises**:
- `ValueError` — if a state is missing its `egif` field, or if an EGIF string
  cannot be parsed back to an EGI.
- `json.JSONDecodeError` — if the input is not valid JSON.

---

## JSON Schema

```json
{
  "schema_version": "1.0",
  "history_id": "<uuid>",
  "created_timestamp": "<ISO-8601>",
  "current_state_id": "<uuid>",
  "root_state_id": "<uuid>",
  "state_sequence": ["<uuid>", ...],
  "branch_points": ["<uuid>", ...],

  "states": {
    "<state-uuid>": {
      "state_id": "<uuid>",
      "step_number": 0,
      "description": "Initial state",
      "timestamp": "<ISO-8601>",
      "egif": "*x (Human x)",
      "metadata": {}
    }
  },

  "transformations": {
    "<step-uuid>": {
      "step_id": "<uuid>",
      "rule_name": "DC+",
      "from_state_id": "<uuid>",
      "to_state_id": "<uuid>",
      "timestamp": "<ISO-8601>",
      "status": "applied",
      "user_annotation": null,
      "metadata": {}
    }
  }
}
```

### Field notes

| Field | Notes |
|---|---|
| `schema_version` | Always `"1.0"` in current implementation |
| `state_sequence` | Ordered list of state IDs along the main linear path |
| `branch_points` | State IDs that have more than one outgoing transformation |
| `states[*].egif` | **Required** on round-trip; this is how EGIs are reconstructed |
| `transformations[*].status` | One of `"applied"`, `"failed"`, `"pending"`, `"reverted"` |
| `transformations[*].user_annotation` | Optional free-text label set by the caller |

---

## Known Limitations

### Context stubs on round-trip

`TransformationContext` carries rich data (selected subgraph, target area,
polarity, nesting depth) that is **not stored** in the JSON. On `from_json`,
every step's context is replaced with a minimal stub:

```python
TransformationContext(
    source_egi=<previous-state-egi>,
    target_area=<sheet>,
    selected_subgraph=frozenset(),
    area_polarity=AreaPolarity.POSITIVE,
    nesting_depth=0,
)
```

This means that after deserialization, the `context` field of each
`TransformationStep` **cannot be used to re-apply** the rule to reproduce the
exact same transformation. The EGI states themselves are faithfully preserved;
only the execution context is lost.

**Implication**: Use the serialized form for archiving, sharing, and inspection —
not for automated proof replay that depends on context details.

### Branch paths in `to_text`

`to_text` follows only the main path from root to `current_state_id` (using
BFS). Alternative branches created via `create_branch_from_state` are silently
omitted. The full DAG structure is preserved in the JSON output.

### `history_id` is not preserved

`from_json` constructs a new `EGITransformationHistory` object, which receives
a fresh UUID as its `history_id`. The original `history_id` from the JSON is
not re-used.

---

## Use Cases

### 1. Save and restore a game session (Endoporeutic Game)

```python
import sys; sys.path.insert(0, 'src')
from proof_serializer import ProofSerializer
from endoporeutic_game import EndoporeuticGame, Player
from egif_parser_dau import parse_egif

# Start a game
domain = parse_egif('*x (Human x) *y (Mortal y)')
goal   = parse_egif('*x (Human x) ~[(Mortal x)]')
game   = EndoporeuticGame(domain_egi=domain, goal_egi=goal)

# ... play several moves ...

# Save after the session
json_str = ProofSerializer.to_json(game.history)
with open('my_game.proof.json', 'w') as f:
    f.write(json_str)

# Restore in a later session
with open('my_game.proof.json') as f:
    restored_history = ProofSerializer.from_json(f.read())

print(f"Restored {len(restored_history.states)} states")
```

---

### 2. Print a proof as readable text for review

```python
from proof_serializer import ProofSerializer
from egi_transformation_history import EGITransformationHistory
from egif_parser_dau import parse_egif
from formal_transformation_rules import (
    DoubleCutInsertionRule, TransformationContext, AreaPolarity
)

egi = parse_egif('*x (Human x)')
h   = EGITransformationHistory(egi, 'Premise')

for _ in range(3):
    current = h.get_current_state().egi
    ctx     = TransformationContext(
        source_egi=current, target_area=current.sheet,
        selected_subgraph=frozenset(),
        area_polarity=AreaPolarity.POSITIVE, nesting_depth=0,
    )
    result = DoubleCutInsertionRule().apply_transformation(ctx)
    h.add_transformation('DC+', ctx, result)

print(ProofSerializer.to_text(h))
```

Output:
```
=== Proof ===

Step 0 — Initial state
  *x (Human x)

Step 1 — DC+
  ~[~[*x (Human x)]]

Step 2 — DC+
  ~[~[~[~[*x (Human x)]]]]

Step 3 — DC+
  ~[~[~[~[~[~[*x (Human x)]]]]]]
```

---

### 3. Inspect the JSON schema programmatically

```python
import json
from proof_serializer import ProofSerializer

# ... build history h ...
data = json.loads(ProofSerializer.to_json(h))

print("States:", len(data['states']))
print("Steps: ", len(data['transformations']))

for sid, state in data['states'].items():
    print(f"  Step {state['step_number']:2d}  {state['egif']}")

for tid, step in data['transformations'].items():
    print(f"  {step['rule_name']:6s}  {step['status']:8s}  {step.get('user_annotation') or ''}")
```

---

### 4. Share a proof between collaborators

```python
# Researcher A — save
json_str = ProofSerializer.to_json(history)
with open('syllogism_proof.json', 'w', encoding='utf-8') as f:
    f.write(json_str)

# Researcher B — load and verify
with open('syllogism_proof.json', encoding='utf-8') as f:
    received = ProofSerializer.from_json(f.read())

from egif_generator_dau import generate_egif
final_egif = generate_egif(received.get_current_state().egi)
print("Final graph:", final_egif)
print("Steps applied:", received.get_current_state().step_number)
```

---

### 5. Annotate steps for academic citation

```python
h.add_transformation(
    'ERA',
    ctx,
    result,
    user_annotation='Dau Theorem 12.3.1 — erasure in positive context',
)
```

Annotations appear in the JSON under `transformations[*].user_annotation` and
are preserved on round-trip.

---

## Running the Tests

```bash
uv run python -m pytest tests/test_proof_serializer.py -v
```

Expected: all tests pass.

## Running the Demo

```bash
uv run python tools/demo_proof_serializer.py
```
