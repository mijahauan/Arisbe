"""
Simple graph building system starting from empty contexts.
Builds graphs through rule-governed transformations in baby steps.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
from immutable_transformation_architecture import (
    TransformationRuleType, ContextType, EGISnapshot
)
from egi_transformation_pipeline import EGITransformationPipeline


class GraphBuildingContext(Enum):
    """Different contexts for graph building."""
    EMPTY_SHEET = "empty_sheet"
    DESIGNATED_AREA = "designated_area"
    COMPOSITION_CONTEXT = "composition_context"


@dataclass
class GraphUtterance:
    """A small graph utterance built through transformation sequence."""
    utterance_id: str
    title: str
    description: str
    initial_egi_id: str
    final_egi_id: str
    transformation_steps: List[str]
    building_context: GraphBuildingContext
    created_at: datetime
    
    def get_step_count(self) -> int:
        """Get number of transformation steps."""
        return len(self.transformation_steps)


@dataclass
class BuildingSession:
    """A session of graph building with multiple utterances."""
    session_id: str
    title: str
    utterances: List[str] = field(default_factory=list)
    current_context_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    
    def add_utterance(self, utterance_id: str) -> None:
        """Add an utterance to this session."""
        self.utterances.append(utterance_id)


class SimpleGraphBuilder:
    """Simple system for building graphs through rule-governed transformations."""
    
    def __init__(self):
        self.pipeline = EGITransformationPipeline()
        self.utterances: Dict[str, GraphUtterance] = {}
        self.sessions: Dict[str, BuildingSession] = {}
        self.active_session_id: Optional[str] = None
    
    def create_empty_context(self, context_type: GraphBuildingContext = GraphBuildingContext.EMPTY_SHEET) -> str:
        """Create an empty context for graph building."""
        context_id = str(uuid.uuid4())
        
        # Create empty EGI
        empty_egi = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet="sheet",
            Cut=frozenset(),
            area=frozendict({"sheet": frozenset()}),
            rel=frozendict()
        )
        
        # Store empty EGI
        empty_snapshot = EGISnapshot(
            egi_id=context_id,
            egi_state=empty_egi,
            timestamp=datetime.now(),
            context_type=ContextType.ERGASTERION,
            provenance_step_id=None,
            logical_description=f"Empty context for graph building ({context_type.value})",
            spatial_layout=frozendict()
        )
        
        self.pipeline.repository.store_egi_snapshot(empty_snapshot)
        return context_id
    
    def start_building_session(self, title: str) -> str:
        """Start a new graph building session."""
        session_id = str(uuid.uuid4())
        
        session = BuildingSession(
            session_id=session_id,
            title=title
        )
        
        self.sessions[session_id] = session
        self.active_session_id = session_id
        
        return session_id
    
    def build_graph_utterance(self, title: str, description: str, 
                            building_steps: List[Dict[str, Any]],
                            context_type: GraphBuildingContext = GraphBuildingContext.EMPTY_SHEET) -> str:
        """Build a small graph utterance through transformation sequence."""
        utterance_id = str(uuid.uuid4())
        
        # Create empty starting context
        initial_egi_id = self.create_empty_context(context_type)
        
        # Apply transformation steps
        current_egi_id = initial_egi_id
        transformation_step_ids = []
        
        for i, step_data in enumerate(building_steps):
            try:
                new_egi_id = self.pipeline.apply_transformation(
                    source_egi_id=current_egi_id,
                    rule_type=step_data["rule_type"],
                    transformation_data=step_data["transformation_data"],
                    context_type=ContextType.ERGASTERION,
                    logical_justification=step_data.get("justification", f"Step {i+1}")
                )
                
                # Find the transformation step that was created
                for step in self.pipeline.repository.transformation_steps.values():
                    if step.target_egi_id == new_egi_id and step.source_egi_id == current_egi_id:
                        transformation_step_ids.append(step.step_id)
                        break
                
                current_egi_id = new_egi_id
                
            except Exception as e:
                print(f"Error in transformation step {i+1}: {e}")
                break
        
        # Create graph utterance
        utterance = GraphUtterance(
            utterance_id=utterance_id,
            title=title,
            description=description,
            initial_egi_id=initial_egi_id,
            final_egi_id=current_egi_id,
            transformation_steps=transformation_step_ids,
            building_context=context_type,
            created_at=datetime.now()
        )
        
        self.utterances[utterance_id] = utterance
        
        # Add to active session if exists
        if self.active_session_id and self.active_session_id in self.sessions:
            self.sessions[self.active_session_id].add_utterance(utterance_id)
        
        return utterance_id
    
    def get_utterance(self, utterance_id: str) -> Optional[GraphUtterance]:
        """Get a graph utterance by ID."""
        return self.utterances.get(utterance_id)
    
    def get_utterance_egi(self, utterance_id: str) -> Optional[RelationalGraphWithCuts]:
        """Get the final EGI state of an utterance."""
        utterance = self.utterances.get(utterance_id)
        if not utterance:
            return None
        
        snapshot = self.pipeline.repository.get_egi_snapshot(utterance.final_egi_id)
        return snapshot.egi_state if snapshot else None
    
    def list_utterances(self) -> List[GraphUtterance]:
        """List all graph utterances."""
        return sorted(self.utterances.values(), key=lambda u: u.created_at, reverse=True)
    
    def analyze_utterance(self, utterance_id: str) -> Dict[str, Any]:
        """Analyze a graph utterance."""
        utterance = self.utterances.get(utterance_id)
        if not utterance:
            return {"error": "Utterance not found"}
        
        final_egi = self.get_utterance_egi(utterance_id)
        if not final_egi:
            return {"error": "Final EGI not found"}
        
        return {
            "utterance_id": utterance_id,
            "title": utterance.title,
            "description": utterance.description,
            "transformation_steps": utterance.get_step_count(),
            "building_context": utterance.building_context.value,
            "final_state": {
                "vertices": len(final_egi.V),
                "edges": len(final_egi.E),
                "cuts": len(final_egi.Cut),
                "total_elements": len(final_egi.V) + len(final_egi.E) + len(final_egi.Cut)
            },
            "complexity_growth": self._calculate_complexity_growth(utterance),
            "rule_sequence": self._get_rule_sequence(utterance)
        }
    
    def _calculate_complexity_growth(self, utterance: GraphUtterance) -> List[int]:
        """Calculate how complexity grows through the utterance."""
        complexity = [0]  # Start with empty context
        
        current_egi_id = utterance.initial_egi_id
        for step_id in utterance.transformation_steps:
            step = self.pipeline.repository.transformation_steps.get(step_id)
            if step:
                snapshot = self.pipeline.repository.get_egi_snapshot(step.target_egi_id)
                if snapshot:
                    egi = snapshot.egi_state
                    total_elements = len(egi.V) + len(egi.E) + len(egi.Cut)
                    complexity.append(total_elements)
        
        return complexity
    
    def _get_rule_sequence(self, utterance: GraphUtterance) -> List[str]:
        """Get the sequence of transformation rules used."""
        rules = []
        for step_id in utterance.transformation_steps:
            step = self.pipeline.repository.transformation_steps.get(step_id)
            if step:
                rules.append(step.rule_type.value)
        return rules


def create_basic_graph_utterances():
    """Create a collection of basic graph utterances for demonstration."""
    
    builder = SimpleGraphBuilder()
    
    print("🏗️  Simple Graph Building System")
    print("=" * 35)
    
    # Start building session
    session_id = builder.start_building_session("Basic Graph Utterances Demo")
    print(f"📁 Started building session: {session_id[:8]}...")
    
    # Define basic graph utterances
    utterances = [
        {
            "title": "Single Vertex",
            "description": "Simplest possible graph - one vertex",
            "steps": [
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v1",
                        "target_area": "sheet"
                    },
                    "justification": "Insert single vertex"
                }
            ]
        },
        {
            "title": "Two Vertices (Conjunction)",
            "description": "Two vertices expressing conjunction through spatial juxtaposition",
            "steps": [
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v1",
                        "target_area": "sheet"
                    },
                    "justification": "Insert first vertex"
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v2",
                        "target_area": "sheet"
                    },
                    "justification": "Insert second vertex for conjunction"
                }
            ]
        },
        {
            "title": "Binary Relation",
            "description": "Two vertices connected by a binary relation",
            "steps": [
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "alice",
                        "target_area": "sheet"
                    },
                    "justification": "Insert first vertex (Alice)"
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "bob",
                        "target_area": "sheet"
                    },
                    "justification": "Insert second vertex (Bob)"
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "edge",
                        "element_id": "knows",
                        "target_area": "sheet",
                        "vertex_sequence": ("alice", "bob"),
                        "relation_name": "Knows"
                    },
                    "justification": "Connect vertices with 'knows' relation"
                }
            ]
        },
        {
            "title": "Simple Negation",
            "description": "Single vertex under negation (cut)",
            "steps": [
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "v1",
                        "target_area": "sheet"
                    },
                    "justification": "Insert vertex to be negated"
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "c1",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["v1"])
                    },
                    "justification": "Insert cut around vertex for negation"
                }
            ]
        },
        {
            "title": "Negated Relation",
            "description": "Binary relation under negation",
            "steps": [
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "alice",
                        "target_area": "sheet"
                    },
                    "justification": "Insert first vertex"
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "bob",
                        "target_area": "sheet"
                    },
                    "justification": "Insert second vertex"
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "edge",
                        "element_id": "likes",
                        "target_area": "sheet",
                        "vertex_sequence": ("alice", "bob"),
                        "relation_name": "Likes"
                    },
                    "justification": "Connect vertices with 'likes' relation"
                },
                {
                    "rule_type": TransformationRuleType.INSERTION,
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "c1",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["bob", "likes"])
                    },
                    "justification": "Insert cut for negation of 'Alice likes Bob'"
                }
            ]
        }
    ]
    
    # Build each utterance
    built_utterances = []
    for utterance_def in utterances:
        utterance_id = builder.build_graph_utterance(
            title=utterance_def["title"],
            description=utterance_def["description"],
            building_steps=utterance_def["steps"]
        )
        built_utterances.append(utterance_id)
        
        # Analyze the utterance
        analysis = builder.analyze_utterance(utterance_id)
        print(f"\n🎯 {analysis['title']}")
        print(f"   Description: {analysis['description']}")
        print(f"   Steps: {analysis['transformation_steps']}")
        print(f"   Final state: {analysis['final_state']['vertices']}V, {analysis['final_state']['edges']}E, {analysis['final_state']['cuts']}C")
        print(f"   Rule sequence: {' → '.join(analysis['rule_sequence'])}")
        print(f"   Complexity growth: {analysis['complexity_growth']}")
    
    # Session summary
    session = builder.sessions[session_id]
    print(f"\n📊 Session Summary:")
    print(f"   Title: {session.title}")
    print(f"   Total utterances: {len(session.utterances)}")
    print(f"   Started: {session.started_at.strftime('%H:%M:%S')}")
    
    # Overall analysis
    total_steps = sum(builder.analyze_utterance(uid)['transformation_steps'] for uid in built_utterances)
    print(f"   Total transformation steps: {total_steps}")
    
    return builder, built_utterances


if __name__ == "__main__":
    create_basic_graph_utterances()
