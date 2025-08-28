import os
import sys
import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QRectF

# Ensure repo src/ is importable similarly to drawing_editor.py
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

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
    # Do not show window in tests
    return ed


def build_simple_scene(ed: DrawingEditor):
    """One cut C1, one vertex v1 in C1, one predicate e1 in C1."""
    schema = {
        "sheet_id": "S",
        "cuts": [{"id": "C1", "parent_id": "S"}],
        "vertices": [{"id": "v1", "area_id": "C1"}],
        "predicates": [{"id": "e1", "name": "P", "area_id": "C1"}],
        "ligatures": [],
    }
    ed.scene.clear()
    ed.model = DrawingModel.from_schema(ed.scene, schema)
    # Inject backrefs so gfx event handlers have editor
    ed._inject_editor_backrefs_for_model()
    return ed.model


def test_vertex_out_of_area_unlocked_vs_locked(editor: DrawingEditor):
    model = build_simple_scene(editor)
    # Move vertex outside its cut area
    v = model.vertices["v1"].gfx
    v.setPos(QPointF(0, 0))  # default cut is around (50,50)+(240x160), so (0,0) is outside

    # Unlocked: should be informational only
    editor.egi_locked = False
    ok, msg = editor._validate_syntactic_constraints()
    assert ok is True
    assert isinstance(msg, str)

    # Locked: should fail
    editor.egi_locked = True
    ok2, msg2 = editor._validate_syntactic_constraints()
    assert ok2 is False
    assert "Vertex v1 outside area C1" in msg2


def test_predicate_out_of_area_unlocked_vs_locked(editor: DrawingEditor):
    model = build_simple_scene(editor)
    # Move predicate outside its cut area by repositioning its rect item
    p_rect = model.predicates["e1"].gfx_rect
    p_rect.setPos(QPointF(0, 0))

    # Unlocked: informational
    editor.egi_locked = False
    ok, msg = editor._validate_syntactic_constraints()
    assert ok is True

    # Locked: failure
    editor.egi_locked = True
    ok2, msg2 = editor._validate_syntactic_constraints()
    assert ok2 is False
    assert "Predicate e1 outside area C1" in msg2


def test_cut_overlap_rule_enforced(editor: DrawingEditor):
    # Two overlapping cuts that neither contains the other -> invalid
    schema = {
        "sheet_id": "S",
        "cuts": [
            {"id": "A", "parent_id": "S"},
            {"id": "B", "parent_id": "S"},
        ],
        "vertices": [],
        "predicates": [],
        "ligatures": [],
    }
    editor.scene.clear()
    editor.model = DrawingModel.from_schema(editor.scene, schema)
    editor._inject_editor_backrefs_for_model()

    # Adjust rects to partially overlap without containment
    a = editor.model.cuts["A"].gfx
    b = editor.model.cuts["B"].gfx
    a.setRect(QRectF(50, 50, 120, 120))
    b.setRect(QRectF(120, 120, 120, 120))  # overlaps with A but neither contains the other

    editor.egi_locked = False  # should not matter
    ok, msg = editor._validate_syntactic_constraints()
    assert ok is False
    assert "Cuts overlap improperly" in msg
