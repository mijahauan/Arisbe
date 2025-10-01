# Graph Entity Scalability & Architecture Analysis

**Date**: 2025-10-01  
**Purpose**: Design efficient storage and access for large-scale graph entities with complex viewing, sharing, and manipulation requirements

---

## 🎯 REQUIREMENTS ANALYSIS

### **Scale Scenarios**

**Small Entity** (Stand-alone EGI):
- 1 state
- 0 transformations
- ~10-50 KB
- Examples from literature

**Medium Entity** (Short proof):
- 10-50 states
- 10-50 transformations
- ~500 KB - 2 MB
- Tutorial sequences, simple proofs

**Large Entity** (Complex reasoning):
- 100-500 states
- 100-500 transformations
- ~10-50 MB
- Extended theorem proving, complex derivations

**Universe of Discourse** (Ongoing development):
- 1,000+ states
- 1,000+ transformations
- Multiple branches
- ~100+ MB
- Collaborative research, extensive reasoning

---

## 🔍 ACCESS PATTERNS

### **Organon Mode - Exploration**

1. **Timeline Viewing**:
   - Load current state (1 EGI)
   - Navigate to specific state (1 EGI)
   - Scrub through sequence (multiple EGIs sequentially)
   - Jump to transformation N (1 EGI)

2. **Terrain Traversal**:
   - View at different nesting depths
   - Collapse/expand specific cuts
   - Focus on subgraph region
   - Multi-scale rendering

3. **Sharing/Export**:
   - Export states M-N (subsequence)
   - Export current state only
   - Export critical section (e.g., moves 42-57)
   - Export entire history

**Access Pattern**: Random access to individual states, sequential access for replay, range queries for subsequences

---

### **Ergasterion Mode - Authoring**

1. **Editing Session**:
   - Load current state
   - Apply transformation → new state
   - Undo → load previous state
   - Redo → load next state
   - Save current state

2. **History Management**:
   - Create new branch
   - Merge branches
   - Compare states
   - Replay transformation sequence

**Access Pattern**: Sequential writes (append), random reads for undo/redo, branch operations

---

### **Agon Mode - Gameplay**

1. **Game Session**:
   - Load starting position
   - Apply move → new state
   - Validate move legality
   - Explore alternative moves (branching)
   - Evaluate current position (umpire)

2. **Game Analysis**:
   - Replay entire game
   - Compare alternative move sequences
   - Export game record
   - Annotate critical moves

**Access Pattern**: Branching writes, sequential replay, state comparison

---

## 🏗️ STORAGE STRATEGIES COMPARISON

### **Strategy 1: Full Snapshots** (Current Simple Approach)

**Structure**:
```json
{
  "states": {
    "state_001": {"egi": {...}},  // Full EGI
    "state_002": {"egi": {...}},  // Full EGI
    "state_003": {"egi": {...}}   // Full EGI
  }
}
```

**Pros**:
- ✅ Simple implementation
- ✅ Fast random access (O(1))
- ✅ No reconstruction needed
- ✅ Easy to understand/debug

**Cons**:
- ❌ Massive redundancy (90%+ duplicate data)
- ❌ Large file sizes (unusable for 500+ states)
- ❌ Slow to load entire history
- ❌ Inefficient for small changes

**Best For**: Small entities (<20 states)

---

### **Strategy 2: Delta Chain** (Maximum Compression)

**Structure**:
```json
{
  "base_state": {"egi": {...}},  // Full EGI
  "deltas": [
    {"add_vertex": {...}, "remove_edge": {...}},  // Delta 1→2
    {"add_cut": {...}},                           // Delta 2→3
    {"modify_relation": {...}}                    // Delta 3→4
  ]
}
```

**Pros**:
- ✅ Minimal storage (10-20% of full snapshots)
- ✅ Complete history with small footprint
- ✅ Natural for append operations
- ✅ Good for linear sequences

**Cons**:
- ❌ Slow reconstruction (O(n) to reach state N)
- ❌ No random access
- ❌ Complex with branching
- ❌ Fragile (corruption breaks chain)

**Best For**: Archival, read-once scenarios

---

### **Strategy 3: Hybrid Snapshots + Deltas** ⭐ **RECOMMENDED**

**Structure**:
```json
{
  "snapshots": {
    "state_000": {"egi": {...}},   // Full snapshot every 10 states
    "state_010": {"egi": {...}},
    "state_020": {"egi": {...}}
  },
  "deltas": {
    "state_001": {"from": "state_000", "delta": {...}},
    "state_002": {"from": "state_001", "delta": {...}},
    "state_011": {"from": "state_010", "delta": {...}}
  }
}
```

**Parameters**:
- **Snapshot interval**: Every N states (configurable, default: 10)
- **Max delta chain**: Never more than N deltas from snapshot

**Reconstruction Algorithm**:
```python
def get_state(state_id):
    if state_id in snapshots:
        return snapshots[state_id]  # O(1)
    
    # Find nearest prior snapshot
    snapshot_id = find_nearest_snapshot(state_id)
    egi = snapshots[snapshot_id]
    
    # Apply deltas sequentially
    for delta in deltas_between(snapshot_id, state_id):
        egi = apply_delta(egi, delta)  # O(k) where k ≤ N
    
    return egi
```

**Pros**:
- ✅ Balanced storage (30-40% of full snapshots)
- ✅ Fast access (O(N) worst case, typically O(5))
- ✅ Handles branching well
- ✅ Fault tolerant (snapshots provide recovery points)
- ✅ Configurable trade-off (storage vs speed)

**Cons**:
- ⚠️ More complex than full snapshots
- ⚠️ Requires delta computation logic

**Best For**: All entity sizes, production use ⭐

---

### **Strategy 4: Structural Indexing** (Advanced)

**Structure**:
```json
{
  "structure_index": {
    "vertices": {
      "v_001": {"appears_in": [0, 1, 2, 5, 7], "changes_at": [5]},
      "v_002": {"appears_in": [0, 1], "removed_at": 2}
    },
    "cuts": {...},
    "edges": {...}
  },
  "state_deltas": [...]  // Minimal deltas
}
```

**Pros**:
- ✅ Enables element-level queries ("where is vertex v_001 used?")
- ✅ Efficient subgraph extraction
- ✅ Supports multi-scale viewing
- ✅ Fast element tracking

**Cons**:
- ❌ Complex to maintain
- ❌ Index overhead
- ❌ Requires careful invalidation

**Best For**: Advanced queries, large universes of discourse

---

## 📊 RECOMMENDED ARCHITECTURE: TIERED STORAGE

### **Tier 1: Hot Cache (In-Memory)**

```python
class GraphEntityCache:
    current_state: StateSnapshot           # Always loaded
    recent_states: LRU[str, StateSnapshot] # Last N accessed (default: 5)
    layout_deltas: Optional[LayoutDeltas]  # Current aesthetic state
```

**Purpose**: Instant access to current + recent states

---

### **Tier 2: Working Set (Fast File Access)**

```
corpus/graphs/[name]/
├── [name].meta.json          # Metadata (always loaded)
├── [name].current.json       # Current state (always loaded)
├── [name].history.jsonl      # Streaming history format ⭐ NEW
└── [name].snapshots/         # Snapshot directory
    ├── snapshot_000.json
    ├── snapshot_010.json
    └── snapshot_020.json
```

**`.history.jsonl`** (JSON Lines format):
```
{"type":"state","state_id":"state_001","timestamp":"...","description":"..."}
{"type":"transformation","step_id":"trans_001","from":"state_001","to":"state_002","rule":"DC+","delta":{...}}
{"type":"state","state_id":"state_002","timestamp":"...","description":"..."}
{"type":"transformation","step_id":"trans_002","from":"state_002","to":"state_003","rule":"INS","delta":{...}}
```

**Advantages of JSONL**:
- ✅ Streaming read/write (append-only)
- ✅ Can read line-by-line (memory efficient)
- ✅ Easy to tail (follow growing file)
- ✅ Simple truncation (for undo/redo)
- ✅ Grep-able (search for specific states)

---

### **Tier 3: Archive (Compressed Storage)**

```
corpus/graphs/[name]/
└── archive/
    ├── states_000-099.json.gz    # Compressed batch
    ├── states_100-199.json.gz
    └── full_export.zip           # Complete export
```

**Purpose**: Long-term storage, full exports, backups

---

## 🎯 SPECIFIC SOLUTIONS FOR REQUIREMENTS

### **1. Scalability → Hybrid Strategy**

**Implementation**:
```python
class ScalableEntityStorage:
    snapshot_interval: int = 10  # Full snapshot every 10 states
    max_delta_chain: int = 10    # Never more than 10 deltas from snapshot
    
    def save_state(self, state: StateSnapshot, is_snapshot: bool = None):
        if is_snapshot is None:
            # Auto-determine: every Nth state
            is_snapshot = state.step_number % self.snapshot_interval == 0
        
        if is_snapshot:
            self._save_full_snapshot(state)
        else:
            delta = self._compute_delta(self.previous_state, state)
            self._append_delta(delta)
    
    def get_state(self, state_id: str) -> StateSnapshot:
        # Check cache first
        if state_id in self.cache:
            return self.cache[state_id]
        
        # Find nearest snapshot
        snapshot_id = self._find_nearest_snapshot(state_id)
        state = self._load_snapshot(snapshot_id)
        
        # Apply deltas
        for delta in self._get_deltas_range(snapshot_id, state_id):
            state = self._apply_delta(state, delta)
        
        # Cache result
        self.cache[state_id] = state
        return state
```

**Storage Metrics**:
- 100 states: ~3 MB (vs 30 MB full snapshots)
- 500 states: ~15 MB (vs 150 MB full snapshots)
- 1000 states: ~30 MB (vs 300 MB full snapshots)

**Access Speed**:
- Current state: O(1) - always cached
- Recent state: O(1) - in LRU cache
- Any state: O(N) where N ≤ snapshot_interval (typically ≤10)

---

### **2. Viewability → Lazy Loading + Structural Index**

**Multi-Scale Viewing**:
```python
class TerrainNavigator:
    def view_at_depth(self, egi: RelationalGraphWithCuts, max_depth: int):
        """Show graph with cuts collapsed beyond max_depth."""
        collapsed = self._collapse_cuts_beyond(egi, max_depth)
        return collapsed
    
    def focus_on_subgraph(self, egi: RelationalGraphWithCuts, 
                          center_elements: Set[ElementID],
                          radius: int):
        """Show only elements within radius of center."""
        subgraph = self._extract_subgraph(egi, center_elements, radius)
        return subgraph
```

**Structural Index** (for fast element tracking):
```json
{
  "element_index": {
    "v_socrates": {
      "first_appears": 0,
      "last_appears": 42,
      "modifications": [5, 12, 27],
      "parent_areas": ["sheet", "c_001", "c_002"]
    }
  }
}
```

**Usage**:
```python
# Find all states where vertex v_socrates appears
states = entity.find_states_with_element("v_socrates")

# Find when edge e_human was added
step = entity.find_element_creation("e_human")

# Get subgraph evolution (only relevant elements)
subgraph_history = entity.extract_subgraph_history(["v_socrates", "e_human"])
```

---

### **3. Sharability → Subsequence Extraction**

**Export Subsequence**:
```python
class ShareableExport:
    def export_subsequence(self, 
                          from_state: str, 
                          to_state: str,
                          format: str = "standalone") -> Path:
        """
        Export a subsequence as standalone entity.
        
        Formats:
        - "standalone": Self-contained .egi.json + .history.json
        - "citation": References to original entity
        - "delta": Minimal delta patch
        """
        
        if format == "standalone":
            # Extract states + transformations
            states = self.get_state_range(from_state, to_state)
            transformations = self.get_transformations_between(from_state, to_state)
            
            # Create new entity
            export = GraphEntity(
                entity_id=generate_id(),
                entity_type="historical",
                name=f"{self.name}_excerpt_{from_state}_{to_state}",
                current_state=states[-1],
                history=self._create_history_from_range(states, transformations)
            )
            
            return self._save_entity(export, "exports/")
```

**Use Cases**:
```python
# Share critical proof section (steps 42-57)
proof_section = entity.export_subsequence("state_042", "state_057")
# → standalone entity with 15 states + 14 transformations

# Share just the DC+ application
dc_plus_move = entity.export_transformation("trans_023")
# → minimal export: before state + transformation + after state

# Share current state as standalone EGI
current = entity.export_current_state()
# → single .egi.json file
```

---

### **4. Agon Complexity → Branch Management**

**Branching Structure**:
```python
class BranchManager:
    def create_branch(self, from_state: str, 
                     branch_name: str,
                     branch_type: HistoryBranchType):
        """Create exploration branch from state."""
        branch = HistoryBranch(
            branch_id=generate_id(),
            parent_state_id=from_state,
            branch_type=branch_type,
            created_timestamp=now(),
            description=branch_name
        )
        self.branches[branch.branch_id] = branch
        return branch
    
    def explore_alternative_move(self, state: str, move: str):
        """Try alternative move without affecting main line."""
        branch = self.create_branch(state, f"Alternative: {move}", 
                                   HistoryBranchType.EXPLORATION)
        # Apply move on branch
        result = self.apply_transformation(move, branch=branch.branch_id)
        return result
    
    def merge_branch(self, branch_id: str, into_branch: str = "main"):
        """Merge exploration into main line."""
        # Validation, conflict resolution, etc.
        pass
```

**Storage**:
```json
{
  "branches": {
    "main": {
      "branch_id": "main",
      "states": ["state_001", "state_002", ...],
      "current_state": "state_042"
    },
    "branch_alt1": {
      "branch_id": "branch_alt1",
      "parent_state": "state_015",  // Branches from state_015
      "states": ["state_015", "state_015a", "state_015b"],
      "current_state": "state_015b"
    }
  }
}
```

---

## 🗄️ DATABASE CONSIDERATION

### **Should We Use a Database?**

**File-Based (Current)** ✅ **RECOMMENDED FOR NOW**:
- ✅ Simple deployment (no DB setup)
- ✅ Version control friendly (Git)
- ✅ Easy backup/sharing (copy files)
- ✅ Portable (works anywhere)
- ✅ Transparent (human-readable JSON)
- ⚠️ Limited query capabilities
- ⚠️ No concurrent access (but not needed yet)

**Graph Database (Neo4j)**:
- ✅ Natural fit for branching structure
- ✅ Fast graph queries
- ✅ Built-in versioning support
- ❌ Complex deployment
- ❌ Requires server
- ❌ Overkill for current scale

**Document Database (MongoDB)**:
- ✅ Good for versioned documents
- ✅ Flexible schema
- ✅ Aggregation queries
- ❌ Requires server
- ❌ Not essential yet

**Recommendation**: 
- **Start with files** (sufficient for 100-500 state entities)
- **Add database later** if needed (1000+ states, collaborative editing)
- **Design abstraction layer** now (easy to swap later)

---

## 🎯 RECOMMENDED IMPLEMENTATION PLAN

### **Phase 1: Hybrid Storage (Immediate)** ⭐

**Tasks**:
1. Implement delta computation for EGI
2. Add snapshot logic (every Nth state)
3. Create JSONL streaming format
4. Implement lazy loading
5. Add LRU cache

**Files**:
- `entity_storage.py` - Hybrid storage implementation
- `egi_delta.py` - Delta computation
- `entity_cache.py` - LRU caching

**Result**: Handle 100-500 state entities efficiently

---

### **Phase 2: Structural Indexing (Near-term)**

**Tasks**:
1. Build element-level index
2. Implement element tracking queries
3. Add subgraph extraction
4. Support multi-scale viewing

**Files**:
- `structural_index.py` - Element indexing
- `subgraph_extractor.py` - Focused extraction
- `terrain_navigator.py` - Multi-scale viewing

**Result**: Fast element queries, subgraph focus

---

### **Phase 3: Advanced Features (Later)**

**Tasks**:
1. Branch management system
2. Subsequence export/import
3. Compression/archival
4. Collaborative editing (if needed)

**Files**:
- `branch_manager.py` - Branching logic
- `export_manager.py` - Sharing/export
- `archive_manager.py` - Long-term storage

**Result**: Full-featured system for complex reasoning

---

## 📊 PERFORMANCE TARGETS

### **Storage Efficiency**

| Entity Size | Full Snapshots | Hybrid (10:1) | Delta Chain |
|------------|---------------|---------------|-------------|
| 10 states | 300 KB | 120 KB (40%) | 50 KB (17%) |
| 100 states | 3 MB | 1.2 MB (40%) | 500 KB (17%) |
| 500 states | 15 MB | 6 MB (40%) | 2.5 MB (17%) |
| 1000 states | 30 MB | 12 MB (40%) | 5 MB (17%) |

**Target**: 30-40% of full snapshot size with hybrid approach

---

### **Access Speed**

| Operation | Target | Strategy |
|-----------|--------|----------|
| Get current state | <1ms | Always cached |
| Get recent state (last 5) | <5ms | LRU cache |
| Get any state | <50ms | Snapshot + deltas (≤10) |
| Sequential replay | 20 states/sec | Streaming JSONL |
| Random jump | <100ms | Snapshot lookup + delta |

---

### **Scalability Limits**

| Metric | Target | Strategy |
|--------|--------|----------|
| Max states per entity | 10,000 | Hybrid storage |
| Max branches | 100 | Branch manager |
| Max concurrent users | 10 | File locking (later: DB) |
| Max file size | 100 MB | Compression/archival |
| Load time (large entity) | <2 sec | Lazy loading |

---

## ✅ RECOMMENDATIONS

### **1. Start Simple, Scale Incrementally**

**Phase 1** (Now):
- Hybrid snapshots + deltas
- JSONL streaming format
- LRU caching
- **Target**: 100-500 states efficiently

**Phase 2** (Soon):
- Structural indexing
- Subsequence export
- Multi-scale viewing
- **Target**: 500-1000 states

**Phase 3** (Later):
- Advanced branching
- Collaborative features
- Database backend (if needed)
- **Target**: 1000+ states, multiple users

### **2. Design for Abstraction**

```python
class EntityStorageBackend(ABC):
    @abstractmethod
    def save_state(self, state: StateSnapshot): pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> StateSnapshot: pass
    
    @abstractmethod
    def get_state_range(self, from_id: str, to_id: str) -> List[StateSnapshot]: pass
```

This allows swapping file-based → database later without changing GUI code.

### **3. Optimize for Common Cases**

**80% of access**: Current + recent states → Cache these
**15% of access**: Sequential replay → JSONL streaming
**5% of access**: Random jumps → Hybrid snapshots

### **4. Plan for Growth**

Current needs: 10-100 states
Near-term: 100-500 states
Long-term: 500-1000+ states

**The hybrid approach scales to all these levels!**

---

## 🎓 SUMMARY

**Storage Strategy**: Hybrid snapshots + deltas ⭐
- Balance between space and speed
- Configurable (tune snapshot interval)
- Handles branching naturally

**File Format**: JSONL streaming ⭐
- Efficient append-only
- Memory-efficient reading
- Easy to debug/grep

**Access Pattern**: Lazy loading + LRU cache ⭐
- Only load what's needed
- Cache recent accesses
- Fast for common operations

**Scalability**: Designed for 1000+ states ⭐
- Current simple cases: instant
- Complex reasoning: still fast
- Universes of discourse: manageable

**The architecture supports all your requirements without premature complexity!**
