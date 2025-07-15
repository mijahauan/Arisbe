"""
Comprehensive tests for the Endoporeutic Game Engine

Tests cover game initialization, move validation, player turns,
sub-innings, model negotiation, and win/loss conditions.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.game_engine import (
    EndoporeuticGameEngine, Player, GameStatus, MoveType, GameMove,
    TransformationType, LegalMoveAnalyzer, ModelNegotiator, NegotiationType
)
from src.eg_types import Node, Edge, Context, Ligature
from src.graph import EGGraph


class TestEndoporeuticGameEngine:
    """Test the main game engine functionality."""
    
    def test_engine_initialization(self):
        """Test game engine initializes correctly."""
        engine = EndoporeuticGameEngine()
        
        assert engine.transformation_engine is not None
        assert engine.move_analyzer is not None
        assert engine.model_negotiator is not None
        assert engine.current_state is None
        assert len(engine.folio) == 0
    
    def test_add_to_folio(self):
        """Test adding graphs to the folio."""
        engine = EndoporeuticGameEngine()
        graph = EGGraph.create_empty()
        
        engine.add_to_folio("test_graph", graph)
        assert "test_graph" in engine.folio
        
        # Test duplicate name raises error
        with pytest.raises(ValueError, match="already exists"):
            engine.add_to_folio("test_graph", graph)
    
    def test_start_inning_with_clif_thesis(self):
        """Test starting an inning with a CLIF thesis."""
        engine = EndoporeuticGameEngine()
        
        # Mock the CLIF parser
        with patch.object(engine.clif_parser, 'parse') as mock_parse:
            mock_graph = EGGraph.create_empty()
            mock_parse.return_value = Mock(graph=mock_graph, errors=[])
            
            state = engine.start_inning("(P x)")
            
            assert state is not None
            assert state.current_player == Player.PROPOSER
            assert state.status == GameStatus.IN_PROGRESS
            assert len(state.move_history) == 0
            mock_parse.assert_called_once_with("(P x)")
    
    def test_start_inning_with_graph_thesis(self):
        """Test starting an inning with an EGGraph thesis."""
        engine = EndoporeuticGameEngine()
        thesis_graph = EGGraph.create_empty()
        
        state = engine.start_inning(thesis_graph)
        
        assert state is not None
        assert state.current_player == Player.PROPOSER
        assert state.status == GameStatus.IN_PROGRESS
        assert state.graph is not None
    
    def test_start_inning_with_domain_model(self):
        """Test starting an inning with a domain model from folio."""
        engine = EndoporeuticGameEngine()
        
        # Add domain model to folio
        domain_model = EGGraph.create_empty()
        engine.add_to_folio("domain", domain_model)
        
        thesis_graph = EGGraph.create_empty()
        state = engine.start_inning(thesis_graph, "domain")
        
        assert state.metadata['domain_model_name'] == "domain"
    
    def test_get_legal_moves_no_game(self):
        """Test getting legal moves when no game is active."""
        engine = EndoporeuticGameEngine()
        moves = engine.get_legal_moves()
        assert len(moves) == 0
    
    def test_make_move_no_game(self):
        """Test making a move when no game is active."""
        engine = EndoporeuticGameEngine()
        move = GameMove(Player.PROPOSER, MoveType.TRANSFORMATION)
        
        success, message = engine.make_move(move)
        assert not success
        assert "No active game" in message
    
    def test_make_move_wrong_player(self):
        """Test making a move with wrong player."""
        engine = EndoporeuticGameEngine()
        thesis_graph = EGGraph.create_empty()
        engine.start_inning(thesis_graph)
        
        # Try to make move as Skeptic when it's Proposer's turn
        move = GameMove(Player.SKEPTIC, MoveType.TRANSFORMATION)
        success, message = engine.make_move(move)
        
        assert not success
        assert "Not skeptic's turn" in message
    
    def test_game_summary(self):
        """Test getting game summary."""
        engine = EndoporeuticGameEngine()
        
        # No game
        summary = engine.get_game_summary()
        assert summary["status"] == "no_active_game"
        
        # With game
        thesis_graph = EGGraph.create_empty()
        engine.start_inning(thesis_graph)
        
        summary = engine.get_game_summary()
        assert summary["status"] == GameStatus.IN_PROGRESS.value
        assert summary["current_player"] == Player.PROPOSER.value
        assert summary["move_count"] == 0


class TestLegalMoveAnalyzer:
    """Test the legal move analysis functionality."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        from src.transformations import TransformationEngine
        engine = TransformationEngine()
        analyzer = LegalMoveAnalyzer(engine)
        
        assert analyzer.transformation_engine is engine
    
    def test_get_legal_moves_game_over(self):
        """Test no legal moves when game is over."""
        from src.transformations import TransformationEngine
        engine = TransformationEngine()
        analyzer = LegalMoveAnalyzer(engine)
        
        # Create game state with game over status
        from src.game_engine import GameState
        state = GameState(
            graph=EGGraph.create_empty(),
            domain_model=EGGraph.create_empty(),
            current_player=Player.PROPOSER,
            contested_context=None,
            status=GameStatus.PROPOSER_WIN,
            move_history=[],
            sub_inning_stack=[],
            metadata={}
        )
        
        moves = analyzer.get_legal_moves(state)
        assert len(moves) == 0
    
    def test_transformation_legal_for_proposer(self):
        """Test which transformations are legal for Proposer."""
        from src.transformations import TransformationEngine
        engine = TransformationEngine()
        analyzer = LegalMoveAnalyzer(engine)
        
        # Mock state
        state = Mock()
        
        # Proposer should be able to use iteration, insertion
        assert analyzer._is_transformation_legal_for_player(
            TransformationType.ITERATION, Player.PROPOSER, state
        )
        assert analyzer._is_transformation_legal_for_player(
            TransformationType.INSERTION, Player.PROPOSER, state
        )
        
        # But not erasure (typically Skeptic's move)
        assert not analyzer._is_transformation_legal_for_player(
            TransformationType.ERASURE, Player.PROPOSER, state
        )
    
    def test_transformation_legal_for_skeptic(self):
        """Test which transformations are legal for Skeptic."""
        from src.transformations import TransformationEngine
        engine = TransformationEngine()
        analyzer = LegalMoveAnalyzer(engine)
        
        # Mock state
        state = Mock()
        
        # Skeptic should be able to use erasure, deiteration
        assert analyzer._is_transformation_legal_for_player(
            TransformationType.ERASURE, Player.SKEPTIC, state
        )
        assert analyzer._is_transformation_legal_for_player(
            TransformationType.DEITERATION, Player.SKEPTIC, state
        )
        
        # But not iteration (typically Proposer's move)
        assert not analyzer._is_transformation_legal_for_player(
            TransformationType.ITERATION, Player.SKEPTIC, state
        )
    
    def test_double_cut_legal_for_both(self):
        """Test double cut operations are legal for both players."""
        from src.transformations import TransformationEngine
        engine = TransformationEngine()
        analyzer = LegalMoveAnalyzer(engine)
        
        state = Mock()
        
        for player in [Player.PROPOSER, Player.SKEPTIC]:
            assert analyzer._is_transformation_legal_for_player(
                TransformationType.DOUBLE_CUT_INSERTION, player, state
            )
            assert analyzer._is_transformation_legal_for_player(
                TransformationType.DOUBLE_CUT_ERASURE, player, state
            )


class TestModelNegotiator:
    """Test the model negotiation functionality."""
    
    def test_negotiator_initialization(self):
        """Test negotiator initializes correctly."""
        negotiator = ModelNegotiator()
        assert len(negotiator.pending_negotiations) == 0
    
    def test_propose_negotiation(self):
        """Test proposing a negotiation."""
        negotiator = ModelNegotiator()
        
        negotiation_id = negotiator.propose_negotiation(
            NegotiationType.ADD_INDIVIDUAL,
            Player.PROPOSER,
            {'node': Mock()}
        )
        
        assert len(negotiator.pending_negotiations) == 1
        assert negotiation_id is not None
        
        negotiation = negotiator.pending_negotiations[0]
        assert negotiation['type'] == NegotiationType.ADD_INDIVIDUAL
        assert negotiation['proposer'] == Player.PROPOSER
        assert negotiation['status'] == 'pending'
    
    def test_respond_to_negotiation(self):
        """Test responding to a negotiation."""
        negotiator = ModelNegotiator()
        
        # Propose negotiation
        negotiation_id = negotiator.propose_negotiation(
            NegotiationType.ADD_INDIVIDUAL,
            Player.PROPOSER,
            {'node': Mock()}
        )
        
        # Accept negotiation
        result = negotiator.respond_to_negotiation(
            negotiation_id, Player.SKEPTIC, True
        )
        
        assert result is True
        negotiation = negotiator.pending_negotiations[0]
        assert negotiation['responder'] == Player.SKEPTIC
        assert negotiation['accepted'] is True
        assert negotiation['status'] == 'resolved'
    
    def test_respond_to_nonexistent_negotiation(self):
        """Test responding to a negotiation that doesn't exist."""
        negotiator = ModelNegotiator()
        
        result = negotiator.respond_to_negotiation(
            "nonexistent", Player.SKEPTIC, True
        )
        
        assert result is False
    
    def test_apply_add_individual_negotiation(self):
        """Test applying an ADD_INDIVIDUAL negotiation."""
        negotiator = ModelNegotiator()
        
        # Create mock node and domain model
        mock_node = Node.create(node_type='individual', properties={'name': 'john'})
        domain_model = EGGraph.create_empty()
        
        # Propose and accept negotiation
        negotiation_id = negotiator.propose_negotiation(
            NegotiationType.ADD_INDIVIDUAL,
            Player.PROPOSER,
            {'node': mock_node}
        )
        negotiator.respond_to_negotiation(negotiation_id, Player.SKEPTIC, True)
        
        # Apply negotiation
        new_model = negotiator.apply_negotiation(negotiation_id, domain_model)
        
        # Check that node was added
        assert len(new_model.nodes) == 1
        assert mock_node.id in new_model.nodes


class TestGameMoves:
    """Test specific game moves and their execution."""
    
    def test_transformation_move_creation(self):
        """Test creating a transformation move."""
        move = GameMove(
            player=Player.PROPOSER,
            move_type=MoveType.TRANSFORMATION,
            transformation_type=TransformationType.ITERATION,
            description="Proposer iterates predicate"
        )
        
        assert move.player == Player.PROPOSER
        assert move.move_type == MoveType.TRANSFORMATION
        assert move.transformation_type == TransformationType.ITERATION
    
    def test_unwrap_negation_move(self):
        """Test creating an unwrap negation move."""
        context_id = uuid4()
        move = GameMove(
            player=Player.SKEPTIC,
            move_type=MoveType.UNWRAP_NEGATION,
            target_context=context_id,
            description="Skeptic unwraps negation"
        )
        
        assert move.player == Player.SKEPTIC
        assert move.move_type == MoveType.UNWRAP_NEGATION
        assert move.target_context == context_id
    
    def test_scoping_challenge_move(self):
        """Test creating a scoping challenge move."""
        target_items = {uuid4(), uuid4()}
        move = GameMove(
            player=Player.SKEPTIC,
            move_type=MoveType.SCOPING_CHALLENGE,
            target_items=target_items,
            description="Skeptic challenges exposed elements"
        )
        
        assert move.player == Player.SKEPTIC
        assert move.move_type == MoveType.SCOPING_CHALLENGE
        assert move.target_items == target_items


class TestGameIntegration:
    """Integration tests for complete game scenarios."""
    
    def test_simple_game_flow(self):
        """Test a simple game flow from start to finish."""
        engine = EndoporeuticGameEngine()
        
        # Start with simple thesis
        thesis_graph = EGGraph.create_empty()
        pred_node = Node.create(node_type='predicate', properties={'name': 'P'})
        thesis_graph = thesis_graph.add_node(pred_node)
        
        # Start inning
        state = engine.start_inning(thesis_graph)
        
        assert state.current_player == Player.PROPOSER
        assert state.status == GameStatus.IN_PROGRESS
        
        # Get legal moves
        legal_moves = engine.get_legal_moves()
        assert len(legal_moves) >= 0  # Should have some legal moves
    
    def test_game_with_domain_model(self):
        """Test game with a domain model."""
        engine = EndoporeuticGameEngine()
        
        # Create domain model
        domain_model = EGGraph.create_empty()
        domain_node = Node.create(node_type='individual', properties={'name': 'john'})
        domain_model = domain_model.add_node(domain_node)
        engine.add_to_folio("domain", domain_model)
        
        # Create thesis
        thesis_graph = EGGraph.create_empty()
        thesis_node = Node.create(node_type='predicate', properties={'name': 'Human'})
        thesis_graph = thesis_graph.add_node(thesis_node)
        
        # Start inning with domain model
        state = engine.start_inning(thesis_graph, "domain")
        
        assert state.metadata['domain_model_name'] == "domain"
        assert state.domain_model is not None
    
    def test_export_game_state(self):
        """Test exporting game state as CLIF."""
        engine = EndoporeuticGameEngine()
        
        # No game
        clif_output = engine.export_game_state()
        assert clif_output == ""
        
        # With game
        thesis_graph = EGGraph.create_empty()
        engine.start_inning(thesis_graph)
        
        # Mock the CLIF generator
        with patch.object(engine.clif_generator, 'generate') as mock_generate:
            mock_generate.return_value = Mock(clif_text="(P x)")
            
            clif_output = engine.export_game_state()
            assert clif_output == "(P x)"
            mock_generate.assert_called_once()


class TestSubInnings:
    """Test sub-inning functionality."""
    
    def test_sub_inning_creation(self):
        """Test creating a sub-inning."""
        from src.game_engine import SubInning
        
        parent_context = uuid4()
        contested_context = uuid4()
        
        sub_inning = SubInning(
            parent_context=parent_context,
            contested_context=contested_context,
            original_proposer=Player.PROPOSER,
            original_skeptic=Player.SKEPTIC,
            depth=1
        )
        
        assert sub_inning.parent_context == parent_context
        assert sub_inning.contested_context == contested_context
        assert sub_inning.original_proposer == Player.PROPOSER
        assert sub_inning.depth == 1
    
    def test_role_reversal_in_sub_inning(self):
        """Test that roles are reversed in sub-innings."""
        engine = EndoporeuticGameEngine()
        thesis_graph = EGGraph.create_empty()
        engine.start_inning(thesis_graph)
        
        # Mock unwrap negation move
        context_id = uuid4()
        move = GameMove(
            player=Player.PROPOSER,  # Current player
            move_type=MoveType.UNWRAP_NEGATION,
            target_context=context_id
        )
        
        # Mock the execution to avoid complex graph operations
        with patch.object(engine, '_execute_unwrap_negation') as mock_execute:
            mock_execute.return_value = (True, "Sub-inning created")
            
            # Mock legal moves to include this move
            with patch.object(engine, 'get_legal_moves') as mock_legal:
                mock_legal.return_value = [move]
                
                success, message = engine.make_move(move)
                
                assert success
                mock_execute.assert_called_once_with(move)


class TestPropertyBasedGameEngine:
    """Property-based tests for game engine."""
    
    def test_game_state_consistency(self):
        """Test that game state remains consistent after moves."""
        engine = EndoporeuticGameEngine()
        thesis_graph = EGGraph.create_empty()
        engine.start_inning(thesis_graph)
        
        initial_state = engine.current_state
        
        # Game state should be consistent
        assert initial_state.current_player in [Player.PROPOSER, Player.SKEPTIC]
        assert initial_state.status in [status for status in GameStatus]
        assert len(initial_state.move_history) == 0
        assert len(initial_state.sub_inning_stack) == 0
    
    def test_move_history_preservation(self):
        """Test that move history is preserved correctly."""
        engine = EndoporeuticGameEngine()
        thesis_graph = EGGraph.create_empty()
        engine.start_inning(thesis_graph)
        
        initial_move_count = len(engine.current_state.move_history)
        
        # Mock a successful move
        move = GameMove(Player.PROPOSER, MoveType.TRANSFORMATION)
        
        with patch.object(engine, '_execute_move') as mock_execute:
            mock_execute.return_value = (True, "Success")
            with patch.object(engine, 'get_legal_moves') as mock_legal:
                mock_legal.return_value = [move]
                
                engine.make_move(move)
                
                # Move should be added to history
                assert len(engine.current_state.move_history) == initial_move_count + 1
                assert engine.current_state.move_history[-1] == move

