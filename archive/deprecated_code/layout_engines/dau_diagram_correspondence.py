"""
Dau-Compliant Diagram-EGI Correspondence Engine

Implements the exact correspondence between EGI logical structure and
diagram representation as specified in Dau's Chapter 12, page 132.

Key Requirements from Dau:
1. N-ary Relation Constraint: n-ary relation → n numbered edge-lines (1...n)
2. Dominating Nodes Constraint: vertex in cut → relation must be in same cut
3. Reconstruction Property: valid diagram → unique EGI (up to isomorphism)

This is a fresh implementation focused solely on Dau's formalism,
avoiding the complexity of previous correspondence attempts.
"""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex


class DiagramElementType(Enum):
    """Types of elements in Dau's diagram representation."""

    VERTEX_SPOT = "vertex_spot"
    EDGE_LINE = "edge_line"
    CUT_LINE = "cut_line"
    RELATION_SIGN = "relation_sign"
    NUMBER_LABEL = "number_label"


@dataclass(frozen=True)
class DiagramElement:
    """A single element in the diagram representation."""

    element_id: str
    element_type: DiagramElementType
    # Minimal spatial info - just containment relationships
    containing_cut: Optional[str] = None  # None means sheet of assertion


@dataclass(frozen=True)
class VertexSpot(DiagramElement):
    """Vertex-spot in diagram (corresponds to EGI vertex)."""

    element_id: str
    element_type: DiagramElementType = DiagramElementType.VERTEX_SPOT
    containing_cut: Optional[str] = None
    label: Optional[str] = None  # None for generic, string for constant
    is_generic: bool = True


@dataclass(frozen=True)
class RelationSign(DiagramElement):
    """Relation-name sign in diagram (corresponds to EGI edge)."""

    element_id: str
    element_type: DiagramElementType = DiagramElementType.RELATION_SIGN
    containing_cut: Optional[str] = None
    relation_name: str = ""
    arity: int = 0  # Number of edge-lines that must be attached


@dataclass(frozen=True)
class EdgeLine(DiagramElement):
    """Edge-line connecting relation-sign to vertex-spot."""

    element_id: str
    element_type: DiagramElementType = DiagramElementType.EDGE_LINE
    containing_cut: Optional[str] = None
    relation_sign_id: str = ""
    vertex_spot_id: str = ""
    position_number: int = 0  # 1, 2, ..., n for n-ary relation


@dataclass(frozen=True)
class CutLine(DiagramElement):
    """Cut-line representing negation context."""

    element_id: str
    element_type: DiagramElementType = DiagramElementType.CUT_LINE
    containing_cut: Optional[str] = None


@dataclass
class DiagramRepresentation:
    """Complete diagram representation following Dau's formalism."""

    sheet_id: str  # The sheet of assertion
    vertex_spots: Dict[str, VertexSpot]
    relation_signs: Dict[str, RelationSign]
    edge_lines: Dict[str, EdgeLine]
    cut_lines: Dict[str, CutLine]

    # Containment relationships (Dau's area mapping equivalent)
    containment: Dict[str, Set[str]]  # area_id -> set of contained element_ids


class ConstraintViolation(Exception):
    """Raised when diagram violates Dau's constraints."""

    pass


class DauDiagramCorrespondence:
    """
    Implements bidirectional correspondence between EGI and diagram representation
    according to Dau's Chapter 12 formalism.
    """

    def validate_diagram_constraints(self, diagram: DiagramRepresentation) -> bool:
        """
        Validate diagram satisfies Dau's two critical constraints.

        Returns True if valid, raises ConstraintViolation with details if invalid.
        """
        self._validate_nary_relation_constraint(diagram)
        self._validate_dominating_nodes_constraint(diagram)
        return True

    def _validate_nary_relation_constraint(
        self, diagram: DiagramRepresentation
    ) -> None:
        """
        Constraint 1: If relation-name sign for n-ary relation occurs,
        then there are n edge-lines numbered 1...n attached to it.
        """
        for relation_id, relation_sign in diagram.relation_signs.items():
            # Find all edge-lines attached to this relation
            attached_lines = [
                line
                for line in diagram.edge_lines.values()
                if line.relation_sign_id == relation_id
            ]

            # Check count matches arity
            if len(attached_lines) != relation_sign.arity:
                raise ConstraintViolation(
                    f"Relation '{relation_sign.relation_name}' has arity {relation_sign.arity} "
                    f"but {len(attached_lines)} edge-lines attached"
                )

            # Check numbering is complete 1...n
            position_numbers = {line.position_number for line in attached_lines}
            expected_numbers = set(range(1, relation_sign.arity + 1))

            if position_numbers != expected_numbers:
                raise ConstraintViolation(
                    f"Relation '{relation_sign.relation_name}' edge-lines have positions "
                    f"{sorted(position_numbers)} but should be {sorted(expected_numbers)}"
                )

    def _validate_dominating_nodes_constraint(
        self, diagram: DiagramRepresentation
    ) -> None:
        """
        Constraint 2: If vertex-spot connected to relation-sign is enclosed by cut-line,
        then relation-sign must also be enclosed by that cut-line.
        """
        for edge_line in diagram.edge_lines.values():
            vertex_spot = diagram.vertex_spots[edge_line.vertex_spot_id]
            relation_sign = diagram.relation_signs[edge_line.relation_sign_id]

            # If vertex is in a cut, relation must be in same cut or containing cut
            if vertex_spot.containing_cut is not None:
                if not self._is_dominated_by(
                    relation_sign.containing_cut, vertex_spot.containing_cut, diagram
                ):
                    raise ConstraintViolation(
                        f"Vertex '{vertex_spot.element_id}' in cut '{vertex_spot.containing_cut}' "
                        f"connected to relation '{relation_sign.element_id}' in cut "
                        f"'{relation_sign.containing_cut}' - violates dominating nodes constraint"
                    )

    def _is_dominated_by(
        self,
        relation_cut: Optional[str],
        vertex_cut: Optional[str],
        diagram: DiagramRepresentation,
    ) -> bool:
        """
        Check if relation dominates vertex per Dau's Definition 12.5.
        Dominating nodes: ctx(e) ≤ ctx(v) for every edge e and vertex v in Ve.
        This means edge context must be same or more nested than vertex context.
        """
        # Both on sheet - valid
        if relation_cut is None and vertex_cut is None:
            return True

        # Relation on sheet, vertex in cut - INVALID (sheet context < cut context)
        if relation_cut is None and vertex_cut is not None:
            return False

        # Relation in cut, vertex on sheet - valid (cut context ≥ sheet context)
        if relation_cut is not None and vertex_cut is None:
            return True

        # Both in cuts - same cut is valid
        if relation_cut == vertex_cut:
            return True

        # Different cuts - relation must be in same or more nested cut than vertex
        # Check if relation_cut is contained within or equal to vertex_cut's nesting
        return self._cut_contains_cut(vertex_cut, relation_cut, diagram)

    def _cut_contains_cut(
        self, outer_cut: str, inner_cut: str, diagram: DiagramRepresentation
    ) -> bool:
        """Check if outer_cut contains inner_cut in nesting hierarchy."""
        # Walk up from inner_cut to see if we reach outer_cut
        current_cut = inner_cut
        visited = set()

        while current_cut is not None and current_cut not in visited:
            visited.add(current_cut)

            # Find what contains current_cut
            containing_area = None
            for area_id, contents in diagram.containment.items():
                if current_cut in contents:
                    containing_area = area_id
                    break

            if containing_area == outer_cut:
                return True

            # Move up to containing area (if it's a cut)
            current_cut = (
                containing_area if containing_area in diagram.cut_lines else None
            )

        return False

    def diagram_to_egi(self, diagram: DiagramRepresentation) -> RelationalGraphWithCuts:
        """
        Reconstruct EGI from valid diagram (Dau's reconstruction property).

        Assumes diagram has been validated with validate_diagram_constraints().
        """
        # Build vertices from vertex-spots
        vertices = frozenset(
            Vertex(id=spot.element_id, label=spot.label, is_generic=spot.is_generic)
            for spot in diagram.vertex_spots.values()
        )

        # Build edges from relation-signs
        edges = frozenset(
            Edge(id=sign.element_id) for sign in diagram.relation_signs.values()
        )

        # Build cuts from cut-lines
        cuts = frozenset(Cut(id=cut.element_id) for cut in diagram.cut_lines.values())

        # Build ν mapping from edge-lines
        nu_mapping = {}
        for relation_id, relation_sign in diagram.relation_signs.items():
            # Get edge-lines for this relation, sorted by position
            relation_lines = [
                line
                for line in diagram.edge_lines.values()
                if line.relation_sign_id == relation_id
            ]
            relation_lines.sort(key=lambda line: line.position_number)

            # Create vertex sequence
            vertex_sequence = tuple(line.vertex_spot_id for line in relation_lines)
            nu_mapping[relation_id] = vertex_sequence

        # Build relation mapping
        rel_mapping = {
            sign.element_id: sign.relation_name
            for sign in diagram.relation_signs.values()
        }

        # Build area mapping from containment
        area_mapping = {}

        # Sheet contains everything not in a cut
        sheet_contents = set()
        for element_type_dict in [
            diagram.vertex_spots,
            diagram.relation_signs,
            diagram.cut_lines,
        ]:
            for element in element_type_dict.values():
                if element.containing_cut is None:
                    sheet_contents.add(element.element_id)
        area_mapping[diagram.sheet_id] = frozenset(sheet_contents)

        # Each cut contains its contents
        for cut_id in diagram.cut_lines:
            cut_contents = set()
            for element_type_dict in [
                diagram.vertex_spots,
                diagram.relation_signs,
                diagram.cut_lines,
            ]:
                for element in element_type_dict.values():
                    if element.containing_cut == cut_id:
                        cut_contents.add(element.element_id)
            area_mapping[cut_id] = frozenset(cut_contents)

        return RelationalGraphWithCuts(
            V=vertices,
            E=edges,
            nu=frozendict(nu_mapping),
            sheet=diagram.sheet_id,
            Cut=cuts,
            area=frozendict(area_mapping),
            rel=frozendict(rel_mapping),
        )

    def egi_to_diagram(self, egi: RelationalGraphWithCuts) -> DiagramRepresentation:
        """
        Generate valid diagram from EGI.

        Creates diagram elements that satisfy Dau's constraints.
        """
        # Create vertex-spots from vertices
        vertex_spots = {}
        for vertex in egi.V:
            containing_cut = self._find_containing_cut(vertex.id, egi)
            vertex_spots[vertex.id] = VertexSpot(
                element_id=vertex.id,
                label=vertex.label,
                is_generic=vertex.is_generic,
                containing_cut=containing_cut,
            )

        # Create relation-signs from edges
        relation_signs = {}
        for edge in egi.E:
            containing_cut = self._find_containing_cut(edge.id, egi)
            vertex_sequence = egi.nu[edge.id]
            relation_signs[edge.id] = RelationSign(
                element_id=edge.id,
                relation_name=egi.rel[edge.id],
                arity=len(vertex_sequence),
                containing_cut=containing_cut,
            )

        # Create edge-lines from ν mapping
        edge_lines = {}
        for edge_id, vertex_sequence in egi.nu.items():
            for position, vertex_id in enumerate(vertex_sequence, 1):
                line_id = f"{edge_id}_to_{vertex_id}_{position}"
                edge_lines[line_id] = EdgeLine(
                    element_id=line_id,
                    relation_sign_id=edge_id,
                    vertex_spot_id=vertex_id,
                    position_number=position,
                )

        # Create cut-lines from cuts
        cut_lines = {}
        for cut in egi.Cut:
            cut_lines[cut.id] = CutLine(element_id=cut.id)

        # Build containment from area mapping
        containment = {}
        for area_id, contents in egi.area.items():
            containment[area_id] = set(contents)

        return DiagramRepresentation(
            sheet_id=egi.sheet,
            vertex_spots=vertex_spots,
            relation_signs=relation_signs,
            edge_lines=edge_lines,
            cut_lines=cut_lines,
            containment=containment,
        )

    def _find_containing_cut(
        self, element_id: str, egi: RelationalGraphWithCuts
    ) -> Optional[str]:
        """Find the cut that directly contains an element (None if on sheet)."""
        for area_id, contents in egi.area.items():
            if element_id in contents and area_id != egi.sheet:
                return area_id
        return None

    def calculate_graph_aware_layout(
        self, diagram: DiagramRepresentation
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calculate spatial positions that understand predicate relationships.

        Creates readable horizontal layouts like "cat---on---mat" by analyzing
        the logical structure of relations and their connections.

        Returns: Dict mapping element_id -> (x, y) position
        """
        positions = {}

        # Build connection graph to understand relationships
        connection_graph = self._build_connection_graph(diagram)

        # Create linear chain following connections
        chain = self._build_element_chain(diagram, connection_graph)

        # Position elements horizontally with proper spacing
        x_start = 100
        y_center = 200
        element_spacing = 120

        current_x = x_start
        for element_id in chain:
            positions[element_id] = (current_x, y_center)
            current_x += element_spacing

        # Position any unconnected elements
        for vertex_id in diagram.vertex_spots:
            if vertex_id not in positions:
                positions[vertex_id] = (current_x, y_center)
                current_x += element_spacing

        for relation_id in diagram.relation_signs:
            if relation_id not in positions:
                positions[relation_id] = (current_x, y_center)
                current_x += element_spacing

        return positions

    def _build_connection_graph(
        self, diagram: DiagramRepresentation
    ) -> Dict[str, List[str]]:
        """Build adjacency graph of element connections."""
        connections = {}

        # Initialize all elements
        for element_id in diagram.vertex_spots:
            connections[element_id] = []
        for element_id in diagram.relation_signs:
            connections[element_id] = []

        # Add connections from edge-lines
        for edge_line in diagram.edge_lines.values():
            vertex_id = edge_line.vertex_spot_id
            relation_id = edge_line.relation_sign_id

            connections[vertex_id].append(relation_id)
            connections[relation_id].append(vertex_id)

        return connections

    def _build_element_chain(
        self, diagram: DiagramRepresentation, connections: Dict[str, List[str]]
    ) -> List[str]:
        """Build linear chain alternating vertex-relation-vertex for readability."""
        chain = []
        used = set()

        # Start with first vertex
        vertices = list(diagram.vertex_spots.keys())
        if not vertices:
            return list(diagram.relation_signs.keys())

        current = vertices[0]
        chain.append(current)
        used.add(current)

        # Follow connections to build chain
        while True:
            # Find connected element not yet used
            next_element = None
            for connected in connections.get(current, []):
                if connected not in used:
                    next_element = connected
                    break

            if next_element is None:
                break

            chain.append(next_element)
            used.add(next_element)
            current = next_element

        return chain
