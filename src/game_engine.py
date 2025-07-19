"""
Complete Endoporeutic Game Engine

This module implements Peirce's Endoporeutic Game as a two-player interactive
system for validating logical propositions through existential graph transformations.
The game engine serves as the "umpire" that enforces rules, manages player turns,
and facilitates model negotiation.

Updated for Entity-Predicate hypergraph architecture where:
- CLIF terms (variables, constants) → Entities (Lines of Identity)
- CLIF predicates → Predicates (hyperedges connecting entities)
- CLIF quantifiers → Entity scoping in contexts

Based on Charles Sanders Peirce's original conception and modern interpretations
by Dau, Sowa, and others.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass
from uuid import UUID, uuid4
import copy

from eg_types import EntityId, PredicateId, ContextId, LigatureId, ItemId
from graph import EGGraph
from context import ContextManager
from transformations import TransformationEngine, TransformationType, TransformationResult
from clif_parser import CLIFParser
from clif_generator import CLIFGenerator


class Player(Enum):
    """Represents the players in the Endoporeutic Game."""
    PROPOSER = "proposer"
    SKEPTIC = "skeptic"


class GameStatus(Enum):
    """Represents the current status of the game."""
    IN_PROGRESS = "in_progress"
    PROPOSER_WIN = "proposer_win"
    SKEPTIC_WIN = "skeptic_win"
    DRAW_EXTEND = "draw_extend"
    SUSPENDED = "suspended"


class MoveType(Enum):
    """Types of moves available in the Endoporeutic Game."""
    TRANSFORMATION = "transformation"
    SCOPING_CHALLENGE = "scoping_challenge"
    JUSTIFICATION = "justification"
    UNWRAP_NEGATION = "unwrap_negation"
    MODEL_NEGOTIATION = "model_negotiation"


class NegotiationType(Enum):
    """Types of model negotiation."""
    ADD_INDIVIDUAL = "add_individual"
    ASSERT_IDENTITY = "assert_identity"
    RETRACT_FACT = "retract_fact"
    AMEND_FACT = "amend_fact"


@dataclass
class GameMove:
    """Represents a single move in the game."""
    player: Player
    move_type: MoveType
    transformation_type: Optional[TransformationType] = None
    target_items: Optional[Set[ItemId]] = None
    target_context: Optional[ContextId] = None
    parameters: Optional[Dict[str, Any]] = None
    description: str = ""


@dataclass
class GameState:
    """Represents the complete state of the game at a point in time."""
    graph: EGGraph
    domain_model: EGGraph
    current_player: Player
    contested_context: Optional[ContextId]
    status: GameStatus
    move_history: List[GameMove]
    sub_inning_stack: List['SubInning']
    metadata: Dict[str, Any]


@dataclass
class SubInning:
    """Represents a sub-inning in the recursive game structure."""
    parent_context: ContextId
    contested_context: ContextId
    original_proposer: Player
    original_skeptic: Player
    depth: int


class LegalMoveAnalyzer:
    """Analyzes the current game state to determine legal moves."""
    
    def __init__(self, transformation_engine: TransformationEngine):
        self.transformation_engine = transformation_engine
    
    def get_legal_moves(self, state: GameState) -> List[GameMove]:
        """Get all legal moves for the current player in the given state."""
        legal_moves = []
        
        if state.status != GameStatus.IN_PROGRESS:
            return legal_moves
        
        # Get transformation-based moves
        transformation_moves = self._get_transformation_moves(state)
        legal_moves.extend(transformation_moves)
        
        # Get scoping challenge moves
        scoping_moves = self._get_scoping_moves(state)
        legal_moves.extend(scoping_moves)
        
        # Get model negotiation moves
        negotiation_moves = self._get_negotiation_moves(state)
        legal_moves.extend(negotiation_moves)
        
        return legal_moves
    
    def _get_transformation_moves(self, state: GameState) -> List[GameMove]:
        """Get legal transformation moves for the current player."""
        moves = []
        
        # Get legal transformations from the transformation engine
        legal_transformations = self.transformation_engine.get_legal_transformations(
            state.graph, state.contested_context
        )
        
        for transformation_type, target_sets in legal_transformations.items():
            for target_items in target_sets:
                # Check if this transformation is legal for the current player
                if self._is_transformation_legal_for_player(
                    state, transformation_type, target_items
                ):
                    move = GameMove(
                        player=state.current_player,
                        move_type=MoveType.TRANSFORMATION,
                        transformation_type=transformation_type,
                        target_items=target_items,
                        target_context=state.contested_context,
                        description=f"{transformation_type.value} on {len(target_items)} items"
                    )
                    moves.append(move)
        
        return moves
    
    def _get_scoping_moves(self, state: GameState) -> List[GameMove]:
        """Get legal scoping challenge moves."""
        moves = []
        
        # Skeptic can challenge scoping of entities
        if state.current_player == Player.SKEPTIC:
            # Find entities that could be challenged for scoping
            entities_in_contested = self._get_entities_in_context(state.graph, state.contested_context)
            
            for entity_id in entities_in_contested:
                entity = state.graph.entities[entity_id]
                if entity.entity_type == 'variable':  # Only variables can be scoped
                    move = GameMove(
                        player=Player.SKEPTIC,
                        move_type=MoveType.SCOPING_CHALLENGE,
                        target_items={entity_id},
                        target_context=state.contested_context,
                        description=f"Challenge scoping of variable {entity.name}"
                    )
                    moves.append(move)
        
        return moves
    
    def _get_negotiation_moves(self, state: GameState) -> List[GameMove]:
        """Get legal model negotiation moves."""
        moves = []
        
        # Both players can propose model negotiations
        negotiation_types = [
            NegotiationType.ADD_INDIVIDUAL,
            NegotiationType.ASSERT_IDENTITY,
            NegotiationType.RETRACT_FACT,
            NegotiationType.AMEND_FACT
        ]
        
        for neg_type in negotiation_types:
            move = GameMove(
                player=state.current_player,
                move_type=MoveType.MODEL_NEGOTIATION,
                parameters={"negotiation_type": neg_type},
                description=f"Propose {neg_type.value}"
            )
            moves.append(move)
        
        return moves
    
    def _is_transformation_legal_for_player(
        self, 
        state: GameState, 
        transformation_type: TransformationType,
        target_items: Set[ItemId]
    ) -> bool:
        """Check if a transformation is legal for the current player."""
        
        # Proposer can only strengthen the thesis (make it harder to refute)
        if state.current_player == Player.PROPOSER:
            strengthening_moves = {
                TransformationType.INSERTION,
                TransformationType.DOUBLE_CUT_INSERTION,
                TransformationType.ITERATION,
                TransformationType.ENTITY_JOIN
            }
            return transformation_type in strengthening_moves
        
        # Skeptic can only weaken the thesis (make it easier to refute)
        elif state.current_player == Player.SKEPTIC:
            weakening_moves = {
                TransformationType.ERASURE,
                TransformationType.DOUBLE_CUT_ERASURE,
                TransformationType.DEITERATION,
                TransformationType.ENTITY_SEVER
            }
            return transformation_type in weakening_moves
        
        return False
    
    def _get_entities_in_context(self, graph: EGGraph, context_id: Optional[ContextId]) -> Set[EntityId]:
        """Get all entities in a specific context."""
        if not context_id:
            return set()
        
        items_in_context = graph.context_manager.get_items_in_context(context_id)
        return {item_id for item_id in items_in_context if item_id in graph.entities}


class EndoporeuticGameEngine:
    """
    Main game engine for the Endoporeutic Game with Entity-Predicate architecture.
    
    Manages game state, enforces rules, and facilitates player interactions
    in the context of existential graph transformations.
    """
    
    def __init__(self):
        """Initialize the game engine."""
        self.transformation_engine = TransformationEngine()
        self.move_analyzer = LegalMoveAnalyzer(self.transformation_engine)
        self.clif_parser = CLIFParser()
        self.clif_generator = CLIFGenerator()
    
    def create_game_state(self, thesis_graph: EGGraph, domain_model: Optional[EGGraph] = None) -> GameState:
        """Create a new game state from a thesis graph."""
        if domain_model is None:
            domain_model = EGGraph.create_empty()
        
        # Find the contested context (deepest positive context with content)
        contested_context = self._find_contested_context(thesis_graph)
        
        return GameState(
            graph=thesis_graph,
            domain_model=domain_model,
            current_player=Player.SKEPTIC,  # Skeptic moves first
            contested_context=contested_context,
            status=GameStatus.IN_PROGRESS,
            move_history=[],
            sub_inning_stack=[],
            metadata={}
        )
    
    def apply_move(self, state: GameState, move: GameMove) -> GameState:
        """Apply a move to the game state and return the new state."""
        if state.status != GameStatus.IN_PROGRESS:
            raise ValueError(f"Cannot apply move to game with status {state.status}")
        
        if move.player != state.current_player:
            raise ValueError(f"Move player {move.player} does not match current player {state.current_player}")
        
        # Validate that the move is legal
        legal_moves = self.get_legal_moves(state)
        if not self._is_move_in_legal_set(move, legal_moves):
            raise ValueError(f"Move is not legal in current state")
        
        # Apply the move based on its type
        if move.move_type == MoveType.TRANSFORMATION:
            return self._apply_transformation_move(state, move)
        elif move.move_type == MoveType.SCOPING_CHALLENGE:
            return self._apply_scoping_challenge(state, move)
        elif move.move_type == MoveType.MODEL_NEGOTIATION:
            return self._apply_model_negotiation(state, move)
        elif move.move_type == MoveType.UNWRAP_NEGATION:
            return self._apply_unwrap_negation(state, move)
        else:
            raise ValueError(f"Unsupported move type: {move.move_type}")
    
    def get_legal_moves(self, state: GameState) -> List[GameMove]:
        """Get all legal moves for the current player."""
        return self.move_analyzer.get_legal_moves(state)
    
    def check_game_end_conditions(self, state: GameState) -> GameStatus:
        """Check if the game has ended and return the appropriate status."""
        
        # Check if the contested context is empty (Skeptic wins)
        if state.contested_context:
            items_in_contested = state.graph.context_manager.get_items_in_context(state.contested_context)
            if not items_in_contested:
                return GameStatus.SKEPTIC_WIN
        
        # Check if no legal moves are available
        legal_moves = self.get_legal_moves(state)
        if not legal_moves:
            # If it's Skeptic's turn and no moves, Proposer wins
            if state.current_player == Player.SKEPTIC:
                return GameStatus.PROPOSER_WIN
            # If it's Proposer's turn and no moves, Skeptic wins
            else:
                return GameStatus.SKEPTIC_WIN
        
        # Check for draw conditions (too many moves without progress)
        if len(state.move_history) > 100:  # Arbitrary limit
            return GameStatus.DRAW_EXTEND
        
        return GameStatus.IN_PROGRESS
    
    def get_game_summary(self, state: GameState) -> Dict[str, Any]:
        """Get a summary of the current game state."""
        contested_items = set()
        if state.contested_context:
            contested_items = state.graph.context_manager.get_items_in_context(state.contested_context)
        
        entities_in_contested = {item for item in contested_items if item in state.graph.entities}
        predicates_in_contested = {item for item in contested_items if item in state.graph.predicates}
        
        return {
            "status": state.status.value,
            "current_player": state.current_player.value,
            "move_count": len(state.move_history),
            "contested_context": str(state.contested_context) if state.contested_context else None,
            "contested_entities": len(entities_in_contested),
            "contested_predicates": len(predicates_in_contested),
            "total_entities": len(state.graph.entities),
            "total_predicates": len(state.graph.predicates),
            "context_depth": self._get_max_context_depth(state.graph),
            "legal_moves_available": len(self.get_legal_moves(state)),
            "sub_innings": len(state.sub_inning_stack)
        }
    
    def export_game_state_to_clif(self, state: GameState) -> str:
        """Export the current game state to CLIF format."""
        try:
            return self.clif_generator.generate(state.graph)
        except Exception as e:
            return f"(comment \"CLIF export failed: {str(e)}\")"
    
    def create_sub_inning(self, state: GameState, target_context: ContextId) -> GameState:
        """Create a sub-inning for a nested context."""
        sub_inning = SubInning(
            parent_context=state.contested_context or state.graph.root_context_id,
            contested_context=target_context,
            original_proposer=state.current_player if state.current_player == Player.PROPOSER else Player.SKEPTIC,
            original_skeptic=state.current_player if state.current_player == Player.SKEPTIC else Player.PROPOSER,
            depth=len(state.sub_inning_stack) + 1
        )
        
        new_stack = state.sub_inning_stack + [sub_inning]
        
        return GameState(
            graph=state.graph,
            domain_model=state.domain_model,
            current_player=Player.SKEPTIC,  # Skeptic always starts sub-innings
            contested_context=target_context,
            status=state.status,
            move_history=state.move_history,
            sub_inning_stack=new_stack,
            metadata=state.metadata
        )
    
    def resolve_sub_inning(self, state: GameState, winner: Player) -> GameState:
        """Resolve the current sub-inning and return to the parent level."""
        if not state.sub_inning_stack:
            raise ValueError("No sub-inning to resolve")
        
        current_sub_inning = state.sub_inning_stack[-1]
        parent_stack = state.sub_inning_stack[:-1]
        
        # Determine the parent contested context
        if parent_stack:
            parent_contested = parent_stack[-1].contested_context
        else:
            parent_contested = self._find_contested_context(state.graph)
        
        # Determine next player based on sub-inning result
        if winner == Player.SKEPTIC:
            next_player = current_sub_inning.original_skeptic
        else:
            next_player = current_sub_inning.original_proposer
        
        return GameState(
            graph=state.graph,
            domain_model=state.domain_model,
            current_player=next_player,
            contested_context=parent_contested,
            status=state.status,
            move_history=state.move_history,
            sub_inning_stack=parent_stack,
            metadata=state.metadata
        )
    
    # Private helper methods
    
    def _find_contested_context(self, graph: EGGraph) -> Optional[ContextId]:
        """Find the context that should be contested in the game."""
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
    
    def _apply_transformation_move(self, state: GameState, move: GameMove) -> GameState:
        """Apply a transformation move to the game state."""
        if not move.transformation_type or not move.target_items:
            raise ValueError("Transformation move requires transformation_type and target_items")
        
        # Apply the transformation
        attempt = self.transformation_engine.apply_transformation(
            state.graph,
            move.transformation_type,
            target_items=move.target_items,
            target_context=move.target_context
        )
        
        if attempt.result != TransformationResult.SUCCESS:
            raise ValueError(f"Transformation failed: {attempt.error_message}")
        
        # Update game state
        new_move_history = state.move_history + [move]
        next_player = Player.PROPOSER if state.current_player == Player.SKEPTIC else Player.SKEPTIC
        
        new_state = GameState(
            graph=attempt.result_graph,
            domain_model=state.domain_model,
            current_player=next_player,
            contested_context=state.contested_context,
            status=state.status,
            move_history=new_move_history,
            sub_inning_stack=state.sub_inning_stack,
            metadata=state.metadata
        )
        
        # Check for game end conditions
        new_status = self.check_game_end_conditions(new_state)
        return GameState(
            graph=new_state.graph,
            domain_model=new_state.domain_model,
            current_player=new_state.current_player,
            contested_context=new_state.contested_context,
            status=new_status,
            move_history=new_state.move_history,
            sub_inning_stack=new_state.sub_inning_stack,
            metadata=new_state.metadata
        )
    
    def _apply_scoping_challenge(self, state: GameState, move: GameMove) -> GameState:
        """Apply a scoping challenge move."""
        if not move.target_items:
            raise ValueError("Scoping challenge requires target_items")
        
        # For now, scoping challenges create sub-innings
        # In a full implementation, this would involve more complex logic
        
        # Find a nested context to contest
        target_entity_id = next(iter(move.target_items))
        entity_context = state.graph.context_manager.find_item_context(target_entity_id)
        
        if entity_context and entity_context != state.contested_context:
            # Create sub-inning for the entity's context
            return self.create_sub_inning(state, entity_context)
        else:
            # Just switch players if no sub-inning needed
            next_player = Player.PROPOSER if state.current_player == Player.SKEPTIC else Player.SKEPTIC
            new_move_history = state.move_history + [move]
            
            return GameState(
                graph=state.graph,
                domain_model=state.domain_model,
                current_player=next_player,
                contested_context=state.contested_context,
                status=state.status,
                move_history=new_move_history,
                sub_inning_stack=state.sub_inning_stack,
                metadata=state.metadata
            )
    
    def _apply_model_negotiation(self, state: GameState, move: GameMove) -> GameState:
        """Apply a model negotiation move."""
        # Model negotiation affects the domain model, not the thesis graph
        # For now, just record the move and switch players
        
        next_player = Player.PROPOSER if state.current_player == Player.SKEPTIC else Player.SKEPTIC
        new_move_history = state.move_history + [move]
        
        # In a full implementation, this would modify the domain_model
        # based on the negotiation type
        
        return GameState(
            graph=state.graph,
            domain_model=state.domain_model,  # Would be modified in full implementation
            current_player=next_player,
            contested_context=state.contested_context,
            status=state.status,
            move_history=new_move_history,
            sub_inning_stack=state.sub_inning_stack,
            metadata=state.metadata
        )
    
    def _apply_unwrap_negation(self, state: GameState, move: GameMove) -> GameState:
        """Apply an unwrap negation move."""
        # This would involve removing a cut and moving its contents up one level
        # For now, just switch players
        
        next_player = Player.PROPOSER if state.current_player == Player.SKEPTIC else Player.SKEPTIC
        new_move_history = state.move_history + [move]
        
        return GameState(
            graph=state.graph,  # Would be modified in full implementation
            domain_model=state.domain_model,
            current_player=next_player,
            contested_context=state.contested_context,
            status=state.status,
            move_history=new_move_history,
            sub_inning_stack=state.sub_inning_stack,
            metadata=state.metadata
        )
    
    def _is_move_in_legal_set(self, move: GameMove, legal_moves: List[GameMove]) -> bool:
        """Check if a move is in the set of legal moves."""
        for legal_move in legal_moves:
            if (move.player == legal_move.player and
                move.move_type == legal_move.move_type and
                move.transformation_type == legal_move.transformation_type and
                move.target_items == legal_move.target_items and
                move.target_context == legal_move.target_context):
                return True
        return False
    
    def _get_max_context_depth(self, graph: EGGraph) -> int:
        """Get the maximum context depth in the graph."""
        if not graph.context_manager.contexts:
            return 0
        return max(context.depth for context in graph.context_manager.contexts.values())


# Convenience functions for game setup and analysis

def create_simple_game(clif_text: str) -> Tuple[EndoporeuticGameEngine, GameState]:
    """Create a simple game from CLIF text."""
    engine = EndoporeuticGameEngine()
    
    # Parse the CLIF text
    parse_result = engine.clif_parser.parse(clif_text)
    if len(parse_result.errors) > 0 or parse_result.graph is None:
        raise ValueError(f"Failed to parse CLIF: {parse_result.errors}")
    
    # Create game state
    game_state = engine.create_game_state(parse_result.graph)
    
    return engine, game_state


def analyze_game_complexity(graph: EGGraph) -> Dict[str, Any]:
    """Analyze the complexity of a graph for game play."""
    total_entities = len(graph.entities)
    total_predicates = len(graph.predicates)
    total_contexts = len(graph.context_manager.contexts)
    max_depth = max((ctx.depth for ctx in graph.context_manager.contexts.values()), default=0)
    
    # Calculate complexity metrics
    structural_complexity = total_entities + total_predicates + total_contexts
    logical_complexity = max_depth * 2  # Depth contributes to logical complexity
    
    # Determine complexity category
    if structural_complexity < 5 and logical_complexity < 4:
        category = "Simple"
    elif structural_complexity < 15 and logical_complexity < 8:
        category = "Moderate"
    else:
        category = "Complex"
    
    return {
        "category": category,
        "structural_complexity": structural_complexity,
        "logical_complexity": logical_complexity,
        "total_entities": total_entities,
        "total_predicates": total_predicates,
        "total_contexts": total_contexts,
        "max_depth": max_depth,
        "estimated_moves": structural_complexity * 2,  # Rough estimate
        "strategic_notes": _generate_strategic_notes(graph)
    }


def _generate_strategic_notes(graph: EGGraph) -> List[str]:
    """Generate strategic notes about a graph."""
    notes = []
    
    entity_count = len(graph.entities)
    predicate_count = len(graph.predicates)
    max_depth = max((ctx.depth for ctx in graph.context_manager.contexts.values()), default=0)
    
    if entity_count > predicate_count:
        notes.append("Many entities suggest rich quantification opportunities")
    
    if predicate_count > entity_count:
        notes.append("Many predicates suggest complex relational structure")
    
    if max_depth > 2:
        notes.append("Deep nesting enables sophisticated logical maneuvers")
    
    if max_depth == 0:
        notes.append("No cuts limit transformation options")
    
    # Count variables vs constants
    variables = sum(1 for e in graph.entities.values() if e.entity_type == 'variable')
    constants = sum(1 for e in graph.entities.values() if e.entity_type == 'constant')
    
    if variables > constants:
        notes.append("Many variables enable flexible scoping strategies")
    elif constants > variables:
        notes.append("Many constants suggest concrete factual claims")
    
    return notes


# API Compatibility Alias
# Provides backward compatibility for test suites and external code
# that expects the shorter class name
EGGameEngine = EndoporeuticGameEngine

# Add compatibility methods to the EndoporeuticGameEngine class
def _add_compatibility_methods():
    """Add compatibility methods to EndoporeuticGameEngine."""
    
    def start_new_game(self, thesis_graph: EGGraph, domain_model: Optional[EGGraph] = None) -> GameState:
        """Start a new game with the given thesis graph.
        
        This is an alias for create_game_state that provides compatibility
        with test expectations and other game initialization patterns.
        """
        return self.create_game_state(thesis_graph, domain_model)
    
    def start_game(self, thesis_graph: EGGraph, domain_model: Optional[EGGraph] = None) -> GameState:
        """Start a game with the given thesis graph.
        
        This is another alias for create_game_state that provides compatibility
        with different naming conventions used in tests.
        """
        return self.create_game_state(thesis_graph, domain_model)
    
    def get_available_moves(self, state: GameState) -> List[GameMove]:
        """Get available moves for the current game state.
        
        This is an alias for get_legal_moves that provides compatibility
        with test expectations and other move analysis patterns.
        """
        return self.get_legal_moves(state)
    
    # Add methods to the class
    EndoporeuticGameEngine.start_new_game = start_new_game
    EndoporeuticGameEngine.start_game = start_game
    EndoporeuticGameEngine.get_available_moves = get_available_moves

# Apply the compatibility methods
_add_compatibility_methods()
