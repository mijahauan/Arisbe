# Frontend Architecture Assessment

## Current State Analysis

### Existing PySide6-Based Implementation
**Files Examined:**
- `src/demo_constraint_qt.py` - Qt-based constraint demo
- `src/pyside6_canvas.py` - PySide6 canvas implementation  
- `src/arisbe_gui.py` - Main Tkinter-based GUI

### Architecture Issues Identified

#### 1. **Mixed UI Frameworks**
- **Problem**: Current codebase mixes Tkinter (`arisbe_gui.py`) and PySide6 (`demo_constraint_qt.py`)
- **Impact**: Inconsistent user experience, maintenance complexity, integration difficulties

#### 2. **Canvas Rendering Failures** 
- **Problem**: PySide6Canvas has fundamental API errors causing segmentation faults
- **Evidence**: `QPointF expected at most 2 arguments, got 5` crashes
- **Impact**: Cannot reliably render diagrams

#### 3. **Pipeline Integration Gaps**
- **Problem**: Existing GUI doesn't integrate with our solidified Graphviz layout engine
- **Evidence**: Demo uses `ConstraintLayoutIntegration` (deprecated), not `GraphvizLayoutEngine`
- **Impact**: Cannot leverage our proven layout pipeline

#### 4. **Missing Core Architecture**
- **Problem**: Current implementations lack the required three-section structure
- **Missing**: Proper Bullpen/Browser/Endoporeutic Game separation
- **Missing**: Warmup/Practice mode distinction in Bullpen

## Recommendation: Start From Scratch

### Why Retrofit Is Impractical

1. **Fundamental Canvas Issues**: PySide6Canvas implementation has deep API problems requiring complete rewrite
2. **Architecture Mismatch**: Current GUI doesn't match required three-section design
3. **Pipeline Incompatibility**: Existing rendering doesn't work with our proven Graphviz pipeline
4. **Framework Confusion**: Mixed Tkinter/PySide6 creates maintenance nightmare

### Proposed New Architecture

#### **Core Design Principles**
1. **Single UI Framework**: Pure PySide6 for professional quality
2. **Clean Pipeline Integration**: Direct integration with proven Graphviz layout engine
3. **Proper Three-Section Structure**: Bullpen, Browser, Endoporeutic Game
4. **Mode-Aware Bullpen**: Clear Warmup/Practice mode distinction

#### **Main Application Structure**
```
ArisbeMainWindow (QMainWindow)
├── QTabWidget (three main sections)
│   ├── BullpenTab (QWidget)
│   │   ├── ModeSelector (Warmup/Practice)
│   │   ├── ElementPalette (QToolBar)
│   │   └── DiagramCanvas (Custom QWidget)
│   ├── BrowserTab (QWidget)
│   │   ├── CorpusExplorer (QTreeWidget)
│   │   └── ExampleViewer (Custom QWidget)
│   └── EndoporeuticGameTab (QWidget)
│       ├── GameControls (QWidget)
│       └── GameCanvas (Custom QWidget)
└── StatusBar (QStatusBar)
```

#### **Diagram Rendering Strategy**
1. **Custom QWidget Canvas**: Replace problematic PySide6Canvas with clean custom implementation
2. **Direct QPainter Integration**: Use Qt's native painting system directly
3. **Pipeline Contract**: Implement proper contracts for Graphviz layout → Qt rendering
4. **Dau Convention Compliance**: Ensure heavy lines, proper cuts, predicate text rendering

#### **Integration Points**
1. **Layout Engine**: Direct integration with `GraphvizLayoutEngine`
2. **EGIF Parser**: Use proven `parse_egif` for input processing
3. **Corpus System**: Load examples from corpus directory
4. **Contract Validation**: Use existing API contract system

### Implementation Strategy

#### **Phase 1: Core Canvas (Immediate Priority)**
- Create new `QtDiagramCanvas` with proper QPainter integration
- Implement Dau-compliant rendering (heavy lines, fine cuts, predicate text)
- Validate against simple EGIF examples
- **Success Criteria**: Visually correct rendering of basic EG patterns

#### **Phase 2: Main Application Shell**
- Implement three-tab structure (Bullpen, Browser, Endoporeutic Game)
- Create mode selector for Bullpen (Warmup/Practice)
- Basic navigation and layout
- **Success Criteria**: Professional UI with proper section separation

#### **Phase 3: Bullpen Integration**
- Integrate QtDiagramCanvas with Bullpen tab
- Implement element palette and selection system
- Connect to Graphviz layout pipeline
- **Success Criteria**: Can load and display EGIF examples correctly

#### **Phase 4: Browser and Game Tabs**
- Corpus integration for Browser tab
- Basic Endoporeutic Game framework
- Cross-tab communication
- **Success Criteria**: Complete application with all three sections functional

## Conclusion

**Recommendation: Start from scratch with new PySide6-based architecture**

**Rationale:**
1. Current implementations have fundamental flaws that would require complete rewrites anyway
2. New architecture can be designed specifically for our proven pipeline
3. Clean implementation will be more maintainable and extensible
4. Opportunity to implement proper Dau convention compliance from the ground up

**Next Steps:**
1. Create new `QtDiagramCanvas` with proper rendering
2. Validate basic diagram display before building full application
3. Implement three-section architecture incrementally
4. Maintain focus on accurate diagram rendering as top priority
