"""
Clean EGI → Qt Diagram Renderer

Pure implementation using only Dau's formalism from egi_core_dau.py
and dau_diagram_correspondence.py. No legacy code contamination.

Architecture:
EGI (Dau 6+1 components) → DiagramRepresentation → Qt Graphics Items

This renderer focuses solely on the logical → visual correspondence
without spatial layout algorithms or legacy EGDF dependencies.
"""

import json
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
)

from dau_diagram_correspondence import (
    CutLine,
    DauDiagramCorrespondence,
    DiagramRepresentation,
    EdgeLine,
    RelationSign,
    VertexSpot,
)
from egi_core_dau import RelationalGraphWithCuts


class CleanDiagramRenderer:
    """
    Pure EGI → Qt diagram renderer using Dau's formalism.

    Renders EGI logical structure as Qt graphics items following
    Dau Chapter 12 correspondence rules with proper styling.
    """

    def __init__(self, style_config=None):
        self.correspondence = DauDiagramCorrespondence()
        self.scene = None
        self.current_egi = None
        self.current_diagram = None

        # Load styling configuration
        self.style = self._load_style_config(style_config)

        # Layout parameters from style
        self.vertex_radius = (
            self.style.get("vertex", {}).get("dot", {}).get("radius", 3)
        )
        self.cut_padding = self.style.get("layout", {}).get("cut_padding", 20.0)
        self.element_spacing = self.style.get("layout", {}).get(
            "sibling_shift", [40.0, 30.0]
        )[0]
        self.ligature_approach_margin = self.style.get("layout", {}).get(
            "ligature_approach_margin", 4.0
        )

    def _load_style_config(self, style_config):
        """Load style configuration from file or use default."""
        if style_config is None:
            # Load default.json
            import json
            import os

            style_path = os.path.join(
                os.path.dirname(__file__), "..", "styles", "default.json"
            )
            try:
                with open(style_path, "r") as f:
                    return json.load(f)
            except:
                # Fallback to minimal style
                return {
                    "vertex": {
                        "dot": {
                            "radius": 3,
                            "fill_color": "#000000",
                            "border_color": "#000000",
                        }
                    },
                    "ligature": {"arm": {"line_color": "#000000", "line_width": 3}},
                    "layout": {
                        "cut_padding": 20.0,
                        "sibling_shift": [40.0, 30.0],
                        "ligature_approach_margin": 4.0,
                    },
                }
        return style_config

    def render_egi_to_scene(
        self, egi: RelationalGraphWithCuts, scene: QGraphicsScene
    ) -> None:
        """
        Render EGI to Qt graphics scene using pure Dau correspondence.

        Steps:
        1. Convert EGI → DiagramRepresentation (pure logical mapping)
        2. Generate simple spatial layout
        3. Create Qt graphics items
        """
        self.current_egi = egi
        self.scene = scene

        # Clear scene
        self.scene.clear()

        # Convert to diagram representation
        self.current_diagram = self.correspondence.egi_to_diagram(egi)

        # Validate diagram constraints
        try:
            self.correspondence.validate_diagram_constraints(self.current_diagram)
        except Exception as e:
            print(f"[CleanDiagramRenderer] Diagram constraint violation: {e}")
            return

        # Calculate graph-aware layout using correspondence layer
        layout_positions = self.correspondence.calculate_graph_aware_layout(
            self.current_diagram
        )
        layout = {
            elem_id: QPointF(x, y) for elem_id, (x, y) in layout_positions.items()
        }

        # Render elements
        self._render_cuts(layout)
        self._render_vertices(layout)
        self._render_relations(layout)
        self._render_edge_lines(layout)

        print(
            f"[CleanDiagramRenderer] Rendered EGI with {len(egi.V)} vertices, "
            f"{len(egi.E)} edges, {len(egi.Cut)} cuts"
        )

    def _calculate_layout(self) -> Dict[str, QPointF]:
        """Calculate positions for all diagram elements in readable horizontal layout."""
        layout = {}

        # Analyze the graph structure to create linear layout
        relations = list(self.current_diagram.relation_signs.keys())
        vertices = list(self.current_diagram.vertex_spots.keys())

        if not relations:
            # Simple vertex layout if no relations
            for i, vertex_id in enumerate(vertices):
                layout[vertex_id] = QPointF(100 + i * 150, 200)
            return layout

        # Create horizontal chain layout: vertex - relation - vertex - relation - vertex
        x_start = 100
        y_center = 200
        element_spacing = 120  # Space between elements

        # Build the chain by following edge connections
        chain = self._build_element_chain()

        # Position elements along the chain
        current_x = x_start
        for element_id in chain:
            layout[element_id] = QPointF(current_x, y_center)
            current_x += element_spacing

        # Position any remaining unconnected elements
        for vertex_id in vertices:
            if vertex_id not in layout:
                layout[vertex_id] = QPointF(current_x, y_center)
                current_x += element_spacing

        for relation_id in relations:
            if relation_id not in layout:
                layout[relation_id] = QPointF(current_x, y_center)
                current_x += element_spacing

        # Position cuts (if any) - above the main chain
        cut_y = y_center - 100
        cut_x = x_start
        for cut_id in self.current_diagram.cut_lines.keys():
            layout[cut_id] = QPointF(cut_x, cut_y)
            cut_x += element_spacing

        return layout

    def _build_element_chain(self) -> List[str]:
        """Build a linear chain of alternating vertices and relations."""
        chain = []
        used_vertices = set()
        used_relations = set()

        # Start with first vertex
        vertices = list(self.current_diagram.vertex_spots.keys())
        relations = list(self.current_diagram.relation_signs.keys())

        if not vertices:
            return list(relations)

        # Start chain with first vertex
        current_vertex = vertices[0]
        chain.append(current_vertex)
        used_vertices.add(current_vertex)

        # Alternate between finding connected relations and vertices
        while len(used_relations) < len(relations) or len(used_vertices) < len(
            vertices
        ):
            # Find relation connected to current vertex
            connected_relation = None
            for edge_id, edge_line in self.current_diagram.edge_lines.items():
                if (
                    edge_line.vertex_spot_id == current_vertex
                    and edge_line.relation_sign_id not in used_relations
                ):
                    connected_relation = edge_line.relation_sign_id
                    break

            if connected_relation:
                chain.append(connected_relation)
                used_relations.add(connected_relation)

                # Find another vertex connected to this relation
                next_vertex = None
                for edge_id, edge_line in self.current_diagram.edge_lines.items():
                    if (
                        edge_line.relation_sign_id == connected_relation
                        and edge_line.vertex_spot_id != current_vertex
                        and edge_line.vertex_spot_id not in used_vertices
                    ):
                        next_vertex = edge_line.vertex_spot_id
                        break

                if next_vertex:
                    chain.append(next_vertex)
                    used_vertices.add(next_vertex)
                    current_vertex = next_vertex
                else:
                    break
            else:
                break

        return chain

    def _render_vertices(self, layout: Dict[str, QPointF]) -> None:
        """Render vertex-spots as styled circles."""
        vertex_style = self.style.get("vertex", {}).get("dot", {})
        fill_color = vertex_style.get("fill_color", "#000000")
        border_color = vertex_style.get("border_color", "#000000")
        border_width = vertex_style.get("border_width", 1)

        for vertex_id, vertex_spot in self.current_diagram.vertex_spots.items():
            pos = layout.get(vertex_id, QPointF(0, 0))

            # Create circle with style
            vertex_item = QGraphicsEllipseItem(
                -self.vertex_radius,
                -self.vertex_radius,
                2 * self.vertex_radius,
                2 * self.vertex_radius,
            )
            vertex_item.setPos(pos)
            vertex_item.setBrush(QBrush(QColor(fill_color)))
            vertex_item.setPen(QPen(QColor(border_color), border_width))
            vertex_item.setFlags(
                vertex_item.GraphicsItemFlag.ItemIsMovable
                | vertex_item.GraphicsItemFlag.ItemIsSelectable
            )

            # Store element ID for interaction
            vertex_item.setData(0, vertex_id)
            vertex_item.setData(1, "vertex")

            self.scene.addItem(vertex_item)

            # Add label if constant vertex
            if not vertex_spot.is_generic and vertex_spot.label:
                label_style = self.style.get("vertex", {}).get("label_text", {})
                font_size = label_style.get("font_size", 9)
                offset = label_style.get("offset", [-18, -16])

                label_item = QGraphicsTextItem(vertex_spot.label)
                label_item.setPos(pos.x() + offset[0], pos.y() + offset[1])
                label_item.setFont(QFont("Arial", font_size))
                self.scene.addItem(label_item)

    def _render_relations(self, layout: Dict[str, QPointF]) -> None:
        """Render relation-signs as text labels."""
        for relation_id, relation_sign in self.current_diagram.relation_signs.items():
            pos = layout.get(relation_id, QPointF(0, 0))

            # Create text item
            relation_item = QGraphicsTextItem(relation_sign.relation_name)
            relation_item.setPos(pos)
            relation_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            relation_item.setDefaultTextColor(QColor("blue"))
            relation_item.setFlags(
                relation_item.GraphicsItemFlag.ItemIsMovable
                | relation_item.GraphicsItemFlag.ItemIsSelectable
            )

            # Store element ID for interaction
            relation_item.setData(0, relation_id)
            relation_item.setData(1, "relation")

            self.scene.addItem(relation_item)

    def _render_edge_lines(self, layout: Dict[str, QPointF]) -> None:
        """Render edge-lines as styled ligatures with collision avoidance."""
        ligature_style = self.style.get("ligature", {}).get("arm", {})
        line_color = ligature_style.get("line_color", "#000000")
        line_width = ligature_style.get("line_width", 3)

        for line_id, edge_line in self.current_diagram.edge_lines.items():
            relation_pos = layout.get(edge_line.relation_sign_id, QPointF(0, 0))
            vertex_pos = layout.get(edge_line.vertex_spot_id, QPointF(0, 0))

            # Generate collision-free path
            path_points = self._generate_ligature_path(relation_pos, vertex_pos, layout)

            # Create ligature as series of connected lines
            for i in range(len(path_points) - 1):
                start_point = path_points[i]
                end_point = path_points[i + 1]

                line_item = QGraphicsLineItem(
                    start_point.x(), start_point.y(), end_point.x(), end_point.y()
                )
                line_item.setPen(
                    QPen(
                        QColor(line_color),
                        line_width,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                    )
                )

                # Store element ID for interaction
                line_item.setData(0, line_id)
                line_item.setData(1, "edge_line")

                self.scene.addItem(line_item)

            # Add position number label with styling
            superscript_style = self.style.get("edge", {}).get("superscript_text", {})
            font_size = superscript_style.get("font_size", 9)
            color = superscript_style.get("color", "#CC0000")

            mid_point = (
                path_points[len(path_points) // 2] if path_points else relation_pos
            )

            number_item = QGraphicsTextItem(str(edge_line.position_number))
            number_item.setPos(mid_point.x() + 5, mid_point.y() - 10)
            number_item.setFont(QFont("Arial", font_size))
            number_item.setDefaultTextColor(QColor(color))

            self.scene.addItem(number_item)

    def _generate_ligature_path(
        self, start: QPointF, end: QPointF, layout: Dict[str, QPointF]
    ) -> List[QPointF]:
        """Generate collision-free path for ligature using simple routing."""
        # Check if direct path intersects any relation text
        if not self._path_intersects_relations(start, end, layout):
            return [start, end]

        # Simple curved path to avoid intersections
        mid_x = (start.x() + end.x()) / 2
        mid_y = min(start.y(), end.y()) - 30  # Curve above

        # Check if curved path is better
        curve_point = QPointF(mid_x, mid_y)
        if not self._path_intersects_relations(
            start, curve_point, layout
        ) and not self._path_intersects_relations(curve_point, end, layout):
            return [start, curve_point, end]

        # Fallback: curve below
        mid_y = max(start.y(), end.y()) + 30
        curve_point = QPointF(mid_x, mid_y)
        return [start, curve_point, end]

    def _path_intersects_relations(
        self, start: QPointF, end: QPointF, layout: Dict[str, QPointF]
    ) -> bool:
        """Check if path intersects any relation text boxes."""
        for relation_id, relation_sign in self.current_diagram.relation_signs.items():
            relation_pos = layout.get(relation_id, QPointF(0, 0))

            # Estimate text bounding box
            text_width = len(relation_sign.relation_name) * 8  # Rough estimate
            text_height = 14
            padding = self.ligature_approach_margin

            # Check if line intersects text rectangle
            if self._line_intersects_rect(
                start, end, relation_pos, text_width + padding, text_height + padding
            ):
                return True

        return False

    def _line_intersects_rect(
        self,
        line_start: QPointF,
        line_end: QPointF,
        rect_center: QPointF,
        rect_width: float,
        rect_height: float,
    ) -> bool:
        """Check if line segment intersects rectangle."""
        # Simple bounding box intersection test
        rect_left = rect_center.x() - rect_width / 2
        rect_right = rect_center.x() + rect_width / 2
        rect_top = rect_center.y() - rect_height / 2
        rect_bottom = rect_center.y() + rect_height / 2

        # Check if line endpoints are on opposite sides of rectangle
        line_min_x = min(line_start.x(), line_end.x())
        line_max_x = max(line_start.x(), line_end.x())
        line_min_y = min(line_start.y(), line_end.y())
        line_max_y = max(line_start.y(), line_end.y())

        # Basic intersection test
        return not (
            line_max_x < rect_left
            or line_min_x > rect_right
            or line_max_y < rect_top
            or line_min_y > rect_bottom
        )

    def _render_cuts(self, layout: Dict[str, QPointF]) -> None:
        """Render cut-lines as rectangles."""
        for cut_id, cut_line in self.current_diagram.cut_lines.items():
            pos = layout.get(cut_id, QPointF(0, 0))

            # Calculate cut size based on contents
            contents = self.current_diagram.containment.get(cut_id, set())
            if contents:
                # Find bounding box of contents
                content_positions = [
                    layout.get(elem_id) for elem_id in contents if elem_id in layout
                ]
                if content_positions:
                    min_x = min(pos.x() for pos in content_positions) - self.cut_padding
                    max_x = max(pos.x() for pos in content_positions) + self.cut_padding
                    min_y = min(pos.y() for pos in content_positions) - self.cut_padding
                    max_y = max(pos.y() for pos in content_positions) + self.cut_padding

                    width = max_x - min_x + 2 * self.cut_padding
                    height = max_y - min_y + 2 * self.cut_padding
                else:
                    width = height = 100
            else:
                width = height = 100

            # Create rectangle
            cut_item = QGraphicsRectItem(0, 0, width, height)
            cut_item.setPos(pos)
            cut_item.setBrush(QBrush(QColor(255, 255, 255, 0)))  # Transparent
            cut_item.setPen(QPen(QColor("black"), 2))
            cut_item.setFlags(
                cut_item.GraphicsItemFlag.ItemIsMovable
                | cut_item.GraphicsItemFlag.ItemIsSelectable
            )

            # Store element ID for interaction
            cut_item.setData(0, cut_id)
            cut_item.setData(1, "cut")

            self.scene.addItem(cut_item)

    def get_element_at_position(self, scene_pos: QPointF) -> Optional[Tuple[str, str]]:
        """
        Get element ID and type at scene position.

        Returns (element_id, element_type) or None if no element found.
        """
        if not self.scene:
            return None

        items = self.scene.items(scene_pos)
        for item in items:
            element_id = item.data(0)
            element_type = item.data(1)
            if element_id and element_type:
                return (element_id, element_type)

        return None

    def highlight_element(self, element_id: str, highlight: bool = True) -> None:
        """Highlight/unhighlight element in scene."""
        if not self.scene:
            return

        color = QColor("yellow") if highlight else QColor("white")

        for item in self.scene.items():
            if item.data(0) == element_id:
                if hasattr(item, "setBrush"):
                    item.setBrush(QBrush(color))
                break


if __name__ == "__main__":
    # Test the clean renderer
    from egi_core_dau import create_cut, create_edge, create_empty_graph, create_vertex

    print("=== Testing Clean Diagram Renderer ===")

    # Create test EGI
    graph = create_empty_graph()

    # Add vertices
    v1 = create_vertex(label=None, is_generic=True)
    v2 = create_vertex(label="Socrates", is_generic=False)
    graph = graph.with_vertex(v1).with_vertex(v2)

    # Add relation
    edge = create_edge()
    graph = graph.with_edge(edge, (v1.id, v2.id), "loves")

    # Add cut
    cut = create_cut()
    graph = graph.with_cut(cut)

    print(
        f"✓ Created test EGI: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts"
    )

    # Test renderer (without Qt app)
    renderer = CleanDiagramRenderer()
    correspondence = DauDiagramCorrespondence()

    # Test EGI → diagram conversion
    diagram = correspondence.egi_to_diagram(graph)
    print(
        f"✓ Converted to diagram: {len(diagram.vertex_spots)} vertex-spots, "
        f"{len(diagram.relation_signs)} relation-signs"
    )

    # Test constraint validation
    try:
        correspondence.validate_diagram_constraints(diagram)
        print("✓ Diagram constraints validated")
    except Exception as e:
        print(f"✗ Constraint violation: {e}")

    print("=== Clean Renderer Test Complete ===")
