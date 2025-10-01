# GUI Implementation Planning: Organon, Ergasterion, Agon

**Date**: 2025-10-01  
**Status**: Planning Phase  
**Foundation**: DiagramController + Layout Engine (100% tested, production-ready)

---

## 📋 EXECUTIVE SUMMARY

We have three major functional areas to implement:
1. **Organon**: Exploration & corpus management (read-only visualization)
2. **Ergasterion**: Composition, editing, and practice (interactive authoring)
3. **Agon**: Formal reasoning & Endoporeutic Game (gameplay/validation)

**Key Question**: Should we build sequentially or in concert?

**Recommendation**: **Incremental, layered approach** - Build core GUI infrastructure first, then add capabilities module-by-module with continuous integration testing.

---

## 🎯 THE THREE AREAS: DETAILED BREAKDOWN

### **1. ORGANON** (Exploration & Corpus Management)

**Purpose**: Navigate, examine, and organize existing knowledge structures

**Primary User Workflows**:
1. **Browse Corpus**: Navigate tree of stored EGIs
2. **View Diagram**: Display read-only EGI visualization
3. **Inspect Properties**: View metadata, EGIF, transformations
4. **Export Diagram**: Generate SVG, PDF, LaTeX outputs
5. **Search & Filter**: Find EGIs by content or metadata
6. **View History**: Explore transformation timeline

**Core Components Needed**:
```
├── Corpus Browser (Tree/List view)
├── Diagram Viewer (Read-only canvas)
├── Metadata Panel (Properties display)
├── Export Dialog (Format selection)
├── Search Panel (Query interface)
└── History Timeline (Transformation sequence)
```

**DiagramController Integration**:
- `load_egi(egi)` - Load graph for viewing
- `get_renderable_dto()` - Get layout for display
- **No editing** - Purely read-only

**Complexity**: 🟢 **LOW** - Mostly display logic, no state mutations

**Dependencies**: SVG renderer, corpus storage system

---

### **2. ERGASTERION** (Composition, Editing, Practice)

**Purpose**: Create, modify, and practice with EGI structures

**Primary User Workflows**:
1. **Create New Diagram**: Start with empty graph or template
2. **Add Elements**: Drag-and-drop vertices, edges, cuts
3. **Reposition Elements**: Aesthetic adjustments with validation
4. **Apply Transformations**: Practice with formal rules (DC+/-, INS/ERA, IT+/-)
5. **Undo/Redo**: Navigate edit history
6. **Style Selection**: Choose visual theme
7. **Save to Corpus**: Persist work to Organon

**Core Components Needed**:
```
├── Interactive Canvas (Edit-enabled diagram display)
├── Element Palette (Drag-and-drop library)
├── Transformation Toolbar (Rule selection)
├── Properties Panel (Element configuration)
├── Style Selector (Theme chooser)
├── Undo/Redo Controls (History navigation)
└── Save Dialog (Corpus integration)
```

**DiagramController Integration**:
- `load_egi(egi)` - Load for editing
- `get_renderable_dto()` - Get current layout
- `update_element_position(id, pos)` - Move elements
- `apply_formal_rule(rule, selection, area)` - Transform
- **CommandExecutor** - Full undo/redo support

**Complexity**: 🟡 **MEDIUM** - Interactive editing, validation, state management

**Dependencies**: 
- All Organon components (for display)
- Command pattern implementation (already done)
- Validation system (already in DiagramController)

---

### **3. AGON** (Formal Reasoning & Endoporeutic Game)

**Purpose**: Conduct rigorous logical reasoning through gameplay

**Primary User Workflows**:
1. **Start Game**: Initialize with hypothesis EGI
2. **Make Moves**: Apply transformation rules as "moves"
3. **Validate Moves**: Check rule compliance
4. **Track Game State**: History of moves and branches
5. **Umpire Decision**: Contradiction/Tautology/Contingent detection
6. **Manage Hypotheses**: Multiple concurrent reasoning contexts
7. **Complete Inquiry Cycle**: Integration with Organon/Ergasterion

**Core Components Needed**:
```
├── Game Board (Specialized interactive canvas)
├── Move Selector (Rule-based transformation)
├── Game History (Move timeline with branches)
├── Umpire Panel (Automated analysis)
├── Hypothesis Manager (Multi-context workspace)
├── Inquiry Tracker (Cycle progress)
└── Game Rules Reference (Help system)
```

**DiagramController Integration**:
- Everything from Ergasterion +
- Game state management
- Move validation (stricter than Ergasterion)
- Branch management
- Outcome detection

**Complexity**: 🔴 **HIGH** - Game logic, outcome detection, multi-context management

**Dependencies**:
- All Ergasterion capabilities
- Game engine logic (not yet implemented)
- Umpire function (semantic analysis)
- Hypothesis comparison system

---

## 🏗️ ARCHITECTURAL CONSIDERATIONS

### **User-Space Separation: Three Approaches**

#### **Option A: Tabbed Interface** (Simplest)
```
[Organon Tab] [Ergasterion Tab] [Agon Tab]
```
**Pros**: Simple, clear separation, easy to implement  
**Cons**: No simultaneous view, switching overhead

#### **Option B: Mode-Based Single Window** (Medium)
```
Top: [Organon Mode | Ergasterion Mode | Agon Mode] ← Radio buttons
Bottom: Same canvas, different controls/behaviors per mode
```
**Pros**: Unified canvas, smooth transitions  
**Cons**: Mode confusion, complex state management

#### **Option C: Separate Applications** (Most Complex)
```
Arisbe Organon (standalone app)
Arisbe Ergasterion (standalone app)
Arisbe Agon (standalone app)
+ IPC for data exchange
```
**Pros**: Complete separation, specialized UX per app  
**Cons**: Complex communication, harder to integrate

**Recommendation**: **Option B (Mode-Based)** - Best balance of separation and integration

---

### **Shared vs. Specialized Components**

#### **Shared Infrastructure** (Used by All)
- DiagramController
- LayoutDTO rendering
- SVG generation
- EGIF display
- Metadata viewing
- Style system

#### **Specialized Components**

**Organon-Specific**:
- Corpus browser/search
- History timeline
- Export wizard
- Read-only canvas

**Ergasterion-Specific**:
- Element palette
- Drag-and-drop editing
- Position validation
- Practice tutorials

**Agon-Specific**:
- Game state manager
- Move validator
- Umpire function
- Hypothesis comparator

---

## 📐 IMPLEMENTATION STRATEGY

### **Recommended Approach: Incremental Layering**

**Phase 1: Core GUI Foundation** (Weeks 1-2)
```
Goal: Get a working window with diagram display

Components:
├── Main Application Window
├── Basic DiagramView (SVG rendering)
├── Mode Selector (Organon/Ergasterion/Agon)
├── EGIF Display Panel
├── Basic Menu System
└── Load/Save Infrastructure

Outcome: Can load EGI and see it rendered
```

**Phase 2: Organon Implementation** (Weeks 3-4)
```
Goal: Full read-only exploration

Add:
├── Corpus Browser
├── Navigation controls (pan/zoom)
├── Metadata display
├── Search functionality
├── Export dialog
└── History viewer

Outcome: Complete exploration environment
```

**Phase 3: Ergasterion Foundation** (Weeks 5-7)
```
Goal: Basic interactive editing

Add:
├── Mouse interaction (click/drag)
├── Element repositioning
├── Position validation
├── Undo/Redo UI
├── Element palette (basic)
└── Save workflow

Outcome: Can move elements and save changes
```

**Phase 4: Ergasterion Transformations** (Weeks 8-10)
```
Goal: Full transformation practice

Add:
├── Transformation toolbar
├── Selection system
├── Rule application UI
├── Visual feedback
├── Practice mode
└── Tutorial system

Outcome: Complete workshop environment
```

**Phase 5: Agon Foundation** (Weeks 11-14)
```
Goal: Basic game functionality

Add:
├── Game initialization
├── Move validation
├── Game history
├── Basic umpire
└── Single-hypothesis workflow

Outcome: Can play basic Endoporeutic Game
```

**Phase 6: Agon Advanced** (Weeks 15-18)
```
Goal: Full reasoning environment

Add:
├── Multi-hypothesis management
├── Advanced umpire (semantic analysis)
├── Inquiry cycle integration
├── Hypothesis comparison
└── Complete game features

Outcome: Full formal reasoning system
```

---

## 🔍 KEY QUESTIONS TO RESOLVE

### **1. GUI Framework Choice**
**Question**: What GUI framework should we use?

**Options**:
- **Qt (PyQt6)**: Full-featured, professional, good canvas support
- **Tkinter**: Built-in, simpler, limited canvas features
- **Web-based (Electron)**: Modern, good for SVG, deployment friendly
- **wxPython**: Cross-platform, native look

**Recommendation**: **PyQt6** - Best canvas support, proven for diagram editors

---

### **2. Build Order**
**Question**: Sequential (Organon → Ergasterion → Agon) or in concert?

**Sequential Pros**:
- ✅ Clear milestones
- ✅ Each module fully complete before next
- ✅ Easier testing

**Sequential Cons**:
- ❌ Long wait for full functionality
- ❌ Late integration issues
- ❌ User can't benefit from partial work

**Concurrent Pros**:
- ✅ All modules progress together
- ✅ Continuous integration testing
- ✅ Early detection of architectural issues

**Concurrent Cons**:
- ❌ More complex coordination
- ❌ Partial implementations everywhere
- ❌ Harder to track progress

**Recommendation**: **Hybrid - Layered Sequential**
- Build core infrastructure first (used by all)
- Then Organon (simplest, establishes patterns)
- Then Ergasterion (builds on Organon)
- Finally Agon (builds on Ergasterion)
- **Continuous integration** at each layer

---

### **3. User Experience Flow**
**Question**: How should users navigate between modes?

**Typical User Journeys**:

**Journey A: Explorer**
```
Organon (browse) → Organon (view) → Organon (export)
```

**Journey B: Learner**
```
Organon (load example) → Ergasterion (practice) → Organon (save result)
```

**Journey C: Researcher**
```
Ergasterion (create hypothesis) → Agon (test) → Organon (archive/refine)
```

**Journey D: Expert**
```
Agon (multiple hypotheses) → Agon (compare) → Organon (export paper)
```

**Design Implication**: Smooth transitions between modes are critical

**Recommendation**: 
- Mode switcher always visible
- "Open in [Mode]" buttons in each mode
- Preserve state during mode switches
- Clear indicators of current mode

---

## 🎨 VISUAL DESIGN CONSIDERATIONS

### **Layout Pattern**
```
┌─────────────────────────────────────────────────────────┐
│ Menu Bar                                                │
├────────┬────────────────────────────────────────┬───────┤
│        │                                        │       │
│ Left   │                                        │ Right │
│ Panel  │       Main Canvas                      │ Panel │
│        │    (Diagram Display/Edit)              │       │
│ (Modes │                                        │(Props)│
│  Tree  │                                        │ EGIF  │
│  Tools)│                                        │ Meta  │
│        │                                        │       │
├────────┴────────────────────────────────────────┴───────┤
│ Status Bar                                              │
└─────────────────────────────────────────────────────────┘
```

### **Mode-Specific Toolbars**

**Organon Mode**:
```
[Back] [Forward] [Zoom In] [Zoom Out] [Fit] [Export] [Search]
```

**Ergasterion Mode**:
```
[Undo] [Redo] [Add Vertex] [Add Edge] [Add Cut] [Transform] [Style] [Save]
```

**Agon Mode**:
```
[New Game] [Make Move] [Undo Move] [Branch] [Umpire] [Compare] [Archive]
```

---

## 🧪 TESTING STRATEGY

### **GUI Testing Approach**
1. **Unit Tests**: Individual widget functionality
2. **Integration Tests**: Mode transitions and data flow
3. **User Workflow Tests**: Complete end-to-end scenarios
4. **Visual Tests**: Screenshot comparison (golden masters)
5. **Performance Tests**: Large diagram handling

### **Critical Test Scenarios**
- Load EGI → Display correctly
- Mode switch preserves state
- Edit → Undo → Redo works
- Transformation → DTO updates correctly
- Invalid edit → Rejected with feedback
- Save → Load → Identical state

---

## 📚 EXISTING CODE REVIEW NEEDED

### **What Needs Investigation**
1. **Existing GUI Code**: Check `src/gui/` directory
2. **Qt Integration**: Any existing PyQt code?
3. **Canvas Implementations**: Prior diagram display code?
4. **Corpus Management**: Storage/retrieval systems?
5. **Export Systems**: LaTeX, SVG generation?

### **What We Already Have** ✅
- DiagramController (complete API)
- LayoutDTO (perfect for rendering)
- SVGRenderer (produces correct output)
- CommandExecutor (undo/redo ready)
- Validation system (logical area checking)
- Style system (JSON-based themes)
- Test infrastructure (workflow tests)

---

## 🎯 IMMEDIATE NEXT STEPS

### **Step 1: Discovery** (Today)
- [ ] Review existing GUI code in `src/gui/`
- [ ] Check for Qt dependencies
- [ ] Identify reusable components
- [ ] Document what exists vs. what's needed

### **Step 2: Decision** (Today/Tomorrow)
- [ ] Confirm GUI framework choice
- [ ] Finalize build order (sequential vs. hybrid)
- [ ] Decide on mode separation approach
- [ ] Define MVP for Phase 1

### **Step 3: Foundation** (This Week)
- [ ] Set up GUI project structure
- [ ] Create main application window
- [ ] Integrate DiagramController
- [ ] Display first SVG from DTO
- [ ] Basic mode switcher

### **Step 4: Organon MVP** (Next Week)
- [ ] Load EGI from file
- [ ] Display in read-only canvas
- [ ] Show EGIF in panel
- [ ] Basic navigation (pan/zoom)
- [ ] Export to SVG

---

## ❓ QUESTIONS FOR USER

1. **GUI Framework**: Do you have a preference (Qt, Tk, Web, wx)?

2. **Build Order**: Sequential (complete each before next) or Hybrid (layers across all)?

3. **Existing Code**: Should we review what's in `src/gui/` before planning further?

4. **Scope**: Are we building for:
   - Single user on desktop?
   - Multi-user collaborative?
   - Web deployment?

5. **Timeline**: What's your target timeline for:
   - Working Organon?
   - Working Ergasterion?
   - Working Agon?

6. **MVP Definition**: What's the absolute minimum for "useful"?
   - Just viewing diagrams?
   - Viewing + simple editing?
   - Full transformation practice?

---

## 📝 SUMMARY

**We have solid foundations**:
- ✅ DiagramController API (tested, production-ready)
- ✅ Layout engine (correct rendering)
- ✅ Testing infrastructure (comprehensive)
- ✅ Clear architectural vision (three modules)

**We need to decide**:
- GUI framework
- Build strategy (sequential/hybrid/concurrent)
- Mode separation approach
- Phase 1 MVP definition

**We should investigate**:
- Existing GUI code
- Qt setup and dependencies
- Corpus storage system
- Export infrastructure

**Recommendation**: Let's review existing GUI code first, then make informed decisions about framework and approach.

---

**Ready to proceed**: Once we answer the key questions, we can start Phase 1 implementation with confidence!
