"""
Serialization Panel for Organon - displays various serialization formats of EGI.
Shows JSON, XML, and binary representations alongside export options.
"""

from __future__ import annotations

import json
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

from egi_core_dau import RelationalGraphWithCuts
from egi_loader import serialize_egi_to_dict


class SerializationPanel(QWidget):
    """
    Display panel for various serialization formats of EGI data.
    Shows JSON, XML, and other structured representations.
    """

    exported = Signal(str)  # emits which format was exported

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._graph: Optional[RelationalGraphWithCuts] = None

        v = QVBoxLayout(self)
        self.tabs = QTabWidget()
        v.addWidget(self.tabs)

        # Read-only serialization displays
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setFont(self._get_monospace_font())
        
        self.xml_display = QTextEdit()
        self.xml_display.setReadOnly(True)
        self.xml_display.setFont(self._get_monospace_font())
        
        self.yaml_display = QTextEdit()
        self.yaml_display.setReadOnly(True)
        self.yaml_display.setFont(self._get_monospace_font())

        self.tabs.addTab(self.json_display, "JSON")
        self.tabs.addTab(self.xml_display, "XML")
        self.tabs.addTab(self.yaml_display, "YAML")

        # Control buttons
        hb = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_copy = QPushButton("Copy Current")
        self.btn_export = QPushButton("Export...")
        
        hb.addWidget(self.btn_refresh)
        hb.addWidget(self.btn_copy)
        hb.addWidget(self.btn_export)
        hb.addStretch(1)
        v.addLayout(hb)

        # Connect signals
        self.btn_refresh.clicked.connect(self._on_refresh)
        self.btn_copy.clicked.connect(self._on_copy_current)
        self.btn_export.clicked.connect(self._on_export)

        self._set_enabled(False)

    def _get_monospace_font(self):
        """Get monospace font for code display."""
        from PySide6.QtGui import QFont
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font

    def clear(self) -> None:
        """Clear all displays and disable controls."""
        self._graph = None
        self.json_display.clear()
        self.xml_display.clear()
        self.yaml_display.clear()
        self._set_enabled(False)

    def set_graph(self, graph: RelationalGraphWithCuts) -> None:
        """Set the EGI graph and generate serializations."""
        self._graph = graph
        self._set_enabled(True)
        self._on_refresh()

    def _set_enabled(self, enabled: bool) -> None:
        """Enable/disable all controls."""
        self.tabs.setEnabled(enabled)
        self.btn_refresh.setEnabled(enabled)
        self.btn_copy.setEnabled(enabled)
        self.btn_export.setEnabled(enabled)

    def _on_refresh(self) -> None:
        """Generate all serialization formats."""
        if not self._graph:
            return

        # Generate JSON serialization
        try:
            egi_dict = serialize_egi_to_dict(self._graph)
            json_str = json.dumps(egi_dict, indent=2, ensure_ascii=False)
            self.json_display.setPlainText(json_str)
        except Exception as e:
            self.json_display.setPlainText(f"JSON serialization error: {e}")

        # Generate XML serialization
        try:
            xml_str = self._generate_xml_serialization(self._graph)
            self.xml_display.setPlainText(xml_str)
        except Exception as e:
            self.xml_display.setPlainText(f"XML serialization error: {e}")

        # Generate YAML serialization
        try:
            yaml_str = self._generate_yaml_serialization(self._graph)
            self.yaml_display.setPlainText(yaml_str)
        except Exception as e:
            self.yaml_display.setPlainText(f"YAML serialization error: {e}")

    def _generate_xml_serialization(self, graph: RelationalGraphWithCuts) -> str:
        """Generate XML representation of EGI."""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<egi>')
        
        # Vertices
        xml_lines.append('  <vertices>')
        for vertex in graph.V:
            xml_lines.append(f'    <vertex id="{vertex.id}" />')
        xml_lines.append('  </vertices>')
        
        # Edges
        xml_lines.append('  <edges>')
        for edge in graph.E:
            xml_lines.append(f'    <edge id="{edge.id}" />')
        xml_lines.append('  </edges>')
        
        # Cuts
        xml_lines.append('  <cuts>')
        for cut in graph.Cut:
            xml_lines.append(f'    <cut id="{cut.id}" />')
        xml_lines.append('  </cuts>')
        
        # Nu mapping
        xml_lines.append('  <nu_mapping>')
        for edge_id, vertex_ids in graph.nu.items():
            vertex_list = ' '.join(str(vid) for vid in vertex_ids)
            xml_lines.append(f'    <mapping edge="{edge_id}" vertices="{vertex_list}" />')
        xml_lines.append('  </nu_mapping>')
        
        # Area mapping
        xml_lines.append('  <area_mapping>')
        for area_id, element_ids in graph.area.items():
            element_list = ' '.join(str(eid) for eid in element_ids)
            xml_lines.append(f'    <area id="{area_id}" elements="{element_list}" />')
        xml_lines.append('  </area_mapping>')
        
        xml_lines.append('</egi>')
        return '\n'.join(xml_lines)

    def _generate_yaml_serialization(self, graph: RelationalGraphWithCuts) -> str:
        """Generate YAML representation of EGI."""
        yaml_lines = ['# EGI YAML Serialization']
        yaml_lines.append('egi:')
        
        # Vertices
        yaml_lines.append('  vertices:')
        for vertex in graph.V:
            yaml_lines.append(f'    - id: {vertex.id}')
        
        # Edges
        yaml_lines.append('  edges:')
        for edge in graph.E:
            yaml_lines.append(f'    - id: {edge.id}')
        
        # Cuts
        yaml_lines.append('  cuts:')
        for cut in graph.Cut:
            yaml_lines.append(f'    - id: {cut.id}')
        
        # Nu mapping
        yaml_lines.append('  nu_mapping:')
        for edge_id, vertex_ids in graph.nu.items():
            vertex_list = [str(vid) for vid in vertex_ids]
            yaml_lines.append(f'    {edge_id}: [{", ".join(vertex_list)}]')
        
        # Area mapping
        yaml_lines.append('  area_mapping:')
        for area_id, element_ids in graph.area.items():
            element_list = [str(eid) for eid in element_ids]
            yaml_lines.append(f'    {area_id}: [{", ".join(element_list)}]')
        
        return '\n'.join(yaml_lines)

    def _on_copy_current(self) -> None:
        """Copy current tab content to clipboard."""
        current_widget = self.tabs.currentWidget()
        tab_name = self.tabs.tabText(self.tabs.currentIndex())
        
        if isinstance(current_widget, QTextEdit):
            current_widget.selectAll()
            current_widget.copy()
            QMessageBox.information(self, "Copied", f"{tab_name} serialization copied to clipboard.")
        else:
            QMessageBox.warning(self, "Copy", "Nothing to copy on this tab.")

    def _on_export(self) -> None:
        """Export current serialization to file."""
        from PySide6.QtWidgets import QFileDialog
        
        tab_name = self.tabs.tabText(self.tabs.currentIndex()).lower()
        current_widget = self.tabs.currentWidget()
        
        if not isinstance(current_widget, QTextEdit):
            QMessageBox.warning(self, "Export", "Nothing to export on this tab.")
            return
        
        # File dialog for export
        file_filter = {
            'json': 'JSON Files (*.json)',
            'xml': 'XML Files (*.xml)',
            'yaml': 'YAML Files (*.yaml *.yml)'
        }.get(tab_name, 'Text Files (*.txt)')
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            f"Export {tab_name.upper()}", 
            f"egi_serialization.{tab_name}",
            file_filter
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(current_widget.toPlainText())
                QMessageBox.information(self, "Export", f"{tab_name.upper()} exported to {file_path}")
                self.exported.emit(tab_name)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export {tab_name}: {e}")
