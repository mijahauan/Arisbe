# Architecture Rework: Hypergraph Mapping Correction

## Issue Identified
- Fundamental hypergraph mapping error in Phases 1-4
- Nodes/Edges mapped backwards (Predicates↔Entities)
- Phase 5B GUI built on flawed foundation

## Rework Plan
- Phase 1-2: Correct data structures
- Phase 3: Fix CLIF parsing
- Phase 4: Rebuild rendering system
- Phase 5: Return to GUI with solid foundation

## Branch Strategy
- feature/phase5b-pyside6-gui: Preserved GUI work (HALTED)
- rework/hypergraph-architecture: Architecture fixes (ACTIVE)

