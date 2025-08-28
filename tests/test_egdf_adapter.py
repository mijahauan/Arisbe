from src.egdf_adapter import drawing_to_egdf_document


def sample_drawing():
    return {
        "sheet_id": "S",
        "cuts": [
            {"id": "c1", "parent_id": "S"},
            {"id": "c2", "parent_id": "c1"},
        ],
        "vertices": [
            {"id": "v1", "area_id": "c2", "label_kind": "constant", "label": "a"},
            {"id": "v2", "area_id": "S"},
        ],
        "predicates": [
            {"id": "e1", "name": "P", "area_id": "c2"},
            {"id": "e2", "name": "R", "area_id": "S"},
        ],
        "ligatures": [
            {"edge_id": "e1", "vertex_ids": ["v1"]},
            {"edge_id": "e2", "vertex_ids": ["v2"]},
        ],
    }


def test_adapter_builds_valid_egdf():
    layout = {
        "units": "pt",
        "cuts": {"c1": {"x": 0, "y": 0, "w": 300, "h": 200}, "c2": {"x": 40, "y": 40, "w": 160, "h": 90}},
        "vertices": {"v1": {"x": 80, "y": 80}, "v2": {"x": 20, "y": 20}},
        "predicates": {"e1": {"text": "P", "x": 100, "y": 60, "w": 20, "h": 12}},
        "ligatures": {"e1": {"area": "c2", "path": {"kind": "spline", "points": [[100,66],[90,74],[80,80]]}}},
    }
    styles = {"imports": ["dau-classic@1.0"], "variables": {}, "rules": []}
    deltas = [{"op": "translate", "id": "e1", "dx": 1, "dy": -1, "by": "test", "at": "2025-08-27T00:00:00Z"}]

    doc = drawing_to_egdf_document(sample_drawing(), layout=layout, styles=styles, deltas=deltas)
    d = doc.to_dict()

    # Hash exists
    assert d["egi_ref"]["hash"].startswith("sha256:")

    # Alphabet contains P and R with arities 1
    alpha = d["egi_ref"]["inline"]["alphabet"]
    assert set(alpha["R"]) == {"P", "R"}
    assert alpha["ar"]["P"] == 1 and alpha["ar"]["R"] == 1

    # rho sets v1 to constant 'a'
    rho = d["egi_ref"]["inline"]["rho"]
    assert rho["v1"] == "a"
    assert rho["v2"] is None

    # Layout/styles/deltas attached
    assert d["layout"]["units"] == "pt"
    assert d["styles"]["imports"] == ["dau-classic@1.0"]
    assert len(d["deltas"]) == 1
