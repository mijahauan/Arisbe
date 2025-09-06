# Manual Testing Guide for Arisbe Integrated Interface

## Overview
This guide documents the manual testing workflow for the integrated Arisbe home interface with embedded Organon and Ergasterion rooms.

## Testing the Integrated Home Interface

### 1. Launch Arisbe
```bash
python arisbe.py
```

### 2. Navigate the Home Interface
- **Foyer**: Welcome screen with authentic Arisbe house image
- **Room Selection**: Three working rooms available:
  - **📚 Organon** (Library): Corpus browsing and graph management
  - **🔨 Ergasterion** (Workshop): Interactive diagram creation and editing
  - **🏆 Agon** (Game Room): Future competition space

### 3. Test Organon (Library) Functionality
1. Click "📚 Enter Organon"
2. Navigate corpus structure in left panel
3. Browse to `corpus/graphs/dau_2006_p112_ligature/`
4. Select the graph to view EGI structure
5. Verify diagram rendering shows:
   - 1 vertex (generic)
   - 3 predicates (P, Q, R)
   - 1 cut containing Q and R
   - Proper ligature connections
6. Test handoff to Ergasterion for editing

### 4. Test Ergasterion (Workshop) Manual Element Creation
1. Click "🔨 Enter Ergasterion" or use handoff from Organon
2. **Canvas starts empty** - this is expected for de novo creation
3. **LEFT-CLICK on empty canvas** to open context menu
4. Test element creation:
   - Select "Add Vertex here" → Creates black dot vertex
   - Select "Add Predicate here" → Creates text box predicate
   - Select "Add Cut here" → Creates oval boundary for negation
5. **RIGHT-CLICK on existing elements** for modification options
6. Test constraint validation by attempting to overlap elements

### 5. Expected Behaviors

#### Constraint System
- **Syntactic constraints**: Always enforced (prevents invalid overlaps)
- **Semantic constraints**: Optional enforcement (logical consistency)
- **Spatial padding**: Elements maintain minimum separation
- **Ligature validation**: Proper connections between elements

#### Element Rendering
- **Vertices**: Black dots with optional labels (e.g., "Socrates")
- **Predicates**: Text boxes with relation names (e.g., "Human")
- **Ligatures**: Heavy lines connecting vertices to predicates
- **Cuts**: Oval boundaries for negation areas

#### Navigation
- **🏠 Return Home**: Available from any room
- **Room indicators**: Show current location
- **Seamless transitions**: No separate windows

## Test Cases Completed

### ✅ Core Infrastructure
- [x] EGI → diagram rendering pipeline
- [x] Constraint engine with syntactic/semantic validation
- [x] Spatial padding and overlap detection
- [x] Vertex, predicate, and ligature rendering
- [x] Integrated home interface with room metaphor

### ✅ User Interface
- [x] Unified "house with rooms" design
- [x] Greek nomenclature (Organon, Ergasterion, Agon)
- [x] Authentic Arisbe house image integration
- [x] Embedded room navigation
- [x] Context menu functionality

### ✅ Corpus Integration
- [x] Organon corpus browsing
- [x] Graph metadata and linear forms display
- [x] EGI structure visualization
- [x] Handoff protocol between rooms

## Manual Testing Checklist

### Home Interface
- [ ] Arisbe launches with foyer view
- [ ] House image displays correctly
- [ ] All three room cards are visible and clickable
- [ ] Room descriptions are accurate

### Organon Testing
- [ ] Library opens within same window
- [ ] Corpus navigation works in left panel
- [ ] Graph selection displays metadata
- [ ] EGI rendering shows correct structure
- [ ] Handoff to Ergasterion functions

### Ergasterion Testing
- [ ] Workshop opens within same window (not separate)
- [ ] Canvas starts empty for de novo creation
- [ ] Left-click on canvas opens context menu
- [ ] Vertex creation works and renders properly
- [ ] Predicate creation works and renders properly
- [ ] Cut creation works and renders properly
- [ ] Right-click on elements shows modification options
- [ ] Constraint validation prevents invalid overlaps

### Navigation Testing
- [ ] "🏠 Return Home" button works from all rooms
- [ ] Room indicators update correctly
- [ ] No separate windows open (fully integrated)
- [ ] Transitions are smooth and intuitive

## Known Limitations
- Agon (Game Room) is placeholder for future implementation
- Some Qt CSS warnings (cosmetic, don't affect functionality)
- Manual element creation required (no automated drawing tools yet)

## Success Criteria
The integrated Arisbe interface successfully provides:
1. **Unified Experience**: All rooms within single window
2. **Authentic Design**: Historical connection to Peirce's house
3. **Functional Workflow**: Browse → Edit → Navigate seamlessly
4. **Constraint Validation**: Proper EG logical structure enforcement
5. **User-Driven Creation**: Manual element placement and editing
