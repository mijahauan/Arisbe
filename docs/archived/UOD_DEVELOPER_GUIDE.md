# Universe of Discourse: Developer Guide
**Working with UoDs Across Organon, Ergasterion, and Agon**

> **⚠️ RETIRED (2026-06-08).** This March-2026 guide documents an API that has
> since been replaced wholesale: `GraphEntity` (now `UniverseOfDiscourse`),
> `src/tomos_index.py` (now `TomosService` in `src/tomos_service.py`),
> `IntegratedCorpusManager` (gone), and `EntityMetadata`/`EntityType` (now
> `UoDMetadata`/`UoDType`/`UoDCategory`). Following its code examples will
> import modules that no longer exist. For the **concepts** see
> [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](../UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md);
> for the **live API** see `src/tomos_service.py`,
> [CORE_API_USAGE_GUIDE.md](../CORE_API_USAGE_GUIDE.md), and
> [ARISBE_CORE_API_REFERENCE.md](../ARISBE_CORE_API_REFERENCE.md). Kept for
> historical reference.

---

## Quick Reference

### The Fundamental Entity

**Universe of Discourse (UoD)**: The complete diachronic process of logical reasoning
- **Not**: A static EGI diagram  
- **But**: The evolving history of transformations, states, and justifications

**Single EGI**: A synchronic snapshot (one frame) within the UoD (the film)

---

## Data Model

### Current Implementation (GraphEntity)
**Location**: `src/graph_entity.py`

```python
@dataclass
class GraphEntity:
    """
    Unified entity representing both synchronic and diachronic aspects.
    
    NOTE: Despite the name "GraphEntity", this is conceptually a UoD.
    Future refactoring will rename to UniverseOfDiscourse.
    """
    metadata: EntityMetadata
    current_egi: RelationalGraphWithCuts  # Synchronic: current state
    history: Optional[EGITransformationHistory]  # Diachronic: transformation log
```

### State Representation

**Complete State** = `(EGI_Model, LayoutDeltas)`

```python
@dataclass
class StateSnapshot:
    """A single frame in the UoD film."""
    state_id: str
    egi: RelationalGraphWithCuts
    timestamp: datetime
    step_number: int
    description: str
    
    # Visual presentation
    diagram_metadata: Dict[str, Any]  # Contains LayoutDeltas
    
    # Linear representations
    linear_forms: Dict[str, str]  # "egif", "cgif", "clif"
    
    # Semantic context
    natural_language_summary: Optional[str]
```

### Transformation History

**Location**: `src/egi_transformation_history.py`

```python
class EGITransformationHistory:
    """Complete diachronic record of UoD evolution."""
    
    # Core storage
    states: Dict[str, StateSnapshot]
    transformations: Dict[str, TransformationStep]
    branches: Dict[str, HistoryBranch]
    
    # Navigation
    state_sequence: List[str]
    current_state_id: str
    
    # Methods
    def add_transformation(rule_name, context, result) -> str
    def get_state(state_id) -> StateSnapshot
    def get_transformation_sequence(from_state, to_state) -> List[TransformationStep]
```

---

## Module-Specific Usage

### Organon 🏛️ (Archive & Publishing)

**Purpose**: Browse, explore, export UoDs

#### Load UoD for Browsing
```python
from tomos_index import load_index, graph_paths
from egi_io import load_egi_json
from graph_entity import GraphEntity

# Browse corpus
index = load_index()
uod_entry = index['entries'][0]

# Load metadata only (fast)
gdir = Path(f"tomos/graphs/{uod_entry['id']}")
info = read_info(gdir)

# Load full UoD
paths = graph_paths(gdir)
egi = load_egi_json(paths['egi'])

# TODO: Load history if exists
# history = load_history(...)
```

#### Navigate History
```python
# If UoD has history
if entity.is_historical:
    # Get current state
    current = entity.history.get_current_state()
    
    # Get specific historical state
    state = entity.history.get_state(state_id)
    
    # Get transformation sequence
    sequence = entity.history.get_transformation_sequence(
        from_state_id=initial_state,
        to_state_id=final_state
    )
    
    # Iterate through timeline
    for state_id in entity.history.state_sequence:
        state = entity.history.get_state(state_id)
        print(f"Step {state.step_number}: {state.description}")
```

#### Export
```python
from history_persistence import HistoryPersistenceManager

# Export current state
from simple_svg_renderer import SimpleSVGRenderer
renderer = SimpleSVGRenderer()
svg = renderer.render(egi, layout_dto)
with open("export.svg", "w") as f:
    f.write(svg)

# Export proof sequence
if entity.is_historical:
    persistence = HistoryPersistenceManager()
    proof_path = persistence.export_proof_sequence(
        history=entity.history,
        from_state_id=initial,
        to_state_id=final,
        filename="my_proof.yaml"
    )
```

---

### Ergasterion 🔬 (Workshop)

**Purpose**: Create, practice, prepare for promotion to Agon

#### Start Practice Session
```python
from egi_core_dau import create_empty_graph
from graph_entity import GraphEntity, EntityMetadata, EntityType, EntityCategory

# Create new empty UoD for practice
egi = create_empty_graph()
# ... build EGI ...

metadata = EntityMetadata(
    entity_id=f"practice_{uuid.uuid4().hex[:8]}",
    entity_type=EntityType.STANDALONE,  # Ephemeral, no history
    name="Practice Session",
    category=EntityCategory.USER_CREATED,
    created=datetime.now(),
    last_modified=datetime.now(),
    # ... other fields
)

practice_entity = GraphEntity(
    metadata=metadata,
    current_egi=egi,
    history=None  # No history in Ergasterion
)
```

#### Copy Literature Example
```python
# Load literature example
literature_egi = load_egi_json("tomos/literature/peirce_modus_ponens.egi.json")

# Create practice copy
practice_entity = GraphEntity(
    metadata=...,  # New metadata for practice
    current_egi=literature_egi,  # Start with literature EGI
    history=None
)

# Now modify safely without affecting original
```

#### Practice Transformations
```python
from formal_transformation_rules import DeiterationRule, TransformationContext

# Apply rule (not recorded in history)
rule = DeiterationRule()
context = TransformationContext(
    source_egi=practice_entity.current_egi,
    target_area=selected_area,
    # ... other context
)
result = rule.apply_transformation(context)

if result.success:
    # Update current EGI
    practice_entity.current_egi = result.result_egi
```

#### Promote to Agon
```python
# User satisfied with practiced graph
# Trigger promotion workflow:

# 1. Validate
from integrated_corpus_manager import IntegratedCorpusManager
manager = IntegratedCorpusManager()
is_valid = manager.validate_item(practice_entity)

if is_valid:
    # 2. Prepare metadata for main UoD
    uod_metadata = EntityMetadata(
        entity_id=f"uod_{uuid.uuid4().hex[:8]}",
        entity_type=EntityType.HISTORICAL,  # Will have history
        name="Main UoD Name",
        category=EntityCategory.ACTIVE_INQUIRY,
        # ...
    )
    
    # 3. Create UoD with history
    uod = GraphEntity(
        metadata=uod_metadata,
        current_egi=practice_entity.current_egi,
        history=None
    )
    uod.promote_to_historical("Initial state from Ergasterion")
    
    # 4. Pass to Agon for Endoporeutic Game challenge
    # ... Agon validation workflow ...
```

---

### Agon ⚔️ (Core Reasoning Engine)

**Purpose**: Validate changes, record history, advance UoD

#### Load Active UoD
```python
from tomos_service import TomosService  # Future unified API

corpus = TomosService()
uod = corpus.get_graph(uod_id)

# Ensure it has history
if not uod.is_historical:
    uod.promote_to_historical("Agon session started")
```

#### Apply Validated Transformation
```python
from formal_transformation_rules import DeiterationRule, TransformationContext

# 1. Create context
rule = DeiterationRule()
context = TransformationContext(
    source_egi=uod.current_egi,
    target_area=selected_area,
    transformation_rule="IT-",
    # ... other fields
)

# 2. Validate preconditions
if not rule.check_preconditions(context):
    print("Transformation invalid!")
    return

# 3. Apply transformation
result = rule.apply_transformation(context)

if result.success:
    # 4. Record in history
    step_id = uod.history.add_transformation(
        rule_name="IT-",
        context=context,
        result=result,
        user_annotation="Removed iterated subgraph",
        logical_justification="Dau Theorem 12.3.1"
    )
    
    # 5. Update current state
    uod.current_egi = result.result_egi
    uod.metadata.last_modified = datetime.now()
    uod.metadata.total_transformations += 1
    
    # 6. Save to corpus
    corpus.save_graph(uod)
```

#### Endoporeutic Game (Future Implementation)
```python
from agon_game_engine import EndoporeuticGame, Graphist, Grapheus

# User proposes new fact
proposed_egi = ...  # From Ergasterion

# Initiate game
game = EndoporeuticGame(
    sheet_of_assertion=uod.current_egi,
    proposed_assertion=proposed_egi
)

# Roles
graphist = Graphist(user_id=current_user)
grapheus = Grapheus(system_challenger=True)

# Game loop
while not game.is_finished():
    if game.current_turn == "grapheus":
        # System tries to reduce to empty sheet
        move = grapheus.choose_move(game.current_state)
        game.apply_move(move)
    else:
        # User defends
        user_move = get_user_move_from_ui()
        game.apply_move(user_move)

# Outcome
if game.winner == "graphist":
    # Assertion justified - accept into UoD
    step_id = uod.history.add_transformation(
        rule_name="ASSERT",
        context=...,
        result=...,
        user_annotation="New fact accepted via Endoporeutic Game",
        logical_justification=f"Defended successfully in game {game.game_id}"
    )
    
    # Merge proposed_egi into uod.current_egi
    uod.current_egi = merge_assertion(uod.current_egi, proposed_egi)
    corpus.save_graph(uod)
else:
    # Assertion rejected
    print("Proposed fact was not justified")
```

---

## Tomos Operations

### Current API (Interim)

**Location**: `src/tomos_index.py`

```python
from tomos_index import (
    load_index,
    create_graph_dir,
    graph_paths,
    read_info,
    write_info,
    upsert_entry
)

# List all UoDs
index = load_index()
for entry in index['entries']:
    print(f"{entry['id']}: {entry['title']}")

# Create new UoD directory
gdir = create_graph_dir(
    graph_id="inquiry_001",
    title="My Investigation",
    category="active_inquiry",
    tags=["practice"]
)

# Get file paths
paths = graph_paths(gdir)
# paths['egi'] = Path to .egi.json
# paths['info'] = Path to .json metadata
# paths['egdf_dir'] = EGDF directory
# paths['exports_dir'] = Exports directory

# Save EGI
from egi_io import save_egi_json
save_egi_json(uod.current_egi, paths['egi'])

# Save metadata
info = {
    "title": uod.name,
    "category": uod.metadata.category.value,
    "description": uod.description,
    # ...
}
write_info(gdir, info)

# Update index
entry = {
    "id": uod.entity_id,
    "title": uod.name,
    "category": uod.metadata.category.value,
    "path": str(gdir),
    "updated": datetime.now().isoformat(),
}
upsert_entry(entry)
```

### Future API (TomosService)

**Location**: `src/tomos_service.py` (to be created)

```python
from tomos_service import TomosService

corpus = TomosService()

# List UoDs
all_uods = corpus.list_graphs()
inquiry_uods = corpus.list_graphs(category=UoDCategory.ACTIVE_INQUIRY)

# Get UoD
uod = corpus.get_graph(uod_id)

# Create new UoD
new_uod = corpus.create_graph(
    name="New Investigation",
    egi=initial_egi,
    category=UoDCategory.ACTIVE_INQUIRY
)

# Save UoD (includes history)
corpus.save_graph(uod)

# Search
results = corpus.search(query="modus ponens", filters={"category": "literature"})

# Validate
validation = corpus.validate_graph(uod_id)

# Export proof
proof_path = corpus.export_proof(
    graph_id=uod_id,
    from_state=initial_state_id,
    to_state=final_state_id
)
```

---

## Common Patterns

### Pattern 1: Import Literature Example (Organon)
```python
# 1. Load from corpus
index = load_index()
lit_entry = [e for e in index['entries'] if e['category'] == 'peirce'][0]

# 2. Load EGI
gdir = Path(f"tomos/literature/{lit_entry['id']}")
paths = graph_paths(gdir)
egi = load_egi_json(paths['egi'])

# 3. Create static UoD (no history)
uod = GraphEntity(
    metadata=EntityMetadata(
        entity_id=lit_entry['id'],
        entity_type=EntityType.STANDALONE,
        name=lit_entry['title'],
        category=EntityCategory.PEIRCE,
        # ...
    ),
    current_egi=egi,
    history=None  # Static import
)

# 4. Display in Organon
# ... visualization code ...
```

### Pattern 2: Start Active Inquiry (Ergasterion → Agon)
```python
# === ERGASTERION ===
# 1. Create practice session
practice_egi = create_empty_graph()
# ... build initial graph ...

# 2. Experiment with transformations
# ... apply rules, refine graph ...

# === AGON ===
# 3. Promote to main UoD
uod = GraphEntity(
    metadata=EntityMetadata(
        entity_id=f"inquiry_{uuid.uuid4().hex[:8]}",
        entity_type=EntityType.HISTORICAL,
        name="Active Inquiry Session",
        category=EntityCategory.ACTIVE_INQUIRY,
        # ...
    ),
    current_egi=practice_egi,  # From Ergasterion
    history=None
)

# 4. Initialize history
uod.promote_to_historical("Initial state from Ergasterion")

# 5. Continue with Agon transformations
# ... validated rule applications recorded in history ...

# 6. Save to corpus
corpus.save_graph(uod)
```

### Pattern 3: Navigate and Rollback (Organon)
```python
# 1. Load UoD with history
uod = corpus.get_graph(uod_id)

if uod.is_historical:
    # 2. View timeline
    print(f"Total states: {len(uod.history.states)}")
    for state_id in uod.history.state_sequence:
        state = uod.history.get_state(state_id)
        print(f"  {state.step_number}: {state.description}")
    
    # 3. Jump to specific state
    target_state = uod.history.get_state(specific_state_id)
    
    # 4. Rollback (create new branch)
    # Set current_state_id to earlier state
    uod.history.current_state_id = earlier_state_id
    uod.current_egi = uod.history.get_state(earlier_state_id).egi
    
    # 5. Continue from there (creates new branch)
    # ... apply new transformations ...
```

### Pattern 4: Export Proof Sequence (Organon)
```python
from history_persistence import HistoryPersistenceManager

# 1. Load UoD
uod = corpus.get_graph(proof_uod_id)

if uod.is_historical:
    # 2. Identify proof sequence
    initial_state = uod.history.state_sequence[0]
    final_state = uod.history.state_sequence[-1]
    
    # 3. Export to YAML
    persistence = HistoryPersistenceManager()
    proof_path = persistence.export_proof_sequence(
        history=uod.history,
        from_state_id=initial_state,
        to_state_id=final_state,
        filename="theorem_proof.yaml"
    )
    
    print(f"Proof exported to {proof_path}")
```

---

## State Management Best Practices

### Immutability
**EGI is immutable** - always create new instances:
```python
# ❌ WRONG - mutating EGI
egi.V.append(new_vertex)

# ✅ CORRECT - immutable pattern
new_egi = egi.with_vertex(new_vertex)
```

### LayoutDeltas
**User edits should be layout deltas**, not EGI changes:
```python
# User drags vertex
layout_deltas = {
    vertex_id: {
        "type": "vertex_position",
        "position": [new_x, new_y]
    }
}

# Store with state
state.diagram_metadata['layout_deltas'] = layout_deltas
```

### History Recording
**Always record transformations** in Agon:
```python
# After successful transformation
step_id = uod.history.add_transformation(
    rule_name=rule_name,
    context=context,
    result=result,
    user_annotation=user_comment,
    logical_justification=citation
)
```

---

## Testing UoDs

### Unit Tests
```python
def test_uod_creation():
    egi = create_empty_graph()
    uod = GraphEntity(
        metadata=...,
        current_egi=egi,
        history=None
    )
    
    assert uod.is_standalone
    assert not uod.is_historical

def test_uod_promotion():
    uod = create_standalone_uod()
    uod.promote_to_historical("Initial")
    
    assert uod.is_historical
    assert len(uod.history.states) == 1

def test_transformation_recording():
    uod = create_historical_uod()
    initial_count = len(uod.history.transformations)
    
    # Apply transformation
    result = apply_rule(uod)
    step_id = uod.history.add_transformation(...)
    
    assert len(uod.history.transformations) == initial_count + 1
```

### Integration Tests
```python
def test_ergasterion_to_agon_workflow():
    # 1. Create in Ergasterion
    practice = create_practice_session()
    
    # 2. Promote to Agon
    uod = promote_to_agon(practice)
    
    # 3. Validate
    assert uod.is_historical
    assert uod.metadata.category == UoDCategory.ACTIVE_INQUIRY
    
    # 4. Apply transformation in Agon
    apply_transformation(uod, rule="IT-")
    
    # 5. Verify history
    assert len(uod.history.transformations) > 0
```

---

## Migration Notes

### From Current Code
**Existing** `GraphEntity` instances can be used as UoDs:
```python
# Current code
entity = GraphEntity(metadata=..., current_egi=egi, history=None)

# Future code (after refactoring)
uod = UniverseOfDiscourse(metadata=..., current_egi=egi, history=None)

# Same interface, better name
```

### Tomos Migration
When `TomosService` is implemented:
1. Existing graphs will be migrated to UoD structure
2. Static literature imports remain standalone
3. User-created graphs get history tracking
4. New tomos structure: `tomos/universes/`

---

## Key Takeaways

1. **UoD is fundamental** - not EGI
2. **EGI is synchronic** - a snapshot in time
3. **History is diachronic** - the complete evolution
4. **State = (EGI, LayoutDeltas)** - structure + presentation
5. **Three modules** - Organon (archive), Ergasterion (workshop), Agon (arena)
6. **Justification through dialogue** - Endoporeutic Game
7. **Complete provenance** - every transformation recorded
8. **Immutable transformations** - history is append-only

---

## Next Steps

### For Developers
1. Read `UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md` for philosophy
2. Use current `GraphEntity` as interim UoD model
3. Follow patterns in this guide
4. Prepare for `TomosService` unified API

### For Implementation
1. Phase 1: Refactor `GraphEntity` → `UniverseOfDiscourse`
2. Phase 2: Implement `TomosService` unified API
3. Phase 3: Build Ergasterion module with isolation
4. Phase 4: Build Agon module with Endoporeutic Game
5. Phase 5: Update Organon for UoD-centric browsing

---

**Last Updated**: 2025-10-14  
**Status**: Developer Guide  
**See Also**: 
- `UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md` - Complete philosophical foundation
- `DATA_PERSISTENCE_MODEL_SUMMARY.md` - Storage and tomos organization
- `CORPUS_API_QUICK_REFERENCE.md` - Current interim APIs
- `AGENTS.md` - Development guidelines
