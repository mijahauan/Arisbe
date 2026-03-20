# Tomos API Quick Reference
**For Organon/Ergasterion/Agon Development**

---

## TL;DR - What to Use Right Now

### ⚠️ CURRENT STATE: FRAGMENTED

**For Organon (Read-Only Viewing)**:
```python
from tomos_index import load_index, graph_paths, read_info
from egi_io import load_egi_json

# Browse corpus
index = load_index()
for entry in index['entries']:
    print(entry['id'], entry['title'])

# Load graph
gdir = Path(f"tomos/graphs/{graph_id}")
paths = graph_paths(gdir)
egi = load_egi_json(paths['egi'])
info = read_info(gdir)
```

**For Ergasterion/Agon (WITH History)**:
```python
from graph_entity import GraphEntity, EntityMetadata, EntityType, EntityCategory
from egi_io import load_egi_json, save_egi_json
from egi_transformation_history import EGITransformationHistory

# Create entity
metadata = EntityMetadata(
    entity_id=graph_id,
    entity_type=EntityType.STANDALONE,  # or HISTORICAL
    name=name,
    category=EntityCategory.USER_CREATED,
    # ... other fields
)
entity = GraphEntity(metadata=metadata, current_egi=egi)

# Promote to historical for transformations
entity.promote_to_historical("Initial state")

# Access history
entity.history.add_transformation(...)
```

**⚠️ NOTE**: Above code is interim solution. See "Recommended Consolidated API" below for future direction.

---

## Current Storage Locations

### Tomos Root
```
tomos/
  index.json           # Lightweight tomos index
  graphs/              # One directory per graph
    <graph_id>/
      <graph_id>.egi.json      # Canonical EGI (use this!)
      <graph_id>.json          # Metadata + linear forms
      EGDF/                    # EGDF documents
      EXPORTS/                 # Exported artifacts
```

### Important Files
- **Canonical EGI**: `tomos/graphs/<graph_id>/<graph_id>.egi.json` ← **SOURCE OF TRUTH**
- **Metadata**: `tomos/graphs/<graph_id>/<graph_id>.json`
- **Index**: `tomos/index.json` ← For browsing

---

## Current Working Functions (tomos_index.py)

### Load Index
```python
from tomos_index import load_index

index = load_index()
# Returns: {
#   "name": "Arisbe Corpus",
#   "version": "0.1",
#   "entries": [
#     {"id": "...", "title": "...", "category": "...", "tags": [], ...}
#   ]
# }
```

### Create New Graph
```python
from tomos_index import create_graph_dir

gdir = create_graph_dir(
    graph_id="my_new_graph",
    title="My New Graph",
    category="user_created",
    tags=["tag1", "tag2"]
)
# Creates: tomos/graphs/my_new_graph/ with subdirectories
# Returns: Path to graph directory
```

### Get Graph Paths
```python
from tomos_index import graph_paths

paths = graph_paths(gdir)
# Returns: {
#   'egi': Path('tomos/graphs/<id>/<id>.egi.json'),
#   'info': Path('tomos/graphs/<id>/<id>.json'),
#   'egdf_dir': Path('tomos/graphs/<id>/EGDF/'),
#   'exports_dir': Path('tomos/graphs/<id>/EXPORTS/')
# }
```

### Read/Write Metadata
```python
from tomos_index import read_info, write_info

# Read
info = read_info(gdir)
# Returns: dict with title, category, tags, linear_forms, etc.

# Write
write_info(gdir, info_dict)
```

---

## EGI Serialization (egi_io.py)

### Save EGI
```python
from egi_io import save_egi_json

save_egi_json(egi, "tomos/graphs/my_graph/my_graph.egi.json")
```

### Load EGI
```python
from egi_io import load_egi_json

egi = load_egi_json("tomos/graphs/my_graph/my_graph.egi.json")
# Returns: RelationalGraphWithCuts
```

---

## GraphEntity Model (graph_entity.py)

### EntityMetadata
```python
from graph_entity import EntityMetadata, EntityType, EntityCategory
from datetime import datetime

metadata = EntityMetadata(
    entity_id="unique_id",
    entity_type=EntityType.STANDALONE,  # or HISTORICAL
    name="Human-readable name",
    description="Optional description",
    category=EntityCategory.USER_CREATED,
    created=datetime.now(),
    last_modified=datetime.now(),
    current_state_id=None,  # For historical entities
    total_states=1,
    total_transformations=0,
    authors=["author_name"],
    tags={"tag1", "tag2"},
    source_citation=None
)
```

### EntityCategory Options
- `EntityCategory.PEIRCE` - From Peirce's writings
- `EntityCategory.SCHOLARS` - From secondary literature
- `EntityCategory.CANONICAL` - Synthetic standard patterns
- `EntityCategory.EPG` - Endoporeutic Game positions
- `EntityCategory.THEOREM_PROVING` - Mathematical proofs
- `EntityCategory.DOMAIN_MODELING` - Real-world applications
- `EntityCategory.USER_CREATED` - User-generated content
- `EntityCategory.UNIVERSE` - Living universe of discourse

### Create GraphEntity
```python
from graph_entity import GraphEntity

entity = GraphEntity(
    metadata=metadata,
    current_egi=egi,
    history=None  # or EGITransformationHistory instance
)
```

### Promote to Historical
```python
# Convert standalone entity to historical
entity.promote_to_historical("Initial state description")

# Now entity.history is available
entity.history  # EGITransformationHistory instance
```

### Check Entity Type
```python
if entity.is_standalone:
    print("Standalone entity (no history)")

if entity.is_historical:
    print("Historical entity (has transformation history)")
```

### Get Linear Forms
```python
egif = entity.get_current_egif()
cgif = entity.get_current_cgif()
clif = entity.get_current_clif()
```

### Access History
```python
if entity.is_historical:
    # Get specific state
    state = entity.get_state(state_id)
    
    # Get transformation
    transform = entity.get_transformation(step_id)
    
    # Access all states
    states = entity.history.states
    
    # Access all transformations
    transforms = entity.history.transformations
```

---

## Recommended Consolidated API (FUTURE)

### TomosService (Not Yet Implemented)

**Proposed unified API for all components**:

```python
from tomos_service import TomosService

corpus = TomosService()

# === ORGANON: Browse & View ===

# List graphs
graphs = corpus.list_graphs(category=EntityCategory.PEIRCE)

# Get metadata only (fast)
meta = corpus.get_graph_metadata(graph_id)

# Load full graph
entity = corpus.get_graph(graph_id)
egi = entity.current_egi

# Search
results = corpus.search(query="modus ponens", filters={"category": "peirce"})

# === ERGASTERION: Create & Transform ===

# Create new graph
entity = corpus.create_graph(
    name="my_practice_graph",
    egi=initial_egi,
    category=EntityCategory.USER_CREATED
)

# Promote for transformation tracking
entity.promote_to_historical()

# Save (includes history)
corpus.save_graph(entity)

# Export proof sequence
corpus.export_proof(
    graph_id=entity.entity_id,
    from_state=initial_state_id,
    to_state=final_state_id
)

# === AGON: Game Positions ===

# Create EPG position
game_entity = corpus.create_graph(
    name="epg_session_001",
    egi=game_position,
    category=EntityCategory.EPG
)

# Game moves create history automatically
game_entity.promote_to_historical()

# === VALIDATION ===

# Validate graph
validation = corpus.validate_graph(graph_id)

# Get statistics
stats = corpus.get_statistics()
```

---

## Common Patterns

### Pattern 1: Browse and View (Organon)
```python
from tomos_index import load_index, graph_paths
from egi_io import load_egi_json

# 1. Load index
index = load_index()

# 2. Pick graph
entry = index['entries'][0]
graph_id = entry['id']

# 3. Load EGI
gdir = Path(f"tomos/graphs/{graph_id}")
paths = graph_paths(gdir)
egi = load_egi_json(paths['egi'])

# 4. Display
# ... visualization code ...
```

### Pattern 2: Create New Graph
```python
from tomos_index import create_graph_dir, graph_paths, upsert_entry
from egi_io import save_egi_json
from egi_core_dau import create_empty_graph

# 1. Create EGI
egi = create_empty_graph()
# ... build EGI ...

# 2. Create directory
gdir = create_graph_dir(
    graph_id="my_new_graph",
    title="My New Graph",
    category="user_created",
    tags=["example"]
)

# 3. Save EGI
paths = graph_paths(gdir)
save_egi_json(egi, paths['egi'])

# 4. Update index
upsert_entry(entry_dict)
```

### Pattern 3: Transform with History (Ergasterion)
```python
from graph_entity import GraphEntity, EntityMetadata, EntityType, EntityCategory
from egi_transformation_history import EGITransformationHistory, StateSnapshot
from egi_io import load_egi_json
from datetime import datetime
import uuid

# 1. Load existing EGI
egi = load_egi_json("tomos/graphs/base_graph/base_graph.egi.json")

# 2. Create entity with history
metadata = EntityMetadata(
    entity_id=f"practice_{uuid.uuid4().hex[:8]}",
    entity_type=EntityType.HISTORICAL,
    name="Practice Session",
    category=EntityCategory.USER_CREATED,
    created=datetime.now(),
    last_modified=datetime.now(),
    current_state_id=None,
    total_states=1,
    total_transformations=0,
    authors=["student"],
    tags={"practice"},
    source_citation=None
)

entity = GraphEntity(metadata=metadata, current_egi=egi)
entity.promote_to_historical("Initial state")

# 3. Apply transformations
# ... transformation logic ...
# entity.history.add_transformation(...)

# 4. Save
# ... save entity using entity_storage or custom code ...
```

### Pattern 4: Export Proof Sequence
```python
from history_persistence import HistoryPersistenceManager

# 1. Load or create entity with history
# ... 

# 2. Export proof
persistence = HistoryPersistenceManager()
proof_path = persistence.export_proof_sequence(
    history=entity.history,
    from_state_id=initial_state,
    to_state_id=final_state,
    filename="my_proof.yaml"
)
```

---

## File Naming Conventions

### Current Convention (tomos_index.py)
```
<graph_id>.egi.json      # Canonical EGI
<graph_id>.json          # Metadata
EGDF/                    # EGDF documents directory
EXPORTS/                 # Exports directory
```

### Observed Variations (inconsistent)
```
<graph_id>.meta.json     # Additional metadata (some graphs)
<variant_name>.egi.json  # Variants (some graphs)
```

### Recommended Convention (consolidation)
```
<graph_id>.egi.json        # Canonical EGI ← SOURCE OF TRUTH
<graph_id>.meta.json       # EntityMetadata
<graph_id>.history.jsonl   # Transformation history (if historical)
snapshots/                 # State snapshots (if historical)
variants/                  # EGI variants (if any)
EGDF/                      # EGDF documents
EXPORTS/                   # Exports
```

---

## Data Validation

### Current: No Automatic Validation
- Graphs in tomos are NOT automatically validated
- Use `integrated_corpus_manager.py` for validation (manual)

### Recommended: Validate on Load
```python
from integrated_corpus_manager import IntegratedCorpusManager

manager = IntegratedCorpusManager()
result = manager.validate_item(corpus_item)

if result['is_valid']:
    print("Valid EGI")
else:
    print("Validation errors:", result['errors'])
```

---

## Common Gotchas

### 1. Multiple EGI Files
**Problem**: Some graph directories have multiple `.egi.json` files  
**Solution**: Always use `<graph_id>.egi.json` as canonical source

### 2. Linear Forms Staleness
**Problem**: Linear forms in metadata may be outdated if EGI changed  
**Solution**: Regenerate linear forms on EGI change (or use `get_current_egif()`)

### 3. History Loading Not Implemented
**Problem**: `entity_storage.py` history loading returns `None`  
**Solution**: Use `history_persistence.py` for full history persistence (interim)

### 4. Index Out of Sync
**Problem**: `tomos/index.json` may not reflect actual graph directories  
**Solution**: Use `upsert_entry()` to update index after creating/modifying graphs

### 5. No Transaction Support
**Problem**: Partial failures can leave tomos in inconsistent state  
**Solution**: Manually implement rollback or use file system snapshots

---

## Migration Notes

### Current → Future Transition

**When TomosService is implemented**:

1. **Replace** direct `tomos_index.py` calls with `TomosService` methods
2. **Keep** `GraphEntity` model (it's the foundation)
3. **Keep** `egi_io.py` for low-level serialization
4. **Migrate** custom history management to `TomosService.save_graph()`

**Backward Compatibility**:
- Old tomos structure will be migrated automatically
- Migration script will add `EntityMetadata` to existing graphs
- `tomos_index.py` utilities will remain for backward compat

---

## Questions? See Full Documentation

- **Full analysis**: `DATA_PERSISTENCE_MODEL_SUMMARY.md`
- **Core API reference**: `ARISBE_CORE_API_REFERENCE.md`
- **Architecture**: `AGENTS.md`

---

**Last Updated**: 2025-10-14  
**Status**: Interim guidance - TomosService implementation pending
