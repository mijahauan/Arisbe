import sys
import os

# Ensure src/ on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from controller import constraint_engine as ce  # noqa: E402


def simple_dto():
    # One cut C1 at (50,50,240,160)
    return {
        "sheet_id": "S",
        "cuts": {"C1": {"rect": (50.0, 50.0, 240.0, 160.0), "parent_id": "S"}},
        "vertices": {"v1": {"pos": (120.0, 120.0), "area_id": "C1"}},
        "predicates": {"e1": {"rect": (200.0, 120.0, 20.0, 12.0), "area_id": "C1"}},
        "ligatures": {},
    }


def test_vertex_out_of_area_unlocked_vs_locked():
    dto = simple_dto()
    # Move vertex out
    dto["vertices"]["v1"]["pos"] = (0.0, 0.0)

    ok, msg, info = ce.validate_syntax(dto, egi_locked=False)
    assert ok is True
    assert isinstance(msg, str)
    assert "out_of_area" in info

    ok2, msg2, info2 = ce.validate_syntax(dto, egi_locked=True)
    assert ok2 is False
    assert "Vertex v1 outside area C1" in msg2


def test_predicate_out_of_area_unlocked_vs_locked():
    dto = simple_dto()
    # Move predicate out (its rect center will be out of C1)
    dto["predicates"]["e1"]["rect"] = (0.0, 0.0, 20.0, 12.0)

    ok, msg, info = ce.validate_syntax(dto, egi_locked=False)
    assert ok is True

    ok2, msg2, info2 = ce.validate_syntax(dto, egi_locked=True)
    assert ok2 is False
    assert "Predicate e1 outside area C1" in msg2


def test_cut_overlap_rule_enforced():
    dto = {
        "sheet_id": "S",
        "cuts": {
            "A": {"rect": (50.0, 50.0, 120.0, 120.0), "parent_id": "S"},
            "B": {"rect": (120.0, 120.0, 120.0, 120.0), "parent_id": "S"},
        },
        "vertices": {},
        "predicates": {},
        "ligatures": {},
    }
    ok, msg, info = ce.validate_syntax(dto, egi_locked=False)
    assert ok is False
    assert "Cuts overlap improperly" in msg


def test_suggest_area_for_point():
    dto = {
        "sheet_id": "S",
        "cuts": {
            "Outer": {"rect": (10.0, 10.0, 400.0, 300.0), "parent_id": "S"},
            "Inner": {"rect": (50.0, 50.0, 100.0, 80.0), "parent_id": "Outer"},
        },
        "vertices": {},
        "predicates": {},
        "ligatures": {},
    }
    # Point in Inner should choose Inner as deepest
    area = ce.suggest_area_for_point(dto, (60.0, 60.0), sheet_id="S")
    assert area == "Inner"
    # Point in Outer but outside Inner
    area2 = ce.suggest_area_for_point(dto, (380.0, 290.0), sheet_id="S")
    assert area2 == "Outer"
    # Point outside all cuts -> sheet
    area3 = ce.suggest_area_for_point(dto, (0.0, 0.0), sheet_id="S")
    assert area3 == "S"


def test_select_subgraph_expands_cut_subtree():
    dto = {
        "sheet_id": "S",
        "cuts": {
            "Parent": {"rect": (10.0, 10.0, 400.0, 300.0), "parent_id": "S"},
            "Child": {"rect": (50.0, 50.0, 100.0, 80.0), "parent_id": "Parent"},
        },
        "vertices": {"v1": {"pos": (60.0, 60.0), "area_id": "Child"}},
        "predicates": {"e1": {"rect": (70.0, 70.0, 20.0, 12.0), "area_id": "Child"}},
        "ligatures": {},
    }
    sel = {"cuts": ["Parent"], "vertices": [], "predicates": []}
    sub = ce.select_subgraph(dto, sel)
    assert "Parent" in sub["cuts"] and "Child" in sub["cuts"]
    assert "v1" in sub["vertices"] and "e1" in sub["predicates"]


def test_plan_move_ok_for_cut_subtree_locked():
    # Parent (P) contains Child (C) which contains a vertex and a predicate
    dto = {
        "sheet_id": "S",
        "cuts": {
            "P": {"rect": (10.0, 10.0, 300.0, 200.0), "parent_id": "S"},
            "C": {"rect": (50.0, 50.0, 100.0, 80.0), "parent_id": "P"},
        },
        "vertices": {"v1": {"pos": (60.0, 60.0), "area_id": "C"}},
        "predicates": {"e1": {"rect": (70.0, 70.0, 20.0, 12.0), "area_id": "C"}},
        "ligatures": {},
    }
    sub = ce.select_subgraph(dto, {"cuts": ["P"], "vertices": [], "predicates": []})
    status, reason, changes = ce.plan_move(dto, sub, {"dx": 5.0, "dy": 7.0}, locked=True)
    assert status == "ok"
    # Ensure cut, child cut, vertex, predicate all have proposed moved geometry
    assert "P" in changes and "rect" in changes["P"]
    assert "C" in changes and "rect" in changes["C"]
    assert "v1" in changes and "pos" in changes["v1"]
    assert "e1" in changes and "rect" in changes["e1"]


def test_plan_move_reject_when_child_cut_leaves_parent_locked():
    # Moving Child far enough should try to leave Parent and be rejected
    dto = {
        "sheet_id": "S",
        "cuts": {
            "P": {"rect": (10.0, 10.0, 300.0, 200.0), "parent_id": "S"},
            "C": {"rect": (50.0, 50.0, 100.0, 80.0), "parent_id": "P"},
        },
        "vertices": {"v1": {"pos": (60.0, 60.0), "area_id": "C"}},
        "predicates": {},
        "ligatures": {},
    }
    sub = ce.select_subgraph(dto, {"cuts": ["C"], "vertices": [], "predicates": []})
    # Large move to the left/up beyond parent's bounds
    status, reason, changes = ce.plan_move(dto, sub, {"dx": -100.0, "dy": -100.0}, locked=True)
    assert status == "reject"
    assert "leave parent" in reason
