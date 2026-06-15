"""
Corpus-conformance tests — the whole curated tomos is *up to spec*.

After the retrofit (``tools/retrofit_corpus.py``), every UoD in the corpus carries
a typed provenance bundle (``src/provenance.py``) with an import ``kind`` and an
annotation layer (``src/annotations.py``).  These tests pin that invariant over
the *real* corpus, so a future addition that forgets its outside-record fails
here.  Provenance/annotations are **outside §3.3** (they describe the source); the
attestation invariant itself is covered by ``test_tomos_attestation.py``.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from annotations import annotations_from_list
from provenance import KIND_PROOF, Provenance
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


def _uod_ids():
    return [u["uod_id"] for u in TomosService(TOMOS_ROOT).list_uods()]


# UoDs whose content is transcribed/cited from a fixed published source.
CITED = {
    "peirce_cp_4_394_man_mortal", "roberts_1973_p57_disjunction",
    "sowa_2011_p356_quantification", "sowa_cat_on_mat", "dau_2006_p112_ligature",
    "theorem_praeclarum",
    # imported ontologies (kind=ontology) — each cites its source vocabulary
    "porphyry_tree", "foaf_core", "sumo_upper", "bfo_core", "colore_between",
    "colore_field", "skos_core",
}
# Imported ontologies (kind=ontology).
ONTOLOGIES = {"porphyry_tree", "foaf_core", "sumo_upper", "bfo_core",
              "colore_between", "colore_field", "skos_core"}
# The worked-proof fixtures (each carries a real chain).
PROOFS = {"peirce_law", "barbara", "group_identity", "theorem_praeclarum",
          "branching_confluence"}


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_every_uod_has_a_valid_provenance_bundle_with_a_kind(uod_id, tomos):
    raw = tomos.load_provenance(uod_id)
    assert raw is not None, f"{uod_id} has no provenance bundle"
    prov = Provenance.from_dict(raw)
    prov.validate()
    assert prov.kind is not None, f"{uod_id} provenance has no import kind"


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_every_uod_has_an_annotation_layer(uod_id, tomos):
    raw = tomos.load_annotations(uod_id)
    assert raw, f"{uod_id} has no annotations"
    layer = annotations_from_list(raw)
    assert layer and all(a.text for a in layer)


@pytest.mark.parametrize("uod_id", sorted(CITED))
def test_cited_uods_carry_a_theorem_source(uod_id, tomos):
    prov = Provenance.from_dict(tomos.load_provenance(uod_id))
    assert prov.theorem_source, f"{uod_id} is cited but has no theorem_source"


@pytest.mark.parametrize("uod_id", sorted(PROOFS))
def test_proof_uods_are_kind_proof(uod_id, tomos):
    prov = Provenance.from_dict(tomos.load_provenance(uod_id))
    assert prov.kind == KIND_PROOF


def test_praeclarum_is_the_transcribed_proof(tomos):
    prov = Provenance.from_dict(tomos.load_provenance("theorem_praeclarum"))
    assert not prov.is_authored_here()   # transcribed, not authored-here
    assert prov.proof_source.get("kind") == "transcribed"
    assert "Leibniz" in prov.formatted()["theorem"]


def test_practice_session_was_retired(tomos):
    assert "practice_43480df3" not in _uod_ids()


@pytest.mark.parametrize("uod_id", sorted(ONTOLOGIES))
def test_imported_ontologies_are_kind_ontology(uod_id, tomos):
    assert uod_id in _uod_ids(), f"{uod_id} not in corpus"
    prov = Provenance.from_dict(tomos.load_provenance(uod_id))
    assert prov.kind == "ontology"
    assert prov.theorem_source, f"{uod_id} ontology cites no source vocabulary"


def test_synthetic_uods_are_authored_not_falsely_cited(tomos):
    """Honesty floor: a synthetic exemplar must NOT carry a fabricated source."""
    synthetic = set(_uod_ids()) - CITED - {"peirce_law", "barbara", "group_identity"}
    for uid in synthetic:
        prov = Provenance.from_dict(tomos.load_provenance(uid))
        assert not prov.theorem_source, (
            f"{uid} is synthetic but carries a theorem_source — a fabricated citation"
        )
