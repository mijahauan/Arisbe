# Web-Based Interactive EGI Viewer: Implementation Plan

**Target**: Production-ready web application for viewing and transforming existential graphs  
**Architecture**: Python backend (Flask/FastAPI) + JavaScript frontend (vanilla JS + SVG)  
**Scope**: Phase 1 focuses on ERA transformation; Phase 2 extends to all 6 transformation rules

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Communication Strategy](#backend-communication-strategy)
3. [Transformation Workflow Design](#transformation-workflow-design)
4. [Subgraph Selection System](#subgraph-selection-system)
5. [Area Targeting System](#area-targeting-system)
6. [State Management and History](#state-management-and-history)
7. [Layout Stability Considerations](#layout-stability-considerations)
8. [Implementation Phases](#implementation-phases)
9. [Technical Specifications](#technical-specifications)
10. [Testing Strategy](#testing-strategy)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser (Client)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Interactive SVG Canvas                                 │ │
│  │  - Pan/zoom (via SVG viewBox manipulation)             │ │
│  │  - Element hover highlighting                           │ │
│  │  - Click selection                                      │ │
│  │  - Transformation mode UI                               │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Control Panel                                          │ │
│  │  - Transformation rule selector                         │ │
│  │  - Element info display                                 │ │
│  │  - Undo/redo buttons                                    │ │
│  │  - Confirm/cancel transformation                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                   Python Backend (FastAPI)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  REST API Endpoints                                     │ │
│  │  - GET /api/diagram/<id>  → LayoutDTO + SVG            │ │
│  │  - POST /api/transform    → Apply transformation       │ │
│  │  - GET /api/history/<id>  → Transformation history     │ │
│  │  - POST /api/undo         → Revert to previous state   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Core Services                                          │ │
│  │  - ELKLayoutEngine        → Generate layouts            │ │
│  │  - SimpleSVGRenderer      → Render SVG                 │ │
│  │  - TransformationEngine   → Apply EG rules             │ │
│  │  - SubgraphClosureValidator → Validate selections      │ │
│  │  - SessionManager         → Track user sessions        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Action → Frontend Event → API Request → Backend Processing → Response
     ↓                                              ↓
  Update UI ← Render New State ← JSON Response ← EGI + Layout
```

---

## Backend Communication Strategy

### Hybrid REST + WebSocket Approach

**REST API** for simple queries and state retrieval:
- Fast, stateless, cacheable
- Good for: loading diagrams, getting element info, simple transformations

**WebSocket** for transformation workflows:
- Real-time progress updates during ELK layout (~1-2s)
- Enables preview before commit
- Better UX for multi-step transformations

### Recommended: Start with REST, Add WebSocket Later

**Phase 1** (MVP): Pure REST
- Simpler to implement and debug
- Acceptable latency for single transformations
- Can show loading spinner during layout

**Phase 2** (Enhancement): Add WebSocket for transformation sessions
- Progress feedback: "Computing layout... 45%"
- Live preview updates
- Multi-step transformation workflows

### API Endpoints (REST)

#### Core Endpoints

```
GET /api/diagrams
  → List available diagrams (from tomos corpus)
  Response: [{ id, name, description, source }]

GET /api/diagram/<id>
  → Load a specific diagram
  Response: {
    egi: <EGI JSON>,
    layout_dto: <LayoutDTO JSON>,
    svg: <SVG string>,
    metadata: { name, description, ... }
  }

POST /api/diagram/new
  Body: { template: "empty" | "double_cut" | ... }
  → Create new diagram from template
  Response: { session_id, egi, layout_dto, svg }

GET /api/session/<session_id>
  → Get current session state
  Response: { egi, layout_dto, svg, history_length, can_undo, can_redo }
```

#### Transformation Endpoints

```
POST /api/transform/validate
  Body: {
    session_id,
    rule: "ERA" | "INS" | "IT+" | "IT-" | "DC+" | "DC-",
    parameters: { ... }  // rule-specific
  }
  → Validate transformation parameters without applying
  Response: {
    valid: true/false,
    errors: [...],
    preview_egi: <EGI JSON>,  // if valid
    preview_svg: <SVG string>  // if valid
  }

POST /api/transform/apply
  Body: {
    session_id,
    rule: "ERA",
    parameters: { selected_elements: [...] }
  }
  → Apply transformation and update session
  Response: {
    success: true/false,
    egi: <new EGI>,
    layout_dto: <new LayoutDTO>,
    svg: <new SVG>,
    history_index: <int>
  }

POST /api/undo
  Body: { session_id }
  → Revert to previous state
  Response: { egi, layout_dto, svg, history_index }

POST /api/redo
  Body: { session_id }
  → Re-apply reverted transformation
  Response: { egi, layout_dto, svg, history_index }
```

#### Element Query Endpoints

```
GET /api/element/<session_id>/<element_id>
  → Get detailed info about an element
  Response: {
    id, type: "vertex"|"predicate"|"cut",
    label, is_generic, area, connections, ...
  }

POST /api/subgraph/validate
  Body: { session_id, selected_elements: [...] }
  → Check if selection forms a proper subgraph
  Response: {
    is_closed: true/false,
    missing_elements: [...],
    closure: [...]  // auto-expanded closure if requested
  }

GET /api/areas/<session_id>
  → Get all areas with polarity info
  Response: [{
    area_id, polarity: "positive"|"negative",
    depth, parent_area, bounds: { min_x, min_y, max_x, max_y }
  }]
```

---

## Transformation Workflow Design

### Universal Workflow Pattern

Every transformation follows this sequence:

```
1. ENTER MODE
   ↓
2. SELECT/SPECIFY
   ↓
3. VALIDATE
   ↓
4. PREVIEW
   ↓
5. CONFIRM or CANCEL
```

### Rule-Specific Workflows

#### ERA (Erasure)

**Context**: Positive area  
**User must specify**: Subgraph to erase  
**Workflow**:

1. **Enter ERA mode**
   - UI highlights positive areas (white fills)
   - Shows message: "Select elements to erase (must be in positive area)"

2. **Select elements**
   - Click predicates/vertices to add to selection
   - Selected elements highlighted in red
   - Real-time closure validation (show missing elements if incomplete)

3. **Validate**
   - POST /api/subgraph/validate with selected elements
   - If invalid, show errors and required additions
   - If valid, enable "Preview" button

4. **Preview**
   - POST /api/transform/validate with rule="ERA"
   - Show preview SVG with erased elements faded out
   - Display confirmation dialog: "Erase N elements?"

5. **Confirm**
   - POST /api/transform/apply
   - Receive new EGI + layout
   - Render new diagram
   - Exit ERA mode

**Cancel**: Clear selection, exit mode

#### INS (Insertion)

**Context**: Negative area  
**User must specify**: (1) Subgraph to insert, (2) Target area  
**Workflow**:

1. **Enter INS mode**
   - UI highlights negative areas (gray fills)
   - Shows input panel: "Enter EGIF to insert"

2. **Specify content**
   - User types EGIF string (e.g., `(Human "Socrates")`)
   - Parse EGIF on frontend (basic validation)
   - Enable "Select Area" button

3. **Select target area**
   - Click on a negative area
   - Highlight selected area in green
   - Enable "Preview" button

4. **Preview**
   - POST /api/transform/validate with rule="INS", content, area
   - Show preview SVG with new elements in green
   - Display confirmation dialog

5. **Confirm**
   - POST /api/transform/apply
   - Receive new EGI + layout
   - Render new diagram

#### IT+ (Iteration - Insert Copy)

**Context**: Any area → even-deeper area  
**User must specify**: (1) Subgraph to iterate, (2) Destination area  
**Workflow**:

1. **Enter IT+ mode**
   - Show message: "Select subgraph to copy, then select destination area"

2. **Select source subgraph**
   - Click elements (with closure validation)
   - Highlight in blue
   - Enable "Select Destination" button

3. **Select destination area**
   - Click on an area that is even-deeper than source
   - Validate depth relationship
   - Highlight destination in green

4. **Preview & Confirm**
   - Show preview with copied elements in destination
   - Apply transformation

#### IT- (Deiteration - Remove Copy)

**Context**: Any area  
**User must specify**: Iterated copy to remove  
**Workflow**:

1. **Enter IT- mode**
   - Show message: "Select iterated copy to remove"

2. **Select copy**
   - Click elements
   - System validates that an original exists elsewhere
   - Highlight in red

3. **Preview & Confirm**
   - Show preview with copy removed
   - Apply transformation

#### DC+ (Double Cut - Insert)

**Context**: Any area  
**User must specify**: Position for double cut  
**Workflow**:

1. **Enter DC+ mode**
   - Show message: "Click area to insert double cut"

2. **Click area**
   - Validate area is accessible
   - Preview shows new nested cuts

3. **Confirm**
   - Apply transformation
   - Double cut appears (initially empty)

#### DC- (Double Cut - Remove)

**Context**: Double cut pair  
**User must specify**: Outer cut of double cut  
**Workflow**:

1. **Enter DC- mode**
   - Show message: "Click outer cut of double cut to collapse"

2. **Click cut**
   - Validate it's a double cut (contains exactly one cut with same contents)
   - Highlight both cuts in yellow

3. **Preview & Confirm**
   - Show preview with double cut collapsed
   - Apply transformation

---

## Subgraph Selection System

### The Challenge

A "proper subgraph" for ERA/IT- must satisfy **closure** requirements. The existing `SubgraphClosureValidator` already implements this logic. The UI must make closure intuitive.

### Selection Strategies

#### Strategy 1: Click-to-Select with Auto-Expansion (Recommended)

**User flow**:
1. User clicks elements to add to selection
2. System continuously validates closure
3. If incomplete, show missing elements in orange outline
4. User can:
   - Manually add missing elements
   - Click "Auto-Complete" to expand to closure
   - See real-time validation status

**Implementation**:
- Frontend tracks selected element IDs
- On each selection change, POST /api/subgraph/validate
- Response includes `is_closed` and `missing_elements`
- Render missing elements with dashed orange outline
- "Auto-Complete" button calls validator with `allow_expansion=True`

#### Strategy 2: Lasso/Marquee Selection

**User flow**:
1. User drags a selection rectangle
2. All elements with centers inside rectangle are selected
3. System validates closure and shows missing elements

**Implementation**:
- SVG `<rect>` overlay for lasso
- Compute element centers from LayoutDTO
- Rectangle intersection test
- Same validation flow as Strategy 1

**Recommendation**: Implement Strategy 1 first (simpler, more precise). Add Strategy 2 later if needed.

### Visual Feedback

```
Selected elements:       Solid red outline, 3px
Missing for closure:     Dashed orange outline, 2px
Valid closed selection:  Solid green outline, 3px
Hovered element:         Yellow glow, 2px
```

### Lines of Identity Across Cuts

**Special case**: Selecting a predicate inside a cut that shares a vertex with the outside.

**Rule**: The closure validator already handles this. If the predicate is selected, the shared vertex must be included in the closure (if it's in an ancestor area).

**UI behavior**: When user selects the predicate, the shared vertex automatically gets an orange outline (missing for closure). User must explicitly select it or use "Auto-Complete".

---

## Area Targeting System

### The Challenge

Areas are spatially nested. Clicking a point could match multiple areas (sheet, outer cut, inner cut, etc.). Need to identify the correct area.

### Deepest-Area-at-Point Algorithm

```python
def find_area_at_point(x: float, y: float, cut_bounds: Dict, area_hierarchy: Dict) -> ElementID:
    """Return the deepest area containing point (x, y)."""
    candidates = []
    
    # Check sheet (always contains everything)
    candidates.append(("sheet", 0))
    
    # Check each cut
    for cut_id, bounds in cut_bounds.items():
        if bounds.min_x <= x <= bounds.max_x and bounds.min_y <= y <= bounds.max_y:
            depth = compute_depth(cut_id, area_hierarchy)
            candidates.append((cut_id, depth))
    
    # Return deepest (highest depth number)
    candidates.sort(key=lambda c: c[1], reverse=True)
    return candidates[0][0]
```

**Frontend implementation**:
- On click, send `{ x, y }` to backend
- Backend returns `{ area_id, polarity, depth }`
- Frontend highlights the area

### Area Highlighting

**On hover**:
- Detect which area is under cursor
- Highlight area boundary with thick colored stroke:
  - Positive area: blue stroke
  - Negative area: green stroke
- Show tooltip: "Area: <id>, Polarity: <positive/negative>, Depth: <n>"

**On selection**:
- Selected area gets filled overlay (semi-transparent):
  - Positive: rgba(0, 100, 255, 0.1)
  - Negative: rgba(0, 200, 100, 0.1)

### Polarity Indication During Transformation

**ERA mode**: Only positive areas are selectable
- Positive areas: normal appearance
- Negative areas: dimmed (opacity 0.3), not clickable

**INS mode**: Only negative areas are selectable
- Negative areas: normal appearance
- Positive areas: dimmed

**IT+ mode**: Show depth numbers on each area
- Helps user understand even-deeper constraint

---

## State Management and History

### Session Model

Each user session maintains:

```python
@dataclass
class TransformationSession:
    session_id: str
    current_egi: RelationalGraphWithCuts
    current_layout_dto: LayoutDTO
    history: List[TransformationStep]
    history_index: int  # current position in history
    created_at: datetime
    last_accessed: datetime

@dataclass
class TransformationStep:
    egi: RelationalGraphWithCuts
    layout_dto: LayoutDTO
    rule: Optional[str]  # None for initial state
    parameters: Optional[Dict]
    timestamp: datetime
```

### History Operations

**Undo**:
```python
if session.history_index > 0:
    session.history_index -= 1
    session.current_egi = session.history[session.history_index].egi
    session.current_layout_dto = session.history[session.history_index].layout_dto
```

**Redo**:
```python
if session.history_index < len(session.history) - 1:
    session.history_index += 1
    session.current_egi = session.history[session.history_index].egi
    session.current_layout_dto = session.history[session.history_index].layout_dto
```

**New transformation**:
```python
# Truncate history if we're not at the end
session.history = session.history[:session.history_index + 1]

# Apply transformation
new_egi = apply_transformation(session.current_egi, rule, parameters)
new_layout_dto = generate_layout(new_egi, style)

# Add to history
session.history.append(TransformationStep(new_egi, new_layout_dto, rule, parameters, now()))
session.history_index += 1
session.current_egi = new_egi
session.current_layout_dto = new_layout_dto
```

### Session Persistence

**In-memory** (Phase 1):
- Store sessions in Python dict: `sessions: Dict[str, TransformationSession]`
- Sessions expire after 1 hour of inactivity
- Simple, no database needed

**Persistent** (Phase 2):
- Store in SQLite or Redis
- Serialize EGI and LayoutDTO as JSON
- Enables session recovery across server restarts

---

## Layout Stability Considerations

### The Problem

When a transformation modifies an EGI, unchanged elements should maintain their positions. The visual diff should be immediately perceptible — only the insertion/deletion should move.

ELK doesn't support this natively (it computes fresh layouts from scratch). We need a **position anchoring** layer.

### Solution: Layout Delta Inheritance

**Before transformation**:
1. Snapshot all element positions from current LayoutDTO
2. Store as `previous_positions: Dict[ElementID, Point]`

**After transformation**:
1. Identify which elements persist (same IDs in new EGI)
2. Feed those positions to ELK as **fixed coordinates** (ELK supports per-node position constraints via `layoutOptions`)
3. Let ELK place only the *new* elements, working around the anchored ones

**Implementation**:

```python
def generate_layout_with_anchoring(
    egi: RelationalGraphWithCuts,
    style: StyleSpecification,
    previous_layout: Optional[LayoutDTO] = None,
) -> LayoutDTO:
    """Generate layout, anchoring unchanged elements from previous layout."""
    
    # Extract positions to anchor
    anchored_positions = {}
    if previous_layout:
        for elem_id, pos in previous_layout.vertex_positions.items():
            if elem_id in {v.id for v in egi.V}:  # element still exists
                anchored_positions[elem_id] = pos
        for elem_id, pos in previous_layout.predicate_positions.items():
            if elem_id in {e.id for e in egi.E}:
                anchored_positions[elem_id] = pos
    
    # Pass to ELK engine
    return elk_engine.generate_layout(egi, style, anchored_positions)
```

**ELK integration**:

In `_egi_to_elk_graph()`, for each anchored node:
```javascript
{
  "id": "node_123",
  "layoutOptions": {
    "org.eclipse.elk.position": "{ x: 100, y: 200 }",
    "org.eclipse.elk.nodeSize.constraints": "FIXED_POSITION"
  }
}
```

### When to Apply Anchoring

**Always** for transformation sequences:
- ERA: anchor everything except erased elements
- INS: anchor everything, let ELK place new elements
- IT+: anchor source and everything else, let ELK place copy
- IT-: anchor everything except removed copy
- DC+: anchor everything, let ELK place new cuts
- DC-: anchor everything except collapsed cuts

**Never** for:
- Initial load of a diagram (no previous layout)
- User explicitly requests "Re-layout from scratch"

### Deferred: Structural Templates

The broader "family resemblance" problem (two implications should look similar) requires **structural layout templates**. This is deferred to future work. For now, anchoring provides continuity within a single transformation sequence, which is the critical UX requirement.

---

## Implementation Phases

### Phase 1: Minimal Interactive Viewer (MVP)

**Goal**: Prove the architecture with basic viewing and one transformation (ERA)

**Deliverables**:
1. ✅ Backend API server (FastAPI)
   - Endpoints: `/api/diagrams`, `/api/diagram/<id>`, `/api/session/<id>`
   - Session management (in-memory)
   - Integration with ELKLayoutEngine and SimpleSVGRenderer

2. ✅ Frontend viewer
   - SVG rendering with pan/zoom
   - Element hover highlighting (show element ID and type)
   - Click to show element info panel

3. ✅ ERA transformation workflow
   - Enter ERA mode
   - Click-to-select elements
   - Real-time closure validation
   - Preview transformation
   - Confirm/cancel
   - Undo/redo

4. ✅ Layout stability
   - Implement position anchoring
   - Verify unchanged elements hold still during ERA

**Success criteria**:
- User can load a diagram from tomos corpus
- User can pan/zoom and inspect elements
- User can erase a subgraph via ERA
- Erased elements disappear, rest stay in place
- User can undo/redo

**Estimated effort**: 3-5 days

### Phase 2: Complete Transformation Suite

**Goal**: Extend to all 6 transformation rules

**Deliverables**:
1. ✅ INS workflow (insert into negative area)
2. ✅ IT+ workflow (iterate into deeper area)
3. ✅ IT- workflow (remove iterated copy)
4. ✅ DC+ workflow (insert double cut)
5. ✅ DC- workflow (collapse double cut)
6. ✅ Transformation mode selector UI
7. ✅ Rule-specific validation and error messages

**Success criteria**:
- User can apply all 6 transformation rules
- Each rule enforces correct polarity and structural constraints
- Preview works for all rules
- Undo/redo works across mixed rule sequences

**Estimated effort**: 4-6 days

### Phase 3: Enhanced UX (Optional)

**Goal**: Polish and advanced features

**Deliverables**:
1. Lasso/marquee selection
2. Keyboard shortcuts (Ctrl+Z undo, Ctrl+Y redo, ESC cancel)
3. Transformation history timeline (visual list of steps)
4. Export diagram as SVG/PNG
5. Load/save sessions
6. WebSocket for live progress updates during layout

**Estimated effort**: 3-4 days

### Phase 4: Layout Templates (Future)

**Goal**: Implement structural layout templates for common patterns

**Deliverables**:
1. `LayoutTemplate` data model
2. Pattern detection on EGI structure
3. Template catalog (implication, conjunction, syllogisms, etc.)
4. Template-based layout seeding
5. User-defined template creation ("save as template")

**Estimated effort**: 5-7 days

---

## Technical Specifications

### Backend Stack

**Framework**: FastAPI
- Modern, async-capable
- Automatic OpenAPI docs
- Built-in validation with Pydantic
- WebSocket support for Phase 3

**Dependencies**:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart  # for file uploads
```

**Project structure**:
```
src/
  web_api/
    __init__.py
    main.py              # FastAPI app
    routes/
      diagrams.py        # Diagram endpoints
      transformations.py # Transformation endpoints
      sessions.py        # Session management
    models/
      api_models.py      # Pydantic request/response models
    services/
      session_manager.py # Session state management
      layout_service.py  # Wrapper around ELKLayoutEngine
```

**Run server**:
```bash
cd src/web_api
uvicorn main:app --reload --port 8000
```

### Frontend Stack

**Framework**: Vanilla JavaScript (no framework)
- Simpler, fewer dependencies
- Direct SVG manipulation
- Can add React/Vue later if needed

**Libraries**:
- **svg-pan-zoom** (https://github.com/bumbu/svg-pan-zoom) — pan/zoom for SVG
- **axios** — HTTP client for API calls
- Optional: **Mousetrap** — keyboard shortcuts

**Project structure**:
```
src/web_viewer/
  index.html           # Main page
  css/
    styles.css         # Layout and styling
  js/
    main.js            # App initialization
    diagram-viewer.js  # SVG rendering and interaction
    transformation-ui.js # Transformation mode UI
    api-client.js      # API communication
    selection-manager.js # Element selection logic
```

**Serve frontend**:
```bash
cd src/web_viewer
python -m http.server 8080
```

Or serve from FastAPI:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="src/web_viewer", html=True), name="viewer")
```

### API Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

Or on error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_SELECTION",
    "message": "Selection is not a closed subgraph",
    "details": {
      "missing_elements": ["vertex_123", "edge_456"]
    }
  }
}
```

### Frontend State Management

Simple global state object:

```javascript
const AppState = {
  currentSession: null,
  currentEGI: null,
  currentLayoutDTO: null,
  currentSVG: null,
  transformationMode: null,  // null | "ERA" | "INS" | ...
  selectedElements: new Set(),
  selectedArea: null,
  canUndo: false,
  canRedo: false,
};
```

### SVG Interaction

**Pan/Zoom**:
```javascript
import svgPanZoom from 'svg-pan-zoom';

const panZoomInstance = svgPanZoom('#diagram-svg', {
  zoomEnabled: true,
  controlIconsEnabled: true,
  fit: true,
  center: true,
});
```

**Element Highlighting**:
```javascript
function highlightElement(elementId, color) {
  const elem = document.getElementById(elementId);
  if (elem) {
    elem.style.stroke = color;
    elem.style.strokeWidth = '3px';
  }
}
```

**Click Handling**:
```javascript
document.getElementById('diagram-svg').addEventListener('click', (e) => {
  const elementId = e.target.id;
  if (elementId && AppState.transformationMode === 'ERA') {
    toggleSelection(elementId);
  }
});
```

---

## Testing Strategy

### Backend Tests

**Unit tests** (pytest):
```python
# tests/web_api/test_transformation_endpoints.py

def test_era_transformation_valid_selection():
    """ERA with valid closed subgraph succeeds."""
    response = client.post("/api/transform/apply", json={
        "session_id": session_id,
        "rule": "ERA",
        "parameters": {"selected_elements": ["edge_1", "vertex_1"]}
    })
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_era_transformation_invalid_selection():
    """ERA with non-closed subgraph fails with error."""
    response = client.post("/api/transform/apply", json={
        "session_id": session_id,
        "rule": "ERA",
        "parameters": {"selected_elements": ["edge_1"]}  # missing vertex
    })
    assert response.status_code == 400
    assert "not a closed subgraph" in response.json()["error"]["message"]
```

**Integration tests**:
- Full transformation sequences (ERA → INS → IT+ → ...)
- Undo/redo across multiple steps
- Session expiration and cleanup

### Frontend Tests

**Manual testing** (Phase 1):
- Checklist of user workflows
- Visual inspection of rendered diagrams

**Automated tests** (Phase 3):
- Playwright or Cypress for E2E tests
- Test transformation workflows end-to-end

### Test Diagrams

Use existing tomos corpus:
- `peirce_modus_ponens` — simple, good for ERA testing
- `dau_2006_p112_ligature` — cross-boundary ligatures
- `roberts_1973_p57_disjunction` — nested cuts

Create test-specific diagrams:
- Minimal ERA test: `(Human *x)` → erase to empty sheet
- Minimal INS test: `~[~[]]` → insert `(P *x)` → `~[~[*x (P x)]]`

---

## Error Handling

### Backend Error Categories

1. **Validation errors** (400 Bad Request)
   - Invalid EGIF syntax
   - Non-closed subgraph selection
   - Wrong polarity for transformation
   - Missing required parameters

2. **State errors** (409 Conflict)
   - Session not found
   - Cannot undo (at start of history)
   - Cannot redo (at end of history)

3. **Server errors** (500 Internal Server Error)
   - ELK subprocess failure
   - Layout generation timeout
   - Unexpected exception

### Frontend Error Display

```javascript
function showError(error) {
  const errorPanel = document.getElementById('error-panel');
  errorPanel.innerHTML = `
    <div class="error-message">
      <strong>${error.code}</strong>: ${error.message}
      ${error.details ? `<pre>${JSON.stringify(error.details, null, 2)}</pre>` : ''}
    </div>
  `;
  errorPanel.style.display = 'block';
}
```

---

## Performance Considerations

### Backend Optimizations

1. **Layout caching**: Cache LayoutDTO for unchanged EGIs (keyed by EGI hash)
2. **Incremental SVG**: Only re-render changed elements (future optimization)
3. **Async layout**: Run ELK subprocess asynchronously, don't block other requests

### Frontend Optimizations

1. **SVG optimization**: Minimize DOM manipulation, batch updates
2. **Debounce hover**: Don't highlight on every mousemove, debounce to 50ms
3. **Lazy loading**: Load diagram list on demand, not all at once

### Latency Budget

- **Initial diagram load**: <2s (ELK layout + SVG render)
- **Transformation preview**: <2s (re-layout + render)
- **Transformation apply**: <2s (same as preview, already computed)
- **Undo/redo**: <100ms (no re-layout, just re-render cached LayoutDTO)
- **Element hover**: <16ms (60fps)

---

## Security Considerations

### Input Validation

- **EGIF parsing**: Validate syntax before passing to parser (prevent injection)
- **Element IDs**: Validate against current EGI (prevent arbitrary ID access)
- **Session IDs**: Use UUIDs, validate ownership

### Rate Limiting

- Limit transformation requests to 10/minute per session
- Limit session creation to 5/minute per IP

### CORS

- Configure CORS headers for API endpoints
- Restrict to known frontend origins in production

---

## Deployment

### Development

```bash
# Terminal 1: Backend
cd src/web_api
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend (if separate)
cd src/web_viewer
python -m http.server 8080

# Or serve frontend from FastAPI (recommended)
# Just run backend, frontend served at http://localhost:8000/
```

### Production

**Option 1: Single server** (FastAPI serves frontend)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Option 2: Separate servers** (Nginx reverse proxy)
```
Frontend: Nginx serves static files
Backend: Nginx proxies /api/* to FastAPI
```

**Docker** (future):
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN npm install elkjs
COPY src/ src/
CMD ["uvicorn", "src.web_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Success Metrics

### Phase 1 (MVP)

- ✅ User can load and view any diagram from tomos corpus
- ✅ User can pan/zoom smoothly (60fps)
- ✅ User can hover over elements and see info
- ✅ User can successfully apply ERA transformation
- ✅ Unchanged elements maintain positions after ERA
- ✅ User can undo/redo ERA

### Phase 2 (Full Transformation Suite)

- ✅ User can apply all 6 transformation rules
- ✅ Each rule enforces correct constraints
- ✅ Preview works for all rules
- ✅ User can build a simple proof (e.g., modus ponens) from scratch using transformations

### Phase 3 (Enhanced UX)

- ✅ User can select elements via lasso
- ✅ Keyboard shortcuts work
- ✅ User can export diagrams
- ✅ WebSocket provides real-time feedback

---

## Open Questions for Implementation

1. **Session expiration**: 1 hour idle timeout reasonable? Or make configurable?

2. **Layout anchoring**: Should we anchor *all* unchanged elements, or only those "near" the transformation site? (Anchoring all is simpler and more predictable)

3. **Preview rendering**: Generate full SVG or just highlight diff? (Full SVG is simpler, diff highlighting is more efficient)

4. **Multi-user support**: Phase 1 assumes single-user sessions. Add collaborative editing later?

5. **Undo/redo UI**: Linear history or branching (Git-style)? (Linear is simpler for Phase 1)

---

## References

### Arisbe Codebase

- `src/elk_layout_engine.py` — Layout generation
- `src/simple_svg_renderer.py` — SVG rendering
- `src/formal_transformation_rules.py` — Transformation rule implementations
- `src/subgraph_closure_validator.py` — Closure validation
- `tests/test_elk_layout_engine.py` — Layout engine tests

### External Documentation

- FastAPI: https://fastapi.tiangolo.com/
- ELK: https://www.eclipse.org/elk/
- SVG pan-zoom: https://github.com/bumbu/svg-pan-zoom
- Peirce's EG: Dau (2006), Roberts (1973)

---

## Appendix: Example API Interactions

### Load a Diagram

**Request**:
```http
GET /api/diagram/peirce_modus_ponens
```

**Response**:
```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "egi": { "V": [...], "E": [...], ... },
    "layout_dto": {
      "vertex_positions": { "v1": {"x": 100, "y": 200}, ... },
      "predicate_positions": { "e1": {"x": 150, "y": 200}, ... },
      "cut_bounds": { "c1": {"min_x": 50, "min_y": 50, "max_x": 300, "max_y": 300} },
      "ligature_paths": [...]
    },
    "svg": "<svg>...</svg>",
    "metadata": {
      "name": "Peirce's Modus Ponens",
      "source": "tomos/graphs/peirce_modus_ponens"
    }
  }
}
```

### Apply ERA Transformation

**Request**:
```http
POST /api/transform/apply
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "rule": "ERA",
  "parameters": {
    "selected_elements": ["edge_1", "vertex_1"]
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "egi": { "V": [...], "E": [...], ... },
    "layout_dto": { ... },
    "svg": "<svg>...</svg>",
    "history_index": 1,
    "can_undo": true,
    "can_redo": false
  }
}
```

### Validate Subgraph

**Request**:
```http
POST /api/subgraph/validate
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "selected_elements": ["edge_1"]
}
```

**Response** (invalid):
```json
{
  "success": false,
  "error": {
    "code": "SUBGRAPH_NOT_CLOSED",
    "message": "Selection is not a closed subgraph",
    "details": {
      "missing_elements": ["vertex_1"],
      "reason": "Edge 'edge_1' connects to vertex 'vertex_1' which is not selected"
    }
  }
}
```

---

## Conclusion

This plan provides a complete roadmap for implementing a web-based interactive EGI viewer with transformation support. The phased approach allows for incremental delivery and validation:

- **Phase 1** proves the architecture with ERA
- **Phase 2** completes the transformation suite
- **Phase 3** adds polish and advanced features
- **Phase 4** (future) adds structural layout templates

The design respects EG semantics, provides clear visual feedback, and maintains layout stability across transformation sequences. All considerations from the original discussion are addressed: backend communication, transformation workflows, subgraph selection, area targeting, state management, and layout stability.

The implementation can proceed with confidence that the architecture is sound and extensible.
