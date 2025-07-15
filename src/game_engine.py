"""
Complete Endoporeutic Game Engine

This module implements Peirce's Endoporeutic Game as a two-player interactive
system for validating logical propositions through existential graph transformations.
The game engine serves as the "umpire" that enforces rules, manages player turns,
and facilitates model negotiation.

Based on Charles Sanders Peirce's original conception and modern interpretations
by Dau, Sowa, and others.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass
from uuid import UUID, uuid4
import copy

from .eg_types import NodeId, EdgeId, ContextId, LigatureId, ItemId
from .graph import EGGraph
from .context import ContextManager
from .transformations import TransformationEngine, TransformationType, TransformationResult
from .clif_parser import CLIFParser
from .clif_generator import CLIFGenerator


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
        """Get all legal moves for the current player in the current state."""
        legal_moves = []
        
        if state.status != GameStatus.IN_PROGRESS:
            return legal_moves
        
        # Add transformation moves
        legal_moves.extend(self._get_transformation_moves(state))
        
        # Add game-specific moves
        legal_moves.extend(self._get_game_specific_moves(state))
        
        return legal_moves
    
    def _get_transformation_moves(self, state: GameState) -> List[GameMove]:
        """Get legal transformation moves."""
        moves = []
        legal_transformations = self.transformation_engine.get_legal_transformations(
            state.graph, state.contested_context
        )
        
        for trans_type in legal_transformations:
            # Create move based on transformation type and current player
            if self._is_transformation_legal_for_player(trans_type, state.current_player, state):
                move = GameMove(
                    player=state.current_player,
                    move_type=MoveType.TRANSFORMATION,
                    transformation_type=trans_type,
                    description=f"{state.current_player.value} applies {trans_type.value}"
                )
                moves.append(move)
        
        return moves
    
    def _get_game_specific_moves(self, state: GameState) -> List[GameMove]:
        """Get game-specific moves like unwrapping negations."""
        moves = []
        
        # Unwrap negation move (for Skeptic)
        if (state.current_player == Player.SKEPTIC and 
            state.contested_context and
            self._can_unwrap_negation(state)):
            move = GameMove(
                player=Player.SKEPTIC,
                move_type=MoveType.UNWRAP_NEGATION,
                target_context=state.contested_context,
                description="Skeptic unwraps negation to create sub-inning"
            )
            moves.append(move)
        
        # Scoping challenge (for Skeptic)
        if state.current_player == Player.SKEPTIC:
            exposed_elements = self._find_exposed_elements(state)
            if exposed_elements:
                move = GameMove(
                    player=Player.SKEPTIC,
                    move_type=MoveType.SCOPING_CHALLENGE,
                    target_items=exposed_elements,
                    description="Skeptic challenges exposed elements"
                )
                moves.append(move)
        
        return moves
    
    def _is_transformation_legal_for_player(self, trans_type: TransformationType, 
                                          player: Player, state: GameState) -> bool:
        """Check if a transformation is legal for the current player."""
        # Proposer can generally use iteration, insertion into positive contexts
        # Skeptic can use erasure from negative contexts
        # Both can use double cut operations
        
        if trans_type in [TransformationType.DOUBLE_CUT_INSERTION, 
                         TransformationType.DOUBLE_CUT_ERASURE]:
            return True
        
        if player == Player.PROPOSER:
            return trans_type in [TransformationType.ITERATION, 
                                TransformationType.INSERTION,
                                TransformationType.LIGATURE_JOIN]
        
        if player == Player.SKEPTIC:
            return trans_type in [TransformationType.ERASURE,
                                TransformationType.DEITERATION,
                                TransformationType.LIGATURE_SEVER]
        
        return False
    
    def _can_unwrap_negation(self, state: GameState) -> bool:
        """Check if the current contested context can be unwrapped."""
        if not state.contested_context:
            return False
        
        context = state.graph.context_manager.get_context(state.contested_context)
        return context and context.context_type == 'cut'
    
    def _find_exposed_elements(self, state: GameState) -> Set[ItemId]:
        """Find elements in the thesis that are exposed to the domain model."""
        exposed = set()
        
        # Look for nodes/edges in the contested context that have connections
        # to elements outside the contested area
        if state.contested_context:
            items_in_context = state.graph.get_items_in_context(state.contested_context)
            
            for item_id in items_in_context:
                # Check if this item has ligatures connecting to domain model
                for ligature in state.graph.ligatures.values():
                    if item_id in ligature.nodes:
                        # Check if ligature connects to domain model elements
                        for node_id in ligature.nodes:
                            if node_id not in items_in_context:
                                exposed.add(item_id)
                                break
        
        return exposed


class ModelNegotiator:
    """Handles model negotiation between players."""
    
    def __init__(self):
        self.pending_negotiations: List[Dict[str, Any]] = []
    
    def propose_negotiation(self, negotiation_type: NegotiationType, 
                          proposer: Player, details: Dict[str, Any]) -> str:
        """Propose a model negotiation."""
        negotiation_id = str(uuid4())
        negotiation = {
            'id': negotiation_id,
            'type': negotiation_type,
            'proposer': proposer,
            'details': details,
            'status': 'pending'
        }
        self.pending_negotiations.append(negotiation)
        return negotiation_id
    
    def respond_to_negotiation(self, negotiation_id: str, 
                             responder: Player, accept: bool) -> bool:
        """Respond to a pending negotiation."""
        for negotiation in self.pending_negotiations:
            if negotiation['id'] == negotiation_id:
                negotiation['responder'] = responder
                negotiation['accepted'] = accept
                negotiation['status'] = 'resolved'
                return accept
        return False
    
    def apply_negotiation(self, negotiation_id: str, 
                         domain_model: EGGraph) -> EGGraph:
        """Apply an accepted negotiation to the domain model."""
        for negotiation in self.pending_negotiations:
            if (negotiation['id'] == negotiation_id and 
                negotiation.get('accepted', False)):
                
                return self._apply_negotiation_type(
                    negotiation['type'], 
                    negotiation['details'], 
                    domain_model
                )
        return domain_model
    
    def _apply_negotiation_type(self, neg_type: NegotiationType, 
                              details: Dict[str, Any], 
                              domain_model: EGGraph) -> EGGraph:
        """Apply a specific type of negotiation."""
        if neg_type == NegotiationType.ADD_INDIVIDUAL:
            # Add new individual to domain model
            new_node = details['node']
            return domain_model.add_node(new_node)
        
        elif neg_type == NegotiationType.ASSERT_IDENTITY:
            # Join two nodes with a ligature
            node1_id = details['node1_id']
            node2_id = details['node2_id']
            ligature = details['ligature']
            return domain_model.add_ligature(ligature)
        
        elif neg_type == NegotiationType.RETRACT_FACT:
            # Remove elements from domain model
            items_to_remove = details['items']
            new_model = domain_model
            for item_id in items_to_remove:
                if item_id in new_model.nodes:
                    new_model = new_model.remove_node(item_id)
                elif item_id in new_model.edges:
                    new_model = new_model.remove_edge(item_id)
            return new_model
        
        return domain_model


class EndoporeuticGameEngine:
    """
    The main game engine that serves as the "umpire" for the Endoporeutic Game.
    
    This class manages the complete game lifecycle, enforces rules, validates moves,
    and facilitates model negotiation between players.
    """
    
    def __init__(self):
        self.transformation_engine = TransformationEngine()
        self.move_analyzer = LegalMoveAnalyzer(self.transformation_engine)
        self.model_negotiator = ModelNegotiator()
        self.clif_parser = CLIFParser()
        self.clif_generator = CLIFGenerator()
        
        # Game state
        self.current_state: Optional[GameState] = None
        self.folio: Dict[str, EGGraph] = {}  # Named graph library
    
    def add_to_folio(self, name: str, graph: EGGraph):
        """Add a named graph to the folio."""
        if name in self.folio:
            raise ValueError(f"Graph '{name}' already exists in folio")
        self.folio[name] = graph
    
    def start_inning(self, thesis: Union[str, EGGraph], 
                    domain_model_name: Optional[str] = None) -> GameState:
        """
        Start a new inning of the Endoporeutic Game.
        
        Args:
            thesis: The thesis to be proven (CLIF string or EGGraph)
            domain_model_name: Name of domain model from folio
        
        Returns:
            Initial game state
        """
        # Parse thesis if it's a CLIF string
        if isinstance(thesis, str):
            parse_result = self.clif_parser.parse(thesis)
            if parse_result.errors:
                raise ValueError(f"Thesis parsing failed: {parse_result.errors}")
            thesis_graph = parse_result.graph
        else:
            thesis_graph = thesis
        
        # Get domain model
        domain_model = EGGraph.create_empty()
        if domain_model_name and domain_model_name in self.folio:
            domain_model = self.folio[domain_model_name]
        
        # Create initial game graph: (not (and M (not G)))
        # This represents: if M then G
        initial_graph = self._create_initial_game_graph(thesis_graph, domain_model)
        
        # Find the contested context (the outer negation of G)
        contested_context = self._find_initial_contested_context(initial_graph)
        
        # Initialize game state
        self.current_state = GameState(
            graph=initial_graph,
            domain_model=domain_model,
            current_player=Player.PROPOSER,
            contested_context=contested_context,
            status=GameStatus.IN_PROGRESS,
            move_history=[],
            sub_inning_stack=[],
            metadata={
                'thesis_description': str(thesis),
                'domain_model_name': domain_model_name,
                'inning_start_time': str(uuid4())  # Placeholder for timestamp
            }
        )
        
        return self.current_state
    
    def get_legal_moves(self) -> List[GameMove]:
        """Get legal moves for the current player."""
        if not self.current_state:
            return []
        return self.move_analyzer.get_legal_moves(self.current_state)
    
    def make_move(self, move: GameMove) -> Tuple[bool, str]:
        """
        Execute a move and update the game state.
        
        Returns:
            (success, message) tuple
        """
        if not self.current_state:
            return False, "No active game"
        
        if self.current_state.status != GameStatus.IN_PROGRESS:
            return False, "Game is not in progress"
        
        if move.player != self.current_state.current_player:
            return False, f"Not {move.player.value}'s turn"
        
        # Validate move is legal
        legal_moves = self.get_legal_moves()
        if not self._is_move_legal(move, legal_moves):
            return False, "Illegal move"
        
        # Execute the move
        success, message = self._execute_move(move)
        
        if success:
            # Add to history
            self.current_state.move_history.append(move)
            
            # Check for win/loss conditions
            self._check_game_status()
            
            # Switch players if appropriate
            if move.move_type != MoveType.UNWRAP_NEGATION:
                self._switch_player()
        
        return success, message
    
    def _create_initial_game_graph(self, thesis: EGGraph, 
                                 domain_model: EGGraph) -> EGGraph:
        """Create the initial game graph representing (not (and M (not G)))."""
        # Start with empty graph
        game_graph = EGGraph.create_empty()
        
        # Add domain model M to the root context
        game_graph = self._copy_subgraph(domain_model, game_graph, 
                                       game_graph.root_context_id)
        
        # Create outer negation cut for (not G)
        game_graph, outer_cut_context = game_graph.create_context(
            'cut', game_graph.root_context_id
        )
        
        # Add thesis G inside the negation (making it not G)
        game_graph = self._copy_subgraph(thesis, game_graph, outer_cut_context.id)
        
        return game_graph
    
    def _copy_subgraph(self, source: EGGraph, target: EGGraph, 
                      target_context: ContextId) -> EGGraph:
        """Copy a subgraph from source to target in the specified context."""
        # This is a simplified implementation
        # A full implementation would handle complex copying with ligatures
        
        new_target = target
        
        # Copy nodes
        for node in source.nodes.values():
            new_target = new_target.add_node(node, target_context)
        
        # Copy edges
        for edge in source.edges.values():
            new_target = new_target.add_edge(edge, target_context)
        
        return new_target
    
    def _find_initial_contested_context(self, graph: EGGraph) -> Optional[ContextId]:
        """Find the initial contested context (outer negation cut)."""
        # Look for cut contexts in the root
        root_items = graph.get_items_in_context(graph.root_context_id)
        
        for item_id in root_items:
            # Check if this item is a context
            try:
                context = graph.context_manager.get_context(item_id)
                if context and context.context_type == 'cut':
                    return context.id
            except:
                # Not a context, continue
                continue
        
        return None
    
    def _is_move_legal(self, move: GameMove, legal_moves: List[GameMove]) -> bool:
        """Check if a move is in the list of legal moves."""
        for legal_move in legal_moves:
            if (move.move_type == legal_move.move_type and
                move.transformation_type == legal_move.transformation_type):
                return True
        return False
    
    def _execute_move(self, move: GameMove) -> Tuple[bool, str]:
        """Execute a specific move."""
        if move.move_type == MoveType.TRANSFORMATION:
            return self._execute_transformation_move(move)
        elif move.move_type == MoveType.UNWRAP_NEGATION:
            return self._execute_unwrap_negation(move)
        elif move.move_type == MoveType.SCOPING_CHALLENGE:
            return self._execute_scoping_challenge(move)
        elif move.move_type == MoveType.MODEL_NEGOTIATION:
            return self._execute_model_negotiation(move)
        else:
            return False, f"Unknown move type: {move.move_type}"
    
    def _execute_transformation_move(self, move: GameMove) -> Tuple[bool, str]:
        """Execute a transformation move."""
        if not move.transformation_type:
            return False, "No transformation type specified"
        
        try:
            # Apply transformation
            attempt = self.transformation_engine.apply_transformation(
                self.current_state.graph,
                move.transformation_type,
                target_items=move.target_items or set(),
                target_context=move.target_context,
                **(move.parameters or {})
            )
            
            if attempt.result == TransformationResult.SUCCESS:
                self.current_state.graph = attempt.result_graph
                return True, f"Applied {move.transformation_type.value}"
            else:
                return False, attempt.error_message or "Transformation failed"
        
        except Exception as e:
            return False, f"Transformation error: {str(e)}"
    
    def _execute_unwrap_negation(self, move: GameMove) -> Tuple[bool, str]:
        """Execute unwrapping a negation (creating sub-inning)."""
        if not move.target_context:
            return False, "No target context specified"
        
        # Create sub-inning
        sub_inning = SubInning(
            parent_context=self.current_state.contested_context,
            contested_context=move.target_context,
            original_proposer=self.current_state.current_player,
            original_skeptic=Player.SKEPTIC if self.current_state.current_player == Player.PROPOSER else Player.PROPOSER,
            depth=len(self.current_state.sub_inning_stack) + 1
        )
        
        self.current_state.sub_inning_stack.append(sub_inning)
        self.current_state.contested_context = move.target_context
        
        # Switch roles for sub-inning
        self.current_state.current_player = (
            Player.SKEPTIC if self.current_state.current_player == Player.PROPOSER 
            else Player.PROPOSER
        )
        
        return True, "Created sub-inning with role reversal"
    
    def _execute_scoping_challenge(self, move: GameMove) -> Tuple[bool, str]:
        """Execute a scoping challenge."""
        if not move.target_items:
            return False, "No target items specified"
        
        # The Proposer must now justify these exposed elements
        # This typically involves finding mappings in the domain model
        
        # For now, we'll mark this as requiring justification
        self.current_state.metadata['pending_justification'] = list(move.target_items)
        
        return True, f"Skeptic challenges {len(move.target_items)} exposed elements"
    
    def _execute_model_negotiation(self, move: GameMove) -> Tuple[bool, str]:
        """Execute a model negotiation move."""
        # This would involve the ModelNegotiator
        # Implementation depends on specific negotiation type
        return True, "Model negotiation initiated"
    
    def _check_game_status(self):
        """Check for win/loss conditions and update game status."""
        if not self.current_state.contested_context:
            # No contested context means game is resolved
            self.current_state.status = GameStatus.PROPOSER_WIN
            return
        
        # Check if contested context is empty
        items_in_context = self.current_state.graph.get_items_in_context(
            self.current_state.contested_context
        )
        
        if not items_in_context:
            # Empty contested context
            if self.current_state.current_player == Player.PROPOSER:
                self.current_state.status = GameStatus.PROPOSER_WIN
            else:
                self.current_state.status = GameStatus.SKEPTIC_WIN
    
    def _switch_player(self):
        """Switch the current player."""
        if self.current_state.current_player == Player.PROPOSER:
            self.current_state.current_player = Player.SKEPTIC
        else:
            self.current_state.current_player = Player.PROPOSER
    
    def get_game_summary(self) -> Dict[str, Any]:
        """Get a summary of the current game state."""
        if not self.current_state:
            return {"status": "no_active_game"}
        
        return {
            "status": self.current_state.status.value,
            "current_player": self.current_state.current_player.value,
            "move_count": len(self.current_state.move_history),
            "sub_inning_depth": len(self.current_state.sub_inning_stack),
            "contested_context": str(self.current_state.contested_context) if self.current_state.contested_context else None,
            "legal_moves_count": len(self.get_legal_moves()),
            "metadata": self.current_state.metadata
        }
    
    def export_game_state(self) -> str:
        """Export the current game state as CLIF."""
        if not self.current_state:
            return ""
        
        result = self.clif_generator.generate(self.current_state.graph)
        return result.clif_text
    
    def save_to_folio(self, name: str, save_type: str = "current_graph"):
        """Save current state to folio."""
        if not self.current_state:
            raise ValueError("No active game to save")
        
        if save_type == "current_graph":
            self.add_to_folio(name, self.current_state.graph)
        elif save_type == "domain_model":
            self.add_to_folio(name, self.current_state.domain_model)
        else:
            raise ValueError(f"Unknown save type: {save_type}")

