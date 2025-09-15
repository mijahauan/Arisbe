"""
EGI-Centered Data Transfer Object for standardized inter-module communication.

This module defines the canonical DTO format that all Arisbe modules should use
for exchanging graph data. It eliminates the list/dict inconsistencies by
providing a single, EGI-based schema.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from egi_core_dau import Cut, Edge, RelationalGraphWithCuts, Vertex


@dataclass
class SpatialInfo:
    """Spatial positioning and dimensions for diagram elements."""

    x: float
    y: float
    width: float = 150.0  # Default cut width
    height: float = 100.0  # Default cut height


@dataclass
class EGIElementDTO:
    """Base DTO for EGI elements with spatial information."""

    id: str
    spatial: Optional[SpatialInfo] = None
    area_id: str = "sheet"  # Which logical area contains this element


@dataclass
class VertexDTO(EGIElementDTO):
    """Vertex with spatial positioning."""

    label: Optional[str] = None
    is_generic: bool = True
    radius: float = 8.0


@dataclass
class EdgeDTO(EGIElementDTO):
    """Edge (predicate) with spatial positioning and connections."""

    relation_name: str = "P"
    incident_vertices: Tuple[str, ...] = ()  # Vertex IDs in order
    text_width: float = 60.0
    text_height: float = 25.0


@dataclass
class CutDTO(EGIElementDTO):
    """Cut with spatial bounds."""

    parent_cut_id: Optional[str] = None
    cut_width: float = 150.0
    cut_height: float = 100.0


@dataclass
class LigatureDTO:
    """Ligature (line of identity) connecting vertices."""

    edge_id: str
    vertex_ids: List[str]
    path_points: List[Tuple[float, float]]
    line_width: float = 2.0


@dataclass
class EGIStateDTO:
    """
    Canonical EGI-based DTO for all inter-module communication.

    This replaces all the inconsistent schemas (drawing_schema, etc.)
    with a single, EGI-centered format that all modules can use.
    """

    # Elements (using dicts for O(1) lookup by ID) - required fields first
    vertices: Dict[str, VertexDTO]
    edges: Dict[str, EdgeDTO]
    cuts: Dict[str, CutDTO]
    ligatures: Dict[str, LigatureDTO]

    # EGI mappings - required fields
    nu_mapping: Dict[str, Tuple[str, ...]]  # edge_id -> vertex_ids
    area_mapping: Dict[str, Set[str]]  # area_id -> element_ids

    # Core EGI structure - optional fields with defaults
    sheet_id: str = "sheet"

    # Metadata - optional fields with defaults
    validation_mode: str = "composition"  # "composition" or "practice"

    def __post_init__(self):
        """Ensure consistency between elements and mappings."""
        # Validate that all referenced IDs exist
        all_vertex_ids = set(self.vertices.keys())
        all_edge_ids = set(self.edges.keys())
        all_cut_ids = set(self.cuts.keys())

        # Check nu_mapping references valid edges and vertices
        for edge_id, vertex_ids in self.nu_mapping.items():
            if edge_id not in all_edge_ids:
                raise ValueError(f"nu_mapping references unknown edge: {edge_id}")
            for vertex_id in vertex_ids:
                if vertex_id not in all_vertex_ids:
                    raise ValueError(
                        f"nu_mapping references unknown vertex: {vertex_id}"
                    )

        # Check area_mapping references valid areas and elements
        all_area_ids = {self.sheet_id} | all_cut_ids
        for area_id, element_ids in self.area_mapping.items():
            if area_id not in all_area_ids:
                raise ValueError(f"area_mapping references unknown area: {area_id}")

    def to_yaml(self) -> str:
        """Serialize EGI state to YAML format."""
        return yaml.safe_dump(asdict(self), sort_keys=False, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "EGIStateDTO":
        """Deserialize EGI state from YAML format."""
        data = yaml.safe_load(yaml_content)
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EGIStateDTO":
        """Create from dictionary (for JSON deserialization)."""
        return cls(**data)


def egi_to_dto(
    egi: RelationalGraphWithCuts, spatial_data: Dict[str, SpatialInfo] = None
) -> EGIStateDTO:
    """Convert EGI core structure to standardized DTO format."""
    spatial_data = spatial_data or {}

    # Convert vertices
    vertices = {}
    for vertex in egi.V:
        spatial = spatial_data.get(vertex.id)
        vertices[vertex.id] = VertexDTO(
            id=vertex.id,
            label=vertex.label,
            is_generic=vertex.is_generic,
            spatial=spatial,
        )

    # Convert edges
    edges = {}
    for edge in egi.E:
        spatial = spatial_data.get(edge.id)
        relation_name = egi.rel.get(edge.id, "P")
        incident_vertices = egi.nu.get(edge.id, ())
        edges[edge.id] = EdgeDTO(
            id=edge.id,
            relation_name=relation_name,
            incident_vertices=incident_vertices,
            spatial=spatial,
        )

    # Convert cuts
    cuts = {}
    for cut in egi.Cut:
        spatial = spatial_data.get(cut.id)
        # Determine parent cut from area mapping
        parent_cut_id = None
        for area_id, contents in egi.area.items():
            if cut.id in contents and area_id != egi.sheet:
                parent_cut_id = area_id
                break

        cuts[cut.id] = CutDTO(id=cut.id, parent_cut_id=parent_cut_id, spatial=spatial)

    return EGIStateDTO(
        sheet_id=egi.sheet,
        vertices=vertices,
        edges=edges,
        cuts=cuts,
        ligatures={},  # Would need ligature extraction logic
        nu_mapping=dict(egi.nu),
        area_mapping={k: set(v) for k, v in egi.area.items()},
    )


def dto_to_egi(dto: EGIStateDTO) -> RelationalGraphWithCuts:
    """Convert standardized DTO back to EGI core structure."""
    from frozendict import frozendict

    # Convert vertices
    vertices = frozenset(
        Vertex(id=v.id, label=v.label, is_generic=v.is_generic)
        for v in dto.vertices.values()
    )

    # Convert edges
    edges = frozenset(Edge(id=e.id) for e in dto.edges.values())

    # Convert cuts
    cuts = frozenset(Cut(id=c.id) for c in dto.cuts.values())

    # Build relation mapping
    rel_mapping = frozendict({e.id: e.relation_name for e in dto.edges.values()})

    # Build nu mapping
    nu_mapping = frozendict(dto.nu_mapping)

    # Build area mapping
    area_mapping = frozendict(
        {
            area_id: frozenset(element_ids)
            for area_id, element_ids in dto.area_mapping.items()
        }
    )

    return RelationalGraphWithCuts(
        V=vertices,
        E=edges,
        nu=nu_mapping,
        sheet=dto.sheet_id,
        Cut=cuts,
        area=area_mapping,
        rel=rel_mapping,
    )


# Adapter functions for legacy schemas
def from_drawing_schema(drawing_schema: Dict[str, Any]) -> EGIStateDTO:
    """Convert legacy drawing_schema to standardized EGI DTO."""
    vertices = {}
    edges = {}
    cuts = {}
    ligatures = {}

    # Handle vertices (both list and dict formats)
    vertex_data = drawing_schema.get("vertices", [])
    if isinstance(vertex_data, dict):
        for vid, vdata in vertex_data.items():
            vertices[vid] = VertexDTO(
                id=vid,
                spatial=SpatialInfo(x=vdata.get("x", 0), y=vdata.get("y", 0)),
                area_id=vdata.get("area_id", "sheet"),
            )
    else:  # list format
        for vdata in vertex_data:
            vid = vdata.get("id")
            if vid:
                vertices[vid] = VertexDTO(
                    id=vid,
                    spatial=SpatialInfo(x=vdata.get("x", 0), y=vdata.get("y", 0)),
                    area_id=vdata.get("area_id", "sheet"),
                )

    # Handle predicates/edges (both list and dict formats)
    predicate_data = drawing_schema.get("predicates", [])
    if isinstance(predicate_data, dict):
        for pid, pdata in predicate_data.items():
            edges[pid] = EdgeDTO(
                id=pid,
                relation_name=pdata.get("text", "P"),
                spatial=SpatialInfo(x=pdata.get("x", 0), y=pdata.get("y", 0)),
                area_id=pdata.get("area_id", "sheet"),
            )
    else:  # list format
        for pdata in predicate_data:
            pid = pdata.get("id")
            if pid:
                edges[pid] = EdgeDTO(
                    id=pid,
                    relation_name=pdata.get("text", "P"),
                    spatial=SpatialInfo(x=pdata.get("x", 0), y=pdata.get("y", 0)),
                    area_id=pdata.get("area_id", "sheet"),
                )

    # Handle cuts (both list and dict formats)
    cut_data = drawing_schema.get("cuts", [])
    if isinstance(cut_data, dict):
        for cid, cdata in cut_data.items():
            cuts[cid] = CutDTO(
                id=cid,
                parent_cut_id=cdata.get("parent_id"),
                spatial=SpatialInfo(
                    x=cdata.get("x", 0),
                    y=cdata.get("y", 0),
                    width=cdata.get("width", 150),
                    height=cdata.get("height", 100),
                ),
                area_id=cdata.get("area_id", "sheet"),
            )
    else:  # list format
        for cdata in cut_data:
            cid = cdata.get("id")
            if cid:
                cuts[cid] = CutDTO(
                    id=cid,
                    parent_cut_id=cdata.get("parent_id"),
                    spatial=SpatialInfo(
                        x=cdata.get("x", 0),
                        y=cdata.get("y", 0),
                        width=cdata.get("width", 150),
                        height=cdata.get("height", 100),
                    ),
                    area_id=cdata.get("area_id", "sheet"),
                )

    return EGIStateDTO(
        sheet_id=drawing_schema.get("sheet_id", "sheet"),
        vertices=vertices,
        edges=edges,
        cuts=cuts,
        ligatures=ligatures,
        nu_mapping={},  # Would need to be extracted from connections
        area_mapping={"sheet": set()},  # Would need to be computed
    )


def to_constraint_engine_format(dto: EGIStateDTO) -> Dict[str, Any]:
    """Convert EGI DTO to constraint engine's expected format."""
    return {
        "sheet_id": dto.sheet_id,
        "cuts": {
            cid: {
                "rect": (
                    cut.spatial.x if cut.spatial else 0,
                    cut.spatial.y if cut.spatial else 0,
                    cut.spatial.width if cut.spatial else cut.cut_width,
                    cut.spatial.height if cut.spatial else cut.cut_height,
                ),
                "parent_id": cut.parent_cut_id,
            }
            for cid, cut in dto.cuts.items()
        },
        "vertices": {
            vid: {
                "pos": (
                    vertex.spatial.x if vertex.spatial else 0,
                    vertex.spatial.y if vertex.spatial else 0,
                ),
                "radius": vertex.radius,
                "area_id": vertex.area_id,
                "name": vertex.label,
            }
            for vid, vertex in dto.vertices.items()
        },
        "predicates": {
            eid: {
                "rect": (
                    edge.spatial.x if edge.spatial else 0,
                    edge.spatial.y if edge.spatial else 0,
                    edge.spatial.width if edge.spatial else edge.text_width,
                    edge.spatial.height if edge.spatial else edge.text_height,
                ),
                "area_id": edge.area_id,
                "text": edge.relation_name,
            }
            for eid, edge in dto.edges.items()
        },
        "ligatures": {
            lid: {
                "path": lig.path_points,
                "width": lig.line_width,
                "vertices": lig.vertex_ids,
            }
            for lid, lig in dto.ligatures.items()
        },
    }
