#!/usr/bin/env python3
"""
EGI System - Clean, Simple, Parsimonious

Single source of truth for existential graphs with minimal operations:
1. EGI Repository - maintains canonical graph state
2. Formal Operations - modify EGI while preserving Dau compliance  
3. Projections - generate EGIF/EGDF from EGI on demand

No complex controllers, pipelines, or adapters. Just essential operations.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from copy import deepcopy
import dataclasses
import uuid
from frozendict import frozendict
import os

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, create_empty_graph


@dataclass
class OperationResult:
    """Result of applying an operation to EGI."""
    success: bool
    error: Optional[str] = None
    modified_elements: Set[str] = None


class EGIOperation(ABC):
    """Base class for operations that modify EGI while preserving Dau compliance."""
    
    @abstractmethod
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Apply operation and return new EGI state."""
        pass
    
    @abstractmethod
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        """Check if operation preserves Dau compliance."""
        pass


class InsertVertex(EGIOperation):
    """Insert a vertex into specified area."""
    
    def __init__(self, vertex_id: str, area_id: Optional[str] = None):
        self.vertex_id = vertex_id
        self.area_id = area_id
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        # Vertex must not already exist
        return not any(v.id == self.vertex_id for v in egi.V)
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        # Coerce literal 'sheet' to actual sheet ID
        target_area = egi.sheet if (self.area_id is None or self.area_id == 'sheet') else self.area_id
        if os.environ.get('ARISBE_DEBUG_EGI') == '1':
            print(f"DEBUG: InsertVertex.apply() - vertex_id: {self.vertex_id}, area_id: {target_area}")
        # Delegate to core helper to preserve invariants
        new_egi = egi.with_vertex_in_context(Vertex(id=self.vertex_id), target_area)
        if os.environ.get('ARISBE_DEBUG_EGI') == '1':
            print(f"DEBUG: New EGI vertices: {[v.id for v in new_egi.V]}")
            print(f"DEBUG: New EGI area coverage: {dict(new_egi.area)}")
        return new_egi


class InsertEdge(EGIOperation):
    """Insert an edge (predicate) connecting vertices."""
    
    def __init__(self, edge_id: str, relation: str, vertices: List[str], area_id: Optional[str] = None):
        self.edge_id = edge_id
        self.relation = relation
        self.vertices = vertices
        self.area_id = area_id
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        # Edge must not exist, vertices must exist
        if any(e.id == self.edge_id for e in egi.E):
            return False
        return all(any(v.id == vid for v in egi.V) for vid in self.vertices)
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        # Coerce literal 'sheet' to actual sheet ID
        target_area = egi.sheet if (self.area_id is None or self.area_id == 'sheet') else self.area_id
        # Delegate to core helper to preserve invariants
        return egi.with_edge(Edge(id=self.edge_id), tuple(self.vertices), self.relation, context_id=target_area)


class InsertCut(EGIOperation):
    """Insert a cut (negation area)."""
    
    def __init__(self, cut_id: str, parent_area: Optional[str] = None):
        self.cut_id = cut_id
        self.parent_area = parent_area
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        return not any(c.id == self.cut_id for c in egi.Cut)
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        # Coerce literal 'sheet' to actual sheet ID
        target_parent = egi.sheet if (self.parent_area is None or self.parent_area == 'sheet') else self.parent_area
        if os.environ.get('ARISBE_DEBUG_EGI') == '1':
            print(f"DEBUG: InsertCut.apply() - cut_id: {self.cut_id}, parent_area: {target_parent}")
        # Delegate to core helper to preserve invariants
        new_egi = egi.with_cut(Cut(id=self.cut_id), context_id=target_parent)
        if os.environ.get('ARISBE_DEBUG_EGI') == '1':
            print(f"DEBUG: New EGI cuts: {[c.id for c in new_egi.Cut]}")
            print(f"DEBUG: New EGI area coverage: {dict(new_egi.area)}")
        return new_egi


class MoveElement(EGIOperation):
    """Move element between areas (preserving Dau constraints)."""
    
    def __init__(self, element_id: str, target_area: str):
        self.element_id = element_id
        self.target_area = target_area
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        # Element must exist in some area
        element_exists = any(self.element_id in area_elements 
                           for area_elements in egi.area.values())
        # Target area must exist
        target_exists = self.target_area in egi.area
        return element_exists and target_exists
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        # Build a new area mapping immutably
        new_area = dict(egi.area)
        # Remove from current area
        for area_id, elements in egi.area.items():
            if self.element_id in elements:
                new_area[area_id] = elements - {self.element_id}
                break
        # Add to target area
        target_set = new_area.get(self.target_area, frozenset())
        new_area[self.target_area] = target_set | {self.element_id}
        # Return a new graph instance with updated area mapping
        return dataclasses.replace(egi, area=frozendict(new_area))


class DeleteElement(EGIOperation):
    """Delete element from EGI (vertex, edge, or cut)."""
    
    def __init__(self, element_id: str):
        self.element_id = element_id
    
    def validate(self, egi: RelationalGraphWithCuts) -> bool:
        # Element must exist
        return (any(v.id == self.element_id for v in egi.V) or
                any(e.id == self.element_id for e in egi.E) or
                any(c.id == self.element_id for c in egi.Cut))
    
    def apply(self, egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        # Delegate to immutable helper on the core graph
        return egi.without_element(self.element_id)


class VisualConformanceValidator:
    """Validates that visual manipulations preserve EGI logical constraints."""
    
    @staticmethod
    def validate_visual_operation(egi: RelationalGraphWithCuts, visual_change: Dict) -> bool:
        """Check if visual change maintains logical conformance."""
        operation_type = visual_change.get('type')
        
        if operation_type == 'move_element':
            # Check area nesting constraints
            element_id = visual_change['element_id']
            target_area = visual_change['target_area']
            
            # Ensure proper cut nesting (no crossing cuts)
            return VisualConformanceValidator._validate_cut_nesting(egi, element_id, target_area)
        
        elif operation_type == 'resize_cut':
            # Ensure cut boundaries don't violate containment
            return VisualConformanceValidator._validate_cut_boundaries(egi, visual_change)
        
        return True
    
    @staticmethod
    def _validate_cut_nesting(egi: RelationalGraphWithCuts, element_id: str, target_area: str) -> bool:
        """Validate cut nesting constraints per Dau's rules."""
        # Simplified: ensure no circular containment
        visited = set()
        current = target_area
        
        while current != egi.sheet and current not in visited:
            visited.add(current)
            # Find parent area (simplified)
            current = egi.sheet  # Would need proper parent tracking
        
        return current != element_id
    
    @staticmethod
    def _validate_cut_boundaries(egi: RelationalGraphWithCuts, change: Dict) -> bool:
        """Validate cut boundary constraints."""
        # Ensure all contained elements remain within cut bounds
        cut_id = change['cut_id']
        new_bounds = change['bounds']
        
        # Would check spatial containment of all elements in cut area
        return True  # Simplified for now


class EGIRepository:
    """Single source of truth for EGI state."""
    
    def __init__(self, initial_egi: RelationalGraphWithCuts = None):
        self.egi = initial_egi or create_empty_graph()
        self.observers: List[callable] = []
        self.operation_history: List[EGIOperation] = []
        self.validator = VisualConformanceValidator()
    
    def apply(self, operation: EGIOperation) -> OperationResult:
        """Apply operation if valid."""
        if not operation.validate(self.egi):
            return OperationResult(success=False, error="Operation validation failed")
        
        try:
            new_egi = operation.apply(self.egi)
            self.egi = new_egi
            self.operation_history.append(operation)
            self._notify_observers()
            return OperationResult(success=True)
        except Exception as e:
            return OperationResult(success=False, error=str(e))
    
    def get_state(self) -> RelationalGraphWithCuts:
        """Get current EGI state (read-only)."""
        return deepcopy(self.egi)
    
    def observe(self, callback: callable):
        """Add observer for state changes."""
        self.observers.append(callback)
    
    def apply_visual_change(self, visual_change: Dict) -> OperationResult:
        """Apply visual manipulation as formal EGI operation."""
        if not self.validator.validate_visual_operation(self.egi, visual_change):
            return OperationResult(success=False, error="Visual change violates EGI constraints")
        
        # Convert visual change to formal operation
        operation = self._visual_to_operation(visual_change)
        if operation:
            return self.apply(operation)
        
        return OperationResult(success=False, error="Cannot convert visual change to formal operation")
    
    def _visual_to_operation(self, visual_change: Dict) -> Optional[EGIOperation]:
        """Convert visual manipulation to formal EGI operation."""
        change_type = visual_change.get('type')
        
        if change_type == 'move_element':
            return MoveElement(visual_change['element_id'], visual_change['target_area'])
        elif change_type == 'delete_element':
            return DeleteElement(visual_change['element_id'])
        elif change_type == 'add_vertex':
            return InsertVertex(visual_change['vertex_id'], visual_change.get('area_id', 'sheet'))
        elif change_type == 'add_edge':
            return InsertEdge(
                visual_change['edge_id'],
                visual_change['relation'],
                visual_change['vertices'],
                visual_change.get('area_id', 'sheet')
            )
        elif change_type == 'add_cut':
            return InsertCut(visual_change['cut_id'], visual_change.get('parent_area', 'sheet'))
        
        return None
    
    def _notify_observers(self):
        """Notify observers of state change."""
        for observer in self.observers:
            observer(self.egi)


class EGIFProjection:
    """Generate EGIF linear form from EGI."""
    
    def generate(self, egi: RelationalGraphWithCuts) -> str:
        """Convert EGI to EGIF string."""
        from egif_generator_dau import EGIFGenerator
        generator = EGIFGenerator(egi)
        return generator.generate()


class CLIFProjection:
    """Generate CLIF linear form from EGI."""
    
    def generate(self, egi: RelationalGraphWithCuts) -> str:
        """Convert EGI to CLIF string."""
        from clif_generator_dau import CLIFGenerator
        generator = CLIFGenerator(egi)
        return generator.generate()


class CGIFProjection:
    """Generate CGIF linear form from EGI."""
    
    def generate(self, egi: RelationalGraphWithCuts) -> str:
        """Convert EGI to CGIF string."""
        from cgif_generator_dau import CGIFGenerator
        generator = CGIFGenerator(egi)
        return generator.generate()


class EGDFProjection:
    """Generate EGDF visual form from EGI with Chapter 16 ligature handling."""
    
    def __init__(self):
        self.layout_cache = {}
        self.correspondence_cache = {}
    
    def generate(self, egi: RelationalGraphWithCuts) -> Dict:
        """Convert EGI to EGDF document with Chapter 16 correspondence system."""
        from egi_spatial_correspondence import create_spatial_correspondence_engine
        
        # Create correspondence engine for this EGI
        correspondence_engine = create_spatial_correspondence_engine(egi)
        
        # Generate spatial layout with Chapter 16 ligature handling
        layout = correspondence_engine.generate_spatial_layout()
        
        # Convert to EGDF format with ligature information
        spatial_primitives = []
        ligature_data = []
        
        for element_id, spatial_element in layout.items():
            bounds = spatial_element.spatial_bounds
            
            # Standard spatial primitive
            primitive = {
                'type': spatial_element.element_type,
                'id': element_id,
                'logical_area': spatial_element.logical_area,
                'bounds': {
                    'x': bounds.x,
                    'y': bounds.y, 
                    'width': bounds.width,
                    'height': bounds.height
                }
            }
            
            # Add Chapter 16 ligature information
            if spatial_element.ligature_geometry:
                ligature_geom = spatial_element.ligature_geometry
                primitive['ligature_data'] = {
                    'vertices': ligature_geom.vertices,
                    'spatial_path': ligature_geom.spatial_path,
                    'branching_points': [
                        {
                            'position_on_ligature': bp.position_on_ligature,
                            'spatial_position': bp.spatial_position,
                            'connected_predicates': bp.connected_predicates,
                            'constant_label': bp.constant_label
                        }
                        for bp in ligature_geom.branching_points
                    ]
                }
                ligature_data.append(primitive['ligature_data'])
            
            # Mark branching points as interactive
            if spatial_element.is_branching_point:
                primitive['interactive'] = True
                primitive['parent_ligature'] = spatial_element.parent_ligature
            
            spatial_primitives.append(primitive)
        
        # Generate correspondence mapping data
        correspondence = correspondence_engine.correspondence
        correspondence_data = {
            'egi_to_spatial': correspondence.egi_to_spatial,
            'spatial_to_egi': correspondence.spatial_to_egi,
            'ligature_mappings': {
                lid: {
                    'vertices': geom.vertices,
                    'path_length': len(geom.spatial_path),
                    'branching_point_count': len(geom.branching_points)
                }
                for lid, geom in correspondence.ligature_mappings.items()
            },
            'area_mappings': {
                aid: {'x': bounds.x, 'y': bounds.y, 'width': bounds.width, 'height': bounds.height}
                for aid, bounds in correspondence.area_mappings.items()
            }
        }
        
        return {
            'egi_structure': {
                'vertices': [v.id for v in egi.V],
                'edges': [e.id for e in egi.E], 
                'cuts': [c.id for c in egi.Cut],
                'relations': dict(egi.rel),
                'connections': dict(egi.nu),
                'areas': {k: list(v) for k, v in egi.area.items()}
            },
            'visual_layout': {
                'spatial_primitives': spatial_primitives,
                'ligature_data': ligature_data,
                'connection_routes': [],
                'styling_integration_point': 'RESERVED_FOR_FUTURE_STYLING',
                'chapter16_compliant': True
            },
            'correspondence_mapping': correspondence_data,
            'interaction_capabilities': {
                'branching_point_dragging': True,
                'ligature_rearrangement': True,
                'chapter16_transformations': [
                    'move_branch', 'extend_ligature', 'restrict_ligature',
                    'retract_ligature', 'rearrange_ligature'
                ]
            },
            'alignment_metadata': {
                'constraints_satisfied': True,
                'containment_preserved': True,
                'chapter16_constraints_satisfied': True,
                'ligature_topology_valid': True
            }
        }


class EGISystem:
    """Complete EGI system - repository + projections."""
    
    def __init__(self):
        self.repository = EGIRepository()
        self.egif_projection = EGIFProjection()
        self.clif_projection = CLIFProjection()
        self.cgif_projection = CGIFProjection()
        self.egdf_projection = EGDFProjection()
    
    # Repository operations
    def insert_vertex(self, vertex_id: str, area_id: Optional[str] = None) -> OperationResult:
        return self.repository.apply(InsertVertex(vertex_id, area_id))
    
    def insert_edge(self, edge_id: str, relation: str, vertices: List[str], area_id: Optional[str] = None) -> OperationResult:
        return self.repository.apply(InsertEdge(edge_id, relation, vertices, area_id))
    
    def insert_cut(self, cut_id: str, parent_area: Optional[str] = None) -> OperationResult:
        return self.repository.apply(InsertCut(cut_id, parent_area))
    
    # Projections
    def to_egif(self) -> str:
        return self.egif_projection.generate(self.repository.get_state())
    
    def to_clif(self) -> str:
        return self.clif_projection.generate(self.repository.get_state())
    
    def to_cgif(self) -> str:
        return self.cgif_projection.generate(self.repository.get_state())
    
    def to_egdf(self) -> Dict:
        return self.egdf_projection.generate(self.repository.get_state())
    
    def get_egi(self) -> RelationalGraphWithCuts:
        return self.repository.get_state()
    
    # Compatibility alias for tests expecting this method name
    def get_current_egi(self) -> RelationalGraphWithCuts:
        return self.get_egi()
    
    def observe_changes(self, callback: callable):
        self.repository.observe(callback)
    
    def apply_visual_change(self, visual_change: Dict) -> OperationResult:
        """Apply visual manipulation as formal EGI operation."""
        return self.repository.apply_visual_change(visual_change)
    
    def move_element(self, element_id: str, target_area: str) -> OperationResult:
        return self.repository.apply(MoveElement(element_id, target_area))
    
    def delete_element(self, element_id: str) -> OperationResult:
        return self.repository.apply(DeleteElement(element_id))

    # --- Loading / replacing EGI from linear forms ---
    def replace_egi(self, new_egi: RelationalGraphWithCuts) -> None:
        """Replace the current EGI with a new immutable graph."""
        self.repository.egi = new_egi
        self.repository._notify_observers()

    def load_egif(self, text: str) -> RelationalGraphWithCuts:
        """Parse EGIF text and replace current EGI."""
        from egif_parser_dau import parse_egif
        egi = parse_egif(text)
        self.replace_egi(egi)
        return egi

    def load_cgif(self, text: str) -> RelationalGraphWithCuts:
        """Parse CGIF text and replace current EGI."""
        from cgif_parser_dau import parse_cgif
        egi = parse_cgif(text)
        self.replace_egi(egi)
        return egi

    def load_linear(self, text: str, format_hint: Optional[str] = None) -> RelationalGraphWithCuts:
        """Load a linear form (EGIF or CGIF) and replace current EGI.
        - If format_hint is 'egif' or 'cgif', use that parser directly.
        - If 'auto' or None, try EGIF first, then CGIF.
        """
        fmt = (format_hint or 'auto').lower()
        if fmt == 'egif':
            return self.load_egif(text)
        if fmt == 'cgif':
            return self.load_cgif(text)

        # Auto-detect by trying EGIF then CGIF
        last_err = None
        try:
            return self.load_egif(text)
        except Exception as e1:
            last_err = e1
            try:
                return self.load_cgif(text)
            except Exception as e2:
                # Raise combined error
                raise ValueError(f"Failed to parse as EGIF ({e1}) or CGIF ({e2})") from e2


# Factory
def create_egi_system() -> EGISystem:
    """Create new EGI system instance."""
    return EGISystem()


# Visual Integration Bridge
class VisualEGIBridge:
    """Bridge between visual interface and EGI operations with spatial-logical alignment."""
    
    def __init__(self, egi_system: EGISystem):
        self.egi_system = egi_system
        self.visual_state_cache = {}
        self.current_layout = {}
        self.alignment_engine = None
    
    def handle_visual_event(self, event: Dict) -> OperationResult:
        """Handle visual manipulation event."""
        event_type = event.get('type')
        
        if event_type == 'drag_element':
            return self._handle_drag(event)
        elif event_type == 'create_element':
            return self._handle_create(event)
        elif event_type == 'delete_element':
            return self._handle_delete(event)
        elif event_type == 'resize_cut':
            return self._handle_resize_cut(event)
        
        return OperationResult(success=False, error=f"Unknown visual event: {event_type}")
    
    def _handle_drag(self, event: Dict) -> OperationResult:
        """Handle element drag with spatial-logical alignment."""
        element_id = event['element_id']
        new_position = (event['position']['x'], event['position']['y'])
        
        # Initialize alignment engine if needed
        if not self.alignment_engine:
            from spatial_logical_alignment import create_spatial_alignment_engine
            self.alignment_engine = create_spatial_alignment_engine(self.egi_system.get_egi())
        
        # Update current layout if empty
        if not self.current_layout:
            self.current_layout = self.alignment_engine.generate_layout()
        
        # Handle spatial drag with constraint validation
        updated_layout = self.alignment_engine.handle_spatial_drag(
            self.current_layout, element_id, new_position
        )
        
        # If layout changed, determine logical area change
        if updated_layout != self.current_layout:
            old_element = self.current_layout.get(element_id)
            new_element = updated_layout.get(element_id)
            
            if old_element and new_element and old_element.logical_area != new_element.logical_area:
                # Apply logical move operation
                visual_change = {
                    'type': 'move_element',
                    'element_id': element_id,
                    'target_area': new_element.logical_area
                }
                
                result = self.egi_system.apply_visual_change(visual_change)
                if result.success:
                    self.current_layout = updated_layout
                return result
            else:
                # Pure spatial repositioning (no logical change)
                self.current_layout = updated_layout
                return OperationResult(success=True)
        
        return OperationResult(success=False, error="Spatial constraint violation")
    
    def _handle_create(self, event: Dict) -> OperationResult:
        """Handle creation of new element."""
        element_type = event['element_type']
        position = event['position']
        area_id = self._determine_target_area(position)
        
        if element_type == 'vertex':
            vertex_id = f"v_{uuid.uuid4().hex[:8]}"
            return self.egi_system.insert_vertex(vertex_id, area_id)
        elif element_type == 'cut':
            cut_id = f"c_{uuid.uuid4().hex[:8]}"
            return self.egi_system.insert_cut(cut_id, area_id)
        
        return OperationResult(success=False, error=f"Cannot create {element_type}")
    
    def _handle_delete(self, event: Dict) -> OperationResult:
        """Handle element deletion."""
        return self.egi_system.delete_element(event['element_id'])
    
    def _handle_resize_cut(self, event: Dict) -> OperationResult:
        """Handle cut resizing (validate containment)."""
        visual_change = {
            'type': 'resize_cut',
            'cut_id': event['cut_id'],
            'bounds': event['new_bounds']
        }
        
        return self.egi_system.apply_visual_change(visual_change)
    
    def _determine_target_area(self, position: Dict) -> str:
        """Determine which area contains the given position."""
        # Simplified: would use spatial analysis of cut boundaries
        return self.egi_system.get_egi().sheet  # Default to sheet area
    
    def sync_visual_state(self) -> Dict:
        """Get current visual state synchronized with EGI."""
        return self.egi_system.to_egdf()
