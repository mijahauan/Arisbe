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

# Enforce PySide6 and block PyQt6 before any Qt import to avoid mixed bindings
import os as _os, sys as _sys
_os.environ.setdefault("QT_API", "pyside6")
if "PyQt6" in _sys.modules:
    # If some dependency already imported PyQt6, neutralize it to prevent loading frameworks
    _sys.modules["PyQt6"] = None  # type: ignore[assignment]

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

# Organon window: force new modular OrganonMainWindow (no legacy fallback)
OrganonWindow = None  # type: ignore
try:
    # Import from src/organon/ when src/ is on path
    import sys
    import os
    organon_path = os.path.join(SRC_DIR, 'organon')
    if organon_path not in sys.path:
        sys.path.insert(0, organon_path)
    from main_window import OrganonMainWindow as _NewOrganon
    OrganonWindow = _NewOrganon  # type: ignore
    try:
        import inspect
        print(f"[Organon] Using new OrganonMainWindow from: {inspect.getsourcefile(_NewOrganon)}")
    except Exception:
        print("[Organon] Using new OrganonMainWindow")
except Exception as _new_exc:
    import traceback as _tb
    print("[Organon] ERROR: New OrganonMainWindow failed to import. No legacy fallback is enabled.")
    try:
        _tb.print_exc()
    except Exception:
        print(str(_new_exc))
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
                import traceback
                tb = traceback.format_exc()
                self._warn(f"Failed to initialize Organon: {e}\n{tb}")
        else:
            self._warn("Organon UI not available (EGIMainWindow import failed)")

        # Ergasterion
        if ErgasterionWindow is not None:
            try:
                self.ergasterion = ErgasterionWindow()
                self.tabs.addTab(self.ergasterion, "Ergasterion")
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self._warn(f"Failed to initialize Ergasterion: {e}\n{tb}")
        else:
            self._warn("Ergasterion UI not available (DrawingEditor import failed)")

        # Agon (stub)
        try:
            self.agon = AgonMainWindow()
            self.tabs.addTab(self.agon, "Agon")
        except Exception as e:
            self._warn(f"Failed to initialize Agon: {e}")

        # Default tab: Organon first
        if self.organon is not None:
            self.tabs.setCurrentWidget(self.organon)
        elif self.ergasterion is not None:
            self.tabs.setCurrentWidget(self.ergasterion)

        # Connect bidirectional handoff if available
        try:
            # Organon → Ergasterion
            if hasattr(self.organon, 'edit_in_ergasterion') and callable(getattr(self.organon, 'edit_in_ergasterion').connect):
                getattr(self.organon, 'edit_in_ergasterion').connect(self._on_edit_in_ergasterion)
            
            # Ergasterion → Organon
            if hasattr(self.ergasterion, 'egi_created_from_diagram') and callable(getattr(self.ergasterion, 'egi_created_from_diagram').connect):
                getattr(self.ergasterion, 'egi_created_from_diagram').connect(self._on_egi_from_ergasterion)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self._warn(f"Failed to connect handoff signals: {e}\n{tb}")

    def _warn(self, msg: str) -> None:
        # Always print to stdout for terminal visibility
        try:
            print(msg)
        except Exception:
            pass
        # Also try to show a message box
        try:
            QMessageBox.warning(self, "Arisbe", msg)
        except Exception:
            pass

    def _on_edit_in_ergasterion(self, payload: dict) -> None:
        """Switch to Ergasterion tab and pass the payload to the embedded editor."""
        try:
            if self.ergasterion is None:
                self._warn("Ergasterion is not available")
                return
            # Switch tab first
            self.tabs.setCurrentWidget(self.ergasterion)
            # Put Ergasterion into embedded mode if API exists
            if hasattr(self.ergasterion, 'set_embedded_mode') and callable(getattr(self.ergasterion, 'set_embedded_mode')):
                try:
                    self.ergasterion.set_embedded_mode(True)
                except Exception:
                    pass
            # Load payload if API exists
            if hasattr(self.ergasterion, 'load_payload') and callable(getattr(self.ergasterion, 'load_payload')):
                self.ergasterion.load_payload(payload)
        except Exception as e:
            self._warn(f"Ergasterion handoff failed: {e}")

    def _on_egi_from_ergasterion(self, payload: dict) -> None:
        """Handle EGI created in Ergasterion, switch to Organon and process."""
        try:
            if self.organon is None:
                self._warn("Organon is not available")
                return
            
            # Switch to Organon tab
            self.tabs.setCurrentWidget(self.organon)
            
            # Pass EGIF to Organon for parsing (if it has the capability)
            if hasattr(self.organon, 'process_egi_from_ergasterion') and callable(getattr(self.organon, 'process_egi_from_ergasterion')):
                self.organon.process_egi_from_ergasterion(payload)
            else:
                self._warn("Organon does not support EGI processing from Ergasterion")
                
        except Exception as e:
            self._warn(f"Ergasterion→Organon handoff failed: {e}")


def main() -> int:
    import sys
    import os
    
    # Suppress tqdm progress bars before any imports
    os.environ['TQDM_DISABLE'] = '1'
    
    # Also suppress tqdm programmatically
    try:
        import tqdm
        # Monkey patch tqdm to do nothing
        tqdm.tqdm.__init__ = lambda self, *args, **kwargs: None
        tqdm.tqdm.update = lambda self, *args, **kwargs: None
        tqdm.tqdm.close = lambda self, *args, **kwargs: None
        tqdm.tqdm.__enter__ = lambda self: self
        tqdm.tqdm.__exit__ = lambda self, *args: None
    except ImportError:
        pass
    
    # OS-level output suppression for progress bar spam from subprocesses
    devnull = os.open(os.devnull, os.O_WRONLY)
    original_stdout_fd = os.dup(1)
    original_stderr_fd = os.dup(2)
    
    try:
        # Redirect file descriptors to /dev/null during initialization
        os.dup2(devnull, 1)  # stdout
        os.dup2(devnull, 2)  # stderr
        
        app = QApplication.instance() or QApplication(sys.argv)
        w = ArisbeUnifiedMain()
        
        # Restore file descriptors after initialization
        os.dup2(original_stdout_fd, 1)
        os.dup2(original_stderr_fd, 2)
        os.close(devnull)
        os.close(original_stdout_fd)
        os.close(original_stderr_fd)
        
        w.show()
        return app.exec()
        
    except Exception as e:
        # Restore file descriptors on error
        try:
            os.dup2(original_stdout_fd, 1)
            os.dup2(original_stderr_fd, 2)
            os.close(devnull)
            os.close(original_stdout_fd)
            os.close(original_stderr_fd)
        except:
            pass
        print(f"Error starting application: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
