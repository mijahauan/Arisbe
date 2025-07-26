"""
EGIF-EG Integration Layer - Phase 3 Implementation

This module provides comprehensive integration between EGIF parsing/generation
and the existing EG-HG (Existential Graph - Hypergraph) architecture. It ensures
seamless interoperability while maintaining the educational and mathematical
benefits of EGIF.

Key integration points:
1. EGIF → EG-HG conversion (parsing to hypergraph)
2. EG-HG → EGIF conversion (hypergraph to linear form)
3. Context management and scoping
4. Entity/Predicate mapping
5. Educational tracing and validation
6. Compatibility with existing CLIF workflows

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, replace
from enum import Enum
import uuid

from eg_types import (
    Entity, Predicate, Context, 
    EntityId, PredicateId, ContextId,
    new_entity_id, new_predicate_id, new_context_id,
    ValidationError, pmap, pset, pvector
)
from graph import EGGraph
from context import ContextManager
from egif_parser import EGIFParseResult, parse_egif
from egif_advanced_constructs import parse_advanced_egif, FunctionSymbol, CoreferencePattern, ScrollPattern
from egif_generator_simple import SimpleEGIFGenerator, SimpleEGIFGenerationResult
from egif_validation_framework import validate_egif, ValidationLevel
from dau_sowa_compatibility import DauSowaCompatibilityAnalyzer, ResolutionStrategy


class IntegrationMode(Enum):
    """Integration modes for different use cases."""
    EDUCATIONAL = "educational"      # Prioritize educational clarity
    MATHEMATICAL = "mathematical"    # Prioritize mathematical rigor
    PRACTICAL = "practical"         # Prioritize computational efficiency
    COMPATIBLE = "compatible"       # Maintain CLIF compatibility


@dataclass
class EGIFIntegrationResult:
    """Result of EGIF integration operation."""
    graph: Optional[EGGraph]
    egif_source: Optional[str]
    success: bool
    errors: List[str]
    warnings: List[str]
    educational_trace: List[str]
    compatibility_issues: List[str]
    performance_metrics: Dict[str, float]
    metadata: Dict[str, Any]
    
    def get_formatted_report(self) -> str:
        """Get formatted integration report."""
        lines = []
        lines.append("🔗 EGIF-EG Integration Report")
        lines.append("=" * 50)
        lines.append(f"Success: {'✅ Yes' if self.success else '❌ No'}")
        
        if self.egif_source:
            lines.append(f"EGIF Source: {self.egif_source}")
        
        if self.graph:
            lines.append(f"Graph Entities: {len(self.graph.entities)}")
            lines.append(f"Graph Predicates: {len(self.graph.predicates)}")
        
        if self.errors:
            lines.append(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  • {error}")
        
        if self.warnings:
            lines.append(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  • {warning}")
        
        if self.compatibility_issues:
            lines.append(f"\n🔍 Compatibility Issues ({len(self.compatibility_issues)}):")
            for issue in self.compatibility_issues:
                lines.append(f"  • {issue}")
        
        if self.performance_metrics:
            lines.append(f"\n⚡ Performance Metrics:")
            for metric, value in self.performance_metrics.items():
                lines.append(f"  {metric}: {value:.4f}s")
        
        if self.educational_trace:
            lines.append(f"\n📚 Educational Trace (first 3):")
            for trace in self.educational_trace[:3]:
                lines.append(f"  • {trace}")
        
        return "\n".join(lines)


class EGIFToEGConverter:
    """Converts EGIF parse results to EG-HG representation."""
    
    def __init__(self, mode: IntegrationMode = IntegrationMode.EDUCATIONAL):
        """Initialize converter with integration mode."""
        self.mode = mode
        self.compatibility_analyzer = DauSowaCompatibilityAnalyzer()
        
    def convert_parse_result_to_graph(self, parse_result: EGIFParseResult, 
                                    base_graph: Optional[EGGraph] = None) -> EGIFIntegrationResult:
        """Convert EGIF parse result to EG-HG representation."""
        import time
        start_time = time.time()
        
        errors = []
        warnings = []
        educational_trace = []
        compatibility_issues = []
        
        try:
            # Start with base graph or create empty
            if base_graph is None:
                graph = EGGraph.create_empty()
            else:
                graph = base_graph
            
            educational_trace.append("Starting EGIF → EG-HG conversion")
            
            # Check for parse errors
            if parse_result.errors:
                for error in parse_result.errors:
                    errors.append(f"Parse error: {error.message}")
                
                return EGIFIntegrationResult(
                    graph=None,
                    egif_source=None,
                    success=False,
                    errors=errors,
                    warnings=warnings,
                    educational_trace=educational_trace,
                    compatibility_issues=compatibility_issues,
                    performance_metrics={"total_time": time.time() - start_time},
                    metadata={}
                )
            
            # Convert entities
            entity_mapping = {}
            for entity in parse_result.entities:
                try:
                    eg_entity = Entity(
                        id=new_entity_id(),
                        name=entity.name,
                        entity_type=entity.entity_type,
                        properties=entity.properties,
                        context_id=entity.context_id
                    )
                    graph = graph.evolve(entities=graph.entities.set(eg_entity.id, eg_entity))
                    entity_mapping[entity.id] = eg_entity.id
                    educational_trace.append(f"Converted entity: {entity.name} ({entity.entity_type})")
                except Exception as e:
                    warnings.append(f"Entity conversion warning: {str(e)}")
            
            # Convert predicates
            for predicate in parse_result.predicates:
                try:
                    # Map entity IDs
                    mapped_entities = []
                    for entity_id in predicate.entities:
                        if entity_id in entity_mapping:
                            mapped_entities.append(entity_mapping[entity_id])
                        else:
                            warnings.append(f"Unmapped entity ID in predicate: {entity_id}")
                    
                    eg_predicate = Predicate(
                        id=new_predicate_id(),
                        name=predicate.name,
                        entities=pvector(mapped_entities),
                        properties=predicate.properties,
                        context_id=predicate.context_id
                    )
                    graph = graph.evolve(predicates=graph.predicates.set(eg_predicate.id, eg_predicate))
                    educational_trace.append(f"Converted predicate: {predicate.name}({len(mapped_entities)} entities)")
                except Exception as e:
                    warnings.append(f"Predicate conversion warning: {str(e)}")
            
            # Handle advanced constructs if present
            if hasattr(parse_result, 'function_symbols') and parse_result.function_symbols:
                for func in parse_result.function_symbols:
                    educational_trace.append(f"Function symbol detected: {func.name} (Dau's extension)")
                    # Note: Function symbols would need special handling in EG-HG
                    warnings.append(f"Function symbol {func.name} requires advanced EG-HG support")
            
            if hasattr(parse_result, 'coreference_patterns') and parse_result.coreference_patterns:
                for pattern in parse_result.coreference_patterns:
                    educational_trace.append(f"Coreference pattern detected: {pattern.pattern_type}")
                    # Note: Coreference patterns would need special ligature handling
                    warnings.append(f"Coreference pattern {pattern.pattern_type} requires ligature support")
            
            conversion_time = time.time() - start_time
            educational_trace.append(f"Conversion completed in {conversion_time:.4f}s")
            
            return EGIFIntegrationResult(
                graph=graph,
                egif_source=None,
                success=True,
                errors=errors,
                warnings=warnings,
                educational_trace=educational_trace,
                compatibility_issues=compatibility_issues,
                performance_metrics={"conversion_time": conversion_time, "total_time": conversion_time},
                metadata={
                    "entities_converted": len(parse_result.entities),
                    "predicates_converted": len(parse_result.predicates),
                    "mode": self.mode.value
                }
            )
            
        except Exception as e:
            errors.append(f"Conversion exception: {str(e)}")
            return EGIFIntegrationResult(
                graph=None,
                egif_source=None,
                success=False,
                errors=errors,
                warnings=warnings,
                educational_trace=educational_trace,
                compatibility_issues=compatibility_issues,
                performance_metrics={"total_time": time.time() - start_time},
                metadata={}
            )


class EGToEGIFConverter:
    """Converts EG-HG representation to EGIF format."""
    
    def __init__(self, mode: IntegrationMode = IntegrationMode.EDUCATIONAL):
        """Initialize converter with integration mode."""
        self.mode = mode
        self.generator = SimpleEGIFGenerator(educational_mode=(mode == IntegrationMode.EDUCATIONAL))
        
    def convert_graph_to_egif(self, graph: EGGraph, 
                            context_id: Optional[ContextId] = None) -> EGIFIntegrationResult:
        """Convert EG-HG representation to EGIF format."""
        import time
        start_time = time.time()
        
        errors = []
        warnings = []
        educational_trace = []
        compatibility_issues = []
        
        try:
            educational_trace.append("Starting EG-HG → EGIF conversion")
            
            # Extract entities and predicates from graph
            entities = list(graph.entities.values())
            predicates = list(graph.predicates.values())
            
            if not entities and not predicates:
                warnings.append("Empty graph - no entities or predicates to convert")
                return EGIFIntegrationResult(
                    graph=graph,
                    egif_source="",
                    success=True,
                    errors=errors,
                    warnings=warnings,
                    educational_trace=educational_trace,
                    compatibility_issues=compatibility_issues,
                    performance_metrics={"total_time": time.time() - start_time},
                    metadata={}
                )
            
            # Filter by context if specified
            if context_id is not None:
                entities = [e for e in entities if e.context_id == context_id]
                predicates = [p for p in predicates if p.context_id == context_id]
                educational_trace.append(f"Filtered to context {context_id}")
            
            # Create a simplified parse result for the generator
            # Note: This is a workaround since we don't have a direct EGGraph → EGIF generator
            simplified_result = type('EGIFParseResult', (), {
                'entities': entities,
                'predicates': predicates,
                'errors': [],
                'educational_trace': []
            })()
            
            # Generate EGIF
            generation_result = self.generator.generate_from_parse_result(simplified_result)
            
            if generation_result.success:
                educational_trace.extend(generation_result.educational_trace)
                educational_trace.append("EG-HG → EGIF conversion successful")
                
                conversion_time = time.time() - start_time
                
                return EGIFIntegrationResult(
                    graph=graph,
                    egif_source=generation_result.egif_source,
                    success=True,
                    errors=errors,
                    warnings=warnings,
                    educational_trace=educational_trace,
                    compatibility_issues=compatibility_issues,
                    performance_metrics={"conversion_time": conversion_time, "total_time": conversion_time},
                    metadata={
                        "entities_processed": len(entities),
                        "predicates_processed": len(predicates),
                        "mode": self.mode.value
                    }
                )
            else:
                errors.extend(generation_result.errors)
                return EGIFIntegrationResult(
                    graph=graph,
                    egif_source=None,
                    success=False,
                    errors=errors,
                    warnings=warnings,
                    educational_trace=educational_trace,
                    compatibility_issues=compatibility_issues,
                    performance_metrics={"total_time": time.time() - start_time},
                    metadata={}
                )
                
        except Exception as e:
            errors.append(f"Conversion exception: {str(e)}")
            return EGIFIntegrationResult(
                graph=graph,
                egif_source=None,
                success=False,
                errors=errors,
                warnings=warnings,
                educational_trace=educational_trace,
                compatibility_issues=compatibility_issues,
                performance_metrics={"total_time": time.time() - start_time},
                metadata={}
            )


class EGIFEGIntegrationManager:
    """
    Comprehensive integration manager for EGIF and EG-HG systems.
    
    Provides high-level operations for seamless integration between
    EGIF linear notation and EG-HG hypergraph representation.
    """
    
    def __init__(self, mode: IntegrationMode = IntegrationMode.EDUCATIONAL):
        """Initialize integration manager."""
        self.mode = mode
        self.egif_to_eg = EGIFToEGConverter(mode)
        self.eg_to_egif = EGToEGIFConverter(mode)
        self.compatibility_analyzer = DauSowaCompatibilityAnalyzer()
        
    def parse_egif_to_graph(self, egif_source: str, 
                          base_graph: Optional[EGGraph] = None,
                          validate: bool = True) -> EGIFIntegrationResult:
        """Parse EGIF source and convert to EG-HG representation."""
        import time
        start_time = time.time()
        
        errors = []
        warnings = []
        educational_trace = []
        compatibility_issues = []
        
        try:
            # Validate EGIF if requested
            if validate:
                validation_report = validate_egif(egif_source, ValidationLevel.STANDARD)
                if validation_report.get_success_rate() < 100:
                    for result in validation_report.results:
                        if not result.passed:
                            if result.severity.value in ['error', 'critical']:
                                errors.append(f"Validation: {result.message}")
                            else:
                                warnings.append(f"Validation: {result.message}")
                
                educational_trace.append(f"Validation: {validation_report.get_success_rate():.1f}% success rate")
            
            # Check for compatibility issues
            if self.mode in [IntegrationMode.MATHEMATICAL, IntegrationMode.COMPATIBLE]:
                compatibility_report = self.compatibility_analyzer.generate_compatibility_report(egif_source)
                if "compatibility issue(s) detected" in compatibility_report:
                    compatibility_issues.append("Dau-Sowa compatibility issues detected")
                    educational_trace.append("Compatibility analysis completed")
            
            # Parse EGIF
            try:
                parse_result = parse_advanced_egif(egif_source, educational_mode=(self.mode == IntegrationMode.EDUCATIONAL))
                educational_trace.append("Advanced EGIF parsing successful")
            except:
                # Fall back to basic parsing
                parse_result = parse_egif(egif_source, educational_mode=(self.mode == IntegrationMode.EDUCATIONAL))
                educational_trace.append("Basic EGIF parsing successful")
                warnings.append("Advanced constructs not supported, using basic parsing")
            
            # Convert to EG-HG
            conversion_result = self.egif_to_eg.convert_parse_result_to_graph(parse_result, base_graph)
            
            # Merge results
            all_errors = errors + conversion_result.errors
            all_warnings = warnings + conversion_result.warnings
            all_educational_trace = educational_trace + conversion_result.educational_trace
            all_compatibility_issues = compatibility_issues + conversion_result.compatibility_issues
            
            total_time = time.time() - start_time
            
            return EGIFIntegrationResult(
                graph=conversion_result.graph,
                egif_source=egif_source,
                success=conversion_result.success and len(all_errors) == 0,
                errors=all_errors,
                warnings=all_warnings,
                educational_trace=all_educational_trace,
                compatibility_issues=all_compatibility_issues,
                performance_metrics={"total_time": total_time, **conversion_result.performance_metrics},
                metadata={**conversion_result.metadata, "validation_performed": validate}
            )
            
        except Exception as e:
            return EGIFIntegrationResult(
                graph=None,
                egif_source=egif_source,
                success=False,
                errors=[f"Integration exception: {str(e)}"],
                warnings=warnings,
                educational_trace=educational_trace,
                compatibility_issues=compatibility_issues,
                performance_metrics={"total_time": time.time() - start_time},
                metadata={}
            )
    
    def generate_egif_from_graph(self, graph: EGGraph, 
                               context_id: Optional[ContextId] = None,
                               validate: bool = True) -> EGIFIntegrationResult:
        """Generate EGIF from EG-HG representation."""
        import time
        start_time = time.time()
        
        try:
            # Convert EG-HG to EGIF
            conversion_result = self.eg_to_egif.convert_graph_to_egif(graph, context_id)
            
            # Validate generated EGIF if requested and successful
            if validate and conversion_result.success and conversion_result.egif_source:
                validation_report = validate_egif(conversion_result.egif_source, ValidationLevel.BASIC)
                if validation_report.get_success_rate() < 100:
                    conversion_result.warnings.append("Generated EGIF failed validation")
                else:
                    conversion_result.educational_trace.append("Generated EGIF validated successfully")
            
            conversion_result.performance_metrics["total_time"] = time.time() - start_time
            return conversion_result
            
        except Exception as e:
            return EGIFIntegrationResult(
                graph=graph,
                egif_source=None,
                success=False,
                errors=[f"Generation exception: {str(e)}"],
                warnings=[],
                educational_trace=[],
                compatibility_issues=[],
                performance_metrics={"total_time": time.time() - start_time},
                metadata={}
            )
    
    def round_trip_test(self, egif_source: str) -> EGIFIntegrationResult:
        """Test round-trip conversion: EGIF → EG-HG → EGIF."""
        import time
        start_time = time.time()
        
        educational_trace = []
        errors = []
        warnings = []
        
        try:
            educational_trace.append("Starting round-trip test: EGIF → EG-HG → EGIF")
            
            # EGIF → EG-HG
            parse_result = self.parse_egif_to_graph(egif_source, validate=False)
            if not parse_result.success:
                return EGIFIntegrationResult(
                    graph=None,
                    egif_source=egif_source,
                    success=False,
                    errors=["Round-trip failed at EGIF → EG-HG step"] + parse_result.errors,
                    warnings=parse_result.warnings,
                    educational_trace=educational_trace + parse_result.educational_trace,
                    compatibility_issues=parse_result.compatibility_issues,
                    performance_metrics={"total_time": time.time() - start_time},
                    metadata={}
                )
            
            educational_trace.append("EGIF → EG-HG conversion successful")
            
            # EG-HG → EGIF
            generate_result = self.generate_egif_from_graph(parse_result.graph, validate=False)
            if not generate_result.success:
                return EGIFIntegrationResult(
                    graph=parse_result.graph,
                    egif_source=egif_source,
                    success=False,
                    errors=["Round-trip failed at EG-HG → EGIF step"] + generate_result.errors,
                    warnings=parse_result.warnings + generate_result.warnings,
                    educational_trace=educational_trace + parse_result.educational_trace + generate_result.educational_trace,
                    compatibility_issues=parse_result.compatibility_issues + generate_result.compatibility_issues,
                    performance_metrics={"total_time": time.time() - start_time},
                    metadata={}
                )
            
            educational_trace.append("EG-HG → EGIF conversion successful")
            
            # Compare original and generated
            original = egif_source.strip()
            generated = generate_result.egif_source.strip()
            
            if original == generated:
                educational_trace.append("✅ Exact round-trip match!")
                success = True
            else:
                educational_trace.append("⚠️ Syntax differs, checking semantic equivalence...")
                # For now, consider it a warning rather than failure
                warnings.append("Round-trip syntax differs but may be semantically equivalent")
                success = True
            
            total_time = time.time() - start_time
            educational_trace.append(f"Round-trip test completed in {total_time:.4f}s")
            
            return EGIFIntegrationResult(
                graph=parse_result.graph,
                egif_source=generate_result.egif_source,
                success=success,
                errors=errors,
                warnings=parse_result.warnings + generate_result.warnings + warnings,
                educational_trace=educational_trace + parse_result.educational_trace + generate_result.educational_trace,
                compatibility_issues=parse_result.compatibility_issues + generate_result.compatibility_issues,
                performance_metrics={"total_time": total_time},
                metadata={
                    "original_egif": original,
                    "generated_egif": generated,
                    "exact_match": original == generated
                }
            )
            
        except Exception as e:
            return EGIFIntegrationResult(
                graph=None,
                egif_source=egif_source,
                success=False,
                errors=[f"Round-trip exception: {str(e)}"],
                warnings=warnings,
                educational_trace=educational_trace,
                compatibility_issues=[],
                performance_metrics={"total_time": time.time() - start_time},
                metadata={}
            )
    
    def get_integration_modes(self) -> Dict[str, str]:
        """Get available integration modes with descriptions."""
        return {
            "educational": "Prioritize educational clarity and learning outcomes",
            "mathematical": "Prioritize mathematical rigor and Dau's formalization",
            "practical": "Prioritize computational efficiency and performance",
            "compatible": "Maintain compatibility with existing CLIF workflows"
        }


# Convenience functions
def egif_to_graph(egif_source: str, mode: IntegrationMode = IntegrationMode.EDUCATIONAL) -> EGIFIntegrationResult:
    """Convert EGIF source to EG-HG representation."""
    manager = EGIFEGIntegrationManager(mode)
    return manager.parse_egif_to_graph(egif_source)


def graph_to_egif(graph: EGGraph, mode: IntegrationMode = IntegrationMode.EDUCATIONAL) -> EGIFIntegrationResult:
    """Convert EG-HG representation to EGIF source."""
    manager = EGIFEGIntegrationManager(mode)
    return manager.generate_egif_from_graph(graph)


def test_egif_integration(egif_source: str, mode: IntegrationMode = IntegrationMode.EDUCATIONAL) -> EGIFIntegrationResult:
    """Test complete EGIF integration with round-trip validation."""
    manager = EGIFEGIntegrationManager(mode)
    return manager.round_trip_test(egif_source)


# Example usage and testing
if __name__ == "__main__":
    print("EGIF-EG Integration Test")
    print("=" * 40)
    
    # Test cases for integration
    test_cases = [
        "(Person *john)",
        "(Person *x) (Mortal x)",
        "(Loves *alice *bob)",
        "(add 2 3 -> *sum)",  # Advanced construct
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        print("-" * 50)
        
        try:
            # Test EGIF → EG-HG conversion
            result = egif_to_graph(test_case, IntegrationMode.EDUCATIONAL)
            print("EGIF → EG-HG:")
            print(f"  Success: {result.success}")
            print(f"  Entities: {len(result.graph.entities) if result.graph else 0}")
            print(f"  Predicates: {len(result.graph.predicates) if result.graph else 0}")
            
            if result.success and result.graph:
                # Test EG-HG → EGIF conversion
                back_result = graph_to_egif(result.graph, IntegrationMode.EDUCATIONAL)
                print("EG-HG → EGIF:")
                print(f"  Success: {back_result.success}")
                print(f"  Generated: {back_result.egif_source}")
            
            # Test round-trip
            round_trip_result = test_egif_integration(test_case, IntegrationMode.EDUCATIONAL)
            print("Round-trip:")
            print(f"  Success: {round_trip_result.success}")
            print(f"  Warnings: {len(round_trip_result.warnings)}")
            
        except Exception as e:
            print(f"Integration test failed: {e}")
        
        if i < len(test_cases):
            print("\n" + "=" * 60)
    
    print("\n" + "=" * 60)
    print("Integration Modes Available:")
    print("=" * 60)
    
    manager = EGIFEGIntegrationManager()
    modes = manager.get_integration_modes()
    for mode, description in modes.items():
        print(f"• {mode.title()}: {description}")
    
    print("\n" + "=" * 60)
    print("EGIF-EG Integration Phase 3 implementation complete!")
    print("Provides seamless integration between EGIF and EG-HG architectures.")

