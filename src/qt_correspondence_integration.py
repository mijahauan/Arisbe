#!/usr/bin/env python3
"""
Qt correspondence integration shim for Arisbe.
Provides light wrappers to convert EGI spatial correspondence output into
Qt-friendly render elements, and a factory tied to the current EGI system.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from egi_system import EGISystem
from egi_spatial_correspondence import create_spatial_correspondence_engine


@dataclass
class QtInteractionEvent:
    event_type: str
    position: Tuple[float, float]
    element_id: str | None = None


@dataclass
class QtRenderElement:
    element_id: str
    element_type: str
    bounds: Dict[str, float]
    # Optional extra fields
    relation_name: str | None = None
    path_points: List[Tuple[float, float]] | None = None


class QtCorrespondenceIntegration:
    """Adapter to generate Qt scene data from the current EGI state."""

    def __init__(self, egi_system: EGISystem):
        self.egi_system = egi_system
        self.engine = create_spatial_correspondence_engine(self.egi_system.get_egi())

    def generate_qt_scene(self) -> Dict[str, Any]:
        """Produce a dict with render_commands and Chapter 16 feature flags."""
        layout = self.engine.generate_spatial_layout()
        render_commands: List[Dict[str, Any]] = []
        ligature_commands: List[Dict[str, Any]] = []

        current_egi = self.egi_system.get_egi()

        def _area_parity(area_id: str) -> int:
            # Count cut nesting depth to the sheet. Even=0 (unshaded), Odd=1 (shaded)
            try:
                sheet = self.engine.egi.sheet
            except Exception:
                return 0
            if not area_id or area_id == sheet:
                return 0
            parity = 0
            current = area_id
            visited = set()
            while current and current not in visited and current != sheet:
                visited.add(current)
                # If current is a cut id, it's a level
                if any(getattr(c, 'id', None) == current for c in self.engine.egi.Cut):
                    parity ^= 1
                try:
                    parent = self.engine._determine_cut_parent_area(current)  # type: ignore[attr-defined]
                except Exception:
                    parent = None
                current = parent
            return parity

        for element_id, element in layout.items():
            cmd: Dict[str, Any] = {
                "type": element.element_type,
                "element_id": element_id,
                "bounds": {
                    "x": element.spatial_bounds.x,
                    "y": element.spatial_bounds.y,
                    "width": element.spatial_bounds.width,
                    "height": element.spatial_bounds.height,
                },
                "area_parity": _area_parity(getattr(element, 'logical_area', self.engine.egi.sheet)),
            }

            if element.element_type == "edge":
                cmd["relation_name"] = current_egi.rel.get(element_id, "Unknown")
                cmd["role"] = "edge.label_box"
            elif element.element_type == "vertex":
                cmd["vertex_name"] = element_id
                cmd["role"] = "vertex.dot"
            elif element.element_type == "cut":
                cmd["role"] = "cut.border"

            if element.element_type == "ligature":
                if getattr(element, "ligature_geometry", None):
                    cmd["path_points"] = element.ligature_geometry.spatial_path
                cmd["role"] = "ligature.arm"
                ligature_commands.append(cmd)
                continue

            render_commands.append(cmd)

        render_commands.extend(ligature_commands)

        return {
            "render_commands": render_commands,
            "chapter16_features": {
                "branching_point_dragging": True,
                "ligature_routing": True,
            },
        }


def create_qt_correspondence_integration(egi_system: EGISystem) -> QtCorrespondenceIntegration:
    return QtCorrespondenceIntegration(egi_system)
