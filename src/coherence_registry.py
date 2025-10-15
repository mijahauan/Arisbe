"""
Coherence Registry - Central Function and Component Registry

This module maintains a comprehensive, searchable registry of all core Dau formalism
functions and components, enabling easy discovery and reference of functionality
across the entire codebase.
"""

from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import inspect
import logging
from pathlib import Path

# Import all core components for registration
from .core_dau_formalism import CoreDauFormalismManager, LinearFormat
from .egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from .formal_transformation_rules import (
    FormalTransformationRule, IterationRule, DeiterationRule,
    InsertionRule, DoubleCutErasureRule, DoubleCutInsertionRule,
    ErasureRule, TransformationContext, AreaPolarity
)
from .hierarchical_index import HierarchicalIndex
from .integration_interfaces import (
    PolarityProvider, TransformationValidator, HistoryTracker,
    IntegrationManager, IntegrationContext
)

# New components added 2025-10-01 to 2025-10-02
from .diagram_controller import DiagramController, CommandExecutor
from .definitive_egi_layout_engine import DefinitiveEGILayoutEngine, LayoutDTO
from .graphviz_svg_renderer import GraphvizSVGRenderer
from .graph_entity import GraphEntity, EntityMetadata, EntityType, EntityCategory
from .entity_storage import EntityStorageManager, LRUCache
from .style_loader import StyleLoader, StyleSpecification


class ComponentCategory(Enum):
    """Categories of registered components."""
    CORE_DATA = "core_data"
    TRANSFORMATION = "transformation"
    LINEAR_FORM = "linear_form"
    VALIDATION = "validation"
    PERSISTENCE = "persistence"
    INTEGRATION = "integration"
    UTILITY = "utility"
    CORPUS_MANAGEMENT = "corpus_management"
    VIEW_MANAGEMENT = "view_management"
    SPATIAL_LAYOUT = "spatial_layout"
    EXPORT_MANAGEMENT = "export_management"
    # Added 2025-10-02
    DIAGRAM_CONTROL = "diagram_control"
    ENTITY_STORAGE = "entity_storage"
    GUI_COMPONENT = "gui_component"
    RENDERING = "rendering"
    STYLE_SYSTEM = "style_system"


class FunctionType(Enum):
    """Types of registered functions."""
    CONSTRUCTOR = "constructor"
    PARSER = "parser"
    GENERATOR = "generator"
    TRANSFORMER = "transformer"
    VALIDATOR = "validator"
    EVALUATOR = "evaluator"
    UTILITY = "utility"
    FACTORY = "factory"


@dataclass
class RegisteredFunction:
    """Registry entry for a function."""
    name: str
    function: Callable
    category: ComponentCategory
    function_type: FunctionType
    description: str
    parameters: List[str]
    return_type: Optional[Type]
    dau_chapter_refs: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    related_functions: List[str] = field(default_factory=list)


@dataclass
class RegisteredComponent:
    """Registry entry for a component/class."""
    name: str
    component_class: Type
    category: ComponentCategory
    description: str
    key_methods: List[str]
    dau_chapter_refs: List[str] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)


class CoherenceRegistry:
    """
    Central registry for all Dau formalism functions and components.
    
    Provides searchable access to:
    - All EGI construction and manipulation functions
    - Linear form parsing/generation capabilities
    - Transformation rule implementations
    - Validation and compliance checking functions
    - Integration interfaces and utilities
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Registry storage
        self.functions: Dict[str, RegisteredFunction] = {}
        self.components: Dict[str, RegisteredComponent] = {}
        self.categories: Dict[ComponentCategory, List[str]] = {cat: [] for cat in ComponentCategory}
        
        # Initialize registry with core components
        self._register_core_components()
        self._register_core_functions()
        self._register_integrated_managers()
        
        self.logger.info(f"CoherenceRegistry initialized with {len(self.functions)} functions and {len(self.components)} components")
    
    def _register_core_components(self):
        """Register all core Dau formalism components."""
        
        # Core data structures
        self.register_component(
            name="RelationalGraphWithCuts",
            component_class=RelationalGraphWithCuts,
            category=ComponentCategory.CORE_DATA,
            description="Core Dau-compliant EGI data structure with 6+1 components (V, E, ν, ⊤, Cut, area, rel)",
            key_methods=["from_specification", "validate", "get_vertex", "get_edge", "get_cut"],
            dau_chapter_refs=["Chapter 11", "Chapter 12", "Chapter 13"],
            usage_examples=[
                "egi = RelationalGraphWithCuts.from_specification(spec)",
                "vertex = egi.get_vertex('vertex_id')",
                "validation = egi.validate()"
            ]
        )
        
        self.register_component(
            name="Vertex",
            component_class=Vertex,
            category=ComponentCategory.CORE_DATA,
            description="EGI vertex with generic/constant distinction and label management",
            key_methods=["__init__", "is_valid"],
            dau_chapter_refs=["Chapter 11", "Chapter 14"],
            usage_examples=[
                "generic_vertex = Vertex(id='x', label=None, is_generic=True)",
                "constant_vertex = Vertex(id='socrates', label='Socrates', is_generic=False)"
            ]
        )
        
        self.register_component(
            name="HierarchicalIndex",
            component_class=HierarchicalIndex,
            category=ComponentCategory.UTILITY,
            description="O(1) polarity and nesting level calculation for EGI areas",
            key_methods=["get_polarity", "get_nesting_level", "build_index"],
            dau_chapter_refs=["Chapter 15", "Chapter 16"],
            usage_examples=[
                "polarity = hierarchical_index.get_polarity('area_id')",
                "level = hierarchical_index.get_nesting_level('cut_id')"
            ]
        )
        
        # Transformation rules
        transformation_rules = [
            (IterationRule, "IT+ - Iteration rule for copying subgraphs", ["Chapter 17", "Chapter 21"]),
            (DeiterationRule, "IT- - Deiteration rule for removing duplicate subgraphs", ["Chapter 17", "Chapter 21"]),
            (InsertionRule, "INS - Insertion rule for adding elements", ["Chapter 17", "Chapter 21"]),
            (ErasureRule, "ERA - Erasure rule for removing elements", ["Chapter 17", "Chapter 21"]),
            (DoubleCutInsertionRule, "DC+ - Double cut insertion rule", ["Chapter 17", "Chapter 21"]),
            (DoubleCutErasureRule, "DC- - Double cut erasure rule", ["Chapter 17", "Chapter 21"])
        ]
        
        for rule_class, description, chapters in transformation_rules:
            self.register_component(
                name=rule_class.__name__,
                component_class=rule_class,
                category=ComponentCategory.TRANSFORMATION,
                description=description,
                key_methods=["apply", "is_valid", "get_preconditions"],
                dau_chapter_refs=chapters,
                usage_examples=[
                    f"rule = {rule_class.__name__}()",
                    "result = rule.apply(egi, context)",
                    "valid = rule.is_valid(egi, parameters)"
                ]
            )
        
        # Integration interfaces
        self.register_component(
            name="CoreDauFormalismManager",
            component_class=CoreDauFormalismManager,
            category=ComponentCategory.INTEGRATION,
            description="Central manager for all core Dau formalism operations and integration",
            key_methods=[
                "create_egi", "validate_egi", "parse_linear_form", "generate_linear_form",
                "apply_transformation", "round_trip_test", "get_comprehensive_status"
            ],
            dau_chapter_refs=["Chapter 11-21"],
            usage_examples=[
                "manager = get_dau_formalism_manager()",
                "egi = manager.create_egi(specification)",
                "egif_text = manager.generate_linear_form(egi, LinearFormat.EGIF)",
                "result = manager.apply_transformation(egi, 'iteration', params)"
            ]
        )
    
    def _register_core_functions(self):
        """Register all core Dau formalism functions."""
        
        # EGI construction functions
        self.register_function(
            name="create_egi",
            function=CoreDauFormalismManager.create_egi,
            category=ComponentCategory.CORE_DATA,
            function_type=FunctionType.CONSTRUCTOR,
            description="Create new Dau-compliant EGI from specification",
            parameters=["self", "specification"],
            return_type=RelationalGraphWithCuts,
            dau_chapter_refs=["Chapter 11", "Chapter 12"],
            examples=[
                "egi = manager.create_egi({'vertices': [...], 'edges': [...]})"
            ]
        )
        
        # Linear form functions
        linear_formats = ["EGIF", "CGIF", "CLIF", "FOPL"]
        for format_name in linear_formats:
            self.register_function(
                name=f"parse_{format_name.lower()}",
                function=CoreDauFormalismManager.parse_linear_form,
                category=ComponentCategory.LINEAR_FORM,
                function_type=FunctionType.PARSER,
                description=f"Parse {format_name} text into Dau-compliant EGI",
                parameters=["self", "text", "format_type"],
                return_type=RelationalGraphWithCuts,
                dau_chapter_refs=["Chapter 18", "Chapter 19"],
                examples=[f"egi = manager.parse_linear_form(text, LinearFormat.{format_name})"]
            )
            
            self.register_function(
                name=f"generate_{format_name.lower()}",
                function=CoreDauFormalismManager.generate_linear_form,
                category=ComponentCategory.LINEAR_FORM,
                function_type=FunctionType.GENERATOR,
                description=f"Generate {format_name} text from Dau-compliant EGI",
                parameters=["self", "egi", "format_type"],
                return_type=str,
                dau_chapter_refs=["Chapter 18", "Chapter 19"],
                examples=[f"text = manager.generate_linear_form(egi, LinearFormat.{format_name})"]
            )
        
        # Transformation functions
        transformation_rules = ["iteration", "deiteration", "insertion", "erasure", "double_cut_insertion", "double_cut_erasure"]
        for rule_name in transformation_rules:
            self.register_function(
                name=f"apply_{rule_name}",
                function=CoreDauFormalismManager.apply_transformation,
                category=ComponentCategory.TRANSFORMATION,
                function_type=FunctionType.TRANSFORMER,
                description=f"Apply {rule_name} transformation rule to EGI",
                parameters=["self", "egi", "rule_name", "parameters"],
                return_type=dict,
                dau_chapter_refs=["Chapter 17", "Chapter 21"],
                examples=[f"result = manager.apply_transformation(egi, '{rule_name}', params)"]
            )
        
        # Validation functions
        self.register_function(
            name="validate_egi",
            function=CoreDauFormalismManager.validate_egi,
            category=ComponentCategory.VALIDATION,
            function_type=FunctionType.VALIDATOR,
            description="Comprehensive validation of EGI against Dau formalism",
            parameters=["self", "egi"],
            return_type=dict,
            dau_chapter_refs=["Chapter 11-21"],
            examples=["validation = manager.validate_egi(egi)"]
        )
        
        self.register_function(
            name="round_trip_test",
            function=CoreDauFormalismManager.round_trip_test,
            category=ComponentCategory.VALIDATION,
            function_type=FunctionType.VALIDATOR,
            description="Test round-trip fidelity for linear format conversion",
            parameters=["self", "egi", "format_type"],
            return_type=dict,
            dau_chapter_refs=["Chapter 18", "Chapter 19"],
            examples=["result = manager.round_trip_test(egi, LinearFormat.EGIF)"]
        )
        
        # Utility functions
        self.register_function(
            name="get_comprehensive_status",
            function=CoreDauFormalismManager.get_comprehensive_status,
            category=ComponentCategory.UTILITY,
            function_type=FunctionType.UTILITY,
            description="Get complete status of all Dau formalism components",
            parameters=["self"],
            return_type=dict,
            dau_chapter_refs=["All chapters"],
            examples=["status = manager.get_comprehensive_status()"]
        )
    
    def _register_integrated_managers(self):
        """Register integrated manager components."""
        
        # Import integrated managers
        try:
            from .integrated_corpus_manager import IntegratedCorpusManager, get_integrated_corpus_manager
            from .integrated_view_manager import IntegratedViewManager, get_integrated_view_manager
            from .integrated_export_manager import IntegratedExportManager, get_integrated_export_manager
            
            # Register IntegratedCorpusManager
            self.register_component(
                name="IntegratedCorpusManager",
                component_class=IntegratedCorpusManager,
                category=ComponentCategory.CORPUS_MANAGEMENT,
                description="Integrated tomos manager with full Dau formalism compliance and validation",
                key_methods=["add_egi", "get_egi", "search_corpus", "load_from_filesystem", "get_corpus_statistics"],
                dau_chapter_refs=["All chapters"],
                usage_examples=[
                    "corpus_manager = get_integrated_corpus_manager()",
                    "item_id = corpus_manager.add_egi(egi, metadata)",
                    "results = corpus_manager.search_corpus('example', category=CorpusCategory.PEIRCE)"
                ]
            )
            
            # Register tomos manager functions
            self.register_function(
                name="get_integrated_corpus_manager",
                function=get_integrated_corpus_manager,
                category=ComponentCategory.CORPUS_MANAGEMENT,
                function_type=FunctionType.FACTORY,
                description="Get global integrated tomos manager instance",
                parameters=[],
                return_type=IntegratedCorpusManager,
                examples=["manager = get_integrated_corpus_manager()"]
            )
            
            # Register IntegratedViewManager
            self.register_component(
                name="IntegratedViewManager",
                component_class=IntegratedViewManager,
                category=ComponentCategory.VIEW_MANAGEMENT,
                description="Integrated view manager providing unified EGI visualization with multiple view types",
                key_methods=["generate_view", "generate_multiple_views", "generate_comparative_view", "export_view"],
                dau_chapter_refs=["Chapter 21"],
                usage_examples=[
                    "view_manager = get_integrated_view_manager()",
                    "view = view_manager.generate_view(egi, ViewType.DETAILED)",
                    "views = view_manager.generate_multiple_views(egi, [ViewType.OVERVIEW, ViewType.HIERARCHICAL])"
                ]
            )
            
            # Register view manager functions
            self.register_function(
                name="get_integrated_view_manager",
                function=get_integrated_view_manager,
                category=ComponentCategory.VIEW_MANAGEMENT,
                function_type=FunctionType.FACTORY,
                description="Get global integrated view manager instance",
                parameters=[],
                return_type=IntegratedViewManager,
                examples=["manager = get_integrated_view_manager()"]
            )
            
            # Register IntegratedExportManager
            self.register_component(
                name="IntegratedExportManager",
                component_class=IntegratedExportManager,
                category=ComponentCategory.EXPORT_MANAGEMENT,
                description="Integrated export manager with unified linear form export and validation",
                key_methods=["export_egi", "export_multiple_formats", "export_to_egif", "export_to_cgif", "export_to_clif"],
                dau_chapter_refs=["Chapter 18", "Chapter 19", "Chapter 20"],
                usage_examples=[
                    "export_manager = get_integrated_export_manager()",
                    "result = export_manager.export_egi(egi, ExportFormat.EGIF, output_path)",
                    "results = export_manager.export_multiple_formats(egi, [ExportFormat.EGIF, ExportFormat.CLIF])"
                ]
            )
            
            # Register export manager functions
            self.register_function(
                name="get_integrated_export_manager",
                function=get_integrated_export_manager,
                category=ComponentCategory.EXPORT_MANAGEMENT,
                function_type=FunctionType.FACTORY,
                description="Get global integrated export manager instance",
                parameters=[],
                return_type=IntegratedExportManager,
                examples=["manager = get_integrated_export_manager()"]
            )
            
            self.logger.info("Registered integrated managers in coherence registry")
            
        except ImportError as e:
            self.logger.warning(f"Could not import integrated managers: {e}")
        
        # Register EGI Spatial Layout Specification
        self._register_spatial_layout_specification()
    
    def _register_spatial_layout_specification(self):
        """Register the comprehensive EGI spatial layout specification."""
        
        # Register the spatial layout specification as a component
        self.register_component(
            name="EGISpatialLayoutSpecification",
            component_class=type("EGISpatialLayoutSpecification", (), {}),  # Placeholder class
            category=ComponentCategory.SPATIAL_LAYOUT,
            description="Complete specification for Dau Chapter 21 compliant EGI spatial layout",
            key_methods=[
                "two_phase_layout", "containment_hierarchy", "ligature_optimization",
                "abstract_layout_units", "exclusive_positioning", "predicate_hooks",
                "spatial_exclusion", "view_depth_control", "collapsible_cuts"
            ],
            dau_chapter_refs=[
                "Chapter 21: Mathematical Logic with Diagrams",
                "Dau's conventions for drawing Existential Graph diagrams",
                "Enclosing-relation as main structural relation",
                "Spatial exclusion principle for sibling cuts",
                "Iconic representation through visible analogies"
            ],
            usage_examples=[
                "# Two-phase layout: containment hierarchy → ligature optimization",
                "# ALU system: abstract units → view-specific scaling",
                "# Exclusive positioning: all elements visually distinct",
                "# 8-point compass hooks: N,NE,E,SE,S,SW,W,NW for predicates",
                "# Depth control: global limiting + individual collapse"
            ]
        )
        
        self.logger.info("Registered EGI Spatial Layout Specification in coherence registry")
    
    def register_function(self, name: str, function: Callable, category: ComponentCategory,
                         function_type: FunctionType, description: str, parameters: List[str],
                         return_type: Optional[Type] = None, dau_chapter_refs: List[str] = None,
                         examples: List[str] = None, related_functions: List[str] = None):
        """Register a function in the coherence registry."""
        
        registered_func = RegisteredFunction(
            name=name,
            function=function,
            category=category,
            function_type=function_type,
            description=description,
            parameters=parameters,
            return_type=return_type,
            dau_chapter_refs=dau_chapter_refs or [],
            examples=examples or [],
            related_functions=related_functions or []
        )
        
        self.functions[name] = registered_func
        self.categories[category].append(name)
        
        self.logger.debug(f"Registered function: {name} in category {category.value}")
    
    def register_component(self, name: str, component_class: Type, category: ComponentCategory,
                          description: str, key_methods: List[str], dau_chapter_refs: List[str] = None,
                          usage_examples: List[str] = None):
        """Register a component class in the coherence registry."""
        
        registered_comp = RegisteredComponent(
            name=name,
            component_class=component_class,
            category=category,
            description=description,
            key_methods=key_methods,
            dau_chapter_refs=dau_chapter_refs or [],
            usage_examples=usage_examples or []
        )
        
        self.components[name] = registered_comp
        if name not in self.categories[category]:
            self.categories[category].append(name)
        
        self.logger.debug(f"Registered component: {name} in category {category.value}")
    
    # ========================================================================
    # Search and Discovery Functions
    # ========================================================================
    
    def search_functions(self, query: str, category: Optional[ComponentCategory] = None,
                        function_type: Optional[FunctionType] = None) -> List[RegisteredFunction]:
        """Search for functions by name, description, or Dau chapter reference."""
        results = []
        query_lower = query.lower()
        
        for func in self.functions.values():
            # Apply filters
            if category and func.category != category:
                continue
            if function_type and func.function_type != function_type:
                continue
            
            # Search in name, description, and chapter references
            if (query_lower in func.name.lower() or
                query_lower in func.description.lower() or
                any(query_lower in ref.lower() for ref in func.dau_chapter_refs)):
                results.append(func)
        
        return results
    
    def search_components(self, query: str, category: Optional[ComponentCategory] = None) -> List[RegisteredComponent]:
        """Search for components by name, description, or Dau chapter reference."""
        results = []
        query_lower = query.lower()
        
        for comp in self.components.values():
            # Apply filters
            if category and comp.category != category:
                continue
            
            # Search in name, description, and chapter references
            if (query_lower in comp.name.lower() or
                query_lower in comp.description.lower() or
                any(query_lower in ref.lower() for ref in comp.dau_chapter_refs)):
                results.append(comp)
        
        return results
    
    def get_functions_by_category(self, category: ComponentCategory) -> List[RegisteredFunction]:
        """Get all functions in a specific category."""
        return [self.functions[name] for name in self.categories[category] if name in self.functions]
    
    def get_components_by_category(self, category: ComponentCategory) -> List[RegisteredComponent]:
        """Get all components in a specific category."""
        return [self.components[name] for name in self.categories[category] if name in self.components]
    
    def get_dau_chapter_functions(self, chapter: str) -> List[RegisteredFunction]:
        """Get all functions related to a specific Dau chapter."""
        results = []
        for func in self.functions.values():
            if any(chapter.lower() in ref.lower() for ref in func.dau_chapter_refs):
                results.append(func)
        return results
    
    def get_related_functions(self, function_name: str) -> List[RegisteredFunction]:
        """Get functions related to the specified function."""
        if function_name not in self.functions:
            return []
        
        func = self.functions[function_name]
        related = []
        
        # Get explicitly related functions
        for related_name in func.related_functions:
            if related_name in self.functions:
                related.append(self.functions[related_name])
        
        # Get functions in same category
        category_functions = self.get_functions_by_category(func.category)
        for cat_func in category_functions:
            if cat_func.name != function_name and cat_func not in related:
                related.append(cat_func)
        
        return related
    
    # ========================================================================
    # Documentation Generation
    # ========================================================================
    
    def generate_function_reference(self, output_path: Optional[Path] = None) -> str:
        """Generate comprehensive function reference documentation."""
        doc_lines = [
            "# Arisbe Core Dau Formalism Function Reference",
            "",
            "This document provides a comprehensive reference to all functions and components",
            "in the integrated Dau formalism system.",
            "",
            "## Table of Contents",
            ""
        ]
        
        # Generate table of contents
        for category in ComponentCategory:
            category_functions = self.get_functions_by_category(category)
            category_components = self.get_components_by_category(category)
            
            if category_functions or category_components:
                doc_lines.append(f"- [{category.value.replace('_', ' ').title()}](#{category.value.replace('_', '-')})")
        
        doc_lines.extend(["", "---", ""])
        
        # Generate detailed sections
        for category in ComponentCategory:
            category_functions = self.get_functions_by_category(category)
            category_components = self.get_components_by_category(category)
            
            if not (category_functions or category_components):
                continue
            
            doc_lines.extend([
                f"## {category.value.replace('_', ' ').title()}",
                ""
            ])
            
            # Document components
            if category_components:
                doc_lines.extend(["### Components", ""])
                for comp in category_components:
                    doc_lines.extend([
                        f"#### {comp.name}",
                        "",
                        comp.description,
                        "",
                        "**Key Methods:**",
                        ""
                    ])
                    for method in comp.key_methods:
                        doc_lines.append(f"- `{method}`")
                    
                    if comp.dau_chapter_refs:
                        doc_lines.extend(["", "**Dau Chapter References:**", ""])
                        for ref in comp.dau_chapter_refs:
                            doc_lines.append(f"- {ref}")
                    
                    if comp.usage_examples:
                        doc_lines.extend(["", "**Usage Examples:**", ""])
                        for example in comp.usage_examples:
                            doc_lines.append(f"```python\n{example}\n```")
                    
                    doc_lines.extend(["", "---", ""])
            
            # Document functions
            if category_functions:
                doc_lines.extend(["### Functions", ""])
                for func in category_functions:
                    doc_lines.extend([
                        f"#### {func.name}",
                        "",
                        f"**Type:** {func.function_type.value}",
                        "",
                        func.description,
                        "",
                        "**Parameters:**",
                        ""
                    ])
                    for param in func.parameters:
                        doc_lines.append(f"- `{param}`")
                    
                    if func.return_type:
                        doc_lines.extend(["", f"**Returns:** `{func.return_type.__name__}`", ""])
                    
                    if func.dau_chapter_refs:
                        doc_lines.extend(["**Dau Chapter References:**", ""])
                        for ref in func.dau_chapter_refs:
                            doc_lines.append(f"- {ref}")
                    
                    if func.examples:
                        doc_lines.extend(["", "**Examples:**", ""])
                        for example in func.examples:
                            doc_lines.append(f"```python\n{example}\n```")
                    
                    doc_lines.extend(["", "---", ""])
        
        documentation = "\n".join(doc_lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(documentation)
            self.logger.info(f"Function reference written to {output_path}")
        
        return documentation
    
    def get_quick_reference(self) -> Dict[str, Any]:
        """Get a quick reference summary of all registered items."""
        return {
            "total_functions": len(self.functions),
            "total_components": len(self.components),
            "categories": {
                cat.value: {
                    "functions": len(self.get_functions_by_category(cat)),
                    "components": len(self.get_components_by_category(cat))
                }
                for cat in ComponentCategory
            },
            "function_types": {
                ftype.value: len([f for f in self.functions.values() if f.function_type == ftype])
                for ftype in FunctionType
            }
        }


# ============================================================================
# Global Registry Instance
# ============================================================================

_global_registry: Optional[CoherenceRegistry] = None

def get_coherence_registry() -> CoherenceRegistry:
    """Get the global coherence registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = CoherenceRegistry()
    return _global_registry

def search_functions(query: str, **kwargs) -> List[RegisteredFunction]:
    """Convenience function to search for functions."""
    return get_coherence_registry().search_functions(query, **kwargs)

def search_components(query: str, **kwargs) -> List[RegisteredComponent]:
    """Convenience function to search for components."""
    return get_coherence_registry().search_components(query, **kwargs)

def get_function_reference() -> str:
    """Convenience function to get function reference documentation."""
    return get_coherence_registry().generate_function_reference()
