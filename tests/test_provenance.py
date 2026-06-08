"""
Tests for the provenance bundle (``src/provenance.py`` + its persistence and the
``save_uod_with_chain`` doorway-union).

Provenance splits into layers that don't share a source — theorem / EG-derivation
/ calculus — and a derivation is either *transcribed* (a published proof) or
*authored here*; flattening them would misattribute an authored derivation to a
historical source (``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §2.5).  Warrant is a
per-layer record (not a tag, not a protected ``UoDMetadata`` field).  These tests
pin:

1. **Model** — defaults; the authored/transcribed helpers; validation of the
   discriminator, required sub-fields, and warrant levels; ``formatted`` faces;
   ``to_dict``/``from_dict`` round-trip.
2. **Persistence + doorway-union** — ``save_provenance``/``load_provenance``
   round-trip; an empty bundle clears the file; unknown UoD → ``None``;
   ``save_uod_with_chain(provenance=…)`` writes it beside the chain.
3. **Read-path surfacing** — the Organon detail route exposes the bundle.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from provenance import (
    DERIVATION_AUTHORED,
    DERIVATION_TRANSCRIBED,
    WARRANT_LOW,
    Provenance,
    authored_proof,
    make_provenance,
    transcribed_proof,
)
from tomos_service import TomosService, TransformationChain
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)
from web_api import main as web_main
from web_api.routes import organon


_PEIRCE_1885 = {
    "type": "article-journal",
    "author": "Peirce, Charles Sanders",
    "title": "On the Algebra of Logic: A Contribution to the Philosophy of Notation",
    "container_title": "American Journal of Mathematics",
    "volume": "7",
    "year": "1885",
    "pages": "180–202",
    "bibkey": "peirce1885algebra",
}
_DAU_2003 = {
    "type": "book",
    "author": "Dau, Frithjof",
    "title": "The Logic System of Concept Graphs with Negation",
    "year": "2003",
    "bibkey": "dau2003logic",
}


# --------------------------------------------------------------------------- #
# 1. Model                                                                    #
# --------------------------------------------------------------------------- #


def test_defaults_and_authored_bundle():
    prov = make_provenance(
        theorem_source=_PEIRCE_1885,
        proof_source=authored_proof("mjh", system="Peirce–Sowa EGIF"),
        method_sources=[_DAU_2003],
    )
    assert prov.warrant == {"theorem": WARRANT_LOW, "derivation": WARRANT_LOW}
    assert prov.is_authored_here() is True
    faces = prov.formatted()
    assert "Peirce" in faces["theorem"]
    assert "Original derivation by mjh" in faces["proof"]
    assert faces["methods"] and "Dau" in faces["methods"][0]


def test_transcribed_bundle():
    prov = make_provenance(
        theorem_source=_PEIRCE_1885,
        proof_source=transcribed_proof({
            "type": "article-journal", "author": "Sowa, John F.",
            "title": "Peirce's Tutorial on Existential Graphs",
            "container_title": "Semiotica", "year": "2011",
        }),
    )
    assert prov.is_authored_here() is False
    assert "Sowa" in prov.formatted()["proof"]


def test_validation_rejects_malformed():
    with pytest.raises(ValueError):
        make_provenance(proof_source={"kind": "nonsense"})
    with pytest.raises(ValueError):
        make_provenance(proof_source={"kind": DERIVATION_TRANSCRIBED})  # no citation
    with pytest.raises(ValueError):
        make_provenance(proof_source={"kind": DERIVATION_AUTHORED})     # no author
    with pytest.raises(ValueError):
        make_provenance(warrant={"theorem": "stellar"})                 # bad level


def test_dict_round_trip():
    prov = make_provenance(
        theorem_source=_PEIRCE_1885,
        proof_source=authored_proof("mjh"),
        method_sources=[_DAU_2003],
        warrant={"theorem": WARRANT_LOW, "derivation": WARRANT_LOW},
    )
    again = Provenance.from_dict(prov.to_dict())
    assert again.theorem_source == prov.theorem_source
    assert again.proof_source == prov.proof_source
    assert again.method_sources == prov.method_sources
    assert again.warrant == prov.warrant


# --------------------------------------------------------------------------- #
# 2. Persistence + doorway-union                                              #
# --------------------------------------------------------------------------- #


@pytest.fixture
def tomos(tmp_path):
    return TomosService(tmp_path / "tomos")


def _make_uod(uod_id: str) -> UniverseOfDiscourse:
    now = datetime.now(timezone.utc)
    meta = UoDMetadata(
        uod_id=uod_id,
        uod_type=UoDType.HISTORICAL,
        name="Provenance UoD",
        description="Synthesised in test for provenance round-trip.",
        category=UoDCategory.THEOREM_PROOF,
        created=now,
        last_modified=now,
    )
    return UniverseOfDiscourse(metadata=meta, current_egi=parse_egif("(P *x)"))


def test_persistence_round_trip(tomos):
    uod = _make_uod("prov_rt")
    tomos.save_uod(uod)
    bundle = make_provenance(
        theorem_source=_PEIRCE_1885, proof_source=authored_proof("mjh")
    ).to_dict()
    tomos.save_provenance(uod, bundle)

    prov_path = tomos._get_uod_path(uod) / "provenance.json"
    assert prov_path.exists()
    assert tomos.load_provenance("prov_rt") == bundle

    tomos.save_provenance(uod, {})
    assert not prov_path.exists()
    assert tomos.load_provenance("prov_rt") is None


def test_unknown_uod_loads_none(tomos):
    assert tomos.load_provenance("nope") is None


def test_save_uod_with_chain_carries_provenance(tomos):
    """The doorway-union: a worked proof imports as a chain that carries its
    low-warrant attribution."""
    uod = _make_uod("prov_chain")
    egi = uod.current_egi
    chain = TransformationChain(
        initial_state_id="s0", steps=[], states={"s0": egi}
    )
    bundle = make_provenance(
        theorem_source=_PEIRCE_1885,
        proof_source=authored_proof("mjh", system="Peirce–Sowa EGIF"),
        method_sources=[_DAU_2003],
    ).to_dict()

    tomos.save_uod_with_chain(uod, chain, provenance=bundle)

    loaded = tomos.load_provenance("prov_chain")
    assert loaded is not None
    assert loaded["proof_source"]["kind"] == DERIVATION_AUTHORED
    assert loaded["warrant"]["derivation"] == WARRANT_LOW
    # The chain itself still round-trips beside the provenance.
    assert tomos.load_chain("prov_chain") is not None


# --------------------------------------------------------------------------- #
# 3. Read-path surfacing (Organon)                                            #
# --------------------------------------------------------------------------- #


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def sample_uod_id():
    ids = [u["uod_id"] for u in TomosService(TOMOS_ROOT).list_uods()]
    if not ids:
        pytest.skip("tomos corpus is empty")
    return "beta_converse_mp" if "beta_converse_mp" in ids else ids[0]


def test_detail_route_surfaces_provenance(client, sample_uod_id, monkeypatch):
    bundle = make_provenance(
        theorem_source=_PEIRCE_1885, proof_source=authored_proof("mjh")
    ).to_dict()
    svc = organon._get_tomos()
    monkeypatch.setattr(svc, "load_provenance", lambda uid: bundle)

    body = client.get(f"/organon/uods/{sample_uod_id}").json()
    assert body["success"] is True
    assert body["data"]["provenance"] == bundle
