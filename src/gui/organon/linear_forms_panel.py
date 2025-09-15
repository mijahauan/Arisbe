from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cgif_generator_dau import CGIFGenerator, generate_cgif
from cgif_parser_dau import CGIFParser
from clif_generator_dau import (
    CLIFGenerator,
    generate_clif,
    generate_clif_with_quantification,
)
from egi_core_dau import RelationalGraphWithCuts
from egif_generator_dau import EGIFGenerator, generate_egif
from egif_parser_dau import EGIFParser


class LinearFormsPanel(QWidget):
    """
    Read-only display of generated linear forms (EGIF, CGIF, CLIF).
    Caller provides a `RelationalGraphWithCuts`. Panel generates on demand.
    """

    copied = Signal(str)  # emits which format was copied

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._graph: Optional[RelationalGraphWithCuts] = None

        v = QVBoxLayout(self)
        self.tabs = QTabWidget()
        v.addWidget(self.tabs)

        # Read-only editors
        self.egif_display = QTextEdit()
        self.egif_display.setReadOnly(True)
        self.cgif_display = QTextEdit()
        self.cgif_display.setReadOnly(True)
        self.clif_display = QTextEdit()
        self.clif_display.setReadOnly(True)

        self.tabs.addTab(self.egif_display, "EGIF")
        self.tabs.addTab(self.cgif_display, "CGIF")
        self.tabs.addTab(self.clif_display, "CLIF")

        # Buttons
        hb = QHBoxLayout()
        self.btn_generate = QPushButton("Generate")
        self.btn_copy = QPushButton("Copy Current")
        hb.addWidget(self.btn_generate)
        hb.addWidget(self.btn_copy)
        hb.addStretch(1)
        v.addLayout(hb)

        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_copy.clicked.connect(self._on_copy_current)

        self._set_enabled(False)

    def clear(self) -> None:
        self._graph = None
        self.egif_display.clear()
        self.cgif_display.clear()
        self.clif_display.clear()
        self._set_enabled(False)

    def set_graph(self, graph: RelationalGraphWithCuts) -> None:
        self._graph = graph
        self._set_enabled(True)
        self._on_generate()

    def _set_enabled(self, enabled: bool) -> None:
        self.tabs.setEnabled(enabled)
        self.btn_generate.setEnabled(enabled)
        self.btn_copy.setEnabled(enabled)

    def _on_generate(self) -> None:
        if not self._graph:
            return
        try:
            egif_str = generate_egif(self._graph)
        except Exception as e:
            egif_str = f"EGIF error: {e}"
        try:
            cgif_str = generate_cgif(self._graph)
        except Exception as e:
            cgif_str = f"CGIF error: {e}"
        try:
            clif_str = generate_clif(self._graph)
        except Exception as e:
            clif_str = f"CLIF error: {e}"
        self.egif_display.setPlainText(egif_str)
        self.cgif_display.setPlainText(cgif_str)
        self.clif_display.setPlainText(clif_str)

    def _on_copy_current(self) -> None:
        w = self.tabs.currentWidget()
        label = self.tabs.tabText(self.tabs.currentIndex())
        if isinstance(w, QTextEdit):
            w.selectAll()
            w.copy()
            self.copied.emit(label)
        else:
            try:
                QMessageBox.information(self, "Copy", "Nothing to copy on this tab.")
            except Exception:
                pass
