# Core Dau Formalism Architecture Documentation

## Executive Summary

This document describes the integrated architecture for the core Dau formalism implementation in Arisbe. The architecture provides a unified, coherent interface to all essential Dau formalism components while maintaining mathematical rigor and theoretical foundations from chapters 11-21.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Core Dau Formalism Manager                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   EGI Core      │ │ Linear Forms    │ │ Transformations │   │
│  │   Data Model    │ │ Integration     │ │ Rules Engine    │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Chapters 11-21  │ │ Persistence &   │ │ Validation &    │   │
│  │ Integration     │ │ History Mgmt    │ │ Testing Suite   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Coherence Framework                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Function        │ │ Quality Gates   │ │ Integration     │   │
│  │ Registry        │ │ & Monitoring    │ │ Interfaces      │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. CoreDauFormalismManager (`src/core_dau_formalism.py`)

**Purpose**: Central manager providing unified access to all Dau formalism operations.

**Key Responsibilities**:
- EGI creation and validation
- Linear form parsing/generation (EGIF, CGIF, CLIF, FOPL)
- Transformation rule application
- State management and persistence
- Comprehensive status reporting

**Primary Interface Methods**:
```python
# EGI Operations
create_egi(specification: Dict[str, Any]) -> RelationalGraphWithCuts
validate_egi(egi: RelationalGraphWithCuts) -> Dict[str, Any]

# Linear Form Integration
parse_linear_form(text: str, format_type: LinearFormat) -> RelationalGraphWithCuts
generate_linear_form(egi: RelationalGraphWithCuts, format_type: LinearFormat) -> str
round_trip_test(egi: RelationalGraphWithCuts, format_type: LinearFormat) -> Dict[str, Any]

# Transformation Operations
apply_transformation(egi: RelationalGraphWithCuts, rule_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]
validate_transformation_sequence(transformations: List[Dict[str, Any]]) -> Dict[str, Any]

# State Management
save_state(identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool
load_state(identifier: str) -> bool
get_comprehensive_status() -> Dict[str, Any]
```

### 2. DauChaptersIntegrationManager (`src/dau_chapters_integration.py`)

**Purpose**: Ensures compliance and integration across Dau formalism chapters 11-21.

**Chapter Coverage**:
- **Chapter 11**: Basic EG structure (V, E, ν, ⊤, Cut, area, rel)
- **Chapter 12**: Cut semantics and nesting hierarchy
- **Chapter 13**: Variable binding and scoping rules
- **Chapter 14**: Predicate logic correspondence
- **Chapter 15**: Spatial correspondence principles
- **Chapter 16**: Polarity and area calculations
- **Chapter 17**: Transformation rule foundations
- **Chapter 18**: Linear form translations
- **Chapter 19**: Semantic evaluation
- **Chapter 20**: Syntactic equivalence
- **Chapter 21**: Complete transformation system

**Key Methods**:
```python
validate_chapter_11_compliance(egi: RelationalGraphWithCuts) -> ChapterComplianceResult
validate_chapter_17_compliance(egi: RelationalGraphWithCuts, transformations: List[Dict[str, Any]]) -> ChapterComplianceResult
validate_chapter_18_compliance(egi: RelationalGraphWithCuts, linear_forms: Dict[str, str]) -> ChapterComplianceResult
validate_chapter_21_compliance(egi: RelationalGraphWithCuts, transformation_sequence: List[Dict[str, Any]]) -> ChapterComplianceResult
validate_full_integration(egi: RelationalGraphWithCuts, linear_forms: Optional[Dict[str, str]], transformations: Optional[List[Dict[str, Any]]]) -> IntegratedValidationResult
```

### 3. CoherenceRegistry (`src/coherence_registry.py`)

**Purpose**: Comprehensive registry of all functions and components for easy discovery and reference.

**Registry Categories**:
- **CORE_DATA**: EGI structures, vertices, edges, cuts
- **TRANSFORMATION**: All transformation rules and contexts
- **LINEAR_FORM**: Parsers and generators for all formats
- **VALIDATION**: Compliance and equivalence checking
- **PERSISTENCE**: History and state management
- **INTEGRATION**: Cross-system coordination interfaces
- **UTILITY**: Helper functions and calculations

**Search and Discovery**:
```python
search_functions(query: str, category: Optional[ComponentCategory] = None) -> List[RegisteredFunction]
search_components(query: str, category: Optional[ComponentCategory] = None) -> List[RegisteredComponent]
get_dau_chapter_functions(chapter: str) -> List[RegisteredFunction]
generate_function_reference() -> str
```

## Data Flow Architecture

### EGI Lifecycle Management

```
1. Creation/Import
   ├── Specification → create_egi() → RelationalGraphWithCuts
   ├── EGIF Text → parse_linear_form(EGIF) → RelationalGraphWithCuts
   ├── CGIF Text → parse_linear_form(CGIF) → RelationalGraphWithCuts
   ├── CLIF Text → parse_linear_form(CLIF) → RelationalGraphWithCuts
   └── FOPL Text → parse_linear_form(FOPL) → RelationalGraphWithCuts

2. Validation
   ├── Structure Validation (Chapter 11)
   ├── Cut Semantics (Chapter 12)
   ├── Variable Scoping (Chapter 13)
   ├── Predicate Logic (Chapter 14)
   ├── Spatial Correspondence (Chapter 15)
   ├── Polarity Calculations (Chapter 16)
   └── Cross-Chapter Consistency

3. Transformation
   ├── Precondition Checking (Chapter 17)
   ├── Rule Application (IT+, IT-, INS, ERA, DC+, DC-)
   ├── Semantic Equivalence Validation
   └── History Recording

4. Export/Persistence
   ├── EGI → generate_linear_form(EGIF) → EGIF Text
   ├── EGI → generate_linear_form(CGIF) → CGIF Text
   ├── EGI → generate_linear_form(CLIF) → CLIF Text
   ├── EGI → generate_linear_form(FOPL) → FOPL Text
   └── State → save_state() → Persistent Storage
```

### Validation Pipeline

```
Input EGI
    │
    ▼
┌─────────────────────────┐
│ Chapter 11: Structure   │ ← 6+1 Components (V, E, ν, ⊤, Cut, area, rel)
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Chapter 12: Cut Nesting │ ← Hierarchical Index Validation
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Chapter 13: Variables   │ ← Scoping and Binding Rules
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Chapter 14: Predicates  │ ← Logic Correspondence
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Cross-Chapter Checks    │ ← Consistency Validation
└─────────────────────────┘
    │
    ▼
Validation Results
```

## Integration Points

### 1. Linear Form Integration

All linear formats are integrated through standardized interfaces:

- **EGIF**: Native Dau format with full fidelity
- **CGIF**: Conceptual Graph Interchange Format
- **CLIF**: Common Logic Interchange Format  
- **FOPL**: First-Order Predicate Logic

**Round-trip Fidelity**: All formats support bidirectional conversion with semantic preservation validation.

### 2. Transformation Rules Integration

Six core transformation rules fully integrated:

- **IT+ (Iteration)**: Copy subgraph to different area
- **IT- (Deiteration)**: Remove duplicate subgraph
- **INS (Insertion)**: Add element to negative area
- **ERA (Erasure)**: Remove element from positive area
- **DC+ (Double Cut Insertion)**: Add nested double cut
- **DC- (Double Cut Erasure)**: Remove nested double cut

Each rule includes:
- Precondition validation
- Semantic equivalence checking
- History tracking
- Rollback capability

### 3. Testing Framework Integration

Comprehensive test suite integrated with coherence framework:

- **18 Test Specifications** covering all categories
- **Logical Equivalence Tests**: Transformation sequence validation
- **Transformation Soundness Tests**: Rule application validation
- **Translation Fidelity Tests**: Round-trip format testing
- **Dau Compliance Tests**: Chapter-specific validation

## Usage Patterns

### Basic EGI Operations

```python
from src.core_dau_formalism import get_dau_formalism_manager

# Get manager instance
manager = get_dau_formalism_manager()

# Create EGI from specification
egi = manager.create_egi({
    "vertices": [{"id": "x", "is_generic": True}],
    "edges": [{"id": "human", "relation": "Human"}],
    "ligatures": [{"edge_id": "human", "vertex_ids": ["x"]}]
})

# Validate EGI
validation = manager.validate_egi(egi)
print(f"Valid: {validation['overall_valid']}")

# Generate EGIF
egif_text = manager.generate_linear_form(egi, LinearFormat.EGIF)

# Test round-trip fidelity
roundtrip = manager.round_trip_test(egi, LinearFormat.EGIF)
print(f"Round-trip successful: {roundtrip['success']}")
```

### Transformation Operations

```python
# Apply iteration rule
result = manager.apply_transformation(egi, "iteration", {
    "source_area": "sheet",
    "target_area": "cut1",
    "subgraph_elements": ["x", "human"]
})

if result["success"]:
    transformed_egi = result["transformed_egi"]
    print("Transformation successful")
else:
    print(f"Transformation failed: {result['error_message']}")
```

### Chapter Compliance Validation

```python
from src.dau_chapters_integration import get_dau_chapters_manager

chapters_manager = get_dau_chapters_manager()

# Validate full integration across all chapters
integration_result = chapters_manager.validate_full_integration(
    egi=egi,
    linear_forms={"egif": egif_text, "cgif": cgif_text},
    transformations=[{"rule": "iteration", "parameters": {...}}]
)

print(f"Overall compliant: {integration_result.overall_compliant}")
for chapter, result in integration_result.chapter_results.items():
    print(f"{chapter.value}: {result.compliant}")
```

### Function Discovery

```python
from src.coherence_registry import get_coherence_registry

registry = get_coherence_registry()

# Search for polarity-related functions
polarity_functions = registry.search_functions("polarity")
for func in polarity_functions:
    print(f"{func.name}: {func.description}")

# Get all transformation functions
transform_functions = registry.get_functions_by_category(ComponentCategory.TRANSFORMATION)

# Generate complete function reference
reference_doc = registry.generate_function_reference()
```

## Quality Assurance

### Automated Validation

The architecture includes comprehensive automated validation:

1. **Pre-commit Hooks**: Quality gates prevent regression
2. **Continuous Testing**: EGI integrity tests run automatically
3. **Chapter Compliance**: Dau formalism validation on every operation
4. **Cross-Component Consistency**: Integration validation across all components

### Monitoring and Reporting

```python
# Get comprehensive system status
status = manager.get_comprehensive_status()

# Check component health
health = status["component_health"]
for component, healthy in health.items():
    print(f"{component}: {'✅' if healthy else '❌'}")

# Monitor transformation history
history = status["transformation_history"]
print(f"Total transformations: {history['total_transformations']}")
print(f"Success rate: {history['successful_transformations'] / history['total_transformations'] * 100:.1f}%")
```

## Extension Points

### Adding New Linear Formats

1. Implement parser class with `parse(text: str) -> RelationalGraphWithCuts`
2. Implement generator class with `generate(egi: RelationalGraphWithCuts) -> str`
3. Register in `CoreDauFormalismManager._init_parsers_generators()`
4. Add to `LinearFormat` enum
5. Update registry and tests

### Adding New Transformation Rules

1. Extend `FormalTransformationRule` abstract base class
2. Implement `apply()`, `is_valid()`, and `get_preconditions()` methods
3. Register in `CoreDauFormalismManager._init_transformation_rules()`
4. Add chapter compliance validation
5. Update registry and test specifications

### Adding New Validation Chapters

1. Implement chapter-specific validation in `DauChaptersIntegrationManager`
2. Add cross-chapter consistency rules
3. Update `validate_full_integration()` method
4. Add test specifications for new chapter
5. Update documentation and registry

## Performance Considerations

- **O(1) Polarity Calculations**: HierarchicalIndex provides constant-time lookups
- **Lazy Validation**: Validation only performed when explicitly requested
- **Incremental History**: Only changed components tracked in transformation history
- **Cached Parsing**: Parsed linear forms cached to avoid re-parsing
- **Batch Operations**: Multiple transformations can be applied in sequence efficiently

## Security and Reliability

- **Immutable Data Structures**: Core EGI components use frozensets and frozendict
- **Validation Gates**: All operations validated before execution
- **Rollback Capability**: Failed transformations leave original EGI unchanged
- **Error Isolation**: Component failures don't affect other subsystems
- **Comprehensive Logging**: All operations logged for debugging and audit

## Conclusion

This integrated architecture provides a coherent, mathematically rigorous foundation for all Dau formalism operations in Arisbe. The system maintains theoretical correctness while providing practical functionality for EGI manipulation, transformation, and validation.

The architecture supports the goal of keeping the "coherent fullness of data and function" easily accessible and referenceable, enabling confident development of GUI and CLI interfaces that interact with complete, validated functionality.
