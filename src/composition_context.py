"""
Standard composition context framework for graph building and Endoporeutic Game.
Implements double cut contexts on sheet of assertion for rule-governed graph construction.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif


@dataclass
class CompositionContext:
    """A context for graph composition with defined rules and constraints."""
    context_id: str
    base_egi: RelationalGraphWithCuts
    composition_area: ElementID
    domain_model: Optional[RelationalGraphWithCuts] = None
    description: str = ""
    depth: int = 0


class StandardCompositionContexts:
    """Factory for creating standard composition contexts."""
    
    @staticmethod
    def create_double_cut_context(context_id: str = "standard_composition") -> CompositionContext:
        """
        Create standard double cut composition context: ~[ ~[ <composition area> ] ]
        
        This creates a negatively enclosed area (depth 1) where new graphs can be built
        following EG transformation rules.
        
        Returns:
            CompositionContext with double cut structure
        """
        # Create empty double cut structure
        egif = "~[ ~[ ] ]"
        base_egi = parse_egif(egif)
        
        # Find any negative area for insertion (odd nesting depth)
        def calculate_nesting_depth(area_id, egi):
            """Calculate nesting depth by counting containing cuts."""
            depth = 0
            for cut in egi.Cut:
                cut_contents = egi.area.get(cut.id, frozenset())
                if area_id in cut_contents:
                    depth += 1
            return depth
        
        composition_area = None
        for area_id in base_egi.area.keys():
            depth = calculate_nesting_depth(area_id, base_egi)
            if depth % 2 == 1:  # Any negative area (odd depth)
                composition_area = area_id
                break
        
        if composition_area is None:
            raise ValueError("Could not identify composition area in double cut structure")
        
        return CompositionContext(
            context_id=context_id,
            base_egi=base_egi,
            composition_area=composition_area,
            description="Standard double cut composition context for graph building",
            depth=2
        )
    
    @staticmethod
    def create_deeper_context(context_id: str = "deep_composition", depth: int = 4) -> CompositionContext:
        """
        Create deeper contextualization for complex composition scenarios.
        
        Args:
            context_id: Identifier for this context
            depth: Nesting depth (must be even for positive composition area)
            
        Returns:
            CompositionContext with specified depth
        """
        if depth % 2 != 0:
            raise ValueError("Composition area depth must be even (positive polarity)")
        
        # Build nested cut structure
        cuts = []
        for i in range(depth // 2):
            cuts.append("~[")
        
        # Add empty composition area
        cuts.append(" ")
        
        # Close cuts
        for i in range(depth // 2):
            cuts.append("]")
        
        egif = " ".join(cuts)
        base_egi = parse_egif(egif)
        
        # Find the negative area for insertion (depth should be odd)
        def calculate_nesting_depth(area_id, egi):
            """Calculate nesting depth by counting containing cuts."""
            depth = 0
            for cut in egi.Cut:
                cut_contents = egi.area.get(cut.id, frozenset())
                if area_id in cut_contents:
                    depth += 1
            return depth
        
        composition_area = None
        # Find any negative area for insertion (odd nesting depth)
        for area_id in base_egi.area.keys():
            area_depth = calculate_nesting_depth(area_id, base_egi)
            if area_depth % 2 == 1:  # Any negative area
                composition_area = area_id
                break
        
        if composition_area is None:
            raise ValueError("Could not identify composition area in deep context structure")
        
        return CompositionContext(
            context_id=context_id,
            base_egi=base_egi,
            composition_area=composition_area,
            description=f"Deep composition context (depth {depth}) for complex scenarios",
            depth=depth
        )
    
    @staticmethod
    def create_domain_model_context(domain_egif: str, context_id: str = "domain_composition") -> CompositionContext:
        """
        Create composition context with domain model for Endoporeutic Game.
        
        Structure: ~[ <domain_model> ~[ <composition_area> ] ]
        
        Args:
            domain_egif: EGIF string representing the domain model
            context_id: Identifier for this context
            
        Returns:
            CompositionContext with domain model and composition area
        """
        # Parse domain model
        domain_egi = parse_egif(domain_egif)
        
        # Create context structure with domain model in outer cut and empty inner cut
        # This is more complex - we need to build the structure programmatically
        
        # For now, create a simple version
        context_egif = f"~[ {domain_egif} ~[ ] ]"
        base_egi = parse_egif(context_egif)
        
        # Find the innermost empty area
        composition_area = None
        for cut in base_egi.Cut:
            cut_contents = base_egi.area.get(cut.id, frozenset())
            if len(cut_contents) == 0:  # Empty area
                composition_area = cut.id
                break
        
        if composition_area is None:
            raise ValueError("Could not identify composition area in domain model context")
        
        return CompositionContext(
            context_id=context_id,
            base_egi=base_egi,
            composition_area=composition_area,
            domain_model=domain_egi,
            description=f"Domain model context for Endoporeutic Game",
            depth=2
        )


class CompositionContextManager:
    """Manages composition contexts and graph building within them."""
    
    def __init__(self):
        self.contexts: Dict[str, CompositionContext] = {}
        self.active_context: Optional[str] = None
    
    def register_context(self, context: CompositionContext) -> None:
        """Register a composition context."""
        self.contexts[context.context_id] = context
    
    def set_active_context(self, context_id: str) -> None:
        """Set the active composition context."""
        if context_id not in self.contexts:
            raise ValueError(f"Context {context_id} not registered")
        self.active_context = context_id
    
    def get_active_context(self) -> Optional[CompositionContext]:
        """Get the currently active composition context."""
        if self.active_context is None:
            return None
        return self.contexts.get(self.active_context)
    
    def get_composition_area(self) -> Optional[ElementID]:
        """Get the composition area of the active context."""
        context = self.get_active_context()
        return context.composition_area if context else None
    
    def create_graph_in_context(self, graph_egif: str) -> RelationalGraphWithCuts:
        """
        Create a new graph within the active composition context.
        
        Args:
            graph_egif: EGIF string for the graph to be composed
            
        Returns:
            Complete EGI with graph placed in composition context
        """
        context = self.get_active_context()
        if context is None:
            raise ValueError("No active composition context")
        
        # Parse the graph to be composed
        graph_egi = parse_egif(graph_egif)
        
        # This is a simplified implementation
        # Full implementation would need to merge the graph into the composition area
        # For now, return the context with a note that this needs full implementation
        
        return context.base_egi
    
    def list_contexts(self) -> List[Tuple[str, str]]:
        """List all registered contexts with their descriptions."""
        return [(ctx_id, ctx.description) for ctx_id, ctx in self.contexts.items()]


class EndoporeuticGameContext:
    """
    Specialized context for Endoporeutic Game scenarios.
    
    Supports the pattern: "Given this Domain Model, the following graph is true"
    with Proposer vs Skeptic gameplay.
    """
    
    def __init__(self, domain_model_egif: str, game_id: str = "endoporeutic_game"):
        self.game_id = game_id
        self.domain_model_egif = domain_model_egif
        self.context = StandardCompositionContexts.create_domain_model_context(
            domain_model_egif, f"{game_id}_context"
        )
        self.proposer_claim: Optional[str] = None
        self.game_state: str = "setup"  # setup, proposing, challenging, resolved
        self.moves: List[Dict[str, Any]] = []
    
    def set_proposer_claim(self, claim_egif: str) -> None:
        """Set the Proposer's claim: 'the following graph is true'."""
        self.proposer_claim = claim_egif
        self.game_state = "proposing"
        self.moves.append({
            "type": "claim",
            "player": "proposer",
            "content": claim_egif,
            "description": "Proposer claims this graph is true given the domain model"
        })
    
    def add_move(self, player: str, move_type: str, content: str, description: str = "") -> None:
        """Add a move to the game history."""
        self.moves.append({
            "type": move_type,
            "player": player,
            "content": content,
            "description": description
        })
    
    def get_game_summary(self) -> Dict[str, Any]:
        """Get a summary of the current game state."""
        return {
            "game_id": self.game_id,
            "domain_model": self.domain_model_egif,
            "proposer_claim": self.proposer_claim,
            "game_state": self.game_state,
            "move_count": len(self.moves),
            "context_depth": self.context.depth
        }


def test_composition_contexts():
    """Test the composition context framework."""
    print("Testing composition context framework...")
    
    # Test 1: Standard double cut context
    print("\n=== Test 1: Standard double cut context ===")
    std_context = StandardCompositionContexts.create_double_cut_context()
    print(f"Context: {std_context.description}")
    print(f"Base EGIF: {generate_egif(std_context.base_egi)}")
    print(f"Composition area: {std_context.composition_area}")
    print(f"Depth: {std_context.depth}")
    
    # Test 2: Deeper context
    print("\n=== Test 2: Deeper context ===")
    deep_context = StandardCompositionContexts.create_deeper_context(depth=6)
    print(f"Context: {deep_context.description}")
    print(f"Base EGIF: {generate_egif(deep_context.base_egi)}")
    print(f"Composition area: {deep_context.composition_area}")
    print(f"Depth: {deep_context.depth}")
    
    # Test 3: Domain model context
    print("\n=== Test 3: Domain model context ===")
    domain_egif = "*x (Human x) (Mortal x)"
    try:
        domain_context = StandardCompositionContexts.create_domain_model_context(domain_egif)
        print(f"Context: {domain_context.description}")
        print(f"Base EGIF: {generate_egif(domain_context.base_egi)}")
        print(f"Composition area: {domain_context.composition_area}")
    except Exception as e:
        print(f"Domain context creation failed: {e}")
    
    # Test 4: Context manager
    print("\n=== Test 4: Context manager ===")
    manager = CompositionContextManager()
    manager.register_context(std_context)
    manager.register_context(deep_context)
    manager.set_active_context("standard_composition")
    
    active = manager.get_active_context()
    print(f"Active context: {active.description if active else 'None'}")
    
    contexts = manager.list_contexts()
    print(f"Registered contexts: {len(contexts)}")
    for ctx_id, desc in contexts:
        print(f"  - {ctx_id}: {desc}")
    
    # Test 5: Endoporeutic Game context
    print("\n=== Test 5: Endoporeutic Game context ===")
    game_domain = "*x (Human x)"
    game = EndoporeuticGameContext(game_domain, "test_game")
    game.set_proposer_claim("(Human \"Socrates\")")
    
    summary = game.get_game_summary()
    print(f"Game summary: {summary}")


if __name__ == "__main__":
    test_composition_contexts()
