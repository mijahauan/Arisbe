import os
import sys
import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QRectF

# Paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(REPO_ROOT, "src")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
for p in (SRC_DIR, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from drawing_editor import DrawingEditor, DrawingModel  # noqa: E402


def ensure_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(scope="function")
def editor():
    ensure_app()
    ed = DrawingEditor()
    return ed


def build_nested_scene(ed: DrawingEditor):
    schema = {
        "sheet_id": "S",
        "cuts": [
            {"id": "Outer", "parent_id": "S"},
            {"id": "Inner", "parent_id": "Outer"},
        ],
        "vertices": [
            {"id": "v1", "area_id": "Outer"},
        ],
        "predicates": [
            {"id": "e1", "name": "P", "area_id": "Outer"},
        ],
        "ligatures": [],
    }
    ed.scene.clear()
    ed.model = DrawingModel.from_schema(ed.scene, schema)
    ed._inject_editor_backrefs_for_model()
    # Place cuts at deterministic rects (Inner strictly inside Outer)
    outer = ed.model.cuts["Outer"].gfx
    inner = ed.model.cuts["Inner"].gfx
    outer.setRect(QRectF(10, 10, 400, 300))
    inner.setRect(QRectF(50, 50, 100, 80))
    return ed.model


def test_vertex_area_reassign_unlocked(editor: DrawingEditor):
    model = build_nested_scene(editor)
    v = model.vertices["v1"].gfx
    # Start outside Inner but inside Outer
    v.setPos(QPointF(20, 20))
    editor.egi_locked = False
    editor.end_interaction()  # should not change yet
    assert model.vertices["v1"].area_id == "Outer"
    # Move into Inner and end interaction -> reassigned to Inner
    v.setPos(QPointF(60, 60))
    editor.egi_locked = False
    editor.end_interaction()
    assert model.vertices["v1"].area_id == "Inner"


def test_vertex_area_not_reassigned_locked(editor: DrawingEditor):
    model = build_nested_scene(editor)
    v = model.vertices["v1"].gfx
    v.setPos(QPointF(60, 60))  # inside Inner
    editor.egi_locked = True
    editor.end_interaction()
    # Should remain Outer in locked mode
    assert model.vertices["v1"].area_id == "Outer"


def test_predicate_area_reassign_unlocked(editor: DrawingEditor):
    model = build_nested_scene(editor)
    p_rect = model.predicates["e1"].gfx_rect
    # Start outside Inner center but inside Outer
    p_rect.setPos(QPointF(20, 20))
    editor.egi_locked = False
    editor.end_interaction()
    assert model.predicates["e1"].area_id == "Outer"
    # Move so its center lands in Inner
    p_rect.setPos(QPointF(60, 60))
    editor.egi_locked = False
    editor.end_interaction()
    assert model.predicates["e1"].area_id == "Inner"


def test_predicate_area_not_reassigned_locked(editor: DrawingEditor):
    model = build_nested_scene(editor)
    p_rect = model.predicates["e1"].gfx_rect
    p_rect.setPos(QPointF(60, 60))  # center in Inner
    editor.egi_locked = True
    editor.end_interaction()
    assert model.predicates["e1"].area_id == "Outer"
