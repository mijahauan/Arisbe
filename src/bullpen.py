"""
Constrained Composition System (Bullpen)

This module provides tools for creating and composing new existential graphs
with syntactic validation and game-readiness checking. The "bullpen" metaphor
refers to the preparation area where new graphs are composed and validated
before being introduced into the game.

Updated for Entity-Predicate hypergraph architecture where:
- CLIF terms (variables, constants) → Entities (Lines of Identity)
- CLIF predicates → Predicates (hyperedges connecting entities)
- CLIF quantifiers → Entity scoping in contexts

The system ensures that only syntactically valid graphs can be created,
provides real-time validation feedback, and offers preview capabilities
for understanding how a proposed graph would behave in the game context.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, replace
from enum import Enum
import uuid

from eg_types import (
    Entity, Predicate, Context, Ligature, 
    EntityId, PredicateId, ContextId, LigatureId, ItemId
)
from graph import EGGraph
from context import ContextManager
from game_engine import EndoporeuticGameEngine, GameState, Player
from clif_parser import CLIFParser
from pattern_recognizer import PatternRecognitionEngine


class ValidationLevel(Enum):
    """Levels of validation for graph composition."""
    SYNTAX_ONLY = "syntax_only"
    SEMANTIC = "semantic"
    GAME_READY = "game_ready"
    FULL = "full"


class CompositionMode(Enum):
    """Modes for graph composition."""
    BLANK_SHEET = "blank_sheet"
    FROM_TEMPLATE = "from_template"
    FROM_CLIF = "from_clif"
    EXTEND_EXISTING = "extend_existing"


@dataclass(frozen=True)
class ValidationResult:
    """Result of graph validation."""
    is_valid: bool
    level: ValidationLevel
    messages: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any error messages."""
        return not self.is_valid or bool(self.messages)
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return bool(self.warnings)


@dataclass(frozen=True)
class CompositionTemplate:
    """Template for common graph patterns."""
    name: str
    description: str
    category: str
    base_graph: EGGraph
    parameters: Dict[str, Any]
    usage_hints: List[str]
    
    def instantiate(self, parameter_values: Dict[str, Any]) -> EGGraph:
        """Create a graph instance from this template with given parameters."""
        # This would implement template instantiation logic
        # For now, return the base graph
        return self.base_graph


@dataclass(frozen=True)
class GamePreview:
    """Preview of how a graph would behave in the game."""
    thesis_graph: EGGraph
    initial_game_state: Optional[GameState]
    contested_context: Optional[ContextId]
    legal_moves_preview: List[str]
    complexity_assessment: str
    strategic_notes: List[str]


class GraphCompositionTool:
    """
    Main tool for constrained composition of existential graphs.
    
    Provides a safe environment for creating and modifying graphs with
    real-time validation and game-readiness checking.
    
    Updated for Entity-Predicate architecture.
    """
    
    def __init__(self):
        self.parser = CLIFParser()
        self.pattern_recognizer = PatternRecognitionEngine()
        self.game_engine = EndoporeuticGameEngine()
        self.templates: Dict[str, CompositionTemplate] = {}
        self._load_default_templates()
    
    def create_blank_sheet(self) -> EGGraph:
        """Create a blank sheet of assertion for composition."""
        return EGGraph.create_empty()
    
    def create_from_template(self, template_name: str, 
                           parameters: Dict[str, Any]) -> Tuple[EGGraph, ValidationResult]:
        """Create a graph from a template with given parameters."""
        if template_name not in self.templates:
            return (
                self.create_blank_sheet(),
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Template '{template_name}' not found"],
                    warnings=[],
                    suggestions=[f"Available templates: {list(self.templates.keys())}"]
                )
            )
        
        template = self.templates[template_name]
        try:
            graph = template.instantiate(parameters)
            validation = self.validate_graph(graph, ValidationLevel.SYNTAX_ONLY)
            return graph, validation
        except Exception as e:
            return (
                self.create_blank_sheet(),
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Template instantiation failed: {str(e)}"],
                    warnings=[],
                    suggestions=template.usage_hints
                )
            )
    
    def create_from_clif(self, clif_text: str) -> Tuple[EGGraph, ValidationResult]:
        """Create a graph by parsing CLIF text."""
        try:
            parse_result = self.parser.parse(clif_text)
            if not parse_result.success:
                return (
                    self.create_blank_sheet(),
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.SYNTAX_ONLY,
                        messages=[f"CLIF parsing failed: {parse_result.error}"],
                        warnings=[],
                        suggestions=["Check CLIF syntax", "Use simpler expressions"]
                    )
                )
            
            graph = parse_result.graph
            validation = self.validate_graph(graph, ValidationLevel.SEMANTIC)
            return graph, validation
            
        except Exception as e:
            return (
                self.create_blank_sheet(),
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Unexpected error: {str(e)}"],
                    warnings=[],
                    suggestions=["Check input format", "Try simpler expressions"]
                )
            )
    
    def add_entity(self, graph: EGGraph, name: str, entity_type: str = 'variable',
                   context_id: Optional[ContextId] = None) -> Tuple[EGGraph, ValidationResult]:
        """Add an entity (Line of Identity) to the graph."""
        if context_id is None:
            context_id = graph.root_context_id
        
        # Create entity
        entity = Entity.create(
            name=name,
            entity_type=entity_type,
            properties={}
        )
        
        try:
            new_graph = graph.add_entity(entity, context_id)
            validation = self.validate_graph(new_graph, ValidationLevel.SYNTAX_ONLY)
            return new_graph, validation
        except Exception as e:
            return (
                graph,
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Failed to add entity: {str(e)}"],
                    warnings=[],
                    suggestions=["Check entity name", "Verify context exists"]
                )
            )
    
    def add_predicate(self, graph: EGGraph, name: str, entity_ids: List[EntityId],
                     context_id: Optional[ContextId] = None) -> Tuple[EGGraph, ValidationResult]:
        """Add a predicate (hyperedge) connecting entities to the graph."""
        if context_id is None:
            context_id = graph.root_context_id
        
        # Validate that all entities exist
        for entity_id in entity_ids:
            if entity_id not in graph.entities:
                return (
                    graph,
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.SYNTAX_ONLY,
                        messages=[f"Entity {entity_id} does not exist"],
                        warnings=[],
                        suggestions=["Create entities before connecting them with predicates"]
                    )
                )
        
        # Create predicate
        predicate = Predicate.create(
            name=name,
            entities=entity_ids,
            arity=len(entity_ids),
            properties={}
        )
        
        try:
            new_graph = graph.add_predicate(predicate, context_id)
            validation = self.validate_graph(new_graph, ValidationLevel.SYNTAX_ONLY)
            return new_graph, validation
        except Exception as e:
            return (
                graph,
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Failed to add predicate: {str(e)}"],
                    warnings=[],
                    suggestions=["Check predicate name", "Verify all entities exist", "Verify context exists"]
                )
            )
    
    def add_context(self, graph: EGGraph, context_type: str, parent_id: Optional[ContextId] = None,
                   name: Optional[str] = None) -> Tuple[EGGraph, ValidationResult]:
        """Add a new context (cut) to the graph."""
        if parent_id is None:
            parent_id = graph.root_context_id
        
        try:
            new_graph, new_context = graph.create_context(context_type, parent_id, name)
            validation = self.validate_graph(new_graph, ValidationLevel.SYNTAX_ONLY)
            return new_graph, validation
        except Exception as e:
            return (
                graph,
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Failed to add context: {str(e)}"],
                    warnings=[],
                    suggestions=["Check context type", "Verify parent context exists"]
                )
            )
    
    def remove_item(self, graph: EGGraph, item_id: ItemId) -> Tuple[EGGraph, ValidationResult]:
        """Remove an item from the graph."""
        try:
            if item_id in graph.entities:
                new_graph = graph.remove_entity(item_id)
            elif item_id in graph.predicates:
                new_graph = graph.remove_predicate(item_id)
            elif item_id in graph.context_manager.contexts:
                new_graph = graph.remove_context(item_id)
            else:
                return (
                    graph,
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.SYNTAX_ONLY,
                        messages=[f"Item {item_id} not found"],
                        warnings=[],
                        suggestions=["Check item ID", "Refresh graph view"]
                    )
                )
            
            validation = self.validate_graph(new_graph, ValidationLevel.SYNTAX_ONLY)
            return new_graph, validation
        except Exception as e:
            return (
                graph,
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Failed to remove item: {str(e)}"],
                    warnings=[],
                    suggestions=["Check for dependencies", "Remove connected items first"]
                )
            )
    
    def move_item(self, graph: EGGraph, item_id: ItemId, 
                 target_context: ContextId) -> Tuple[EGGraph, ValidationResult]:
        """Move an item to a different context."""
        try:
            # Remove from current context and add to target context
            if item_id in graph.entities:
                entity = graph.entities[item_id]
                new_graph = graph.remove_entity(item_id)
                new_graph = new_graph.add_entity(entity, target_context)
            elif item_id in graph.predicates:
                predicate = graph.predicates[item_id]
                new_graph = graph.remove_predicate(item_id)
                new_graph = new_graph.add_predicate(predicate, target_context)
            else:
                return (
                    graph,
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.SYNTAX_ONLY,
                        messages=[f"Item {item_id} not found or cannot be moved"],
                        warnings=[],
                        suggestions=["Check item ID", "Contexts cannot be moved this way"]
                    )
                )
            
            validation = self.validate_graph(new_graph, ValidationLevel.SYNTAX_ONLY)
            return new_graph, validation
        except Exception as e:
            return (
                graph,
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Failed to move item: {str(e)}"],
                    warnings=[],
                    suggestions=["Check target context exists", "Verify move is legal"]
                )
            )
    
    def validate_graph(self, graph: EGGraph, level: ValidationLevel) -> ValidationResult:
        """Validate a graph at the specified level."""
        messages = []
        warnings = []
        suggestions = []
        is_valid = True
        
        try:
            # Syntax validation
            if level in [ValidationLevel.SYNTAX_ONLY, ValidationLevel.SEMANTIC, 
                        ValidationLevel.GAME_READY, ValidationLevel.FULL]:
                syntax_result = self._validate_syntax(graph)
                if not syntax_result.is_valid:
                    is_valid = False
                    messages.extend(syntax_result.messages)
                warnings.extend(syntax_result.warnings)
                suggestions.extend(syntax_result.suggestions)
            
            # Semantic validation
            if level in [ValidationLevel.SEMANTIC, ValidationLevel.GAME_READY, ValidationLevel.FULL]:
                semantic_result = self._validate_semantics(graph)
                if not semantic_result.is_valid:
                    warnings.extend(semantic_result.messages)  # Semantic issues are warnings
                warnings.extend(semantic_result.warnings)
                suggestions.extend(semantic_result.suggestions)
            
            # Game readiness validation
            if level in [ValidationLevel.GAME_READY, ValidationLevel.FULL]:
                game_result = self._validate_game_readiness(graph)
                if not game_result.is_valid:
                    warnings.extend(game_result.messages)  # Game issues are warnings
                warnings.extend(game_result.warnings)
                suggestions.extend(game_result.suggestions)
            
        except Exception as e:
            is_valid = False
            messages.append(f"Validation error: {str(e)}")
            suggestions.append("Check graph structure")
        
        return ValidationResult(
            is_valid=is_valid,
            level=level,
            messages=messages,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_syntax(self, graph: EGGraph) -> ValidationResult:
        """Validate syntactic correctness of the graph."""
        messages = []
        warnings = []
        suggestions = []
        
        # Check entity consistency
        for predicate in graph.predicates.values():
            for entity_id in predicate.entities:
                if entity_id not in graph.entities:
                    messages.append(f"Predicate {predicate.name} references non-existent entity {entity_id}")
                    suggestions.append("Remove invalid predicate or add missing entity")
        
        # Check context hierarchy
        for context in graph.context_manager.contexts.values():
            if context.parent_context and context.parent_context not in graph.context_manager.contexts:
                messages.append(f"Context {context.id} has invalid parent reference")
                suggestions.append("Fix context hierarchy")
        
        # Check for orphaned items
        for entity in graph.entities.values():
            entity_context = graph.context_manager.find_item_context(entity.id)
            if entity_context is None:
                warnings.append(f"Entity {entity.name} is not in any context")
                suggestions.append("Place entities in appropriate contexts")
        
        for predicate in graph.predicates.values():
            predicate_context = graph.context_manager.find_item_context(predicate.id)
            if predicate_context is None:
                warnings.append(f"Predicate {predicate.name} is not in any context")
                suggestions.append("Place predicates in appropriate contexts")
        
        is_valid = len(messages) == 0
        return ValidationResult(is_valid, ValidationLevel.SYNTAX_ONLY, messages, warnings, suggestions)
    
    def _validate_semantics(self, graph: EGGraph) -> ValidationResult:
        """Validate semantic correctness of the graph."""
        messages = []
        warnings = []
        suggestions = []
        
        # Check for meaningful content
        if len(graph.entities) == 0 and len(graph.predicates) == 0:
            warnings.append("Graph contains no entities or predicates")
            suggestions.append("Add some content to make the graph meaningful")
        
        # Check for isolated entities
        for entity in graph.entities.values():
            connected_predicates = [p for p in graph.predicates.values() if entity.id in p.entities]
            if not connected_predicates:
                warnings.append(f"Entity {entity.name} is not connected to any predicates")
                suggestions.append("Connect entities to predicates or remove unused entities")
        
        # Check for zero-arity predicates (which are valid but unusual)
        zero_arity_predicates = [p for p in graph.predicates.values() if p.arity == 0]
        if zero_arity_predicates:
            warnings.append(f"Found {len(zero_arity_predicates)} zero-arity predicates")
            suggestions.append("Zero-arity predicates represent propositions without arguments")
        
        is_valid = True  # Semantic issues are warnings, not errors
        return ValidationResult(is_valid, ValidationLevel.SEMANTIC, messages, warnings, suggestions)
    
    def _validate_game_readiness(self, graph: EGGraph) -> ValidationResult:
        """Validate that the graph is ready for game play."""
        messages = []
        warnings = []
        suggestions = []
        
        # Check for sufficient complexity
        total_items = len(graph.entities) + len(graph.predicates)
        if total_items < 2:
            warnings.append("Graph may be too simple for interesting game play")
            suggestions.append("Add more entities and predicates for richer game dynamics")
        
        # Check for nested contexts (needed for interesting transformations)
        max_depth = max((ctx.depth for ctx in graph.context_manager.contexts.values()), default=0)
        if max_depth < 2:
            warnings.append("Graph has no nested contexts")
            suggestions.append("Add cuts (nested contexts) to enable more transformation rules")
        
        # Check for quantified variables (entities in nested contexts)
        entities_in_nested_contexts = 0
        for entity in graph.entities.values():
            entity_context = graph.context_manager.find_item_context(entity.id)
            if entity_context:
                context = graph.context_manager.get_context(entity_context)
                if context and context.depth > 0:
                    entities_in_nested_contexts += 1
        
        if entities_in_nested_contexts == 0:
            warnings.append("No entities in nested contexts (no quantification)")
            suggestions.append("Place some entities in cuts to represent quantified variables")
        
        is_valid = True  # Game readiness issues are warnings
        return ValidationResult(is_valid, ValidationLevel.GAME_READY, messages, warnings, suggestions)
    
    def get_composition_suggestions(self, graph: EGGraph) -> List[str]:
        """Get suggestions for improving the graph composition."""
        suggestions = []
        
        # Analyze current structure
        entity_count = len(graph.entities)
        predicate_count = len(graph.predicates)
        context_count = len(graph.context_manager.contexts)
        
        if entity_count == 0:
            suggestions.append("Add entities to represent individuals or variables")
        
        if predicate_count == 0:
            suggestions.append("Add predicates to express relationships or properties")
        
        if context_count <= 1:
            suggestions.append("Add cuts (contexts) to express negation or quantification")
        
        # Check for common patterns
        if entity_count > 0 and predicate_count == 0:
            suggestions.append("Connect entities with predicates to express relationships")
        
        if predicate_count > entity_count * 2:
            suggestions.append("Consider adding more entities to balance the graph")
        
        # Pattern-based suggestions
        patterns = self.pattern_recognizer.analyze_graph(graph)
        if not patterns:
            suggestions.append("Consider using common logical patterns (universal quantification, implication)")
        
        return suggestions
    
    def preview_game_behavior(self, graph: EGGraph) -> GamePreview:
        """Preview how the graph would behave in the Endoporeutic Game."""
        try:
            # Create initial game state
            initial_state = self.game_engine.create_game_state(graph)
            
            # Find contested context (deepest positive context with content)
            contested_context = self._find_contested_context(graph)
            
            # Get preview of legal moves
            legal_moves = self.game_engine.get_legal_moves(initial_state)
            legal_moves_preview = [self._describe_move(move) for move in legal_moves[:5]]  # First 5 moves
            
            # Assess complexity
            complexity = self._assess_complexity(graph)
            
            # Generate strategic notes
            strategic_notes = self._generate_strategic_notes(graph, legal_moves)
            
            return GamePreview(
                thesis_graph=graph,
                initial_game_state=initial_state,
                contested_context=contested_context,
                legal_moves_preview=legal_moves_preview,
                complexity_assessment=complexity,
                strategic_notes=strategic_notes
            )
            
        except Exception as e:
            return GamePreview(
                thesis_graph=graph,
                initial_game_state=None,
                contested_context=None,
                legal_moves_preview=[f"Error generating preview: {str(e)}"],
                complexity_assessment="Unknown",
                strategic_notes=["Preview generation failed"]
            )
    
    def _find_contested_context(self, graph: EGGraph) -> Optional[ContextId]:
        """Find the context that would be contested in the game."""
        # Look for the deepest positive context with content
        best_context = None
        max_depth = -1
        
        for context in graph.context_manager.contexts.values():
            if context.depth % 2 == 0:  # Positive context
                items_in_context = graph.context_manager.get_items_in_context(context.id)
                if items_in_context and context.depth > max_depth:
                    max_depth = context.depth
                    best_context = context.id
        
        return best_context
    
    def _describe_move(self, move) -> str:
        """Generate a human-readable description of a game move."""
        # This would generate descriptions based on move type
        return f"{move.move_type.value} move"
    
    def _assess_complexity(self, graph: EGGraph) -> str:
        """Assess the complexity of the graph for game play."""
        total_items = len(graph.entities) + len(graph.predicates)
        max_depth = max((ctx.depth for ctx in graph.context_manager.contexts.values()), default=0)
        
        if total_items < 3:
            return "Simple"
        elif total_items < 8:
            return "Moderate"
        else:
            return "Complex"
    
    def _generate_strategic_notes(self, graph: EGGraph, legal_moves) -> List[str]:
        """Generate strategic notes about the graph."""
        notes = []
        
        # Analyze structure
        entity_count = len(graph.entities)
        predicate_count = len(graph.predicates)
        
        if entity_count > predicate_count:
            notes.append("Many entities suggest rich quantification opportunities")
        
        if predicate_count > entity_count:
            notes.append("Many predicates suggest complex relational structure")
        
        # Analyze contexts
        max_depth = max((ctx.depth for ctx in graph.context_manager.contexts.values()), default=0)
        if max_depth > 2:
            notes.append("Deep nesting enables sophisticated logical maneuvers")
        
        return notes
    
    def _load_default_templates(self):
        """Load default composition templates."""
        # Simple predicate template
        simple_graph = EGGraph.create_empty()
        self.templates["simple_predicate"] = CompositionTemplate(
            name="Simple Predicate",
            description="A single predicate with one entity",
            category="Basic",
            base_graph=simple_graph,
            parameters={"predicate_name": str, "entity_name": str},
            usage_hints=["Good for starting simple assertions"]
        )
        
        # Universal quantification template
        universal_graph = EGGraph.create_empty()
        self.templates["universal_quantification"] = CompositionTemplate(
            name="Universal Quantification",
            description="Pattern for universal quantification: ~[exists x ~[P(x)]]",
            category="Quantification",
            base_graph=universal_graph,
            parameters={"variable_name": str, "predicate_name": str},
            usage_hints=["Creates forall pattern", "Use for general statements"]
        )


# Convenience functions for common operations

def create_simple_assertion(predicate_name: str, entity_names: List[str]) -> EGGraph:
    """Create a simple assertion with one predicate and entities."""
    tool = GraphCompositionTool()
    graph = tool.create_blank_sheet()
    
    # Add entities
    entity_ids = []
    for entity_name in entity_names:
        graph, _ = tool.add_entity(graph, entity_name, 'constant')
        # Find the entity we just added
        for entity in graph.entities.values():
            if entity.name == entity_name:
                entity_ids.append(entity.id)
                break
    
    # Add predicate
    graph, _ = tool.add_predicate(graph, predicate_name, entity_ids)
    
    return graph


def create_existential_statement(variable_name: str, predicate_name: str) -> EGGraph:
    """Create an existential statement: exists x P(x)."""
    tool = GraphCompositionTool()
    graph = tool.create_blank_sheet()
    
    # Create positive context for existential scope
    graph, _ = tool.add_context(graph, 'assertion', graph.root_context_id, 'Existential Scope')
    
    # Find the context we just created
    existential_context = None
    for context in graph.context_manager.contexts.values():
        if context.parent_context == graph.root_context_id and context.depth == 1:
            existential_context = context.id
            break
    
    if existential_context:
        # Add variable in existential scope
        graph, _ = tool.add_entity(graph, variable_name, 'variable', existential_context)
        
        # Find the entity we just added
        variable_id = None
        for entity in graph.entities.values():
            if entity.name == variable_name:
                variable_id = entity.id
                break
        
        if variable_id:
            # Add predicate connecting to the variable
            graph, _ = tool.add_predicate(graph, predicate_name, [variable_id], existential_context)
    
    return graph


def create_universal_statement(variable_name: str, predicate_name: str) -> EGGraph:
    """Create a universal statement: forall x P(x) ≡ ~[exists x ~[P(x)]]."""
    tool = GraphCompositionTool()
    graph = tool.create_blank_sheet()
    
    # Create outer negation
    graph, _ = tool.add_context(graph, 'cut', graph.root_context_id, 'Universal Outer Cut')
    outer_cut = None
    for context in graph.context_manager.contexts.values():
        if context.parent_context == graph.root_context_id and context.depth == 1:
            outer_cut = context.id
            break
    
    if outer_cut:
        # Create existential scope inside outer cut
        graph, _ = tool.add_context(graph, 'assertion', outer_cut, 'Existential Scope')
        existential_context = None
        for context in graph.context_manager.contexts.values():
            if context.parent_context == outer_cut and context.depth == 2:
                existential_context = context.id
                break
        
        if existential_context:
            # Create inner negation
            graph, _ = tool.add_context(graph, 'cut', existential_context, 'Predicate Negation')
            inner_cut = None
            for context in graph.context_manager.contexts.values():
                if context.parent_context == existential_context and context.depth == 3:
                    inner_cut = context.id
                    break
            
            if inner_cut:
                # Add variable in existential scope
                graph, _ = tool.add_entity(graph, variable_name, 'variable', existential_context)
                
                # Find the entity we just added
                variable_id = None
                for entity in graph.entities.values():
                    if entity.name == variable_name:
                        variable_id = entity.id
                        break
                
                if variable_id:
                    # Add predicate in inner cut (negated)
                    graph, _ = tool.add_predicate(graph, predicate_name, [variable_id], inner_cut)
    
    return graph

