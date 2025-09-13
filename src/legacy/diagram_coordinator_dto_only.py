"""
DiagramCoordinator - DTO-only version without legacy schema confusion.

This is a cleaned up version that uses only the EGI DTO system and eliminates
the legacy current_drawing_schema that was causing data format confusion.
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid
from egi_dto import EGIStateDTO, VertexDTO, EdgeDTO, CutDTO, SpatialInfo

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsScene
from styling.style_manager import StyleManager


@dataclass
class Point2D:
    """Simple 2D point for coordinate handling."""
    x: float
    y: float
    
    def __str__(self):
        return f"Point2D(x={self.x}, y={self.y})"


class ValidationMode(Enum):
    """Validation modes for the coordinator."""
    COMPOSITION = "composition"  # Syntactic constraints only
    PRACTICE = "practice"       # Syntactic + semantic constraints


class DiagramCoordinator:
    """DTO-only DiagramCoordinator without legacy schema confusion."""
    
    def __init__(self, scene: QGraphicsScene, style_manager: StyleManager):
        self.scene = scene
        self.style_manager = style_manager
        self.validation_mode = ValidationMode.COMPOSITION
        
        # EGI-centered state as single source of truth
        self.egi_state: EGIStateDTO = EGIStateDTO(
            vertices={},
            edges={},
            cuts={},
            ligatures={},
            nu_mapping={},
            area_mapping={"sheet": set()}
        )
    
    # --- Core Element Creation Methods ---
    
    def create_vertex(self, position: Point2D, area_id: str = "sheet") -> Optional[str]:
        """Create vertex using DTO system."""
        try:
            # Generate unique ID based on existing vertices
            vertex_id = f"v_{len(self.egi_state.vertices):06d}"
            
            # Create DTO
            vertex_dto = VertexDTO(
                id=vertex_id,
                spatial=SpatialInfo(x=position.x, y=position.y),
                area_id=area_id,
                radius=8.0
            )
            
            # Add to EGI state
            self.egi_state.vertices[vertex_id] = vertex_dto
            
            # Update area mapping
            if area_id not in self.egi_state.area_mapping:
                self.egi_state.area_mapping[area_id] = set()
            self.egi_state.area_mapping[area_id].add(vertex_id)
            
            print(f"Created vertex DTO: {vertex_id} at ({position.x}, {position.y}) in {area_id}")
            return vertex_id
            
        except Exception as e:
            print(f"Error creating vertex: {e}")
            return None
    
    def create_predicate(self, text: str, position: Point2D, area_id: str = "sheet") -> Optional[str]:
        """Create predicate (edge) using DTO system."""
        try:
            # Generate unique ID based on existing edges
            edge_id = f"e_{len(self.egi_state.edges):06d}"
            
            # Create DTO
            edge_dto = EdgeDTO(
                id=edge_id,
                spatial=SpatialInfo(x=position.x, y=position.y),
                area_id=area_id,
                relation_name=text,
                text_width=60.0,
                text_height=25.0
            )
            
            # Add to EGI state
            self.egi_state.edges[edge_id] = edge_dto
            
            # Update area mapping
            if area_id not in self.egi_state.area_mapping:
                self.egi_state.area_mapping[area_id] = set()
            self.egi_state.area_mapping[area_id].add(edge_id)
            
            print(f"Created edge DTO: {edge_id} '{text}' at ({position.x}, {position.y}) in {area_id}")
            return edge_id
            
        except Exception as e:
            print(f"Error creating predicate: {e}")
            return None
    
    def create_cut(self, x: float, y: float, width: float, height: float, 
                   parent_area_id: str = "sheet") -> Optional[str]:
        """Create cut using DTO system."""
        try:
            # Generate unique ID based on existing cuts
            cut_id = f"c_{len(self.egi_state.cuts):06d}"
            
            # Create DTO
            cut_dto = CutDTO(
                id=cut_id,
                spatial=SpatialInfo(x=x, y=y, width=width, height=height),
                area_id=parent_area_id,
                parent_cut_id=parent_area_id if parent_area_id != "sheet" else None,
                cut_width=width,
                cut_height=height
            )
            
            # Add to EGI state
            self.egi_state.cuts[cut_id] = cut_dto
            
            # Update area mapping
            if parent_area_id not in self.egi_state.area_mapping:
                self.egi_state.area_mapping[parent_area_id] = set()
            self.egi_state.area_mapping[parent_area_id].add(cut_id)
            
            # Create new area for this cut
            cut_area_id = f"cut_{cut_id}"
            self.egi_state.area_mapping[cut_area_id] = set()
            
            print(f"Created cut DTO: {cut_id} at ({x}, {y}) size ({width}x{height}) in {parent_area_id}")
            return cut_id
            
        except Exception as e:
            print(f"Error creating cut: {e}")
            return None
    
    # --- Position Update Methods ---
    
    def update_vertex_position(self, vertex_id: str, position: Point2D):
        """Update vertex position in DTO."""
        if vertex_id in self.egi_state.vertices:
            vertex_dto = self.egi_state.vertices[vertex_id]
            if vertex_dto.spatial:
                vertex_dto.spatial.x = position.x
                vertex_dto.spatial.y = position.y
                print(f"Updated vertex {vertex_id} position to ({position.x}, {position.y})")
    
    def update_predicate_position(self, edge_id: str, position: Point2D):
        """Update predicate position in DTO."""
        if edge_id in self.egi_state.edges:
            edge_dto = self.egi_state.edges[edge_id]
            if edge_dto.spatial:
                edge_dto.spatial.x = position.x
                edge_dto.spatial.y = position.y
                print(f"Updated edge {edge_id} position to ({position.x}, {position.y})")
    
    def update_cut_position(self, cut_id: str, x: float, y: float):
        """Update cut position in DTO."""
        if cut_id in self.egi_state.cuts:
            cut_dto = self.egi_state.cuts[cut_id]
            if cut_dto.spatial:
                cut_dto.spatial.x = x
                cut_dto.spatial.y = y
                print(f"Updated cut {cut_id} position to ({x}, {y})")
    
    # --- Utility Methods ---
    
    def get_all_elements_in_area(self, area_id: str) -> List[str]:
        """Get all element IDs in a specific area."""
        return list(self.egi_state.area_mapping.get(area_id, set()))
    
    def get_element_count(self) -> Dict[str, int]:
        """Get count of each element type."""
        return {
            "vertices": len(self.egi_state.vertices),
            "edges": len(self.egi_state.edges),
            "cuts": len(self.egi_state.cuts),
            "ligatures": len(self.egi_state.ligatures)
        }
    
    def clear_all(self):
        """Clear all elements from the diagram."""
        self.egi_state = EGIStateDTO(
            vertices={},
            edges={},
            cuts={},
            ligatures={},
            nu_mapping={},
            area_mapping={"sheet": set()}
        )
        print("Cleared all diagram elements")


# Example usage
if __name__ == "__main__":
    print("DTO-only DiagramCoordinator")
    print("Features:")
    print("- Uses only EGI DTO system")
    print("- No legacy schema confusion")
    print("- Clean, consistent data structures")
    print("- Proper type safety with dataclasses")

