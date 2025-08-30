#!/usr/bin/env python3
"""
Arisbe Unified App Shell (Organon, Ergasterion, Agon)

- Organon: embeds existing EGIMainWindow (read-only browsing/export UI scaffold)
- Ergasterion: embeds tools.drawing_editor.DrawingEditor with Composition/Practice modes
- Agon: placeholder window for future Endoporeutic Game features

Each is a full-window QMainWindow added as a tab for quick switching.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt

# Make repo-level src/ and tools/ importable when running from repo root
import os, sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(REPO_ROOT, "src")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
for p in (SRC_DIR, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Organon window
try:
    from qt_egi_gui import EGIMainWindow as OrganonWindow
except Exception:
    OrganonWindow = None  # type: ignore

# Ergasterion window (DrawingEditor)
try:
    from drawing_editor import DrawingEditor as ErgasterionWindow
except Exception:
    ErgasterionWindow = None  # type: ignore


class AgonMainWindow(QMainWindow):
    """Stub for Agon environment."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe – Agon (stub)")
        central = QWidget(self)
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        from PySide6.QtWidgets import QLabel
        lbl = QLabel("Agon will host the Endoporeutic Game. This is a stub.")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)


class ArisbeUnifiedMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe – Unified")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Instantiate each full-window app and mount as tabs
        self.organon: Optional[QMainWindow] = None
        self.ergasterion: Optional[QMainWindow] = None
        self.agon: Optional[QMainWindow] = None

        # Organon
        if OrganonWindow is not None:
            try:
                self.organon = OrganonWindow()
                self.tabs.addTab(self.organon, "Organon")
            except Exception as e:
                self._warn(f"Failed to initialize Organon: {e}")
        else:
            self._warn("Organon UI not available (EGIMainWindow import failed)")

        # Ergasterion
        if ErgasterionWindow is not None:
            try:
                self.ergasterion = ErgasterionWindow()
                self.tabs.addTab(self.ergasterion, "Ergasterion")
            except Exception as e:
                self._warn(f"Failed to initialize Ergasterion: {e}")
        else:
            self._warn("Ergasterion UI not available (DrawingEditor import failed)")

        # Agon (stub)
        try:
            self.agon = AgonMainWindow()
            self.tabs.addTab(self.agon, "Agon")
        except Exception as e:
            self._warn(f"Failed to initialize Agon: {e}")

        # Default tab
        if self.ergasterion is not None:
            self.tabs.setCurrentWidget(self.ergasterion)
        elif self.organon is not None:
            self.tabs.setCurrentWidget(self.organon)

    def _warn(self, msg: str) -> None:
        try:
            QMessageBox.warning(self, "Arisbe", msg)
        except Exception:
            print(msg)


def main() -> int:
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    w = ArisbeUnifiedMain()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
