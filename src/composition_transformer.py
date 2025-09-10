"""
Composition-aware transformation interface for rule-governed graph building.
Integrates composition contexts with transformation workflows.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json

from composition_context import (
    CompositionContext, 
    CompositionContextManager, 
    StandardCompositionContexts,
    EndoporeuticGameContext
)
from interactive_egif_transformer import InteractiveEGIFTransformer, GraphAnalysis
from egif_transformation_interface import TransformationRequest, TransformationResponse
from egi_core_dau import RelationalGraphWithCuts, ElementID
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif


@dataclass
class CompositionSession:
    """A graph composition session within a specific context."""
    session_id: str
    context: CompositionContext
    current_egi: RelationalGraphWithCuts
    transformation_history: List[Dict[str, Any]]
    description: str = ""


class CompositionTransformer:
    """
    Enhanced transformer that supports rule-governed graph building within composition contexts.
    
    Enables the fundamental requirement: start from empty contexts and execute transformation
    sequences that produce new graphs following EG rules.
    """
    
    def __init__(self):
        self.base_transformer = InteractiveEGIFTransformer()
        self.context_manager = CompositionContextManager()
        self.active_session: Optional[CompositionSession] = None
        self.sessions: Dict[str, CompositionSession] = {}
        
        # Initialize standard contexts
        self._setup_standard_contexts()
    
    def _setup_standard_contexts(self):
        """Set up standard composition contexts."""
        # Standard double cut context for basic graph building
        std_context = StandardCompositionContexts.create_double_cut_context("standard")
        self.context_manager.register_context(std_context)
        
        # Deeper context for complex compositions
        deep_context = StandardCompositionContexts.create_deeper_context("deep", depth=4)
        self.context_manager.register_context(deep_context)
    
    def start_composition_session(self, context_id: str, session_id: str, 
                                description: str = "") -> CompositionSession:
        """
        Start a new composition session in the specified context.
        
        Args:
            context_id: ID of the composition context to use
            session_id: Unique identifier for this session
            description: Optional description of the composition goal
            
        Returns:
            CompositionSession ready for graph building
        """
        if context_id not in self.context_manager.contexts:
            raise ValueError(f"Context {context_id} not found")
        
        context = self.context_manager.contexts[context_id]
        
        # Start with the base context EGI
        session = CompositionSession(
            session_id=session_id,
            context=context,
            current_egi=context.base_egi,
            transformation_history=[],
            description=description
        )
        
        self.sessions[session_id] = session
        self.active_session = session
        self.context_manager.set_active_context(context_id)
        
        # Initialize the base transformer with the context
        self.base_transformer.current_egi = context.base_egi
        self.base_transformer.current_egif = generate_egif(context.base_egi)
        
        return session
    
    def get_composition_analysis(self) -> Optional[GraphAnalysis]:
        """Get analysis of the current composition state."""
        if not self.active_session:
            return None
        
        # Use the base transformer's analysis capabilities
        current_egif = generate_egif(self.active_session.current_egi)
        self.base_transformer.current_egi = self.active_session.current_egi
        self.base_transformer.current_egif = current_egif
        
        return self.base_transformer.analyze_graph(current_egif)
    
    def apply_transformation_in_context(self, rule_name: str, target_area: Optional[ElementID] = None,
                                      selected_elements: Optional[List[ElementID]] = None,
                                      **kwargs) -> TransformationResponse:
        """
        Apply a transformation within the active composition context.
        
        Args:
            rule_name: Name of the transformation rule
            target_area: Target area for the transformation (defaults to composition area)
            selected_elements: Elements to transform
            **kwargs: Additional rule-specific parameters
            
        Returns:
            TransformationResponse with the result
        """
        if not self.active_session:
            raise ValueError("No active composition session")
        
        # Default to composition area if no target specified
        if target_area is None:
            target_area = self.active_session.context.composition_area
        
        # Create transformation request
        current_egif = generate_egif(self.active_session.current_egi)
        request = TransformationRequest(
            source_egif=current_egif,
            rule_name=rule_name,
            target_area_description=str(target_area),
            operation_details={
                "selected_subgraph": selected_elements or [],
                **kwargs
            },
            description=f"Apply {rule_name} in composition context"
        )
        
        # Apply transformation using the base transformer
        response = self.base_transformer.interface.apply_transformation(
            request, existing_egi=self.active_session.current_egi
        )
        
        if response.success:
            # Update session state
            self.active_session.current_egi = response.result_egi
            self.active_session.transformation_history.append({
                "rule": rule_name,
                "target_area": str(target_area),
                "selected_elements": [str(e) for e in (selected_elements or [])],
                "result_egif": response.result_egif,
                "timestamp": response.timestamp
            })
            
            # Update base transformer state
            self.base_transformer.current_egi = response.result_egi
            self.base_transformer.current_egif = response.result_egif
        
        return response
    
    def insert_in_composition_area(self, egif_content: str) -> TransformationResponse:
        """
        Insert content directly into the composition area using INS transformation.
        
        Args:
            egif_content: EGIF string to insert
            
        Returns:
            TransformationResponse with the result
        """
        # Use the correct parameter structure for INS operations
        if not self.active_session:
            raise ValueError("No active composition session")
        
        current_egif = generate_egif(self.active_session.current_egi)
        request = TransformationRequest(
            source_egif=current_egif,
            rule_name="INS",
            target_area_description=str(self.active_session.context.composition_area),
            operation_details={"insert_content": egif_content},
            description=f"Insert content into composition area"
        )
        
        response = self.base_transformer.interface.apply_transformation(
            request, existing_egi=self.active_session.current_egi
        )
        
        if response.success:
            self.active_session.current_egi = response.result_egi
            self.active_session.transformation_history.append({
                "rule": "INS",
                "target_area": str(self.active_session.context.composition_area),
                "content": egif_content,
                "result_egif": response.result_egif,
                "timestamp": getattr(response, 'timestamp', 'unknown')
            })
            
            self.base_transformer.current_egi = response.result_egi
            self.base_transformer.current_egif = response.result_egif
        
        return response
    
    def build_simple_graph(self, predicates: List[str], connections: List[Tuple[str, str]] = None) -> TransformationResponse:
        """
        Build a simple graph by inserting predicates and connecting them.
        
        Args:
            predicates: List of predicate names to insert
            connections: Optional list of (predicate1, predicate2) connections
            
        Returns:
            TransformationResponse with the final result
        """
        if not predicates:
            raise ValueError("Must provide at least one predicate")
        
        # For now, just insert the first predicate as a simple relation
        # More complex graph building will be handled in future iterations
        simple_predicate = f'({predicates[0]} "example")'
        return self.insert_in_composition_area(simple_predicate)
    
    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of the active composition session."""
        if not self.active_session:
            return None
        
        return {
            "session_id": self.active_session.session_id,
            "context_id": self.active_session.context.context_id,
            "context_description": self.active_session.context.description,
            "composition_area": str(self.active_session.context.composition_area),
            "current_egif": generate_egif(self.active_session.current_egi),
            "transformation_count": len(self.active_session.transformation_history),
            "description": self.active_session.description
        }
    
    def list_available_contexts(self) -> List[Tuple[str, str]]:
        """List all available composition contexts."""
        return self.context_manager.list_contexts()
    
    def create_endoporeutic_game_session(self, domain_model_egif: str, 
                                       game_id: str = "endoporeutic_game") -> EndoporeuticGameContext:
        """
        Create an Endoporeutic Game session with domain model context.
        
        Args:
            domain_model_egif: EGIF string for the domain model
            game_id: Unique identifier for the game
            
        Returns:
            EndoporeuticGameContext ready for gameplay
        """
        game_context = EndoporeuticGameContext(domain_model_egif, game_id)
        
        # Register the game's composition context
        self.context_manager.register_context(game_context.context)
        
        return game_context


def test_composition_transformer():
    """Test the composition transformer functionality."""
    print("Testing composition transformer...")
    
    # Test 1: Basic composition session
    print("\n=== Test 1: Basic composition session ===")
    transformer = CompositionTransformer()
    
    # List available contexts
    contexts = transformer.list_available_contexts()
    print(f"Available contexts: {len(contexts)}")
    for ctx_id, desc in contexts:
        print(f"  - {ctx_id}: {desc}")
    
    # Start a composition session
    session = transformer.start_composition_session(
        "standard", 
        "test_session_1", 
        "Testing basic graph building"
    )
    print(f"Started session: {session.session_id}")
    
    # Get initial analysis
    analysis = transformer.get_composition_analysis()
    if analysis:
        print(f"Initial state - Cuts: {analysis.cut_count}, Areas: {len(analysis.areas)}")
        print(f"Initial EGIF: {analysis.egif}")
    
    # Test 2: Simple graph building
    print("\n=== Test 2: Simple graph building ===")
    try:
        # Insert a simple predicate
        response = transformer.insert_in_composition_area("(Human \"Socrates\")")
        if response.success:
            print(f"Inserted predicate successfully")
            print(f"Result EGIF: {response.result_egif}")
        else:
            print(f"Insertion failed: {response.error_message}")
    except Exception as e:
        print(f"Error during insertion: {e}")
    
    # Test 3: Session summary
    print("\n=== Test 3: Session summary ===")
    summary = transformer.get_session_summary()
    if summary:
        print(f"Session summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    
    # Test 4: Build simple connected graph
    print("\n=== Test 4: Build simple connected graph ===")
    try:
        transformer2 = CompositionTransformer()
        session2 = transformer2.start_composition_session(
            "standard", 
            "test_session_2", 
            "Testing connected graph building"
        )
        
        response = transformer2.build_simple_graph(
            ["Human", "Mortal"], 
            [("Human", "Mortal")]
        )
        if response.success:
            print(f"Built connected graph successfully")
            print(f"Result EGIF: {response.result_egif}")
        else:
            print(f"Graph building failed: {response.error_message}")
    except Exception as e:
        print(f"Error during graph building: {e}")


if __name__ == "__main__":
    test_composition_transformer()
