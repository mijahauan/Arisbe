"""
Tests for the seeded import-walkthrough fixtures (``tools/build_*_chain.py``):
Peirce's Law (Alpha), and — as they land — Barbara and group-identity (Beta).

Each fixture is a *real* ``TransformationChain`` (every step a sound Dau-rule
application), carrying a typed provenance bundle and an annotation layer at the
scopes the walkthrough mapped (``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §4).  These
tests pin: the derivation reaches the stated conclusion; the provenance is a
valid authored-here bundle; the annotations cover the expected scopes; and the
whole payload round-trips through ``save_uod_with_chain`` + ``save_annotations``
against an isolated corpus (the conclusion's §3.3 attests at the save boundary).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import eg_navigation as nav
from annotations import (
    SCOPE_CHAIN,
    SCOPE_STEP,
    SCOPE_UOD,
    annotations_from_list,
    for_scope,
    for_step,
)
from egif_parser_dau import parse_egif
from provenance import Provenance
from tomos_service import TomosService

from tools.build_peirce_law_chain import (
    TARGET_EGIF as PEIRCE_TARGET,
    build_peirce_law_chain,
    peirce_law_annotations,
    peirce_law_provenance,
)
from tools.build_barbara_chain import (
    CONCLUSION_EGIF as BARBARA_CONCLUSION,
    barbara_annotations,
    barbara_provenance,
    build_barbara_chain,
)


@pytest.fixture
def tomos(tmp_path):
    return TomosService(tmp_path / "tomos")


# --------------------------------------------------------------------------- #
# Peirce's Law (Alpha)                                                        #
# --------------------------------------------------------------------------- #


def test_peirce_law_reaches_conclusion():
    chain, uod = build_peirce_law_chain()
    assert [s.rule_name for s in chain.steps] == [
        "DC+", "INS", "INS", "IT+", "DC+", "IT+"
    ]
    # Pure Alpha → order-insensitive area signature is the authority.
    assert nav.area_signature(uod.current_egi) == nav.area_signature(
        parse_egif(PEIRCE_TARGET)
    )


def test_peirce_law_provenance_is_authored_here():
    prov = Provenance.from_dict(peirce_law_provenance())
    prov.validate()
    assert prov.is_authored_here() is True
    assert "Peirce" in prov.formatted()["theorem"]
    assert prov.warrant == {"theorem": "low", "derivation": "low"}


def test_peirce_law_annotations_cover_scopes():
    layer = annotations_from_list(peirce_law_annotations())
    assert len(for_scope(layer, SCOPE_UOD)) == 1
    assert len(for_scope(layer, SCOPE_CHAIN)) == 1
    # The crux is the two freely-inserted double cuts: steps 1 and 5.
    assert [a.step_id for a in for_scope(layer, SCOPE_STEP)] == ["step-1", "step-5"]
    assert for_step(layer, "step-1")[0].tags == ["crux"]


def test_peirce_law_full_payload_round_trips(tomos):
    chain, uod = build_peirce_law_chain()
    tomos.save_uod_with_chain(uod, chain, provenance=peirce_law_provenance())
    tomos.save_annotations(uod, peirce_law_annotations())

    assert tomos.load_chain(uod.uod_id) is not None
    prov = Provenance.from_dict(tomos.load_provenance(uod.uod_id))
    assert prov.is_authored_here()
    layer = annotations_from_list(tomos.load_annotations(uod.uod_id))
    assert {a.scope for a in layer} == {SCOPE_UOD, SCOPE_CHAIN, SCOPE_STEP}


# --------------------------------------------------------------------------- #
# Barbara (Beta, from premises) — exercises the derived iterate-and-join       #
# --------------------------------------------------------------------------- #


def test_barbara_reaches_conclusion():
    chain, uod = build_barbara_chain()
    # Derived UI move first, then ordinary primitives.
    assert [s.rule_name for s in chain.steps] == ["UI", "IT-", "DC-", "ERA"]
    # Beta → full isomorphism is the authority (A1 stays asserted + every-S-is-P).
    assert nav.same_graph(uod.current_egi, parse_egif(BARBARA_CONCLUSION))


def test_barbara_ui_step_is_marked_derived():
    chain, _ = build_barbara_chain()
    ui = chain.steps[0]
    assert ui.rule_name == "UI"
    assert ui.parameters.get("derived") is True


def test_barbara_provenance_and_annotations():
    prov = Provenance.from_dict(barbara_provenance())
    prov.validate()
    assert prov.is_authored_here()
    assert "Aristotle" in prov.formatted()["theorem"]

    layer = annotations_from_list(barbara_annotations())
    # The Beta crux is the step-1 iterate-and-join.
    step1 = for_step(layer, "step-1")
    assert step1 and "beta-crux" in step1[0].tags


def test_barbara_full_payload_round_trips(tomos):
    chain, uod = build_barbara_chain()
    tomos.save_uod_with_chain(uod, chain, provenance=barbara_provenance())
    tomos.save_annotations(uod, barbara_annotations())
    assert tomos.load_chain(uod.uod_id) is not None
    assert Provenance.from_dict(tomos.load_provenance(uod.uod_id)).is_authored_here()
