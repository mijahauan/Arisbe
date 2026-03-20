"""
Qt Diagram Renderer - Convert LayoutDTO to interactive QGraphicsScene.

This renderer creates native Qt graphics items for full interactivity:
- Vertices as QGraphicsEllipseItem (draggable, selectable)
- Predicates as QGraphicsTextItem (draggable, selectable)  
- Ligatures as QGraphicsPathItem (visual feedback)
- Cuts as QGraphicsRectItem (visual hierarchy)

Used by Ergasterion for interactive editing.
"""

from typing import Dict, Optional, Set
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsItem,
)

from unified_d3_engine import LayoutDTO, Point
from egi_core_dau import RelationalGraphWithCuts


class InteractiveGraphicsItem:
    """Mixin for interactive diagram elements - adds element_id and interactive flags."""
    
    def setup_interactive(self, element_id: str):
        """Set up interactive properties. Call this after QGraphicsItem.__init__."""
        self.element_id = element_id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)
        
        # Track if this item has moved
        self._original_pos = None
        self._has_moved = False
    
    def itemChange(self, change, value):
        """Track when item position changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self._original_pos is None:
                self._original_pos = value
            else:
                self._has_moved = True
        return super().itemChange(change, value)


class InteractiveVertexItem(QGraphicsEllipseItem, InteractiveGraphicsItem):
    """Interactive vertex (draggable circle with label)."""
    
    def __init__(self, vertex_id: str, position: Point, radius: float, label: str, rendering_mode: str = "dot_and_label"):
        # Initialize graphics item
        super().__init__(-radius, -radius, radius*2, radius*2)
        # Set up interactive properties
        self.setup_interactive(vertex_id)
        
        # Set position
        self.setPos(position.x, position.y)
        
        # DEBUG: Print rendering mode
        print(f"[InteractiveVertexItem] Creating vertex '{label}' with rendering_mode='{rendering_mode}'")
        
        # Style - only show dot if rendering_mode includes "dot"
        show_dot = rendering_mode in ["dot_only", "dot_and_label"]
        print(f"[InteractiveVertexItem] show_dot={show_dot}")
        
        if show_dot:
            # Draw visible dot (Dau style)
            pen = QPen(QColor("#000000"))
            pen.setWidth(2.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            self.setPen(pen)
            self.setBrush(QBrush(QColor("#000000")))
        else:
            # No visible dot (Peirce/Sowa style) - just invisible hitbox
            pen = QPen(Qt.PenStyle.NoPen)
            self.setPen(pen)
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        # Label (shown in all modes except dot_only)
        if label and rendering_mode != "dot_only":
            self.label_item = QGraphicsTextItem(label, self)
            font = QFont("Times New Roman", 11)
            self.label_item.setFont(font)
            # Position label to the right of vertex
            self.label_item.setPos(radius + 5, -radius - 5)
        else:
            self.label_item = None
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        pen = QPen(QColor("#1E88E5"))
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        pen = QPen(QColor("#000000"))
        pen.setWidth(2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        super().hoverLeaveEvent(event)


class InteractivePredicateItem(QGraphicsTextItem, InteractiveGraphicsItem):
    """Interactive predicate (draggable text)."""
    
    def __init__(self, predicate_id: str, position: Point, label: str):
        # Initialize text item
        super().__init__(label)
        # Set up interactive properties
        self.setup_interactive(predicate_id)
        
        # Set font
        font = QFont("Times New Roman", 12)
        self.setFont(font)
        
        # Store center position for accurate retrieval
        self.center_position = position
        
        # Center text at position (QGraphicsTextItem uses top-left origin)
        bounds = self.boundingRect()
        self.setPos(position.x - bounds.width()/2, position.y - bounds.height()/2)
        
        # Make background transparent
        self.setDefaultTextColor(QColor("#000000"))
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setDefaultTextColor(QColor("#1E88E5"))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        self.setDefaultTextColor(QColor("#000000"))
        super().hoverLeaveEvent(event)


class LigaturePathItem(QGraphicsPathItem):
    """Non-interactive ligature path (visual only)."""
    
    def __init__(self, points: list, cap_style: str = "butt", line_width: float = 2.5):
        super().__init__()
        
        # DEBUG: Print cap_style being used
        print(f"[LigaturePathItem] Creating ligature with cap_style='{cap_style}'")
        print(f"  Points type: {type(points)}, count: {len(points) if hasattr(points, '__len__') else 'N/A'}")
        
        try:
            if len(points) > 0:
                print(f"  Start: ({points[0].x:.1f}, {points[0].y:.1f})")
                if len(points) > 1:
                    print(f"  End: ({points[-1].x:.1f}, {points[-1].y:.1f})")
                if len(points) > 2:
                    print(f"  WARNING: Multi-segment path with {len(points)} points!")
        except Exception as e:
            print(f"  ERROR accessing points: {e}")
        
        # Create path from points
        path = QPainterPath()
        if points and len(points) > 0:
            try:
                path.moveTo(points[0].x, points[0].y)
                for point in points[1:]:
                    path.lineTo(point.x, point.y)
                print(f"  Path created successfully with {len(points)} segments")
            except Exception as e:
                print(f"  ERROR creating path: {e}")
        else:
            print(f"  WARNING: Empty points list! No path created.")
        
        self.setPath(path)
        
        # Style
        pen = QPen(QColor("#000000"))
        pen.setWidth(line_width)
        
        # Set cap style based on style specification
        if cap_style == "round":
            print(f"[LigaturePathItem] Setting RoundCap (will create dots!)")
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        elif cap_style == "square":
            print(f"[LigaturePathItem] Setting SquareCap")
            pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        else:  # "butt" or default
            print(f"[LigaturePathItem] Setting FlatCap (no dots)")
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        
        # CRITICAL: Set join style to prevent rounded corners at line segments
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        
        # Disable cosmetic pen (so width scales with zoom)
        pen.setCosmetic(False)
        
        self.setPen(pen)
        
        # DEBUG: Verify pen settings
        actual_cap = self.pen().capStyle()
        cap_names = {
            Qt.PenCapStyle.FlatCap: "FlatCap",
            Qt.PenCapStyle.RoundCap: "RoundCap",
            Qt.PenCapStyle.SquareCap: "SquareCap"
        }
        print(f"[LigaturePathItem] Final pen cap style: {cap_names.get(actual_cap, 'Unknown')}")
        
        # Not selectable/movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)


class CutRectItem(QGraphicsRectItem, InteractiveGraphicsItem):
    """Interactive cut boundary (selectable, movable, and resizable)."""
    
    def __init__(self, cut_id: str, bounds: 'BoundingBox', polarity: int):
        x = bounds.min_x
        y = bounds.min_y
        w = bounds.max_x - bounds.min_x
        h = bounds.max_y - bounds.min_y
        
        super().__init__(x, y, w, h)
        
        # Set up interactive properties
        self.setup_interactive(cut_id)
        self.cut_id = cut_id
        
        # Store original bounds for move/resize detection
        self.original_pos = (x, y)
        self.original_size = (w, h)
        
        # Cuts are selectable AND movable (container movement)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        # Enable geometry changes for resize tracking
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Style based on polarity
        pen = QPen(QColor("#000000"))
        pen.setWidth(1.5)
        self.setPen(pen)
        
        # CRITICAL: Always use transparent brush
        # Shading is handled by separate background items, not the cut border itself
        self.setBrush(QBrush(Qt.GlobalColor.transparent))
        
        # Store polarity for reference
        self.polarity = polarity
        
        # Resize state
        self._resize_handle = None  # 'se', 'sw', 'ne', 'nw', 'e', 'w', 'n', 's'
        self._resize_start_rect = None
        self._resize_start_pos = None
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        pen = QPen(QColor("#1E88E5"))  # Blue
        pen.setWidth(2)
        self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        pen = QPen(QColor("#000000"))
        pen.setWidth(1.5)
        self.setPen(pen)
        self._resize_handle = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverLeaveEvent(event)
    
    def hoverMoveEvent(self, event):
        """Update cursor based on position (resize handles)."""
        if not self.isSelected():
            super().hoverMoveEvent(event)
            return
        
        # Check if hovering near edges/corners (resize handles)
        handle = self._get_resize_handle(event.pos())
        self._resize_handle = handle
        
        # Set cursor based on handle
        cursor_map = {
            'se': Qt.CursorShape.SizeFDiagCursor,
            'sw': Qt.CursorShape.SizeBDiagCursor,
            'ne': Qt.CursorShape.SizeBDiagCursor,
            'nw': Qt.CursorShape.SizeFDiagCursor,
            'e': Qt.CursorShape.SizeHorCursor,
            'w': Qt.CursorShape.SizeHorCursor,
            'n': Qt.CursorShape.SizeVerCursor,
            's': Qt.CursorShape.SizeVerCursor,
        }
        
        if handle:
            self.setCursor(cursor_map.get(handle, Qt.CursorShape.ArrowCursor))
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)  # Move cursor
        
        super().hoverMoveEvent(event)
    
    def _get_resize_handle(self, pos):
        """Determine which resize handle (if any) the position is over."""
        rect = self.rect()
        handle_size = 10.0  # pixels
        
        x, y = pos.x(), pos.y()
        left, top = rect.left(), rect.top()
        right, bottom = rect.right(), rect.bottom()
        
        # Check corners first
        if abs(x - right) < handle_size and abs(y - bottom) < handle_size:
            return 'se'
        if abs(x - left) < handle_size and abs(y - bottom) < handle_size:
            return 'sw'
        if abs(x - right) < handle_size and abs(y - top) < handle_size:
            return 'ne'
        if abs(x - left) < handle_size and abs(y - top) < handle_size:
            return 'nw'
        
        # Check edges
        if abs(x - right) < handle_size:
            return 'e'
        if abs(x - left) < handle_size:
            return 'w'
        if abs(y - bottom) < handle_size:
            return 's'
        if abs(y - top) < handle_size:
            return 'n'
        
        return None
    
    def mousePressEvent(self, event):
        """Start resize or move operation."""
        if event.button() == Qt.MouseButton.LeftButton and self.isSelected():
            handle = self._get_resize_handle(event.pos())
            if handle:
                # Start resize
                self._resize_handle = handle
                self._resize_start_rect = self.rect()
                self._resize_start_pos = event.pos()
                # Disable ItemIsMovable during resize
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                event.accept()
                return
        
        # Default move behavior
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle resize dragging."""
        if self._resize_handle and self._resize_start_rect:
            delta = event.pos() - self._resize_start_pos
            self._apply_resize(delta)
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Finish resize or move operation."""
        if self._resize_handle:
            # Finished resizing
            self._resize_handle = None
            self._resize_start_rect = None
            self._resize_start_pos = None
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            event.accept()
            # Emit custom signal for resize completion (handled by canvas)
            return
        
        super().mouseReleaseEvent(event)
    
    def _apply_resize(self, delta):
        """Apply resize based on handle and delta."""
        if not self._resize_start_rect:
            return
        
        rect = self._resize_start_rect
        handle = self._resize_handle
        
        # Calculate new rect based on handle
        new_rect = QRectF(rect)
        
        if 'e' in handle:  # East (right edge)
            new_rect.setRight(rect.right() + delta.x())
        if 'w' in handle:  # West (left edge)
            new_rect.setLeft(rect.left() + delta.x())
        if 'n' in handle:  # North (top edge)
            new_rect.setTop(rect.top() + delta.y())
        if 's' in handle:  # South (bottom edge)
            new_rect.setBottom(rect.bottom() + delta.y())
        
        # Enforce minimum size
        min_size = 40.0
        if new_rect.width() < min_size:
            if 'w' in handle:
                new_rect.setLeft(new_rect.right() - min_size)
            else:
                new_rect.setRight(new_rect.left() + min_size)
        
        if new_rect.height() < min_size:
            if 'n' in handle:
                new_rect.setTop(new_rect.bottom() - min_size)
            else:
                new_rect.setBottom(new_rect.top() + min_size)
        
        self.setRect(new_rect)


class QtDiagramRenderer:
    """
    Renders LayoutDTO as interactive QGraphicsScene.
    
    Creates native Qt graphics items for full interactivity in Ergasterion mode.
    """
    
    def __init__(self):
        self.vertex_items: Dict[str, InteractiveVertexItem] = {}
        self.predicate_items: Dict[str, InteractivePredicateItem] = {}
        self.ligature_items: list = []
        self.cut_items: Dict[str, CutRectItem] = {}
    
    def render_to_scene(
        self, 
        dto: LayoutDTO, 
        egi: RelationalGraphWithCuts
    ) -> QGraphicsScene:
        """
        Render LayoutDTO as interactive QGraphicsScene.
        
        Args:
            dto: Layout information
            egi: EGI model for labels/properties
            
        Returns:
            QGraphicsScene with interactive items
        """
        print(f"QtDiagramRenderer.render_to_scene: {len(dto.vertex_positions)}V, {len(dto.predicate_positions)}P")
        scene = QGraphicsScene()
        
        # Clear previous items
        self.vertex_items.clear()
        self.predicate_items.clear()
        self.ligature_items.clear()
        self.cut_items.clear()
        
        # Get style from DTO
        style = dto.style
        
        # 1. Render cuts (background)
        # Z-order: inner cuts should be on top of outer cuts (by nesting depth)
        polarity_map = self._compute_polarity_map(egi, dto.sheet_id)
        nesting_depth_map = self._compute_nesting_depth(egi, dto.sheet_id)
        
        # First pass: Create background shading for odd-polarity cuts WITH HOLES
        # Build a hierarchy map to find child cuts
        child_cuts = {}  # cut_id -> list of direct child cut_ids
        for area_id, contents in egi.area.items():
            if area_id in dto.cut_bounds:  # Only consider actual cuts
                child_cuts[area_id] = [elem_id for elem_id in contents 
                                      if elem_id in dto.cut_bounds and elem_id != dto.sheet_id]
        
        for cut_id, bounds in dto.cut_bounds.items():
            if cut_id != dto.sheet_id:
                polarity = polarity_map.get(cut_id, 0)
                nesting_depth = nesting_depth_map.get(cut_id, 0)
                
                # Only create background for odd polarity (gray shading)
                if polarity % 2 == 1:
                    from PySide6.QtGui import QPainterPath
                    
                    # Create main rectangle
                    path = QPainterPath()
                    path.addRect(bounds.min_x, bounds.min_y,
                                bounds.max_x - bounds.min_x,
                                bounds.max_y - bounds.min_y)
                    
                    # Subtract child cut rectangles (create holes)
                    for child_id in child_cuts.get(cut_id, []):
                        child_bounds = dto.cut_bounds[child_id]
                        child_rect = QPainterPath()
                        child_rect.addRect(child_bounds.min_x, child_bounds.min_y,
                                          child_bounds.max_x - child_bounds.min_x,
                                          child_bounds.max_y - child_bounds.min_y)
                        path = path.subtracted(child_rect)
                    
                    # Create path item
                    from PySide6.QtWidgets import QGraphicsPathItem
                    bg_item = QGraphicsPathItem(path)
                    bg_item.setPen(QPen(Qt.PenStyle.NoPen))  # No border
                    bg_item.setBrush(QBrush(QColor(0, 0, 0, 20)))  # Gray fill
                    # Background renders at depth-1 (behind the cut border)
                    bg_item.setZValue((nesting_depth * 10.0) - 1)
                    scene.addItem(bg_item)
        
        # Second pass: Create interactive cut borders (always transparent)
        for cut_id, bounds in dto.cut_bounds.items():
            if cut_id != dto.sheet_id:  # Don't render sheet
                polarity = polarity_map.get(cut_id, 0)
                nesting_depth = nesting_depth_map.get(cut_id, 0)
                cut_item = CutRectItem(cut_id, bounds, polarity)
                # Set z-order: deeper nested cuts on top
                cut_item.setZValue(nesting_depth * 10.0)
                scene.addItem(cut_item)
                self.cut_items[cut_id] = cut_item
        
        # 2. Render ligatures (middle layer)
        # Get ligature style from raw_style_data
        ligature_cap_style = style.raw_style_data.get('ligature', {}).get('cap_style', 'butt')
        ligature_line_width = style.ligature_line_width
        
        print(f"[QtDiagramRenderer] Style: {style.style_name}, cap_style from raw_style_data: '{ligature_cap_style}'")
        print(f"[QtDiagramRenderer] Rendering {len(dto.ligature_paths)} ligatures")
        
        for idx, ligature in enumerate(dto.ligature_paths):
            print(f"[QtDiagramRenderer] Ligature {idx}: predicate={ligature.predicate_id}, vertex={ligature.vertex_id}")
            print(f"  Points object: {ligature.points}, type: {type(ligature.points)}")
            ligature_item = LigaturePathItem(ligature.points, ligature_cap_style, ligature_line_width)
            scene.addItem(ligature_item)
            self.ligature_items.append(ligature_item)
        
        # 3. Render vertices (interactive, top layer)
        # Z-order: 1000+ to be above all cuts
        for vertex_id, point in dto.vertex_positions.items():
            # Get vertex label from EGI
            vertex = egi._vertex_map.get(vertex_id)
            label = vertex.label if vertex and vertex.label else ""
            
            vertex_item = InteractiveVertexItem(
                vertex_id,
                point,
                style.vertex_radius,
                label,
                style.vertex_rendering_mode
            )
            vertex_item.setZValue(1000.0)  # Always above cuts
            scene.addItem(vertex_item)
            self.vertex_items[vertex_id] = vertex_item
        
        # 4. Render predicates (interactive, top layer)
        # Z-order: 1000+ to be above all cuts
        for pred_id, point in dto.predicate_positions.items():
            # Get predicate name from EGI.rel mapping
            label = egi.rel.get(pred_id, "?")
            
            pred_item = InteractivePredicateItem(pred_id, point, label)
            pred_item.setZValue(1000.0)  # Always above cuts
            scene.addItem(pred_item)
            self.predicate_items[pred_id] = pred_item
        
        # Set scene bounds with validation and generous padding
        vb = dto.viewport_bounds
        width = vb.max_x - vb.min_x
        height = vb.max_y - vb.min_y
        
        # Add generous padding to allow free movement beyond visible bounds
        padding = 500.0  # Large padding for interactive workspace
        
        # Sanity check: reject infinite or invalid bounds
        import math
        if (math.isfinite(width) and math.isfinite(height) and 
            width > 0 and height > 0 and width < 100000 and height < 100000):
            scene.setSceneRect(
                vb.min_x - padding, 
                vb.min_y - padding, 
                width + 2*padding, 
                height + 2*padding
            )
            print(f"Scene rect set: ({vb.min_x - padding}, {vb.min_y - padding}) [{width + 2*padding}x{height + 2*padding}]")
        else:
            print(f"WARNING: Invalid viewport bounds, using fallback")
            # Fallback: calculate from actual items with padding
            item_rect = scene.itemsBoundingRect()
            scene.setSceneRect(
                item_rect.x() - padding,
                item_rect.y() - padding,
                item_rect.width() + 2*padding,
                item_rect.height() + 2*padding
            )
        
        return scene
    
    def _compute_nesting_depth(self, egi: RelationalGraphWithCuts, sheet_id: str) -> Dict[str, int]:
        """Compute nesting depth for each cut (deeper = higher number)."""
        depth_map = {sheet_id: 0}
        
        def get_depth(cut_id: str, visited: set = None) -> int:
            """Recursively calculate depth of a cut."""
            if visited is None:
                visited = set()
            
            if cut_id in visited:
                return 1  # Cycle detection
            visited.add(cut_id)
            
            if cut_id in depth_map:
                return depth_map[cut_id]
            
            # Find which area contains this cut
            for parent_id, contents in egi.area.items():
                if cut_id in contents:
                    # Found parent - depth is parent's depth + 1
                    parent_depth = get_depth(parent_id, visited)
                    depth = parent_depth + 1
                    depth_map[cut_id] = depth
                    return depth
            
            # Not found in any area - assume on sheet
            depth_map[cut_id] = 1
            return 1
        
        # Calculate depth for all cuts
        for cut in egi.Cut:
            if cut.id != sheet_id:
                get_depth(cut.id)
        
        return depth_map
    
    def _compute_polarity_map(self, egi: RelationalGraphWithCuts, sheet_id: str) -> Dict[str, int]:
        """Compute polarity for each cut (alternating odd/even by nesting)."""
        # Polarity is just nesting depth mod 2
        # Sheet = 0 (even/positive), first cut = 1 (odd/negative), etc.
        return self._compute_nesting_depth(egi, sheet_id)
    
    def get_selected_elements(self, scene: QGraphicsScene) -> Set[str]:
        """Get IDs of currently selected elements."""
        selected = set()
        for item in scene.selectedItems():
            if isinstance(item, InteractiveGraphicsItem):
                selected.add(item.element_id)
        return selected
    
    def clear_selection(self, scene: QGraphicsScene):
        """Clear all selections."""
        scene.clearSelection()
    
    def select_elements(self, scene: QGraphicsScene, element_ids: Set[str]):
        """Select specific elements by ID."""
        for item in scene.items():
            if isinstance(item, InteractiveGraphicsItem):
                item.setSelected(item.element_id in element_ids)
