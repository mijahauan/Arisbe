# Diachronic Delta Workflow

## Architecture Overview

The **diachronic delta workflow** ensures that user aesthetic choices persist intelligently across logical transformations in the Universe of Discourse.

### Core Concept

Each state in the transformation sequence is a **pair**:

```
State_n = (EGI_n, LayoutDeltas_n)
```

- **EGI_n**: The logical structure at this point
- **LayoutDeltas_n**: User aesthetic constraints (vertex/predicate positions)

### The Workflow

```
State_0 = (EGI_0, {})
   ↓ [User moves vertex]
State_0' = (EGI_0, Deltas_0')
   ↓ [Apply IT+ rule]
State_1 = (EGI_1, Deltas_1)  ← Deltas_1 inherited from Deltas_0' via reconciliation
   ↓ [User adjusts layout]
State_1' = (EGI_1, Deltas_1')
   ↓ [Apply DC+ rule]
State_2 = (EGI_2, Deltas_2)  ← Deltas_2 inherited from Deltas_1' via reconciliation
```

## Implementation

### 1. State Storage

**Location**: `egi_transformation_history.py::StateSnapshot`

```python
@dataclass(frozen=True)
class StateSnapshot:
    state_id: str
    egi: RelationalGraphWithCuts
    diagram_metadata: Dict[str, Any]  # ← Stores layout_deltas
```

The `diagram_metadata` field stores:
```json
{
  "layout_deltas": {
    "v_abc123": {
      "type": "vertex_position",
      "position": [250.5, 180.3]
    },
    "e_def456": {
      "type": "edge_position",
      "position": [300.1, 200.7]
    }
  },
  "delta_reconciliation": {
    "preserved": 5,
    "discarded": 2
  }
}
```

### 2. Delta Reconciliation

**Location**: `diagram_controller.py::_preserve_valid_constraints()`

When a transformation is applied:

1. **Capture** old deltas: `old_deltas = dict(self.layout_deltas)`
2. **Apply** logical transformation: `self.egi_model = result.result_egi`
3. **Reconcile** deltas:
   - Iterate through `old_deltas`
   - Discard deltas for deleted elements
   - Preserve deltas for surviving elements
   - Result: `new_deltas` (subset of `old_deltas`)
4. **Record** in history with both EGI and deltas
5. **Layout** with inherited constraints

### 3. Transformation Process

**Location**: `diagram_controller.py::apply_formal_rule()`

```python
# Step 1: Capture current state
old_deltas = dict(self.layout_deltas)

# Step 2: Apply logical transformation
self.egi_model = result.result_egi

# Step 3: Delta reconciliation
self._preserve_valid_constraints()

# Step 4: Record in history
if self.transformation_history:
    self._record_transformation_with_deltas(
        rule_name, context, result, old_deltas, self.layout_deltas
    )

# Step 5: Layout with inherited constraints
self._trigger_full_relayout()
```

### 4. Fast Path vs. Slow Path

**Fast Path** (logic-indifferent moves):
- User drags vertex/predicate
- Update `layout_deltas` directly
- Recalculate affected ligatures
- Refresh display (NO relayout)
- **Does NOT create new state** in sequence

**Slow Path** (logical transformations):
- Apply formal rule (DC+, IT+, etc.)
- Create new state: `(EGI_n+1, Deltas_n+1)`
- Full relayout with inherited deltas
- **DOES create new state** in sequence

## File Persistence

### Saving with Deltas

**Location**: `ergasterion_mode.py::_on_save_egi()`

```python
payload = to_dict(egi)
payload['layout_deltas'] = {
    elem_id: {
        'type': delta.delta_type,
        'position': list(delta.new_position)
    }
    for elem_id, delta in self.controller.layout_deltas.items()
}
```

### Loading with Deltas

**Location**: `ergasterion_mode.py::_on_load_egi()`

```python
data = json.loads(file_content)
egi = from_dict(data)

if 'layout_deltas' in data:
    for element_id, delta_data in data['layout_deltas'].items():
        delta = LayoutDelta(
            element_id=element_id,
            delta_type=delta_data['type'],
            new_position=tuple(delta_data['position'])
        )
        self.controller.layout_deltas[element_id] = delta
```

## Enabling History Tracking

**Optional** - Enable for advanced proof workflows:

```python
# After loading EGI
controller.load_egi(egi)
controller.enable_transformation_history("Cat on Mat - Initial")
```

Now transformations are recorded in a full history with:
- Complete state snapshots
- Delta reconciliation tracking
- Branch management
- Rollback capabilities

## The Architect Analogy

```
Blueprint v1 (EGI_0):
  Floor plan + Door handle annotations (Deltas_0)
  
[Client requests: "Merge two offices"]
  
Blueprint v2 (EGI_1):
  Updated floor plan + Preserved annotations (Deltas_1)
  - Annotation for demolished wall: DISCARDED
  - Annotation for main entrance: PRESERVED
```

This is **exactly** what the reconciliation algorithm does.

## Key Benefits

1. **Aesthetic Continuity**: User layout choices persist across transformations
2. **Intelligent Reconciliation**: Only valid constraints are carried forward
3. **Minimal Storage**: Only deltas stored, not full layout snapshots
4. **Fast Path**: Logic-indifferent moves don't trigger relayout
5. **Provenance**: Complete history of logical + aesthetic evolution

## Testing the Workflow

1. Load an EGI
2. Move a vertex (fast path - no new state)
3. Apply IT+ (slow path - creates State_1 with inherited delta)
4. Move a predicate (fast path - modifies State_1 deltas)
5. Apply DC+ (slow path - creates State_2 with reconciled deltas)
6. Save file → Both EGI and deltas persisted
7. Reload file → Exact layout restored

The deltas flow intelligently through the transformation sequence!
