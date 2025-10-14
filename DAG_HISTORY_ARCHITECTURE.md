# DAG-Based Transformation History Architecture

## Overview

The Universe of Discourse (UoD) history model now supports **branching development** through a **Directed Acyclic Graph (DAG)** structure. This enables realistic inquiry workflows where multiple paths can be explored from any historical state.

## Why DAG Instead of Linear?

**Linear History Limitations:**
- Real inquiry involves exploration and backtracking
- Alternative proof paths cannot be represented
- "What if?" scenarios require creating separate UoDs
- No way to compare different approaches from same starting point

**DAG Benefits:**
- Branch from any historical state
- Explore multiple transformation paths
- Keep all explorations in one UoD
- Compare alternative approaches
- Preserve full reasoning context

## Architecture

### Core Data Structure

```python
class EGITransformationHistory:
    # States and transformations
    states: Dict[str, StateSnapshot]           # All states in DAG
    transformations: Dict[str, TransformationStep]  # All edges in DAG
    
    # DAG structure
    root_state_id: str                         # Root of DAG (initial state)
    branch_points: Set[str]                    # States with multiple children
    state_to_outgoing_steps: Dict[str, List[str]]  # Adjacency list
    state_to_incoming_step: Dict[str, Optional[str]]  # Parent edges
    
    # Navigation
    current_state_id: str                      # Current position in DAG
    current_branch_id: str                     # Current active branch
```

### DAG Properties

1. **Single Root**: Every DAG has one initial state (root)
2. **Acyclic**: No cycles (validated during construction)
3. **Multiple Paths**: Many paths can exist from root to any state
4. **Branch Points**: States with multiple outgoing edges tracked explicitly

## API

### Creating Branches

```python
# Branch from any historical state
branch_id = history.create_branch_from_state(
    source_state_id="state_xyz",
    branch_type=HistoryBranchType.EXPLORATION,
    description="Alternative proof approach"
)

# Continue transformations on new branch
history.add_transformation(rule_name, context, result)
```

### Querying DAG Structure

```python
# Get all paths from root to a state
paths = history.get_all_paths_from_root(target_state_id)

# Get immediate children of a state
children = history.get_child_states(state_id)

# Check if state is a branch point
is_branch = history.is_branch_point(state_id)

# Get all branch points
branch_points = history.get_branch_points()

# Find path between any two states
sequence = history.get_transformation_sequence(from_state, to_state)
```

### DAG Statistics

```python
stats = history.get_dag_statistics()
# Returns:
# {
#     "total_states": 10,
#     "total_transformations": 9,
#     "total_branches": 3,
#     "active_branches": 2,
#     "branch_points": 2,
#     "root_state_id": "...",
#     "current_state_id": "...",
#     "max_depth": 5
# }
```

## Use Cases

### 1. Theorem Proving with Alternative Paths

```python
# Start proof
uod = UniverseOfDiscourse(metadata, initial_egi)
uod.promote_to_historical("Initial theorem statement")

# Apply several transformations
uod.history.add_transformation(...)  # State 1
uod.history.add_transformation(...)  # State 2
uod.history.add_transformation(...)  # State 3

# Try alternative approach from State 2
branch_id = uod.history.create_branch_from_state(
    state_2_id,
    HistoryBranchType.ALTERNATIVE,
    "Try contrapositive approach"
)

# Explore alternative
uod.history.add_transformation(...)  # State 4a
uod.history.add_transformation(...)  # State 5a

# Compare both approaches
main_path = uod.history.get_transformation_sequence(root, state_3)
alt_path = uod.history.get_transformation_sequence(root, state_5a)
```

### 2. Learning with Exploration

```python
# Practice session
uod = create_practice_session()

# Make several moves
apply_transformation(...)  # State 1
apply_transformation(...)  # State 2

# "What if I had done X instead?"
branch_id = uod.history.create_branch_from_state(
    state_1_id,
    HistoryBranchType.EXPLORATION,
    "Exploring different strategy"
)

# Explore alternative without losing original work
apply_transformation(...)  # State 3a (on branch)
apply_transformation(...)  # State 4a (on branch)
```

### 3. Collaborative Reasoning

```python
# Researcher A's approach
main_branch = uod.current_branch_id

# Researcher B explores alternative
branch_b = uod.history.create_branch_from_state(
    state_id,
    HistoryBranchType.ALTERNATIVE,
    "Researcher B's alternative proof"
)

# Both paths preserved in same UoD
all_branches = uod.history.get_all_branches()
compare_approaches(branch_a, branch_b)
```

## Backward Compatibility

**100% backward compatible** with existing linear history:
- Linear sequences still work exactly as before
- `state_sequence` and `step_sequence` maintained for compatibility
- New DAG features are opt-in (use branching methods explicitly)
- All existing code continues to work unchanged

## Implementation Details

### Path Finding

**Breadth-First Search (BFS)** finds shortest path between states:
```python
def _find_path_bfs(from_state, to_state) -> List[str]:
    # Returns shortest path or None if no path exists
```

**Depth-First Search (DFS)** finds all paths:
```python
def get_all_paths_from_root(target_state) -> List[List[str]]:
    # Returns all possible paths from root to target
```

### Branch Point Detection

Automatically tracked when states gain multiple children:
```python
# When adding transformation
if len(state_to_outgoing_steps[current_state]) > 1:
    branch_points.add(current_state)
```

### Cycle Prevention

DAG structure prevents cycles:
- Each state has at most one incoming edge (from parent)
- Multiple outgoing edges allowed (branching)
- Path finding includes cycle detection

## Export/Import

DAG structure fully serializable:

```python
export_data = history.export_history_data()
# Includes:
# - root_state_id
# - branch_points
# - dag_statistics
# - all states, transformations, branches
```

## GUI Integration

### Organon (Visualization)

```
History Timeline:
┌─────────────────────────────────────┐
│ State 0 (root)                      │
│    │                                │
│    ├─→ State 1 (main)               │
│    │     │                          │
│    │     ├─→ State 2                │
│    │     │     │                    │
│    │     │     └─→ State 3 (leaf)  │
│    │     │                          │
│    │     └─→ State 2a (branch)     │
│    │           │                    │
│    │           └─→ State 3a (leaf) │
└─────────────────────────────────────┘
```

Features:
- Visual DAG representation
- Branch point indicators
- Navigate any path
- Compare states across branches

### Ergasterion (Practice)

- "Branch from here" button on timeline
- Explore alternatives without losing work
- Visual indication of current branch
- Merge/compare branches

## Testing

Comprehensive test suite validates:
- ✅ Linear history (backward compatibility)
- ✅ Branching from any state
- ✅ Multiple paths through DAG
- ✅ Branch point detection
- ✅ Path finding (BFS/DFS)
- ✅ DAG statistics
- ✅ Export/import with DAG structure

Test coverage: `tools/test_history_dag.py`

## Performance

**Time Complexity:**
- Add transformation: O(1)
- Create branch: O(1)
- Find shortest path: O(V + E) BFS
- Find all paths: O(V!) DFS (worst case)
- Get children: O(1)
- Check branch point: O(1)

**Space Complexity:**
- O(V + E) where V = states, E = transformations

**Scalability:**
- Efficient for typical inquiry (10-100 states)
- Handles complex proofs (100-1000 states)
- Path finding optimized for DAG structure

## Future Enhancements

1. **Merge Branches**: Combine alternative paths
2. **Branch Labels**: User-defined names for branches
3. **Branch Colors**: Visual distinction in GUI
4. **Diff Views**: Compare states across branches
5. **Branch Metrics**: Success rates, path lengths
6. **Automatic Pruning**: Remove abandoned branches

## References

- **Dau Chapters 14-15**: Transformation rules
- **UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md**: UoD model
- **egi_transformation_history.py**: Implementation
- **tools/test_history_dag.py**: Test suite

## Summary

The DAG-based history model enables realistic inquiry workflows while maintaining 100% backward compatibility. Branch from any state, explore alternatives, and preserve full reasoning context—all within a single Universe of Discourse.

**Key Benefit**: Inquiry is not linear—now the UoD model reflects that reality.
