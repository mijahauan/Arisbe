# Canonical Core Standardization Strategy

## **OBJECTIVE: CANONICAL EGI/EGDF FOUNDATION**

Establish the EGI/EGDF core as the **canonical, standardized mathematical foundation** for all future extensions (CLIF, CGIF, LaTeX, web GUIs, natural language interfaces, etc.).

## **CORE CANONICALIZATION REQUIREMENTS**

### **1. Mathematical/Logical Core (Immutable)**
These components must remain **canonical and unchanging**:

```
EGI Core:
├── RelationalGraphWithCuts (egi_core_dau.py)
├── Vertex, Edge, Cut, ElementID classes
├── ν (nu) mapping and κ (kappa) labeling functions
├── Area containment and cut nesting logic
├── Immutable operations and transformations

EGIF Interface:
├── EGIFParser (egif_parser_dau.py)
├── EGIFGenerator (egif_generator_dau.py)
├── Sowa-compliant syntax and semantics
├── Round-trip integrity guarantees

EGDF Interface:
├── EGDFParser (egdf_parser.py)
├── EGDF document structure and metadata
├── Spatial primitive contracts
├── JSON/YAML serialization
```

### **2. Arbitrary/Visual Features (Extensible)**
These components support **Peircean "arbitrary" features** without affecting core logic:

```
EGDF Visual Extensions:
├── Layout hints and positioning preferences
├── Styling and rendering preferences
├── Export-specific formatting options
├── GUI interaction metadata
├── Historical diagram reproduction data

Export Extensions:
├── LaTeX-specific formatting
├── PDF rendering options
├── Web GUI styling hints
├── Print layout specifications
```

## **CANONICALIZATION IMPLEMENTATION STRATEGY**

### **Phase 1: API Documentation and Contracts**

#### **1.1 Formal API Documentation**
```bash
# Generate comprehensive API documentation
pip install sphinx sphinx-autodoc-typehints
sphinx-quickstart docs/api
sphinx-apidoc -o docs/api/source src/
```

**Target Files for Documentation:**
- `src/egi_core_dau.py` - Core EGI classes and operations
- `src/egif_parser_dau.py` - EGIF parsing interface
- `src/egif_generator_dau.py` - EGIF generation interface
- `src/egdf_parser.py` - EGDF document interface
- `src/graphviz_layout_engine_v2.py` - Layout engine interface

#### **1.2 API Contract Enforcement**
```python
# Example canonical API contract
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@runtime_checkable
class CanonicalEGIInterface(Protocol):
    """Canonical interface for EGI operations."""
    
    def parse_egif(self, egif_text: str) -> RelationalGraphWithCuts:
        """Parse EGIF to canonical EGI representation."""
        ...
    
    def generate_egif(self, egi: RelationalGraphWithCuts) -> str:
        """Generate EGIF from canonical EGI representation."""
        ...
    
    def validate_structure(self, egi: RelationalGraphWithCuts) -> bool:
        """Validate EGI structural integrity."""
        ...

@dataclass(frozen=True)
class CanonicalAPIVersion:
    """Version information for canonical APIs."""
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

CANONICAL_API_VERSION = CanonicalAPIVersion(1, 0, 0)
```

### **Phase 2: Core Standardization**

#### **2.1 Canonical Module Structure**
```
src/canonical/
├── __init__.py                 # Canonical API exports
├── egi_core.py                 # Canonical EGI classes
├── egif_interface.py           # Canonical EGIF operations
├── egdf_interface.py           # Canonical EGDF operations
├── contracts.py                # API contracts and validation
├── version.py                  # Version management
└── exceptions.py               # Canonical exception hierarchy
```

#### **2.2 Canonical Import Pattern**
```python
# All future extensions must use this pattern
from arisbe.canonical import (
    RelationalGraphWithCuts,
    EGIFParser,
    EGIFGenerator,
    EGDFDocument,
    CanonicalAPIVersion
)

# Version checking for compatibility
from arisbe.canonical import CANONICAL_API_VERSION
assert CANONICAL_API_VERSION.major == 1, "Incompatible API version"
```

#### **2.3 Separation of Concerns**
```python
# Mathematical/Logical Core (IMMUTABLE)
class RelationalGraphWithCuts:
    """Canonical EGI representation - NEVER modify interface."""
    
    # Core mathematical operations
    def get_area(self, context_id: ElementID) -> Set[ElementID]: ...
    def get_nu_mapping(self, edge_id: ElementID) -> List[ElementID]: ...
    def validate_containment(self) -> bool: ...

# Arbitrary/Visual Features (EXTENSIBLE)
class EGDFVisualExtensions:
    """Extensible visual features - safe to modify/extend."""
    
    layout_hints: Dict[str, Any]
    styling_preferences: Dict[str, Any]
    export_metadata: Dict[str, Any]
    gui_interaction_data: Dict[str, Any]
```

### **Phase 3: Extension Framework**

#### **3.1 Extension Registration System**
```python
# Extension registry for new formats/interfaces
class CanonicalExtensionRegistry:
    """Registry for canonical extensions."""
    
    _parsers: Dict[str, Type[CanonicalParser]] = {}
    _generators: Dict[str, Type[CanonicalGenerator]] = {}
    _exporters: Dict[str, Type[CanonicalExporter]] = {}
    
    @classmethod
    def register_parser(cls, format_name: str, parser_class: Type):
        """Register a new format parser."""
        cls._parsers[format_name] = parser_class
    
    @classmethod
    def register_exporter(cls, format_name: str, exporter_class: Type):
        """Register a new format exporter."""
        cls._exporters[format_name] = exporter_class

# Usage for new extensions
@CanonicalExtensionRegistry.register_parser("CLIF")
class CLIFParser(CanonicalParser):
    def parse(self, clif_text: str) -> RelationalGraphWithCuts:
        # Must return canonical EGI
        pass

@CanonicalExtensionRegistry.register_exporter("LaTeX")
class LaTeXExporter(CanonicalExporter):
    def export(self, egdf_doc: EGDFDocument) -> str:
        # Can use arbitrary visual features
        pass
```

#### **3.2 Developer Guidelines**
```python
# Mandatory developer contract for extensions
class CanonicalExtensionContract:
    """Contract that all extensions must follow."""
    
    RULES = [
        "MUST use canonical EGI as the mathematical foundation",
        "MUST NOT modify core EGI classes or interfaces",
        "MUST preserve round-trip integrity through EGI",
        "MAY use EGDF arbitrary features for visual/export purposes",
        "MUST validate against canonical test suite",
        "MUST declare API version compatibility"
    ]
```

## **IMPLEMENTATION ROADMAP**

### **Immediate Actions (Week 1)**
1. **Audit Current Core**
   - Identify all core mathematical/logical components
   - Document current API surfaces and dependencies
   - Create baseline test suite for canonical behavior

2. **Create Canonical Module Structure**
   - Move core components to `src/canonical/`
   - Implement version management and contracts
   - Add comprehensive API documentation

3. **Establish API Contracts**
   - Add runtime validation decorators
   - Implement canonical exception hierarchy
   - Create extension registration system

### **Short-term Goals (Month 1)**
1. **Freeze Core APIs**
   - Lock down EGI/EGIF/EGDF interfaces
   - Implement semantic versioning
   - Add backward compatibility guarantees

2. **Separate Arbitrary Features**
   - Move visual/layout features to extensible layer
   - Ensure core logic is unaffected by visual changes
   - Add validation to prevent core contamination

3. **Create Extension Framework**
   - Build registration system for new formats
   - Create developer guidelines and templates
   - Add automated compliance checking

### **Long-term Vision (Months 2-6)**
1. **Extension Development**
   - CLIF/CGIF translators using canonical APIs
   - LaTeX exporter with arbitrary visual features
   - Web GUI using canonical pipeline
   - Natural language interface

2. **Quality Assurance**
   - Comprehensive test coverage for canonical core
   - Automated regression testing
   - Performance benchmarking
   - Documentation maintenance

## **SUCCESS CRITERIA**

### **Canonical Core Achieved When:**
- ✅ All mathematical/logical operations use identical APIs
- ✅ Round-trip integrity guaranteed through canonical EGI
- ✅ Extensions cannot contaminate core logic
- ✅ API documentation is comprehensive and current
- ✅ Version management prevents compatibility issues
- ✅ Developer guidelines ensure consistent extensions

### **Extension Framework Achieved When:**
- ✅ New formats (CLIF, CGIF) integrate seamlessly
- ✅ Export systems (LaTeX, PDF) use arbitrary features safely
- ✅ GUI systems use canonical pipeline exclusively
- ✅ Natural language interfaces preserve mathematical meaning
- ✅ All extensions validate against canonical test suite

## **QUALITY GATES**

### **Before Any Extension Development:**
1. Core API documentation must be complete
2. Canonical test suite must pass 100%
3. API contracts must be enforced with runtime validation
4. Separation between core/arbitrary must be validated
5. Version management must be operational

### **Before Extension Release:**
1. Must use canonical APIs exclusively
2. Must preserve EGI round-trip integrity
3. Must pass canonical compliance tests
4. Must declare API version compatibility
5. Must not affect core mathematical behavior

This canonicalization strategy ensures that the EGI/EGDF core becomes the unambiguous, standardized foundation for all future development while preserving the flexibility for arbitrary visual features and diverse extension development.
