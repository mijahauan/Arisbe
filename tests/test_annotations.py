"""
Tests for the annotation layer (``src/annotations.py`` + its persistence and
read-path surfacing).

The layer is marginalia *about* a UoD / chain / step / element — a side store
that rides alongside the graph, **never baked into** the EGI, the ``ChainStep``,
or ``UoDMetadata``, and **outside §3.3** (a comment is not a sign in the graph).
See ``docs/archived/ORGANON_IMPORT_WALKTHROUGH.md`` §3.  These tests pin:

1. **Model** — four scopes; per-scope target validation; deterministic ids;
   to_dict/from_dict round-trip; the scope/target query helpers.
2. **Persistence** — ``save_annotations`` / ``load_annotations`` round-trip
   (mirroring the ``bibliography.json`` side-file); an empty list clears a stale
   file; an unknown UoD loads ``[]``.
3. **Read-path surfacing** — the Organon detail route exposes the raw layer;
   the chain route routes step-scoped notes onto the right frame and surfaces
   chain-/uod-scoped notes at the top, alongside (not replacing) the baked-in
   ``user_annotation``.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from annotations import (
    Annotation,
    SCOPE_CHAIN,
    SCOPE_ELEMENT,
    SCOPE_STEP,
    SCOPE_UOD,
    annotations_from_list,
    annotations_to_list,
    for_element,
    for_scope,
    for_state,
    for_step,
    make_annotation,
)
from egif_parser_dau import parse_egif
from tomos_service import TomosService
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)
from web_api import main as web_main
from web_api.routes import organon


# --------------------------------------------------------------------------- #
# 1. Model                                                                    #
# --------------------------------------------------------------------------- #


def test_scope_target_validation():
    """step needs step_id; element needs state_id + element_id; bad scope/empty
    text are rejected."""
    # Happy paths.
    make_annotation(SCOPE_UOD, "about the universe")
    make_annotation(SCOPE_CHAIN, "about the whole derivation")
    make_annotation(SCOPE_STEP, "about step 1", step_id="step-1")
    make_annotation(SCOPE_ELEMENT, "this cut is the crux",
                    state_id="s0", element_id="c_1")

    with pytest.raises(ValueError):
        make_annotation(SCOPE_STEP, "no step id")              # missing step_id
    with pytest.raises(ValueError):
        make_annotation(SCOPE_ELEMENT, "no anchor", state_id="s0")  # missing element_id
    with pytest.raises(ValueError):
        make_annotation("nonsense", "bad scope")
    with pytest.raises(ValueError):
        make_annotation(SCOPE_UOD, "   ")                      # empty text


def test_id_is_deterministic_and_scope_sensitive():
    """Same content → same id (idempotent seeding); different target → different id."""
    a = make_annotation(SCOPE_STEP, "note", step_id="step-1")
    b = make_annotation(SCOPE_STEP, "note", step_id="step-1")
    c = make_annotation(SCOPE_STEP, "note", step_id="step-2")
    assert a.id == b.id
    assert a.id != c.id
    assert a.id.startswith("ann_")


def test_dict_round_trip():
    a = make_annotation(
        SCOPE_ELEMENT, "the freely-inserted double cut",
        author="mjh", created="2026-06-08T00:00:00+00:00",
        tags=["crux", "fixture"], state_id="s5", element_id="c_double",
    )
    assert Annotation.from_dict(a.to_dict()) == a


def test_query_helpers():
    layer = [
        make_annotation(SCOPE_UOD, "u"),
        make_annotation(SCOPE_CHAIN, "c"),
        make_annotation(SCOPE_STEP, "s1", step_id="step-1"),
        make_annotation(SCOPE_STEP, "s2", step_id="step-2"),
        make_annotation(SCOPE_ELEMENT, "e-a", state_id="s0", element_id="v_a"),
        make_annotation(SCOPE_ELEMENT, "e-b", state_id="s0", element_id="v_b"),
        make_annotation(SCOPE_ELEMENT, "e-c", state_id="s1", element_id="v_a"),
    ]
    assert [a.text for a in for_scope(layer, SCOPE_UOD)] == ["u"]
    assert [a.text for a in for_step(layer, "step-1")] == ["s1"]
    assert [a.text for a in for_element(layer, "s0", "v_a")] == ["e-a"]
    assert {a.text for a in for_state(layer, "s0")} == {"e-a", "e-b"}
    assert {a.text for a in for_state(layer, "s1")} == {"e-c"}


# --------------------------------------------------------------------------- #
# 2. Persistence                                                              #
# --------------------------------------------------------------------------- #


@pytest.fixture
def tomos(tmp_path):
    return TomosService(tmp_path / "tomos")


def _make_uod(uod_id: str) -> UniverseOfDiscourse:
    now = datetime.now(timezone.utc)
    meta = UoDMetadata(
        uod_id=uod_id,
        uod_type=UoDType.HISTORICAL,
        name="Annotation persistence UoD",
        description="Synthesised in test for annotation round-trip.",
        category=UoDCategory.PRACTICE_SESSION,
        created=now,
        last_modified=now,
    )
    return UniverseOfDiscourse(metadata=meta, current_egi=parse_egif("(P *x)"))


def test_persistence_round_trip(tomos):
    uod = _make_uod("ann_rt")
    tomos.save_uod(uod)

    layer = [
        make_annotation(SCOPE_CHAIN, "the whole derivation turns on the double cuts"),
        make_annotation(SCOPE_STEP, "this step is universal instantiation",
                        step_id="step-1", tags=["fixture"]),
    ]
    tomos.save_annotations(uod, annotations_to_list(layer))

    ann_path = tomos._get_uod_path(uod) / "annotations.json"
    assert ann_path.exists()
    assert annotations_from_list(tomos.load_annotations("ann_rt")) == layer


def test_empty_list_clears_stale_file(tomos):
    uod = _make_uod("ann_clear")
    tomos.save_uod(uod)
    tomos.save_annotations(uod, annotations_to_list(
        [make_annotation(SCOPE_UOD, "temporary")]))
    ann_path = tomos._get_uod_path(uod) / "annotations.json"
    assert ann_path.exists()

    tomos.save_annotations(uod, [])
    assert not ann_path.exists()
    assert tomos.load_annotations("ann_clear") == []


def test_unknown_uod_loads_empty(tomos):
    assert tomos.load_annotations("does_not_exist") == []


# --------------------------------------------------------------------------- #
# 3. Read-path surfacing (Organon)                                            #
# --------------------------------------------------------------------------- #


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def chain_uod_id():
    """A real corpus UoD that carries a chain; skip if the corpus lacks one."""
    preferred = "beta_converse_mp"
    ids = [u["uod_id"] for u in TomosService(TOMOS_ROOT).list_uods()]
    if preferred not in ids:
        pytest.skip("corpus has no beta_converse_mp chain UoD")
    return preferred


def test_detail_route_surfaces_raw_layer(client, chain_uod_id, monkeypatch):
    """GET /organon/uods/{id} exposes the annotation layer verbatim."""
    crafted = annotations_to_list([
        make_annotation(SCOPE_UOD, "a note about this universe"),
    ])
    svc = organon._get_tomos()
    monkeypatch.setattr(svc, "load_annotations", lambda uid: crafted)

    body = client.get(f"/organon/uods/{chain_uod_id}").json()
    assert body["success"] is True
    assert body["data"]["annotations"] == crafted


def test_chain_route_routes_scopes_to_frames(client, chain_uod_id, monkeypatch):
    """Step-scoped notes land on the matching frame; chain-/uod-scoped notes
    surface at the top; the baked-in user_annotation is untouched."""
    crafted = annotations_to_list([
        make_annotation(SCOPE_UOD, "universe note"),
        make_annotation(SCOPE_CHAIN, "whole-derivation note"),
        make_annotation(SCOPE_STEP, "external note on step 1", step_id="step-1"),
    ])
    svc = organon._get_tomos()
    monkeypatch.setattr(svc, "load_annotations", lambda uid: crafted)

    body = client.get(f"/organon/uods/{chain_uod_id}/chain").json()
    assert body["success"] is True
    data = body["data"]
    assert data["has_chain"] is True

    # Top-level chain/uod notes.
    assert [a["text"] for a in data["chain_annotations"]] == ["whole-derivation note"]
    assert [a["text"] for a in data["uod_annotations"]] == ["universe note"]

    # The step-1 frame carries the external note in its additive layer, while
    # still exposing the baked-in user_annotation separately.
    step1_frames = [f for f in data["frames"] if f.get("step_id") == "step-1"]
    assert step1_frames, "expected a frame for step-1 in the chain"
    frame = step1_frames[0]
    assert "external note on step 1" in [a["text"] for a in frame["annotations"]]
    assert frame["annotation"] is not None  # baked-in user_annotation preserved

    # A frame without a matching step-scoped note has an empty additive layer.
    other = [f for f in data["frames"] if f.get("step_id") not in ("step-1", None)]
    for f in other:
        assert all(a["scope"] != SCOPE_STEP or a["step_id"] != "step-1"
                   for a in f["annotations"])
