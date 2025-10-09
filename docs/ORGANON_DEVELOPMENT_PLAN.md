# Organon Development Plan: Synchronic & Diachronic Views

**Date**: 2025-10-09  
**Status**: Phase 3A - Complete Organon Mode  
**Goal**: Support both standalone EGI viewing AND historical transformation sequences

---

## 📊 Current State Assessment

### ✅ **Data Model - COMPLETE**

We have a **robust diachronic-synchronic model** already implemented:

#### **1. GraphEntity (`graph_entity.py` - 305 lines)**

**Synchronic Aspect** (current state):
```python
@dataclass
class GraphEntity:
    metadata: EntityMetadata
    current_egi: RelationalGraphWithCuts  # Current state
    history: Optional[EGITransformationHistory]  # Transformation sequence
```

**Key Properties**:
- ✅ `current_egi`: Current synchronic state
- ✅ `is_standalone`: Single EGI, no history
- ✅ `is_historical`: Has transformation sequence
- ✅ `get_current_egif()`: Linear form of current state
- ✅ `get_state(state_id)`: Access any historical state
- ✅ `get_transformation(step_id)`: Access transformation steps
- ✅ `get_state_range(from, to)`: Get sequence of states

**Entity Types**:
- `STANDALONE`: Single EGI snapshot (current corpus graphs)
- `HISTORICAL`: Sequence of states + transformations (what we need to support)

**Categories**:
- `PEIRCE`, `SCHOLARS`, `CANONICAL`: Literature examples
- `EPG`: Endoporeutic Game positions
- `THEOREM_PROVING`: Proof sequences
- `DOMAIN_MODELING`: Domain models
- `USER_CREATED`: User work
- `UNIVERSE`: Living universe of discourse

#### **2. EGITransformationHistory (`egi_transformation_history.py` - 485 lines)**

**Diachronic Aspect** (history tracking):
```python
@dataclass(frozen=True)
class StateSnapshot:
    state_id: str
    egi: RelationalGraphWithCuts
    timestamp: datetime
    step_number: int
    description: str
    linear_forms: Dict[str, str]  # EGIF, CGIF, CLIF
    diagram_metadata: Dict[str, Any]  # Layout info
    natural_language_summary: Optional[str]

@dataclass(frozen=True)
class TransformationStep:
    step_id: str
    rule_name: str  # DC+, DC-, INS, ERA, IT+, IT-
    from_state_id: str
    to_state_id: str
    timestamp: datetime
    description: str
    affected_elements: List[ElementID]
    transformation_result: TransformationResult
```

**Features**:
- ✅ Immutable state snapshots
- ✅ Transformation steps with formal rules
- ✅ Provenance tracking
- ✅ Branch support (linear, exploration, alternative)
- ✅ Rollback capabilities

#### **3. EntityStorageManager (`entity_storage.py` - 368 lines)**

**Efficient Storage**:
```python
class EntityStorageManager:
    # Hybrid snapshots + deltas
    # JSONL streaming format
    # LRU caching for states
    # Efficient for 1000+ states
```

**File Structure**:
```
corpus/graphs/
  entity_name/
    entity_name.meta.json         # Metadata
    entity_name.egi.json           # Current state
    entity_name.history.jsonl      # Transformation log
    snapshots/                     # Full snapshots every N states
      state_001.json
      state_010.json
      state_020.json
```

### ⏳ **GUI Components - PARTIAL**

#### **Current Organon (`gui_clean/organon/organon_mode.py` - 285 lines)**

**Implemented**:
- ✅ Corpus browser with entity selection
- ✅ Diagram canvas (SVG display via DiagramController)
- ✅ EGIF panel (shows current state)
- ✅ Load from corpus (uses EntityStorageManager)
- ✅ Load from file
- ✅ Export SVG
- ✅ Edit button (signals to Ergasterion)

**Missing**:
- ❌ **Metadata panel** - No display of entity properties
- ❌ **History timeline** - No view of transformation sequence
- ❌ **State navigation** - Can't browse through states
- ❌ **Transformation viewer** - Can't see rule applications
- ❌ **Linear form switcher** - Only shows EGIF, not CGIF/CLIF
- ❌ **Search/filter** - No corpus search
- ❌ **Themes** - No dark/light modes

---

## 🎯 Development Plan: Synchronic & Diachronic Views

### **Phase 3A.1: Metadata & Info Panel** (Week 1, Days 1-3)

#### **Goal**: Display entity metadata and statistics

#### **Component**: `MetadataPanel`

**Create**: `src/gui_clean/organon/metadata_panel.py`

```python
class MetadataPanel(QWidget):
    """
    Display entity metadata and properties.
    
    Shows:
    - Entity name, description
    - Category and tags
    - Authors and citation
    - Created/modified timestamps
    - Entity type (standalone vs historical)
    - Statistics (if historical):
      - Total states
      - Total transformations
      - Current state number
      - Complexity metrics
    """
    
    def __init__(self):
        # Create labeled fields for metadata
        # Use QFormLayout for clean presentation
        pass
    
    def update_metadata(self, entity: GraphEntity):
        """Update display with entity metadata."""
        metadata = entity.metadata
        
        # Display basic info
        self.name_label.setText(metadata.name)
        self.description_label.setText(metadata.description)
        self.category_label.setText(metadata.category.value)
        
        # Display timestamps
        self.created_label.setText(metadata.created.strftime("%Y-%m-%d"))
        self.modified_label.setText(metadata.last_modified.strftime("%Y-%m-%d"))
        
        # Display type-specific info
        if entity.is_standalone:
            self.type_label.setText("Standalone")
            self.history_group.hide()
        else:
            self.type_label.setText("Historical")
            self.history_group.show()
            self.states_label.setText(f"{metadata.total_states} states")
            self.transforms_label.setText(f"{metadata.total_transformations} transformations")
            self.current_label.setText(f"State {entity.history.current_state_number}")
        
        # Display authorship
        if metadata.authors:
            self.authors_label.setText(", ".join(metadata.authors))
        
        # Display tags
        if metadata.tags:
            self.tags_label.setText(", ".join(metadata.tags))
        
        # Display citation
        if metadata.source_citation:
            self.citation_label.setText(metadata.source_citation)
```

**Integration**:
```python
# In organon_mode.py
self.metadata_panel = MetadataPanel()
right_sidebar.addWidget(self.metadata_panel)

# When entity loaded:
def _on_load_from_corpus(self, entity_name: str):
    entity = storage.load_entity(entity_name)
    self.metadata_panel.update_metadata(entity)  # NEW
```

---

### **Phase 3A.2: History Timeline** (Week 1, Days 4-5)

#### **Goal**: Visual timeline of transformation sequence

#### **Component**: `HistoryTimeline`

**Create**: `src/gui_clean/organon/history_timeline.py`

```python
class HistoryTimeline(QWidget):
    """
    Timeline view of transformation history.
    
    Shows:
    - Linear sequence of states
    - Transformation steps between states
    - Current position indicator
    - Clickable states for navigation
    
    Emits:
    - state_selected(state_id) when user clicks a state
    """
    
    state_selected = Signal(str)  # Emits state_id
    
    def __init__(self):
        # Use QGraphicsView for custom timeline
        # OR QListWidget with custom items
        pass
    
    def update_history(self, entity: GraphEntity):
        """Update timeline with entity history."""
        if not entity.is_historical:
            self.setVisible(False)
            return
        
        self.setVisible(True)
        self.clear()
        
        history = entity.history
        
        # For each state in sequence:
        for i, state_id in enumerate(history.state_sequence):
            state = history.states[state_id]
            
            # Create timeline item
            item = TimelineItem(
                state_number=i+1,
                state_id=state_id,
                description=state.description,
                timestamp=state.timestamp,
                is_current=(state_id == history.current_state_id)
            )
            
            self.add_item(item)
            
            # Add transformation arrow if not last
            if i < len(history.state_sequence) - 1:
                next_state_id = history.state_sequence[i+1]
                step = self._find_step(state_id, next_state_id, history)
                if step:
                    arrow = TransformationArrow(
                        rule_name=step.rule_name,
                        description=step.description
                    )
                    self.add_arrow(arrow)
    
    def _find_step(self, from_id, to_id, history):
        """Find transformation step between states."""
        for step in history.steps.values():
            if step.from_state_id == from_id and step.to_state_id == to_id:
                return step
        return None
```

**Timeline Item Widget**:
```python
class TimelineItem(QWidget):
    """
    Single state in timeline.
    
    Visual:
    ┌─────────────────────┐
    │  [STATE 5]          │  ← Bold if current
    │  DC+ on vertex x    │  ← Description
    │  2025-10-09 14:30   │  ← Timestamp
    └─────────────────────┘
    """
    clicked = Signal(str)  # Emits state_id
    
    def __init__(self, state_number, state_id, description, timestamp, is_current):
        # Style based on is_current
        # Make clickable
        pass
```

**Integration**:
```python
# In organon_mode.py
self.history_timeline = HistoryTimeline()
self.history_timeline.state_selected.connect(self._on_state_selected)
history_panel.addWidget(self.history_timeline)

def _on_load_from_corpus(self, entity_name: str):
    entity = storage.load_entity(entity_name)
    self.history_timeline.update_history(entity)  # NEW
    self._current_entity = entity  # Store for navigation

def _on_state_selected(self, state_id: str):
    """Navigate to selected historical state."""
    if not self._current_entity or not self._current_entity.is_historical:
        return
    
    # Get state snapshot
    state = self._current_entity.get_state(state_id)
    
    # Load state's EGI into controller
    self.controller.load_egi(state.egi)
    
    # Render
    dto = self.controller.get_renderable_dto()
    self.canvas.display_dto(dto, state.egi)
    
    # Update EGIF
    egif = state.linear_forms.get("egif", generate_egif(state.egi))
    self.egif_text.setPlainText(egif)
    
    # Show state info
    self.statusBar().showMessage(
        f"Viewing State {state.step_number}: {state.description}",
        5000
    )
```

---

### **Phase 3A.3: Transformation Viewer** (Week 2, Days 1-2)

#### **Goal**: Show detailed transformation information

#### **Component**: `TransformationViewer`

**Create**: `src/gui_clean/organon/transformation_viewer.py`

```python
class TransformationViewer(QDialog):
    """
    Detailed view of a transformation step.
    
    Shows:
    - Rule name and description
    - Before/after states (side-by-side)
    - Affected elements (highlighted)
    - Transformation validation details
    - Natural language explanation
    """
    
    def __init__(self, step: TransformationStep, from_state: StateSnapshot, to_state: StateSnapshot):
        # Two-column layout: before | after
        # Highlight affected elements
        # Show rule description
        pass
```

**Usage**:
```python
# In history_timeline.py - double-click on arrow
def _on_arrow_double_clicked(self, step_id: str):
    step = self.history.steps[step_id]
    from_state = self.history.states[step.from_state_id]
    to_state = self.history.states[step.to_state_id]
    
    viewer = TransformationViewer(step, from_state, to_state)
    viewer.exec()
```

---

### **Phase 3A.4: Linear Form Switcher** (Week 2, Days 3-4)

#### **Goal**: View current state in multiple formats

#### **Component**: `LinearFormPanel`

**Update**: `src/gui_clean/organon/organon_mode.py`

```python
class LinearFormPanel(QWidget):
    """
    Tabbed panel for different linear representations.
    
    Tabs:
    - EGIF (Existential Graph Interchange Format)
    - CGIF (Conceptual Graph Interchange Format)
    - CLIF (Common Logic Interchange Format)
    """
    
    def __init__(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # EGIF tab
        self.egif_text = QTextEdit()
        self.egif_text.setReadOnly(True)
        self.egif_text.setFont("Courier New")
        self.tabs.addTab(self.egif_text, "EGIF")
        
        # CGIF tab
        self.cgif_text = QTextEdit()
        self.cgif_text.setReadOnly(True)
        self.cgif_text.setFont("Courier New")
        self.tabs.addTab(self.cgif_text, "CGIF")
        
        # CLIF tab
        self.clif_text = QTextEdit()
        self.clif_text.setReadOnly(True)
        self.clif_text.setFont("Courier New")
        self.tabs.addTab(self.clif_text, "CLIF")
        
        layout.addWidget(self.tabs)
    
    def update_from_entity(self, entity: GraphEntity):
        """Update all formats from entity."""
        # EGIF
        egif = entity.get_current_egif()
        self.egif_text.setPlainText(egif)
        
        # CGIF
        cgif = entity.get_current_cgif()
        if cgif:
            self.cgif_text.setPlainText(cgif)
        else:
            self.cgif_text.setPlainText("[CGIF not available]")
        
        # CLIF
        clif = entity.get_current_clif()
        if clif:
            self.clif_text.setPlainText(clif)
        else:
            self.clif_text.setPlainText("[CLIF not available]")
    
    def update_from_state(self, state: StateSnapshot):
        """Update from historical state snapshot."""
        # Use cached linear forms if available
        if "egif" in state.linear_forms:
            self.egif_text.setPlainText(state.linear_forms["egif"])
        
        if "cgif" in state.linear_forms:
            self.cgif_text.setPlainText(state.linear_forms["cgif"])
        else:
            # Generate on demand
            from cgif_generator_dau import generate_cgif
            try:
                cgif = generate_cgif(state.egi)
                self.cgif_text.setPlainText(cgif)
            except Exception as e:
                self.cgif_text.setPlainText(f"[CGIF error: {e}]")
        
        # Similar for CLIF
```

---

### **Phase 3A.5: State Navigation Controls** (Week 2, Day 5)

#### **Goal**: Easy navigation through history

#### **Component**: Navigation buttons

**Add to Organon UI**:
```python
class StateNavigationBar(QWidget):
    """
    Navigation controls for historical entities.
    
    Controls:
    - |< First
    - <  Previous
    - >  Next
    - >| Last
    - [State 5 of 23] indicator
    """
    
    prev_state = Signal()
    next_state = Signal()
    first_state = Signal()
    last_state = Signal()
    
    def __init__(self):
        layout = QHBoxLayout(self)
        
        self.first_btn = QPushButton("|<")
        self.first_btn.clicked.connect(self.first_state.emit)
        layout.addWidget(self.first_btn)
        
        self.prev_btn = QPushButton("<")
        self.prev_btn.clicked.connect(self.prev_state.emit)
        layout.addWidget(self.prev_btn)
        
        self.state_label = QLabel("State 1 of 1")
        layout.addWidget(self.state_label)
        
        self.next_btn = QPushButton(">")
        self.next_btn.clicked.connect(self.next_state.emit)
        layout.addWidget(self.next_btn)
        
        self.last_btn = QPushButton(">|")
        self.last_btn.clicked.connect(self.last_state.emit)
        layout.addWidget(self.last_btn)
    
    def update_state(self, current: int, total: int):
        """Update state indicator and button states."""
        self.state_label.setText(f"State {current} of {total}")
        
        self.first_btn.setEnabled(current > 1)
        self.prev_btn.setEnabled(current > 1)
        self.next_btn.setEnabled(current < total)
        self.last_btn.setEnabled(current < total)
```

---

## 🏗️ Updated Organon Architecture

### **New Layout**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Organon Mode - Exploration & Corpus Management                        │
├──────────┬──────────────────────────────────────────────┬───────────────┤
│  Corpus  │  Main Viewing Area                           │  Info Sidebar │
│  Browser │                                              │               │
│          │  ┌────────────────────────────────────────┐  │  ┌─────────┐  │
│  [Tree]  │  │  Action Bar                            │  │  │Metadata │  │
│  Peirce  │  │  [Load] [Export] [Edit] [Theme]        │  │  │Panel    │  │
│  Scholars│  └────────────────────────────────────────┘  │  │         │  │
│  Canon   │                                              │  │  Name   │  │
│  User    │  ┌────────────────────────────────────────┐  │  │  Type   │  │
│  EPG     │  │                                        │  │  │  Tags   │  │
│  Theorem │  │                                        │  │  │  Created│  │
│  Domain  │  │          Diagram Canvas                │  │  └─────────┘  │
│          │  │         (SVG Display)                  │  │               │
│  [Filter]│  │                                        │  │  ┌─────────┐  │
│  [Search]│  │                                        │  │  │Linear   │  │
│          │  │                                        │  │  │Forms    │  │
│          │  └────────────────────────────────────────┘  │  │         │  │
│          │                                              │  │ [EGIF]  │  │
│          │  ┌────────────────────────────────────────┐  │  │ [CGIF]  │  │
│          │  │  History Timeline (if historical)      │  │  │ [CLIF]  │  │
│          │  │  [S1]──DC+──>[S2]──INS──>[S3]──...     │  │  │         │  │
│          │  └────────────────────────────────────────┘  │  └─────────┘  │
│          │                                              │               │
│          │  [|< < State 5 of 23 > >|]                   │               │
└──────────┴──────────────────────────────────────────────┴───────────────┘
```

### **File Structure**:

```
src/gui_clean/organon/
  __init__.py
  organon_mode.py              # Main mode widget (updated)
  corpus_browser.py            # Corpus tree browser (existing)
  metadata_panel.py            # NEW - Entity metadata display
  history_timeline.py          # NEW - Transformation timeline
  transformation_viewer.py     # NEW - Detailed transformation view
  linear_form_panel.py         # NEW - Multi-format linear form tabs
  state_navigation.py          # NEW - Navigation controls
```

---

## 📋 Implementation Checklist

### **Week 1: Metadata & History Basics**
- [ ] Day 1-2: Create `MetadataPanel` component
- [ ] Day 2-3: Integrate metadata panel into Organon
- [ ] Day 3: Test with both standalone and historical entities
- [ ] Day 4: Create `HistoryTimeline` component
- [ ] Day 5: Integrate timeline with state navigation

### **Week 2: Detailed Views & Navigation**
- [ ] Day 1: Create `TransformationViewer` dialog
- [ ] Day 2: Connect viewer to timeline clicks
- [ ] Day 3: Create `LinearFormPanel` with tabs
- [ ] Day 4: Integrate CGIF/CLIF generation
- [ ] Day 5: Create `StateNavigationBar` with keyboard shortcuts

### **Week 3: Polish & Testing**
- [ ] Day 1: Theme support (light/dark)
- [ ] Day 2: Search & filter in corpus browser
- [ ] Day 3: Export options (PDF, multiple formats)
- [ ] Day 4: Comprehensive GUI tests
- [ ] Day 5: User acceptance testing & documentation

---

## 🧪 Testing Strategy

### **Test Cases**:

1. **Standalone Entities**:
   - Load standalone EGI
   - View metadata (no history)
   - Export SVG
   - View in all linear formats

2. **Historical Entities**:
   - Load entity with 10+ states
   - Navigate through history
   - View transformation details
   - Verify state snapshots accurate

3. **Edge Cases**:
   - Empty corpus
   - Single-state historical entity
   - Very long history (100+ states)
   - Branching histories
   - Corrupted entity files

### **Integration Tests**:
```python
def test_organon_historical_entity():
    """Test Organon with historical entity."""
    # Create test entity with 5 states
    entity = create_test_historical_entity(num_states=5)
    
    # Load in Organon
    organon.load_entity(entity)
    
    # Verify metadata displayed
    assert "Historical" in organon.metadata_panel.text()
    assert "5 states" in organon.metadata_panel.text()
    
    # Verify timeline shown
    assert organon.history_timeline.isVisible()
    assert len(organon.history_timeline.items) == 5
    
    # Navigate to state 3
    organon.history_timeline.select_state("state_003")
    
    # Verify diagram updated
    assert organon.canvas.current_state_id == "state_003"
```

---

## 🎯 Success Criteria

### **Synchronic View** (current state):
- ✅ Display current EGI diagram
- ✅ Show EGIF, CGIF, CLIF linear forms
- ✅ Display entity metadata
- ✅ Export current state

### **Diachronic View** (history):
- ✅ Display transformation timeline
- ✅ Navigate between states (prev/next/jump)
- ✅ View transformation details (rule, elements)
- ✅ Show state snapshots with annotations
- ✅ Export history sequence

### **User Experience**:
- ✅ Smooth transitions between states
- ✅ Clear indication of current vs historical view
- ✅ Keyboard shortcuts for navigation
- ✅ Responsive with 100+ state histories

---

## 🚀 Next Immediate Step

**Create `MetadataPanel` component** (Days 1-2):

1. Create file: `src/gui_clean/organon/metadata_panel.py`
2. Implement basic metadata display
3. Integrate into `organon_mode.py`
4. Test with existing corpus entities

**Estimated time**: 1-2 days
**Files to modify**: 2 (new component + integration)
**Lines of code**: ~200-300

Ready to start implementing?
