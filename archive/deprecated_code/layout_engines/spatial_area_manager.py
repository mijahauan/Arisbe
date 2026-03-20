"""
Spatial Area Manager: Leverages Qt's built-in BSP spatial indexing for precise area detection.

This system uses QGraphicsScene's itemAt() functionality to provide:
1. Efficient point-in-area queries using Qt's BSP tree
2. Precise logical-to-physical area correspondence
3. Dynamic area boundary tracking
4. Integration with existing QGraphicsItem rendering pipeline
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainterPath, QPolygonF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsScene

from egi_core_dau import ElementID, RelationalGraphWithCuts


class AreaGraphicsItem(QGraphicsPathItem):
    """A QGraphicsItem that represents a logical area boundary for spatial queries."""
    
    def __init__(self, area_id: ElementID, boundary_path: QPainterPath):
        super().__init__(boundary_path)
        self.area_id = area_id
        # Make invisible but still detectable by itemAt()
        self.setVisible(False)
        self.setZValue(-1000)  # Behind everything else


class SpatialAreaManager:
    """
    Leverages Qt's BSP spatial indexing for efficient area detection.
    
    Uses QGraphicsScene.itemAt() to determine which logical area contains a point,
    eliminating the need for custom spatial indexing algorithms.
    """
    
    def __init__(self, graphics_scene: QGraphicsScene):
        self.graphics_scene = graphics_scene
        self.area_items: Dict[ElementID, AreaGraphicsItem] = {}
        self.area_hierarchy: Dict[ElementID, Set[ElementID]] = {}
        self.sheet_area_id: Optional[ElementID] = None
        
    def initialize_from_egi(self, egi: RelationalGraphWithCuts, cut_bounds: Dict[ElementID, QRectF]):
        """Initialize area items from EGI structure and cut layout."""
        # Clear existing area items from scene
        for item in self.area_items.values():
            self.graphics_scene.removeItem(item)
        self.area_items.clear()
        self.area_hierarchy.clear()
        self.sheet_area_id = egi.sheet
        
        # Step 1: Create invisible area items for all cuts
        for cut in egi.Cut:
            if cut.id in cut_bounds:
                cut_rect = cut_bounds[cut.id]
                cut_path = QPainterPath()
                cut_path.addRoundedRect(cut_rect, 10, 10)
                
                # Create invisible area item for spatial queries
                area_item = AreaGraphicsItem(cut.id, cut_path)
                self.area_items[cut.id] = area_item
                self.graphics_scene.addItem(area_item)
        
        # Step 2: Build area hierarchy for depth ordering
        self._build_area_hierarchy(egi)
        
        # Step 3: Create sheet area (entire scene minus cuts)
        self._create_sheet_area_item()
        
        # Step 4: Set Z-values based on nesting depth for proper hit testing
        self._set_area_z_order()
    
    def _build_area_hierarchy(self, egi: RelationalGraphWithCuts):
        """Build parent-child relationships between areas."""
        for area_id, contents in egi.area.items():
            if area_id not in self.area_hierarchy:
                self.area_hierarchy[area_id] = set()
            
            # Find child cuts in this area
            for elem_id in contents:
                if elem_id in self.area_items:  # This element is a cut
                    self.area_hierarchy[area_id].add(elem_id)
    
    def _create_sheet_area_item(self):
        """Create sheet area item covering entire scene."""
        # Sheet area covers the entire scene bounds
        scene_rect = self.graphics_scene.sceneRect()
        if scene_rect.isEmpty():
            scene_rect = QRectF(-1000, -1000, 2000, 2000)  # Default large area
        
        sheet_path = QPainterPath()
        sheet_path.addRect(scene_rect)
        
        # Create sheet area item (will be behind cuts in Z-order)
        sheet_item = AreaGraphicsItem(self.sheet_area_id, sheet_path)
        self.area_items[self.sheet_area_id] = sheet_item
        self.graphics_scene.addItem(sheet_item)
    
    def get_area_at_point(self, point: QPointF) -> Optional[ElementID]:
        """Get the logical area ID for a specific pixel coordinate using Qt's BSP tree."""
        # Use Qt's optimized spatial indexing to find the topmost area item
        item = self.graphics_scene.itemAt(point, self.graphics_scene.views()[0].transform() if self.graphics_scene.views() else None)
        
        # Walk up the item hierarchy to find an AreaGraphicsItem
        while item:
            if isinstance(item, AreaGraphicsItem):
                return item.area_id
            item = item.parentItem()
        
        # Fallback: check all area items manually (shouldn't happen with proper Z-order)
        for area_item in self.area_items.values():
            if area_item.contains(area_item.mapFromScene(point)):
                return area_item.area_id
        
        return None
    
    def get_area_item(self, area_id: ElementID) -> Optional[AreaGraphicsItem]:
        """Get the graphics item for a logical area."""
        return self.area_items.get(area_id)
    
    def update_cut_boundary(self, cut_id: ElementID, new_bounds: QRectF):
        """Update a cut's boundary."""
        if cut_id not in self.area_items:
            return
        
        # Update cut path
        cut_path = QPainterPath()
        cut_path.addRoundedRect(new_bounds, 10, 10)
        
        # Update the graphics item
        self.area_items[cut_id].setPath(cut_path)
    
    def _set_area_z_order(self):
        """Set Z-order of area items based on nesting depth for proper hit testing."""
        # Sheet area should be deepest (most negative Z)
        if self.sheet_area_id in self.area_items:
            self.area_items[self.sheet_area_id].setZValue(-2000)
        
        # Set cut Z-values based on hierarchy depth
        for area_id, area_item in self.area_items.items():
            if area_id != self.sheet_area_id:
                depth = self.get_area_hierarchy_depth(area_id)
                # More nested cuts have higher (less negative) Z values for proper hit testing
                area_item.setZValue(-1000 + depth * 100)
    
    def get_area_bounds(self, area_id: ElementID) -> Optional[QRectF]:
        """Get bounding rectangle for an area."""
        item = self.area_items.get(area_id)
        return item.boundingRect() if item else None
    
    def get_safe_position_in_area(self, area_id: ElementID, margin: float = 20.0) -> Optional[QPointF]:
        """Get a safe position within an area, away from boundaries."""
        item = self.area_items.get(area_id)
        if not item:
            return None
        
        bounds = item.boundingRect()
        
        # For cuts, use center with margin
        if area_id != self.sheet_area_id:
            safe_bounds = bounds.adjusted(margin, margin, -margin, -margin)
            if safe_bounds.width() > 0 and safe_bounds.height() > 0:
                return safe_bounds.center()
            else:
                return bounds.center()
        
        # For sheet area, find a position not inside any cuts
        test_points = [
            QPointF(bounds.x() + margin, bounds.y() + margin),
            QPointF(bounds.center().x(), bounds.y() + margin),
            QPointF(bounds.right() - margin, bounds.y() + margin),
            bounds.center()
        ]
        
        for point in test_points:
            if self.get_area_at_point(point) == area_id:
                return point
        
        return bounds.center()  # Fallback
    
    def get_area_hierarchy_depth(self, area_id: ElementID) -> int:
        """Get nesting depth of an area (sheet=0, cuts increase depth)."""
        if area_id == self.sheet_area_id:
            return 0
        
        # Find depth by traversing hierarchy
        depth = 1
        for parent_id, children in self.area_hierarchy.items():
            if area_id in children:
                if parent_id == self.sheet_area_id:
                    return depth
                else:
                    return depth + self.get_area_hierarchy_depth(parent_id)
        
        return depth
    
    def debug_area_info(self) -> str:
        """Generate debug information about area items."""
        scene_rect = self.graphics_scene.sceneRect()
        info = [f"Scene: {scene_rect}"]
        
        for area_id, item in self.area_items.items():
            bounds = item.boundingRect()
            depth = self.get_area_hierarchy_depth(area_id)
            z_value = item.zValue()
            info.append(f"Area {area_id}: bounds={bounds}, depth={depth}, z={z_value}")
        
        return "\n".join(info)
