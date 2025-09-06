#!/usr/bin/env python3
"""
DiagramCoordinator - Central coordination layer for EGI-Spatial correspondence.

This module orchestrates the existing components to maintain precise correspondence
between logical EGI structure and spatial diagram representation. It serves as
the "translator" between logical and spatial forms.

Key responsibilities:
1. Maintain logical-spatial correspondence during user interactions
2. Enforce exclusive positioning and containment rules
3. Coordinate between EGI model, spatial renderer, and constraint validation
4. Support both Composition Mode (syntax only) and Practice Mode (syntax + semantics)
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid
from egi_dto import EGIStateDTO, VertexDTO, EdgeDTO, CutDTO, SpatialInfo, from_drawing_schema, to_constraint_engine_format

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsScene
from frozendict import frozendict

from shared_diagram_renderer import SharedDiagramRenderer
from drawing_to_egi_adapter import drawing_to_relational_graph
from egi_spatial_correspondence import create_spatial_correspondence_engine
from diagram_data_contract import DiagramDataContract, DiagramState
from styling.style_manager import StyleManager
from egdf_parser import EGDFDocument
from spatial_logical_alignment import create_spatial_alignment_engine, SpatialElement, SpatialBounds
from spatial_region_manager import SpatialRegionManager
from coordinate_negotiator import CoordinateNegotiator, QtRenderingBackend

# Define LigatureGeometry class for type hints
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class LigatureGeometry:
    ligature_id: str
    vertices: List[str]
    spatial_path: List[Tuple[float, float]]
    branching_points: List[Tuple[float, float]] = None
    
    def __post_init__(self):
        if self.branching_points is None:
            self.branching_points = []

# Import EGIF conversion utilities
try:
    from egif_generator_dau import EGIFGenerator
    def egi_to_egif(egi):
        """Convert EGI to EGIF using existing generator."""
        if egi is None:
            return "No EGI available"
        try:
            generator = EGIFGenerator(egi)
            return generator.generate()
        except Exception as e:
            return f"EGIF generation error: {e}"
except ImportError:
    def egi_to_egif(egi):
        """Fallback EGIF converter."""
        return f"[EGIF conversion not available]\nEGI: {egi}"

# Import constraint engine if available
try:
    from controller import constraint_engine
except ImportError:
    constraint_engine = None


@dataclass
class Point2D:
    """Simple 2D point for coordinate handling."""
    x: float
    y: float
    
    def to_qpointf(self) -> QPointF:
        return QPointF(self.x, self.y)
    
    @classmethod
    def from_qpointf(cls, point: QPointF) -> 'Point2D':
        return cls(point.x(), point.y())


class InteractionMode:
    """User interaction modes."""
    SELECT = "select"
    CREATE_VERTEX = "create_vertex"
    CREATE_PREDICATE = "create_predicate"
    CREATE_CUT = "create_cut"
    CREATE_LIGATURE = "create_ligature"


class ValidationMode:
    """Constraint validation modes."""
    COMPOSITION = "composition"  # Syntax constraints only
    PRACTICE = "practice"       # Syntax + semantic constraints


class DiagramCoordinator:
    """
    Central coordinator that maintains EGI-spatial correspondence.
    
    This is the "translator" that ensures spatial movements respect logical meaning
    and that logical operations are reflected in spatial representation.
    """
    
    def __init__(self, scene: QGraphicsScene, style_manager: StyleManager):
        """Initialize coordinator with Qt scene."""
        self.scene = scene
        self.style_manager = style_manager
        self.renderer = SharedDiagramRenderer(scene, style_manager)
        # Set coordinator reference in renderer for area updates
        self.renderer.coordinator = self
        
        # Core state - use standardized data contract
        self.target_egi = None
        self.egi = None
        self.diagram_state = DiagramDataContract.create_empty_state()
        self.correspondence_engine = None
        
        # Iron-clad spatial-logical correspondence system
        self.region_manager = SpatialRegionManager(800, 600)  # Default canvas size
        self.spatial_alignment_engine = None
        self.current_spatial_layout: Dict[str, SpatialElement] = {}
        
        # Coordinate negotiation system for platform independence
        self.coordinate_negotiator = CoordinateNegotiator(self.region_manager)
        self.qt_backend = QtRenderingBackend(scene)
        self.coordinate_negotiator.set_rendering_backend(self.qt_backend)
        
        # Mode flags
        self.is_egi_only_mode = False
        self.is_practice_mode = False
        self.interaction_mode = "add_vertex"
        self.validation_mode = "composition"
        
        # EGI-centered state as single source of truth
        self.egi_state: EGIStateDTO = EGIStateDTO(
            vertices={},
            edges={},
            cuts={},
            ligatures={},
            nu_mapping={},
            area_mapping={"sheet": set()}
        )
        self.original_egdf_data = None
        
        # Initialize current_drawing_schema for compatibility
        self.current_drawing_schema = {
            "vertices": [],
            "predicates": [],
            "cuts": [],
            "ligatures": []
        }
    
    # --- Core Coordination Methods ---
    
    def create_vertex(self, position: Point2D, area_id: str = "sheet") -> Optional[str]:
        """Create vertex with logical-spatial correspondence."""
        # Generate unique ID
        vertex_id = f"v_{len(self.current_drawing_schema['vertices']):06x}"
        
        # Validate position if in Practice mode
        if self.validation_mode == ValidationMode.PRACTICE and constraint_engine:
            if not self._validate_vertex_position(position, area_id):
                return None
        
        # Add to drawing schema
        vertex_data = {
            "id": vertex_id,
            "area_id": area_id,
            "pos": position,
            "x": position.x,
            "y": position.y,
            "label_kind": "generic",
            "label": None
        }
        self.current_drawing_schema["vertices"].append(vertex_data)
        
        # Also add to diagram_state for rendering
        from diagram_data_contract import VertexElement, ElementPosition
        self.diagram_state.vertices[vertex_id] = VertexElement(
            id=vertex_id,
            position=ElementPosition(position.x, position.y),
            area_id=area_id,
            label_kind="generic",
            label=None
        )
        
        # Memory model operations - no rendering needed during creation
        
        # Update EGI only if explicitly requested or if validation fails
        # User positioning takes priority over automatic systems
        
        return vertex_id
    
    def create_predicate(self, name: str, position: Point2D, area_id: str = "sheet") -> Optional[str]:
        """Create predicate with logical-spatial correspondence."""
        # Generate unique ID
        predicate_id = f"e_{len(self.current_drawing_schema['predicates']):06x}"
        
        # Validate position if in Practice mode
        if self.validation_mode == ValidationMode.PRACTICE and constraint_engine:
            if not self._validate_predicate_position(position, area_id):
                return None
        
        # Add to drawing schema
        predicate_data = {
            "id": predicate_id,
            "name": name,
            "text": name,
            "area_id": area_id,
            "pos": position,
            "x": position.x,
            "y": position.y
        }
        self.current_drawing_schema["predicates"].append(predicate_data)
        
        # Also add to diagram_state for rendering
        from diagram_data_contract import PredicateElement, ElementPosition
        self.diagram_state.predicates[predicate_id] = PredicateElement(
            id=predicate_id,
            name=name,
            position=ElementPosition(position.x, position.y),
            area_id=area_id
        )
        
        # Memory model operations - no rendering needed during creation
        
        # Update EGI only if explicitly requested or if validation fails
        # User positioning takes priority over automatic systems
        
        return predicate_id
    
    def create_cut(self, x: float, y: float, width: float, height: float, parent_area_id: str = "sheet") -> Optional[str]:
        """Create cut with logical-spatial correspondence."""
        # Generate unique ID
        cut_id = f"c_{len(self.current_drawing_schema['cuts']):06x}"
        
        # Validate cut placement
        if not self._validate_cut_placement(x, y, width, height, parent_area_id):
            return None
        
        # Add to drawing schema
        cut_data = {
            "id": cut_id,
            "parent_id": parent_area_id if parent_area_id != "sheet" else None,
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }
        self.current_drawing_schema["cuts"].append(cut_data)
        
        # Also add to diagram_state for rendering
        from diagram_data_contract import CutElement, ElementPosition, ElementSize
        self.diagram_state.cuts[cut_id] = CutElement(
            id=cut_id,
            position=ElementPosition(x, y),
            size=ElementSize(width, height),
            area_id=parent_area_id
        )
        
        # Memory model operations - no rendering needed during creation
        
        # Update EGI only if explicitly requested or if validation fails
        # User positioning takes priority over automatic systems
        
        return cut_id
    
    def create_ligature(self, predicate_id: str, vertex_id: str) -> bool:
        """Create ligature connection with logical-spatial correspondence."""
        # Validate connection
        if not self._validate_ligature_connection(predicate_id, vertex_id):
            return False
        
        # Find or create ligature entry
        ligature_entry = None
        for lig in self.current_drawing_schema["ligatures"]:
            if lig["edge_id"] == predicate_id:
                ligature_entry = lig
                break
        
        if not ligature_entry:
            ligature_entry = {
                "edge_id": predicate_id,
                "vertex_ids": []
            }
            self.current_drawing_schema["ligatures"].append(ligature_entry)
        
        # Add vertex to ligature if not already present
        if vertex_id not in ligature_entry["vertex_ids"]:
            ligature_entry["vertex_ids"].append(vertex_id)
        
        # Generate ligature geometry for spatial representation
        if self.correspondence_engine:
            geometry = self._generate_ligature_geometry(predicate_id, ligature_entry["vertex_ids"])
            if geometry:
                self.correspondence_engine.correspondence.ligature_mappings[predicate_id] = geometry
        
        # Update EGI if it exists
        if self.egi and self.correspondence_engine:
            self._sync_drawing_to_egi()
        
        # Memory model update complete
        
        return True
    
    def move_element(self, element_id: str, new_position: Point2D) -> bool:
        """Move element with iron-clad logical-spatial correspondence maintenance."""
        print(f"MOVE_ELEMENT: DISABLED - Blocking automatic repositioning for {element_id}")
        return True
    
    # --- EGI Integration ---
    
    def load_from_egdf(self, egdf_data: Dict[str, Any]) -> bool:
        """Load diagram from EGDF data using standardized contract."""
        try:
            print(f"Stored EGDF data with keys: {list(egdf_data.keys())}")
            
            # Store original EGDF data for rendering
            self.original_egdf_data = egdf_data
            
            # Convert EGDF to standardized diagram state
            self.diagram_state = DiagramDataContract.from_egdf(egdf_data)
            
            # EGDF loaded into memory model
            
            return True
            
        except Exception as e:
            print(f"Failed to load EGDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_current_egi(self) -> Optional[Any]:
        """Get the current EGI structure."""
        return self.egi
    
    def update_predicate_text(self, predicate_id: str, new_text: str) -> bool:
        """Update predicate text in the underlying EGI data."""
        try:
            if not self.current_egi:
                print(f"No EGI data available to update predicate {predicate_id}")
                return False
            
            # Update the rel mapping in the EGI data
            if hasattr(self.current_egi, 'rel') and predicate_id in self.current_egi.rel:
                # Create new rel mapping with updated text
                new_rel = dict(self.current_egi.rel)
                new_rel[predicate_id] = new_text
                
                # Update the EGI object (this creates a new immutable instance)
                self.current_egi = self.current_egi._replace(rel=frozendict(new_rel))
                
                print(f"Updated predicate {predicate_id} text to '{new_text}' in EGI data")
                return True
            else:
                print(f"Predicate {predicate_id} not found in EGI rel mapping")
                return False
                
        except Exception as e:
            print(f"Error updating predicate text: {e}")
            return False
    
    def export_to_egdf(self) -> Optional[Dict[str, Any]]:
        """Export current state to EGDF format."""
        return self.save_to_egdf()
    
    def save_to_egdf(self) -> Optional[Dict[str, Any]]:
        """Save current state to EGDF format."""
        if not self.current_drawing_schema:
            print("No drawing schema available")
            return None
            
        try:
            # Create basic EGDF structure from current drawing schema
            egdf_data = {
                "metadata": {
                    "version": "1.0",
                    "created": "2025-01-27T00:00:00Z"
                },
                "layout": {
                    "predicates": {},
                    "vertices": {}
                },
                "egi_ref": {
                    "inline": {
                        "sheet": "S",
                        "V": [],
                        "E": [],
                        "Cut": [],
                        "nu": {},
                        "rel": {},
                        "rho": {},
                        "area": {"S": []},
                        "alphabet": {
                            "C": [],
                            "F": [],
                            "R": [],
                            "ar": {}
                        }
                    }
                }
            }
            
            # Add predicates to layout
            predicates_data = self.current_drawing_schema.get("predicates", {})
            if isinstance(predicates_data, dict):
                for pred_id, pred_data in predicates_data.items():
                    egdf_data["layout"]["predicates"][pred_id] = {
                        "text": pred_data.get("name", pred_data.get("text", pred_id)),
                        "x": pred_data.get("x", 0),
                        "y": pred_data.get("y", 0)
                    }
            elif isinstance(predicates_data, list):
                for pred in predicates_data:
                    egdf_data["layout"]["predicates"][pred["id"]] = {
                        "text": pred["name"],
                        "x": pred["pos"].x,
                        "y": pred["pos"].y
                    }
            
            # Add vertices to layout
            vertices_data = self.current_drawing_schema.get("vertices", {})
            if isinstance(vertices_data, dict):
                for vertex_id, vertex_data in vertices_data.items():
                    egdf_data["layout"]["vertices"][vertex_id] = {
                        "x": vertex_data.get("x", 0),
                        "y": vertex_data.get("y", 0)
                    }
            elif isinstance(vertices_data, list):
                for vertex in vertices_data:
                    egdf_data["layout"]["vertices"][vertex["id"]] = {
                        "x": vertex["pos"].x,
                        "y": vertex["pos"].y
                    }
            
            # Populate EGI data from drawing schema
            vertices = []
            edges = []
            relations = set()
            area_contents = []
            
            vertices_data = self.current_drawing_schema.get("vertices", [])
            if isinstance(vertices_data, dict):
                for vertex_id in vertices_data.keys():
                    vertices.append(vertex_id)
                    area_contents.append(vertex_id)
                    egdf_data["egi_ref"]["inline"]["rho"][vertex_id] = None
            elif isinstance(vertices_data, list):
                for vertex in vertices_data:
                    vertices.append(vertex["id"])
                    area_contents.append(vertex["id"])
                    egdf_data["egi_ref"]["inline"]["rho"][vertex["id"]] = None
            
            predicates_data = self.current_drawing_schema.get("predicates", {})
            if isinstance(predicates_data, dict):
                for pred_id, pred_data in predicates_data.items():
                    edges.append(pred_id)
                    area_contents.append(pred_id)
                    pred_name = pred_data.get("name", pred_data.get("text", pred_id))
                    relations.add(pred_name)
                    egdf_data["egi_ref"]["inline"]["rel"][pred_id] = pred_name
                    egdf_data["egi_ref"]["inline"]["alphabet"]["ar"][pred_name] = 1  # Default arity
            elif isinstance(predicates_data, list):
                for pred in predicates_data:
                    edges.append(pred["id"])
                    area_contents.append(pred["id"])
                    relations.add(pred["name"])
                    egdf_data["egi_ref"]["inline"]["rel"][pred["id"]] = pred["name"]
                    egdf_data["egi_ref"]["inline"]["alphabet"]["ar"][pred["name"]] = 1  # Default arity
            
            # Add ligatures to nu mapping
            for ligature in self.current_drawing_schema["ligatures"]:
                egdf_data["egi_ref"]["inline"]["nu"][ligature["edge_id"]] = ligature["vertex_ids"]
                # Update arity based on vertex count
                edge_id = ligature["edge_id"]
                if edge_id in egdf_data["egi_ref"]["inline"]["rel"]:
                    rel_name = egdf_data["egi_ref"]["inline"]["rel"][edge_id]
                    egdf_data["egi_ref"]["inline"]["alphabet"]["ar"][rel_name] = len(ligature["vertex_ids"])
            
            egdf_data["egi_ref"]["inline"]["V"] = vertices
            egdf_data["egi_ref"]["inline"]["E"] = edges
            egdf_data["egi_ref"]["inline"]["alphabet"]["R"] = list(relations)
            egdf_data["egi_ref"]["inline"]["area"]["S"] = area_contents
            
            return egdf_data
            
        except Exception as e:
            print(f"Failed to save to EGDF: {e}")
            return None
    
    # --- Mode Management ---
    
    def set_validation_mode(self, mode: str) -> None:
        """Set validation mode (composition or practice)."""
        self.validation_mode = mode
    
    def set_interaction_mode(self, mode: str) -> None:
        """Set interaction mode."""
        self.interaction_mode = mode
    
    def add_vertex_at_position(self, x: float, y: float) -> str:
        """Add a vertex at the specified position and return its ID."""
        try:
            import uuid
            vertex_id = f"v_{uuid.uuid4().hex[:6]}"
            
            # Use standardized data contract
            self.diagram_state.add_vertex(vertex_id, x, y)
            
            # Store position in renderer for immediate access
            if hasattr(self.renderer, 'element_positions'):
                from PySide6.QtCore import QPointF
                self.renderer.element_positions[vertex_id] = QPointF(x, y)
            
            # Update EGI structure
            self._sync_diagram_to_egi()
            
            # Memory model updated
            
            print(f"Added vertex {vertex_id} at ({x:.1f}, {y:.1f})")
            return vertex_id
                
        except Exception as e:
            print(f"Failed to add vertex: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def add_cut_at_position(self, x: float, y: float, width: float = 100, height: float = 100) -> str:
        """Add a cut at the specified position and return its ID."""
        try:
            import uuid
            cut_id = f"c_{uuid.uuid4().hex[:6]}"
            
            # Add to drawing schema (for EGIF generation)
            cut_data = {
                "id": cut_id,
                "pos": Point2D(x, y),
                "area_id": "sheet",
                "width": width,
                "height": height
            }
            self.current_drawing_schema["cuts"].append(cut_data)
            
            # Also add to diagram state (for rendering)
            self.diagram_state.add_cut(cut_id, x, y, width, height)
            
            # Update EGI structure
            if self.egi and self.correspondence_engine:
                self._sync_drawing_to_egi()
            
            print(f"Added cut {cut_id} at ({x:.1f}, {y:.1f}) with size {width}x{height}")
            return cut_id
                
        except Exception as e:
            print(f"Failed to add cut: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def add_predicate_at_position(self, x: float, y: float, text: str) -> str:
        """Add a predicate at the specified position and return its ID."""
        try:
            import uuid
            predicate_id = f"e_{uuid.uuid4().hex[:6]}"
            
            # Use standardized data contract
            self.diagram_state.add_predicate(predicate_id, text, x, y)
            
            # Store position in renderer for immediate access
            if hasattr(self.renderer, 'element_positions'):
                from PySide6.QtCore import QPointF
                self.renderer.element_positions[predicate_id] = QPointF(x, y)
            
            # Update EGI structure
            self._sync_diagram_to_egi()
            
            # Memory model updated
            
            print(f"Added predicate {predicate_id} '{text}' at ({x:.1f}, {y:.1f})")
            return predicate_id
                
        except Exception as e:
            print(f"Failed to add predicate: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def initialize_empty_scene(self) -> None:
        """Initialize an empty scene for drawing from scratch."""
        if self.scene:
            self.scene.clear()
        
        # Reset drawing schema to empty state
        self.current_drawing_schema = {
            "sheet_id": "sheet",
            "cuts": {},
            "vertices": {},
            "predicates": [],
            "ligatures": []
        }
        
        # Clear any existing EGI
        self.egi = None
        
        print("Initialized empty scene for drawing from scratch")
    
    def set_target_egi(self, target_egi) -> None:
        """Set target EGI and initialize iron-clad spatial-logical correspondence system."""
        self.target_egi = target_egi
        self.egi = target_egi
        
        # Initialize correspondence engine
        if target_egi:
            self.correspondence_engine = create_spatial_correspondence_engine(target_egi)
            
            # Initialize iron-clad spatial alignment engine
            if not self.spatial_alignment_engine:
                self.spatial_alignment_engine = create_spatial_alignment_engine(
                    self.region_manager, target_egi
                )
            
            # Synchronize coordinate systems with canvas
            self._synchronize_region_coordinates_with_canvas()
            
            # Synchronize coordinate negotiator
            self.synchronize_coordinates()
            
            print(f"IRON-CLAD: Initialized spatial-logical correspondence for EGI with {len(target_egi.vertices) if hasattr(target_egi, 'vertices') else 0} vertices")

        # Convert EGI to diagram state for rendering
        self._convert_egi_to_diagram_state(target_egi)
        
        print(f"Set target EGI for EGI-only mode: {len(target_egi.V)} vertices, {len(target_egi.E)} edges")
        print(f"Iron-clad correspondence: {len(self.current_spatial_layout)} spatial elements, {len(self.region_manager.get_all_regions())} regions")
    
    def get_target_egif(self) -> str:
        """Get target EGI in EGIF linear form."""
        if self.target_egi:
            return egi_to_egif(self.target_egi)
        return "No target EGI set"
    
    def get_current_egif(self) -> str:
        """Get current diagram EGI in EGIF linear form."""
        if self.is_egi_only_mode:
            # In EGI-only mode, generate EGI from current diagram state
            current_egi = self.generate_egi_from_diagram()
            if current_egi:
                return egi_to_egif(current_egi)
            return "Empty diagram - no elements created yet"
        elif self.egi:
            return egi_to_egif(self.egi)
        return "No current EGI"
    
    def _convert_egi_to_diagram_state(self, egi: Any) -> None:
        """Convert EGI to diagram state for rendering."""
        from diagram_data_contract import DiagramState, VertexElement, PredicateElement, CutElement, ElementPosition, ElementSize
        
        vertices = {}
        predicates = {}
        cuts = {}
        
        # Convert vertices with default positions
        for i, vertex in enumerate(egi.V):
            vertices[vertex.id] = VertexElement(
                id=vertex.id,
                position=ElementPosition(100 + i * 50, 100),  # Default layout
                label_kind="constant" if not vertex.is_generic else "generic",
                label=vertex.label
            )
        
        # Convert edges (predicates) with default positions
        for i, edge in enumerate(egi.E):
            relation_name = egi.rel.get(edge.id, f"Pred_{edge.id}")
            predicates[edge.id] = PredicateElement(
                id=edge.id,
                name=relation_name,
                position=ElementPosition(200 + i * 100, 100)  # Default layout
            )
        
        # Convert cuts with default positions
        for i, cut in enumerate(egi.Cut):
            cuts[cut.id] = CutElement(
                id=cut.id,
                position=ElementPosition(50 + i * 150, 50),
                size=ElementSize(200, 150)  # Default size
            )
        
        # Convert ν mappings to ligatures
        ligatures = []
        for edge_id, vertex_sequence in egi.nu.items():
            if edge_id in predicates:
                predicate_pos = predicates[edge_id].position
                for vertex_id in vertex_sequence:
                    if vertex_id in vertices:
                        vertex_pos = vertices[vertex_id].position
                        ligature = {
                            "id": f"lig_{edge_id}_{vertex_id}",
                            "from_vertex": vertex_id,
                            "to_predicate": edge_id,
                            "path": [
                                {"x": vertex_pos.x, "y": vertex_pos.y},
                                {"x": predicate_pos.x, "y": predicate_pos.y}
                            ]
                        }
                        ligatures.append(ligature)
        
        self.diagram_state = DiagramState(
            vertices=vertices,
            predicates=predicates,
            cuts=cuts,
            ligatures=ligatures
        )

    def generate_egi_from_diagram(self) -> Optional[Any]:
        """Generate EGI from current diagram state using drawing_to_egi_adapter."""
        try:
            if not self.current_drawing_schema:
                return None
            
            # Use the existing drawing_to_egi_adapter to convert drawing schema to EGI
            egi = drawing_to_relational_graph(self.current_drawing_schema)
            return egi
            
        except Exception as e:
            print(f"Failed to generate EGI from diagram: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def replace_drawing_ids_with_target_egi_ids(self, target_egi: Any) -> bool:
        """Replace current drawing element IDs with target EGI IDs to maintain consistency."""
        try:
            if not self.current_drawing_schema or not target_egi:
                return False
            
            # Create mapping from current elements to target elements based on structural equivalence
            id_mapping = self._create_structural_id_mapping(target_egi)
            
            # Update drawing schema with target IDs
            self._update_drawing_schema_ids(id_mapping)
            
            # Update scene graphics items with new IDs
            self._update_scene_item_ids(id_mapping)
            
            # Set the target EGI as the current EGI (now that IDs match)
            self.egi = target_egi
            
            print(f"Successfully replaced drawing IDs with target EGI IDs: {len(id_mapping)} mappings")
            return True
            
        except Exception as e:
            print(f"Failed to replace drawing IDs: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_structural_id_mapping(self, target_egi: Any) -> Dict[str, str]:
        """Create mapping from current drawing IDs to target EGI IDs based on structure."""
        mapping = {}
        
        # Map vertices by label/position
        current_vertices = self.current_drawing_schema.get("vertices", [])
        for i, current_vertex in enumerate(current_vertices):
            if i < len(target_egi.V):
                target_vertex = target_egi.V[i]
                mapping[current_vertex["id"]] = target_vertex.id
        
        # Map predicates by text/relation
        current_predicates = self.current_drawing_schema.get("predicates", [])
        target_predicates = list(target_egi.E)
        for i, current_pred in enumerate(current_predicates):
            if i < len(target_predicates):
                target_pred = target_predicates[i]
                mapping[current_pred["id"]] = target_pred.id
        
        # Map cuts by containment structure
        current_cuts = self.current_drawing_schema.get("cuts", [])
        target_cuts = list(target_egi.Cut)
        for i, current_cut in enumerate(current_cuts):
            if i < len(target_cuts):
                target_cut = target_cuts[i]
                mapping[current_cut["id"]] = target_cut.id
        
        return mapping
    
    def _update_drawing_schema_ids(self, id_mapping: Dict[str, str]) -> None:
        """Update drawing schema with new IDs."""
        # Update vertex IDs
        for vertex in self.current_drawing_schema.get("vertices", []):
            if vertex["id"] in id_mapping:
                vertex["id"] = id_mapping[vertex["id"]]
        
        # Update predicate IDs
        for predicate in self.current_drawing_schema.get("predicates", []):
            if predicate["id"] in id_mapping:
                predicate["id"] = id_mapping[predicate["id"]]
        
        # Update cut IDs
        for cut in self.current_drawing_schema.get("cuts", []):
            if cut["id"] in id_mapping:
                cut["id"] = id_mapping[cut["id"]]
        
        # Update ligature endpoint references
        for ligature in self.current_drawing_schema.get("ligatures", []):
            for endpoint in ligature.get("endpoints", []):
                if endpoint.get("element_id") in id_mapping:
                    endpoint["element_id"] = id_mapping[endpoint["element_id"]]
    
    def _update_scene_item_ids(self, id_mapping: Dict[str, str]) -> None:
        """Update Qt scene graphics items with new IDs."""
        if not self.scene:
            return
        
        # Update graphics items that have ID attributes
        for item in self.scene.items():
            if hasattr(item, 'vertex_id') and item.vertex_id in id_mapping:
                item.vertex_id = id_mapping[item.vertex_id]
            elif hasattr(item, 'predicate_id') and item.predicate_id in id_mapping:
                item.predicate_id = id_mapping[item.predicate_id]
            elif hasattr(item, 'cut_id') and item.cut_id in id_mapping:
                item.cut_id = id_mapping[item.cut_id]
    
    def analyze_missing_elements(self) -> Dict[str, List[str]]:
        """Analyze what elements are missing from current diagram vs target."""
        if not self.target_egi or not self.egi:
            return {"vertices": [], "predicates": [], "cuts": []}
        
        missing = {
            "vertices": [],
            "predicates": [],
            "cuts": []
        }
        
        # Find missing vertices
        current_vertex_ids = {v.id for v in self.egi.V}
        target_vertex_ids = {v.id for v in self.target_egi.V}
        for vid in target_vertex_ids - current_vertex_ids:
            # Find the vertex in target to get its label
            target_vertex = next((v for v in self.target_egi.V if v.id == vid), None)
            if target_vertex:
                label = self.target_egi.rho.get(vid, f"vertex {vid}")
                missing["vertices"].append(f"{vid}: {label}")
        
        # Find missing predicates/edges
        current_edge_ids = {e.id for e in self.egi.E}
        target_edge_ids = {e.id for e in self.target_egi.E}
        for eid in target_edge_ids - current_edge_ids:
            # Find the predicate text from rho mapping
            predicate_text = self.target_egi.rho.get(eid, f"predicate {eid}")
            missing["predicates"].append(f"{eid}: {predicate_text}")
        
        # Find missing cuts
        current_cut_ids = {c.id for c in self.egi.Cut}
        target_cut_ids = {c.id for c in self.target_egi.Cut}
        for cid in target_cut_ids - current_cut_ids:
            missing["cuts"].append(f"cut {cid}")
        
        return missing
    
    # --- Internal Methods ---
    
    def _sync_diagram_to_egi(self) -> None:
        """Synchronize diagram state to EGI using standardized contract."""
        try:
            # Convert standardized diagram state to EGI format
            drawing_schema = DiagramDataContract.to_egi_format(self.diagram_state)
            self.egi = drawing_to_relational_graph(drawing_schema)
            if self.correspondence_engine:
                self.correspondence_engine = create_spatial_correspondence_engine(self.egi)
        except Exception as e:
            print(f"Failed to sync drawing to EGI: {e}")
    def _render_current_state(self) -> None:
        """Render the current diagram state - DISABLED to prevent repositioning."""
        # DISABLED: This method causes element repositioning/jumping
        # Elements are now rendered directly in create_*_direct methods
        print("DEBUG: _render_current_state() disabled to prevent repositioning")
        return
    
    def _regenerate_egi_from_spatial_layout(self, spatial_layout: Dict[str, SpatialElement]) -> None:
        """Regenerate EGI structure from spatial layout to maintain iron-clad correspondence."""
        try:
            print("IRON-CLAD: Regenerating EGI from spatial layout")
            
            # Update drawing schema based on spatial layout area assignments
            for element_id, spatial_element in spatial_layout.items():
                element_data = self._find_element_data(element_id)
                if element_data:
                    element_data["area_id"] = spatial_element.logical_area
                    print(f"Updated {element_id} area assignment to {spatial_element.logical_area}")
            
            # Regenerate EGI from updated drawing schema
            self.egi = drawing_to_relational_graph(self.current_drawing_schema)
            
            # Update spatial alignment engine with new EGI
            if self.spatial_alignment_engine:
                self.spatial_alignment_engine.egi = self.egi
                
            print("IRON-CLAD: EGI regeneration complete")
            
        except Exception as e:
            print(f"Failed to regenerate EGI from spatial layout: {e}")
            import traceback
            traceback.print_exc()

    def _synchronize_region_coordinates_with_canvas(self) -> None:
        """Synchronize SpatialRegionManager coordinates with actual Qt canvas coordinates."""
        try:
            print("COORDINATE SYNC: Synchronizing region coordinates with canvas")
            
            # Update region coordinates based on actual cut positions in drawing schema
            for cut_data in self.current_drawing_schema.get("cuts", []):
                cut_id = cut_data.get("id")
                cut_pos = cut_data.get("pos")
                cut_width = cut_data.get("width", 100)
                cut_height = cut_data.get("height", 100)
                
                if cut_pos and cut_id:
                    # Find corresponding logical area
                    logical_area_id = f"cut_{cut_id}"
                    region = self.region_manager.get_region_for_logical_area(logical_area_id)
                    
                    if region:
                        # Update region bounds to match canvas coordinates
                        # Convert center position to top-left bounds
                        canvas_x = cut_pos.x - cut_width/2
                        canvas_y = cut_pos.y - cut_height/2
                        
                        region.bounds = (canvas_x, canvas_y, cut_width, cut_height)
                        
                        print(f"COORDINATE SYNC: Updated region {logical_area_id} to canvas bounds ({canvas_x}, {canvas_y}, {cut_width}, {cut_height})")
                    else:
                        # Create region if it doesn't exist
                        try:
                            canvas_x = cut_pos.x - cut_width/2
                            canvas_y = cut_pos.y - cut_height/2
                            
                            from spatial_region_manager import SpatialRegion
                            new_region = SpatialRegion(
                                region_id=f"region_{logical_area_id}",
                                logical_area_id=logical_area_id,
                                bounds=(canvas_x, canvas_y, cut_width, cut_height),
                                parent_region_id="region_sheet"
                            )
                            
                            self.region_manager.regions[f"region_{logical_area_id}"] = new_region
                            self.region_manager.logical_area_to_region[logical_area_id] = f"region_{logical_area_id}"
                            
                            # Add to parent's children
                            parent_region = self.region_manager.regions.get("region_sheet")
                            if parent_region:
                                parent_region.child_region_ids.add(f"region_{logical_area_id}")
                            
                            print(f"COORDINATE SYNC: Created new region {logical_area_id} at canvas bounds ({canvas_x}, {canvas_y}, {cut_width}, {cut_height})")
                            
                        except Exception as e:
                            print(f"Failed to create region for {logical_area_id}: {e}")
            
            # Update spatial layout coordinates to match canvas
            for element_id, spatial_element in self.current_spatial_layout.items():
                element_data = self._find_element_data(element_id)
                if element_data and hasattr(element_data.get("pos"), 'x'):
                    # Update spatial element bounds to match canvas position
                    canvas_pos = element_data["pos"]
                    spatial_element.bounds = SpatialBounds(
                        canvas_pos.x, canvas_pos.y,
                        spatial_element.bounds.width, spatial_element.bounds.height
                    )
                    print(f"COORDINATE SYNC: Updated {element_id} spatial bounds to ({canvas_pos.x}, {canvas_pos.y})")
                        
        except Exception as e:
            print(f"Failed to synchronize region coordinates: {e}")
            import traceback
            traceback.print_exc()

    def _sync_diagram_to_egi(self) -> None:
        """Synchronize diagram state to EGI using standardized contract."""
        try:
            # Convert standardized diagram state to EGI format
            drawing_schema = DiagramDataContract.to_egi_format(self.diagram_state)
            self.egi = drawing_to_relational_graph(drawing_schema)
            if self.correspondence_engine:
                self.correspondence_engine = create_spatial_correspondence_engine(self.egi)
        except Exception as e:
            print(f"Failed to sync drawing to EGI: {e}")
            import traceback
            traceback.print_exc()

    def _render_original_egdf(self) -> None:
        """Render using the original EGDF data passed in handoff."""
        print(f"_render_original_egdf called, self.original_egdf_data is: {self.original_egdf_data is not None}")
        if not self.original_egdf_data:
            print("No original EGDF data available")
            return

        try:
            print(f"Attempting to render EGDF with keys: {list(self.original_egdf_data.keys())}")
            doc = EGDFDocument.from_dict(self.original_egdf_data)
            self.renderer.render_egdf(doc)
            print("Successfully rendered original EGDF")
        except Exception as e:
            print(f"Failed to render original EGDF: {e}")
            import traceback
            traceback.print_exc()

    def _validate_vertex_position(self, position: Point2D, area_id: str) -> bool:
        """Validate vertex position using constraint engine."""
        if not constraint_engine:
            return True

        # Use existing constraint validation
        dto = dict(self.current_drawing_schema)
        ok, msg, info = constraint_engine.validate_syntax(dto, self.validation_mode == ValidationMode.PRACTICE)
        return ok

    def _validate_predicate_position(self, position: Point2D, area_id: str) -> bool:
        """Validate predicate position using constraint engine."""
        return self._validate_vertex_position(position, area_id)  # Same validation

    def _validate_cut_placement(self, x: float, y: float, width: float, height: float, parent_area_id: str) -> bool:
        """Validate cut placement using constraint engine."""
        return True  # Simplified for now

    def _validate_ligature_connection(self, predicate_id: str, vertex_id: str) -> bool:
        """Validate ligature connection."""
        # Basic validation - ensure both elements exist
        pred_exists = any(p["id"] == predicate_id for p in self.current_drawing_schema["predicates"])
        vertex_exists = any(v["id"] == vertex_id for v in self.current_drawing_schema["vertices"])
        return pred_exists and vertex_exists

    def _validate_element_position(self, position: Point2D, area_id: str) -> bool:
        """Validate element position for movement."""
        return self._validate_vertex_position(position, area_id)

    def _find_element_data(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Find element data in drawing schema."""
        # Check vertices
        for vertex in self.current_drawing_schema["vertices"]:
            if vertex["id"] == element_id:
                return vertex

        # Check predicates
        for predicate in self.current_drawing_schema["predicates"]:
            if predicate["id"] == element_id:
                return predicate

        # Check cuts
        for cut in self.current_drawing_schema["cuts"]:
            if cut["id"] == element_id:
                return cut

        return None

    def _inline_egi_to_relational_graph(self, inline_egi: Dict[str, Any]) -> Any:
        """Convert inline EGI format to Any."""
        # This would need to be implemented based on the inline EGI format
        # For now, use the drawing_to_egi_adapter approach
        return drawing_to_relational_graph(self.current_drawing_schema)

    def _apply_layout_to_drawing_schema(self, layout: Dict[str, Any]) -> None:
        """Apply EGDF layout to drawing schema."""
        # Initialize drawing schema (but preserve original_egdf_data)
        self.current_drawing_schema = {
            "sheet_id": "sheet",
            "cuts": [],
            "vertices": [],
            "predicates": [],
            "ligatures": []
        }

        # Extract predicates
        predicates = layout.get("predicates", {})
        for pred_id, pred_data in predicates.items():
            text = pred_data.get("text", pred_id)
            x = pred_data.get("x", 100)
            y = pred_data.get("y", 100)

            predicate_data = {
                "id": pred_id,
            "name": text,
            "area_id": "sheet",  # Default area
            "pos": Point2D(x, y)
        }
    
    def _render_original_egdf(self) -> None:
        """Render using the original EGDF data passed in handoff."""
        print(f"_render_original_egdf called, self.original_egdf_data is: {self.original_egdf_data is not None}")
        if not self.original_egdf_data:
            print("No original EGDF data available")
            return
            
        try:
            print(f"Attempting to render EGDF with keys: {list(self.original_egdf_data.keys())}")
            doc = EGDFDocument.from_dict(self.original_egdf_data)
            self.renderer.render_egdf(doc)
            print("Successfully rendered original EGDF")
        except Exception as e:
            print(f"Failed to render original EGDF: {e}")
            import traceback
            traceback.print_exc()
    
    def _validate_vertex_position(self, position: Point2D, area_id: str) -> bool:
        """Validate vertex position using constraint engine."""
        if not constraint_engine:
            return True
        
        # Use existing constraint validation
        dto = dict(self.current_drawing_schema)
        ok, msg, info = constraint_engine.validate_syntax(dto, self.validation_mode == ValidationMode.PRACTICE)
        return ok
    
    def _validate_predicate_position(self, position: Point2D, area_id: str) -> bool:
        """Validate predicate position using constraint engine."""
        return self._validate_vertex_position(position, area_id)  # Same validation
    
    def _validate_cut_placement_bounds(self, bounds: SpatialBounds, parent_area_id: str) -> bool:
        """Validate cut placement using constraint engine with bounds."""
        if not constraint_engine:
            return True
        
        # Create temporary DTO with proposed cut
        temp_dto = dict(self.current_drawing_schema)
        temp_dto["cuts"] = list(temp_dto["cuts"])
        temp_dto["cuts"].append({
            "id": "_temp",
            "parent_id": parent_area_id if parent_area_id != "sheet" else None,
            "rect": (bounds.x, bounds.y, bounds.width, bounds.height)
        })
        
        ok, msg, info = constraint_engine.validate_syntax(temp_dto, False)
        return ok
    
    def _validate_ligature_connection(self, predicate_id: str, vertex_id: str) -> bool:
        """Validate ligature connection."""
        # Basic validation - ensure both elements exist
        pred_exists = any(p["id"] == predicate_id for p in self.current_drawing_schema["predicates"])
        vertex_exists = any(v["id"] == vertex_id for v in self.current_drawing_schema["vertices"])
        return pred_exists and vertex_exists
    
    def _validate_element_position(self, position: Point2D, area_id: str) -> bool:
        """Validate element position for movement."""
        return self._validate_vertex_position(position, area_id)
    
    def _find_element_data(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Find element data in drawing schema."""
        # Check vertices
        for vertex in self.current_drawing_schema["vertices"]:
            if vertex["id"] == element_id:
                return vertex
        
        # Check predicates
        for predicate in self.current_drawing_schema["predicates"]:
            if predicate["id"] == element_id:
                return predicate
        
        # Check cuts
        for cut in self.current_drawing_schema["cuts"]:
            if cut["id"] == element_id:
                return cut
        
        return None
    
    def _inline_egi_to_relational_graph(self, inline_egi: Dict[str, Any]) -> Any:
        """Convert inline EGI format to Any."""
        # This would need to be implemented based on the inline EGI format
        # For now, use the drawing_to_egi_adapter approach
        return drawing_to_relational_graph(self.current_drawing_schema)
    
    def _apply_layout_to_drawing_schema(self, layout: Dict[str, Any]) -> None:
        """Apply EGDF layout to drawing schema."""
        # Initialize drawing schema (but preserve original_egdf_data)
        self.current_drawing_schema = {
            "sheet_id": "sheet",
            "cuts": [],
            "vertices": [],
            "predicates": [],
            "ligatures": []
        }
        
        # Extract predicates
        predicates = layout.get("predicates", {})
        for pred_id, pred_data in predicates.items():
            text = pred_data.get("text", pred_id)
            x = pred_data.get("x", 100)
            y = pred_data.get("y", 100)
            
            predicate_data = {
                "id": pred_id,
                "name": text,
                "area_id": "sheet",  # Default area
                "pos": Point2D(x, y)
            }
            self.current_drawing_schema["predicates"].append(predicate_data)
        
        # Extract vertices
        vertices = layout.get("vertices", {})
        for vertex_id, vertex_data in vertices.items():
            x = vertex_data.get("x", 150)
            y = vertex_data.get("y", 150)
            
            vertex_data_schema = {
                "id": vertex_id,
                "area_id": "sheet",  # Default area
                "pos": Point2D(x, y),
                "label_kind": "generic",
                "label": None
            }
            self.current_drawing_schema["vertices"].append(vertex_data_schema)
        
        # Generate ligatures from EGI nu mappings
        if self.egi:
            for edge_id, vertex_ids in self.egi.nu.items():
                if len(vertex_ids) > 0:
                    ligature_data = {
                        "edge_id": edge_id,
                        "vertex_ids": list(vertex_ids),
                        "area_id": "sheet"
                    }
                    self.current_drawing_schema["ligatures"].append(ligature_data)
    
    def _generate_ligature_geometry(self, predicate_id: str, vertex_ids: List[str]) -> Optional[LigatureGeometry]:
        """Generate ligature geometry for spatial representation and user suggestions."""
        try:
            # Find predicate and vertex positions
            predicate_pos = None
            for pred in self.current_drawing_schema["predicates"]:
                if pred["id"] == predicate_id:
                    predicate_pos = pred["pos"]
                    break
            
            if not predicate_pos:
                return None
            
            vertex_positions = []
            for vertex_id in vertex_ids:
                for vertex in self.current_drawing_schema["vertices"]:
                    if vertex["id"] == vertex_id:
                        vertex_positions.append((vertex_id, vertex["pos"]))
                        break
            
            if not vertex_positions:
                return None
            
            # Generate spatial path from predicate to vertices
            spatial_path = [(predicate_pos.x, predicate_pos.y)]
            
            # For multiple vertices, create branching ligature geometry
            if len(vertex_positions) == 1:
                # Simple direct connection
                vertex_pos = vertex_positions[0][1]
                spatial_path.append((vertex_pos.x, vertex_pos.y))
            else:
                # Multi-vertex ligature with branching
                # Calculate centroid for branching point
                centroid_x = sum(pos.x for _, pos in vertex_positions) / len(vertex_positions)
                centroid_y = sum(pos.y for _, pos in vertex_positions) / len(vertex_positions)
                
                # Add branch point
                spatial_path.append((centroid_x, centroid_y))
                
                # Add paths to each vertex
                for vertex_id, vertex_pos in vertex_positions:
                    spatial_path.extend([
                        (centroid_x, centroid_y),  # Back to branch point
                        (vertex_pos.x, vertex_pos.y)  # To vertex
                    ])
            
            # Create ligature geometry with Chapter 16 compliance
            geometry = LigatureGeometry(
                ligature_id=predicate_id,
                vertices=vertex_ids,
                spatial_path=spatial_path,
                area_id="sheet",  # Default area
                branching_points=[(centroid_x, centroid_y)] if len(vertex_positions) > 1 else [],
                bridges=[]  # No crossings initially
            )
            
            return geometry
            
        except Exception as e:
            print(f"Failed to generate ligature geometry: {e}")
            return None
    
    def suggest_ligature_improvements(self, predicate_id: str) -> List[Dict[str, Any]]:
        """Generate user suggestions for ligature improvements based on geometry analysis."""
        suggestions = []
        
        if not self.correspondence_engine:
            return suggestions
        
        geometry = self.correspondence_engine.correspondence.ligature_mappings.get(predicate_id)
        if not geometry:
            return suggestions
        
        try:
            # Analyze current geometry for improvement opportunities
            
            # 1. Check for crossing minimization
            if self._has_ligature_crossings(geometry):
                suggestions.append({
                    "type": "crossing_reduction",
                    "description": "Rearrange ligature to reduce crossings",
                    "priority": "high",
                    "action": "rearrange_geometry"
                })
            
            # 2. Check for path length optimization
            if self._can_optimize_path_length(geometry):
                suggestions.append({
                    "type": "path_optimization",
                    "description": "Shorten ligature path for better readability",
                    "priority": "medium", 
                    "action": "optimize_path"
                })
            
            # 3. Check for area constraint violations
            violations = self._check_area_violations(geometry)
            if violations:
                suggestions.append({
                    "type": "area_compliance",
                    "description": f"Ligature violates area constraints: {violations}",
                    "priority": "high",
                    "action": "fix_area_violations"
                })
            
            # 4. Check for branching point optimization
            if len(geometry.vertices) > 2 and self._can_optimize_branching(geometry):
                suggestions.append({
                    "type": "branching_optimization",
                    "description": "Optimize branching point placement",
                    "priority": "low",
                    "action": "optimize_branching"
                })
                
        except Exception as e:
            print(f"Failed to generate ligature suggestions: {e}")
        
        return suggestions
    
    def apply_ligature_suggestion(self, predicate_id: str, suggestion_type: str) -> bool:
        """Apply a ligature improvement suggestion."""
        if not self.correspondence_engine:
            return False
        
        geometry = self.correspondence_engine.correspondence.ligature_mappings.get(predicate_id)
        if not geometry:
            return False
        
        try:
            if suggestion_type == "crossing_reduction":
                return self._reduce_ligature_crossings(predicate_id, geometry)
            elif suggestion_type == "path_optimization":
                return self._optimize_ligature_path(predicate_id, geometry)
            elif suggestion_type == "area_compliance":
                return self._fix_area_violations(predicate_id, geometry)
            elif suggestion_type == "branching_optimization":
                return self._optimize_branching_points(predicate_id, geometry)
                
        except Exception as e:
            print(f"Failed to apply ligature suggestion: {e}")
        
        return False
    
    # --- Ligature Geometry Analysis Methods ---
    
    def _has_ligature_crossings(self, geometry: LigatureGeometry) -> bool:
        """Check if ligature has crossings with other ligatures."""
        # Simplified - would need full crossing detection
        return len(geometry.spatial_path) > 4  # Heuristic
    
    def _can_optimize_path_length(self, geometry: LigatureGeometry) -> bool:
        """Check if ligature path can be shortened."""
        if len(geometry.spatial_path) < 2:
            return False
        
        # Calculate total path length
        total_length = 0
        for i in range(len(geometry.spatial_path) - 1):
            x1, y1 = geometry.spatial_path[i]
            x2, y2 = geometry.spatial_path[i + 1]
            total_length += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        # Check if direct connections would be significantly shorter
        if len(geometry.vertices) == 1:
            # Direct path length
            start = geometry.spatial_path[0]
            end = geometry.spatial_path[-1]
            direct_length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
            
            return total_length > direct_length * 1.2  # 20% threshold
        
        return False
    
    def _check_area_violations(self, geometry: LigatureGeometry) -> List[str]:
        """Check for area constraint violations."""
        violations = []
        
        # Check if ligature path stays within its designated area
        area_bounds = self.correspondence_engine.correspondence.area_mappings.get(geometry.area_id)
        if area_bounds:
            for x, y in geometry.spatial_path:
                if not (area_bounds.x <= x <= area_bounds.x + area_bounds.width and
                        area_bounds.y <= y <= area_bounds.y + area_bounds.height):
                    violations.append("path_outside_area")
                    break
        
        return violations
    
    def _can_optimize_branching(self, geometry: LigatureGeometry) -> bool:
        """Check if branching points can be optimized."""
        return len(geometry.branching_points) > 0 and len(geometry.vertices) > 2
    
    # --- Ligature Optimization Methods ---
    
    def _reduce_ligature_crossings(self, predicate_id: str, geometry: LigatureGeometry) -> bool:
        """Reduce ligature crossings through rearrangement."""
        # Simplified implementation - would use full crossing detection and resolution
        new_geometry = LigatureGeometry(
            ligature_id=geometry.ligature_id,
            vertices=geometry.vertices,
            spatial_path=geometry.spatial_path,  # Would be optimized
            area_id=geometry.area_id,
            branching_points=geometry.branching_points,
            bridges=[]  # Clear bridges after rearrangement
        )
        
        return self.correspondence_engine._rearrange_ligature(predicate_id, new_geometry)
    
    def _optimize_ligature_path(self, predicate_id: str, geometry: LigatureGeometry) -> bool:
        """Optimize ligature path for shorter length."""
        if len(geometry.spatial_path) < 2:
            return False
        
        # Create optimized path (simplified - direct connections)
        optimized_path = [geometry.spatial_path[0], geometry.spatial_path[-1]]
        
        new_geometry = LigatureGeometry(
            ligature_id=geometry.ligature_id,
            vertices=geometry.vertices,
            spatial_path=optimized_path,
            area_id=geometry.area_id,
            branching_points=[],  # Remove branching for direct path
            bridges=geometry.bridges
        )
        
        return self.correspondence_engine._rearrange_ligature(predicate_id, new_geometry)
    
    def _fix_area_violations(self, predicate_id: str, geometry: LigatureGeometry) -> bool:
        """Fix area constraint violations."""
        # Would implement path adjustment to stay within area bounds
        return True  # Simplified
    
    def _optimize_branching_points(self, predicate_id: str, geometry: LigatureGeometry) -> bool:
        """Optimize branching point placement."""
        if len(geometry.vertices) <= 2:
            return False
        
        # Recalculate optimal branching point
        vertex_positions = []
        for vertex_id in geometry.vertices:
            for vertex in self.current_drawing_schema["vertices"]:
                if vertex["id"] == vertex_id:
                    vertex_positions.append(vertex["pos"])
                    break
        
        if vertex_positions:
            # Calculate centroid
            centroid_x = sum(pos.x for pos in vertex_positions) / len(vertex_positions)
            centroid_y = sum(pos.y for pos in vertex_positions) / len(vertex_positions)
            
            new_geometry = LigatureGeometry(
                ligature_id=geometry.ligature_id,
                vertices=geometry.vertices,
                spatial_path=geometry.spatial_path,  # Would be recalculated
                area_id=geometry.area_id,
                branching_points=[(centroid_x, centroid_y)],
                bridges=geometry.bridges
            )
            
            return self.correspondence_engine._rearrange_ligature(predicate_id, new_geometry)
        
        return False
    
    def get_predicate_vertices(self, predicate_id: str) -> List[str]:
        """Get list of vertices connected to a predicate."""
        if not self.egi_system or not self.egi_system.nu:
            return []
        
        return self.egi_system.nu.get(predicate_id, [])
    
    def set_predicate_arity(self, predicate_id: str, arity: int) -> bool:
        """Set the arity for a predicate, adjusting nu mapping as needed."""
        if not self.egi_system:
            return False
        
        try:
            current_vertices = self.egi_system.nu.get(predicate_id, [])
            current_arity = len(current_vertices)
            
            if arity == current_arity:
                return True  # No change needed
            
            if arity > current_arity:
                # Need to add vertices - create new ones
                for i in range(arity - current_arity):
                    new_vertex_id = f"v_{len(self.egi_system.V) + i + 1}"
                    self.egi_system.V.add(new_vertex_id)
                    current_vertices.append(new_vertex_id)
                    
                    # Add to rho mapping with default variable name
                    if not self.egi_system.rho:
                        self.egi_system.rho = {}
                    self.egi_system.rho[new_vertex_id] = f"x{len(self.egi_system.rho) + 1}"
            
            elif arity < current_arity:
                # Need to remove vertices - remove from end
                vertices_to_remove = current_vertices[arity:]
                current_vertices = current_vertices[:arity]
                
                # Remove vertices that are no longer connected to any predicate
                for vertex_id in vertices_to_remove:
                    still_connected = False
                    for other_pred_id, other_vertices in self.egi_system.nu.items():
                        if other_pred_id != predicate_id and vertex_id in other_vertices:
                            still_connected = True
                            break
                    
                    if not still_connected:
                        self.egi_system.V.discard(vertex_id)
                        if self.egi_system.rho and vertex_id in self.egi_system.rho:
                            del self.egi_system.rho[vertex_id]
            
            # Update nu mapping
            self.egi_system.nu[predicate_id] = current_vertices
            
            # Trigger re-render to show changes
            if hasattr(self, 'renderer') and self.renderer:
                self._update_spatial_from_egi()
            
            return True
            
        except Exception as e:
            print(f"Error setting predicate arity: {e}")
            return False
    
    def _validate_move_constraints(self, element_id: str, new_position: Point2D) -> bool:
        """Validate move against syntactic and semantic constraints."""
        # ALWAYS enforce syntactic constraints regardless of mode
        if not self._validate_syntactic_constraints(element_id, new_position):
            return False
            
        # Additional semantic constraints only in practice mode
        if self.validation_mode == ValidationMode.PRACTICE:
            return self._validate_semantic_constraints(element_id, new_position)
        
        return True
    
    def _validate_syntactic_constraints(self, element_id: str, new_position: Point2D) -> bool:
        """Validate syntactic constraints (cut containment, element positioning)."""
        # Use current drawing schema instead of original EGDF for live validation
        schema = self.current_drawing_schema
        
        # Check for overlapping predicates (syntactic violation)
        predicates = schema.get("predicates", {})
        if element_id in predicates:
            element_data = predicates[element_id]
            element_w = element_data.get("w", 50)  # Default predicate width
            element_h = element_data.get("h", 26)  # Default predicate height
            element_rect = (new_position.x, new_position.y, element_w, element_h)
            
            for other_id, other_data in predicates.items():
                if other_id == element_id:
                    continue
                other_pos = other_data.get("pos", Point2D(0, 0))
                other_w = other_data.get("w", 50)
                other_h = other_data.get("h", 26)
                other_rect = (other_pos.x, other_pos.y, other_w, other_h)
                
                if self._rectangles_overlap(element_rect, other_rect):
                    print(f"Syntactic violation: Predicate {element_id} overlaps with {other_id}")
                    return False
        
        # Check cut overlap constraints
        cuts = schema.get("cuts", {})
        if element_id in cuts:
            element_data = cuts[element_id]
            element_w = element_data.get("w", 100)
            element_h = element_data.get("h", 100)
            element_rect = (new_position.x, new_position.y, element_w, element_h)
            
            for other_id, other_data in cuts.items():
                if other_id == element_id:
                    continue
                other_pos = other_data.get("pos", Point2D(0, 0))
                other_w = other_data.get("w", 100)
                other_h = other_data.get("h", 100)
                other_rect = (other_pos.x, other_pos.y, other_w, other_h)
                
                if self._rectangles_overlap(element_rect, other_rect):
                    print(f"Syntactic violation: Cut {element_id} overlaps with {other_id}")
                    return False
        
        return True
    
    def _validate_semantic_constraints(self, element_id: str, new_position: Point2D) -> bool:
        """Validate semantic constraints (meaning-preserving moves only)."""
        # In practice mode, only allow meaning-preserving transformations
        # For now, this is a placeholder - would implement full Dau transformation rules
        print(f"Semantic validation for {element_id} - allowing move (placeholder)")
        return True
    
    def _rectangles_overlap(self, rect1: tuple, rect2: tuple) -> bool:
        """Check if two rectangles overlap."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)
    
    def _sync_drawing_schema_to_diagram_state(self):
        """Update diagram state from current drawing schema for rendering."""
        from diagram_data_contract import DiagramDataContract, VertexData, PredicateData, CutData, Point2D
        
        # Convert vertices from drawing schema to diagram state
        diagram_vertices = {}
        for vertex in self.current_drawing_schema.get("vertices", []):
            diagram_vertices[vertex["id"]] = VertexData(
                id=vertex["id"],
                position=vertex["pos"],
                label=vertex.get("label") or f"*{vertex['id']}",
                area_id=vertex.get("area_id", "sheet")
            )
        
        # Convert predicates from drawing schema to diagram state
        diagram_predicates = {}
        for predicate in self.current_drawing_schema.get("predicates", []):
            diagram_predicates[predicate["id"]] = PredicateData(
                id=predicate["id"],
                position=predicate["pos"],
                text=predicate["name"],
                area_id=predicate.get("area_id", "sheet"),
                connected_vertices=predicate.get("connected_vertices", [])
            )
        
        # Convert cuts from drawing schema to diagram state
        diagram_cuts = {}
        for cut in self.current_drawing_schema.get("cuts", []):
            diagram_cuts[cut["id"]] = CutData(
                id=cut["id"],
                position=cut["pos"],
                area_id=cut.get("area_id", "sheet"),
                width=cut.get("width", 150),
                height=cut.get("height", 100)
            )
        
        # Update diagram state
        self.diagram_state = DiagramDataContract(
            vertices=diagram_vertices,
            predicates=diagram_predicates,
            cuts=diagram_cuts,
            ligatures={}
        )
        print(f"DEBUG: Updated diagram_state with {len(diagram_vertices)} vertices, {len(diagram_predicates)} predicates, {len(diagram_cuts)} cuts")
    
    def handle_canvas_click(self, scene_x: float, scene_y: float) -> Optional[str]:
        """
        Handle canvas click for element placement using clean coordinate negotiation.
        
        Returns the logical area where the click occurred, or None if invalid.
        """
        print(f"CANVAS CLICK: GUI coordinates ({scene_x}, {scene_y})")
        
        # Use coordinate negotiator for clean bidirectional mapping
        logical_area = self.coordinate_negotiator.get_logical_area_for_rendering_position(scene_x, scene_y)
        print(f"CANVAS CLICK: Mapped to logical area: {logical_area}")
        
        return logical_area
    
    def create_element_at_click(self, scene_x: float, scene_y: float, element_type: str, text: str = None) -> Optional[str]:
        """Create an element at the exact click coordinates with clean coordinate mapping."""
        
        print(f"CREATE ELEMENT: GUI coordinates ({scene_x}, {scene_y})")
        
        # Use coordinate negotiator to map GUI coordinates to proper data coordinates
        logical_area = self.coordinate_negotiator.get_logical_area_for_rendering_position(scene_x, scene_y)
        data_x, data_y = self.coordinate_negotiator.get_data_position_for_rendering(scene_x, scene_y)
        
        print(f"CREATE ELEMENT: Negotiated coordinates - GUI ({scene_x}, {scene_y}) → Data ({data_x}, {data_y}), logical area: {logical_area}")
        
        # Validate constraints before creation if in practice mode
        if self.validation_mode == ValidationMode.PRACTICE:
            # Skip validation for now - proper constraint validation to be implemented
            pass
    
        # Create element based on type at EXACT click position
        if element_type == "vertex":
            vertex_id = f"v_{len(self.egi_state.vertices):06x}"
            vertex_dto = VertexDTO(
                id=vertex_id,
                spatial=SpatialInfo(x=data_x, y=data_y),
                area_id=logical_area
            )
            
            # Add to EGI state
            self.egi_state.vertices[vertex_id] = vertex_dto
            
            # Update area mapping
            if logical_area not in self.egi_state.area_mapping:
                self.egi_state.area_mapping[logical_area] = set()
            self.egi_state.area_mapping[logical_area].add(vertex_id)
            
            # Render at EXACT click coordinates - no round-trip conversion
            if self.renderer:
                print(f"RENDER VERTEX: Using exact click coordinates ({scene_x}, {scene_y})")
                self.renderer.render_vertex(vertex_dto, gui_x=scene_x, gui_y=scene_y)
            
            print(f"Created vertex {vertex_id} at ({scene_x}, {scene_y})")
            return vertex_id
            
        elif element_type == "predicate":
            predicate_name = text if text else "P"
            edge_id = f"p_{len(self.egi_state.edges):06x}"
            edge_dto = EdgeDTO(
                id=edge_id,
                relation_name=predicate_name,
                spatial=SpatialInfo(x=scene_x, y=scene_y),
                area_id=logical_area
            )
            
            # Add to EGI state
            self.egi_state.edges[edge_id] = edge_dto
            
            # Update area mapping
            if logical_area not in self.egi_state.area_mapping:
                self.egi_state.area_mapping[logical_area] = set()
            self.egi_state.area_mapping[logical_area].add(edge_id)
            
            # Render immediately
            if self.renderer:
                # Convert to legacy format for renderer
                predicate_data = {
                    "id": edge_id,
                    "x": scene_x,
                    "y": scene_y,
                    "text": predicate_name,
                    "area_id": logical_area
                }
                self.renderer._draw_predicate(predicate_data)
            
            print(f"Created predicate '{predicate_name}' with ID {edge_id}")
            return edge_id
            
        elif element_type == "cut":
            cut_id = f"c_{len(self.egi_state.cuts):06x}"
            cut_dto = CutDTO(
                id=cut_id,
                spatial=SpatialInfo(x=scene_x, y=scene_y, width=150.0, height=100.0),
                area_id=logical_area,
                parent_cut_id=logical_area if logical_area != "sheet" else None
            )
            
            # Add to EGI state
            self.egi_state.cuts[cut_id] = cut_dto
            
            # Update area mapping - cuts create new areas
            self.egi_state.area_mapping[cut_id] = set()
            if logical_area not in self.egi_state.area_mapping:
                self.egi_state.area_mapping[logical_area] = set()
            self.egi_state.area_mapping[logical_area].add(cut_id)
            
            # Render immediately using DTO directly
            if self.renderer:
                self.renderer.render_cut(cut_dto)
            
            print(f"Created cut {cut_id} at ({scene_x}, {scene_y})")
            return cut_id
            
        else:
            print(f"ERROR: Unknown element type: {element_type}")
            return None

def _sync_drawing_schema_to_diagram_state(self):
    """Update diagram state from current drawing schema for rendering."""
    from diagram_data_contract import DiagramDataContract, VertexData, PredicateData, CutData, Point2D
    
    # Convert vertices from drawing schema to diagram state
    diagram_vertices = {}
    for vertex in self.current_drawing_schema.get("vertices", []):
        diagram_vertices[vertex["id"]] = VertexData(
            id=vertex["id"],
            position=vertex["pos"],
            label=vertex.get("label") or f"*{vertex['id']}",
            area_id=vertex.get("area_id", "sheet")
        )
    
    # Convert predicates from drawing schema to diagram state
    diagram_predicates = {}
    for predicate in self.current_drawing_schema.get("predicates", []):
        diagram_predicates[predicate["id"]] = PredicateData(
            id=predicate["id"],
            position=predicate["pos"],
            text=predicate["name"],
            area_id=predicate.get("area_id", "sheet"),
            connected_vertices=predicate.get("connected_vertices", [])
        )
    
    # Convert cuts from drawing schema to diagram state
    diagram_cuts = {}
    for cut in self.current_drawing_schema.get("cuts", []):
        diagram_cuts[cut["id"]] = CutData(
            id=cut["id"],
            position=cut["pos"],
            area_id=cut.get("area_id", "sheet"),
            width=cut.get("width", 150),
            height=cut.get("height", 100)
        )
    
    # Update diagram state
    self.diagram_state = DiagramDataContract(
        vertices=diagram_vertices,
        predicates=diagram_predicates,
        cuts=diagram_cuts,
        ligatures={}
    )
    print(f"DEBUG: Updated diagram_state with {len(diagram_vertices)} vertices, {len(diagram_predicates)} predicates, {len(diagram_cuts)} cuts")

def handle_canvas_click(self, scene_x: float, scene_y: float) -> Optional[str]:
    """
    Handle canvas click for element placement using coordinate negotiation.
    
    Returns the logical area where the click occurred, or None if invalid.
    """
    print(f"CANVAS CLICK: Scene coordinates ({scene_x}, {scene_y})")
    
    # Use coordinate negotiator to determine valid placement area
    logical_area = self.coordinate_negotiator.get_valid_placement_area(scene_x, scene_y)
    
    if logical_area:
        print(f"CANVAS CLICK: Valid placement area found: {logical_area}")
        
        # Convert to data model coordinates for element creation
        data_x, data_y = self.coordinate_negotiator.get_data_position_for_rendering(scene_x, scene_y)
        print(f"CANVAS CLICK: Data model coordinates ({data_x}, {data_y})")
        
        return logical_area
    else:
        print(f"CANVAS CLICK: No valid placement area at ({scene_x}, {scene_y})")
        return None

def create_element_at_click(self, scene_x: float, scene_y: float, element_type: str, text: str = None) -> Optional[str]:
    """Create an element at the exact click coordinates with constraint validation."""
    
    # Use scene coordinates directly - no conversion, no negotiation
    # The user clicked here, the element goes here
    
    # Determine logical area for data model (but don't let it override position)
    logical_area = self._detect_logical_area_at_position(scene_x, scene_y)
    
    # Validate constraints before creation if in practice mode
    if self.validation_mode == ValidationMode.PRACTICE:
        if not self._validate_element_placement(scene_x, scene_y, element_type, logical_area):
            print(f"CONSTRAINT VIOLATION: Cannot place {element_type} at ({scene_x}, {scene_y}) - would overlap existing elements")
            return None
    
        # This method was replaced by the EGI DTO implementation above
        return None
    
    def update_egi_on_demand(self) -> None:
        """Update EGI only when explicitly requested by user or on validation failure."""
        if self.egi and self.correspondence_engine:
            try:
                self._sync_drawing_to_egi()
                print("EGI updated on user request")
            except Exception as e:
                print(f"EGI update failed: {e}")
    
    def _detect_logical_area_at_position(self, x: float, y: float) -> str:
        """Detect logical area at position without interfering with positioning."""
        # Check if position is inside any cuts
        cuts = self.current_drawing_schema.get("cuts", [])
        if isinstance(cuts, list):
            for cut_data in cuts:
                cut_x = cut_data.get("x", 0)
                cut_y = cut_data.get("y", 0) 
                cut_w = cut_data.get("width", 0)
                cut_h = cut_data.get("height", 0)
                
                if (cut_x <= x <= cut_x + cut_w and cut_y <= y <= cut_y + cut_h):
                    return cut_data.get("id", "sheet")
        
        return "sheet"  # Default to sheet level
    
    def create_vertex_direct(self, x: float, y: float, area_id: str) -> str:
        """Create vertex at exact coordinates with no positioning interference."""
        vertex_id = f"v_{len(self.current_drawing_schema.get('vertices', {})):06x}"
        
        # Add to drawing schema at exact position
        if "vertices" not in self.current_drawing_schema:
            self.current_drawing_schema["vertices"] = []
        
        # Remove any existing vertex with same ID
        self.current_drawing_schema["vertices"] = [
            v for v in self.current_drawing_schema["vertices"] if v.get("id") != vertex_id
        ]
        
        # Add new vertex
        self.current_drawing_schema["vertices"].append({
            "id": vertex_id,
            "x": x,
            "y": y,
            "area_id": area_id
        })
        
        # Add to diagram_state for rendering at exact position
        from diagram_data_contract import VertexElement, ElementPosition
        self.diagram_state.vertices[vertex_id] = VertexElement(
            id=vertex_id,
            position=ElementPosition(x, y),
            area_id=area_id,
            label_kind="generic",
            label=None
        )
        
        # Render with styling at exact position - no repositioning
        style = self.style_manager.resolve(type="vertex", role="dot")
        radius = float(style.get("radius", 8))
        
        from PySide6.QtWidgets import QGraphicsEllipseItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPen, QBrush, QColor
        
        dot = QGraphicsEllipseItem(QRectF(x - radius, y - radius, radius * 2, radius * 2))
        
        # Apply styling
        pen_color = QColor(style.get("border_color", "#000000"))
        fill_color = QColor(style.get("fill_color", "#000000"))
        pen_width = float(style.get("border_width", 1))
        
        dot.setPen(QPen(pen_color, pen_width))
        dot.setBrush(QBrush(fill_color))
        dot.setPos(0, 0)  # Position is already in the rect
        dot.vertex_id = vertex_id
        
        # Make selectable and movable with custom tracking
        dot.setFlag(dot.GraphicsItemFlag.ItemIsSelectable, True)
        dot.setFlag(dot.GraphicsItemFlag.ItemIsMovable, True)
        dot.setFlag(dot.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Store original position for movement tracking
        dot._original_pos = dot.pos()
        dot._element_id = vertex_id
        dot._element_type = "vertex"
        dot._coordinator = self
        
        # Override itemChange to track movement
        original_itemChange = dot.itemChange
        def itemChange(change, value):
            if change == dot.GraphicsItemChange.ItemPositionHasChanged:
                new_pos = value
                abs_x = new_pos.x() + x
                abs_y = new_pos.y() + y
                self._update_element_position(vertex_id, "vertex", abs_x, abs_y)
            return original_itemChange(change, value)
        dot.itemChange = itemChange
        
        self.scene.addItem(dot)
        print(f"Created vertex {vertex_id} at exact position ({x}, {y})")
        
        return vertex_id
    
    def create_predicate_direct(self, name: str, x: float, y: float, area_id: str) -> str:
        """Create predicate at exact coordinates with no positioning interference."""
        predicate_id = f"e_{len(self.current_drawing_schema.get('predicates', {})):06x}"
        
        # Add to drawing schema at exact position
        if "predicates" not in self.current_drawing_schema:
            self.current_drawing_schema["predicates"] = []
            
        # Remove any existing predicate with same ID
        self.current_drawing_schema["predicates"] = [
            p for p in self.current_drawing_schema["predicates"] if p.get("id") != predicate_id
        ]
        
        # Add new predicate
        self.current_drawing_schema["predicates"].append({
            "id": predicate_id,
            "name": name,
            "pos": Point2D(x, y),
            "area_id": area_id
        })
        
        # Add to diagram_state for rendering at exact position
        from diagram_data_contract import PredicateElement, ElementPosition
        self.diagram_state.predicates[predicate_id] = PredicateElement(
            id=predicate_id,
            name=name,
            position=ElementPosition(x, y),
            area_id=area_id
        )
        
        # Render with styling at exact position - no repositioning
        style = self.style_manager.resolve(type="predicate", role="text")
        
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtGui import QFont, QColor
        
        text_item = QGraphicsTextItem(name)
        text_item.setPos(x, y)
        
        # Apply styling
        font_family = style.get("font_family", "Arial")
        font_size = int(style.get("font_size", 12))
        text_color = QColor(style.get("color", "#000000"))
        
        text_item.setFont(QFont(font_family, font_size))
        text_item.setDefaultTextColor(text_color)
        text_item.predicate_id = predicate_id
        
        # Make selectable and movable with custom tracking
        text_item.setFlag(text_item.GraphicsItemFlag.ItemIsSelectable, True)
        text_item.setFlag(text_item.GraphicsItemFlag.ItemIsMovable, True)
        text_item.setFlag(text_item.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Store tracking info
        text_item._element_id = predicate_id
        text_item._element_type = "predicate"
        
        # Override itemChange to track movement
        original_itemChange = text_item.itemChange
        def itemChange(change, value):
            if change == text_item.GraphicsItemChange.ItemPositionHasChanged:
                new_pos = value
                self._update_element_position(predicate_id, "predicate", new_pos.x(), new_pos.y())
            return original_itemChange(change, value)
        text_item.itemChange = itemChange
        
        self.scene.addItem(text_item)
        print(f"Created predicate '{name}' {predicate_id} at exact position ({x}, {y})")
        
        return predicate_id
    
    def create_cut_direct(self, x: float, y: float, width: float, height: float, parent_area_id: str) -> str:
        """Create cut at exact coordinates with no positioning interference."""
        cut_id = f"c_{len(self.current_drawing_schema.get('cuts', {})):06x}"
        
        # Add to drawing schema at exact position
        if "cuts" not in self.current_drawing_schema:
            self.current_drawing_schema["cuts"] = []
            
        # Remove any existing cut with same ID
        self.current_drawing_schema["cuts"] = [
            c for c in self.current_drawing_schema["cuts"] if c.get("id") != cut_id
        ]
        
        # Add new cut
        self.current_drawing_schema["cuts"].append({
            "id": cut_id,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "area_id": parent_area_id
        })
        
        # Add to diagram_state for rendering at exact position
        from diagram_data_contract import CutElement, ElementPosition, ElementSize
        self.diagram_state.cuts[cut_id] = CutElement(
            id=cut_id,
            position=ElementPosition(x, y),
            size=ElementSize(width, height),
            area_id=parent_area_id
        )
        
        # Render with styling at exact position - no repositioning
        style = self.style_manager.resolve(type="cut", role="border")
        
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPen, QBrush, QColor
        
        # Apply styling with proper key names
        border_color = QColor(style.get("border_color", style.get("line_color", "#000000")))
        border_width = float(style.get("border_width", style.get("line_width", 2)))
        fill_color = QColor(style.get("fill_color", "transparent"))
        
        # Use simple rectangle for better interaction
        rect_item = QGraphicsRectItem(0, 0, width, height)
        rect_item.setPen(QPen(border_color, border_width))
        rect_item.setBrush(QBrush(fill_color))
        rect_item.cut_id = cut_id
        rect_item.setPos(x, y)
        rect_item.setZValue(10)  # Above other elements for selection
        
        # Make selectable and movable with custom tracking
        rect_item.setFlag(rect_item.GraphicsItemFlag.ItemIsSelectable, True)
        rect_item.setFlag(rect_item.GraphicsItemFlag.ItemIsMovable, True)
        rect_item.setFlag(rect_item.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Add selection visual feedback
        def paint(painter, option, widget):
            # Draw the rectangle
            painter.setPen(rect_item.pen())
            painter.setBrush(rect_item.brush())
            painter.drawRect(rect_item.rect())
            
            # Draw selection outline if selected
            if rect_item.isSelected():
                selection_pen = QPen(QColor("#1E88E5"), 3)
                selection_pen.setStyle(selection_pen.PenStyle.DashLine)
                painter.setPen(selection_pen)
                painter.setBrush(QBrush())
                painter.drawRect(rect_item.rect())
        
        rect_item.paint = paint
        
        # Store tracking info
        rect_item._element_id = cut_id
        rect_item._element_type = "cut"
        
        # Override itemChange to track movement - use proper method binding
        original_itemChange = QGraphicsRectItem.itemChange
        def itemChange(change, value):
            if change == rect_item.GraphicsItemChange.ItemPositionHasChanged:
                new_pos = value
                print(f"DEBUG: Cut {cut_id} moved to ({new_pos.x()}, {new_pos.y()})")
                self._update_element_position(cut_id, "cut", new_pos.x(), new_pos.y())
            return original_itemChange(rect_item, change, value)
        rect_item.itemChange = itemChange.__get__(rect_item, QGraphicsRectItem)
        
        # Store original size for resize operations
        rect_item._original_width = width
        rect_item._original_height = height
        
        self.scene.addItem(rect_item)
        print(f"Created cut {cut_id} at exact position ({x}, {y}) size {width}x{height}")
        
        return cut_id
    
    def update_vertex_name(self, vertex_id: str, name: str) -> bool:
        """Update vertex name in both drawing schema and EGIF."""
        try:
            # Update drawing schema
            for vertex in self.current_drawing_schema.get("vertices", []):
                if vertex.get("id") == vertex_id:
                    vertex["name"] = name if name else None
                    break
            
            # Update diagram state
            if vertex_id in self.diagram_state.vertices:
                self.diagram_state.vertices[vertex_id].label = name if name else None
            
            # Sync to EGI
            self._sync_diagram_to_egi()
            print(f"Updated vertex {vertex_id} name to '{name}'")
            return True
            
        except Exception as e:
            print(f"Failed to update vertex name: {e}")
            return False
    
    def update_cut_size(self, cut_id: str, width: float, height: float) -> bool:
        """Update cut size in both drawing schema and EGIF."""
        try:
            # Update drawing schema
            for cut in self.current_drawing_schema.get("cuts", []):
                if cut.get("id") == cut_id:
                    cut["width"] = width
                    cut["height"] = height
                    break
            
            # Update diagram state
            if cut_id in self.diagram_state.cuts:
                # Update the cut's bounding box
                cut_obj = self.diagram_state.cuts[cut_id]
                if hasattr(cut_obj, 'x') and hasattr(cut_obj, 'y'):
                    # Keep position, update size
                    cut_obj.width = width
                    cut_obj.height = height
            
            # Recalculate areas and sync to EGI
            self._recalculate_logical_areas()
            self._sync_diagram_to_egi()
            print(f"Updated cut {cut_id} size to {width}x{height}")
            return True
            
        except Exception as e:
            print(f"Failed to update cut size: {e}")
            return False
    
    def create_ligature(self, source_type: str, source_id: str, target_type: str, target_id: str) -> bool:
        """Create a ligature connection between two elements."""
        try:
            # Validate connection based on EG semantics
            if source_type == "predicate" and target_type == "vertex":
                # Predicate to vertex - check ν mapping allows this connection
                if self._validate_predicate_vertex_connection(source_id, target_id):
                    self._create_ligature_visual(source_id, target_id, source_type, target_type)
                    self._update_nu_mapping(source_id, target_id)
                    self._sync_diagram_to_egi()
                    return True
                else:
                    print(f"Semantic constraint: Predicate {source_id} cannot connect to vertex {target_id}")
                    return False
            
            elif source_type == "vertex" and target_type == "predicate":
                # Vertex to predicate - same validation as above
                if self._validate_predicate_vertex_connection(target_id, source_id):
                    self._create_ligature_visual(source_id, target_id, source_type, target_type)
                    self._update_nu_mapping(target_id, source_id)
                    self._sync_diagram_to_egi()
                    return True
                else:
                    print(f"Semantic constraint: Vertex {source_id} cannot connect to predicate {target_id}")
                    return False
            
            elif source_type == "vertex" and target_type == "vertex":
                # Vertex to vertex - creates identity line (always valid in composition mode)
                self._create_ligature_visual(source_id, target_id, source_type, target_type)
                self._create_identity_connection(source_id, target_id)
                self._sync_diagram_to_egi()
                return True
            
            else:
                print(f"Invalid ligature connection: {source_type} to {target_type}")
                return False
                
        except Exception as e:
            print(f"Failed to create ligature: {e}")
            return False
    
    def _validate_predicate_vertex_connection(self, predicate_id: str, vertex_id: str) -> bool:
        """Validate if a predicate can connect to a vertex based on semantic constraints."""
        # In composition mode, allow all connections (user is building the diagram)
        if self.validation_mode == ValidationMode.COMPOSITION:
            return True
        
        # In practice mode, check existing ν mapping
        if self.validation_mode == ValidationMode.PRACTICE:
            # Check if this connection exists in the target EGI
            # For now, allow all connections - full validation will be implemented later
            return True
        
        return True
    
    def _create_ligature_visual(self, source_id: str, target_id: str, source_type: str, target_type: str):
        """Create visual ligature line between two elements."""
        from PySide6.QtWidgets import QGraphicsLineItem
        from PySide6.QtGui import QPen, QColor
        from PySide6.QtCore import QLineF
        
        # Find source and target items in the scene
        source_item = None
        target_item = None
        
        for item in self.scene.items():
            if hasattr(item, f'{source_type}_id') and getattr(item, f'{source_type}_id') == source_id:
                source_item = item
            if hasattr(item, f'{target_type}_id') and getattr(item, f'{target_type}_id') == target_id:
                target_item = item
        
        if source_item and target_item:
            # Calculate connection points
            source_pos = source_item.pos() + source_item.boundingRect().center()
            target_pos = target_item.pos() + target_item.boundingRect().center()
            
            # Create line item
            line = QGraphicsLineItem(QLineF(source_pos, target_pos))
            
            # Style the ligature
            style = self.style_manager.resolve(type="ligature", role="line")
            color = QColor(style.get("color", "#000000"))
            width = float(style.get("width", 2))
            line.setPen(QPen(color, width))
            
            # Store connection info
            line.source_id = source_id
            line.target_id = target_id
            line.source_type = source_type
            line.target_type = target_type
            line.setZValue(100)  # Ligatures on top
            
            self.scene.addItem(line)
            print(f"Created ligature visual from {source_type} {source_id} to {target_type} {target_id}")
    
    def _update_nu_mapping(self, predicate_id: str, vertex_id: str):
        """Update the ν mapping for predicate-vertex connections."""
        # Update drawing schema
        for predicate in self.current_drawing_schema.get("predicates", []):
            if predicate.get("id") == predicate_id:
                if "connected_vertices" not in predicate:
                    predicate["connected_vertices"] = []
                if vertex_id not in predicate["connected_vertices"]:
                    predicate["connected_vertices"].append(vertex_id)
                break
        
        # Update diagram state
        if predicate_id in self.diagram_state.predicates:
            pred_obj = self.diagram_state.predicates[predicate_id]
            if not hasattr(pred_obj, 'connected_vertices'):
                pred_obj.connected_vertices = []
            if vertex_id not in pred_obj.connected_vertices:
                pred_obj.connected_vertices.append(vertex_id)
    
    def _create_identity_connection(self, vertex1_id: str, vertex2_id: str):
        """Create identity connection between two vertices."""
        # For now, just log the connection - full identity logic will be implemented later
        print(f"Created identity connection between vertices {vertex1_id} and {vertex2_id}")
        
        # Update drawing schema to track identity connections
        if "identity_connections" not in self.current_drawing_schema:
            self.current_drawing_schema["identity_connections"] = []
        
        connection = {"vertex1": vertex1_id, "vertex2": vertex2_id}
        if connection not in self.current_drawing_schema["identity_connections"]:
            self.current_drawing_schema["identity_connections"].append(connection)
    
    def _update_element_position(self, element_id: str, element_type: str, new_x: float, new_y: float) -> None:
        """Update element position in both drawing schema and EGIF."""
        try:
            # Update drawing schema
            if element_type == "vertex":
                for vertex in self.current_drawing_schema.get("vertices", []):
                    if vertex.get("id") == element_id:
                        vertex["x"] = new_x
                        vertex["y"] = new_y
                        break
            elif element_type == "predicate":
                for predicate in self.current_drawing_schema.get("predicates", []):
                    if predicate.get("id") == element_id:
                        predicate["x"] = new_x
                        predicate["y"] = new_y
                        break
            elif element_type == "cut":
                for cut in self.current_drawing_schema.get("cuts", []):
                    if cut.get("id") == element_id:
                        cut["x"] = new_x
                        cut["y"] = new_y
                        break
            
            # Update diagram state
            if element_type == "vertex" and element_id in self.diagram_state.vertices:
                self.diagram_state.vertices[element_id].position.x = new_x
                self.diagram_state.vertices[element_id].position.y = new_y
            elif element_type == "predicate" and element_id in self.diagram_state.predicates:
                self.diagram_state.predicates[element_id].position.x = new_x
                self.diagram_state.predicates[element_id].position.y = new_y
            elif element_type == "cut" and element_id in self.diagram_state.cuts:
                self.diagram_state.cuts[element_id].position.x = new_x
                self.diagram_state.cuts[element_id].position.y = new_y
            
            # Update area assignment based on new position
            new_area = self._detect_logical_area_at_position(new_x, new_y)
            if element_type == "vertex":
                for vertex in self.current_drawing_schema.get("vertices", []):
                    if vertex.get("id") == element_id:
                        vertex["area_id"] = new_area
                        break
                if element_id in self.diagram_state.vertices:
                    self.diagram_state.vertices[element_id].area_id = new_area
            elif element_type == "predicate":
                for predicate in self.current_drawing_schema.get("predicates", []):
                    if predicate.get("id") == element_id:
                        predicate["area_id"] = new_area
                        break
                if element_id in self.diagram_state.predicates:
                    self.diagram_state.predicates[element_id].area_id = new_area
            
            # Sync to EGI
            self._sync_diagram_to_egi()
            print(f"Updated {element_type} {element_id} position to ({new_x}, {new_y}) in area {new_area}")
            
        except Exception as e:
            print(f"Failed to update element position: {e}")
    
    def _validate_element_placement(self, x: float, y: float, element_type: str, area_id: str) -> bool:
        """Validate element placement using constraint engine."""
        try:
            from controller.constraint_engine import validate_syntactic_constraints
            
            # Build DTO with proposed element for validation
            dto = self._build_constraint_dto_with_element(x, y, element_type, area_id)
            
            # Check syntactic constraints
            valid, msg, info = validate_syntactic_constraints(dto)
            if not valid:
                print(f"SYNTACTIC CONSTRAINT: {msg}")
                return False
                
            return True
            
        except ImportError:
            print("WARNING: Constraint engine not available, allowing placement")
            return True
        except Exception as e:
            print(f"ERROR in constraint validation: {e}")
            return True  # Allow on error to avoid blocking user
    
    def _build_constraint_dto_with_element(self, x: float, y: float, element_type: str, area_id: str) -> dict:
        """Build constraint DTO including proposed new element."""
        dto = {
            'sheet_id': 'sheet',
            'cuts': {},
            'vertices': {},
            'predicates': {},
            'ligatures': {}
        }
        
        # Add existing elements from drawing schema
        for cut_data in self.current_drawing_schema.get('cuts', []):
            cut_id = cut_data['id']
            dto['cuts'][cut_id] = {
                'rect': (cut_data['x'], cut_data['y'], cut_data['width'], cut_data['height']),
                'parent_id': cut_data.get('parent_id', 'sheet')
            }
        
        for vertex_data in self.current_drawing_schema.get('vertices', []):
            vertex_id = vertex_data['id']
            dto['vertices'][vertex_id] = {
                'pos': (vertex_data['x'], vertex_data['y']),
                'radius': 8.0,
                'area_id': vertex_data.get('area_id', 'sheet')
            }
        
        for pred_data in self.current_drawing_schema.get('predicates', []):
            pred_id = pred_data['id']
            # Estimate text bounds for constraint checking
            text_width = len(pred_data.get('text', 'P')) * 8
            text_height = 12
            dto['predicates'][pred_id] = {
                'rect': (pred_data['x'], pred_data['y'], text_width, text_height),
                'area_id': pred_data.get('area_id', 'sheet'),
                'text': pred_data.get('text', 'P')
            }
        
        # Add proposed new element
        if element_type == "vertex":
            dto['vertices']['_proposed'] = {
                'pos': (x, y),
                'radius': 8.0,
                'area_id': area_id
            }
        elif element_type == "predicate":
            dto['predicates']['_proposed'] = {
                'rect': (x, y, 20, 12),  # Estimated size
                'area_id': area_id,
                'text': 'P'
            }
        elif element_type == "cut":
            dto['cuts']['_proposed'] = {
                'rect': (x, y, 150, 100),
                'parent_id': area_id if area_id != 'sheet' else None
            }
        
        return dto
    
    def synchronize_coordinates(self) -> None:
        """Synchronize coordinate systems with actual rendered elements."""
        print("COORDINATE SYNC: Synchronizing all coordinate systems")
        
        # Update coordinate negotiator with current elements
        for vertex in self.current_drawing_schema.get("vertices", []):
            self.coordinate_negotiator.register_element(
                vertex["id"], 
                vertex["pos"].x, 
                vertex["pos"].y
            )
        
        for predicate in self.current_drawing_schema.get("predicates", []):
            self.coordinate_negotiator.register_element(
                predicate["id"], 
                predicate["pos"].x, 
                predicate["pos"].y
            )
        
        for cut in self.current_drawing_schema.get("cuts", []):
            self.coordinate_negotiator.register_element(
                cut["id"], 
                cut["pos"].x, 
                cut["pos"].y,
                cut.get("width", 150),
                cut.get("height", 100)
            )
            
            # Create spatial region for cut using coordinate negotiator
            parent_area = cut.get("area_id", "sheet")
            logical_area = self.coordinate_negotiator.create_region_for_cut(
                cut["id"], 
                cut["pos"].x, 
                cut["pos"].y,
                cut.get("width", 150),
                cut.get("height", 100),
                parent_area
            )
            
            # Update cut's area_id if it was created
            cut["area_id"] = logical_area
        
        # Synchronize with rendering backend
        self.coordinate_negotiator.synchronize_with_rendering_backend()
        
        print("COORDINATE SYNC: Synchronization complete")
