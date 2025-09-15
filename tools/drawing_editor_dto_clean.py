#!/usr/bin/env python3
"""
Ergasterion Drawing Editor with Proper Default EG Styling

This version uses the actual default theme styling and eliminates all repositioning.
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent / "Arisbe" / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Import existing components
try:
    from diagram_coordinator import DiagramCoordinator, Point2D
    from styling.style_manager import StyleManager

    print("All imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class ProperStyledResizeHandle(QGraphicsEllipseItem):
    """Resize handle with proper styling."""

    def __init__(self, parent_cut, corner):
        super().__init__(QRectF(-4, -4, 8, 8))
        self.parent_cut = parent_cut
        self.corner = corner
        self.setParentItem(parent_cut)

        # Small blue handles for visibility
        self.setBrush(QBrush(QColor("#4444ff")))
        self.setPen(QPen(QColor("#000000"), 1))

        self.update_position()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    def update_position(self):
        """Update handle position."""
        rect = self.parent_cut.rect()

        if self.corner == 0:  # Top-left
            self.setPos(rect.left(), rect.top())
        elif self.corner == 1:  # Top-right
            self.setPos(rect.right(), rect.top())
        elif self.corner == 2:  # Bottom-left
            self.setPos(rect.left(), rect.bottom())
        elif self.corner == 3:  # Bottom-right
            self.setPos(rect.right(), rect.bottom())

    def mousePressEvent(self, event):
        """Start resize."""
        self.resize_start_pos = self.pos()
        self.resize_start_rect = self.parent_cut.rect()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle resize."""
        super().mouseMoveEvent(event)

        current_pos = self.pos()
        delta = current_pos - self.resize_start_pos
        old_rect = self.resize_start_rect

        # Calculate new rectangle
        if self.corner == 0:  # Top-left
            new_rect = QRectF(
                old_rect.left() + delta.x(),
                old_rect.top() + delta.y(),
                old_rect.width() - delta.x(),
                old_rect.height() - delta.y(),
            )
        elif self.corner == 1:  # Top-right
            new_rect = QRectF(
                old_rect.left(),
                old_rect.top() + delta.y(),
                old_rect.width() + delta.x(),
                old_rect.height() - delta.y(),
            )
        elif self.corner == 2:  # Bottom-left
            new_rect = QRectF(
                old_rect.left() + delta.x(),
                old_rect.top(),
                old_rect.width() - delta.x(),
                old_rect.height() + delta.y(),
            )
        elif self.corner == 3:  # Bottom-right
            new_rect = QRectF(
                old_rect.left(),
                old_rect.top(),
                old_rect.width() + delta.x(),
                old_rect.height() + delta.y(),
            )

        # Enforce minimum size
        if new_rect.width() > 50 and new_rect.height() > 30:
            self.parent_cut.setRect(new_rect)
            self.parent_cut.update_handles()


class ProperStyledCut(QGraphicsRectItem):
    """Cut with proper default EG styling."""

    def __init__(self, rect, cut_id, style_manager):
        super().__init__(rect)
        self.cut_id = cut_id
        self.style_manager = style_manager
        self.handles = []

        # Apply proper default EG cut styling
        self._apply_proper_cut_style()

        # Make it movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Create resize handles
        self.create_handles()

    def _apply_proper_cut_style(self):
        """Apply proper default EG cut styling from theme."""
        try:
            # Get cut border style from theme
            cut_style = self.style_manager.resolve(type="cut", role="border")

            # Extract styling values
            border_color = cut_style.get("border_color", "#000000")
            border_width = cut_style.get("border_width", 2)
            fill_color = cut_style.get("fill_color", "transparent")

            # Apply styling
            pen = QPen(QColor(border_color), border_width)

            if fill_color == "transparent":
                brush = QBrush(Qt.GlobalColor.transparent)
            else:
                brush = QBrush(QColor(fill_color))

            self.setPen(pen)
            self.setBrush(brush)

            print(
                f"Applied cut style: border={border_color} width={border_width} fill={fill_color}"
            )

        except Exception as e:
            print(f"Error applying cut style: {e}")
            # Fallback to basic styling
            self.setPen(QPen(QColor("#000000"), 2))
            self.setBrush(QBrush(Qt.GlobalColor.transparent))

    def create_handles(self):
        """Create resize handles."""
        for handle in self.handles:
            if handle.scene():
                handle.scene().removeItem(handle)
        self.handles.clear()

        for i in range(4):
            handle = ProperStyledResizeHandle(self, i)
            self.handles.append(handle)

    def update_handles(self):
        """Update all handle positions."""
        for handle in self.handles:
            handle.update_position()

    def mousePressEvent(self, event):
        """Only allow moving if clicked on border."""
        rect = self.rect()
        pos = event.pos()

        # Check if near border (within 15 pixels)
        margin = 15
        near_border = (
            pos.x() < margin
            or pos.x() > rect.width() - margin
            or pos.y() < margin
            or pos.y() > rect.height() - margin
        )

        if near_border:
            super().mousePressEvent(event)
        else:
            event.ignore()


class ProperStyledDrawingView(QGraphicsView):
    """Drawing view with proper default EG styling and NO repositioning."""

    def __init__(self, scene, coordinator, style_manager):
        super().__init__(scene)
        self.coordinator = coordinator
        self.style_manager = style_manager

        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def mousePressEvent(self, event):
        """Handle mouse press - NO REPOSITIONING LOGIC."""
        if event.button() == Qt.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._show_context_menu(event.position().toPoint(), scene_pos)
        else:
            # Just pass through - no custom drag logic
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release - NO REPOSITIONING LOGIC."""
        # Just pass through - no validation or repositioning
        super().mouseReleaseEvent(event)

    def _show_context_menu(self, view_pos, scene_pos):
        """Show context menu."""
        area_info = self._detect_area(scene_pos)

        menu = QMenu(self)

        vertex_action = menu.addAction(f"Create Vertex in {area_info['type']}")
        vertex_action.triggered.connect(
            lambda: self._create_vertex(scene_pos, area_info)
        )

        predicate_action = menu.addAction(f"Create Predicate in {area_info['type']}")
        predicate_action.triggered.connect(
            lambda: self._create_predicate(scene_pos, area_info)
        )

        cut_action = menu.addAction(f"Create Cut in {area_info['type']}")
        cut_action.triggered.connect(lambda: self._create_cut(scene_pos, area_info))

        menu.exec(self.mapToGlobal(view_pos))

    def _detect_area(self, scene_pos):
        """Detect area."""
        # Check all cuts to see if we're inside any enclosed area
        for item in self.scene().items():
            if isinstance(item, ProperStyledCut):
                cut_rect = item.mapRectToScene(item.rect())
                if cut_rect.contains(scene_pos):
                    return {
                        "type": f"cut_{item.cut_id}_area",
                        "area_id": f"cut_{item.cut_id}",
                        "cut_id": item.cut_id,
                    }

        return {"type": "sheet", "area_id": "sheet"}

    def _create_vertex(self, scene_pos, area_info):
        """Create vertex with proper default EG styling."""
        try:
            position = Point2D(scene_pos.x(), scene_pos.y())
            vertex_id = self.coordinator.create_vertex(position, area_info["area_id"])

            if vertex_id:
                # Create vertex with proper default EG styling
                vertex = self._create_proper_styled_vertex(scene_pos.x(), scene_pos.y())
                vertex.vertex_id = vertex_id
                self.scene().addItem(vertex)
                print(
                    f"Created properly styled vertex {vertex_id} at exact position {scene_pos}"
                )

        except Exception as e:
            print(f"Error creating vertex: {e}")

    def _create_predicate(self, scene_pos, area_info):
        """Create predicate with proper default EG styling."""
        text, ok = QInputDialog.getText(
            self, "Create Predicate", "Enter predicate name:"
        )
        if ok and text:
            try:
                position = Point2D(scene_pos.x(), scene_pos.y())
                predicate_id = self.coordinator.create_predicate(
                    text, position, area_info["area_id"]
                )

                if predicate_id:
                    # Create predicate with proper default EG styling
                    predicate = self._create_proper_styled_predicate(
                        text, scene_pos.x(), scene_pos.y()
                    )
                    predicate.predicate_id = predicate_id
                    self.scene().addItem(predicate)
                    print(
                        f"Created properly styled predicate {predicate_id} '{text}' at exact position {scene_pos}"
                    )

            except Exception as e:
                print(f"Error creating predicate: {e}")

    def _create_cut(self, scene_pos, area_info):
        """Create cut with proper default EG styling."""
        try:
            width = 150.0
            height = 100.0

            cut_id = self.coordinator.create_cut(
                scene_pos.x(), scene_pos.y(), width, height, area_info["area_id"]
            )

            if cut_id:
                # Create cut with proper default EG styling
                rect = QRectF(0, 0, width, height)
                cut = ProperStyledCut(rect, cut_id, self.style_manager)
                cut.setPos(scene_pos.x(), scene_pos.y())

                self.scene().addItem(cut)
                print(
                    f"Created properly styled cut {cut_id} at exact position {scene_pos}"
                )

        except Exception as e:
            print(f"Error creating cut: {e}")

    def _create_proper_styled_vertex(self, x, y):
        """Create vertex with proper default EG styling from theme."""
        try:
            # Get vertex dot style from theme
            vertex_style = self.style_manager.resolve(type="vertex", role="dot")

            # Extract styling values
            fill_color = vertex_style.get("fill_color", "#000000")
            border_color = vertex_style.get("border_color", "#000000")
            border_width = vertex_style.get("border_width", 1)
            radius = vertex_style.get("radius", 3)

            # Create vertex
            vertex = QGraphicsEllipseItem(
                QRectF(-radius, -radius, 2 * radius, 2 * radius)
            )
            vertex.setPos(x, y)

            # Apply proper styling
            vertex.setPen(QPen(QColor(border_color), border_width))
            vertex.setBrush(QBrush(QColor(fill_color)))

            # Make it movable
            vertex.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            vertex.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

            print(
                f"Applied vertex style: fill={fill_color} border={border_color} width={border_width} radius={radius}"
            )

            return vertex

        except Exception as e:
            print(f"Error creating styled vertex: {e}")
            # Fallback
            vertex = QGraphicsEllipseItem(QRectF(-3, -3, 6, 6))
            vertex.setPos(x, y)
            vertex.setPen(QPen(QColor("#000000"), 1))
            vertex.setBrush(QBrush(QColor("#000000")))
            vertex.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            vertex.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            return vertex

    def _create_proper_styled_predicate(self, text, x, y):
        """Create predicate with proper default EG styling from theme."""
        try:
            # Get global font style from theme
            global_style = self.style_manager.resolve(type="global")

            # Extract font values
            font_family = global_style.get("font_family", "Arial")
            font_size = global_style.get("font_size", 10)

            # Create predicate
            predicate = QGraphicsTextItem(text)
            predicate.setPos(x, y)

            # Apply proper font styling
            font = QFont(font_family, font_size)
            predicate.setFont(font)
            predicate.setDefaultTextColor(QColor("#000000"))

            # Make it movable
            predicate.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            predicate.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

            print(f"Applied predicate style: font={font_family} size={font_size}")

            return predicate

        except Exception as e:
            print(f"Error creating styled predicate: {e}")
            # Fallback
            predicate = QGraphicsTextItem(text)
            predicate.setPos(x, y)
            predicate.setFont(QFont("Arial", 10))
            predicate.setDefaultTextColor(QColor("#000000"))
            predicate.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            predicate.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            return predicate


class ProperDefaultStyledEditor(QMainWindow):
    """Editor with proper default EG styling and no repositioning."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ergasterion - Proper Default EG Styling")
        self.setGeometry(100, 100, 800, 600)

        try:
            # Initialize components
            self.scene = QGraphicsScene()
            self.style_manager = StyleManager()
            self.coordinator = DiagramCoordinator(self.scene, self.style_manager)

            # Create view with proper styling and no repositioning
            self.view = ProperStyledDrawingView(
                self.scene, self.coordinator, self.style_manager
            )
            self.setCentralWidget(self.view)

            # Status
            self.statusBar().showMessage(
                "Proper default EG styling with no repositioning. Cuts are resizable."
            )

            print("Proper Default Styled Ergasterion Drawing Editor initialized")

        except Exception as e:
            print(f"Error initializing editor: {e}")
            import traceback

            traceback.print_exc()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    try:
        window = ProperDefaultStyledEditor()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
