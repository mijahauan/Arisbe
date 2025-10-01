# Diachronic-Synchronic Data Model Analysis

**Date**: 2025-10-01  
**Purpose**: Assess existing history/transformation infrastructure and align with vision of unified diachronic/synchronic model

---

## 🎯 VISION: "MOVING PICTURE OF THOUGHT"

### **Core Concept**

The fundamental entity in Arisbe should be:

**A diachronic sequence of synchronic EGI states, linked by valid transformations**

This represents Peirce's "moving picture of thought" - a coherent, dynamically developing universe of discourse.

### **Two Types of Graphs**

1. **Stand-Alone EGIs**: Static snapshots
   - From literature (Peirce, scholars)
   - User proposals for inclusion
   - Test cases, examples
   - Stored as: `.egi.json` files

2. **Universe of Discourse**: Living, evolving entities
   - Diachronic sequence of states
   - Linked by transformation history
   - Complete provenance
   - Stored as: `.history.json` + state snapshots

---

## 📊 CURRENT INFRASTRUCTURE ANALYSIS

### **1. EGI Transformation History** (`egi_transformation_history.py`)

**Key Components**:

```python
@dataclass(frozen=True)
class StateSnapshot:
    """Immutable snapshot of an EGI state"""
    state_id: str
    egi: RelationalGraphWithCuts
    timestamp: datetime
    step_number: int
    description: str
    
    # Semantic context
    domain_model: Optional[Any]
    active_domain_contexts: Set[str]
    
    # Multiple representations
    linear_forms: Dict[str, str]  # EGIF, CLIF, CGIF
    diagram_metadata: Dict[str, Any]  # Layout info
    
    # Annotations
    natural_language_summary: Optional[str]
```

**✅ Strengths**:
- Captures complete EGI state at each step
- Immutable snapshots (aligns with EGI immutability)
- Multiple representations (EGIF, diagram metadata)
- Semantic annotations
- Hierarchical index required

**❌ Gaps**:
- No direct link to corpus storage
- Domain model integration incomplete
- Missing layout deltas (aesthetic adjustments)

```python
@dataclass(frozen=True)
class TransformationStep:
    """Record of single transformation"""
    step_id: str
    rule_name: str
    from_state_id: str
    to_state_id: str
    context: TransformationContext
    result: TransformationResult
    timestamp: datetime
    status: TransformationStatus
    
    # Rich context
    logical_provenance: Optional[LogicalProvenance]
    affected_domain_contexts: Set[str]
    natural_language_description: Optional[str]
    
    # Collaboration
    author_id: Optional[str]
    reviewer_ids: Set[str]
    approval_status: Optional[str]
```

**✅ Strengths**:
- Links states via transformations
- Logical provenance (rule citations)
- Natural language descriptions
- Collaboration support
- Validation status

**❌ Gaps**:
- No aesthetic delta tracking (LayoutDeltas)
- No connection to DiagramController state

```python
class EGITransformationHistory:
    """Complete history with branching"""
    - states: Dict[str, StateSnapshot]
    - steps: Dict[str, TransformationStep]
    - branches: Dict[str, HistoryBranch]
    - current_state_id: str
```

**✅ Strengths**:
- Full graph structure (states + edges = transformation steps)
- Branching support (exploration, alternatives)
- Navigation (rollback, replay)

**❌ Gaps**:
- Not integrated with DiagramController
- No LayoutDeltas persistence
- No corpus linkage

---

### **2. History Persistence** (`history_persistence.py`)

**Key Capabilities**:

```python
class HistoryPersistenceManager:
    - save_history_json()      # Primary storage
    - load_history_json()      # Load complete history
    - save_history_yaml()      # Human-readable
    - save_compressed()        # Large histories
    - export_proof()           # LaTeX, Markdown
```

**✅ Strengths**:
- Multiple formats (JSON, YAML, compressed)
- Proof export (academic papers)
- Complete serialization

**❌ Gaps**:
- No corpus integration
- Separate from `.egi.json` files
- No sync with DiagramController state

---

### **3. Efficient Historical Storage** (`efficient_historical_storage.py`)

**Key Capabilities**:

```python
class EfficientHistoricalStorage:
    - Delta compression (only store changes)
    - Structural diffs
    - Fast replay
```

**✅ Strengths**:
- Storage efficiency
- Delta compression
- Fast state reconstruction

**❌ Gaps**:
- Not used by current system
- No integration with transformation history
- Missing LayoutDeltas

---

### **4. Interactive Transformer with History** (`interactive_transformer_with_history.py`)

**Key Capabilities**:

```python
class InteractiveTransformerWithHistory:
    - create_new_session()
    - apply_transformation()
    - undo/redo
    - auto-save
    - session management
```

**✅ Strengths**:
- Session-based workflow
- Auto-save
- Undo/redo
- EGIF integration

**❌ Gaps**:
- No DiagramController integration
- No LayoutDeltas
- No corpus integration
- EGIF-focused (not EGI-first)

---

## 🔍 KEY GAPS IN CURRENT INFRASTRUCTURE

### **1. No Unified Diachronic-Synchronic Model**

**Current**: Two separate worlds
- **Synchronic**: `.egi.json` files (static)
- **Diachronic**: `.history.json` files (transformations)
- **No connection between them**

**Needed**: Unified model
- Single entity represents both aspects
- Corpus stores both static AND historical graphs
- GUI can switch between views seamlessly

---

### **2. No DiagramController Integration**

**Current**: History system doesn't know about DiagramController
- No LayoutDeltas in history
- No aesthetic adjustment tracking
- Transformations lose user layout preferences

**Needed**: DiagramController as history source
- Every transformation recorded with LayoutDeltas
- User aesthetics preserved across history
- Replay includes layout evolution

---

### **3. No Corpus Integration**

**Current**: History files separate from corpus
- `.egi.json` in `corpus/graphs/`
- `.history.json` in `histories/`
- No linkage

**Needed**: History as first-class corpus citizen
- `corpus/graphs/[name]/[name].history.json`
- Stand-alone EGIs can become historical
- Historical graphs can export current state

---

### **4. No Layout History**

**Current**: Only logical transformations tracked
- LayoutDeltas not persisted
- Aesthetic adjustments lost
- Replay doesn't reproduce visual evolution

**Needed**: Complete visual+logical history
- LayoutDeltas in TransformationStep
- Aesthetic adjustments as "micro-transformations"
- Full replay of visual development

---

## 🏗️ PROPOSED UNIFIED MODEL

### **Data Model**

```python
@dataclass
class GraphEntity:
    """
    Unified entity representing both synchronic and diachronic aspects.
    
    Can be:
    1. Stand-alone EGI (single state, no history)
    2. Historical sequence (multiple states + transformations)
    """
    
    entity_id: str
    entity_type: Literal["standalone", "historical"]
    
    # Metadata
    name: str
    description: str
    category: str  # "peirce", "scholars", "canonical", "epg", "universe"
    created: datetime
    last_modified: datetime
    
    # Synchronic aspect (current state)
    current_state: StateSnapshot
    current_egi: RelationalGraphWithCuts
    current_layout_deltas: Optional[LayoutDeltas]
    
    # Diachronic aspect (for historical entities)
    history: Optional[EGITransformationHistory]
    
    # Corpus location
    corpus_path: Path  # corpus/graphs/[name]/
    
    # Multiple representations
    egif: str
    cgif: Optional[str]
    clif: Optional[str]
    
    def is_standalone(self) -> bool:
        return self.history is None or len(self.history.states) <= 1
    
    def is_historical(self) -> bool:
        return self.history is not None and len(self.history.states) > 1
    
    def promote_to_historical(self):
        """Convert standalone to historical by creating initial snapshot."""
        pass
    
    def export_current_state(self) -> Path:
        """Export current state as standalone .egi.json"""
        pass
```

### **Storage Structure**

```
corpus/graphs/[graph_name]/
├── [graph_name].meta.json          # Entity metadata
├── [graph_name].egi.json           # Current state (always present)
├── [graph_name].history.json       # Transformation history (if historical)
├── [graph_name].layout.json        # Current LayoutDeltas (if modified)
├── EGDF/
│   ├── state_001.egdf              # Historical layouts
│   ├── state_002.egdf
│   └── current.egdf
└── EXPORTS/
    ├── current.svg
    ├── proof.tex
    └── timeline.png
```

**`.meta.json`**:
```json
{
  "entity_id": "uuid",
  "entity_type": "historical",
  "name": "Socrates Mortality Proof",
  "description": "Derivation of Socrates' mortality",
  "category": "theorem_proving",
  "created": "2025-10-01T...",
  "last_modified": "2025-10-01T...",
  "current_state_id": "state_042",
  "total_states": 42,
  "total_transformations": 41,
  "authors": ["user_id"],
  "tags": ["syllogism", "classical_logic"]
}
```

**`.egi.json`**: Current EGI state (standard format)

**`.history.json`**: Complete transformation history
```json
{
  "history_id": "uuid",
  "entity_id": "uuid",
  "states": {
    "state_001": {
      "state_id": "state_001",
      "egi": {...},  // Full EGI or delta reference
      "timestamp": "...",
      "step_number": 1,
      "description": "Initial state",
      "linear_forms": {"egif": "...", "clif": "..."},
      "layout_deltas": {...}  // NEW: Layout state
    },
    ...
  },
  "transformations": {
    "trans_001": {
      "step_id": "trans_001",
      "rule_name": "DC+",
      "from_state_id": "state_001",
      "to_state_id": "state_002",
      "context": {...},
      "result": {...},
      "logical_provenance": {...},
      "layout_delta_changes": {...},  // NEW: Layout changes
      "natural_language": "Added double cut around..."
    },
    ...
  },
  "branches": {...},
  "current_state_id": "state_042"
}
```

**`.layout.json`**: Current layout deltas (DiagramController state)
```json
{
  "layout_deltas": {
    "v_id": {
      "delta_type": "vertex_position",
      "new_position": [100.0, 200.0]
    },
    ...
  },
  "style": "dau_compliant"
}
```

---

## 🔄 INTEGRATION WITH GUI

### **Organon Mode**

**Load Entity**:
```python
# Load from corpus
entity = corpus_manager.load_entity("socrates_proof")

# Display current state
controller.load_egi(entity.current_egi)
if entity.current_layout_deltas:
    controller.apply_layout_deltas(entity.current_layout_deltas)
dto = controller.get_renderable_dto()
canvas.display_dto(dto, entity.current_egi)

# Show history timeline (if historical)
if entity.is_historical():
    timeline_widget.display_history(entity.history)
    
# Navigate history
def view_state(state_id):
    snapshot = entity.history.get_state(state_id)
    controller.load_egi(snapshot.egi)
    # Apply historical layout deltas
    canvas.display_dto(controller.get_renderable_dto())
```

**Views**:
1. **Current State** (synchronic) - What it is now
2. **History Timeline** (diachronic) - How it evolved
3. **Transformation Sequence** - Step-by-step derivation
4. **Branching Tree** - Alternative proof paths

---

### **Ergasterion Mode**

**Start Session**:
```python
# Load entity for editing
entity = corpus_manager.load_entity("my_proof")
session = ergasterion.start_session(entity)

# Apply transformation
success = session.apply_transformation("DC+", selection, area)
# Automatically creates new state in history
# Records LayoutDeltas from DiagramController

# User adjusts layout
session.update_position(vertex_id, new_pos)
# Records as aesthetic micro-transformation

# Save
corpus_manager.save_entity(entity)
# Saves both .egi.json and .history.json
```

**Features**:
- Every transformation adds to history
- Layout adjustments tracked
- Full undo/redo through history
- Auto-save current state

---

### **Agon Mode**

**Game Session**:
```python
# Start game from hypothesis
entity = corpus_manager.load_entity("hypothesis_01")
game = agon.start_game(entity)

# Each move creates new state
game.make_move("INS", selection, area)
# New StateSnapshot with move annotation

# Umpire evaluation
outcome = game.evaluate_current_state()
if outcome == "contingent":
    # Archive as valid proof
    corpus_manager.save_entity(entity, category="proofs")
```

**Features**:
- Complete game history
- Move-by-move replay
- Alternative move exploration (branching)
- Final state export

---

## 🎯 IMPLEMENTATION ROADMAP

### **Phase 1: Data Model Unification**

**Tasks**:
1. Create `GraphEntity` class
2. Extend `StateSnapshot` to include LayoutDeltas
3. Extend `TransformationStep` to include layout changes
4. Create unified corpus manager

**Files to Create/Modify**:
- `graph_entity.py` - NEW: Unified entity model
- `egi_transformation_history.py` - ADD LayoutDeltas support
- `corpus_manager_unified.py` - NEW: Handles both types

---

### **Phase 2: DiagramController Integration**

**Tasks**:
1. DiagramController emits history events
2. LayoutDeltas captured in transformations
3. Aesthetic adjustments tracked
4. State snapshots include full visual state

**Files to Create/Modify**:
- `diagram_controller.py` - ADD history event emission
- `layout_history.py` - NEW: Layout evolution tracking

---

### **Phase 3: Corpus Integration**

**Tasks**:
1. New corpus structure (.meta.json, .history.json, .layout.json)
2. Migration tool for existing .egi.json files
3. Import/export for historical entities
4. Corpus browser shows both types

**Files to Create/Modify**:
- `corpus_structure.py` - NEW: Storage format
- `migration_tool.py` - NEW: Migrate existing corpus
- `corpus_browser.py` - NEW: GUI component

---

### **Phase 4: GUI Integration**

**Tasks**:
1. **Organon**: Timeline view, history navigation
2. **Ergasterion**: Session-based editing with history
3. **Agon**: Game moves as transformations

**Files to Create/Modify**:
- `organon_mode.py` - ADD timeline view
- `ergasterion_mode.py` - ADD session management
- `agon_mode.py` - ADD game history

---

## 📋 IMMEDIATE NEXT STEPS

### **For Current GUI Work**

1. **Decide on entity model**:
   - Keep standalone EGIs simple (.egi.json only)
   - Add optional .history.json for evolved graphs
   - GraphEntity wraps both

2. **Organon MVP**:
   - Load standalone EGIs (current)
   - Display history timeline (if .history.json exists)
   - View historical states (if available)
   - Export current state

3. **Corpus Browser**:
   - Show entity type (standalone vs historical)
   - Display metadata (steps, transformations)
   - Filter by category
   - Preview current state

4. **Later Phases**:
   - Ergasterion creates/extends histories
   - Agon uses histories for game replay
   - Full diachronic-synchronic integration

---

## 🎓 CONCEPTUAL ALIGNMENT

### **Peirce's Vision**

> "The diagram itself, in its individuality, is a **moving picture of thought**."

**Our Implementation**:
- **Synchronic**: Each EGI state is a snapshot
- **Diachronic**: Transformation sequence is the motion
- **Together**: Complete "moving picture"

### **Dau's Formalism**

- **Static EGI**: Relational Graph with Cuts (synchronic)
- **Transformations**: Formal rules preserving logical equivalence
- **History**: Sequence of valid transformations (diachronic)

### **Arisbe's Synthesis**

```
GraphEntity = Synchronic State + Diachronic History
            = Current EGI + Transformation Sequence
            = "What it is" + "How it became"
            = Snapshot + Evolution
            = Being + Becoming
```

---

## ✅ RECOMMENDATIONS

### **1. Adopt Unified Model Gradually**

**Phase 1** (Current GUI work):
- Simple: Load .egi.json files
- Display current state
- Optional: Show .history.json if exists

**Phase 2** (Ergasterion):
- Create histories as users edit
- Save transformations automatically
- Full undo/redo

**Phase 3** (Full Integration):
- All entities support both aspects
- Seamless synchronic/diachronic views
- Complete "moving picture"

### **2. Extend Existing Infrastructure**

**Don't rebuild**, extend:
- ✅ `egi_transformation_history.py` - ADD LayoutDeltas
- ✅ `history_persistence.py` - ADD corpus integration
- ✅ NEW `graph_entity.py` - Wrap both aspects
- ✅ NEW `corpus_manager_unified.py` - Handle both types

### **3. Make History Optional**

- Standalone EGIs remain simple
- History added on demand
- User promotes standalone → historical
- Backward compatible

### **4. DiagramController as History Source**

- Controller emits events
- History system listens
- Automatic state snapshots
- No manual history management

---

## 🎯 SUMMARY

**Current State**:
- ✅ Strong history infrastructure exists
- ✅ Transformation tracking comprehensive
- ❌ Not integrated with DiagramController
- ❌ Separate from corpus
- ❌ No layout history

**Vision**:
- GraphEntity = Synchronic + Diachronic
- Corpus stores both static and historical
- GUI seamlessly switches views
- Complete "moving picture of thought"

**Path Forward**:
1. Start simple (load .egi.json)
2. Add optional history (.history.json)
3. Integrate DiagramController
4. Full diachronic-synchronic unity

**The existing infrastructure is solid - we just need to connect it to the corpus and DiagramController!**
