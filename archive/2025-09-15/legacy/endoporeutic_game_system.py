"""
Endoporeutic Game Domain Model and Proof Context System.
Implements the framework for Proposer vs Skeptic gameplay with domain models.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from composition_context import CompositionContext, StandardCompositionContexts

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from egif_transformation_interface import (
    EGIFTransformationInterface,
    TransformationRequest,
)
from graph_isomorphism_engine import GraphIsomorphismEngine, IsomorphismValidator


class GameState(Enum):
    """States of an Endoporeutic Game."""

    SETUP = "setup"
    DOMAIN_ESTABLISHED = "domain_established"
    CLAIM_MADE = "claim_made"
    CHALLENGING = "challenging"
    PROOF_ATTEMPT = "proof_attempt"
    DISPROOF_ATTEMPT = "disproof_attempt"
    RESOLVED_PROVEN = "resolved_proven"
    RESOLVED_DISPROVEN = "resolved_disproven"
    ABANDONED = "abandoned"


class PlayerRole(Enum):
    """Roles in the Endoporeutic Game."""

    PROPOSER = "proposer"  # Graphist - makes claims and attempts proofs
    SKEPTIC = "skeptic"  # Grapheus - challenges and attempts disproofs
    UMPIRE = "umpire"  # Optional - validates moves and rules


@dataclass
class GameMove:
    """A single move in the Endoporeutic Game."""

    move_id: str
    player: PlayerRole
    move_type: str
    timestamp: datetime
    content: Dict[str, Any]
    description: str
    egif_before: Optional[str] = None
    egif_after: Optional[str] = None
    transformation_used: Optional[str] = None
    is_valid: bool = True
    validation_notes: str = ""


@dataclass
class DomainModel:
    """Domain model for the Endoporeutic Game context."""

    domain_id: str
    name: str
    description: str
    domain_egif: str
    domain_egi: RelationalGraphWithCuts
    axioms: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofContext:
    """Context for proof attempts within the game."""

    context_id: str
    domain_model: DomainModel
    composition_context: CompositionContext
    current_state: RelationalGraphWithCuts
    proof_steps: List[GameMove] = field(default_factory=list)
    is_valid_context: bool = True
    validation_errors: List[str] = field(default_factory=list)


class EndoporeuticGameEngine:
    """
    Core engine for managing Endoporeutic Game sessions.

    Implements the pattern: "Given this Domain Model, the following graph is true"
    with structured gameplay between Proposer and Skeptic.
    """

    def __init__(self):
        self.transformation_interface = EGIFTransformationInterface()
        self.active_games: Dict[str, "EndoporeuticGame"] = {}
        self.domain_models: Dict[str, DomainModel] = {}

    def create_domain_model(
        self,
        domain_id: str,
        name: str,
        description: str,
        domain_egif: str,
        axioms: List[str] = None,
    ) -> DomainModel:
        """Create a new domain model for use in games."""

        try:
            domain_egi = parse_egif(domain_egif)
        except Exception as e:
            raise ValueError(f"Invalid domain EGIF: {e}")

        domain_model = DomainModel(
            domain_id=domain_id,
            name=name,
            description=description,
            domain_egif=domain_egif,
            domain_egi=domain_egi,
            axioms=axioms or [],
            constraints=[],
            metadata={"created": datetime.now().isoformat()},
        )

        self.domain_models[domain_id] = domain_model
        return domain_model

    def start_game(
        self,
        game_id: str,
        domain_id: str,
        proposer_id: str,
        skeptic_id: str,
        umpire_id: Optional[str] = None,
    ) -> "EndoporeuticGame":
        """Start a new Endoporeutic Game session."""

        if domain_id not in self.domain_models:
            raise ValueError(f"Domain model {domain_id} not found")

        domain_model = self.domain_models[domain_id]

        game = EndoporeuticGame(
            game_id=game_id,
            domain_model=domain_model,
            proposer_id=proposer_id,
            skeptic_id=skeptic_id,
            umpire_id=umpire_id,
            engine=self,
        )

        self.active_games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional["EndoporeuticGame"]:
        """Get an active game by ID."""
        return self.active_games.get(game_id)

    def list_domain_models(self) -> List[Tuple[str, str, str]]:
        """List available domain models."""
        return [
            (dm.domain_id, dm.name, dm.description)
            for dm in self.domain_models.values()
        ]


class EndoporeuticGame:
    """
    A single Endoporeutic Game session between Proposer and Skeptic.

    Game flow:
    1. Domain model is established
    2. Proposer makes a claim: "Given domain D, graph G is true"
    3. Skeptic can challenge the claim
    4. Players engage in proof/disproof attempts using EG transformations
    5. Game resolves when claim is proven, disproven, or abandoned
    """

    def __init__(self, domain_model: "DomainModel"):
        """Initialize game with domain model."""
        self.game_id = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.domain_model = domain_model
        self.state = GameState.SETUP
        self.moves: List[GameMove] = []
        self.current_claim: Optional[str] = None
        self.proof_context: Optional["ProofContext"] = None
        self.engine = EndoporeuticGameEngine()
        self.isomorphism_validator = IsomorphismValidator()

        # Initialize composition context for proof attempts
        self.composition_context = StandardCompositionContexts.create_basic_context()

        # Set up proof context with domain
        self.proof_context = ProofContext(
            context_id=f"proof_{self.game_id}",
            domain_model=self.domain_model,
            composition_context=self.composition_context,
            current_state=self.domain_model.domain_egi,
        )

        self.state = GameState.DOMAIN_ESTABLISHED

        # Initialize the game context
        self._initialize_game_context()

    def _initialize_game_context(self):
        """Initialize the game's proof context."""

        # Create composition context with domain model
        composition_context = StandardCompositionContexts.create_domain_model_context(
            self.domain_model.domain_egif, f"{self.game_id}_context"
        )

        self.proof_context = ProofContext(
            context_id=f"{self.game_id}_proof",
            domain_model=self.domain_model,
            composition_context=composition_context,
            current_state=composition_context.base_egi,
        )

        self.state = GameState.DOMAIN_ESTABLISHED

        # Record initialization move
        self._record_move(
            player=PlayerRole.UMPIRE,
            move_type="initialize",
            content={
                "domain_model": self.domain_model.domain_id,
                "context_created": True,
            },
            description=f"Game initialized with domain model: {self.domain_model.name}",
        )

    def make_claim(self, claim_egif: str, description: str = "") -> bool:
        """Proposer makes a claim about what should be true given the domain."""

        if self.state != GameState.DOMAIN_ESTABLISHED:
            raise ValueError(f"Cannot make claim in state {self.state}")

        try:
            # Validate the claim EGIF
            claim_egi = parse_egif(claim_egif)

            self.current_claim = claim_egif
            self.state = GameState.CLAIM_MADE

            self._record_move(
                player=PlayerRole.PROPOSER,
                move_type="claim",
                content={"claim_egif": claim_egif, "claim_description": description},
                description=f"Proposer claims: {description or 'Graph is true given domain'}",
            )

            return True

        except Exception as e:
            self._record_move(
                player=PlayerRole.PROPOSER,
                move_type="claim",
                content={"claim_egif": claim_egif, "error": str(e)},
                description=f"Invalid claim: {e}",
                is_valid=False,
            )
            return False

    def challenge_claim(self, challenge_reason: str) -> bool:
        """Skeptic challenges the Proposer's claim."""

        if self.state != GameState.CLAIM_MADE:
            raise ValueError(f"Cannot challenge in state {self.state}")

        self.state = GameState.CHALLENGING

        self._record_move(
            player=PlayerRole.SKEPTIC,
            move_type="challenge",
            content={
                "challenge_reason": challenge_reason,
                "challenged_claim": self.current_claim,
            },
            description=f"Skeptic challenges: {challenge_reason}",
        )

        return True

    def attempt_proof_step(
        self,
        player: PlayerRole,
        transformation_rule: str,
        target_area: str,
        operation_details: Dict[str, Any],
        description: str = "",
    ) -> bool:
        """Attempt a proof step using EG transformations with isomorphism validation."""

        if self.state not in [
            GameState.CHALLENGING,
            GameState.PROOF_ATTEMPT,
            GameState.DISPROOF_ATTEMPT,
        ]:
            raise ValueError(f"Cannot make proof moves in state {self.state}")

        if not self.proof_context:
            raise ValueError("No proof context available")

        try:
            # Create transformation request
            current_egif = generate_egif(self.proof_context.current_state)

            request = TransformationRequest(
                source_egif=current_egif,
                rule_name=transformation_rule,
                target_area_description=target_area,
                operation_details=operation_details,
                description=description,
            )

            # Apply transformation
            response = self.engine.transformation_interface.apply_transformation(
                request, existing_egi=self.proof_context.current_state
            )

            if response.success:
                # Validate isomorphism for proof steps that require it
                if self._requires_isomorphism_validation(transformation_rule):
                    if not self._validate_proof_step_isomorphism(
                        response, operation_details
                    ):
                        self._record_move(
                            player=player,
                            move_type="proof_step",
                            content={
                                "transformation_rule": transformation_rule,
                                "operation_details": operation_details,
                                "error": "Isomorphism validation failed",
                            },
                            description=f"Invalid proof step: {description}",
                            is_valid=False,
                        )
                        return False

                # Update proof context
                self.proof_context.current_state = response.result_egi

                # Update game state
                if player == PlayerRole.PROPOSER:
                    self.state = GameState.PROOF_ATTEMPT
                else:
                    self.state = GameState.DISPROOF_ATTEMPT

                # Record successful move
                move = self._record_move(
                    player=player,
                    move_type="transformation",
                    content={
                        "rule": transformation_rule,
                        "target_area": target_area,
                        "operation_details": operation_details,
                        "success": True,
                    },
                    description=description or f"Applied {transformation_rule}",
                    egif_before=current_egif,
                    egif_after=response.result_egif,
                    transformation_used=transformation_rule,
                )

                self.proof_context.proof_steps.append(move)
                return True

            else:
                # Record failed move
                self._record_move(
                    player=player,
                    move_type="transformation",
                    content={
                        "rule": transformation_rule,
                        "target_area": target_area,
                        "operation_details": operation_details,
                        "success": False,
                        "error": response.error_message,
                    },
                    description=f"Failed {transformation_rule}: {response.error_message}",
                    is_valid=False,
                    validation_notes=response.error_message,
                )
                return False

        except Exception as e:
            self._record_move(
                player=player,
                move_type="transformation",
                content={"rule": transformation_rule, "error": str(e)},
                description=f"Error in transformation: {e}",
                is_valid=False,
                validation_notes=str(e),
            )
            return False

    def _requires_isomorphism_validation(self, transformation_rule: str) -> bool:
        """Check if transformation rule requires isomorphism validation."""
        # IT- (deiteration) requires isomorphism validation
        # IT+ (iteration) may also require validation in some contexts
        return transformation_rule in ["IT-", "IT+"]

    def _validate_proof_step_isomorphism(
        self, response, operation_details: Dict[str, Any]
    ) -> bool:
        """Validate isomorphism requirements for proof steps."""
        if not response.result_egi or not self.proof_context:
            return False

        # For IT- operations, validate that the removed subgraph had an isomorphic counterpart
        if "selected_subgraph" in operation_details:
            selected_elements = operation_details["selected_subgraph"]
            target_area = operation_details.get("target_area", "sheet")

            # Use isomorphism validator to check deiteration validity
            nesting_hierarchy = self._get_nesting_hierarchy(
                self.proof_context.current_state, target_area
            )
            is_valid, error = self.isomorphism_validator.validate_deiteration_candidate(
                self.proof_context.current_state,
                frozenset(selected_elements),
                target_area,
                nesting_hierarchy,
            )

            return is_valid

        return True  # No specific validation needed

    def _get_nesting_hierarchy(
        self, egi: RelationalGraphWithCuts, target_area: str
    ) -> List[str]:
        """Get nesting hierarchy for area validation."""
        hierarchy = [target_area]
        current_area = target_area

        # Walk up the nesting chain to sheet
        while current_area != egi.sheet:
            # Find which area contains current_area
            parent_area = None
            for area_id, contents in egi.area.items():
                if current_area in contents:
                    parent_area = area_id
                    break

            if parent_area is None:
                break

            hierarchy.append(parent_area)
            current_area = parent_area

        return hierarchy

    def declare_victory(self, player: PlayerRole, victory_reason: str) -> bool:
        """Player declares victory with reasoning."""

        if player == PlayerRole.PROPOSER:
            self.state = GameState.RESOLVED_PROVEN
            move_type = "victory_claim_proven"
        else:
            self.state = GameState.RESOLVED_DISPROVEN
            move_type = "victory_claim_disproven"

        self._record_move(
            player=player,
            move_type=move_type,
            content={
                "victory_reason": victory_reason,
                "final_state": (
                    generate_egif(self.proof_context.current_state)
                    if self.proof_context
                    else None
                ),
            },
            description=f"{player.value.title()} declares victory: {victory_reason}",
        )

        return True

    def abandon_game(self, reason: str = "Game abandoned") -> bool:
        """Abandon the current game."""

        self.state = GameState.ABANDONED

        self._record_move(
            player=PlayerRole.UMPIRE,
            move_type="abandon",
            content={"reason": reason},
            description=f"Game abandoned: {reason}",
        )

        return True

    def _record_move(
        self,
        player: PlayerRole,
        move_type: str,
        content: Dict[str, Any],
        description: str,
        egif_before: Optional[str] = None,
        egif_after: Optional[str] = None,
        transformation_used: Optional[str] = None,
        is_valid: bool = True,
        validation_notes: str = "",
    ) -> GameMove:
        """Record a move in the game history."""

        move = GameMove(
            move_id=f"{self.game_id}_move_{len(self.moves) + 1}",
            player=player,
            move_type=move_type,
            timestamp=datetime.now(),
            content=content,
            description=description,
            egif_before=egif_before,
            egif_after=egif_after,
            transformation_used=transformation_used,
            is_valid=is_valid,
            validation_notes=validation_notes,
        )

        self.moves.append(move)
        self.metadata["last_activity"] = datetime.now().isoformat()

        return move

    def get_game_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the game state."""

        return {
            "game_id": self.game_id,
            "state": self.state.value,
            "domain_model": {
                "id": self.domain_model.domain_id,
                "name": self.domain_model.name,
                "description": self.domain_model.description,
            },
            "players": {
                "proposer": self.proposer_id,
                "skeptic": self.skeptic_id,
                "umpire": self.umpire_id,
            },
            "current_claim": self.current_claim,
            "move_count": len(self.moves),
            "proof_steps": (
                len(self.proof_context.proof_steps) if self.proof_context else 0
            ),
            "current_egif": (
                generate_egif(self.proof_context.current_state)
                if self.proof_context
                else None
            ),
            "metadata": self.metadata,
        }

    def export_game_transcript(self) -> Dict[str, Any]:
        """Export complete game transcript for analysis."""

        return {
            "game_summary": self.get_game_summary(),
            "domain_model": {
                "domain_id": self.domain_model.domain_id,
                "name": self.domain_model.name,
                "description": self.domain_model.description,
                "domain_egif": self.domain_model.domain_egif,
                "axioms": self.domain_model.axioms,
            },
            "moves": [
                {
                    "move_id": move.move_id,
                    "player": move.player.value,
                    "move_type": move.move_type,
                    "timestamp": move.timestamp.isoformat(),
                    "description": move.description,
                    "content": move.content,
                    "egif_before": move.egif_before,
                    "egif_after": move.egif_after,
                    "transformation_used": move.transformation_used,
                    "is_valid": move.is_valid,
                    "validation_notes": move.validation_notes,
                }
                for move in self.moves
            ],
        }


def test_endoporeutic_game_system():
    """Test the Endoporeutic Game system."""
    print("=== Testing Endoporeutic Game System ===")

    # Create game engine
    engine = EndoporeuticGameEngine()

    # Test 1: Create domain model
    print("\n--- Test 1: Create Domain Model ---")
    domain_model = engine.create_domain_model(
        domain_id="human_mortality",
        name="Human Mortality Domain",
        description="Basic domain about humans and mortality",
        domain_egif="*x (Human x) (Mortal x)",
        axioms=["All humans are mortal"],
    )
    print(f"Created domain model: {domain_model.name}")

    # Test 2: Start game
    print("\n--- Test 2: Start Game ---")
    game = engine.start_game(
        game_id="test_game_1",
        domain_id="human_mortality",
        proposer_id="alice",
        skeptic_id="bob",
    )
    print(f"Started game: {game.game_id}")
    print(f"Game state: {game.state.value}")

    # Test 3: Make claim
    print("\n--- Test 3: Proposer Makes Claim ---")
    claim_success = game.make_claim(
        claim_egif='(Human "Socrates")', description="Socrates is human"
    )
    print(f"Claim made successfully: {claim_success}")
    print(f"Game state: {game.state.value}")

    # Test 4: Challenge claim
    print("\n--- Test 4: Skeptic Challenges ---")
    challenge_success = game.challenge_claim("Need proof that Socrates exists")
    print(f"Challenge made successfully: {challenge_success}")
    print(f"Game state: {game.state.value}")

    # Test 5: Attempt proof step
    print("\n--- Test 5: Proof Step Attempt ---")
    try:
        proof_success = game.attempt_proof_step(
            player=PlayerRole.PROPOSER,
            transformation_rule="INS",
            target_area="negative_area",
            operation_details={"insert_content": '(Exists "Socrates")'},
            description="Insert existence claim for Socrates",
        )
        print(f"Proof step successful: {proof_success}")
        print(f"Game state: {game.state.value}")
    except Exception as e:
        print(f"Proof step failed: {e}")

    # Test 6: Game summary
    print("\n--- Test 6: Game Summary ---")
    summary = game.get_game_summary()
    print(f"Game summary:")
    for key, value in summary.items():
        if key != "current_egif":  # Skip long EGIF output
            print(f"  {key}: {value}")

    # Test 7: Export transcript
    print("\n--- Test 7: Export Transcript ---")
    transcript = game.export_game_transcript()
    print(f"Transcript contains {len(transcript['moves'])} moves")

    return engine, game


if __name__ == "__main__":
    test_endoporeutic_game_system()
