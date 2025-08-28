import os
import sys
import pytest

# Ensure Qt runs offscreen for CI/headless
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF

from tools.drawing_editor import DrawingEditor


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def _set_cut_rect(editor: DrawingEditor, cut_id: str, rect: QRectF) -> None:
    c = editor.model.cuts[cut_id]
    c.gfx.setRect(rect)


def _schema_parent_map(editor: DrawingEditor):
    schema = editor._gather_schema_from_scene()
    return {c["id"]: c.get("parent_id") for c in schema["cuts"]}, schema["sheet_id"]


def test_parent_smallest_fully_containing_cut(qapp):
    editor = DrawingEditor()
    # Create two cuts via schema, then adjust geometry
    schema = {
        "sheet_id": "S",
        "cuts": [
            {"id": "outer", "parent_id": "S"},
            {"id": "inner", "parent_id": "S"},  # will be nested by geometry
        ],
        "vertices": [],
        "predicates": [],
        "ligatures": [],
    }
    # Load into editor
    editor.model = editor.model.from_schema(editor.scene, schema)

    # Place outer as large rect; inner fully inside
    _set_cut_rect(editor, "outer", QRectF(100, 100, 400, 300))
    _set_cut_rect(editor, "inner", QRectF(200, 200, 120, 80))

    pm, sheet = _schema_parent_map(editor)
    assert pm["inner"] == "outer"
    assert pm["outer"] == sheet


def test_disjoint_siblings_are_sheet_children(qapp):
    editor = DrawingEditor()
    schema = {
        "sheet_id": "S",
        "cuts": [
            {"id": "c1", "parent_id": "S"},
            {"id": "c2", "parent_id": "S"},
        ],
        "vertices": [],
        "predicates": [],
        "ligatures": [],
    }
    editor.model = editor.model.from_schema(editor.scene, schema)

    _set_cut_rect(editor, "c1", QRectF(50, 50, 150, 120))
    _set_cut_rect(editor, "c2", QRectF(300, 60, 140, 110))

    pm, sheet = _schema_parent_map(editor)
    assert pm["c1"] == sheet
    assert pm["c2"] == sheet


def test_partial_overlap_promotes_to_sheet(qapp):
    editor = DrawingEditor()
    schema = {
        "sheet_id": "S",
        "cuts": [
            {"id": "outer", "parent_id": "S"},
            {"id": "child", "parent_id": "S"},
        ],
        "vertices": [],
        "predicates": [],
        "ligatures": [],
    }
    editor.model = editor.model.from_schema(editor.scene, schema)

    # Place child fully inside initially -> parent should be outer
    _set_cut_rect(editor, "outer", QRectF(100, 100, 300, 220))
    _set_cut_rect(editor, "child", QRectF(160, 160, 80, 60))
    pm, sheet = _schema_parent_map(editor)
    assert pm["child"] == "outer"

    # Now make child partially overlap (not fully contained) -> promote to sheet
    _set_cut_rect(editor, "child", QRectF(50, 150, 140, 80))  # sticks out of outer's left
    editor.end_interaction()  # trigger any deferred preview/refresh hooks
    pm2, _ = _schema_parent_map(editor)
    assert pm2["child"] == sheet
