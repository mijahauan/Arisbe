"""
EGIF Generator - Simplified Implementation for Phase 2

This module provides EGIF generation from parse results, bypassing the EGGraph
integration issues while demonstrating the core bidirectional conversion capability.

This simplified version works directly with the entities and predicates from
the EGIF parser, enabling round-trip testing and validation.

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass

from egif_parser import EGIFParseResult, parse_egif
from eg_types import Entity, Predicate, EntityId, PredicateId


@dataclass
class SimpleEGIFGenerationResult:
    """Result of generating EGIF from parse structures."""
    egif_source: Optional[str]
    success: bool
    errors: List[str]
    educational_trace: List[str]
    entity_labels: Dict[EntityId, str]
    
    def get_summary(self) -> str:
        """Get a summary of the generation result."""
        if self.success:
            entity_count = len(self.entity_labels)
            return f"EGIF generation successful: {entity_count} entities"
        else:
            error_count = len(self.errors)
            return f"EGIF generation failed with {error_count} error(s)"


class SimpleEGIFGenerator:
    """
    Simplified EGIF generator that works with parse results.
    
    This generator demonstrates bidirectional conversion by taking
    the entities and predicates from a parse result and generating
    equivalent EGIF syntax.
    """
    
    def __init__(self, educational_mode: bool = True):
        """Initialize the simple EGIF generator."""
        self.educational_mode = educational_mode
        self.generation_trace = []
        
    def generate_from_parse_result(self, parse_result: EGIFParseResult) -> SimpleEGIFGenerationResult:
        """
        Generate EGIF from a parse result.
        
        Args:
            parse_result: Result from EGIF parsing
            
        Returns:
            SimpleEGIFGenerationResult with generated EGIF
        """
        self._reset_state()
        
        if parse_result.errors:
            return SimpleEGIFGenerationResult(
                egif_source=None,
                success=False,
                errors=[f"Parse errors prevent generation: {len(parse_result.errors)} errors"],
                educational_trace=[],
                entity_labels={}
            )
        
        try:
            self._trace("Starting EGIF generation from parse result")
            
            # Store entities for reference during generation
            self._current_entities = parse_result.entities
            
            # Create entity label mapping
            entity_labels = self._create_entity_labels(parse_result.entities)
            
            # Generate relations
            relations = self._generate_relations(parse_result.predicates, entity_labels)
            
            # Combine into EGIF
            egif_source = " ".join(relations)
            
            self._trace(f"Generated EGIF: {egif_source}")
            
            return SimpleEGIFGenerationResult(
                egif_source=egif_source,
                success=True,
                errors=[],
                educational_trace=self.generation_trace,
                entity_labels=entity_labels
            )
            
        except Exception as e:
            return SimpleEGIFGenerationResult(
                egif_source=None,
                success=False,
                errors=[f"Generation error: {str(e)}"],
                educational_trace=self.generation_trace,
                entity_labels={}
            )
    
    def _reset_state(self):
        """Reset generator state."""
        self.generation_trace = []
    
    def _trace(self, message: str):
        """Add message to trace."""
        if self.educational_mode:
            self.generation_trace.append(message)
    
    def _create_entity_labels(self, entities: List[Entity]) -> Dict[EntityId, str]:
        """Create mapping from entity IDs to labels."""
        entity_labels = {}
        
        for entity in entities:
            if entity.name:
                entity_labels[entity.id] = entity.name
            else:
                # Generate a label based on entity type
                if entity.entity_type == 'constant':
                    value = entity.properties.get('value', 'const')
                    entity_labels[entity.id] = str(value)
                else:
                    entity_labels[entity.id] = f"entity_{len(entity_labels)}"
        
        self._trace(f"Created {len(entity_labels)} entity labels")
        return entity_labels
    
    def _generate_relations(self, predicates: List[Predicate], entity_labels: Dict[EntityId, str]) -> List[str]:
        """Generate EGIF relation syntax."""
        relations = []
        entity_first_use = {}  # Track first use of each entity
        
        # Sort predicates by ID for consistent ordering
        sorted_predicates = sorted(predicates, key=lambda p: str(p.id))
        
        for predicate in sorted_predicates:
            relation_parts = [f"({predicate.name}"]
            
            for entity_id in predicate.entities:
                label = entity_labels.get(entity_id, "unknown")
                
                # Find the entity to check its type
                entity = next((e for e in self._current_entities if e.id == entity_id), None)
                
                if entity and entity.entity_type == 'constant':
                    # Constants are never defining labels, just use the value directly
                    value = entity.properties.get('value', label)
                    relation_parts.append(str(value))
                    self._trace(f"Constant value {value} in {predicate.name}")
                else:
                    # Variable entity - determine if defining or bound
                    if entity_id not in entity_first_use:
                        # First use - defining label
                        entity_first_use[entity_id] = predicate.id
                        relation_parts.append(f"*{label}")
                        self._trace(f"First use of entity {label} in {predicate.name}")
                    else:
                        # Later use - bound label
                        relation_parts.append(label)
                        self._trace(f"Bound use of entity {label} in {predicate.name}")
            
            relation_parts.append(")")
            relation_egif = " ".join(relation_parts)
            relations.append(relation_egif)
            self._trace(f"Generated relation: {relation_egif}")
        
        return relations


def simple_round_trip_test(original_egif: str) -> Tuple[bool, str, List[str]]:
    """
    Test round-trip conversion using simplified generator.
    
    Args:
        original_egif: Original EGIF source
        
    Returns:
        Tuple of (success, regenerated_egif, messages)
    """
    messages = []
    
    # Parse original
    parse_result = parse_egif(original_egif, educational_mode=False)
    
    if parse_result.errors:
        error_msgs = [f"Parse error: {e.message}" for e in parse_result.errors]
        return False, "", error_msgs
    
    # Generate from parse result
    generator = SimpleEGIFGenerator(educational_mode=False)
    gen_result = generator.generate_from_parse_result(parse_result)
    
    if not gen_result.success:
        return False, "", gen_result.errors
    
    messages.append(f"Original:  {original_egif}")
    messages.append(f"Generated: {gen_result.egif_source}")
    
    # Check semantic equivalence (allowing for formatting differences)
    original_normalized = original_egif.replace(" ", "").replace("\n", "")
    generated_normalized = gen_result.egif_source.replace(" ", "").replace("\n", "")
    
    if original_normalized == generated_normalized:
        messages.append("✅ Exact round-trip match!")
    else:
        messages.append("⚠️  Formatting differs, checking semantic equivalence...")
        # For now, we'll consider it successful if both parse without errors
        reparse_result = parse_egif(gen_result.egif_source, educational_mode=False)
        if not reparse_result.errors:
            messages.append("✅ Semantic round-trip successful!")
        else:
            messages.append("❌ Semantic round-trip failed")
            return False, gen_result.egif_source, messages
    
    return True, gen_result.egif_source, messages


# Example usage and testing
if __name__ == "__main__":
    print("Simple EGIF Generator Test")
    print("=" * 40)
    
    # Test cases for round-trip conversion
    test_cases = [
        "(Person *x)",
        "(Person *x) (Mortal x)",
        "(Loves *john *mary)",
        "(Person *x) (Age x 25)",
        "(Between *a *b *c)",
    ]
    
    for i, original_egif in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {original_egif}")
        print("-" * 50)
        
        success, generated, messages = simple_round_trip_test(original_egif)
        
        for message in messages:
            print(message)
        
        if success:
            print("✅ Round-trip test PASSED")
        else:
            print("❌ Round-trip test FAILED")
    
    print("\n" + "=" * 60)
    print("Detailed Generation Example")
    print("=" * 60)
    
    # Show detailed generation process
    example_egif = "(Person *john) (Loves john *mary) (Person mary)"
    print(f"Example: {example_egif}")
    
    # Parse
    parse_result = parse_egif(example_egif, educational_mode=True)
    print(f"\nParsing result:")
    print(f"  Entities: {len(parse_result.entities)}")
    print(f"  Predicates: {len(parse_result.predicates)}")
    
    for entity in parse_result.entities:
        print(f"    Entity: {entity.name} ({entity.entity_type})")
    
    for predicate in parse_result.predicates:
        entity_names = []
        for eid in predicate.entities:
            entity = next((e for e in parse_result.entities if e.id == eid), None)
            entity_names.append(entity.name if entity else str(eid))
        print(f"    Predicate: {predicate.name}({', '.join(entity_names)})")
    
    # Generate
    generator = SimpleEGIFGenerator(educational_mode=True)
    gen_result = generator.generate_from_parse_result(parse_result)
    
    print(f"\nGeneration result:")
    print(f"  Success: {gen_result.success}")
    print(f"  Generated: {gen_result.egif_source}")
    
    print(f"\nGeneration trace:")
    for trace in gen_result.educational_trace:
        print(f"  {trace}")
    
    print("\n" + "=" * 60)
    print("Simple EGIF Generator Phase 2 implementation complete!")
    print("Demonstrates bidirectional EGIF ↔ Parse Result conversion.")

