# Arisbe EG Works - Condensed Active Plan

## Current Priority: CGAL-Based Area Management System

### Critical Issue Identified
- Visual rendering problems stem from lack of precise area boundary awareness
- Need exact correspondence between Dau's logical areas and visual boundaries
- Current system lacks constraint-based positioning within areas

### Solution: Area-Based Spatial Modeling with CGAL

#### Core Principle
- **Logical areas** (from EGI) map to **visual areas** (bounded by cuts)
- **Movement within areas is arbitrary to logic** - enables visual optimization
- **Area boundaries are immutable** - preserves logical structure

#### Why CGAL?
- **Exact arithmetic** - no floating-point precision errors
- **Robust edge case handling** - touching boundaries, degenerate cuts, complex intersections
- **Proven reliability** - academic/industrial computational geometry standard

### Immediate Next Steps

#### Phase 1: CGAL Integration
- [ ] Install CGAL Python bindings
- [ ] Create CGALAreaManager class for exact area boundary management
- [ ] Implement exact polygon operations for area subtraction
- [ ] Test with Roberts Disjunction and nested quantifier examples

#### Phase 2: Area-Aware EGDF Generation
- [ ] Replace current positioning with area-constrained optimization
- [ ] Ensure elements stay within assigned logical areas
- [ ] Optimize visual positioning within area constraints
- [ ] Maintain 1.5px ligature clearance and visual separation

#### Phase 3: Interactive Constraints
- [ ] Enable drag-and-drop with area boundary enforcement
- [ ] Real-time constraint validation for user interactions
- [ ] Visual feedback for constraint violations

### Current Visual Issues Being Addressed
- Heavy line spacing (wide gaps at predicate boundaries)
- Line separation (continuous appearance of separate identity lines)
- Vertex positioning (respecting logical areas while optimizing visually)

### Architecture Requirements
- **Exact area boundaries** - cuts define precise available space
- **Hierarchical area model** - sheet → cuts → sub-cuts with exact geometry
- **Constraint enforcement** - impossible to violate area boundaries
- **Visual optimization** - elements positioned optimally within constraints

### Technical Stack
- **CGAL**: Computational geometry with exact arithmetic
- **Python bindings**: cgal-bindings package
- **Integration**: Area-aware EGDF generator with constraint system

---
*Condensed from 158K plan.md to fix update system*
*Original archived as plan_archive_2025-08-13.md*
