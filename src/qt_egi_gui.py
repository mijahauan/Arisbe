#!/usr/bin/env python3
"""
Arisbe Qt GUI - Organon Mode (minimal scaffold)

Defines required classes for tests:
- BranchingPointItem, LigatureItem, PredicateItem, CutItem
- EGIGraphicsView, EGIControlPanel, EGIMainWindow

Integrates with EGISystem and QtCorrespondenceIntegration to generate a scene.
"""
from __future__ import annotations

from typing import Any, Dict, List

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath

from egi_system import create_egi_system, EGISystem
from qt_correspondence_integration import create_qt_correspondence_integration
from styling.style_manager import create_style_manager


# --- Minimal graphics items ---
class BranchingPointItem(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, r: float = 6.0):
        super().__init__(x - r / 2, y - r / 2, r, r)
        self.setBrush(QBrush(QColor(0, 0, 0)))
        self.setPen(QPen(QColor(0, 0, 0), 1))


class LigatureItem(QGraphicsLineItem):
    pass


class PredicateItem(QGraphicsTextItem):
    def __init__(self, label: str, x: float, y: float):
        super().__init__(label)
        self.setFont(QFont("Arial", 10))
        rect = self.boundingRect()
        self.setPos(x - rect.width() / 2, y - rect.height() / 2)


class CutItem(QGraphicsRectItem):
    def __init__(self, x: float, y: float, w: float, h: float):
        super().__init__(x, y, w, h)
        pen = QPen(QColor(0, 0, 0), 1)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(240, 240, 240, 60)))


# --- View and control panel ---
class EGIGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene):
        super().__init__(scene)
        self.setRenderHints(self.renderHints())


class EGIControlPanel(QWidget):
    def __init__(self, main_window: 'EGIMainWindow'):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        refresh_btn = QPushButton("Refresh Scene")
        refresh_btn.clicked.connect(self.main_window.refresh_scene)
        layout.addWidget(refresh_btn)
        export_btn = QPushButton("Export TikZ (stub)")
        export_btn.clicked.connect(self.main_window.export_tikz)
        layout.addWidget(export_btn)
        layout.addStretch()


# --- Main window ---
class EGIMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe – Organon")
        self.resize(1000, 700)

        # Core systems
        self.egi_system: EGISystem = create_egi_system()
        self.qt_integration = create_qt_correspondence_integration(self.igi_seed())
        self.style = create_style_manager()

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # Scene and view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.graphics_view = EGIGraphicsView(self.scene)

        # Control panel
        self.control_panel = EGIControlPanel(self)

        root.addWidget(self.graphics_view, 1)
        root.addWidget(self.control_panel)

        # Seed demo content and render
        self.seed_demo_graph()
        self.refresh_scene()

    def igi_seed(self) -> EGISystem:
        """Return EGI system for integration (helper for decoupled construction)."""
        return self.egi_system

    def seed_demo_graph(self):
        """Populate a small demo graph: Person(Tom), Happy(Tom), and a cut."""
        self.egi_system.insert_vertex("Tom")
        self.egi_system.insert_edge("e1", "Person", ["Tom"])
        self.egi_system.insert_edge("e2", "Happy", ["Tom"])
        self.egi_system.insert_cut("cut_1")

    def clear_scene(self):
        self.scene.clear()

    def refresh_scene(self):
        self.clear_scene()
        # Regenerate integration each refresh to reflect current EGI
        self.qt_integration = create_qt_correspondence_integration(self.egi_system)
        scene_data = self.qt_integration.generate_qt_scene()
        for cmd in scene_data.get("render_commands", []):
            self._emit_command(cmd)

    def _emit_command(self, cmd: Dict[str, Any]):
        typ = cmd.get("type")
        role = cmd.get("role")
        b = cmd.get("bounds", {})
        x, y, w, h = b.get("x", 0.0), b.get("y", 0.0), b.get("width", 0.0), b.get("height", 0.0)

        if typ == "vertex":
            # Draw small spot and label
            s = self.style.resolve(type="vertex", role=role)
            radius = float(s.get("radius", 3))
            fill = QColor(s.get("fill_color", "#000000"))
            border_color = QColor(s.get("border_color", "#000000"))
            border_w = float(s.get("border_width", 1))
            spot = QGraphicsEllipseItem(x + w / 2 - radius, y + h / 2 - radius, 2 * radius, 2 * radius)
            spot.setBrush(QBrush(fill))
            spot.setPen(QPen(border_color, border_w))
            self.scene.addItem(spot)
            label = QGraphicsTextItem(cmd.get("vertex_name", cmd.get("element_id", "")))
            g = self.style.resolve(type="vertex", role="vertex.label")
            label.setFont(QFont(g.get("font_family", "Arial"), int(g.get("font_size", 9))))
            label.setPos(x + w / 2 + 8, y + h / 2 - 8)
            self.scene.addItem(label)
        elif typ == "edge":
            # Draw predicate background exactly matching engine-provided bounds with thin border
            s = self.style.resolve(type="edge", role=role)
            # Border transparent per spec
            border_color = QColor(s.get("border_color", "transparent"))
            border_w = float(s.get("border_width", 1))
            # Fill should track the cut fill based on area parity
            ap = int(cmd.get("area_parity", 0))
            s_fill_cut = self.style.resolve(type="cut", role="cut.fill")
            cut_fill_color = QColor(s_fill_cut.get("fill_color", "rgba(240,240,240,0.31)"))
            fill_color = cut_fill_color if ap == 1 else QColor("transparent")
            bg = QGraphicsRectItem(x, y, w, h)
            bg.setPen(QPen(border_color, border_w))
            bg.setBrush(QBrush(fill_color))
            self.scene.addItem(bg)

            # Center text within that rectangle
            text = QGraphicsTextItem(cmd.get("relation_name", cmd.get("element_id", "")))
            g = self.style.resolve(type="edge", role="edge.label_text")
            text.setFont(QFont(g.get("font_family", "Arial"), int(g.get("font_size", 10))))
            rect = text.boundingRect()
            tx = x + (w - rect.width()) / 2
            ty = y + (h - rect.height()) / 2
            text.setPos(tx, ty)
            self.scene.addItem(text)
        elif typ == "cut":
            # Rounded rectangle cut
            s_border = self.style.resolve(type="cut", role=role)
            s_fill = self.style.resolve(type="cut", role="cut.fill")
            radius = float(s_border.get("radius", 10))
            line_w = float(s_border.get("line_width", 1))
            line_color = QColor(s_border.get("line_color", "#000000"))
            # Fill depends on area parity: odd=shaded, even=transparent
            ap = int(cmd.get("area_parity", 0))
            shaded = QColor(s_fill.get("fill_color", "rgba(240,240,240,0.31)"))
            fill_color = shaded if ap == 1 else QColor("transparent")
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, w, h), radius, radius)
            path_item = self.scene.addPath(path, QPen(line_color, line_w), QBrush(fill_color))
            path_item.setZValue(-1)
        elif typ == "ligature":
            pts = cmd.get("path_points", []) or []
            if len(pts) >= 2:
                path = QPainterPath()
                x0, y0 = pts[0]
                path.moveTo(x0, y0)
                for x1, y1 in pts[1:]:
                    path.lineTo(x1, y1)
                s = self.style.resolve(type="ligature", role=role)
                pen = QPen(QColor(s.get("line_color", "#000000")), float(s.get("line_width", 3)))
                try:
                    from PyQt6.QtCore import Qt as QtCoreQt
                    cap = str(s.get("cap", "round")).lower()
                    if cap == "round":
                        pen.setCapStyle(QtCoreQt.PenCapStyle.RoundCap)
                    elif cap == "square":
                        pen.setCapStyle(QtCoreQt.PenCapStyle.SquareCap)
                    else:
                        pen.setCapStyle(QtCoreQt.PenCapStyle.FlatCap)
                except Exception:
                    pass
                self.scene.addPath(path, pen)

                # Optional: draw small markers at hook endpoints to aid debugging visibility
                import os
                if os.environ.get('ARISBE_DEBUG_HOOKS') == '1':
                    base_pt = pts[0]
                    for i, (hx, hy) in enumerate(pts[1:], start=1):
                        # Consider a hook point if followed by base or if it's not equal to base
                        is_base = (hx, hy) == base_pt
                        next_is_base = (i + 1 < len(pts)) and (pts[i + 1] == base_pt)
                        if not is_base and next_is_base:
                            marker = QGraphicsEllipseItem(hx - 2, hy - 2, 4, 4)
                            marker.setBrush(QBrush(QColor(220, 0, 0)))
                            marker.setPen(QPen(QColor(220, 0, 0), 0))
                            self.scene.addItem(marker)

    def export_tikz(self):
        # Generate TikZ from current scene via correspondence integration
        try:
            from export.tikz_exporter import generate_tikz
        except Exception:
            # Fallback import path if module-style import fails
            from .export.tikz_exporter import generate_tikz  # type: ignore

        # Ensure we use the freshest commands
        self.qt_integration = create_qt_correspondence_integration(self.egi_system)
        scene_data = self.qt_integration.generate_qt_scene()
        render_commands = scene_data.get("render_commands", [])

        tikz_doc = generate_tikz(render_commands, standalone=True)

        # Write to project-local file
        import os
        out_path = os.path.join(os.getcwd(), "arisbe_export.tex")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(tikz_doc)
            print(f"[TikZ Export] Wrote {len(tikz_doc)} chars to {out_path}")
        except Exception as e:
            print(f"[TikZ Export] Failed to write TikZ: {e}")


def main():
    import sys
    app = QApplication(sys.argv)
    win = EGIMainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
