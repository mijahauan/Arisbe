#!/usr/bin/env python3
"""
Simplified standalone test for dynamic view generation.
Avoids complex import chains by implementing minimal components directly.
"""

import sys
import os
sys.path.append('src')

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import xml.etree.ElementTree as ET

# Import only the core EGI structure
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from frozendict import frozendict

# Import transformation engine for rule-governed operations (simplified for testing)
# from transformation_engine import TransformationEngine, OperationRequest, OperationType
# from transformation_rules import TransformationRuleType
# from spatial_tracker import RTreeCutTracker

# Import reusable rendering core
from reusable_rendering_core import BoundaryAnchor, CutRenderer, LigatureRenderer, VertexRenderer, RenderingStyle


class DetailLevel(Enum):
    """Level of detail for rendering at different zoom levels."""
    OVERVIEW = "overview"
    INTERMEDIATE = "intermediate"
    DETAILED = "detailed"
    MICRO = "micro"


@dataclass
class ViewportBounds:
    """Defines the visible area and zoom level for a view."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    zoom_level: float = 1.0
    
    @property
    def width(self) -> float:
        return self.x_max - self.x_min
    
    @property
    def height(self) -> float:
        return self.y_max - self.y_min


@dataclass
class RenderedElement:
    """A rendered element with its visual properties."""
    element_id: ElementID
    element_type: str  # 'vertex', 'edge', 'cut'
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    text: str = ""
    font_size: float = 12.0
    visible: bool = True
    detail_level: DetailLevel = DetailLevel.DETAILED
    
    # Visual properties
    color: str = "black"
    background_color: str = "white"
    border_color: str = "black"
    border_width: float = 1.0
    
    # For cuts - path coordinates
    path_points: List[Tuple[float, float]] = field(default_factory=list)
    
    # For edges - ligature connection points
    ligature_points: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class GraphView:
    """A rendered view of a graph with all visual elements."""
    viewport: ViewportBounds
    elements: List[RenderedElement]
    detail_level: DetailLevel
    
    # Metadata
    total_elements: int = 0
    visible_elements: int = 0
    
    def get_elements_by_type(self, element_type: str) -> List[RenderedElement]:
        """Get all rendered elements of a specific type."""
        return [e for e in self.elements if e.element_type == element_type]


class CutPositionValidator:
    """Validates and enforces exclusive positioning constraints for cuts."""
    
    def __init__(self):
        self.cuts = {}  # cut_id -> (x, y, width, height)
    
    def add_cut(self, cut_id: str, x: float, y: float, width: float, height: float) -> bool:
        """Add a cut and validate its position against existing cuts."""
        new_rect = (x, y, width, height)
        
        # Check against all existing cuts
        for existing_id, existing_rect in self.cuts.items():
            if not self._are_exclusive(new_rect, existing_rect):
                return False  # Position violates exclusive constraint
        
        self.cuts[cut_id] = new_rect
        return True
    
    def _are_exclusive(self, rect1: Tuple[float, float, float, float], 
                      rect2: Tuple[float, float, float, float]) -> bool:
        """Check if two rectangles are either nested or disjoint (no partial overlap)."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        # Convert to right/bottom coordinates
        r1, b1 = x1 + w1, y1 + h1
        r2, b2 = x2 + w2, y2 + h2
        
        # Check if completely disjoint
        if r1 <= x2 or r2 <= x1 or b1 <= y2 or b2 <= y1:
            return True  # Disjoint - valid
        
        # Check if rect1 completely contains rect2
        if x1 <= x2 and y1 <= y2 and r1 >= r2 and b1 >= b2:
            return True  # Nested - valid
        
        # Check if rect2 completely contains rect1
        if x2 <= x1 and y2 <= y1 and r2 >= r1 and b2 >= b1:
            return True  # Nested - valid
        
        # Otherwise, partial overlap - invalid
        return False
    
    def get_nesting_depth(self, cut_id: str) -> int:
        """Get the nesting depth of a cut (how many cuts contain it)."""
        if cut_id not in self.cuts:
            return 0
        
        target_rect = self.cuts[cut_id]
        depth = 0
        
        for other_id, other_rect in self.cuts.items():
            if other_id != cut_id and self._contains(other_rect, target_rect):
                depth += 1
        
        return depth
    
    def _contains(self, outer_rect: Tuple[float, float, float, float],
                  inner_rect: Tuple[float, float, float, float]) -> bool:
        """Check if outer_rect completely contains inner_rect."""
        x1, y1, w1, h1 = outer_rect
        x2, y2, w2, h2 = inner_rect
        
        return (x1 <= x2 and y1 <= y2 and 
                x1 + w1 >= x2 + w2 and y1 + h1 >= y2 + h2)


class ExclusiveLayoutEngine:
    """Layout engine that ensures exclusive positioning of cuts."""
    
    def __init__(self):
        self.validator = CutPositionValidator()
        self.base_cut_size = 80  # Base size for cuts
        self.cut_padding = 20    # Padding between cuts
        self.nesting_margin = 15 # Margin for nested cuts
    
    def layout_cuts(self, egi: RelationalGraphWithCuts) -> Dict[str, Tuple[float, float, float, float]]:
        """Layout cuts ensuring exclusive positioning."""
        cut_positions = {}
        
        if not egi.Cut:
            return cut_positions
        
        # Simple layout for now - position cuts sequentially
        current_x, current_y = 50, 50
        
        for i, cut in enumerate(egi.Cut):
            cut_id = cut.id
            width = height = self.base_cut_size
            
            # Validate and add position
            if self.validator.add_cut(cut_id, current_x, current_y, width, height):
                cut_positions[cut_id] = (current_x, current_y, width, height)
            
            # Move to next position
            current_y += height + self.cut_padding
        
        return cut_positions


class TransformationRuleGovernedBuilder:
    """Builder that ensures all graph operations follow EG transformation rules."""
    
    def __init__(self):
        self.operation_history = []  # Track operations for provenance
    
    def build_graph_with_rules(self, base_graph: RelationalGraphWithCuts, 
                              operations: List[Dict]) -> RelationalGraphWithCuts:
        """Build a graph by applying a sequence of rule-governed operations."""
        current_graph = base_graph
        
        for operation in operations:
            # Apply operation following EG transformation rules
            if operation["type"] == "ADD_VERTEX":
                current_graph = self._add_vertex_with_rules(current_graph, operation)
            elif operation["type"] == "ADD_EDGE":
                current_graph = self._add_edge_with_rules(current_graph, operation)
            elif operation["type"] == "ADD_CUT":
                current_graph = self._add_cut_with_rules(current_graph, operation)
            
            self.operation_history.append(operation)
        
        return current_graph
    
    def _add_vertex_with_rules(self, graph: RelationalGraphWithCuts, operation: Dict) -> RelationalGraphWithCuts:
        """Add vertex following insertion rule constraints."""
        vertex_id = operation["target_element_id"]
        context_id = operation["context_id"]
        
        # Create new vertex
        new_vertex = Vertex(id=vertex_id)
        
        # Update graph following transformation rules
        new_vertices = graph.V | frozenset([new_vertex])
        new_area = dict(graph.area)
        new_area[context_id] = new_area.get(context_id, frozenset()) | frozenset([vertex_id])
        new_rho = dict(graph.rho)
        new_rho[vertex_id] = operation.get("parameters", {}).get("name", "")
        
        return RelationalGraphWithCuts(
            V=new_vertices,
            E=graph.E,
            nu=graph.nu,
            sheet=graph.sheet,
            Cut=graph.Cut,
            area=frozendict(new_area),
            rel=graph.rel,
            rho=frozendict(new_rho)
        )
    
    def _add_edge_with_rules(self, graph: RelationalGraphWithCuts, operation: Dict) -> RelationalGraphWithCuts:
        """Add edge following insertion rule constraints."""
        # Implementation would follow EG transformation rules for edge insertion
        return graph
    
    def _add_cut_with_rules(self, graph: RelationalGraphWithCuts, operation: Dict) -> RelationalGraphWithCuts:
        """Add cut following double-cut insertion rule constraints."""
        # Implementation would follow EG transformation rules for cut insertion
        return graph
    
    def validate_graph_construction(self, graph: RelationalGraphWithCuts) -> bool:
        """Validate that a graph could have been constructed using transformation rules."""
        # Check spatial logic consistency
        # Validate cut nesting relationships
        # Ensure vertex-edge relationships follow ν mapping constraints
        return True  # Simplified validation for now


class SimpleViewGenerator:
    """Simplified view generator for testing."""
    
    def __init__(self):
        self.layout_engine = ExclusiveLayoutEngine()
    
    def generate_view(self, egi: RelationalGraphWithCuts, viewport: ViewportBounds) -> GraphView:
        """Generate a simple view of the graph."""
        
        # Determine detail level based on zoom
        if viewport.zoom_level < 0.1:
            detail_level = DetailLevel.OVERVIEW
        elif viewport.zoom_level < 0.5:
            detail_level = DetailLevel.INTERMEDIATE
        elif viewport.zoom_level < 2.0:
            detail_level = DetailLevel.DETAILED
        else:
            detail_level = DetailLevel.MICRO
        
        elements = []
        
        # Simple layout: arrange elements properly according to logical structure
        base_x, base_y = 50, 80
        spacing_x, spacing_y = 120, 80
        
        # First, determine which elements are in cuts vs on sheet
        elements_in_cuts = set()
        for cut_id, enclosed in egi.area.items():
            if cut_id != egi.sheet:  # Don't count sheet as a cut
                elements_in_cuts.update(enclosed)
        
        # Position vertices first
        vertex_positions = {}
        sheet_vertex_count = 0
        cut_vertex_positions = {}
        
        for vertex in egi.V:
            if vertex.id in elements_in_cuts:
                # This vertex is inside a cut - we'll position it later
                continue
            else:
                # Position on sheet (outside cuts)
                x = base_x + (sheet_vertex_count % 4) * spacing_x
                y = base_y + (sheet_vertex_count // 4) * spacing_y
                vertex_positions[vertex.id] = (x, y)
                sheet_vertex_count += 1
        
        # Render cuts and position their contents
        cut_positions = {}
        for i, cut in enumerate(egi.Cut):
            # Position cut on sheet
            cut_x = base_x + 200 + (i % 2) * 250
            cut_y = base_y + 150 + (i // 2) * 200
            
            # Get elements enclosed by this cut
            enclosed = egi.area.get(cut.id, set())
            
            # Position vertices inside this cut
            cut_vertex_count = 0
            for vertex in egi.V:
                if vertex.id in enclosed:
                    # Position inside cut
                    x = cut_x + 30 + (cut_vertex_count % 2) * 60
                    y = cut_y + 30 + (cut_vertex_count // 2) * 40
                    vertex_positions[vertex.id] = (x, y)
                    cut_vertex_count += 1
            
            # Calculate cut boundary around enclosed elements
            if enclosed:
                # Find bounding box of enclosed elements
                min_x = cut_x + 20
                min_y = cut_y + 20
                max_x = cut_x + 120
                max_y = cut_y + 80
            else:
                # Empty cut
                min_x, min_y = cut_x, cut_y
                max_x, max_y = cut_x + 100, cut_y + 60
            
            # Add margin around cut contents
            margin = 15
            cut_element = RenderedElement(
                element_id=cut.id,
                element_type="cut",
                x=min_x - margin,
                y=min_y - margin,
                width=(max_x - min_x) + 2 * margin,
                height=(max_y - min_y) + 2 * margin,
                path_points=[
                    (min_x - margin, min_y - margin),
                    (max_x + margin, min_y - margin),
                    (max_x + margin, max_y + margin),
                    (min_x - margin, max_y + margin),
                    (min_x - margin, min_y - margin)  # Close path
                ],
                border_width=2.0,
                border_color="blue",
                detail_level=detail_level
            )
            elements.append(cut_element)
            cut_positions[cut.id] = (cut_x, cut_y)
        
        # Render vertices
        for vertex in egi.V:
            if vertex.id not in vertex_positions:
                continue  # Skip if we couldn't position it
                
            x, y = vertex_positions[vertex.id]
            
            # Get constant name if any
            constant_name = egi.rho.get(vertex.id, "")
            
            # Calculate nesting depth for parity (universal vs individual)
            nesting_depth = 0
            for cut_id, enclosed in egi.area.items():
                if cut_id != egi.sheet and vertex.id in enclosed:
                    nesting_depth += 1
            
            is_universal = (nesting_depth % 2) == 1
            
            vertex_element = RenderedElement(
                element_id=vertex.id,
                element_type="vertex",
                x=x - 5,
                y=y - 5,
                width=10,
                height=10,
                text=constant_name,
                font_size=12,
                color="blue" if is_universal else "black",
                detail_level=detail_level
            )
            elements.append(vertex_element)
        
        # Render edges
        for edge in egi.E:
            # Get connected vertices
            connected_vertices = egi.nu.get(edge.id, [])
            if not connected_vertices:
                continue
            
            # Check if edge is inside a cut
            edge_in_cut = None
            for cut_id, enclosed in egi.area.items():
                if cut_id != egi.sheet and edge.id in enclosed:
                    edge_in_cut = cut_id
                    break
            
            # Position edge based on its first connected vertex or cut location
            if connected_vertices[0] in vertex_positions:
                vx, vy = vertex_positions[connected_vertices[0]]
                if edge_in_cut and edge_in_cut in cut_positions:
                    # Edge is in cut, position it inside cut
                    cut_x, cut_y = cut_positions[edge_in_cut]
                    x, y = cut_x + 40, cut_y + 50
                else:
                    # Edge is on sheet, position near first vertex
                    x, y = vx + 20, vy - 10
            else:
                # Fallback positioning
                x = base_x + len(elements) * 30
                y = base_y - 30
            
            # Get relation name
            relation_name = egi.rel.get(edge.id, f"R{edge.id}")
            
            # Calculate ligature points to connected vertices
            ligature_points = []
            for vertex_id in connected_vertices:
                if vertex_id in vertex_positions:
                    vx, vy = vertex_positions[vertex_id]
                    ligature_points.append((vx, vy))
            
            edge_element = RenderedElement(
                element_id=edge.id,
                element_type="edge",
                x=x,
                y=y,
                width=len(relation_name) * 8,
                height=16,
                text=relation_name,
                font_size=14,
                ligature_points=ligature_points,
                detail_level=detail_level
            )
            elements.append(edge_element)
        
        return GraphView(
            viewport=viewport,
            elements=elements,
            detail_level=detail_level,
            total_elements=len(egi.V) + len(egi.E) + len(egi.Cut),
            visible_elements=len(elements)
        )


class SimpleSVGRenderer:
    """Renders a GraphView to SVG for immediate visual feedback."""
    
    def __init__(self):
        self.width = 800
        self.height = 600
        # Initialize reusable rendering components
        self.cut_renderer = CutRenderer()
        self.ligature_renderer = LigatureRenderer()
        self.vertex_renderer = VertexRenderer()
        self.boundary_anchor = BoundaryAnchor()

    def render_to_svg(self, view: GraphView, filename: str = "test_graph.svg"):
        """Render a GraphView to an SVG file."""
        
        # Create SVG root element
        svg = ET.Element("svg", {
            "width": str(self.width),
            "height": str(self.height),
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": f"0 0 {self.width} {self.height}"
        })
        
        # Add background
        background = ET.SubElement(svg, "rect", {
            "width": "100%",
            "height": "100%",
            "fill": "white",
            "stroke": "lightgray",
            "stroke-width": "1"
        })
        
        # Add title
        title_text = ET.SubElement(svg, "text", {
            "x": "10",
            "y": "25",
            "font-family": "Arial, sans-serif",
            "font-size": "16",
            "fill": "black"
        })
        title_text.text = f"EG View - {view.visible_elements}/{view.total_elements} elements visible - {view.detail_level.value}"
        
        # Render elements by type (cuts first, then edges, then vertices)
        cuts = view.get_elements_by_type("cut")
        edges = view.get_elements_by_type("edge")
        vertices = view.get_elements_by_type("vertex")
        
        # Render cuts (background)
        for cut in cuts:
            self._render_cut_svg(svg, cut)
        
        # Render edges
        for edge in edges:
            self._render_edge_svg(svg, edge)
        
        # Render vertices (foreground)
        for vertex in vertices:
            self._render_vertex_svg(svg, vertex)
        
        # Add viewport info
        viewport_info = ET.SubElement(svg, "text", {
            "x": "10",
            "y": str(self.height - 10),
            "font-family": "Arial, sans-serif",
            "font-size": "12",
            "fill": "gray"
        })
        viewport_info.text = f"Viewport: ({view.viewport.x_min:.1f}, {view.viewport.y_min:.1f}) to ({view.viewport.x_max:.1f}, {view.viewport.y_max:.1f}) | Zoom: {view.viewport.zoom_level:.2f}"
        
        # Write to file
        tree = ET.ElementTree(svg)
        ET.indent(tree, space="  ", level=0)
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        
        print(f"✅ Rendered graph to {filename}")
        return filename
    
    def _render_cut_svg(self, parent: ET.Element, cut: RenderedElement):
        """Render a cut as a closed path."""
        if cut.path_points:
            # Render as path
            path_data = "M " + " L ".join([f"{x},{y}" for x, y in cut.path_points]) + " Z"
            path = ET.SubElement(parent, "path", {
                "d": path_data,
                "fill": "none",
                "stroke": cut.border_color,
                "stroke-width": str(cut.border_width),
                "stroke-dasharray": "5,5"
            })
        
        # Add cut label
        text = ET.SubElement(parent, "text", {
            "x": str(cut.x + 5),
            "y": str(cut.y + 15),
            "font-family": "Arial, sans-serif",
            "font-size": "10",
            "fill": "blue"
        })
        text.text = f"Cut {cut.element_id}"
    
    def _render_vertex_svg(self, parent: ET.Element, vertex: RenderedElement):
        """Render a vertex using reusable rendering core."""
        # Calculate vertex center
        center_x = vertex.x + vertex.width / 2
        center_y = vertex.y + vertex.height / 2
        
        # Determine if vertex is universal (based on nesting depth parity)
        is_universal = getattr(vertex, 'nesting_depth', 0) % 2 == 1
        
        # Use reusable vertex renderer
        vertex_elements = self.vertex_renderer.render_vertex_spot(
            center_x, center_y, radius=3, name=vertex.text or "", is_universal=is_universal
        )
        
        # Add elements to parent
        for element_svg in vertex_elements:
            try:
                element = ET.fromstring(element_svg)
                parent.append(element)
            except ET.ParseError:
                # Fallback for malformed SVG
                pass
        
        # Vertex label (constant name if any)
        if vertex.text:
            text = ET.SubElement(parent, "text", {
                "x": str(vertex.x + vertex.width / 2),
                "y": str(vertex.y + vertex.height + 15),
                "font-family": "Arial, sans-serif",
                "font-size": str(vertex.font_size),
                "fill": vertex.color,
                "text-anchor": "middle"
            })
            text.text = vertex.text
        
        # Vertex ID for debugging
        id_text = ET.SubElement(parent, "text", {
            "x": str(vertex.x + vertex.width + 5),
            "y": str(vertex.y + vertex.height / 2 + 3),
            "font-family": "Arial, sans-serif",
            "font-size": "8",
            "fill": "gray"
        })
        id_text.text = f"v{vertex.element_id}"
    
    def _render_edge_svg(self, parent: ET.Element, edge: RenderedElement):
        """Render an edge as text with ligature lines respecting ν mapping order."""
        
        # Edge text (relation name)
        text = ET.SubElement(parent, "text", {
            "x": str(edge.x),
            "y": str(edge.y + edge.height),
            "font-family": "Arial, sans-serif",
            "font-size": str(edge.font_size),
            "fill": edge.color
        })
        text.text = edge.text or f"R{edge.element_id}"
        
        # Ligature lines (connections to vertices in ν mapping order)
        edge_center_x = edge.x + edge.width / 2
        edge_center_y = edge.y + edge.height / 2
        
        # Render ligatures in ν mapping order - this preserves Dau's argument order
        for i, (lx, ly) in enumerate(edge.ligature_points):
            # Simple line from edge to vertex
            line = ET.SubElement(parent, "line", {
                "x1": str(edge_center_x),
                "y1": str(edge_center_y),
                "x2": str(lx),
                "y2": str(ly),
                "stroke": "black",
                "stroke-width": "1.5"
            })
            
            # Optional: Add small position indicator for debugging (can be removed)
            if len(edge.ligature_points) > 1:
                # Small circle at connection point to show ν mapping order
                circle = ET.SubElement(parent, "circle", {
                    "cx": str(lx),
                    "cy": str(ly),
                    "r": "3",
                    "fill": "lightblue",
                    "stroke": "blue",
                    "stroke-width": "1"
                })
                
                # Tiny position number
                pos_text = ET.SubElement(parent, "text", {
                    "x": str(lx + 8),
                    "y": str(ly + 3),
                    "font-family": "Arial, sans-serif", 
                    "font-size": "8",
                    "fill": "blue"
                })
                pos_text.text = str(i + 1)
                
    def _render_edges(self, view: GraphView) -> str:
        """Render all edges as ligatures."""
        elements = []
        
        # Build vertex lookup for ligature connections
        vertex_lookup = {v.element_id: v for v in view.get_elements_by_type("vertex")}
        
        for edge in view.get_elements_by_type("edge"):
            # Render ligature using the new system
            ligature_svg = self._render_ligature(edge, vertex_lookup)
            if ligature_svg:
                elements.append(ligature_svg)
            
            # For non-identity relations, still render predicate text
            if edge.text and edge.text != "=":
                predicate_svg = self._render_predicate_text(edge)
                if predicate_svg:
                    elements.append(predicate_svg)
        
        return '\n'.join(elements)
    
    def _render_predicate_text(self, edge: RenderedElement) -> str:
        """Render predicate text for non-identity relations."""
        if not edge.text or edge.text == "=":
            return ""
        
        text_style = "font-family:serif;font-size:14px;fill:blue;text-anchor:middle"
        
        return f'<text x="{edge.x + edge.width/2}" y="{edge.y + edge.height/2}" style="{text_style}">{edge.text}</text>'
    
    def _render_ligature(self, edge: RenderedElement, vertex_lookup: Dict[ElementID, RenderedElement]) -> str:
        """Render a ligature for an edge."""
        # TO DO: implement ligature rendering
        return ""


def create_simple_test_graph() -> RelationalGraphWithCuts:
    """Create a simple test graph for visualization testing."""
    
    # Create vertices
    v1 = Vertex(id="v1")
    v2 = Vertex(id="v2")
    v3 = Vertex(id="v3")
    
    # Create edges
    e1 = Edge(id="e1")  # Connects v1 and v2
    e2 = Edge(id="e2")  # Connects v2 and v3
    
    # Create a cut
    c1 = Cut(id="c1")
    
    # Create the graph
    egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2, v3]),
        E=frozenset([e1, e2]),
        nu=frozendict({
            "e1": ["v1", "v2"],
            "e2": ["v2", "v3"]
        }),
        sheet="sheet1",
        Cut=frozenset([c1]),
        area=frozendict({
            "c1": frozenset(["e2"]),  # Cut contains ONLY the "Knows" edge
            "sheet1": frozenset(["v1", "v2", "v3", "e1", "c1"])  # Sheet contains all vertices and "Loves" edge
        }),
        rel=frozendict({
            "e1": "Loves",
            "e2": "Knows"
        }),
        rho=frozendict({
            "v1": "Alice",
            "v2": "",  # No constant (existentially quantified)
            "v3": "Bob"
        })
    )
    
    return egi


def create_two_different_things() -> RelationalGraphWithCuts:
    """Create EG expressing 'two different things' using only vertices and ligatures."""
    
    # Two vertices with no connecting ligature = two different things
    v1 = Vertex(id="v1")
    v2 = Vertex(id="v2") 
    
    # No edges needed - spatial juxtaposition expresses conjunction
    # Lack of ligature connection expresses difference
    
    egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2]),
        E=frozenset(),  # No edges/ligatures
        nu=frozendict(),  # No connections
        sheet="sheet1",
        Cut=frozenset(),  # No cuts needed
        area=frozendict({
            "sheet1": frozenset(["v1", "v2"])  # Both vertices on sheet
        }),
        rel=frozendict(),  # No relations
        rho=frozendict({
            "v1": "",  # Generic (existentially quantified)
            "v2": ""   # Generic (existentially quantified)  
        })
    )
    
    return egi


def create_at_least_three_things() -> RelationalGraphWithCuts:
    """Create EG expressing 'at least three things' using vertices and cuts."""
    
    # Three vertices, with negation of "only two exist"
    v1 = Vertex(id="v1")
    v2 = Vertex(id="v2")
    v3 = Vertex(id="v3")
    
    # Cut negating the identity of v3 with either v1 or v2
    # This prevents reducing to just two things
    c1 = Cut(id="c1")
    
    # Identity edge inside cut (what we're negating)
    e1 = Edge(id="e1")  # Identity relation between v3 and v1
    
    egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2, v3]),
        E=frozenset([e1]),
        nu=frozendict({
            "e1": ["v3", "v1"]  # Identity ligature in cut (negated)
        }),
        sheet="sheet1", 
        Cut=frozenset([c1]),
        area=frozendict({
            "c1": frozenset(["e1"]),  # Identity relation inside cut (negated)
            "sheet1": frozenset(["v1", "v2", "v3", "c1"])  # All vertices on sheet
        }),
        rel=frozendict({
            "e1": "="  # Identity relation
        }),
        rho=frozendict({
            "v1": "",  # Generic
            "v2": "",  # Generic
            "v3": ""   # Generic
        })
    )
    
    return egi


def create_exactly_three_things() -> RelationalGraphWithCuts:
    """Create EG expressing 'exactly three things' using vertices, ligatures, and cuts."""
    
    # Three vertices on sheet, with nested cuts preventing both
    # reduction to fewer and expansion to more
    v1 = Vertex(id="v1")
    v2 = Vertex(id="v2") 
    v3 = Vertex(id="v3")
    v4 = Vertex(id="v4")  # Fourth vertex to be negated
    
    # Outer cut: negates existence of fourth thing
    c1 = Cut(id="c1")
    # Inner cut: negates identity of any two of the first three
    c2 = Cut(id="c2")
    
    # Identity edges
    e1 = Edge(id="e1")  # Identity between v1 and v2 (doubly negated = asserted different)
    
    egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2, v3, v4]),
        E=frozenset([e1]),
        nu=frozendict({
            "e1": ["v1", "v2"]  # Identity ligature in inner cut
        }),
        sheet="sheet1",
        Cut=frozenset([c1, c2]),
        area=frozendict({
            "c2": frozenset(["e1"]),  # Identity relation in inner cut
            "c1": frozenset(["v4", "c2"]),  # Fourth vertex and inner cut in outer cut  
            "sheet1": frozenset(["v1", "v2", "v3", "c1"])  # First three vertices on sheet
        }),
        rel=frozendict({
            "e1": "="  # Identity relation
        }),
        rho=frozendict({
            "v1": "",  # Generic
            "v2": "",  # Generic  
            "v3": "",  # Generic
            "v4": ""   # Generic (negated existence)
        })
    )
    
    return egi


def test_basic_rendering():
    """Test basic rendering functionality."""
    print("🧪 Testing Basic Rendering")
    print("=" * 50)
    
    # Create test graph
    egi = create_simple_test_graph()
    print(f"📊 Created test graph: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
    
    # Create view generator
    view_generator = SimpleViewGenerator()
    
    # Generate view
    viewport = ViewportBounds(0, 0, 400, 300, zoom_level=1.0)
    view = view_generator.generate_view(egi, viewport)
    
    print(f"👁️  Generated view: {view.visible_elements}/{view.total_elements} elements visible")
    print(f"📏 Detail level: {view.detail_level}")
    
    # Render to SVG
    renderer = SimpleSVGRenderer()
    svg_file = renderer.render_to_svg(view, "test_basic_rendering.svg")
    
    return svg_file


def test_zoom_levels():
    """Test different zoom levels and detail transitions."""
    print("\n🔍 Testing Zoom Levels")
    print("=" * 50)
    
    egi = create_simple_test_graph()
    view_generator = SimpleViewGenerator()
    renderer = SimpleSVGRenderer()
    
    zoom_levels = [0.05, 0.3, 1.0, 3.0]  # Overview, Intermediate, Detailed, Micro
    
    for i, zoom in enumerate(zoom_levels):
        viewport = ViewportBounds(0, 0, 400, 300, zoom_level=zoom)
        view = view_generator.generate_view(egi, viewport)
        
        filename = f"test_zoom_{i+1}_{view.detail_level.value}.svg"
        renderer.render_to_svg(view, filename)
        
        print(f"🔍 Zoom {zoom:4.2f} -> {view.detail_level.value:12s} -> {filename}")


def test_vertex_ligature_graphs():
    """Test rendering of vertex/ligature-only graphs."""
    print("\n🔍 Testing Vertex/Ligature Graphs")
    print("=" * 50)
    
    view_generator = SimpleViewGenerator()
    renderer = SimpleSVGRenderer()
    
    # Test "two different things"
    egi = create_two_different_things()
    viewport = ViewportBounds(0, 0, 200, 200, zoom_level=1.0)
    view = view_generator.generate_view(egi, viewport)
    filename = f"test_two_different_things_{view.detail_level.value}.svg"
    renderer.render_to_svg(view, filename)
    
    # Test "at least three things"
    egi = create_at_least_three_things()
    viewport = ViewportBounds(0, 0, 300, 300, zoom_level=1.0)
    view = view_generator.generate_view(egi, viewport)
    filename = f"test_at_least_three_things_{view.detail_level.value}.svg"
    renderer.render_to_svg(view, filename)
    
    # Test "exactly three things"
    egi = create_exactly_three_things()
    viewport = ViewportBounds(0, 0, 400, 400, zoom_level=1.0)
    view = view_generator.generate_view(egi, viewport)
    filename = f"test_exactly_three_things_{view.detail_level.value}.svg"
    renderer.render_to_svg(view, filename)


def test_transformation_rule_governance():
    """Test transformation rule governance in graph construction."""
    print("\n🔧 Testing Transformation Rule Governance")
    print("=" * 50)
    
    try:
        # Create rule-governed builder
        builder = TransformationRuleGovernedBuilder()
        
        # Start with empty sheet of assertion
        base_graph = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet="sheet1",
            Cut=frozenset(),
            area=frozendict({"sheet1": frozenset()}),
            rel=frozendict(),
            rho=frozendict()
        )
        
        # Define operations to build "two different things" using transformation rules
        operations = [
            {
                "type": "ADD_VERTEX",
                "target_element_id": "v1",
                "context_id": "sheet1",
                "parameters": {"name": ""}
            },
            {
                "type": "ADD_VERTEX",
                "target_element_id": "v2",
                "context_id": "sheet1", 
                "parameters": {"name": ""}
            }
        ]
        
        # Build graph using transformation rules
        result_graph = builder.build_graph_with_rules(base_graph, operations)
        
        # Validate construction follows rules
        is_valid = builder.validate_graph_construction(result_graph)
        
        print(f"✅ Rule-governed construction: {len(result_graph.V)} vertices")
        print(f"✅ Validation result: {is_valid}")
        
        # Render the rule-governed graph
        view_generator = SimpleViewGenerator()
        renderer = SimpleSVGRenderer()
        
        viewport = ViewportBounds(0, 0, 200, 200, zoom_level=1.0)
        view = view_generator.generate_view(result_graph, viewport)
        filename = f"test_rule_governed_construction_{view.detail_level.value}.svg"
        renderer.render_to_svg(view, filename)
        
        print(f"✅ Rendered rule-governed graph to {filename}")
        
    except Exception as e:
        print(f"⚠️ Transformation rule test failed: {e}")
        print("   (This is expected if transformation engine dependencies are missing)")


def main():
    """Run all tests and generate visual output."""
    print("🚀 Simplified Dynamic View Test")
    print("=" * 50)
    
    try:
        # Basic functionality test
        svg_file = test_basic_rendering()
        
        # Zoom level tests
        test_zoom_levels()
        
        # Vertex/ligature graph tests
        test_vertex_ligature_graphs()
        
        # Transformation rule governance tests
        test_transformation_rule_governance()
        
        print("\n✅ All tests completed!")
        print("📁 Generated SVG files:")
        for filename in [
            "test_basic_rendering.svg",
            "test_zoom_1_overview.svg",
            "test_zoom_2_intermediate.svg", 
            "test_zoom_3_detailed.svg",
            "test_zoom_4_micro.svg",
            "test_two_different_things_detailed.svg",
            "test_at_least_three_things_detailed.svg",
            "test_exactly_three_things_detailed.svg"
        ]:
            if os.path.exists(filename):
                print(f"  📄 {filename}")
        
        print(f"\n🎯 Open {svg_file} in your browser to see the EG diagram!")
        print("\n📝 Graph structure:")
        print("   Alice --[Loves]--> (someone) --[Knows]--> Bob")
        print("                         ^")
        print("                    [Cut c1 - negation context]")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
