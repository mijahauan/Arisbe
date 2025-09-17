"""
Core Dau Formalism Integration Module

This module provides the unified interface to all core Dau formalism components,
ensuring coherent access to EG data persistence, linear form integration,
transformation rules, and chapters 11-21 compliance.

Architecture:
- Centralizes access to all Dau-compliant components
- Provides unified validation and consistency checking
- Integrates with coherence framework for monitoring
- Maintains comprehensive function registry
"""

from typing import Dict, List, Optional, Union, Any, Protocol
from dataclasses import dataclass
from enum import Enum
import logging

# Core EGI components
from .egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from .hierarchical_index import HierarchicalIndex
from .formal_transformation_rules import (
    FormalTransformationRule, IterationRule, DeiterationRule,
    InsertionRule, DoubleCutErasureRule, DoubleCutInsertionRule,
    ErasureRule, TransformationContext, AreaPolarity
)

# Linear form parsers and generators
from .egif_parser_dau import EGIFParser
from .egif_generator_dau import EGIFGenerator
from .cgif_parser_dau import CGIFParser
from .cgif_generator_dau import CGIFGenerator
from .clif_parser_dau import CLIFParser
from .clif_generator_dau import CLIFGenerator

# Chapter-specific compliance engines
from .dau_semantic_evaluation_engine import SemanticEvaluationEngine
from .enhanced_dau_compliance_engine import EnhancedDauComplianceEngine
from .chapter18_fopl_translation import Chapter18FOPLTranslator

# Persistence and history
from .egi_transformation_history import EGITransformationHistory

# Integration interfaces - import only what exists
try:
    from .integration_interfaces import (
        PolarityProvider, TransformationValidator, HistoryTracker,
        IntegrationContext
    )
except ImportError:
    # Create minimal interfaces if not available
    class PolarityProvider: pass
    class TransformationValidator: pass
    class HistoryTracker: pass
    class IntegrationContext: pass


class LinearFormat(Enum):
    """Supported linear representation formats."""
    EGIF = "egif"
    CGIF = "cgif"
    CLIF = "clif"
    FOPL = "fopl"


@dataclass
class DauFormalismState:
    """Complete state of Dau formalism components."""
    egi: Optional[RelationalGraphWithCuts] = None
    linear_forms: Dict[LinearFormat, str] = None
    transformation_history: List[Dict[str, Any]] = None
    validation_results: Dict[str, bool] = None
    compliance_status: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.linear_forms is None:
            self.linear_forms = {}
        if self.transformation_history is None:
            self.transformation_history = []
        if self.validation_results is None:
            self.validation_results = {}
        if self.compliance_status is None:
            self.compliance_status = {}


class CoreDauFormalismManager:
    """
    Central manager for all core Dau formalism components.
    
    This class provides unified access to:
    - EG data persistence and retrieval
    - Linear form parsing/generation (EGIF/CGIF/CLIF/FOPL)
    - Transformation rule application and validation
    - Dau chapters 11-21 compliance checking
    - Comprehensive testing and validation
    """
    
    def __init__(self, integration_context: Optional[IntegrationContext] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize integration context
        if integration_context is None:
            integration_context = IntegrationContext()
        self.integration_manager = IntegrationManager(integration_context)
        
        # Initialize core components
        self._init_parsers_generators()
        self._init_transformation_rules()
        self._init_compliance_engines()
        self._init_persistence_managers()
        
        # State tracking
        self.current_state = DauFormalismState()
        
        self.logger.info("CoreDauFormalismManager initialized with full integration")
    
    def _init_parsers_generators(self):
        """Initialize parsers and generators"""
        self.parsers = {
            LinearFormat.EGIF: EGIFParser,
            LinearFormat.CGIF: CGIFParser,
            LinearFormat.CLIF: CLIFParser
        }
        
        self.generators = {
            LinearFormat.EGIF: EGIFGenerator,
            LinearFormat.CGIF: CGIFGenerator,
            LinearFormat.CLIF: CLIFGenerator
        }
        
        # FOPL uses specialized translation engine
        self.fopl_translator = Chapter18FOPLTranslator()
    
    def _init_transformation_rules(self):
        """Initialize all Dau transformation rules."""
        self.transformation_rules = {
            "iteration": IterationRule(),
            "deiteration": DeiterationRule(),
            "insertion": InsertionRule(),
            "erasure": ErasureRule(),
            "double_cut_insertion": DoubleCutInsertionRule(),
            "double_cut_erasure": DoubleCutErasureRule(),
        }
    
    def _init_compliance_engines(self):
        """Initialize Dau compliance and evaluation engines."""
        self.semantic_engine = SemanticEvaluationEngine()
        self.compliance_engine = EnhancedDauComplianceEngine()
    
    def _init_persistence_managers(self):
        """Initialize persistence and history managers."""
        self.transformation_history = EGITransformationHistory()
    
    # ========================================================================
    # Core EGI Operations
    # ========================================================================
    
    def create_egi(self, specification: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Create a new Dau-compliant EGI from specification."""
        try:
            # Validate specification against Dau formalism
            validation_result = self.compliance_engine.validate_specification(specification)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid EGI specification: {validation_result.errors}")
            
            # Create EGI using core Dau components
            egi = RelationalGraphWithCuts.from_specification(specification)
            
            # Update current state
            self.current_state.egi = egi
            self.current_state.validation_results["egi_creation"] = True
            
            self.logger.info(f"Created Dau-compliant EGI with {len(egi.V)} vertices, {len(egi.E)} edges")
            return egi
            
        except Exception as e:
            self.logger.error(f"Failed to create EGI: {e}")
            self.current_state.validation_results["egi_creation"] = False
            raise
    
    def validate_egi(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Comprehensive validation of EGI against Dau formalism."""
        validation_results = {}
        
        try:
            # Core structure validation (6+1 components)
            validation_results["structure"] = self._validate_egi_structure(egi)
            
            # Hierarchical index validation
            validation_results["hierarchy"] = self._validate_hierarchical_structure(egi)
            
            # Semantic evaluation
            validation_results["semantics"] = self.semantic_evaluator.evaluate(egi)
            
            # Compliance with specific chapters
            validation_results["compliance"] = self.compliance_engine.check_full_compliance(egi)
            
            # Overall validity
            validation_results["overall_valid"] = all([
                validation_results["structure"]["valid"],
                validation_results["hierarchy"]["valid"],
                validation_results["semantics"]["valid"],
                validation_results["compliance"]["valid"]
            ])
            
            self.current_state.validation_results.update(validation_results)
            return validation_results
            
        except Exception as e:
            self.logger.error(f"EGI validation failed: {e}")
            validation_results["error"] = str(e)
            validation_results["overall_valid"] = False
            return validation_results
    
    def _validate_egi_structure(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Validate core EGI structure (V, E, ν, ⊤, Cut, area, rel)."""
        results = {"valid": True, "errors": []}
        
        # Check required components
        required_components = ["V", "E", "nu", "sheet", "Cut", "area", "rel"]
        for component in required_components:
            if not hasattr(egi, component):
                results["errors"].append(f"Missing required component: {component}")
                results["valid"] = False
        
        # Validate component types and relationships
        if hasattr(egi, "V") and hasattr(egi, "E") and hasattr(egi, "nu"):
            # Check ν mapping consistency
            for edge_id, vertex_tuple in egi.nu.items():
                if edge_id not in {e.id for e in egi.E}:
                    results["errors"].append(f"Edge {edge_id} in ν not found in E")
                    results["valid"] = False
                
                for vertex_id in vertex_tuple:
                    if vertex_id not in {v.id for v in egi.V}:
                        results["errors"].append(f"Vertex {vertex_id} in ν not found in V")
                        results["valid"] = False
        
        return results
    
    def _validate_hierarchical_structure(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Validate hierarchical index and cut nesting."""
        results = {"valid": True, "errors": []}
        
        try:
            # Ensure hierarchical index is built
            if not hasattr(egi, 'hierarchical_index') or not egi.hierarchical_index.areas:
                egi._build_hierarchical_index()
            
            # Validate cut nesting hierarchy
            for cut in egi.Cut:
                nesting_level = egi.hierarchical_index.get_nesting_level(cut.id)
                if nesting_level is None:
                    results["errors"].append(f"Cut {cut.id} not found in hierarchical index")
                    results["valid"] = False
            
            # Validate polarity calculations
            for area_id in egi.area.keys():
                polarity = egi.hierarchical_index.get_polarity(area_id)
                if polarity not in ["positive", "negative"]:
                    results["errors"].append(f"Invalid polarity for area {area_id}: {polarity}")
                    results["valid"] = False
                    
        except Exception as e:
            results["errors"].append(f"Hierarchical validation error: {e}")
            results["valid"] = False
        
        return results
    
    # ========================================================================
    # Linear Form Integration
    # ========================================================================
    
    def parse_linear_form(self, text: str, format_type: LinearFormat) -> RelationalGraphWithCuts:
        """Parse linear form text into Dau-compliant EGI."""
        try:
            if format_type == LinearFormat.EGIF:
                parser = EGIFParser(text)
                return parser.parse()
            elif format_type == LinearFormat.FOPL:
                # FOPL requires special translation
                egi = self.fopl_translator.translate_to_egi(text)
            else:
                parser = self.parsers[format_type]
                egi = parser.parse(text)
            
            # Validate parsed EGI
            validation_results = self.validate_egi(egi)
            if not validation_results["overall_valid"]:
                raise ValueError(f"Parsed EGI failed validation: {validation_results['errors']}")
            
            # Update state
            self.current_state.egi = egi
            self.current_state.linear_forms[format_type] = text
            
            self.logger.info(f"Successfully parsed {format_type.value} into Dau-compliant EGI")
            return egi
            
        except Exception as e:
            self.logger.error(f"Failed to parse {format_type.value}: {e}")
            raise
    
    def generate_linear_form(self, egi: RelationalGraphWithCuts, format_type: LinearFormat) -> str:
        """Generate linear form text from Dau-compliant EGI."""
        try:
            # Validate EGI before generation
            validation_results = self.validate_egi(egi)
            if not validation_results["overall_valid"]:
                self.logger.warning(f"Generating from potentially invalid EGI: {validation_results['errors']}")
            
            if format_type == LinearFormat.FOPL:
                # FOPL requires special translation
                text = self.fopl_translator.translate_from_egi(egi)
            elif format_type == LinearFormat.EGIF:
                generator = EGIFGenerator(egi)
                text = generator.generate()
            else:
                generator = self.generators[format_type]
                text = generator.generate(egi)
            
            # Update state
            self.current_state.linear_forms[format_type] = text
            
            self.logger.info(f"Successfully generated {format_type.value} from EGI")
            return text
            
        except Exception as e:
            self.logger.error(f"Failed to generate {format_type.value}: {e}")
            raise
    
    def round_trip_test(self, egi: RelationalGraphWithCuts, format_type: LinearFormat) -> Dict[str, Any]:
        """Test round-trip fidelity for a linear format."""
        results = {"success": False, "errors": []}
        
        try:
            # Generate linear form
            linear_text = self.generate_linear_form(egi, format_type)
            
            # Parse back to EGI
            reconstructed_egi = self.parse_linear_form(linear_text, format_type)
            
            # Compare structural equivalence
            equivalence_check = self._check_egi_equivalence(egi, reconstructed_egi)
            
            results["success"] = equivalence_check["equivalent"]
            results["linear_text"] = linear_text
            results["equivalence_details"] = equivalence_check
            
            if not results["success"]:
                results["errors"] = equivalence_check["differences"]
            
            self.logger.info(f"Round-trip test for {format_type.value}: {'PASSED' if results['success'] else 'FAILED'}")
            return results
            
        except Exception as e:
            results["errors"].append(str(e))
            self.logger.error(f"Round-trip test failed for {format_type.value}: {e}")
            return results
    
    def _check_egi_equivalence(self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Check logical equivalence between two EGIs."""
        # Use semantic evaluation engine for deep equivalence checking
        return self.semantic_evaluator.check_equivalence(egi1, egi2)
    
    # ========================================================================
    # Transformation Rule Integration
    # ========================================================================
    
    def apply_transformation(self, egi: RelationalGraphWithCuts, rule_name: str, 
                           parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a Dau transformation rule to an EGI."""
        try:
            if rule_name not in self.transformation_rules:
                raise ValueError(f"Unknown transformation rule: {rule_name}")
            
            rule = self.transformation_rules[rule_name]
            
            # Create transformation context
            context = TransformationContext(
                source_egi=egi,
                rule_name=rule_name,
                parameters=parameters
            )
            
            # Apply transformation
            result = rule.apply(egi, context)
            
            if result.success:
                # Validate transformed EGI
                validation_results = self.validate_egi(result.transformed_egi)
                
                # Record transformation in history
                self.transformation_history.add_transformation(
                    source_egi=egi,
                    target_egi=result.transformed_egi,
                    rule_name=rule_name,
                    parameters=parameters,
                    validation_results=validation_results
                )
                
                # Update current state
                self.current_state.egi = result.transformed_egi
                self.current_state.transformation_history.append({
                    "rule": rule_name,
                    "parameters": parameters,
                    "success": True,
                    "validation": validation_results
                })
                
                self.logger.info(f"Successfully applied {rule_name} transformation")
            else:
                self.logger.warning(f"Transformation {rule_name} failed: {result.error_message}")
            
            return {
                "success": result.success,
                "transformed_egi": result.transformed_egi if result.success else None,
                "error_message": result.error_message,
                "changes_made": result.changes_made
            }
            
        except Exception as e:
            self.logger.error(f"Transformation application failed: {e}")
            return {
                "success": False,
                "transformed_egi": None,
                "error_message": str(e),
                "changes_made": {}
            }
    
    def validate_transformation_sequence(self, transformations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a sequence of transformations for logical consistency."""
        results = {"valid": True, "errors": [], "sequence_results": []}
        
        current_egi = self.current_state.egi
        if current_egi is None:
            results["errors"].append("No current EGI to start transformation sequence")
            results["valid"] = False
            return results
        
        try:
            for i, transform_spec in enumerate(transformations):
                rule_name = transform_spec["rule"]
                parameters = transform_spec.get("parameters", {})
                
                # Apply transformation
                transform_result = self.apply_transformation(current_egi, rule_name, parameters)
                
                step_result = {
                    "step": i + 1,
                    "rule": rule_name,
                    "success": transform_result["success"],
                    "error": transform_result.get("error_message")
                }
                
                if transform_result["success"]:
                    current_egi = transform_result["transformed_egi"]
                    
                    # Check semantic equivalence with original
                    equivalence = self._check_egi_equivalence(self.current_state.egi, current_egi)
                    step_result["semantic_equivalence"] = equivalence
                    
                    if not equivalence["equivalent"]:
                        results["errors"].append(f"Step {i+1}: Semantic equivalence lost")
                        results["valid"] = False
                else:
                    results["errors"].append(f"Step {i+1}: Transformation failed")
                    results["valid"] = False
                
                results["sequence_results"].append(step_result)
            
            return results
            
        except Exception as e:
            results["errors"].append(f"Sequence validation error: {e}")
            results["valid"] = False
            return results
    
    # ========================================================================
    # Persistence and History
    # ========================================================================
    
    def save_state(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save current formalism state to persistent storage."""
        try:
            state_data = {
                "egi": self.current_state.egi,
                "linear_forms": self.current_state.linear_forms,
                "transformation_history": self.current_state.transformation_history,
                "validation_results": self.current_state.validation_results,
                "compliance_status": self.current_state.compliance_status,
                "metadata": metadata or {}
            }
            
            success = self.history_manager.save_state(identifier, state_data)
            
            if success:
                self.logger.info(f"Saved formalism state: {identifier}")
            else:
                self.logger.error(f"Failed to save formalism state: {identifier}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"State save error: {e}")
            return False
    
    def load_state(self, identifier: str) -> bool:
        """Load formalism state from persistent storage."""
        try:
            state_data = self.history_manager.load_state(identifier)
            
            if state_data:
                self.current_state = DauFormalismState(
                    egi=state_data.get("egi"),
                    linear_forms=state_data.get("linear_forms", {}),
                    transformation_history=state_data.get("transformation_history", []),
                    validation_results=state_data.get("validation_results", {}),
                    compliance_status=state_data.get("compliance_status", {})
                )
                
                self.logger.info(f"Loaded formalism state: {identifier}")
                return True
            else:
                self.logger.warning(f"No state found for identifier: {identifier}")
                return False
                
        except Exception as e:
            self.logger.error(f"State load error: {e}")
            return False
    
    # ========================================================================
    # Comprehensive Status and Reporting
    # ========================================================================
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get complete status of all Dau formalism components."""
        status = {
            "timestamp": self._get_timestamp(),
            "current_egi": {
                "present": self.current_state.egi is not None,
                "vertex_count": len(self.current_state.egi.V) if self.current_state.egi else 0,
                "edge_count": len(self.current_state.egi.E) if self.current_state.egi else 0,
                "cut_count": len(self.current_state.egi.Cut) if self.current_state.egi else 0
            },
            "linear_forms": {
                "available_formats": list(self.current_state.linear_forms.keys()),
                "format_count": len(self.current_state.linear_forms)
            },
            "transformation_history": {
                "total_transformations": len(self.current_state.transformation_history),
                "successful_transformations": sum(1 for t in self.current_state.transformation_history if t.get("success", False))
            },
            "validation_status": self.current_state.validation_results,
            "compliance_status": self.current_state.compliance_status,
            "component_health": self._check_component_health()
        }
        
        return status
    
    def _check_component_health(self) -> Dict[str, bool]:
        """Check health status of all integrated components."""
        health = {}
        
        try:
            # Test parsers
            for format_type, parser in self.parsers.items():
                health[f"parser_{format_type.value}"] = hasattr(parser, 'parse') and callable(parser.parse)
            
            # Test generators
            for format_type, generator in self.generators.items():
                health[f"generator_{format_type.value}"] = hasattr(generator, 'generate') and callable(generator.generate)
            
            # Test transformation rules
            for rule_name, rule in self.transformation_rules.items():
                health[f"rule_{rule_name}"] = hasattr(rule, 'apply') and callable(rule.apply)
            
            # Test compliance engines
            health["semantic_evaluator"] = hasattr(self.semantic_evaluator, 'evaluate') and callable(self.semantic_evaluator.evaluate)
            health["compliance_engine"] = hasattr(self.compliance_engine, 'check_full_compliance') and callable(self.compliance_engine.check_full_compliance)
            
            # Test persistence
            health["history_manager"] = hasattr(self.history_manager, 'save_state') and callable(self.history_manager.save_state)
            
        except Exception as e:
            self.logger.error(f"Component health check error: {e}")
            health["health_check_error"] = str(e)
        
        return health
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for status reporting."""
        from datetime import datetime
        return datetime.now().isoformat()


# ============================================================================
# Coherence Framework Integration
# ============================================================================

def register_with_coherence_framework():
    """Register core Dau formalism with coherence framework."""
    from .integration_interfaces import IntegrationContext
    
    # Create integration context for Dau formalism
    context = IntegrationContext(
        polarity_provider=None,  # Will be set by manager
        transformation_validator=None,  # Will be set by manager
        history_tracker=None,  # Will be set by manager
        corpus_manager=None  # Optional
    )
    
    # Create and return manager
    manager = CoreDauFormalismManager(context)
    
    # Register as polarity provider
    context.polarity_provider = manager.integration_manager.polarity_provider
    
    return manager


# Module-level convenience functions
_global_manager: Optional[CoreDauFormalismManager] = None

def get_dau_formalism_manager() -> CoreDauFormalismManager:
    """Get global Dau formalism manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = register_with_coherence_framework()
    return _global_manager

def reset_dau_formalism_manager():
    """Reset global manager (for testing)."""
    global _global_manager
    _global_manager = None
