"""
Strategic Lookahead System for Endoporeutic Game

This module provides strategic lookahead capabilities for the Endoporeutic Game,
enabling players to analyze potential move sequences and their consequences.
The system evaluates game positions, suggests optimal moves, and predicts
opponent responses.

Updated for Entity-Predicate hypergraph architecture where:
- CLIF terms (variables, constants) → Entities (Lines of Identity)
- CLIF predicates → Predicates (hyperedges connecting entities)
- CLIF quantifiers → Entity scoping in contexts

The lookahead system supports:
1. Move tree generation and evaluation
2. Position assessment and scoring
3. Strategic move recommendation
4. Opponent response prediction
5. Game outcome probability estimation
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import copy
from collections import defaultdict
import math

from eg_types import EntityId, PredicateId, ContextId, LigatureId, ItemId
from graph import EGGraph
from game_engine import (
    EndoporeuticGameEngine, GameState, GameMove, Player, GameStatus, MoveType
)
from transformations import TransformationType
from pattern_recognizer import PatternRecognitionEngine, PatternType


class PositionEvaluation(Enum):
    """Evaluation of a game position."""
    PROPOSER_WINNING = "proposer_winning"
    PROPOSER_ADVANTAGE = "proposer_advantage"
    BALANCED = "balanced"
    SKEPTIC_ADVANTAGE = "skeptic_advantage"
    SKEPTIC_WINNING = "skeptic_winning"


class MoveQuality(Enum):
    """Quality assessment of a move."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    POOR = "poor"
    BLUNDER = "blunder"


@dataclass
class PositionScore:
    """Numerical score for a game position."""
    raw_score: float  # Positive favors Proposer, negative favors Skeptic
    confidence: float  # 0.0 to 1.0
    evaluation: PositionEvaluation
    factors: Dict[str, float]  # Contributing factors to the score
    
    @property
    def normalized_score(self) -> float:
        """Get score normalized to [-1, 1] range."""
        return max(-1.0, min(1.0, self.raw_score / 100.0))


@dataclass
class MoveEvaluation:
    """Evaluation of a specific move."""
    move: GameMove
    quality: MoveQuality
    score_change: float
    position_after: PositionScore
    tactical_benefits: List[str]
    strategic_risks: List[str]
    opponent_responses: List['MoveEvaluation']
    depth_analyzed: int


@dataclass
class LookaheadNode:
    """Node in the lookahead tree."""
    state: GameState
    move_to_reach: Optional[GameMove]
    parent: Optional['LookaheadNode']
    children: List['LookaheadNode']
    position_score: Optional[PositionScore]
    best_move: Optional[GameMove]
    depth: int
    is_terminal: bool


@dataclass
class LookaheadResult:
    """Result of lookahead analysis."""
    best_move: Optional[GameMove]
    best_score: PositionScore
    principal_variation: List[GameMove]
    move_evaluations: List[MoveEvaluation]
    analysis_depth: int
    nodes_evaluated: int
    time_taken: float


class PositionEvaluator:
    """Evaluates game positions to determine who has the advantage."""
    
    def __init__(self):
        """Initialize the position evaluator."""
        self.pattern_engine = PatternRecognitionEngine()
    
    def evaluate_position(self, state: GameState) -> PositionScore:
        """Evaluate the current position and return a score."""
        if state.status != GameStatus.IN_PROGRESS:
            return self._evaluate_terminal_position(state)
        
        factors = {}
        
        # Material evaluation (entities and predicates)
        material_score = self._evaluate_material(state.graph)
        factors['material'] = material_score
        
        # Structural evaluation (context depth, complexity)
        structural_score = self._evaluate_structure(state.graph)
        factors['structure'] = structural_score
        
        # Tactical evaluation (immediate threats and opportunities)
        tactical_score = self._evaluate_tactics(state)
        factors['tactics'] = tactical_score
        
        # Strategic evaluation (long-term position factors)
        strategic_score = self._evaluate_strategy(state)
        factors['strategy'] = strategic_score
        
        # Mobility evaluation (number of legal moves)
        mobility_score = self._evaluate_mobility(state)
        factors['mobility'] = mobility_score
        
        # Pattern evaluation (logical patterns present)
        pattern_score = self._evaluate_patterns(state.graph)
        factors['patterns'] = pattern_score
        
        # Combine factors with weights
        weights = {
            'material': 0.25,
            'structure': 0.20,
            'tactics': 0.25,
            'strategy': 0.15,
            'mobility': 0.10,
            'patterns': 0.05
        }
        
        raw_score = sum(factors[factor] * weights[factor] for factor in factors)
        
        # Determine evaluation category
        if raw_score > 50:
            evaluation = PositionEvaluation.PROPOSER_WINNING
        elif raw_score > 20:
            evaluation = PositionEvaluation.PROPOSER_ADVANTAGE
        elif raw_score > -20:
            evaluation = PositionEvaluation.BALANCED
        elif raw_score > -50:
            evaluation = PositionEvaluation.SKEPTIC_ADVANTAGE
        else:
            evaluation = PositionEvaluation.SKEPTIC_WINNING
        
        # Calculate confidence based on score magnitude and consistency
        confidence = min(1.0, abs(raw_score) / 100.0)
        
        return PositionScore(
            raw_score=raw_score,
            confidence=confidence,
            evaluation=evaluation,
            factors=factors
        )
    
    def _evaluate_terminal_position(self, state: GameState) -> PositionScore:
        """Evaluate a terminal (ended) game position."""
        if state.status == GameStatus.PROPOSER_WIN:
            return PositionScore(
                raw_score=1000.0,
                confidence=1.0,
                evaluation=PositionEvaluation.PROPOSER_WINNING,
                factors={'terminal': 1000.0}
            )
        elif state.status == GameStatus.SKEPTIC_WIN:
            return PositionScore(
                raw_score=-1000.0,
                confidence=1.0,
                evaluation=PositionEvaluation.SKEPTIC_WINNING,
                factors={'terminal': -1000.0}
            )
        else:  # Draw
            return PositionScore(
                raw_score=0.0,
                confidence=1.0,
                evaluation=PositionEvaluation.BALANCED,
                factors={'terminal': 0.0}
            )
    
    def _evaluate_material(self, graph: EGGraph) -> float:
        """Evaluate material balance (entities and predicates)."""
        entity_count = len(graph.entities)
        predicate_count = len(graph.predicates)
        
        # More entities generally favor the Skeptic (more to attack)
        # More predicates generally favor the Proposer (more assertions)
        material_score = predicate_count * 5 - entity_count * 3
        
        return material_score
    
    def _evaluate_structure(self, graph: EGGraph) -> float:
        """Evaluate structural factors."""
        max_depth = 0
        if graph.context_manager.contexts:
            max_depth = max(ctx.depth for ctx in graph.context_manager.contexts.values())
        
        context_count = len(graph.context_manager.contexts)
        
        # Deeper structures generally favor the Proposer (more complex logic)
        # But too many contexts can be unwieldy
        depth_score = max_depth * 8 - (context_count - max_depth) * 2
        
        return depth_score
    
    def _evaluate_tactics(self, state: GameState) -> float:
        """Evaluate tactical factors (immediate threats)."""
        tactical_score = 0.0
        
        # Check for immediate winning/losing threats
        if state.contested_context:
            items_in_contested = state.graph.context_manager.get_items_in_context(state.contested_context)
            
            # Empty contested context = Skeptic wins
            if not items_in_contested:
                tactical_score -= 500.0
            
            # Very few items = dangerous for Proposer
            elif len(items_in_contested) <= 2:
                tactical_score -= 50.0
            
            # Many items = good for Proposer
            elif len(items_in_contested) >= 5:
                tactical_score += 30.0
        
        return tactical_score
    
    def _evaluate_strategy(self, state: GameState) -> float:
        """Evaluate strategic factors."""
        strategic_score = 0.0
        
        # Analyze variable scoping
        variables_in_graph = sum(1 for e in state.graph.entities.values() 
                               if e.entity_type == 'variable')
        constants_in_graph = sum(1 for e in state.graph.entities.values() 
                               if e.entity_type == 'constant')
        
        # More variables give more flexibility (slight advantage to current player)
        strategic_score += variables_in_graph * 2
        
        # Constants provide concrete claims (advantage to Proposer)
        strategic_score += constants_in_graph * 3
        
        # Analyze ligature connections
        ligature_count = len(state.graph.ligatures)
        strategic_score += ligature_count * 5  # Connections favor Proposer
        
        return strategic_score
    
    def _evaluate_mobility(self, state: GameState) -> float:
        """Evaluate mobility (number of legal moves)."""
        # This would require access to the game engine
        # For now, return a placeholder based on graph complexity
        
        total_items = len(state.graph.entities) + len(state.graph.predicates)
        context_count = len(state.graph.context_manager.contexts)
        
        # More items and contexts generally mean more move options
        mobility_estimate = total_items * 2 + context_count * 3
        
        # Current player benefits from having more options
        if state.current_player == Player.PROPOSER:
            return mobility_estimate * 0.5
        else:
            return -mobility_estimate * 0.5
    
    def _evaluate_patterns(self, graph: EGGraph) -> float:
        """Evaluate logical patterns in the graph."""
        patterns = self.pattern_engine.find_patterns(graph)
        pattern_score = 0.0
        
        for pattern in patterns:
            if pattern.pattern_type == PatternType.UNIVERSAL_QUANTIFICATION:
                pattern_score += 15  # Strong logical structure favors Proposer
            elif pattern.pattern_type == PatternType.EXISTENTIAL_QUANTIFICATION:
                pattern_score += 10  # Quantification favors Proposer
            elif pattern.pattern_type == PatternType.IMPLICATION:
                pattern_score += 12  # Implications favor Proposer
            elif pattern.pattern_type == PatternType.CONJUNCTION:
                pattern_score += 8   # Conjunctions favor Proposer
            elif pattern.pattern_type == PatternType.NEGATION:
                pattern_score -= 5   # Negations can favor Skeptic
        
        return pattern_score


class LookaheadEngine:
    """
    Strategic lookahead engine for the Endoporeutic Game with Entity-Predicate architecture.
    
    Provides deep analysis of move sequences, position evaluation,
    and strategic recommendations for optimal play.
    """
    
    def __init__(self, game_engine: EndoporeuticGameEngine):
        """Initialize the lookahead engine."""
        self.game_engine = game_engine
        self.position_evaluator = PositionEvaluator()
        self.transposition_table: Dict[str, PositionScore] = {}
        self.max_depth = 6
        self.max_nodes = 10000
    
    def analyze_position(self, state: GameState, depth: int = 4) -> LookaheadResult:
        """Analyze the current position to the specified depth."""
        start_time = 0  # Would use time.time() in real implementation
        
        # Create root node
        root = LookaheadNode(
            state=state,
            move_to_reach=None,
            parent=None,
            children=[],
            position_score=None,
            best_move=None,
            depth=0,
            is_terminal=state.status != GameStatus.IN_PROGRESS
        )
        
        # Perform minimax search with alpha-beta pruning
        nodes_evaluated = 0
        best_score = self._minimax(root, depth, -math.inf, math.inf, True, nodes_evaluated)
        
        # Extract results
        best_move = root.best_move
        principal_variation = self._extract_principal_variation(root)
        move_evaluations = self._generate_move_evaluations(root)
        
        end_time = 0  # Would use time.time() in real implementation
        time_taken = end_time - start_time
        
        return LookaheadResult(
            best_move=best_move,
            best_score=best_score,
            principal_variation=principal_variation,
            move_evaluations=move_evaluations,
            analysis_depth=depth,
            nodes_evaluated=nodes_evaluated,
            time_taken=time_taken
        )
    
    def suggest_move(self, state: GameState) -> Optional[GameMove]:
        """Suggest the best move for the current position."""
        if state.status != GameStatus.IN_PROGRESS:
            return None
        
        result = self.analyze_position(state, depth=4)
        return result.best_move
    
    def evaluate_move(self, state: GameState, move: GameMove) -> MoveEvaluation:
        """Evaluate a specific move in the current position."""
        # Apply the move
        try:
            new_state = self.game_engine.apply_move(state, move)
        except ValueError:
            # Illegal move
            return MoveEvaluation(
                move=move,
                quality=MoveQuality.BLUNDER,
                score_change=-1000.0,
                position_after=PositionScore(-1000.0, 1.0, PositionEvaluation.SKEPTIC_WINNING, {}),
                tactical_benefits=[],
                strategic_risks=["Illegal move"],
                opponent_responses=[],
                depth_analyzed=0
            )
        
        # Evaluate positions before and after
        position_before = self.position_evaluator.evaluate_position(state)
        position_after = self.position_evaluator.evaluate_position(new_state)
        
        # Calculate score change (from current player's perspective)
        if state.current_player == Player.PROPOSER:
            score_change = position_after.raw_score - position_before.raw_score
        else:
            score_change = position_before.raw_score - position_after.raw_score
        
        # Determine move quality
        if score_change > 50:
            quality = MoveQuality.EXCELLENT
        elif score_change > 20:
            quality = MoveQuality.GOOD
        elif score_change > -10:
            quality = MoveQuality.NEUTRAL
        elif score_change > -50:
            quality = MoveQuality.POOR
        else:
            quality = MoveQuality.BLUNDER
        
        # Analyze tactical benefits and risks
        tactical_benefits = self._analyze_tactical_benefits(state, new_state, move)
        strategic_risks = self._analyze_strategic_risks(state, new_state, move)
        
        # Analyze opponent responses (shallow)
        opponent_responses = self._analyze_opponent_responses(new_state, depth=2)
        
        return MoveEvaluation(
            move=move,
            quality=quality,
            score_change=score_change,
            position_after=position_after,
            tactical_benefits=tactical_benefits,
            strategic_risks=strategic_risks,
            opponent_responses=opponent_responses,
            depth_analyzed=2
        )
    
    def predict_game_outcome(self, state: GameState) -> Dict[str, float]:
        """Predict the probability of different game outcomes."""
        if state.status != GameStatus.IN_PROGRESS:
            # Game already ended
            if state.status == GameStatus.PROPOSER_WIN:
                return {"proposer_win": 1.0, "skeptic_win": 0.0, "draw": 0.0}
            elif state.status == GameStatus.SKEPTIC_WIN:
                return {"proposer_win": 0.0, "skeptic_win": 1.0, "draw": 0.0}
            else:
                return {"proposer_win": 0.0, "skeptic_win": 0.0, "draw": 1.0}
        
        # Analyze current position
        position_score = self.position_evaluator.evaluate_position(state)
        
        # Convert score to probabilities using sigmoid function
        normalized_score = position_score.normalized_score
        
        # Sigmoid transformation
        proposer_advantage = 1 / (1 + math.exp(-normalized_score * 3))
        
        # Adjust for confidence
        confidence_factor = position_score.confidence
        
        # Calculate probabilities
        if proposer_advantage > 0.6:
            proposer_win_prob = 0.4 + (proposer_advantage - 0.6) * confidence_factor
            skeptic_win_prob = 0.4 - (proposer_advantage - 0.6) * confidence_factor
        elif proposer_advantage < 0.4:
            proposer_win_prob = 0.4 - (0.4 - proposer_advantage) * confidence_factor
            skeptic_win_prob = 0.4 + (0.4 - proposer_advantage) * confidence_factor
        else:
            proposer_win_prob = 0.4
            skeptic_win_prob = 0.4
        
        draw_prob = 1.0 - proposer_win_prob - skeptic_win_prob
        
        return {
            "proposer_win": max(0.0, min(1.0, proposer_win_prob)),
            "skeptic_win": max(0.0, min(1.0, skeptic_win_prob)),
            "draw": max(0.0, min(1.0, draw_prob))
        }
    
    def find_tactical_shots(self, state: GameState) -> List[GameMove]:
        """Find tactical moves that create immediate threats."""
        tactical_moves = []
        
        legal_moves = self.game_engine.get_legal_moves(state)
        
        for move in legal_moves:
            try:
                new_state = self.game_engine.apply_move(state, move)
                
                # Check if this move creates a tactical threat
                if self._is_tactical_shot(state, new_state, move):
                    tactical_moves.append(move)
                    
            except ValueError:
                continue  # Skip illegal moves
        
        return tactical_moves
    
    def analyze_endgame(self, state: GameState) -> Dict[str, Any]:
        """Analyze endgame positions with perfect play."""
        # This would implement endgame tablebase lookup or deep search
        # For now, return basic analysis
        
        contested_items = set()
        if state.contested_context:
            contested_items = state.graph.context_manager.get_items_in_context(state.contested_context)
        
        entities_in_contested = {item for item in contested_items if item in state.graph.entities}
        predicates_in_contested = {item for item in contested_items if item in state.graph.predicates}
        
        is_endgame = len(contested_items) <= 3
        
        return {
            "is_endgame": is_endgame,
            "contested_items": len(contested_items),
            "contested_entities": len(entities_in_contested),
            "contested_predicates": len(predicates_in_contested),
            "theoretical_result": "unknown",  # Would be computed with perfect play
            "key_moves": [],  # Critical moves in the endgame
            "conversion_plan": []  # Plan to convert advantage
        }
    
    # Private helper methods
    
    def _minimax(self, node: LookaheadNode, depth: int, alpha: float, beta: float, 
                maximizing_player: bool, nodes_evaluated: int) -> PositionScore:
        """Minimax algorithm with alpha-beta pruning."""
        nodes_evaluated += 1
        
        # Terminal node or depth limit reached
        if depth == 0 or node.is_terminal or nodes_evaluated >= self.max_nodes:
            node.position_score = self.position_evaluator.evaluate_position(node.state)
            return node.position_score
        
        # Check transposition table
        state_hash = self._compute_state_hash(node.state)
        if state_hash in self.transposition_table:
            return self.transposition_table[state_hash]
        
        # Generate child nodes
        legal_moves = self.game_engine.get_legal_moves(node.state)
        
        if maximizing_player:
            max_eval = PositionScore(-math.inf, 0.0, PositionEvaluation.SKEPTIC_WINNING, {})
            
            for move in legal_moves:
                try:
                    new_state = self.game_engine.apply_move(node.state, move)
                    child_node = LookaheadNode(
                        state=new_state,
                        move_to_reach=move,
                        parent=node,
                        children=[],
                        position_score=None,
                        best_move=None,
                        depth=node.depth + 1,
                        is_terminal=new_state.status != GameStatus.IN_PROGRESS
                    )
                    node.children.append(child_node)
                    
                    eval_score = self._minimax(child_node, depth - 1, alpha, beta, False, nodes_evaluated)
                    
                    if eval_score.raw_score > max_eval.raw_score:
                        max_eval = eval_score
                        node.best_move = move
                    
                    alpha = max(alpha, eval_score.raw_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
                        
                except ValueError:
                    continue  # Skip illegal moves
            
            node.position_score = max_eval
            
        else:
            min_eval = PositionScore(math.inf, 0.0, PositionEvaluation.PROPOSER_WINNING, {})
            
            for move in legal_moves:
                try:
                    new_state = self.game_engine.apply_move(node.state, move)
                    child_node = LookaheadNode(
                        state=new_state,
                        move_to_reach=move,
                        parent=node,
                        children=[],
                        position_score=None,
                        best_move=None,
                        depth=node.depth + 1,
                        is_terminal=new_state.status != GameStatus.IN_PROGRESS
                    )
                    node.children.append(child_node)
                    
                    eval_score = self._minimax(child_node, depth - 1, alpha, beta, True, nodes_evaluated)
                    
                    if eval_score.raw_score < min_eval.raw_score:
                        min_eval = eval_score
                        node.best_move = move
                    
                    beta = min(beta, eval_score.raw_score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
                        
                except ValueError:
                    continue  # Skip illegal moves
            
            node.position_score = min_eval
        
        # Store in transposition table
        self.transposition_table[state_hash] = node.position_score
        
        return node.position_score
    
    def _extract_principal_variation(self, root: LookaheadNode) -> List[GameMove]:
        """Extract the principal variation (best line of play)."""
        pv = []
        current = root
        
        while current.best_move and current.children:
            pv.append(current.best_move)
            # Find the child corresponding to the best move
            for child in current.children:
                if child.move_to_reach == current.best_move:
                    current = child
                    break
            else:
                break  # Best move child not found
        
        return pv
    
    def _generate_move_evaluations(self, root: LookaheadNode) -> List[MoveEvaluation]:
        """Generate evaluations for all legal moves."""
        evaluations = []
        
        for child in root.children:
            if child.move_to_reach and child.position_score:
                # Determine move quality based on score
                score_change = child.position_score.raw_score - (root.position_score.raw_score if root.position_score else 0)
                
                if score_change > 30:
                    quality = MoveQuality.EXCELLENT
                elif score_change > 10:
                    quality = MoveQuality.GOOD
                elif score_change > -10:
                    quality = MoveQuality.NEUTRAL
                elif score_change > -30:
                    quality = MoveQuality.POOR
                else:
                    quality = MoveQuality.BLUNDER
                
                evaluation = MoveEvaluation(
                    move=child.move_to_reach,
                    quality=quality,
                    score_change=score_change,
                    position_after=child.position_score,
                    tactical_benefits=[],
                    strategic_risks=[],
                    opponent_responses=[],
                    depth_analyzed=child.depth
                )
                evaluations.append(evaluation)
        
        # Sort by score change (best first)
        evaluations.sort(key=lambda e: e.score_change, reverse=True)
        
        return evaluations
    
    def _analyze_tactical_benefits(self, old_state: GameState, new_state: GameState, move: GameMove) -> List[str]:
        """Analyze tactical benefits of a move."""
        benefits = []
        
        if move.move_type == MoveType.TRANSFORMATION:
            if move.transformation_type == TransformationType.ERASURE:
                benefits.append("Removes opponent's assertion")
            elif move.transformation_type == TransformationType.INSERTION:
                benefits.append("Adds supporting assertion")
            elif move.transformation_type == TransformationType.ITERATION:
                benefits.append("Copies assertion to deeper context")
            elif move.transformation_type == TransformationType.DOUBLE_CUT_ERASURE:
                benefits.append("Simplifies graph structure")
        
        # Check if move threatens to empty contested context
        if new_state.contested_context:
            items_after = new_state.graph.context_manager.get_items_in_context(new_state.contested_context)
            if len(items_after) <= 1:
                benefits.append("Threatens to empty contested context")
        
        return benefits
    
    def _analyze_strategic_risks(self, old_state: GameState, new_state: GameState, move: GameMove) -> List[str]:
        """Analyze strategic risks of a move."""
        risks = []
        
        # Check if move exposes entities to attack
        old_entities = len(old_state.graph.entities)
        new_entities = len(new_state.graph.entities)
        
        if new_entities > old_entities:
            risks.append("Introduces new entities vulnerable to attack")
        
        # Check if move increases graph complexity unnecessarily
        old_contexts = len(old_state.graph.context_manager.contexts)
        new_contexts = len(new_state.graph.context_manager.contexts)
        
        if new_contexts > old_contexts + 1:
            risks.append("Significantly increases graph complexity")
        
        return risks
    
    def _analyze_opponent_responses(self, state: GameState, depth: int) -> List[MoveEvaluation]:
        """Analyze likely opponent responses."""
        if depth <= 0:
            return []
        
        legal_moves = self.game_engine.get_legal_moves(state)
        responses = []
        
        # Evaluate top few moves
        for move in legal_moves[:3]:  # Limit to top 3 for performance
            evaluation = self.evaluate_move(state, move)
            evaluation.depth_analyzed = depth - 1
            responses.append(evaluation)
        
        # Sort by quality
        responses.sort(key=lambda e: e.score_change, reverse=True)
        
        return responses
    
    def _is_tactical_shot(self, old_state: GameState, new_state: GameState, move: GameMove) -> bool:
        """Check if a move is a tactical shot (creates immediate threat)."""
        # Check if move threatens to win immediately
        if new_state.status in [GameStatus.PROPOSER_WIN, GameStatus.SKEPTIC_WIN]:
            return True
        
        # Check if move threatens to empty contested context
        if new_state.contested_context:
            items_after = new_state.graph.context_manager.get_items_in_context(new_state.contested_context)
            if len(items_after) <= 1:
                return True
        
        # Check if move creates forcing sequence
        opponent_moves = self.game_engine.get_legal_moves(new_state)
        if len(opponent_moves) <= 2:  # Limited opponent options
            return True
        
        return False
    
    def _compute_state_hash(self, state: GameState) -> str:
        """Compute a hash for the game state for transposition table."""
        # Simple hash based on graph structure and game state
        entity_count = len(state.graph.entities)
        predicate_count = len(state.graph.predicates)
        context_count = len(state.graph.context_manager.contexts)
        current_player = state.current_player.value
        contested_context = str(state.contested_context) if state.contested_context else "none"
        
        return f"{entity_count}_{predicate_count}_{context_count}_{current_player}_{contested_context}"


# Convenience functions for strategic analysis

def quick_move_suggestion(game_engine: EndoporeuticGameEngine, state: GameState) -> Optional[GameMove]:
    """Get a quick move suggestion without deep analysis."""
    lookahead = LookaheadEngine(game_engine)
    return lookahead.suggest_move(state)


def analyze_critical_position(game_engine: EndoporeuticGameEngine, state: GameState) -> Dict[str, Any]:
    """Perform deep analysis of a critical position."""
    lookahead = LookaheadEngine(game_engine)
    
    # Deep analysis
    result = lookahead.analyze_position(state, depth=6)
    
    # Tactical analysis
    tactical_shots = lookahead.find_tactical_shots(state)
    
    # Outcome prediction
    outcome_probs = lookahead.predict_game_outcome(state)
    
    # Endgame analysis
    endgame_info = lookahead.analyze_endgame(state)
    
    return {
        "best_move": result.best_move.description if result.best_move else "No move found",
        "evaluation": result.best_score.evaluation.value,
        "score": result.best_score.raw_score,
        "confidence": result.best_score.confidence,
        "principal_variation": [move.description for move in result.principal_variation],
        "tactical_shots": len(tactical_shots),
        "outcome_probabilities": outcome_probs,
        "endgame_info": endgame_info,
        "analysis_depth": result.analysis_depth,
        "nodes_evaluated": result.nodes_evaluated
    }


def compare_moves(game_engine: EndoporeuticGameEngine, state: GameState, 
                 moves: List[GameMove]) -> List[MoveEvaluation]:
    """Compare multiple moves and rank them."""
    lookahead = LookaheadEngine(game_engine)
    
    evaluations = []
    for move in moves:
        evaluation = lookahead.evaluate_move(state, move)
        evaluations.append(evaluation)
    
    # Sort by score change (best first)
    evaluations.sort(key=lambda e: e.score_change, reverse=True)
    
    return evaluations

