"""
Coordinate Negotiation Module for Arisbe Existential Graph Editor

This module provides a clean separation between:
1. Data Model Coordinates (EGI logical areas, drawing schema)
2. Spatial-Logical Correspondence (SpatialRegionManager regions)
3. Rendering Coordinates (Qt canvas, graphics items)

Maintains platform independence and enables easier migration between rendering backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple

from spatial_logical_alignment import SpatialBounds, SpatialElement
from spatial_region_manager import SpatialRegion, SpatialRegionManager


@dataclass
class CoordinateTransform:
    """Represents a coordinate transformation between coordinate systems."""

    scale_x: float = 1.0
    scale_y: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    def apply(self, x: float, y: float) -> Tuple[float, float]:
        """Apply transformation to coordinates."""
        return (x * self.scale_x + self.offset_x, y * self.scale_y + self.offset_y)

    def inverse(self, x: float, y: float) -> Tuple[float, float]:
        """Apply inverse transformation to coordinates."""
        return ((x - self.offset_x) / self.scale_x, (y - self.offset_y) / self.scale_y)


class RenderingBackend(Protocol):
    """Protocol for rendering backend abstraction."""

    def get_item_bounds(self, item_id: str) -> Optional[SpatialBounds]:
        """Get actual rendered bounds of an item."""
        ...

    def get_scene_position(
        self, screen_x: float, screen_y: float
    ) -> Tuple[float, float]:
        """Convert screen coordinates to scene coordinates."""
        ...

    def get_items_at_position(self, x: float, y: float) -> List[str]:
        """Get item IDs at the given scene position."""
        ...


class CoordinateNegotiator:
    """
    Central coordinator for all coordinate transformations in Arisbe.

    Maintains consistency between data model, logical areas, and rendering.
    Provides platform-independent coordinate operations.
    """

    def __init__(
        self,
        region_manager: SpatialRegionManager,
        rendering_backend: Optional[RenderingBackend] = None,
    ):
        self.region_manager = region_manager
        self.rendering_backend = rendering_backend

        # Coordinate system mappings - identity transforms by default
        # GUI systems should call negotiate_coordinate_mapping() to establish proper transforms
        self.data_to_logical = CoordinateTransform()
        self.logical_to_rendering = CoordinateTransform()

        # Element tracking
        self.element_positions: Dict[str, Tuple[float, float]] = (
            {}
        )  # Data model coordinates
        self.element_bounds: Dict[str, SpatialBounds] = {}  # Logical coordinates

    def set_rendering_backend(self, backend: RenderingBackend) -> None:
        """Set the rendering backend for coordinate queries."""
        self.rendering_backend = backend

    def register_element(
        self,
        element_id: str,
        data_x: float,
        data_y: float,
        width: float = 20,
        height: float = 20,
    ) -> None:
        """Register an element with its data model coordinates."""
        self.element_positions[element_id] = (data_x, data_y)

        # Transform to logical coordinates
        logical_x, logical_y = self.data_to_logical.apply(data_x, data_y)
        self.element_bounds[element_id] = SpatialBounds(
            logical_x, logical_y, width, height
        )

    def update_element_position(
        self, element_id: str, data_x: float, data_y: float
    ) -> None:
        """Update element position in data model coordinates."""
        self.element_positions[element_id] = (data_x, data_y)

        # Update logical coordinates
        logical_x, logical_y = self.data_to_logical.apply(data_x, data_y)
        if element_id in self.element_bounds:
            bounds = self.element_bounds[element_id]
            self.element_bounds[element_id] = SpatialBounds(
                logical_x, logical_y, bounds.width, bounds.height
            )

    def get_logical_area_for_data_position(self, data_x: float, data_y: float) -> str:
        """Get logical area for a data model position."""
        logical_x, logical_y = self.data_to_logical.apply(data_x, data_y)
        return self.region_manager.get_logical_area_at_point(logical_x, logical_y)

    def get_logical_area_for_rendering_position(
        self, render_x: float, render_y: float
    ) -> str:
        """Get logical area for a rendering position (e.g., Qt scene coordinates)."""
        logical_x, logical_y = self.logical_to_rendering.inverse(render_x, render_y)
        return self.region_manager.get_logical_area_at_point(logical_x, logical_y)

    def get_rendering_position_for_data(
        self, data_x: float, data_y: float
    ) -> Tuple[float, float]:
        """Convert data model coordinates to rendering coordinates."""
        logical_x, logical_y = self.data_to_logical.apply(data_x, data_y)
        return self.logical_to_rendering.apply(logical_x, logical_y)

    def get_data_position_for_rendering(
        self, render_x: float, render_y: float
    ) -> Tuple[float, float]:
        """Convert rendering coordinates to data model coordinates."""
        logical_x, logical_y = self.logical_to_rendering.inverse(render_x, render_y)
        return self.data_to_logical.inverse(logical_x, logical_y)

    def synchronize_with_rendering_backend(self) -> None:
        """Synchronize coordinate systems with actual rendered elements."""
        if not self.rendering_backend:
            return

        print("COORDINATE SYNC: Synchronizing with rendering backend")

        # Update transforms based on actual rendered positions
        for element_id in self.element_positions:
            actual_bounds = self.rendering_backend.get_item_bounds(element_id)
            if actual_bounds:
                data_x, data_y = self.element_positions[element_id]

                # Calculate transform adjustment
                expected_render_x, expected_render_y = (
                    self.get_rendering_position_for_data(data_x, data_y)
                )
                actual_render_x, actual_render_y = actual_bounds.x, actual_bounds.y

                # Update transform if significant deviation
                dx = actual_render_x - expected_render_x
                dy = actual_render_y - expected_render_y

                if abs(dx) > 1.0 or abs(dy) > 1.0:
                    print(
                        f"COORDINATE SYNC: Adjusting transform for {element_id}: offset ({dx}, {dy})"
                    )
                    self.logical_to_rendering.offset_x += dx
                    self.logical_to_rendering.offset_y += dy

    def create_region_for_cut(
        self,
        cut_id: str,
        data_x: float,
        data_y: float,
        width: float,
        height: float,
        parent_area: str = "sheet",
    ) -> str:
        """Create a spatial region for a cut using data model coordinates."""
        # Transform to logical coordinates
        logical_x, logical_y = self.data_to_logical.apply(data_x, data_y)
        logical_width = width * self.data_to_logical.scale_x
        logical_height = height * self.data_to_logical.scale_y

        # Create region in SpatialRegionManager
        logical_area_id = f"cut_{cut_id}"

        # Manual region creation with proper bounds
        from spatial_region_manager import SpatialRegion

        region = SpatialRegion(
            region_id=f"region_{logical_area_id}",
            logical_area_id=logical_area_id,
            bounds=(logical_x, logical_y, logical_width, logical_height),
            parent_region_id=f"region_{parent_area}",
        )

        self.region_manager.regions[f"region_{logical_area_id}"] = region
        self.region_manager.logical_area_to_region[logical_area_id] = (
            f"region_{logical_area_id}"
        )

        # Add to parent's children
        parent_region = self.region_manager.regions.get(f"region_{parent_area}")
        if parent_region:
            parent_region.child_region_ids.add(f"region_{logical_area_id}")

        print(
            f"COORDINATE NEGOTIATOR: Created region {logical_area_id} at logical ({logical_x}, {logical_y}, {logical_width}, {logical_height})"
        )

        return logical_area_id

    def get_valid_placement_area(
        self, render_x: float, render_y: float
    ) -> Optional[str]:
        """Get valid logical area for element placement at rendering coordinates."""
        logical_area = self.get_logical_area_for_rendering_position(render_x, render_y)

        # Validate that the area exists and can accept new elements
        region = self.region_manager.get_region_for_logical_area(logical_area)
        if region:
            return logical_area

        return None

    def get_region_bounds_in_rendering_coordinates(
        self, logical_area_id: str
    ) -> Optional[SpatialBounds]:
        """Get region bounds in rendering coordinate system."""
        region = self.region_manager.get_region_for_logical_area(logical_area_id)
        if not region:
            return None

        # Transform logical bounds to rendering coordinates
        render_x, render_y = self.logical_to_rendering.apply(region.x, region.y)
        render_width = region.width * self.logical_to_rendering.scale_x
        render_height = region.height * self.logical_to_rendering.scale_y

        return SpatialBounds(render_x, render_y, render_width, render_height)

    def debug_coordinate_systems(self) -> Dict[str, Any]:
        """Get debugging information about coordinate systems."""
        info = {
            "transforms": {
                "data_to_logical": {
                    "scale": (
                        self.data_to_logical.scale_x,
                        self.data_to_logical.scale_y,
                    ),
                    "offset": (
                        self.data_to_logical.offset_x,
                        self.data_to_logical.offset_y,
                    ),
                },
                "logical_to_rendering": {
                    "scale": (
                        self.logical_to_rendering.scale_x,
                        self.logical_to_rendering.scale_y,
                    ),
                    "offset": (
                        self.logical_to_rendering.offset_x,
                        self.logical_to_rendering.offset_y,
                    ),
                },
            },
            "elements": {},
            "regions": {},
        }

        # Element coordinate mappings
        for element_id, (data_x, data_y) in self.element_positions.items():
            logical_x, logical_y = self.data_to_logical.apply(data_x, data_y)
            render_x, render_y = self.logical_to_rendering.apply(logical_x, logical_y)

            info["elements"][element_id] = {
                "data": (data_x, data_y),
                "logical": (logical_x, logical_y),
                "rendering": (render_x, render_y),
                "logical_area": self.get_logical_area_for_data_position(data_x, data_y),
            }

        # Region coordinate mappings
        for region_id, region in self.region_manager.regions.items():
            render_bounds = self.get_region_bounds_in_rendering_coordinates(
                region.logical_area_id
            )
            info["regions"][region_id] = {
                "logical_area": region.logical_area_id,
                "logical_bounds": region.bounds,
                "rendering_bounds": render_bounds.to_dict() if render_bounds else None,
            }

        return info

    def negotiate_coordinate_mapping(
        self,
        gui_viewport_bounds: Tuple[float, float, float, float],
        logical_workspace_bounds: Tuple[float, float, float, float],
    ) -> None:
        """
        Negotiate coordinate mapping between GUI viewport and logical workspace.

        Args:
            gui_viewport_bounds: (min_x, min_y, width, height) of GUI viewport
            logical_workspace_bounds: (min_x, min_y, width, height) of desired logical workspace
        """
        gui_min_x, gui_min_y, gui_width, gui_height = gui_viewport_bounds
        logical_min_x, logical_min_y, logical_width, logical_height = (
            logical_workspace_bounds
        )

        # Calculate scale factors to fit logical workspace into GUI viewport
        scale_x = gui_width / logical_width if logical_width > 0 else 1.0
        scale_y = gui_height / logical_height if logical_height > 0 else 1.0

        # Use uniform scaling to preserve aspect ratio
        scale = min(scale_x, scale_y)

        # Calculate offsets to center logical workspace in GUI viewport
        offset_x = (
            gui_min_x + (gui_width - logical_width * scale) / 2 - logical_min_x * scale
        )
        offset_y = (
            gui_min_y
            + (gui_height - logical_height * scale) / 2
            - logical_min_y * scale
        )

        # Update coordinate transforms
        self.logical_to_rendering = CoordinateTransform(
            scale_x=scale, scale_y=scale, offset_x=offset_x, offset_y=offset_y
        )

        print(
            f"COORDINATE NEGOTIATION: GUI viewport {gui_viewport_bounds} → Logical workspace {logical_workspace_bounds}"
        )
        print(f"COORDINATE NEGOTIATION: Scale={scale}, Offset=({offset_x}, {offset_y})")

    def auto_negotiate_from_gui_bounds(
        self, gui_min_x: float, gui_min_y: float, gui_max_x: float, gui_max_y: float
    ) -> None:
        """
        Auto-negotiate coordinate mapping from GUI bounds to standard logical workspace.

        Maps GUI coordinate range to logical workspace centered at (0,0) with reasonable size.
        """
        gui_width = gui_max_x - gui_min_x
        gui_height = gui_max_y - gui_min_y

        # Define standard logical workspace: 1000x1000 centered at origin
        logical_size = 1000
        logical_workspace_bounds = (
            -logical_size / 2,
            -logical_size / 2,
            logical_size,
            logical_size,
        )
        gui_viewport_bounds = (gui_min_x, gui_min_y, gui_width, gui_height)

        self.negotiate_coordinate_mapping(gui_viewport_bounds, logical_workspace_bounds)


class QtRenderingBackend:
    """Qt-specific rendering backend implementation."""

    def __init__(self, scene):
        self.scene = scene

    def get_item_bounds(self, item_id: str) -> Optional[SpatialBounds]:
        """Get actual rendered bounds of a Qt graphics item."""
        for item in self.scene.items():
            if (
                (hasattr(item, "vertex_id") and item.vertex_id == item_id)
                or (hasattr(item, "predicate_id") and item.predicate_id == item_id)
                or (hasattr(item, "cut_id") and item.cut_id == item_id)
            ):

                pos = item.pos()
                rect = item.boundingRect()
                return SpatialBounds(pos.x(), pos.y(), rect.width(), rect.height())

        return None

    def get_scene_position(
        self, screen_x: float, screen_y: float
    ) -> Tuple[float, float]:
        """Convert screen coordinates to Qt scene coordinates."""
        # This would typically use QGraphicsView.mapToScene()
        # For now, assume direct mapping
        return (screen_x, screen_y)

    def get_items_at_position(self, x: float, y: float) -> List[str]:
        """Get Qt graphics item IDs at the given scene position."""
        from PySide6.QtCore import QPointF

        items = self.scene.items(QPointF(x, y))

        item_ids = []
        for item in items:
            if hasattr(item, "vertex_id"):
                item_ids.append(item.vertex_id)
            elif hasattr(item, "predicate_id"):
                item_ids.append(item.predicate_id)
            elif hasattr(item, "cut_id"):
                item_ids.append(item.cut_id)

        return item_ids
