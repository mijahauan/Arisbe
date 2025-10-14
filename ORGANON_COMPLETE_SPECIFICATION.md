# Organon Complete Feature Specification

## Current Status
✅ **IMPLEMENTED**: Basic viewing (browse, load, display UoDs)  
⚠️ **INCOMPLETE**: Import/export, metadata management, history navigation

---

## 1. Synchronic & Diachronic Exploration

### Synchronic View (Current State)
**Status**: ✅ Partially implemented
- [x] View current EGI diagram
- [x] View current EGIF linear form
- [x] View current metadata
- [ ] Compare states side-by-side
- [ ] Export current state in multiple formats
- [ ] View complexity metrics

### Diachronic View (Historical Process)
**Status**: ⚠️ Partially implemented
- [x] View transformation history timeline
- [x] Navigate to previous states (time-travel)
- [ ] Compare any two states
- [ ] View transformation justifications
- [ ] Export entire history
- [ ] Visualize transformation graph
- [ ] Filter history (by rule, date, author)
- [ ] Search across all states

---

## 2. Import/Export System

### Import Formats
**Status**: ⚠️ Parsers exist, GUI integration needed
- [ ] **EGIF** (Extended Graph Interchange Format) - ✅ Parser ready
- [ ] **CGIF** (Conceptual Graph Interchange Format) - ✅ Parser ready
- [ ] **CLIF** (Common Logic Interchange Format) - ✅ Parser ready
- [ ] **FOPL** (First-Order Predicate Logic - Dau Ch.18) - ✅ Translator ready
- [ ] **JSON** (Full UoD with metadata) - ✅ CorpusService ready
- [ ] **JSON** (EGI only) - ✅ egi_io ready
- [ ] **Batch Import** (multiple files)

### Export Formats
**Status**: ⚠️ Generators exist, GUI integration needed
- [x] **SVG** (Scalable Vector Graphics) - ✅ Working in GUI
- [ ] **EGIF** (Linear form of current state) - ✅ Generator ready
- [ ] **CGIF** (Conceptual Graphs format) - ✅ Generator ready
- [ ] **CLIF** (Common Logic format) - ✅ Generator ready
- [ ] **FOPL** (First-Order Predicate Logic) - ✅ Translator ready
- [ ] **JSON** (Full UoD with metadata + history) - ✅ CorpusService ready
- [ ] **JSON** (Current EGI only) - ✅ egi_io ready
- [ ] **PDF** (Rendered diagram + metadata) - Future
- [ ] **LaTeX** (For academic papers) - Future
- [ ] **History Export** (All states + transformations) - ✅ Data model ready

### Import/Export UI
- [ ] Import dialog with format selection
- [ ] Export dialog with format + options
- [ ] Preview before import
- [ ] Validation during import
- [ ] Error handling and reporting
- [ ] Progress indication for large files

---

## 3. Metadata Management

### View Metadata
**Status**: ✅ Implemented (read-only)
- [x] Name, description
- [x] Type (static/dynamic)
- [x] Category
- [x] Tags
- [x] Authors, citation
- [x] Timestamps
- [x] History statistics

### Edit Metadata
**Status**: ❌ Not implemented
- [ ] Edit name/description
- [ ] Add/remove tags
- [ ] Change category
- [ ] Add/edit authors
- [ ] Add/edit citation
- [ ] Add notes/annotations
- [ ] Link related UoDs
- [ ] Validation of changes
- [ ] Save metadata changes

### Metadata Dialog
- [ ] Modal dialog for editing
- [ ] Form validation
- [ ] Undo changes
- [ ] Save/Cancel buttons
- [ ] Preview of changes

---

## 4. Corpus Management

### UoD Operations
**Status**: ⚠️ Partially implemented
- [x] Browse corpus (list UoDs)
- [x] Load UoD
- [x] Filter by type (static/dynamic)
- [ ] Search UoDs (by name, tags, author)
- [ ] Delete UoD (with confirmation)
- [ ] Duplicate UoD
- [ ] Rename UoD
- [ ] Archive/unarchive
- [ ] Export multiple UoDs

### Corpus Statistics
**Status**: ❌ Not implemented
- [ ] Total UoDs count
- [ ] Static vs. Dynamic counts
- [ ] Category breakdown
- [ ] Average complexity metrics
- [ ] Storage size
- [ ] Most recent additions
- [ ] Most frequently viewed

---

## 5. History Navigation & Analysis

### Timeline Features
**Status**: ⚠️ Basic timeline implemented
- [x] Linear timeline view
- [x] Click to navigate states
- [x] Current state indicator
- [ ] Branching visualization (if supported)
- [ ] Transformation details on hover
- [ ] Filter timeline (by rule type)
- [ ] Search timeline
- [ ] Export timeline

### State Comparison
**Status**: ❌ Not implemented
- [ ] Select two states to compare
- [ ] Side-by-side diagram view
- [ ] Highlight differences
- [ ] Diff of EGIF forms
- [ ] Show transformation path
- [ ] Export comparison

### Transformation Analysis
**Status**: ❌ Not implemented
- [ ] View transformation details
- [ ] Show preconditions/postconditions
- [ ] View justification (if recorded)
- [ ] Show applied rule
- [ ] View affected elements
- [ ] Export transformation record

---

## 6. Visualization Options

### Diagram Display
**Status**: ✅ Basic display working
- [x] SVG rendering
- [x] Zoom controls (TODO: verify)
- [x] Pan controls (TODO: verify)
- [ ] Highlight elements by type
- [ ] Show/hide cut labels
- [ ] Show/hide arity numbers
- [ ] Toggle variable labels
- [ ] Export view as image

### Layout Options
**Status**: ❌ Not implemented
- [ ] Reset layout (clear deltas)
- [ ] Auto-layout algorithms
- [ ] Manual element repositioning
- [ ] Grid snap
- [ ] Alignment tools

---

## 7. Integration Features

### Ergasterion Integration
**Status**: ⚠️ Foundation implemented
- [x] "Edit in Ergasterion" button
- [x] Pass UoD to Ergasterion
- [ ] Receive updated UoD back
- [ ] Show diff of changes
- [ ] Merge changes dialog

### Agon Integration
**Status**: ❌ Not implemented
- [ ] "Validate in Agon" button
- [ ] Show validation results
- [ ] View proof attempts
- [ ] Show equivalent forms

---

## 8. User Experience Enhancements

### Navigation
**Status**: ⚠️ Basic navigation working
- [x] Corpus browser sidebar
- [x] Metadata panel
- [x] History timeline (for historical UoDs)
- [ ] Breadcrumb navigation
- [ ] Recent files list
- [ ] Bookmarks/favorites
- [ ] Quick search bar

### Feedback & Status
**Status**: ⚠️ Basic status bar working
- [x] Status bar messages
- [ ] Progress bars for long operations
- [ ] Error notifications
- [ ] Warning dialogs
- [ ] Success confirmations
- [ ] Tooltips on all controls

### Keyboard Shortcuts
**Status**: ❌ Not implemented
- [ ] Ctrl+O: Open/Load
- [ ] Ctrl+E: Export
- [ ] Ctrl+F: Search
- [ ] Ctrl+Left/Right: Navigate history
- [ ] F5: Refresh
- [ ] Esc: Clear selection

---

## 9. Quality of Life Features

### Performance
- [ ] Lazy loading for large corpora
- [ ] Thumbnail previews in browser
- [ ] Caching of rendered diagrams
- [ ] Background loading

### Accessibility
- [ ] High contrast mode
- [ ] Font size adjustment
- [ ] Screen reader support
- [ ] Keyboard-only navigation

### Help & Documentation
- [ ] Help menu
- [ ] Tooltips
- [ ] Context-sensitive help
- [ ] User guide integration
- [ ] Quick start tutorial

---

## Implementation Priority

### Phase 4a.1: Essential Features (Next)
**Priority: HIGH**
1. **Import System**: EGIF import for literature
2. **Export System**: EGIF, CGIF, full JSON export
3. **Metadata Editing**: Basic edit dialog
4. **History Comparison**: Compare two states

### Phase 4a.2: Core Enhancement
**Priority: MEDIUM**
1. **Search & Filter**: Corpus search
2. **UoD Operations**: Delete, duplicate, rename
3. **Visualization Options**: Layout controls
4. **Transformation Analysis**: View details

### Phase 4a.3: Polish & UX
**Priority: LOW**
1. **Keyboard Shortcuts**
2. **Statistics Dashboard**
3. **Help System**
4. **Accessibility Features**

---

## Testing Requirements

### Unit Tests
- [ ] Import parsers (EGIF, CGIF, JSON)
- [ ] Export generators
- [ ] Metadata validation
- [ ] Search/filter logic

### Integration Tests
- [ ] Load UoD → Edit → Save workflow
- [ ] Import → Display → Export roundtrip
- [ ] History navigation
- [ ] Metadata changes persistence

### Manual Tests
- [ ] UI responsiveness
- [ ] Error handling
- [ ] Large corpus performance
- [ ] Export format correctness

---

## Success Criteria

Organon is **COMPLETE** when:
- ✅ Users can import literature in multiple formats
- ✅ Users can export UoDs in all standard formats
- ✅ Users can edit all metadata fields
- ✅ Users can compare historical states
- ✅ Users can search and filter corpus
- ✅ Users can manage UoDs (delete, duplicate, rename)
- ✅ All operations have proper error handling
- ✅ Performance is acceptable for 100+ UoDs
- ✅ Integration tests pass
- ✅ User documentation exists

---

## Current Gap Analysis

| Feature Category | Completion | Critical Missing |
|------------------|------------|------------------|
| Viewing | 80% | State comparison |
| Import | 0% | All formats |
| Export | 20% | EGIF, CGIF, JSON |
| Metadata | 50% | Edit capability |
| History | 40% | Comparison, analysis |
| Corpus Mgmt | 30% | Search, operations |
| Visualization | 60% | Layout options |
| Integration | 30% | Agon, feedback |
| UX | 40% | Shortcuts, help |

**Overall Completion**: ~40%

---

## Recommended Next Steps

1. **Import/Export System** (highest priority)
   - Implement EGIF import for literature
   - Implement full export (EGIF, CGIF, JSON)
   - Test roundtrip for each format

2. **Metadata Management**
   - Create edit dialog
   - Add save functionality
   - Validate changes

3. **History Enhancement**
   - State comparison view
   - Transformation details
   - Export history

4. **Corpus Operations**
   - Search and filter
   - Delete with confirmation
   - Duplicate UoD

This will bring Organon to ~70% completion and provide the essential tools for corpus management.
