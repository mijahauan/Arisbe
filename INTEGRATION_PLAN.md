# Arisbe Codebase Integration Plan

## Executive Summary
The coherence analysis revealed 2,710 issues, primarily from disconnected code sections (2,705 orphans). This indicates the codebase grew beyond context capacity, creating isolated subsystems that don't communicate.

## Critical Integration Priorities

### Phase 1: Core Interface Standardization (HIGH PRIORITY)

#### 1.1 Polarity Function Consolidation
**Problem**: 8 different polarity calculation implementations with incompatible interfaces
**Solution**: 
- Establish `HierarchicalIndex.get_polarity(area_id: str) -> AreaPolarity` as canonical
- Deprecate manual traversal implementations
- Create adapter functions for legacy interfaces

**Files to Integrate**:
- `formal_transformation_rules.py:75` - `calculate_area_polarity`
- `egif_transformation_interface.py:107` - `_calculate_area_polarity`
- `chapter21_diagram_engine.py:458` - `_calculate_area_polarity_and_depth` (already optimized)

#### 1.2 Transformation Interface Standardization
**Problem**: 129 files with incompatible transformation interfaces
**Solution**:
- Establish `TransformationContext` as standard parameter object
- Create unified `apply_transformation(context: TransformationContext) -> TransformationResult`
- Implement adapter pattern for legacy interfaces

### Phase 2: Reconnect Dau Treatise Implementations (HIGH PRIORITY)

#### 2.1 Integrate Theorem Correspondence Tests
**Current State**: `DauTheoremCorrespondenceTests` completely orphaned
**Integration Points**:
- Connect to `formal_transformation_rules.py` for validation
- Use `HierarchicalIndex` for nesting level calculations
- Integrate with GUI test runner

**Action Items**:
```python
# In formal_transformation_rules.py
from dau_theorem_correspondence_tests import DauTheoremCorrespondenceTests

class FormalTransformationRule:
    def validate_theoretical_compliance(self):
        return DauTheoremCorrespondenceTests().run_all_theorem_tests()
```

#### 2.2 Connect Semantic Evaluation Engine
**Current State**: `dau_semantic_evaluation_engine.py` isolated
**Integration Points**:
- Connect to transformation validation pipeline
- Use for soundness verification in GUI
- Integrate with corpus validation

### Phase 3: Unify Data Persistence Models (MEDIUM PRIORITY)

#### 3.1 Consolidate History Systems
**Problem**: Multiple disconnected history tracking systems
**Files**:
- `egi_transformation_history.py`
- `history_persistence.py` 
- `interactive_transformer_with_history.py`

**Solution**: Create unified `HistoryManager` that all systems use

#### 3.2 Integrate Corpus Management
**Problem**: `CorpusManager` and related classes have no integration
**Solution**:
- Connect to GUI `Organon` tab
- Integrate with transformation history
- Use for graph persistence

### Phase 4: Parser/Generator Coordination (MEDIUM PRIORITY)

#### 4.1 Multi-Format Synchronization
**Current State**: EGIF, CGIF, CLIF parsers/generators work independently
**Integration Points**:
- Create `FormatSynchronizer` in `chapter21_diagram_engine.py`
- Ensure translation consistency across formats
- Validate syntactic equivalence

## Implementation Strategy

### Step 1: Create Integration Interfaces
```python
# New file: src/integration_interfaces.py
from abc import ABC, abstractmethod
from typing import Protocol

class PolarityProvider(Protocol):
    def get_polarity(self, area_id: str) -> AreaPolarity: ...

class TransformationValidator(Protocol):
    def validate_transformation(self, context: TransformationContext) -> bool: ...

class HistoryTracker(Protocol):
    def record_transformation(self, before: EGI, after: EGI, rule: str) -> None: ...
```

### Step 2: Implement Adapter Pattern
```python
# Adapt legacy interfaces to new standards
class LegacyPolarityAdapter:
    def __init__(self, hierarchical_index: HierarchicalIndex):
        self.index = hierarchical_index
    
    def calculate_area_polarity(self, egi, area_id):
        # Legacy interface -> new implementation
        return self.index.get_polarity(str(area_id))
```

### Step 3: Progressive Integration
1. **Week 1**: Standardize polarity interfaces
2. **Week 2**: Connect Dau theorem tests
3. **Week 3**: Unify history systems
4. **Week 4**: Integrate corpus management

## Coherence Maintenance System

### Automated Integration Checks
```bash
# Add to CI/CD pipeline
python tools/coherence_analyzer.py
if [ $? -ne 0 ]; then
    echo "Coherence issues detected - review before merge"
    exit 1
fi
```

### Integration Documentation
- Document all integration points in `ARCHITECTURE_MAP.md`
- Maintain dependency graph
- Update when adding new subsystems

## Success Metrics
- **Orphaned code**: Reduce from 2,705 to < 100
- **Interface inconsistencies**: Reduce from 5 to 0
- **Test coverage**: Increase integration test coverage to 80%
- **Documentation**: All major subsystems documented with integration points

## Risk Mitigation
- **Backward compatibility**: Use adapter pattern to maintain existing interfaces
- **Incremental integration**: Phase implementation to avoid breaking changes
- **Validation**: Run full test suite after each integration phase
- **Rollback plan**: Maintain git branches for each integration phase
