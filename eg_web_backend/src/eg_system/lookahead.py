"""
Look Ahead System

This module provides tools for exploring the consequences of transformations
and patterns before committing to them. It supports two main types of look aheads:

1. Step-based look aheads: Preview the effect of specific transformations
2. Pattern-based look aheads: Explore instances of general patterns

The system enables safe exploration of the logical space without modifying
the actual game state or graph structure.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, replace
from enum import Enum
import copy

from .eg_types import (
    Node, Edge, Context, Ligature, NodeId, EdgeId, ContextId, 
    LigatureId, ItemId
)
from .graph import EGGraph
from .transformations import (
    TransformationEngine, TransformationType, TransformationResult,
    ValidationResult as TransformationValidation
)
from .game_engine import EndoporeuticGameEngine, GameState, GameMove, Player, MoveType
from .pattern_recognizer import PatternRecognitionEngine, PatternMatch


class LookAheadType(Enum):
    """Types of look ahead operations."""
    TRANSFORMATION = "transformation"
    GAME_MOVE = "game_move"
    PATTERN_EXPLORATION = "pattern_exploration"
    MOVE_SEQUENCE = "move_sequence"


@dataclass(frozen=True)
class TransformationPreview:
    """Preview of a transformation's effects."""
    original_graph: EGGraph
    transformed_graph: Optional[EGGraph]
    transformation_type: TransformationType
    target_items: Set[ItemId]
    success: bool
    validation_result: TransformationValidation
    side_effects: List[str]
    reversibility: str
    complexity_change: str
    
    @property
    def is_valid(self) -> bool:
        """Check if the transformation preview is valid."""
        return self.success and self.transformed_graph is not None


@dataclass(frozen=True)
class PatternMatch:
    """A match for a pattern in a graph."""
    pattern_type: str
    confidence: float
    matched_items: Set[ItemId]
    context: ContextId
    description: str
    logical_form: str
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence match."""
        return self.confidence >= 0.8


@dataclass(frozen=True)
class PatternExploration:
    """Results of exploring pattern instances."""
    pattern_template: str
    base_graph: EGGraph
    matches: List[PatternMatch]
    potential_instantiations: List[EGGraph]
    exploration_notes: List[str]
    
    @property
    def match_count(self) -> int:
        """Number of pattern matches found."""
        return len(self.matches)


@dataclass(frozen=True)
class GameMovePreview:
    """Preview of a game move's effects."""
    original_state: GameState
    move: GameMove
    resulting_state: Optional[GameState]
    success: bool
    error_message: Optional[str]
    legal_moves_after: List[GameMove]
    game_status_change: str
    strategic_assessment: str


@dataclass(frozen=True)
class MoveSequenceSimulation:
    """Simulation of a sequence of moves."""
    initial_state: GameState
    moves: List[GameMove]
    intermediate_states: List[GameState]
    final_state: Optional[GameState]
    success: bool
    failure_point: Optional[int]
    outcome_assessment: str
    alternative_suggestions: List[str]


class LookAheadEngine:
    """
    Main engine for look ahead operations.
    
    Provides safe exploration of transformations, game moves, and patterns
    without modifying the actual game state or graph structure.
    """
    
    def __init__(self):
        self.transformation_engine = TransformationEngine()
        self.pattern_recognizer = PatternRecognitionEngine()
        self.game_engine = EndoporeuticGameEngine()
    
    def preview_transformation(self, graph: EGGraph, transformation_type: TransformationType,
                             target_items: Set[ItemId], 
                             additional_params: Optional[Dict[str, Any]] = None) -> TransformationPreview:
        """
        Preview the effects of applying a transformation to a graph.
        
        Args:
            graph: The graph to transform
            transformation_type: Type of transformation to apply
            target_items: Items to target for transformation
            additional_params: Additional parameters for the transformation
            
        Returns:
            Preview of the transformation's effects
        """
        # Create a copy of the graph for safe exploration
        graph_copy = copy.deepcopy(graph)
        
        try:
            # Attempt the transformation
            result = self.transformation_engine.apply_transformation(
                graph_copy, transformation_type, target_items, additional_params or {}
            )
            
            if result.result == TransformationResult.SUCCESS:
                transformed_graph = result.new_graph
                success = True
                validation_result = TransformationValidation(True, "Transformation successful")
            else:
                transformed_graph = None
                success = False
                validation_result = TransformationValidation(False, result.message)
            
            # Analyze side effects
            side_effects = self._analyze_side_effects(graph, transformed_graph, transformation_type)
            
            # Assess reversibility
            reversibility = self._assess_reversibility(transformation_type, target_items)
            
            # Assess complexity change
            complexity_change = self._assess_complexity_change(graph, transformed_graph)
            
            return TransformationPreview(
                original_graph=graph,
                transformed_graph=transformed_graph,
                transformation_type=transformation_type,
                target_items=target_items,
                success=success,
                validation_result=validation_result,
                side_effects=side_effects,
                reversibility=reversibility,
                complexity_change=complexity_change
            )
            
        except Exception as e:
            return TransformationPreview(
                original_graph=graph,
                transformed_graph=None,
                transformation_type=transformation_type,
                target_items=target_items,
                success=False,
                validation_result=TransformationValidation(False, f"Error: {str(e)}"),
                side_effects=[],
                reversibility="Unknown",
                complexity_change="Unknown"
            )
    
    def explore_pattern_instances(self, pattern_template: str, base_graph: EGGraph,
                                domain_graph: Optional[EGGraph] = None) -> PatternExploration:
        """
        Explore instances of a pattern in a graph or domain.
        
        Args:
            pattern_template: Template describing the pattern to find
            base_graph: Graph to search for patterns
            domain_graph: Optional domain model for additional context
            
        Returns:
            Results of pattern exploration
        """
        try:
            # Find existing matches in the base graph
            matches = self._find_pattern_matches(pattern_template, base_graph)
            
            # Generate potential instantiations
            instantiations = self._generate_pattern_instantiations(
                pattern_template, base_graph, domain_graph
            )
            
            # Generate exploration notes
            notes = self._generate_exploration_notes(pattern_template, matches, instantiations)
            
            return PatternExploration(
                pattern_template=pattern_template,
                base_graph=base_graph,
                matches=matches,
                potential_instantiations=instantiations,
                exploration_notes=notes
            )
            
        except Exception as e:
            return PatternExploration(
                pattern_template=pattern_template,
                base_graph=base_graph,
                matches=[],
                potential_instantiations=[],
                exploration_notes=[f"Exploration failed: {str(e)}"]
            )
    
    def preview_game_move(self, current_state: GameState, move: GameMove) -> GameMovePreview:
        """
        Preview the effects of a game move.
        
        Args:
            current_state: Current game state
            move: Move to preview
            
        Returns:
            Preview of the move's effects
        """
        # Create a copy of the game engine with the current state
        engine_copy = copy.deepcopy(self.game_engine)
        engine_copy.current_state = copy.deepcopy(current_state)
        
        try:
            # Attempt the move
            success, message = engine_copy.make_move(move)
            
            if success:
                resulting_state = engine_copy.current_state
                legal_moves_after = engine_copy.get_legal_moves()
                game_status_change = self._assess_game_status_change(current_state, resulting_state)
                strategic_assessment = self._assess_move_strategy(move, current_state, resulting_state)
                error_message = None
            else:
                resulting_state = None
                legal_moves_after = []
                game_status_change = "Move failed"
                strategic_assessment = "Invalid move"
                error_message = message
            
            return GameMovePreview(
                original_state=current_state,
                move=move,
                resulting_state=resulting_state,
                success=success,
                error_message=error_message,
                legal_moves_after=legal_moves_after,
                game_status_change=game_status_change,
                strategic_assessment=strategic_assessment
            )
            
        except Exception as e:
            return GameMovePreview(
                original_state=current_state,
                move=move,
                resulting_state=None,
                success=False,
                error_message=f"Error: {str(e)}",
                legal_moves_after=[],
                game_status_change="Error occurred",
                strategic_assessment="Cannot assess"
            )
    
    def simulate_move_sequence(self, initial_state: GameState, 
                             moves: List[GameMove]) -> MoveSequenceSimulation:
        """
        Simulate a sequence of moves to see their combined effect.
        
        Args:
            initial_state: Starting game state
            moves: Sequence of moves to simulate
            
        Returns:
            Results of the move sequence simulation
        """
        # Create a copy of the game engine
        engine_copy = copy.deepcopy(self.game_engine)
        engine_copy.current_state = copy.deepcopy(initial_state)
        
        intermediate_states = []
        failure_point = None
        
        try:
            for i, move in enumerate(moves):
                success, message = engine_copy.make_move(move)
                
                if success:
                    intermediate_states.append(copy.deepcopy(engine_copy.current_state))
                else:
                    failure_point = i
                    break
            
            if failure_point is None:
                # All moves succeeded
                final_state = engine_copy.current_state
                success = True
                outcome_assessment = self._assess_sequence_outcome(initial_state, final_state)
                alternative_suggestions = []
            else:
                # Sequence failed at some point
                final_state = None
                success = False
                outcome_assessment = f"Sequence failed at move {failure_point + 1}"
                alternative_suggestions = self._suggest_alternatives(moves, failure_point)
            
            return MoveSequenceSimulation(
                initial_state=initial_state,
                moves=moves,
                intermediate_states=intermediate_states,
                final_state=final_state,
                success=success,
                failure_point=failure_point,
                outcome_assessment=outcome_assessment,
                alternative_suggestions=alternative_suggestions
            )
            
        except Exception as e:
            return MoveSequenceSimulation(
                initial_state=initial_state,
                moves=moves,
                intermediate_states=intermediate_states,
                final_state=None,
                success=False,
                failure_point=0,
                outcome_assessment=f"Simulation error: {str(e)}",
                alternative_suggestions=[]
            )
    
    def get_transformation_suggestions(self, graph: EGGraph, 
                                     goal: Optional[str] = None) -> List[TransformationPreview]:
        """
        Get suggestions for useful transformations on a graph.
        
        Args:
            graph: Graph to analyze
            goal: Optional goal description to guide suggestions
            
        Returns:
            List of suggested transformations with previews
        """
        suggestions = []
        
        # Get all possible transformations
        legal_transformations = self.transformation_engine.get_legal_transformations(graph)
        
        # Preview each transformation
        for transformation_type, target_sets in legal_transformations.items():
            for target_items in target_sets[:3]:  # Limit to first 3 for each type
                preview = self.preview_transformation(graph, transformation_type, target_items)
                if preview.is_valid:
                    suggestions.append(preview)
        
        # Sort by usefulness (this would be more sophisticated in practice)
        suggestions.sort(key=lambda p: len(p.side_effects))
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def _analyze_side_effects(self, original: EGGraph, transformed: Optional[EGGraph],
                            transformation_type: TransformationType) -> List[str]:
        """Analyze side effects of a transformation."""
        if transformed is None:
            return ["Transformation failed"]
        
        side_effects = []
        
        # Compare node counts
        original_nodes = len(original.nodes)
        new_nodes = len(transformed.nodes)
        if new_nodes != original_nodes:
            side_effects.append(f"Node count changed: {original_nodes} → {new_nodes}")
        
        # Compare edge counts
        original_edges = len(original.edges)
        new_edges = len(transformed.edges)
        if new_edges != original_edges:
            side_effects.append(f"Edge count changed: {original_edges} → {new_edges}")
        
        # Compare context structure
        original_contexts = len(original.context_manager.contexts)
        new_contexts = len(transformed.context_manager.contexts)
        if new_contexts != original_contexts:
            side_effects.append(f"Context count changed: {original_contexts} → {new_contexts}")
        
        # Check for ligature changes
        original_ligatures = len(original.ligatures)
        new_ligatures = len(transformed.ligatures)
        if new_ligatures != original_ligatures:
            side_effects.append(f"Ligature count changed: {original_ligatures} → {new_ligatures}")
        
        return side_effects
    
    def _assess_reversibility(self, transformation_type: TransformationType, 
                            target_items: Set[ItemId]) -> str:
        """Assess whether a transformation is easily reversible."""
        reversible_transformations = {
            TransformationType.DOUBLE_CUT_INSERTION,
            TransformationType.DOUBLE_CUT_ERASURE,
            TransformationType.ITERATION,
            TransformationType.DEITERATION
        }
        
        if transformation_type in reversible_transformations:
            return "Easily reversible"
        else:
            return "May be difficult to reverse"
    
    def _assess_complexity_change(self, original: EGGraph, 
                                transformed: Optional[EGGraph]) -> str:
        """Assess how transformation affects graph complexity."""
        if transformed is None:
            return "Unknown"
        
        original_complexity = self._calculate_complexity(original)
        new_complexity = self._calculate_complexity(transformed)
        
        if new_complexity > original_complexity:
            return "Increased complexity"
        elif new_complexity < original_complexity:
            return "Reduced complexity"
        else:
            return "Complexity unchanged"
    
    def _calculate_complexity(self, graph: EGGraph) -> int:
        """Calculate a simple complexity metric for a graph."""
        return (len(graph.nodes) + 
                len(graph.edges) + 
                len(graph.ligatures) + 
                graph.context_manager.get_max_depth() * 2)
    
    def _find_pattern_matches(self, pattern_template: str, graph: EGGraph) -> List[PatternMatch]:
        """Find matches for a pattern template in a graph."""
        matches = []
        
        # Use pattern recognizer to find logical patterns
        patterns = self.pattern_recognizer.recognize_all_patterns(graph)
        
        for pattern in patterns:
            if pattern_template.lower() in pattern.pattern_type.lower():
                match = PatternMatch(
                    pattern_type=pattern.pattern_type,
                    confidence=pattern.confidence,
                    matched_items=pattern.matched_items,
                    context=pattern.context,
                    description=pattern.description,
                    logical_form=pattern.logical_form
                )
                matches.append(match)
        
        return matches
    
    def _generate_pattern_instantiations(self, pattern_template: str, base_graph: EGGraph,
                                       domain_graph: Optional[EGGraph]) -> List[EGGraph]:
        """Generate potential instantiations of a pattern."""
        instantiations = []
        
        # This would implement pattern instantiation logic
        # For now, return empty list
        
        return instantiations
    
    def _generate_exploration_notes(self, pattern_template: str, matches: List[PatternMatch],
                                  instantiations: List[EGGraph]) -> List[str]:
        """Generate notes about pattern exploration results."""
        notes = []
        
        if matches:
            notes.append(f"Found {len(matches)} existing instances of pattern")
            high_confidence = [m for m in matches if m.is_high_confidence]
            if high_confidence:
                notes.append(f"{len(high_confidence)} high-confidence matches")
        else:
            notes.append("No existing instances found")
        
        if instantiations:
            notes.append(f"Generated {len(instantiations)} potential instantiations")
        
        return notes
    
    def _assess_game_status_change(self, before: GameState, after: GameState) -> str:
        """Assess how a move changed the game status."""
        if before.status != after.status:
            return f"Status changed: {before.status} → {after.status}"
        
        if before.current_player != after.current_player:
            return f"Player changed: {before.current_player} → {after.current_player}"
        
        if before.contested_context != after.contested_context:
            return "Contested context changed"
        
        return "No significant status change"
    
    def _assess_move_strategy(self, move: GameMove, before: GameState, 
                            after: GameState) -> str:
        """Assess the strategic value of a move."""
        if move.move_type == MoveType.TRANSFORMATION:
            return f"Applied {move.transformation_type} transformation"
        elif move.move_type == MoveType.UNWRAP_NEGATION:
            return "Created sub-inning with role reversal"
        elif move.move_type == MoveType.SCOPING_CHALLENGE:
            return "Challenged exposed elements"
        else:
            return "Standard game move"
    
    def _assess_sequence_outcome(self, initial: GameState, final: GameState) -> str:
        """Assess the outcome of a move sequence."""
        if initial.status != final.status:
            return f"Game concluded: {final.status}"
        
        move_count = len(final.move_history) - len(initial.move_history)
        return f"Sequence of {move_count} moves completed successfully"
    
    def _suggest_alternatives(self, failed_moves: List[GameMove], 
                            failure_point: int) -> List[str]:
        """Suggest alternative moves when a sequence fails."""
        suggestions = []
        
        failed_move = failed_moves[failure_point]
        
        if failed_move.move_type == MoveType.TRANSFORMATION:
            suggestions.append("Try a different transformation type")
            suggestions.append("Check if target items are valid")
        elif failed_move.move_type == MoveType.UNWRAP_NEGATION:
            suggestions.append("Ensure the target context is a cut")
            suggestions.append("Check if unwrapping is legal at this point")
        else:
            suggestions.append("Verify move is legal in current game state")
        
        return suggestions


class UndoRedoManager:
    """
    Manager for undo/redo operations during look ahead exploration.
    
    Maintains a history of graph states to enable safe exploration
    with easy backtracking.
    """
    
    def __init__(self, initial_graph: EGGraph):
        self.history: List[EGGraph] = [initial_graph]
        self.current_index: int = 0
        self.max_history: int = 50  # Limit history size
    
    def save_state(self, graph: EGGraph) -> None:
        """Save a new graph state."""
        # Remove any future states if we're not at the end
        self.history = self.history[:self.current_index + 1]
        
        # Add new state
        self.history.append(copy.deepcopy(graph))
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
    
    def undo(self) -> Optional[EGGraph]:
        """Undo to previous state."""
        if self.current_index > 0:
            self.current_index -= 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def redo(self) -> Optional[EGGraph]:
        """Redo to next state."""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.current_index < len(self.history) - 1
    
    def get_current_state(self) -> EGGraph:
        """Get the current graph state."""
        return copy.deepcopy(self.history[self.current_index])
    
    def clear_history(self, new_initial: EGGraph) -> None:
        """Clear history and start fresh with a new initial state."""
        self.history = [copy.deepcopy(new_initial)]
        self.current_index = 0

