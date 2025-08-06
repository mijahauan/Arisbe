"""
Canonical Arisbe Core - Standardized Mathematical Foundation

This module provides the canonical, standardized APIs for all EGI/EGDF operations.
All future extensions (CLIF, CGIF, LaTeX, web GUIs, NL interfaces) MUST use these APIs.

ARCHITECTURAL PRINCIPLE:
- Mathematical/Logical Core: Immutable, canonical operations
- Arbitrary/Visual Features: Extensible, export-specific features
- Strict separation ensures core logic remains uncontaminated

VERSION POLICY:
- Major version changes indicate breaking API changes
- Minor version changes add backward-compatible features
- Patch version changes fix bugs without API changes
"""

from typing import Dict, Set, List, Optional, Any, Type, Protocol, runtime_checkable
from dataclasses import dataclass
import sys
import os

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Core canonical imports
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from egif_parser_dau import EGIFParser
from egif_generator_dau import EGIFGenerator
from egdf_parser import EGDFParser, EGDFDocument

@dataclass(frozen=True)
class CanonicalAPIVersion:
    """Version information for canonical APIs."""
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def is_compatible_with(self, other: 'CanonicalAPIVersion') -> bool:
        """Check if this version is compatible with another version."""
        # Same major version indicates compatibility
        return self.major == other.major

# Current canonical API version
CANONICAL_API_VERSION = CanonicalAPIVersion(1, 0, 0)

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

@runtime_checkable
class CanonicalEGDFInterface(Protocol):
    """Canonical interface for EGDF operations."""
    
    def create_egdf_from_egi(self, egi: RelationalGraphWithCuts, layout_primitives: List[Any]) -> EGDFDocument:
        """Create EGDF document from canonical EGI and layout primitives."""
        ...
    
    def extract_egi_from_egdf(self, egdf_doc: EGDFDocument) -> RelationalGraphWithCuts:
        """Extract canonical EGI from EGDF document."""
        ...
    
    def validate_round_trip(self, original_egi: RelationalGraphWithCuts, egdf_doc: EGDFDocument) -> bool:
        """Validate that EGDF preserves EGI structure in round-trip."""
        ...

class CanonicalExtensionRegistry:
    """Registry for canonical extensions."""
    
    _parsers: Dict[str, Type] = {}
    _generators: Dict[str, Type] = {}
    _exporters: Dict[str, Type] = {}
    _validators: Dict[str, Type] = {}
    
    @classmethod
    def register_parser(cls, format_name: str, parser_class: Type):
        """Register a new format parser."""
        if not hasattr(parser_class, 'parse'):
            raise ValueError(f"Parser {parser_class} must implement 'parse' method")
        cls._parsers[format_name] = parser_class
        print(f"✅ Registered canonical parser: {format_name}")
    
    @classmethod
    def register_generator(cls, format_name: str, generator_class: Type):
        """Register a new format generator."""
        if not hasattr(generator_class, 'generate'):
            raise ValueError(f"Generator {generator_class} must implement 'generate' method")
        cls._generators[format_name] = generator_class
        print(f"✅ Registered canonical generator: {format_name}")
    
    @classmethod
    def register_exporter(cls, format_name: str, exporter_class: Type):
        """Register a new format exporter."""
        if not hasattr(exporter_class, 'export'):
            raise ValueError(f"Exporter {exporter_class} must implement 'export' method")
        cls._exporters[format_name] = exporter_class
        print(f"✅ Registered canonical exporter: {format_name}")
    
    @classmethod
    def get_parser(cls, format_name: str) -> Optional[Type]:
        """Get registered parser for format."""
        return cls._parsers.get(format_name)
    
    @classmethod
    def get_generator(cls, format_name: str) -> Optional[Type]:
        """Get registered generator for format."""
        return cls._generators.get(format_name)
    
    @classmethod
    def get_exporter(cls, format_name: str) -> Optional[Type]:
        """Get registered exporter for format."""
        return cls._exporters.get(format_name)
    
    @classmethod
    def list_formats(cls) -> Dict[str, List[str]]:
        """List all registered formats by category."""
        return {
            'parsers': list(cls._parsers.keys()),
            'generators': list(cls._generators.keys()),
            'exporters': list(cls._exporters.keys())
        }

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
    
    @classmethod
    def validate_extension(cls, extension_class: Type, extension_type: str) -> bool:
        """Validate that an extension follows the canonical contract."""
        required_methods = {
            'parser': ['parse'],
            'generator': ['generate'], 
            'exporter': ['export']
        }
        
        if extension_type not in required_methods:
            raise ValueError(f"Unknown extension type: {extension_type}")
        
        for method_name in required_methods[extension_type]:
            if not hasattr(extension_class, method_name):
                raise ValueError(f"Extension {extension_class} missing required method: {method_name}")
        
        # Check for API version compatibility
        if hasattr(extension_class, 'REQUIRED_API_VERSION'):
            required_version = extension_class.REQUIRED_API_VERSION
            if not CANONICAL_API_VERSION.is_compatible_with(required_version):
                raise ValueError(f"Extension requires API version {required_version}, but current is {CANONICAL_API_VERSION}")
        
        return True

# Create canonical wrapper classes for consistent API
class CanonicalEGDFParser:
    """Canonical wrapper for EGDFParser to provide consistent API."""
    
    def __init__(self):
        self.egdf_parser = EGDFParser()
    
    def parse(self, egdf_content: str) -> RelationalGraphWithCuts:
        """Parse EGDF content to canonical EGI."""
        egdf_doc = self.egdf_parser.parse_egdf(egdf_content)
        return self.egdf_parser.extract_egi_from_egdf(egdf_doc)
    
    def generate(self, egi: RelationalGraphWithCuts, layout_primitives: List[Any] = None) -> str:
        """Generate EGDF content from canonical EGI."""
        if layout_primitives is None:
            # Use basic layout generator if no primitives provided
            from egdf_parser import EGDFLayoutGenerator
            layout_gen = EGDFLayoutGenerator()
            layout_primitives = layout_gen.generate_layout_from_egi(egi)
        
        egdf_doc = self.egdf_parser.create_egdf_from_egi(egi, layout_primitives)
        return self.egdf_parser.egdf_to_json(egdf_doc)

class CanonicalEGIFGenerator:
    """Canonical wrapper for EGIFGenerator to provide consistent API."""
    
    def __init__(self):
        pass
    
    def generate(self, egi: RelationalGraphWithCuts) -> str:
        """Generate EGIF from canonical EGI."""
        generator = EGIFGenerator(egi)
        return generator.generate()

# Register core canonical implementations
CanonicalExtensionRegistry.register_parser("EGIF", EGIFParser)
CanonicalExtensionRegistry.register_generator("EGIF", CanonicalEGIFGenerator)
CanonicalExtensionRegistry.register_parser("EGDF", CanonicalEGDFParser)
CanonicalExtensionRegistry.register_generator("EGDF", CanonicalEGDFParser)

# Export canonical API
__all__ = [
    # Core classes
    'RelationalGraphWithCuts',
    'Vertex', 
    'Edge',
    'Cut',
    'ElementID',
    'EGIFParser',
    'EGIFGenerator', 
    'EGDFParser',
    'EGDFDocument',
    
    # Version management
    'CANONICAL_API_VERSION',
    'CanonicalAPIVersion',
    
    # Interfaces
    'CanonicalEGIInterface',
    'CanonicalEGDFInterface',
    
    # Extension framework
    'CanonicalExtensionRegistry',
    'CanonicalExtensionContract'
]

def get_canonical_info() -> Dict[str, Any]:
    """Get information about the canonical core."""
    return {
        'version': str(CANONICAL_API_VERSION),
        'registered_formats': CanonicalExtensionRegistry.list_formats(),
        'contract_rules': CanonicalExtensionContract.RULES,
        'core_classes': [
            'RelationalGraphWithCuts',
            'EGIFParser', 
            'EGIFGenerator',
            'EGDFParser'
        ]
    }

if __name__ == "__main__":
    print("🎯 CANONICAL ARISBE CORE")
    print("=" * 50)
    print(f"API Version: {CANONICAL_API_VERSION}")
    print(f"Registered Formats: {CanonicalExtensionRegistry.list_formats()}")
    print("✅ Canonical core initialized successfully")
