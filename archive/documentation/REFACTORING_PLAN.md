# Definitive Three-Pass Engine Refactoring Plan

## Critical Architectural Flaws Identified

1. **Pass 1 Conflation**: Dot positions ALL elements (should only size containers)
2. **Pass 2 Chaining**: d3-force uses dot hints (should start fresh)
3. **Port Miscalculation**: Ports added to dot input (should be calculated geometrically after)
4. **No True Bottom-Up**: Independent cut layouts (should propagate child sizes upward)

## Refactoring Strategy

### Phase 1: Fix Pass 1 (CRITICAL)
- Keep full dot input (vertices/edges for sizing) ✓
- Extract cluster geometry → KEEP ✓
- **REMOVE** `_extract_graphviz_positions()` call
- **REMOVE** `self.graphviz_positions` storage
- Add geometric port calculation AFTER Pass 1

### Phase 2: Rewrite Pass 2 (MAJOR)
- Remove ALL Graphviz hints from `_layout_cut()`
- Implement true recursive bottom-up in `_pass2_content()`
- Child cuts as fixed nodes in parent layout
- Start d3-force with NO initial positions

### Phase 3: Enhance Pass 3
- Integrate area-aware A* pathfinder
- Add validation logic
- Handle port-to-port routing

## Implementation Steps

1. Create backup of current engine
2. Apply Phase 1 fixes to existing file
3. Test Pass 1 (container sizing only)
4. Apply Phase 2 refactoring
5. Test Pass 2 (recursive layout)
6. Apply Phase 3 enhancements
7. Full tomos validation

## Testing Plan

- Simple flat sheet (no cuts)
- One cut with content
- Nested cuts (2-3 levels)
- Full tomos (15 graphs)
- Compare with previous output

