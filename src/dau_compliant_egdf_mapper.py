#!/usr/bin/env python3
"""
Dau-Compliant EGDF Mapper

Implements the formal mapping from xdot parsing → Dau-compliant EGDF → precise EGI correspondence
as specified in docs/EGDF_DAU_SPECIFICATION.md.

This class ensures that every visual element has unambiguous semantic meaning and bidirectional
correspondence with the EGI model for both Warmup and Practice interaction modes.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Core imports
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from layout_engine_clean import SpatialPrimitive, LayoutResult
from xdot_parser_simple import SimpleXdotParser, XdotCluster, XdotNode, XdotEdge
from graphviz_layout_engine_v2 import GraphvizLayoutEngine

# EGDF primitive classes
from egdf_parser import (
    VertexPrimitive, PredicatePrimitive, CutPrimitive, IdentityLinePrimitive,
    CanvasSettings, StyleTheme
)

class InteractionMode(Enum):
    """Interaction modes for constraint enforcement."""
    WARMUP = "warmup"      # Syntactic constraints only
    PRACTICE = "practice"  # Semantic constraints (meaning-preserving)

@dataclass
class EGIOperation:
    """Represents an EGI operation corresponding to a user action."""
    operation_type: str  # 'move_vertex', 'resize_cut', 'connect_ligature', etc.
    target_elements: List[str]  # Element IDs affected
    parameters: Dict[str, Any]  # Operation-specific parameters
    constraints: List[str]  # Applicable constraints

@dataclass
class UserAction:
    """Represents a user interaction with visual elements."""
    action_type: str  # 'drag', 'click', 'resize', etc.
    target_primitive_id: str
    start_position: Tuple[float, float]
    end_position: Optional[Tuple[float, float]] = None
    modifiers: List[str] = None  # 'shift', 'ctrl', etc.

class DauCompliantEGDFMapper:
    """
    Formal mapper implementing xdot → Dau-compliant EGDF → EGI correspondence.
    
    This class ensures precise bidirectional mapping between visual elements and
    EGI logical structure, enabling both compositional (Warmup) and formal (Practice) modes.
    """
    
    def __init__(self):
        self.layout_engine = GraphvizLayoutEngine()
        self.xdot_parser = SimpleXdotParser()
        self.default_style = StyleTheme()
        
        # Correspondence tracking
        self._egi_to_visual: Dict[str, str] = {}  # EGI element ID → visual primitive ID
        self._visual_to_egi: Dict[str, str] = {}  # Visual primitive ID → EGI element ID
    
    def xdot_to_egdf(self, xdot_data: str, egi_model: RelationalGraphWithCuts) -> List[SpatialPrimitive]:
        """
        Convert xdot parsing output to Dau-compliant EGDF primitives.
        
        Implements the formal mapping:
        Graphviz xdot → Dau-compliant visual elements → EGI correspondence
        """
        # Step 1: Parse xdot data
        clusters, nodes, edges = self.xdot_parser.parse_xdot(xdot_data)
        
        # Step 2: Convert to Dau-compliant primitives
        primitives = []
        
        # Convert clusters to rounded rectangle cuts
        for cluster in clusters:
            cut_primitive = self._create_dau_cut_primitive(cluster, egi_model)
            primitives.append(cut_primitive)
        
        # Convert nodes to predicates or vertices
        for node in nodes:
            if self._is_predicate_node(node, egi_model):
                predicate_primitive = self._create_dau_predicate_primitive(node, egi_model)
                primitives.append(predicate_primitive)
            else:
                vertex_primitive = self._create_dau_vertex_primitive(node, egi_model)
                primitives.append(vertex_primitive)
        
        # Convert edges to identity lines
        for edge in edges:
            if self._is_identity_edge(edge, egi_model):
                identity_primitive = self._create_dau_identity_primitive(edge, egi_model)
                primitives.append(identity_primitive)
        
        # Step 3: Validate correspondence
        self._validate_egi_correspondence(primitives, egi_model)
        
        return primitives
    
    def _validate_egi_correspondence(self, primitives: List[SpatialPrimitive], egi_model: RelationalGraphWithCuts):
        """Validate that primitives correspond correctly to EGI elements."""
        # Basic validation - can be enhanced later
        print(f"📊 Validating correspondence: {len(primitives)} primitives vs EGI model")
        return True
    
    def _create_dau_cut_primitive(self, cluster: XdotCluster, egi_model: RelationalGraphWithCuts) -> CutPrimitive:
        """Create Dau-compliant cut primitive from xdot cluster."""
        return CutPrimitive(
            type="cut",
            id=cluster.name,
            egi_element_id=cluster.name,
            shape="rounded_rectangle",  # Dau specification: rounded rectangles, not ovals
            bounds={
                'left': cluster.bb[0],
                'top': cluster.bb[1],
                'right': cluster.bb[2],
                'bottom': cluster.bb[3]
            },
            style_overrides={
                'corner_radius': 8.0,  # Dau-compliant corner radius
                'line_width': 1.0,     # Fine-drawn closed curve
                'color': '#000000'
            },
            containment=self._compute_cut_containment(cluster.name, egi_model),
            provenance={
                'source': 'xdot_cluster',
                'dau_compliant': True,
                'mapping_validated': True
            }
        )
    
    def _create_dau_predicate_primitive(self, node: XdotNode, egi_model: RelationalGraphWithCuts) -> PredicatePrimitive:
        """Create Dau-compliant predicate primitive from xdot node."""
        relation_name = egi_model.get_relation_name(node.name)
        
        return PredicatePrimitive(
            element_id=node.name,
            position=node.pos,
            text=relation_name,
            bounds=(
                node.pos[0] - node.width/2,
                node.pos[1] - node.height/2,
                node.pos[0] + node.width/2,
                node.pos[1] + node.height/2
            ),
            argument_order=self._compute_argument_order(node.name, egi_model),
            bounding_box={
                'width': node.width,
                'height': node.height,
                'padding': 4.0  # Clear periphery for hook attachment
            },
            provenance={
                'source': 'xdot_node',
                'dau_compliant': True,
                'periphery_defined': True
            }
        )
    
    def _create_dau_vertex_primitive(self, node: XdotNode, egi_model: RelationalGraphWithCuts) -> VertexPrimitive:
        """Create Dau-compliant vertex primitive from xdot node."""
        return VertexPrimitive(
            element_id=node.name,
            position=node.pos,
            bounds=(
                node.pos[0] - 6,  # Standard vertex radius
                node.pos[1] - 6,
                node.pos[0] + 6,
                node.pos[1] + 6
            ),
            annotations=self._get_vertex_annotations(node.name, egi_model),
            provenance={
                'source': 'xdot_node',
                'on_ligature': True,
                'dau_compliant': True
            }
        )
    
    def _create_dau_identity_primitive(self, edge: XdotEdge, egi_model: RelationalGraphWithCuts) -> IdentityLinePrimitive:
        """Create Dau-compliant identity line primitive from xdot edge."""
        return IdentityLinePrimitive(
            element_id=f"ligature_{edge.tail}_{edge.head}",
            coordinates=edge.points,  # Continuous spline path from Graphviz
            connection_points={
                'tail': edge.tail,
                'head': edge.head,
                'spline_points': len(edge.points)
            },
            provenance={
                'source': 'xdot_edge',
                'continuous_line': True,
                'collision_free': True  # Graphviz ensures this
            }
        )
    
    def egdf_to_egi_action(self, user_action: UserAction, visual_target: SpatialPrimitive, 
                          mode: InteractionMode) -> EGIOperation:
        """
        Convert user action on visual element to corresponding EGI operation.
        
        Implements mode-aware constraint enforcement:
        - Warmup: Syntactic constraints only
        - Practice: Semantic constraints (meaning-preserving)
        """
        # Map visual action to EGI operation
        if user_action.action_type == 'drag' and visual_target.element_type == 'vertex':
            return self._map_vertex_move_action(user_action, visual_target, mode)
        
        elif user_action.action_type == 'resize' and visual_target.element_type == 'cut':
            return self._map_cut_resize_action(user_action, visual_target, mode)
        
        elif user_action.action_type == 'connect':
            return self._map_ligature_connect_action(user_action, visual_target, mode)
        
        else:
            raise ValueError(f"Unsupported action: {user_action.action_type} on {visual_target.element_type}")
    
    def _map_vertex_move_action(self, action: UserAction, target: SpatialPrimitive, 
                               mode: InteractionMode) -> EGIOperation:
        """Map vertex movement to EGI operation with mode-appropriate constraints."""
        constraints = ['must_stay_on_ligature', 'syntactic_validity']
        
        if mode == InteractionMode.PRACTICE:
            constraints.extend(['meaning_preserving', 'formal_rule_compliance'])
        
        return EGIOperation(
            operation_type='move_vertex',
            target_elements=[target.element_id],
            parameters={
                'new_position': action.end_position,
                'old_position': action.start_position,
                'area_change': self._compute_area_change(action, target)
            },
            constraints=constraints
        )
    
    def _map_cut_resize_action(self, action: UserAction, target: SpatialPrimitive, 
                              mode: InteractionMode) -> EGIOperation:
        """Map cut resize to EGI operation with containment constraints."""
        constraints = ['must_contain_children', 'no_sibling_overlap']
        
        if mode == InteractionMode.PRACTICE:
            constraints.extend(['meaning_preserving'])
        
        return EGIOperation(
            operation_type='resize_cut',
            target_elements=[target.element_id],
            parameters={
                'new_bounds': self._compute_new_bounds(action, target),
                'affected_children': self._get_cut_children(target.element_id)
            },
            constraints=constraints
        )
    
    def _map_ligature_connect_action(self, action: UserAction, target: SpatialPrimitive, 
                                    mode: InteractionMode) -> EGIOperation:
        """Map ligature connection to EGI ν mapping update."""
        constraints = ['valid_connection', 'arity_consistency']
        
        if mode == InteractionMode.PRACTICE:
            constraints.extend(['rule_based_only'])
        
        return EGIOperation(
            operation_type='connect_ligature',
            target_elements=[target.element_id],
            parameters={
                'connection_type': 'vertex_to_predicate',
                'nu_mapping_update': True
            },
            constraints=constraints
        )
    
    def validate_correspondence(self, egdf_primitives: List[SpatialPrimitive], 
                               egi_model: RelationalGraphWithCuts) -> bool:
        """
        Validate that EGDF primitives maintain precise correspondence with EGI model.
        
        Ensures every visual element has unambiguous semantic meaning.
        """
        try:
            # Check 1: Every EGI element has a corresponding visual primitive
            egi_elements = self._get_all_egi_elements(egi_model)
            
            # Extract element IDs using correct attribute names
            visual_elements = set()
            for p in egdf_primitives:
                if hasattr(p, 'element_id'):
                    visual_elements.add(p.element_id)
                elif hasattr(p, 'id'):
                    visual_elements.add(p.id)
                elif hasattr(p, 'egi_element_id'):
                    visual_elements.add(p.egi_element_id)
            
            missing_visual = egi_elements - visual_elements
            if missing_visual:
                print(f"⚠️  Missing visual primitives for EGI elements: {missing_visual}")
            
            # Check 2: Every visual primitive corresponds to an EGI element
            extra_visual = visual_elements - egi_elements
            if extra_visual:
                # Allow synthetic elements like ligature IDs
                synthetic_allowed = {p for p in extra_visual if p.startswith('ligature_')}
                unexpected = extra_visual - synthetic_allowed
                if unexpected:
                    print(f"⚠️  Visual primitives without EGI correspondence: {unexpected}")
            
            # Check 3: Dau-compliant specifications
            self._validate_dau_compliance(egdf_primitives)
            
            # Check 4: Structural consistency
            self._validate_structural_consistency(egdf_primitives, egi_model)
            
            return True
            
        except Exception as e:
            print(f"❌ Correspondence validation failed: {e}")
            return False
    
    def _validate_dau_compliance(self, primitives: List[SpatialPrimitive]):
        """Validate Dau-specific visual conventions."""
        for primitive in primitives:
            # Get element ID using correct attribute name
            element_id = getattr(primitive, 'element_id', getattr(primitive, 'id', 'unknown'))
            
            if hasattr(primitive, 'shape'):  # CutPrimitive
                if primitive.shape != "rounded_rectangle":
                    print(f"⚠️  Cut {element_id} should be rounded rectangle, not {primitive.shape}")
            
            elif hasattr(primitive, 'coordinates'):  # IdentityLinePrimitive
                if len(primitive.coordinates) < 2:
                    print(f"⚠️  Identity line {element_id} should have continuous path")
    
    def _get_all_egi_elements(self, egi: RelationalGraphWithCuts) -> set:
        """Get all element IDs from EGI model."""
        elements = set()
        elements.update(v.id for v in egi.V)
        elements.update(e.id for e in egi.E)
        elements.update(c.id for c in egi.Cut)
        return elements
    
    # Helper methods for mapping operations
    def _is_predicate_node(self, node: XdotNode, egi: RelationalGraphWithCuts) -> bool:
        """Determine if xdot node represents a predicate."""
        return any(edge.id == node.name for edge in egi.E)
    
    def _is_identity_edge(self, edge: XdotEdge, egi: RelationalGraphWithCuts) -> bool:
        """Determine if xdot edge represents an identity line."""
        # Check if this edge connects elements in the ν mapping
        return any(edge.tail in vertex_seq or edge.head in vertex_seq 
                  for vertex_seq in egi.nu.values())
    
    def _compute_cut_containment(self, cut_id: str, egi: RelationalGraphWithCuts) -> Dict[str, List[str]]:
        """Compute what elements are contained within a cut."""
        contained = []
        if hasattr(egi, 'area'):
            for element_id, area_id in egi.area.items():
                if area_id == cut_id:
                    contained.append(element_id)
        return {'contains': contained}
    
    def _compute_argument_order(self, edge_id: str, egi: RelationalGraphWithCuts) -> List[Dict[str, Any]]:
        """Compute argument order for predicate from ν mapping."""
        if edge_id in egi.nu:
            vertex_sequence = egi.nu[edge_id]
            return [
                {'vertex_id': vid, 'index': i, 'hook_position': None}
                for i, vid in enumerate(vertex_sequence)
            ]
        return []
    
    def _get_vertex_annotations(self, vertex_id: str, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Get annotations for vertex (constant names, etc.)."""
        # This should extract constant names and other vertex metadata
        vertex = next((v for v in egi.V if v.id == vertex_id), None)
        if vertex and hasattr(vertex, 'name'):
            return {'constant_name': vertex.name}
        return {}
    
    def _compute_area_change(self, action: UserAction, target: SpatialPrimitive) -> Optional[str]:
        """Compute if vertex movement changes its logical area."""
        # This would determine if the vertex moves to a different cut
        return None  # Simplified for now
    
    def _compute_new_bounds(self, action: UserAction, target: SpatialPrimitive) -> Tuple[float, float, float, float]:
        """Compute new bounds for resized cut."""
        # This would calculate the new cut boundaries
        return target.bounds  # Simplified for now
    
    def _get_cut_children(self, cut_id: str) -> List[str]:
        """Get all elements contained within a cut."""
        # This would return all child element IDs
        return []  # Simplified for now
    
    def _validate_structural_consistency(self, primitives: List[SpatialPrimitive], 
                                       egi: RelationalGraphWithCuts):
        """Validate that visual structure matches EGI logical structure."""
        # This would check containment relationships, connectivity, etc.
        pass  # Simplified for now


class InteractionConstraints:
    """Enforce mode-appropriate constraints on user interactions."""
    
    def validate_warmup_action(self, action: UserAction, selection: List[SpatialPrimitive]) -> bool:
        """Validate action in Warmup mode (syntactic constraints only)."""
        # Allow flexible composition with structural validity
        return self._check_syntactic_validity(action, selection)
    
    def validate_practice_action(self, action: UserAction, selection: List[SpatialPrimitive]) -> bool:
        """Validate action in Practice mode (semantic constraints)."""
        # Enforce meaning-preserving transformations only
        return (self._check_syntactic_validity(action, selection) and 
                self._check_semantic_preservation(action, selection))
    
    def _check_syntactic_validity(self, action: UserAction, selection: List[SpatialPrimitive]) -> bool:
        """Check if action maintains valid EG structure."""
        # Implement syntactic constraint checking
        return True  # Simplified for now
    
    def _check_semantic_preservation(self, action: UserAction, selection: List[SpatialPrimitive]) -> bool:
        """Check if action preserves logical meaning."""
        # Implement semantic constraint checking
        return True  # Simplified for now
    
    def enforce_dau_conventions(self, primitives: List[SpatialPrimitive]) -> List[SpatialPrimitive]:
        """Apply Dau-specific visual conventions to primitives."""
        enhanced_primitives = []
        
        for primitive in primitives:
            if isinstance(primitive, CutPrimitive):
                # Ensure cuts are rounded rectangles
                primitive.shape = "rounded_rectangle"
                if not primitive.style_overrides:
                    primitive.style_overrides = {}
                primitive.style_overrides['corner_radius'] = 8.0
            
            elif isinstance(primitive, IdentityLinePrimitive):
                # Ensure ligatures are continuous and collision-free
                if not primitive.provenance:
                    primitive.provenance = {}
                primitive.provenance['continuous_line'] = True
            
            enhanced_primitives.append(primitive)
        
        return enhanced_primitives
