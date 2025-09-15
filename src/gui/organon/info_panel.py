from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import corpus_index as cidx


@dataclass
class GraphInfo:
    graph_dir: Path
    info: Dict[str, Any]


class InfoPanel(QWidget):
    saved = Signal(dict)  # emits updated info dict
    discarded = Signal()
    edited = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._graph_dir: Optional[Path] = None
        self._info: Dict[str, Any] = {}
        self._dirty: bool = False
        self._egi_exists: bool = False

        v = QVBoxLayout(self)
        self._status = QLabel("")
        self._status.setWordWrap(True)
        v.addWidget(self._status)

        # Create scrollable form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        form = QFormLayout(scroll_widget)

        # Core fields
        self.txt_id = QLineEdit()
        self.txt_title = QLineEdit()
        self.txt_category = QLineEdit()
        self.txt_tags = QLineEdit()
        self.txt_status = QLineEdit()

        # Enhanced metadata fields
        self.txt_description = QTextEdit()
        self.txt_description.setMaximumHeight(80)
        self.txt_source = QLineEdit()
        self.txt_logical_pattern = QLineEdit()
        self.txt_logical_form = QLineEdit()
        self.txt_natural_language_form = QTextEdit()
        self.txt_natural_language_form.setMaximumHeight(60)
        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(80)

        # Read-only fields for timestamps and links
        self.lbl_created = QLabel()
        self.lbl_updated = QLabel()
        self.lbl_linear_forms = QLabel()

        # Connect text change signals
        for w in (
            self.txt_id,
            self.txt_title,
            self.txt_category,
            self.txt_tags,
            self.txt_status,
            self.txt_source,
            self.txt_logical_pattern,
            self.txt_logical_form,
        ):
            w.textEdited.connect(self._on_edited)
        for w in (self.txt_description, self.txt_natural_language_form, self.txt_notes):
            w.textChanged.connect(self._on_edited)

        # Add form rows
        form.addRow("ID:", self.txt_id)
        form.addRow("Title:", self.txt_title)
        form.addRow("Description:", self.txt_description)
        form.addRow("Category:", self.txt_category)
        form.addRow("Tags (comma-separated):", self.txt_tags)
        form.addRow("Status:", self.txt_status)
        form.addRow("Source:", self.txt_source)
        form.addRow("Logical Pattern:", self.txt_logical_pattern)
        form.addRow("Logical Form:", self.txt_logical_form)
        form.addRow("Natural Language:", self.txt_natural_language_form)
        form.addRow("Notes:", self.txt_notes)
        form.addRow("Created:", self.lbl_created)
        form.addRow("Updated:", self.lbl_updated)
        form.addRow("Linear Forms:", self.lbl_linear_forms)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        v.addWidget(scroll)

        # Actions
        row = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_discard = QPushButton("Discard")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_discard.clicked.connect(self._on_discard)
        row.addWidget(self.btn_save)
        row.addWidget(self.btn_discard)
        v.addLayout(row)
        v.addStretch()

        # Initialize with disabled state until graph is loaded
        for w in (
            self.txt_id,
            self.txt_title,
            self.txt_category,
            self.txt_tags,
            self.txt_status,
            self.txt_description,
            self.txt_source,
            self.txt_logical_pattern,
            self.txt_logical_form,
            self.txt_natural_language_form,
            self.txt_notes,
            self.btn_save,
            self.btn_discard,
        ):
            w.setEnabled(False)

    # Public API
    def load_graph_dir(self, gdir: Path) -> None:
        self._graph_dir = gdir
        try:
            self._info = cidx.read_info(gdir)
        except Exception:
            self._info = {
                "id": gdir.name,
                "title": gdir.name,
                "category": None,
                "tags": [],
            }

        self._populate_fields()
        self._dirty = False
        self._update_status()
        self._update_enabled_based_on_field_source()

    # Internals
    def _populate_fields(self) -> None:
        id_ = self._info.get("id") or ""
        title = self._info.get("title") or ""
        category = self._info.get("category") or ""
        tags_list = self._info.get("tags") or []
        tags = ", ".join(tags_list)
        status = self._info.get("status") or "draft"

        # Enhanced metadata fields
        description = self._info.get("description") or ""
        source = self._info.get("source") or ""
        logical_pattern = self._info.get("logical_pattern") or ""
        logical_form = self._info.get("logical_form") or ""
        natural_language_form = self._info.get("natural_language_form") or ""
        notes = self._info.get("notes") or ""

        self.txt_id.setText(id_)
        self.txt_title.setText(title)
        self.txt_category.setText(category)
        self.txt_tags.setText(tags)
        self.txt_status.setText(status)
        self.txt_description.setPlainText(description)
        self.txt_source.setText(source)
        self.txt_logical_pattern.setText(logical_pattern)
        self.txt_logical_form.setText(logical_form)
        self.txt_natural_language_form.setPlainText(natural_language_form)
        self.txt_notes.setPlainText(notes)

        # Timestamps
        created = self._info.get("created", "")
        updated = self._info.get("updated", "")
        self.lbl_created.setText(
            created[:19] if created else ""
        )  # Show YYYY-MM-DD HH:MM:SS
        self.lbl_updated.setText(updated[:19] if updated else "")

        # Linear forms summary
        linear_forms = self._info.get("linear_forms", {})
        forms_summary = []
        for fmt in ["egif", "cgif", "clif"]:
            if fmt in linear_forms:
                forms_summary.append(fmt.upper())
        self.lbl_linear_forms.setText(
            ", ".join(forms_summary) if forms_summary else "None"
        )

    def _collect_fields(self) -> Dict[str, Any]:
        id_ = self.txt_id.text().strip()
        title = self.txt_title.text().strip() or id_
        category = self.txt_category.text().strip() or None
        tags = [t.strip() for t in self.txt_tags.text().split(",") if t.strip()]

        # Enhanced metadata
        description = self.txt_description.toPlainText().strip() or None
        source = self.txt_source.text().strip() or None
        logical_pattern = self.txt_logical_pattern.text().strip() or None
        logical_form = self.txt_logical_form.text().strip() or None
        natural_language_form = (
            self.txt_natural_language_form.toPlainText().strip() or None
        )
        notes = self.txt_notes.toPlainText().strip() or None

        info = dict(self._info)
        info.update(
            {
                "id": id_,
                "title": title,
                "category": category,
                "tags": tags,
                "status": self.txt_status.text().strip() or "draft",
                "description": description,
                "source": source,
                "logical_pattern": logical_pattern,
                "logical_form": logical_form,
                "natural_language_form": natural_language_form,
                "notes": notes,
            }
        )
        return info

    def _update_enabled_based_on_field_source(self) -> None:
        """Enable/disable fields based on their data source, not EGI state."""
        # Enable all editable widgets when graph is loaded
        for w in (
            self.txt_title,
            self.txt_category,
            self.txt_tags,
            self.txt_status,
            self.txt_description,
            self.txt_source,
            self.txt_logical_pattern,
            self.txt_notes,
            self.btn_save,
            self.btn_discard,
        ):
            w.setEnabled(True)

        # ID: read-only once set (inherited from index) but still enabled
        self.txt_id.setEnabled(True)
        self.txt_id.setReadOnly(True)

        # All user metadata fields are always editable
        self.txt_title.setReadOnly(False)
        self.txt_category.setReadOnly(False)
        self.txt_tags.setReadOnly(False)
        self.txt_status.setReadOnly(False)
        self.txt_description.setReadOnly(False)
        self.txt_source.setReadOnly(False)
        self.txt_logical_pattern.setReadOnly(False)
        self.txt_notes.setReadOnly(False)

        # Linear forms: editable only if blank (derived from EGI when populated)
        logical_form = (self._info.get("logical_form") or "").strip()
        natural_language_form = (self._info.get("natural_language_form") or "").strip()

        self.txt_logical_form.setEnabled(True)
        self.txt_natural_language_form.setEnabled(True)
        self.txt_logical_form.setReadOnly(bool(logical_form))
        self.txt_natural_language_form.setReadOnly(bool(natural_language_form))

    def _update_status(self) -> None:
        if not self._graph_dir:
            self._status.setText("No graph selected")
            return
        tag_badge = (
            ("[" + ", ".join(self._info.get("tags") or []) + "]")
            if self._info.get("tags")
            else ""
        )
        self._status.setText(f"Editing: {self._graph_dir.name}  {tag_badge}")

    def _on_edited(self, *_):
        self._dirty = True
        self.edited.emit()

    def _on_save(self) -> None:
        if not self._graph_dir:
            return
        updated = self._collect_fields()
        try:
            cidx.write_info(self._graph_dir, updated)
            # Also upsert index entry to reflect changes in list
            entry = {
                "id": updated.get("id"),
                "title": updated.get("title"),
                "category": updated.get("category"),
                "tags": updated.get("tags", []),
                "path": str(self._graph_dir.relative_to(cidx.REPO_ROOT)),
                "updated": updated.get("updated"),
            }
            cidx.upsert_entry(entry)
        except Exception:
            pass
        self._info = updated
        self._dirty = False
        self._update_status()
        self.saved.emit(dict(self._info))

    def _on_discard(self) -> None:
        if not self._graph_dir:
            return
        # reload from disk
        try:
            self._info = cidx.read_info(self._graph_dir)
        except Exception:
            pass
        self._populate_fields()
        self._dirty = False
        self._update_status()
        self.discarded.emit()
