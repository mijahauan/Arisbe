"""
Constrained Composition System (Bullpen)

This module provides tools for creating and composing new existential graphs
with syntactic validation and game-readiness checking. The "bullpen" metaphor
refers to the preparation area where new graphs are composed and validated
before being introduced into the game.

The system ensures that only syntactically valid graphs can be created,
provides real-time validation feedback, and offers preview capabilities
for understanding how a proposed graph would behave in the game context.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, replace
from enum import Enum
import uuid

from .eg_types import (
    Node, Edge, Context, Ligature, NodeId, EdgeId, ContextId, 
    LigatureId, ItemId
)
from .graph import EGGraph
from .context import ContextManager
from .game_engine import EndoporeuticGameEngine, GameState, Player
from .clif_parser import CLIFParser
from .pattern_recognizer import PatternRecognitionEngine


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
    
    def add_predicate(self, graph: EGGraph, name: str, arity: int, 
                     context_id: Optional[ContextId] = None) -> Tuple[EGGraph, ValidationResult]:
        """Add a predicate node to the graph."""
        if context_id is None:
            context_id = graph.root_context_id
        
        # Create predicate node
        node_id = NodeId(uuid.uuid4())
        predicate_node = Node.create(
            id=node_id,
            node_type='predicate',
            properties={'name': name, 'arity': arity}
        )
        
        try:
            new_graph = graph.add_node(predicate_node, context_id)
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
                    suggestions=["Check context exists", "Verify predicate parameters"]
                )
            )
    
    def create_context(self, graph: EGGraph, context_type: str, 
                      parent_id: Optional[ContextId] = None,
                      name: Optional[str] = None) -> Tuple[EGGraph, Context, ValidationResult]:
        """Create a new context (cut) in the graph."""
        if parent_id is None:
            parent_id = graph.root_context_id
        
        try:
            new_graph, new_context = graph.create_context(context_type, parent_id, name)
            validation = self.validate_graph(new_graph, ValidationLevel.SYNTAX_ONLY)
            return new_graph, new_context, validation
        except Exception as e:
            return (
                graph,
                Context.create(ContextId(uuid.uuid4()), context_type, parent_id),
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Failed to create context: {str(e)}"],
                    warnings=[],
                    suggestions=["Check parent context exists", "Verify context type"]
                )
            )
    
    def add_ligature(self, graph: EGGraph, nodes: Set[NodeId]) -> Tuple[EGGraph, ValidationResult]:
        """Add a ligature connecting the specified nodes."""
        if len(nodes) < 2:
            return (
                graph,
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=["Ligature requires at least 2 nodes"],
                    warnings=[],
                    suggestions=["Select multiple nodes to connect"]
                )
            )
        
        # Verify all nodes exist
        for node_id in nodes:
            if node_id not in graph.nodes:
                return (
                    graph,
                    ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.SYNTAX_ONLY,
                        messages=[f"Node {node_id} not found in graph"],
                        warnings=[],
                        suggestions=["Verify node IDs are correct"]
                    )
                )
        
        try:
            ligature_id = LigatureId(uuid.uuid4())
            ligature = Ligature.create(ligature_id, nodes)
            new_graph = graph.add_ligature(ligature)
            validation = self.validate_graph(new_graph, ValidationLevel.SYNTAX_ONLY)
            return new_graph, validation
        except Exception as e:
            return (
                graph,
                ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.SYNTAX_ONLY,
                    messages=[f"Failed to add ligature: {str(e)}"],
                    warnings=[],
                    suggestions=["Check node compatibility", "Verify graph structure"]
                )
            )
    
    def validate_graph(self, graph: EGGraph, level: ValidationLevel) -> ValidationResult:
        """Validate a graph at the specified level."""
        messages = []
        warnings = []
        suggestions = []
        is_valid = True
        
        # Syntax validation
        try:
            syntax_result = self._validate_syntax(graph)
            if not syntax_result.is_valid:
                is_valid = False
                messages.extend(syntax_result.messages)
            warnings.extend(syntax_result.warnings)
            suggestions.extend(syntax_result.suggestions)
        except Exception as e:
            is_valid = False
            messages.append(f"Syntax validation error: {str(e)}")
        
        if level == ValidationLevel.SYNTAX_ONLY:
            return ValidationResult(is_valid, level, messages, warnings, suggestions)
        
        # Semantic validation
        if is_valid:
            try:
                semantic_result = self._validate_semantics(graph)
                if not semantic_result.is_valid:
                    is_valid = False
                    messages.extend(semantic_result.messages)
                warnings.extend(semantic_result.warnings)
                suggestions.extend(semantic_result.suggestions)
            except Exception as e:
                is_valid = False
                messages.append(f"Semantic validation error: {str(e)}")
        
        if level == ValidationLevel.SEMANTIC:
            return ValidationResult(is_valid, level, messages, warnings, suggestions)
        
        # Game readiness validation
        if is_valid:
            try:
                game_result = self._validate_game_readiness(graph)
                if not game_result.is_valid:
                    warnings.extend(game_result.messages)  # Game issues are warnings, not errors
                warnings.extend(game_result.warnings)
                suggestions.extend(game_result.suggestions)
            except Exception as e:
                warnings.append(f"Game readiness check error: {str(e)}")
        
        return ValidationResult(is_valid, level, messages, warnings, suggestions)
    
    def preview_in_game(self, thesis_graph: EGGraph, 
                       domain_model_name: Optional[str] = None) -> GamePreview:
        """Preview how the graph would behave as a thesis in the game."""
        try:
            # Create a temporary game state
            temp_engine = EndoporeuticGameEngine()
            if domain_model_name:
                # Load domain model from folio
                domain_model = temp_engine.folio.get_graph(domain_model_name)
            else:
                # Use empty domain model
                domain_model = EGGraph.create_empty()
            
            # Start a temporary inning
            initial_state = temp_engine.start_inning(thesis_graph, domain_model_name)
            
            # Get legal moves preview
            legal_moves = temp_engine.get_legal_moves()
            move_descriptions = [move.description for move in legal_moves[:5]]  # First 5 moves
            
            # Assess complexity
            complexity = self._assess_complexity(thesis_graph)
            
            # Generate strategic notes
            strategic_notes = self._generate_strategic_notes(thesis_graph, initial_state)
            
            return GamePreview(
                thesis_graph=thesis_graph,
                initial_game_state=initial_state,
                contested_context=temp_engine.current_state.contested_context,
                legal_moves_preview=move_descriptions,
                complexity_assessment=complexity,
                strategic_notes=strategic_notes
            )
            
        except Exception as e:
            return GamePreview(
                thesis_graph=thesis_graph,
                initial_game_state=None,
                contested_context=None,
                legal_moves_preview=[],
                complexity_assessment=f"Error: {str(e)}",
                strategic_notes=["Preview failed - check graph validity"]
            )
    
    def get_available_templates(self) -> List[CompositionTemplate]:
        """Get list of available composition templates."""
        return list(self.templates.values())
    
    def save_as_template(self, graph: EGGraph, name: str, description: str,
                        category: str = "user") -> bool:
        """Save a graph as a reusable template."""
        try:
            template = CompositionTemplate(
                name=name,
                description=description,
                category=category,
                base_graph=graph,
                parameters={},
                usage_hints=[]
            )
            self.templates[name] = template
            return True
        except Exception:
            return False
    
    def _validate_syntax(self, graph: EGGraph) -> ValidationResult:
        """Validate syntactic correctness of the graph."""
        messages = []
        warnings = []
        suggestions = []
        
        # Check context hierarchy
        try:
            hierarchy_errors = graph.context_manager.validate_context_hierarchy()
            if hierarchy_errors:
                messages.extend(hierarchy_errors)
        except Exception as e:
            messages.append(f"Context hierarchy validation failed: {str(e)}")
        
        # Check node-edge consistency
        for edge_id, edge in graph.edges.items():
            for node_id in edge.nodes:
                if node_id not in graph.nodes:
                    messages.append(f"Edge {edge_id} references non-existent node {node_id}")
        
        # Check ligature consistency
        for ligature_id, ligature in graph.ligatures.items():
            for node_id in ligature.nodes:
                if node_id not in graph.nodes:
                    messages.append(f"Ligature {ligature_id} references non-existent node {node_id}")
        
        # Check for orphaned elements
        orphaned_nodes = []
        for node_id, node in graph.nodes.items():
            # Check if node is in any context
            found_in_context = False
            for context_id, context in graph.context_manager.contexts.items():
                if node_id in graph.get_items_in_context(context_id):
                    found_in_context = True
                    break
            if not found_in_context:
                orphaned_nodes.append(node_id)
        
        if orphaned_nodes:
            warnings.append(f"Found {len(orphaned_nodes)} orphaned nodes")
            suggestions.append("Ensure all nodes are placed in appropriate contexts")
        
        is_valid = len(messages) == 0
        return ValidationResult(is_valid, ValidationLevel.SYNTAX_ONLY, messages, warnings, suggestions)
    
    def _validate_semantics(self, graph: EGGraph) -> ValidationResult:
        """Validate semantic correctness of the graph."""
        messages = []
        warnings = []
        suggestions = []
        
        # Check for meaningful content
        if len(graph.nodes) == 0 and len(graph.edges) == 0:
            warnings.append("Graph is empty")
            suggestions.append("Add some predicates or logical structure")
        
        # Check predicate arities
        for node_id, node in graph.nodes.items():
            if node.node_type == 'predicate':
                arity = node.properties.get('arity', 0)
                # Count connections to this predicate
                connections = 0
                for edge_id, edge in graph.edges.items():
                    if node_id in edge.nodes:
                        connections += 1
                
                if connections != arity:
                    warnings.append(f"Predicate {node.properties.get('name', node_id)} has arity {arity} but {connections} connections")
                    suggestions.append("Check predicate argument structure")
        
        # Check for disconnected components
        components = graph.find_connected_components()
        if len(components) > 1:
            warnings.append(f"Graph has {len(components)} disconnected components")
            suggestions.append("Consider if all components are necessary")
        
        is_valid = len(messages) == 0
        return ValidationResult(is_valid, ValidationLevel.SEMANTIC, messages, warnings, suggestions)
    
    def _validate_game_readiness(self, graph: EGGraph) -> ValidationResult:
        """Validate readiness for use in the endoporeutic game."""
        messages = []
        warnings = []
        suggestions = []
        
        # Check if graph can serve as a meaningful thesis
        if len(graph.nodes) == 0:
            messages.append("Empty graph cannot serve as a thesis")
            suggestions.append("Add predicates or logical assertions")
        
        # Check for overly complex structures
        max_depth = graph.context_manager.get_max_depth()
        if max_depth > 5:
            warnings.append(f"Graph has deep nesting (depth {max_depth}) which may be difficult to play")
            suggestions.append("Consider simplifying the logical structure")
        
        # Check for very large graphs
        total_elements = len(graph.nodes) + len(graph.edges) + len(graph.ligatures)
        if total_elements > 50:
            warnings.append(f"Large graph ({total_elements} elements) may be unwieldy in gameplay")
            suggestions.append("Consider breaking into smaller sub-problems")
        
        is_valid = len(messages) == 0
        return ValidationResult(is_valid, ValidationLevel.GAME_READY, messages, warnings, suggestions)
    
    def _assess_complexity(self, graph: EGGraph) -> str:
        """Assess the complexity of a graph for gameplay."""
        node_count = len(graph.nodes)
        edge_count = len(graph.edges)
        ligature_count = len(graph.ligatures)
        max_depth = graph.context_manager.get_max_depth()
        
        total_elements = node_count + edge_count + ligature_count
        
        if total_elements <= 5 and max_depth <= 2:
            return "Simple - Good for beginners"
        elif total_elements <= 15 and max_depth <= 3:
            return "Moderate - Suitable for intermediate players"
        elif total_elements <= 30 and max_depth <= 4:
            return "Complex - Challenging for experienced players"
        else:
            return "Very Complex - Expert level"
    
    def _generate_strategic_notes(self, graph: EGGraph, state: Optional[GameState]) -> List[str]:
        """Generate strategic notes about the graph."""
        notes = []
        
        # Analyze structure
        if len(graph.ligatures) > 0:
            notes.append(f"Contains {len(graph.ligatures)} identity connections - watch for deiteration opportunities")
        
        # Analyze contexts
        cut_contexts = [c for c in graph.context_manager.contexts.values() if c.context_type == 'cut']
        if len(cut_contexts) > 0:
            notes.append(f"Has {len(cut_contexts)} cuts - multiple negation levels to navigate")
        
        # Analyze patterns
        patterns = self.pattern_recognizer.recognize_all_patterns(graph)
        if patterns:
            pattern_types = [p.pattern_type for p in patterns]
            notes.append(f"Contains logical patterns: {', '.join(set(pattern_types))}")
        
        return notes
    
    def _load_default_templates(self):
        """Load default composition templates."""
        # Simple assertion template
        simple_graph = EGGraph.create_empty()
        # Add a simple predicate (this would be implemented properly)
        
        self.templates["simple_assertion"] = CompositionTemplate(
            name="simple_assertion",
            description="A simple predicate assertion",
            category="basic",
            base_graph=simple_graph,
            parameters={"predicate_name": "P", "arity": 1},
            usage_hints=["Good starting point for beginners", "Can be extended with arguments"]
        )
        
        # Universal quantification template
        self.templates["universal_quantification"] = CompositionTemplate(
            name="universal_quantification",
            description="Universal quantification pattern (forall x P(x))",
            category="quantification",
            base_graph=simple_graph,  # Would be properly constructed
            parameters={"variable": "x", "predicate": "P"},
            usage_hints=["Represents 'for all' statements", "Creates nested negation structure"]
        )
        
        # Implication template
        self.templates["implication"] = CompositionTemplate(
            name="implication",
            description="Implication pattern (if P then Q)",
            category="logical",
            base_graph=simple_graph,  # Would be properly constructed
            parameters={"antecedent": "P", "consequent": "Q"},
            usage_hints=["Represents conditional statements", "Uses nested cuts for logical structure"]
        )


class ComponentLibrary:
    """
    Library of reusable graph components and patterns.
    
    Provides a collection of common logical structures that can be
    easily inserted into graphs during composition.
    """
    
    def __init__(self):
        self.predicates: Dict[str, Dict[str, Any]] = {}
        self.patterns: Dict[str, EGGraph] = {}
        self.logical_forms: Dict[str, EGGraph] = {}
        self._initialize_library()
    
    def get_common_predicates(self) -> List[Dict[str, Any]]:
        """Get list of commonly used predicates."""
        return [
            {"name": "Person", "arity": 1, "description": "x is a person"},
            {"name": "Loves", "arity": 2, "description": "x loves y"},
            {"name": "Mortal", "arity": 1, "description": "x is mortal"},
            {"name": "Human", "arity": 1, "description": "x is human"},
            {"name": "Equals", "arity": 2, "description": "x equals y"},
            {"name": "GreaterThan", "arity": 2, "description": "x is greater than y"},
            {"name": "Member", "arity": 2, "description": "x is a member of y"},
            {"name": "Subset", "arity": 2, "description": "x is a subset of y"}
        ]
    
    def get_logical_patterns(self) -> List[Dict[str, Any]]:
        """Get list of common logical patterns."""
        return [
            {"name": "universal_quantification", "description": "For all x, P(x)"},
            {"name": "existential_quantification", "description": "There exists x such that P(x)"},
            {"name": "implication", "description": "If P then Q"},
            {"name": "biconditional", "description": "P if and only if Q"},
            {"name": "disjunction", "description": "P or Q"},
            {"name": "conjunction", "description": "P and Q"},
            {"name": "negation", "description": "Not P"}
        ]
    
    def create_predicate_node(self, name: str, arity: int) -> Node:
        """Create a predicate node with the given name and arity."""
        node_id = NodeId(uuid.uuid4())
        return Node.create(
            id=node_id,
            node_type='predicate',
            properties={'name': name, 'arity': arity}
        )
    
    def create_individual_node(self, name: str) -> Node:
        """Create an individual (constant) node."""
        node_id = NodeId(uuid.uuid4())
        return Node.create(
            id=node_id,
            node_type='individual',
            properties={'name': name}
        )
    
    def create_variable_node(self, name: str) -> Node:
        """Create a variable node."""
        node_id = NodeId(uuid.uuid4())
        return Node.create(
            id=node_id,
            node_type='variable',
            properties={'name': name}
        )
    
    def _initialize_library(self):
        """Initialize the component library with common elements."""
        # This would populate the library with common predicates and patterns
        pass

