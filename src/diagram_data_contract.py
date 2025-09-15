"""
Standardized data contract for diagram elements and positioning.

This module defines the canonical data structures used throughout the Arisbe system
for representing diagram elements, their positions, and their relationships.
No more guessing about dict vs list - this is the single source of truth.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QPointF, QRectF


@dataclass
class ElementPosition:
    """Canonical position representation for any diagram element."""

    x: float
    y: float

    def to_qpointf(self) -> QPointF:
        return QPointF(self.x, self.y)

    @classmethod
    def from_qpointf(cls, point: QPointF) -> "ElementPosition":
        return cls(point.x(), point.y())


@dataclass
class ElementSize:
    """Canonical size representation for diagram elements."""

    width: float
    height: float

    def to_qrectf(self, position: ElementPosition) -> QRectF:
        return QRectF(position.x, position.y, self.width, self.height)


@dataclass
class VertexElement:
    """Canonical vertex representation."""

    id: str
    position: ElementPosition
    area_id: str = "sheet"
    label_kind: Optional[str] = None
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.position.x,
            "y": self.position.y,
            "area_id": self.area_id,
            "label_kind": self.label_kind,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VertexElement":
        return cls(
            id=data["id"],
            position=ElementPosition(data.get("x", 0), data.get("y", 0)),
            area_id=data.get("area_id", "sheet"),
            label_kind=data.get("label_kind"),
            label=data.get("label"),
        )


@dataclass
class PredicateElement:
    """Canonical predicate representation."""

    id: str
    name: str
    position: ElementPosition
    area_id: str = "sheet"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "text": self.name,  # Legacy compatibility
            "x": self.position.x,
            "y": self.position.y,
            "area_id": self.area_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PredicateElement":
        name = data.get("name") or data.get("text", data.get("id", ""))
        return cls(
            id=data["id"],
            name=name,
            position=ElementPosition(data.get("x", 0), data.get("y", 0)),
            area_id=data.get("area_id", "sheet"),
        )


@dataclass
class CutElement:
    """Canonical cut representation."""

    id: str
    position: ElementPosition
    size: ElementSize
    area_id: str = "sheet"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.position.x,
            "y": self.position.y,
            "w": self.size.width,
            "h": self.size.height,
            "width": self.size.width,  # Legacy compatibility
            "height": self.size.height,  # Legacy compatibility
            "area_id": self.area_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CutElement":
        width = data.get("width") or data.get("w", 100)
        height = data.get("height") or data.get("h", 100)
        return cls(
            id=data["id"],
            position=ElementPosition(data.get("x", 0), data.get("y", 0)),
            size=ElementSize(width, height),
            area_id=data.get("area_id", "sheet"),
        )


@dataclass
class DiagramState:
    """Canonical diagram state representation."""

    vertices: Dict[str, VertexElement]
    predicates: Dict[str, PredicateElement]
    cuts: Dict[str, CutElement]
    ligatures: List[Dict[str, Any]]  # Keep as-is for now

    def to_drawing_schema(self) -> Dict[str, Any]:
        """Convert to drawing schema format for EGI adapter."""
        return {
            "vertices": [v.to_dict() for v in self.vertices.values()],
            "predicates": [p.to_dict() for p in self.predicates.values()],
            "cuts": [c.to_dict() for c in self.cuts.values()],
            "ligatures": self.ligatures,
        }

    @classmethod
    def from_drawing_schema(cls, schema: Dict[str, Any]) -> "DiagramState":
        """Create from drawing schema, handling both dict and list formats."""
        vertices = {}
        predicates = {}
        cuts = {}

        # Handle vertices
        vertices_data = schema.get("vertices", [])
        if isinstance(vertices_data, dict):
            for vid, vdata in vertices_data.items():
                vdata["id"] = vid  # Ensure ID is set
                vertices[vid] = VertexElement.from_dict(vdata)
        elif isinstance(vertices_data, list):
            for vdata in vertices_data:
                if isinstance(vdata, dict) and "id" in vdata:
                    vertices[vdata["id"]] = VertexElement.from_dict(vdata)

        # Handle predicates
        predicates_data = schema.get("predicates", [])
        if isinstance(predicates_data, dict):
            for pid, pdata in predicates_data.items():
                pdata["id"] = pid  # Ensure ID is set
                predicates[pid] = PredicateElement.from_dict(pdata)
        elif isinstance(predicates_data, list):
            for pdata in predicates_data:
                if isinstance(pdata, dict) and "id" in pdata:
                    predicates[pdata["id"]] = PredicateElement.from_dict(pdata)

        # Handle cuts
        cuts_data = schema.get("cuts", [])
        if isinstance(cuts_data, dict):
            for cid, cdata in cuts_data.items():
                cdata["id"] = cid  # Ensure ID is set
                cuts[cid] = CutElement.from_dict(cdata)
        elif isinstance(cuts_data, list):
            for cdata in cuts_data:
                if isinstance(cdata, dict) and "id" in cdata:
                    cuts[cdata["id"]] = CutElement.from_dict(cdata)

        return cls(
            vertices=vertices,
            predicates=predicates,
            cuts=cuts,
            ligatures=schema.get("ligatures", []),
        )

    def add_vertex(self, vertex_id: str, x: float, y: float) -> None:
        """Add a vertex at the specified position."""
        self.vertices[vertex_id] = VertexElement(
            id=vertex_id, position=ElementPosition(x, y)
        )

    def add_predicate(self, predicate_id: str, name: str, x: float, y: float) -> None:
        """Add a predicate at the specified position."""
        self.predicates[predicate_id] = PredicateElement(
            id=predicate_id, name=name, position=ElementPosition(x, y)
        )

    def add_cut(
        self, cut_id: str, x: float, y: float, width: float = 100, height: float = 100
    ) -> None:
        """Add a cut at the specified position with the specified size."""
        self.cuts[cut_id] = CutElement(
            id=cut_id, position=ElementPosition(x, y), size=ElementSize(width, height)
        )

    def update_element_position(self, element_id: str, x: float, y: float) -> bool:
        """Update position of any element by ID. Returns True if found and updated."""
        if element_id in self.vertices:
            self.vertices[element_id].position = ElementPosition(x, y)
            return True
        elif element_id in self.predicates:
            self.predicates[element_id].position = ElementPosition(x, y)
            return True
        elif element_id in self.cuts:
            self.cuts[element_id].position = ElementPosition(x, y)
            return True
        return False

    def update_cut_size(self, cut_id: str, width: float, height: float) -> bool:
        """Update size of a cut. Returns True if found and updated."""
        if cut_id in self.cuts:
            self.cuts[cut_id].size = ElementSize(width, height)
            return True
        return False

    def get_element_position(self, element_id: str) -> Optional[ElementPosition]:
        """Get position of any element by ID."""
        if element_id in self.vertices:
            return self.vertices[element_id].position
        elif element_id in self.predicates:
            return self.predicates[element_id].position
        elif element_id in self.cuts:
            return self.cuts[element_id].position
        return None


class DiagramDataContract:
    """
    Standardized contract for all diagram data operations.

    This class enforces consistent data handling across the entire system.
    No more dict/list confusion - everything goes through this contract.
    """

    @staticmethod
    def normalize_drawing_schema(schema: Dict[str, Any]) -> DiagramState:
        """Convert any drawing schema format to canonical DiagramState."""
        return DiagramState.from_drawing_schema(schema)

    @staticmethod
    def to_egi_format(state: DiagramState) -> Dict[str, Any]:
        """Convert DiagramState to EGI adapter format."""
        return state.to_drawing_schema()

    @staticmethod
    def create_empty_state() -> DiagramState:
        """Create an empty diagram state."""
        return DiagramState(vertices={}, predicates={}, cuts={}, ligatures=[])
