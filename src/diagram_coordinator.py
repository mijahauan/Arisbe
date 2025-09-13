"""
DiagramCoordinator - Clean DTO-only version

This replaces the legacy DiagramCoordinator with a clean implementation that uses
only the EGI DTO system and eliminates all legacy schema confusion.
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid
from egi_core_dau import RelationalGraphWithCuts
from egi_dto import EGIStateDTO, VertexDTO, EdgeDTO, CutDTO, SpatialInfo

# Import other required classes
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
    """Clean DTO-only DiagramCoordinator without legacy schema confusion."""
    
    def __init__(self, scene, style_manager: StyleManager):
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
        
        print("Clean DTO-only DiagramCoordinator initialized")
    
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
    
    def load_egi_data(self, egi_data: Dict[str, Any]):
        """Load EGI data from handoff payload."""
        try:
            print(f"[DiagramCoordinator] Loading EGI data with keys: {list(egi_data.keys())}")
            
            # Clear existing state
            self.clear_all()
            
            # Load vertices
            if "V" in egi_data and egi_data["V"]:
                for vertex_data in egi_data["V"]:
                    # Handle both string IDs and dict objects
                    if isinstance(vertex_data, str):
                        vertex_id = vertex_data
                    elif isinstance(vertex_data, dict):
                        vertex_id = vertex_data.get("id", f"v_{len(self.egi_state.vertices):06d}")
                    else:
                        vertex_id = f"v_{len(self.egi_state.vertices):06d}"
                    
                    # Create vertex DTO with default position if not provided
                    vertex_dto = VertexDTO(
                        id=vertex_id,
                        spatial=SpatialInfo(x=100.0 + len(self.egi_state.vertices) * 50, y=100.0),
                        area_id="sheet",
                        radius=8.0
                    )
                    self.egi_state.vertices[vertex_id] = vertex_dto
                    self.egi_state.area_mapping["sheet"].add(vertex_id)
                    print(f"Loaded vertex: {vertex_id}")
            
            # Load edges (predicates)
            if "E" in egi_data and egi_data["E"]:
                for edge_data in egi_data["E"]:
                    # Handle both string IDs and dict objects
                    if isinstance(edge_data, str):
                        edge_id = edge_data
                    elif isinstance(edge_data, dict):
                        edge_id = edge_data.get("id", f"e_{len(self.egi_state.edges):06d}")
                    else:
                        edge_id = f"e_{len(self.egi_state.edges):06d}"
                    
                    # Get relation name from rel mapping
                    relation_name = egi_data.get("rel", {}).get(edge_id, "Unknown")
                    
                    edge_dto = EdgeDTO(
                        id=edge_id,
                        spatial=SpatialInfo(x=200.0 + len(self.egi_state.edges) * 50, y=150.0),
                        area_id="sheet",
                        relation_name=relation_name,
                        text_width=60.0,
                        text_height=25.0
                    )
                    self.egi_state.edges[edge_id] = edge_dto
                    self.egi_state.area_mapping["sheet"].add(edge_id)
                    print(f"Loaded edge: {edge_id} ({relation_name})")
            
            # Load cuts
            if "Cut" in egi_data and egi_data["Cut"]:
                for cut_data in egi_data["Cut"]:
                    # Handle both string IDs and dict objects
                    if isinstance(cut_data, str):
                        cut_id = cut_data
                    elif isinstance(cut_data, dict):
                        cut_id = cut_data.get("id", f"c_{len(self.egi_state.cuts):06d}")
                    else:
                        cut_id = f"c_{len(self.egi_state.cuts):06d}"
                    
                    cut_dto = CutDTO(
                        id=cut_id,
                        spatial=SpatialInfo(x=150.0 + len(self.egi_state.cuts) * 30, y=200.0, width=200.0, height=150.0),
                        area_id="sheet",
                        parent_cut_id=None,
                        cut_width=200.0,
                        cut_height=150.0
                    )
                    self.egi_state.cuts[cut_id] = cut_dto
                    self.egi_state.area_mapping["sheet"].add(cut_id)
                    
                    # Create area for this cut
                    cut_area_id = f"cut_{cut_id}"
                    self.egi_state.area_mapping[cut_area_id] = set()
                    print(f"Loaded cut: {cut_id}")
            
            print(f"[DiagramCoordinator] Successfully loaded EGI data: {self.get_element_count()}")
            
            # Render the loaded elements to the scene
            self._render_loaded_elements()
            
        except Exception as e:
            print(f"[DiagramCoordinator] Error loading EGI data: {e}")
            import traceback
            traceback.print_exc()
    
    def load_egi_dto(self, egi_dto: EGIStateDTO):
        """Load EGI DTO directly into the coordinator."""
        try:
            print(f"[DiagramCoordinator] Loading EGI DTO with {len(egi_dto.vertices)} vertices, {len(egi_dto.edges)} edges, {len(egi_dto.cuts)} cuts")
            
            # Clear existing state
            self.clear_all()
            
            # Set the DTO directly
            self.egi_state = egi_dto
            
            # Ensure sheet area exists in area mapping
            if self.egi_state.sheet_id not in self.egi_state.area_mapping:
                self.egi_state.area_mapping[self.egi_state.sheet_id] = set()
            
            print(f"[DiagramCoordinator] Successfully loaded EGI DTO: {self.get_element_count()}")
            
            # Render the loaded elements to the scene
            self._render_loaded_elements()
            
        except Exception as e:
            print(f"[DiagramCoordinator] Error loading EGI DTO: {e}")
            import traceback
            traceback.print_exc()
    
    def _render_loaded_elements(self):
        """Render all loaded EGI elements to the scene."""
        try:
            from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsRectItem
            from PySide6.QtGui import QBrush, QPen, QColor, QFont
            from PySide6.QtCore import Qt
            
            print(f"[DiagramCoordinator] Rendering {len(self.egi_state.vertices)} vertices, {len(self.egi_state.edges)} edges, {len(self.egi_state.cuts)} cuts")
            
            # Render vertices
            for vertex_id, vertex_dto in self.egi_state.vertices.items():
                if vertex_dto.spatial:
                    vertex_item = QGraphicsEllipseItem(-8, -8, 16, 16)
                    vertex_item.setBrush(QBrush(QColor("white")))
                    vertex_item.setPen(QPen(QColor("black"), 2))
                    vertex_item.setPos(vertex_dto.spatial.x, vertex_dto.spatial.y)
                    vertex_item.setFlags(vertex_item.GraphicsItemFlag.ItemIsMovable | 
                                       vertex_item.GraphicsItemFlag.ItemIsSelectable)
                    vertex_item.element_id = vertex_id
                    self.scene.addItem(vertex_item)
                    print(f"Rendered vertex {vertex_id} at ({vertex_dto.spatial.x}, {vertex_dto.spatial.y})")
            
            # Render edges (predicates)
            for edge_id, edge_dto in self.egi_state.edges.items():
                if edge_dto.spatial and edge_dto.relation_name:
                    edge_item = QGraphicsTextItem(edge_dto.relation_name)
                    edge_item.setPos(edge_dto.spatial.x, edge_dto.spatial.y)
                    edge_item.setFlags(edge_item.GraphicsItemFlag.ItemIsMovable | 
                                     edge_item.GraphicsItemFlag.ItemIsSelectable)
                    font = QFont("Arial", 12)
                    edge_item.setFont(font)
                    edge_item.setDefaultTextColor(QColor("black"))
                    edge_item.element_id = edge_id
                    self.scene.addItem(edge_item)
                    print(f"Rendered edge {edge_id} '{edge_dto.relation_name}' at ({edge_dto.spatial.x}, {edge_dto.spatial.y})")
            
            # Render cuts
            for cut_id, cut_dto in self.egi_state.cuts.items():
                if cut_dto.spatial:
                    cut_item = QGraphicsRectItem(0, 0, cut_dto.cut_width, cut_dto.cut_height)
                    cut_item.setPos(cut_dto.spatial.x, cut_dto.spatial.y)
                    cut_item.setBrush(QBrush(QColor(255, 255, 255, 0)))  # Transparent
                    cut_item.setPen(QPen(QColor("black"), 2))
                    cut_item.setFlags(cut_item.GraphicsItemFlag.ItemIsMovable | 
                                    cut_item.GraphicsItemFlag.ItemIsSelectable)
                    cut_item.element_id = cut_id
                    self.scene.addItem(cut_item)
                    print(f"Rendered cut {cut_id} at ({cut_dto.spatial.x}, {cut_dto.spatial.y})")
            
            print(f"[DiagramCoordinator] Finished rendering all elements")
            
        except Exception as e:
            print(f"[DiagramCoordinator] Error rendering elements: {e}")
            import traceback
            traceback.print_exc()
    
    # --- Legacy Compatibility Methods (minimal implementation) ---
    
    def get_current_drawing_schema(self):
        """Legacy compatibility - returns DTO data in old format."""
        print("WARNING: get_current_drawing_schema called - this is legacy compatibility")
        return {
            "vertices": list(self.egi_state.vertices.values()),
            "predicates": list(self.egi_state.edges.values()),
            "cuts": list(self.egi_state.cuts.values()),
            "ligatures": list(self.egi_state.ligatures.values())
        }


# For backward compatibility, export the Point2D class
__all__ = ['DiagramCoordinator', 'Point2D', 'ValidationMode']

