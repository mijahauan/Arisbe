from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from export.tikz_exporter import generate_tikz


class ExportsPanel(QWidget):
    """
    Minimal exports UI for Organon. Accepts render_commands and produces TikZ.
    Caller is responsible for providing render_commands array from EGDF or viewer.
    """

    exported = Signal(str)  # path saved

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._render_commands: List[Dict[str, Any]] = []

        v = QVBoxLayout(self)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        v.addWidget(self.output)

        hb = QHBoxLayout()
        self.chk_standalone = QCheckBox("Standalone LaTeX document")
        self.chk_standalone.setChecked(True)
        hb.addWidget(self.chk_standalone)
        hb.addStretch(1)
        v.addLayout(hb)

        hb2 = QHBoxLayout()
        self.btn_generate = QPushButton("Generate TikZ")
        self.btn_save = QPushButton("Save As…")
        hb2.addWidget(self.btn_generate)
        hb2.addWidget(self.btn_save)
        hb2.addStretch(1)
        v.addLayout(hb2)

        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_save.clicked.connect(self._on_save)
        self._set_enabled(False)

    def clear(self) -> None:
        self._render_commands = []
        self.output.clear()
        self._set_enabled(False)

    def set_render_commands(self, cmds: List[Dict[str, Any]]) -> None:
        self._render_commands = list(cmds or [])
        self._set_enabled(bool(self._render_commands))
        if self._render_commands:
            self._on_generate()

    def _set_enabled(self, enabled: bool) -> None:
        self.output.setEnabled(True)  # allow selection even when no cmds
        self.chk_standalone.setEnabled(enabled)
        self.btn_generate.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)

    def _on_generate(self) -> None:
        if not self._render_commands:
            return
        try:
            text = generate_tikz(
                self._render_commands, standalone=self.chk_standalone.isChecked()
            )
        except Exception as e:
            text = f"TikZ error: {e}"
        self.output.setPlainText(text)

    def _on_save(self) -> None:
        if not self.output.toPlainText().strip():
            return
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save TikZ", "diagram.tex", "TeX Files (*.tex)"
            )
        except Exception:
            path = ""
        if not path:
            return
        try:
            Path(path).write_text(self.output.toPlainText(), encoding="utf-8")
            self.exported.emit(path)
        except Exception as e:
            try:
                QMessageBox.critical(self, "Save Error", f"Failed to save TikZ:\n{e}")
            except Exception:
                pass
