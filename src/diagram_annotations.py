"""
Diagram annotation system for Arisbe EGI visualization.
Supports hook notation display and explicit identity edge symbols as per Dau Chapter 12.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import ElementID, RelationalGraphWithCuts


class AnnotationMode(Enum):
    """Annotation display modes for diagram rendering."""

    NONE = "none"
    HOOKS = "hooks"
    EXPLICIT_IDENTITY = "explicit_identity"
    BOTH = "both"


@dataclass(frozen=True)
class HookAnnotation:
    """Annotation for displaying hook notation (e, i) on diagrams."""

    edge_id: ElementID
    position: int  # 1-indexed as per Dau
    vertex_id: ElementID
    display_label: str  # e.g., "(e1, 2)"


@dataclass(frozen=True)
class IdentityEdgeAnnotation:
    """Annotation for displaying explicit identity edge symbols."""

    edge_id: ElementID
    vertex_ids: Tuple[ElementID, ElementID]
    display_symbol: str = "="
    show_numbered_lines: bool = True


@dataclass(frozen=True)
class LigatureAnnotation:
    """Annotation for highlighting ligature structures."""

    ligature_vertices: FrozenSet[ElementID]
    ligature_id: str
    highlight_color: str = "#FFE4B5"  # Moccasin


@dataclass(frozen=True)
class DiagramAnnotations:
    """Complete annotation set for an EGI diagram."""

    hook_annotations: FrozenSet[HookAnnotation] = frozenset()
    identity_annotations: FrozenSet[IdentityEdgeAnnotation] = frozenset()
    ligature_annotations: FrozenSet[LigatureAnnotation] = frozenset()
    mode: AnnotationMode = AnnotationMode.NONE


class AnnotationGenerator:
    """Generates diagram annotations from EGI structures."""

    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi

    def generate_hook_annotations(self) -> FrozenSet[HookAnnotation]:
        """Generate hook annotations for all edges."""
        annotations = set()

        for edge_id in {e.id for e in self.egi.E}:
            hooks = self.egi.get_hooks(edge_id)
            for edge_id_hook, position in hooks:
                vertex_id = self.egi.get_vertex_at_hook(edge_id, position)
                display_label = f"({edge_id}, {position})"

                annotations.add(
                    HookAnnotation(
                        edge_id=edge_id,
                        position=position,
                        vertex_id=vertex_id,
                        display_label=display_label,
                    )
                )

        return frozenset(annotations)

    def generate_identity_annotations(self) -> FrozenSet[IdentityEdgeAnnotation]:
        """Generate explicit identity edge annotations."""
        annotations = set()

        for edge_id in self.egi.get_identity_edges():
            vertex_seq = self.egi.get_incident_vertices(edge_id)
            if len(vertex_seq) == 2:
                annotations.add(
                    IdentityEdgeAnnotation(
                        edge_id=edge_id,
                        vertex_ids=(vertex_seq[0], vertex_seq[1]),
                        display_symbol="=",
                        show_numbered_lines=True,
                    )
                )

        return frozenset(annotations)

    def generate_ligature_annotations(self) -> FrozenSet[LigatureAnnotation]:
        """Generate ligature highlighting annotations."""
        annotations = set()
        ligatures = self.egi.get_ligatures()

        for i, ligature in enumerate(ligatures):
            if len(ligature) > 1:  # Only annotate non-trivial ligatures
                annotations.add(
                    LigatureAnnotation(
                        ligature_vertices=ligature,
                        ligature_id=f"L{i+1}",
                        highlight_color="#FFE4B5",
                    )
                )

        return frozenset(annotations)

    def generate_annotations(self, mode: AnnotationMode) -> DiagramAnnotations:
        """Generate complete annotation set based on mode."""
        hook_annotations = frozenset()
        identity_annotations = frozenset()
        ligature_annotations = frozenset()

        if mode in [AnnotationMode.HOOKS, AnnotationMode.BOTH]:
            hook_annotations = self.generate_hook_annotations()

        if mode in [AnnotationMode.EXPLICIT_IDENTITY, AnnotationMode.BOTH]:
            identity_annotations = self.generate_identity_annotations()

        # Always generate ligature annotations for structural understanding
        ligature_annotations = self.generate_ligature_annotations()

        return DiagramAnnotations(
            hook_annotations=hook_annotations,
            identity_annotations=identity_annotations,
            ligature_annotations=ligature_annotations,
            mode=mode,
        )


class AnnotationRenderer:
    """Renders annotations on diagram representations."""

    @staticmethod
    def get_hook_display_text(annotation: HookAnnotation) -> str:
        """Get display text for hook annotation."""
        return annotation.display_label

    @staticmethod
    def get_identity_display_elements(
        annotation: IdentityEdgeAnnotation,
    ) -> Dict[str, any]:
        """Get display elements for explicit identity edge."""
        return {
            "symbol": annotation.display_symbol,
            "show_numbered_lines": annotation.show_numbered_lines,
            "vertex_1": annotation.vertex_ids[0],
            "vertex_2": annotation.vertex_ids[1],
            "edge_id": annotation.edge_id,
        }

    @staticmethod
    def get_ligature_highlight_info(annotation: LigatureAnnotation) -> Dict[str, any]:
        """Get highlighting information for ligature."""
        return {
            "vertices": annotation.ligature_vertices,
            "color": annotation.highlight_color,
            "label": annotation.ligature_id,
        }

    @staticmethod
    def should_use_simplified_identity_display(annotations: DiagramAnnotations) -> bool:
        """Determine if identity edges should use simplified line representation."""
        return annotations.mode not in [
            AnnotationMode.EXPLICIT_IDENTITY,
            AnnotationMode.BOTH,
        ]


# Utility functions for integration with existing rendering system


def create_annotations_for_egi(
    egi: RelationalGraphWithCuts, mode: AnnotationMode = AnnotationMode.NONE
) -> DiagramAnnotations:
    """Create annotations for an EGI with specified mode."""
    generator = AnnotationGenerator(egi)
    return generator.generate_annotations(mode)


def get_branching_point_annotations(
    egi: RelationalGraphWithCuts,
) -> Dict[ElementID, int]:
    """Get branching point information for special rendering."""
    branching_info = {}
    for vertex in egi.V:
        if egi.is_branching_point(vertex.id):
            branching_info[vertex.id] = egi.get_branch_count(vertex.id)
    return branching_info


def get_identity_edge_display_mode(
    annotations: DiagramAnnotations, edge_id: ElementID
) -> str:
    """Determine display mode for specific identity edge."""
    if annotations.mode in [AnnotationMode.EXPLICIT_IDENTITY, AnnotationMode.BOTH]:
        return "explicit"
    return "simplified"


def format_hook_label(edge_id: ElementID, position: int) -> str:
    """Format hook label for display."""
    return f"({edge_id}, {position})"


def get_ligature_membership(
    egi: RelationalGraphWithCuts, vertex_id: ElementID
) -> Optional[FrozenSet[ElementID]]:
    """Get the ligature that contains the specified vertex."""
    return egi.get_vertex_ligature(vertex_id)
