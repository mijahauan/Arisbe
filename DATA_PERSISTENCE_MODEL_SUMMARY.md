# Data Persistence Model Summary
**Universe of Discourse Storage for Organon/Ergasterion/Agon**

**Date**: 2025-10-14  
**Purpose**: Define UoD-centric data model and corpus organization

---

## Executive Summary

### Current Status: ⚠️ **FRAGMENTED** + ⚡ **PHILOSOPHICAL REFRAMING**

**Philosophical Shift**: The fundamental entity is the **Universe of Discourse (UoD)**, not a static EGI diagram.
- **UoD** = Diachronic process (the film)
- **EGI** = Synchronic snapshot (one frame)

**Technical Problem**: Multiple overlapping persistence systems with inconsistent interfaces and storage strategies.

**Impact**: 
- Unclear which system to use for Organon/Ergasterion/Agon
- Corpus organized around graphs, not UoDs
- No unified diachronic history model

**Recommendation**: Consolidate to single UoD-centric persistence model before proceeding.

👉 **See also**: [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md) for complete philosophical foundation

---

## Current Persistence Systems (4 Found)

### 1. **corpus_index.py** - Directory-Per-Graph Storage ✅ **IN USE**

**Location**: `src/corpus_index.py`  
**Storage**: `corpus/graphs/<graph_id>/`  
**Status**: **Currently active in corpus**

**Storage Structure**:
```
corpus/
  index.json                    # Lightweight index for browsing
  graphs/
    <graph_id>/
      <graph_id>.egi.json       # Canonical EGI (source of truth)
      <graph_id>.json           # Metadata + linear forms
      EGDF/                     # Derived EGDF documents
      EXPORTS/                  # Exported artifacts (tex/pdf/png)
```

**Data Model**:
```python
@dataclass
class CorpusEntry:
    id: str
    title: str
    category: Optional[str]
    tags: List[str]
    path: Path
    updated: Optional[str]
    has_egdf: Optional[bool]
    has_exports: Optional[bool]
```

**Key Functions**:
- `load_index()` - Load lightweight corpus index
- `create_graph_dir(graph_id, title, category, tags)` - Create new graph
- `graph_paths(gdir)` - Get all file paths for graph
- `read_info(gdir)` / `write_info(gdir, info)` - Metadata management

**Strengths**:
- ✅ Simple, file-based
- ✅ Currently in use (15 graphs in corpus)
- ✅ Clear separation: EGI (canonical) + metadata + derived artifacts
- ✅ Version-aware EGDF storage with timestamps

**Weaknesses**:
- ⚠️ No validation integration
- ⚠️ No transformation history support
- ⚠️ Minimal metadata schema

---

### 2. **integrated_corpus_manager.py** - Full-Featured Corpus Manager

**Location**: `src/integrated_corpus_manager.py`  
**Storage**: Configurable corpus root (default: `corpus/`)  
**Status**: **Implemented but not actively used**

**Data Model**:
```python
@dataclass
class CorpusItem:
    id: str
    title: str
    category: CorpusCategory  # Enum with 7 categories
    description: str
    
    # Content in various formats
    egif_content: Optional[str]
    cgif_content: Optional[str]
    clif_content: Optional[str]
    fopl_content: Optional[str]
    
    # Parsed and validated EGI
    egi: Optional[RelationalGraphWithCuts]
    
    # Validation results
    validation_results: Dict[str, Any]
    chapter_compliance: Dict[str, bool]
    
    # Metadata and provenance
    metadata: Dict[str, Any]
    file_path: Optional[Path]
    source_format: Optional[CorpusFormat]
    
    # Quality metrics
    complexity_score: Optional[float]
    educational_value: Optional[str]
    difficulty_level: Optional[str]
```

**Key Features**:
- Full Dau formalism validation
- Multi-format support (EGIF, CGIF, CLIF, FOPL)
- Chapter compliance checking
- Advanced search and filtering
- Quality metrics and educational categorization
- Validation caching

**Interface** (implements `CorpusManager` protocol):
- `add_egi(egi, metadata) -> str`
- `get_egi(item_id) -> RelationalGraphWithCuts`
- `remove_egi(item_id) -> bool`
- `list_egis(category) -> List[str]`

**Strengths**:
- ✅ Full validation integration
- ✅ Rich metadata and search
- ✅ Quality metrics
- ✅ Protocol-based interface

**Weaknesses**:
- ❌ Not currently used
- ❌ More complex than needed for simple use cases
- ❌ No transformation history support
- ❌ Unclear relationship to corpus_index.py

---

### 3. **entity_storage.py** - Hybrid Snapshots + Deltas

**Location**: `src/entity_storage.py`  
**Storage**: Configurable corpus root (default: `corpus/graphs/`)  
**Status**: **Implemented for GraphEntity, not actively used**

**Data Model**:
```python
# Uses GraphEntity from graph_entity.py
@dataclass
class GraphEntity:
    metadata: EntityMetadata
    current_egi: RelationalGraphWithCuts
    history: Optional[EGITransformationHistory]  # For historical entities
```

**Storage Structure**:
```
corpus/graphs/
  <entity_name>/
    <entity_name>.meta.json      # Entity metadata
    <entity_name>.egi.json        # Current EGI state
    <entity_name>.history.jsonl   # Transformation history (JSONL)
    snapshots/                    # Full EGI snapshots every N states
      state_0000.json
      state_0010.json
      state_0020.json
```

**Key Features**:
- Hybrid storage: snapshots every N states + deltas
- JSONL streaming format for history
- Lazy loading with LRU cache
- Handles 1000+ states efficiently
- Supports both standalone and historical entities

**Interface**:
- `save_entity(entity) -> Path`
- `load_entity(entity_name, load_full_history) -> GraphEntity`
- `load_entity_metadata(entity_name) -> EntityMetadata`
- `list_entities(category) -> List[str]`

**Strengths**:
- ✅ Efficient for large histories
- ✅ Lazy loading
- ✅ Unified standalone/historical model
- ✅ Designed for scalability

**Weaknesses**:
- ❌ Not currently used
- ❌ History loading not fully implemented (returns None)
- ❌ Duplicates functionality of corpus_index.py

---

### 4. **history_persistence.py** - Transformation History Persistence

**Location**: `src/history_persistence.py`  
**Storage**: Configurable base path (default: `histories/`)  
**Status**: **Specialized for transformation histories**

**Storage Structure**:
```
histories/
  json/           # Primary storage format
  yaml/           # Human-readable exports
  compressed/     # Gzipped for large histories
```

**Data Model**:
- Serializes `EnhancedEGITransformationHistory`
- Complete state snapshots
- Transformation steps with provenance
- Branch management
- Collaboration metadata

**Key Features**:
- Multiple formats (JSON, YAML, compressed)
- Incremental checkpoints
- Proof sequence exports
- Domain model integration (placeholder)
- Comprehensive history serialization

**Interface**:
- `save_history_json(history, filename) -> Path`
- `load_history_json(filepath) -> EnhancedEGITransformationHistory`
- `save_history_yaml(history, filename) -> Path`
- `export_proof_sequence(history, from_state, to_state) -> Path`

**Strengths**:
- ✅ Full-featured history persistence
- ✅ Multiple export formats
- ✅ Academic workflow support (YAML)

**Weaknesses**:
- ❌ Separate from corpus storage
- ❌ Not integrated with corpus_index or entity_storage
- ❌ Unclear usage pattern for Organon/Ergasterion/Agon

---

### 5. **egi_io.py** - Basic EGI Serialization ✅ **FOUNDATIONAL**

**Location**: `src/egi_io.py`  
**Status**: **Core utility, actively used**

**Functions**:
- `to_dict(egi) -> Dict` - Serialize EGI to dictionary
- `from_dict(d) -> RelationalGraphWithCuts` - Deserialize EGI
- `save_egi_json(egi, path)` - Save EGI to JSON file
- `load_egi_json(path) -> RelationalGraphWithCuts` - Load EGI from JSON

**Schema**:
```json
{
  "sheet": "sheet",
  "V": [{"id": "...", "label": "...", "is_generic": true}],
  "E": [{"id": "..."}],
  "Cut": [{"id": "..."}],
  "nu": {"edge_id": ["vertex_id1", "vertex_id2"]},
  "rel": {"edge_id": "relation_name"},
  "area": {"cut_id": ["element_id1", "element_id2"]},
  "alphabet": {...},
  "rho": {}
}
```

**Strengths**:
- ✅ Simple, reliable
- ✅ Used by all other systems
- ✅ Well-tested

---

## Data Models Comparison

### GraphEntity (graph_entity.py) - Unified Model ✅ **RECOMMENDED**

**Supports**:
- Standalone EGI (single state, no history)
- Historical sequence (states + transformations)

**Key Properties**:
```python
@dataclass
class EntityMetadata:
    entity_id: str
    entity_type: EntityType  # STANDALONE or HISTORICAL
    name: str
    description: str
    category: EntityCategory  # 8 categories
    created: datetime
    last_modified: datetime
    current_state_id: Optional[str]
    total_states: int
    total_transformations: int
    authors: List[str]
    tags: Set[str]
    source_citation: Optional[str]

@dataclass  
class GraphEntity:
    metadata: EntityMetadata
    current_egi: RelationalGraphWithCuts
    history: Optional[EGITransformationHistory]
```

**Categories**:
- `PEIRCE` - From Peirce's writings
- `SCHOLARS` - From secondary literature
- `CANONICAL` - Synthetic standard patterns
- `EPG` - Endoporeutic Game positions
- `THEOREM_PROVING` - Mathematical proofs
- `DOMAIN_MODELING` - Real-world applications
- `USER_CREATED` - User-generated content
- `UNIVERSE` - Living universe of discourse

**Methods**:
- `is_standalone` / `is_historical`
- `get_current_egif()` / `get_current_cgif()` / `get_current_clif()`
- `get_state(state_id)` - Get historical state
- `get_transformation(step_id)` - Get transformation
- `promote_to_historical()` - Convert standalone → historical

**Strengths**:
- ✅ Unified diachronic-synchronic model
- ✅ Supports both Organon (standalone) and Ergasterion/Agon (historical)
- ✅ Clean interface
- ✅ Category system fits all use cases

---

## Current Actual Usage (Based on Corpus Inspection)

**Active System**: `corpus_index.py`

**Corpus Statistics**:
- **Total graphs**: 15 (as of inspection)
- **Storage format**: Directory per graph
- **Files per graph**:
  - `<graph_id>.egi.json` - Canonical EGI ✅
  - `<graph_id>.json` - Metadata + linear forms ✅
  - `EGDF/` - Derived EGDF documents ✅
  - `EXPORTS/` - Exported artifacts ✅

**Sample Graph** (`sowa_cat_on_mat`):
```
sowa_cat_on_mat/
  sowa_cat_on_mat.egi.json       # Canonical EGI
  sowa_cat_on_mat.json           # Metadata
  sowa_cat_on_mat.meta.json      # Additional metadata (?)
  cat_on_mat_2.egi.json          # Variant (?)
  EGDF/                          # 1 EGDF document
  EXPORTS/                       # Empty
```

**Issues Observed**:
- ⚠️ Inconsistent file naming (`.meta.json` vs `.json`)
- ⚠️ Multiple EGI files in same directory (unclear which is canonical)
- ⚠️ No validation results stored
- ⚠️ No transformation history

---

## Integration Interfaces (integration_interfaces.py)

**Protocols Defined**:

### CorpusManager Protocol
```python
class CorpusManager(Protocol):
    def add_egi(self, egi, metadata) -> str
    def search_corpus(self, query) -> List[Dict]
    def get_egi(self, egi_id) -> Optional[RelationalGraphWithCuts]
```

**Implementations**:
- ✅ `IntegratedCorpusManager` implements this
- ❌ `corpus_index.py` does NOT implement this protocol
- ❌ `EntityStorageManager` does NOT implement this protocol

**Result**: Interface fragmentation

---

## Problems Identified

### 1. **Multiple Overlapping Systems**
- `corpus_index.py` - Actually in use
- `integrated_corpus_manager.py` - Implemented but unused
- `entity_storage.py` - Implemented but unused
- `history_persistence.py` - Separate history storage

**Impact**: Unclear which system to use for new development

### 2. **No Unified Interface**
- Different APIs for same operations
- `corpus_index.py` doesn't implement `CorpusManager` protocol
- Inconsistent return types and error handling

**Impact**: Hard to write code that works across systems

### 3. **Transformation History Not Integrated**
- `history_persistence.py` stores in separate `histories/` directory
- Not connected to corpus graphs
- Unclear how Ergasterion/Agon should track transformations

**Impact**: Can't easily link corpus graphs to transformation sessions

### 4. **Metadata Inconsistency**
- `corpus_index.py`: Minimal metadata (title, category, tags)
- `integrated_corpus_manager.py`: Rich metadata (validation, quality, difficulty)
- `entity_storage.py`: Medium metadata (EntityMetadata)

**Impact**: Can't rely on consistent metadata across graphs

### 5. **No Validation Integration**
- Current corpus (corpus_index.py) has no validation
- `integrated_corpus_manager.py` has validation but isn't used
- Quality unknown for existing corpus graphs

**Impact**: May have invalid graphs in corpus

### 6. **Unclear Storage Location**
- Is it `corpus/graphs/` or `corpus/` root?
- Are histories in `histories/` or `corpus/graphs/<id>/`?
- Are EGDF documents part of graph or separate?

**Impact**: Confusing file organization

---

## Recommendations for Consolidation

### **Recommended Unified Model**

**Use**: `GraphEntity` + `corpus_index.py` storage pattern

**Rationale**:
1. `GraphEntity` provides unified diachronic/synchronic model
2. `corpus_index.py` storage pattern is simple and already in use
3. Combine best of both: rich model + simple storage

### **Proposed Architecture**

```
corpus/
  index.json                     # Lightweight index (keep)
  graphs/
    <graph_id>/
      # Core files (corpus_index.py pattern)
      <graph_id>.egi.json        # Canonical EGI (source of truth)
      <graph_id>.meta.json       # EntityMetadata (from GraphEntity)
      
      # Optional historical data (if EntityType.HISTORICAL)
      <graph_id>.history.jsonl   # Transformation history (entity_storage.py pattern)
      snapshots/                 # State snapshots (entity_storage.py pattern)
      
      # Derived artifacts (corpus_index.py pattern)
      EGDF/                      # EGDF documents
      EXPORTS/                   # Exports
```

**Key Changes**:
1. **Standardize on EntityMetadata** for all graphs
2. **Integrate history** into graph directories (not separate `histories/`)
3. **Remove redundant metadata file** (`<graph_id>.json` → just `<graph_id>.meta.json`)
4. **Clear canonical source**: `<graph_id>.egi.json` is always the truth

### **Unified API**

**Create single CorpusService**:
```python
class CorpusService:
    """Unified corpus management for Organon/Ergasterion/Agon."""
    
    # Basic operations (from corpus_index.py)
    def list_graphs(self, category: Optional[EntityCategory] = None) -> List[str]
    def get_graph(self, graph_id: str) -> GraphEntity
    def save_graph(self, entity: GraphEntity) -> None
    def create_graph(self, name: str, egi: RelationalGraphWithCuts, 
                     category: EntityCategory) -> GraphEntity
    
    # Search (from integrated_corpus_manager.py)
    def search(self, query: str, filters: Dict) -> List[GraphEntity]
    def get_statistics(self) -> Dict[str, Any]
    
    # Validation (from integrated_corpus_manager.py)
    def validate_graph(self, graph_id: str) -> Dict[str, Any]
    
    # History (from entity_storage.py + history_persistence.py)
    def save_history_state(self, graph_id: str, state: StateSnapshot) -> None
    def load_history(self, graph_id: str, lazy: bool = True) -> EGITransformationHistory
    def export_proof(self, graph_id: str, from_state: str, to_state: str) -> Path
```

**Implementation Strategy**:
1. Use `corpus_index.py` file organization
2. Use `GraphEntity` data model
3. Use `entity_storage.py` history patterns
4. Use `integrated_corpus_manager.py` validation/search logic
5. Use `history_persistence.py` export formats

---

## Usage by Application Component

### **Organon** (Read-Only Browsing & Exploration)

**Needs**:
- List all graphs by category
- Load graph metadata (fast, no full EGI load)
- Load full graph for viewing
- Search corpus
- View linear forms (EGIF, CGIF, CLIF)

**Recommended**:
```python
corpus = CorpusService()

# Browse
graphs = corpus.list_graphs(category=EntityCategory.PEIRCE)

# Quick metadata (no EGI load)
meta = corpus.get_graph_metadata(graph_id)

# Full load for viewing
entity = corpus.get_graph(graph_id)
egi = entity.current_egi
egif = entity.get_current_egif()
```

### **Ergasterion** (Learning & Practice with Transformations)

**Needs**:
- All Organon features
- Create new practice graphs
- Apply transformations
- Track transformation history
- Undo/redo
- Save transformation sessions

**Recommended**:
```python
corpus = CorpusService()

# Start practice session
entity = corpus.get_graph(base_graph_id)
entity.promote_to_historical()  # Convert to historical

# Apply transformations (creates history automatically)
# ... transformation logic ...

# Save entire session
corpus.save_graph(entity)  # Saves EGI + history

# Export proof sequence
corpus.export_proof(entity.entity_id, initial_state_id, final_state_id)
```

### **Agon** (Endoporeutic Game)

**Needs**:
- All Ergasterion features
- Game position management
- Branch management (proposer/skeptic moves)
- Multi-user sessions (future)
- Validation of legal moves

**Recommended**:
```python
corpus = CorpusService()

# Create EPG position
entity = corpus.create_graph(
    name="epg_session_001",
    egi=initial_position,
    category=EntityCategory.EPG
)
entity.promote_to_historical()

# Game moves create branches in history
# ... game logic ...

# Save game session
corpus.save_graph(entity)
```

---

## Migration Plan

### Phase 1: Create Unified CorpusService

**Tasks**:
1. Create `src/corpus_service.py`
2. Implement basic operations using `corpus_index.py` + `egi_io.py`
3. Add `GraphEntity` support
4. Add tests

**Files to create**:
- `src/corpus_service.py` - Unified service
- `tests/test_corpus_service.py` - Tests

### Phase 2: Integrate History Support

**Tasks**:
1. Add history methods to CorpusService
2. Integrate `entity_storage.py` snapshot patterns
3. Integrate `history_persistence.py` export formats
4. Test round-trip: save history → load history

**Files to modify**:
- `src/corpus_service.py` - Add history methods
- `src/entity_storage.py` - Fix history loading (currently returns None)

### Phase 3: Add Validation & Search

**Tasks**:
1. Add validation methods from `integrated_corpus_manager.py`
2. Add search methods
3. Add quality metrics
4. Migrate validation cache to corpus service

**Files to modify**:
- `src/corpus_service.py` - Add validation/search

### Phase 4: Migrate Existing Corpus

**Tasks**:
1. Write migration script
2. Add EntityMetadata to all existing graphs
3. Validate all graphs
4. Update index.json format

**Files to create**:
- `tools/migrate_to_unified_corpus.py`

### Phase 5: Update GUI Components

**Tasks**:
1. Update Organon to use CorpusService
2. Implement Ergasterion with history support
3. Implement Agon with branch support

**Files to modify**:
- `src/gui_clean/organon/*`
- `src/gui_clean/ergasterion/*` (to be created)
- `src/gui_clean/agon/*` (to be created)

### Phase 6: Deprecate Old Systems

**Tasks**:
1. Mark `integrated_corpus_manager.py` as deprecated
2. Keep `corpus_index.py` utilities for backward compat
3. Keep `entity_storage.py` utilities (used internally)
4. Keep `history_persistence.py` (used internally)

---

## Success Criteria

### Unified Model
- [ ] Single `CorpusService` API
- [ ] All operations use `GraphEntity` model
- [ ] Consistent storage pattern across corpus

### Data Integrity
- [ ] All existing corpus graphs validated
- [ ] No data loss during migration
- [ ] Round-trip save/load preserves all data

### Cross-Component Consistency
- [ ] Organon, Ergasterion, Agon use same API
- [ ] Same metadata format everywhere
- [ ] Same history format everywhere

### Documentation
- [ ] Clear API documentation
- [ ] Storage format documented
- [ ] Migration guide for existing tools

### Performance
- [ ] Fast metadata browsing (< 100ms for 100 graphs)
- [ ] Lazy history loading works
- [ ] Large histories (1000+ states) handled efficiently

---

## Open Questions

### Q1: Linear Forms Storage
**Current**: Stored in `<graph_id>.json` as generated content  
**Question**: Should linear forms be generated on-demand or cached?  
**Recommendation**: Cache in metadata, regenerate if EGI changes

### Q2: EGDF Document Versioning
**Current**: Timestamped EGDF files in `EGDF/` subdirectory  
**Question**: How to manage multiple EGDF versions of same EGI?  
**Recommendation**: Keep timestamp versioning, add "default" symlink/flag

### Q3: Multiple EGI Files Per Graph
**Observed**: `sowa_cat_on_mat` has 2 EGI files  
**Question**: Are these variants or versions?  
**Recommendation**: One canonical `<graph_id>.egi.json`, variants in `variants/` subdirectory

### Q4: Validation Results Storage
**Current**: Not stored in corpus_index.py system  
**Question**: Should validation results be cached?  
**Recommendation**: Cache in `<graph_id>.meta.json`, refresh on EGI change

### Q5: Collaboration Metadata
**Current**: Only in `history_persistence.py`  
**Question**: How to handle multi-user sessions?  
**Recommendation**: Add to EntityMetadata when needed (defer for now)

---

## Next Steps (Immediate)

### Before Ergasterion/Agon Development:

1. **Create CorpusService** (2-3 days)
   - Implement Phase 1 (basic operations)
   - Test with existing corpus

2. **Add History Support** (2-3 days)
   - Implement Phase 2 (history integration)
   - Test round-trip save/load

3. **Document API** (1 day)
   - Write API documentation
   - Create usage examples for Organon/Ergasterion/Agon

4. **Update AGENTS.md** (1 hour)
   - Document unified corpus model
   - Add to development guidelines

**Total Estimated Time**: 1 week

### After Consolidation:

- Proceed with Ergasterion development using CorpusService
- Proceed with Agon development using CorpusService
- Migrate existing tools to use CorpusService

---

## Summary

**Current State**: Fragmented (4 overlapping systems)

**Recommended State**: Unified CorpusService using GraphEntity model

**Key Benefits**:
- ✅ Single API for all components
- ✅ Consistent data model
- ✅ Integrated history support
- ✅ Simple storage pattern (already in use)
- ✅ Clear migration path

**Blocking Issue for Ergasterion/Agon**: 
Without unified corpus model, each component would need to pick a system and potentially fragment further.

**Recommendation**: 
**Spend 1 week consolidating before proceeding** with Ergasterion/Agon development. This will prevent future integration problems and make development faster.

---

**Last Updated**: 2025-10-14  
**Status**: Analysis Complete - Awaiting Decision on Consolidation
