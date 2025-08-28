import json
from src.egdf_parser import EGDFDocument


def minimal_egi():
    return {
        "sheet": "S",
        "V": ["v1"],
        "E": ["e1"],
        "Cut": ["c1"],
        "nu": {"e1": ["v1"]},
        "rel": {"e1": "P"},
        "area": {"S": ["c1"], "c1": ["v1", "e1"]},
        "rho": {"v1": None},
        "alphabet": {"C": [], "F": [], "R": ["P"], "ar": {"P": 1}},
    }


def test_hash_is_computed_and_validated():
    inline = minimal_egi()
    header = {"version": "0.1", "generator": "test", "created": ""}
    doc = EGDFDocument(
        header=header,
        egi_ref={"inline": inline},
        layout={"units": "pt"},
        styles={},
        deltas=[],
    )
    # to_dict triggers validate and hash computation
    d = doc.to_dict()
    assert d["egi_ref"]["hash"].startswith("sha256:")

    # Tweak content and ensure validation fails if hash provided mismatches
    bad = d
    bad["egi_ref"]["inline"]["rel"]["e1"] = "Q"
    try:
        EGDFDocument.from_dict(bad)
        assert False, "Expected ValueError due to mismatched hash"
    except ValueError as e:
        assert "does not match" in str(e)


def test_json_yaml_roundtrip():
    inline = minimal_egi()
    header = {"version": "0.1", "generator": "test", "created": ""}
    doc = EGDFDocument(header=header, egi_ref={"inline": inline})

    j = doc.to_json()
    doc2 = EGDFDocument.from_json(j)
    assert doc2.egi_ref["hash"] == doc.egi_ref["hash"]

    y = doc.to_yaml()
    doc3 = EGDFDocument.from_yaml(y)
    assert doc3.egi_ref["hash"] == doc.egi_ref["hash"]


def test_unknown_delta_op_tolerated():
    inline = minimal_egi()
    header = {"version": "0.1", "generator": "test", "created": ""}
    deltas = [
        {"op": "translate", "id": "e1", "dx": 1, "dy": -2, "by": "tester", "at": "2025-08-27T00:00:00Z"},
        {"op": "warp_space", "mystery": 42},  # unknown op should be tolerated by parser
    ]
    doc = EGDFDocument(header=header, egi_ref={"inline": inline}, deltas=deltas)
    d = doc.to_dict()
    assert len(d["deltas"]) == 2
    # Ensure we can load it back without errors
    reloaded = EGDFDocument.from_dict(d)
    assert len(reloaded.deltas) == 2


def test_deterministic_serialization_roundtrip():
    inline = minimal_egi()
    header = {"version": "0.1", "generator": "test", "created": ""}
    doc = EGDFDocument(header=header, egi_ref={"inline": inline}, layout={"units": "pt"})
    d1 = doc.to_dict()
    j1 = json.dumps(d1, sort_keys=True)
    doc2 = EGDFDocument.from_dict(d1)
    d2 = doc2.to_dict()
    j2 = json.dumps(d2, sort_keys=True)
    assert j1 == j2
