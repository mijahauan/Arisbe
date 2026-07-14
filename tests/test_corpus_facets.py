"""**Corpus facets** — the reader's axis, beside the producer's (`src/corpus_facets.py`).

``UoDCategory`` answers *how was this made?* (static import vs dynamic session — and
the code depends on that gating). It was never a subject taxonomy, and using it as
one turned ``domain_model`` into a junk drawer: seven ontologies, two game boards,
three dialogue episodes, a modal demonstration and the arithmetic ladder, all on the
one shelf that means "…and the rest."

The tests pin the three things that make the facet layer worth having:

* it is **derived, not invented** — from the authored annotation tags + the
  provenance kind;
* it is **multi-valued** — Cohen's forcing conditions are mathematics AND a modality
  demonstration, and forcing one shelf per thing is the same mistake one level down;
* it is **honest** — nothing is silently defaulted (``unfiled`` is a real answer),
  and no shelf is ever consulted by the calculus.

Plus the headline regression: the three modal demonstrations, documented as *one set
of three*, must land on one shelf.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from corpus_facets import (  # noqa: E402
    PURPOSES, SUBJECTS, UNFILED, facets_for, facets_for_corpus,
    group_by_subject, kind_of, tags_of, unfiled,
)

TOMOS = REPO / "tomos"


@pytest.fixture(scope="module")
def entries():
    idx = json.loads((TOMOS / "index.json").read_text())
    return idx.get("universes") or idx.get("entries") or []


@pytest.fixture(scope="module")
def facets(entries):
    return facets_for_corpus(TOMOS, entries)


# --- derived, not invented -------------------------------------------------- #

def test_a_tag_decides_the_shelf_and_says_so():
    f = facets_for("x", tags=["mathematics", "teaching"], category="domain_model")
    assert "mathematics" in f.subjects and "teach" in f.purposes
    assert any(d.startswith("tag:") for d in f.derived_by)   # traceable, not magic


def test_provenance_kind_shelves_the_ontologies():
    f = facets_for("foaf", tags=[], category="domain_model", kind="ontology")
    assert f.subjects == ("ontology",) and "kind:ontology" in f.derived_by


def test_the_producer_axis_is_the_LAST_resort_not_the_first():
    """A proof with no tags is still logic — that is what the category *means*.
    But a tag always wins over it."""
    bare = facets_for("p", tags=[], category="theorem_proof")
    assert bare.subjects == ("logic",) and bare.purposes == ("prove",)
    tagged = facets_for("p", tags=["mathematics"], category="theorem_proof")
    assert tagged.subjects == ("mathematics",)   # the tag, not the category


def test_nothing_is_silently_defaulted():
    """An unshelvable UoD is NAMED. A growing unfiled list says the tag vocabulary
    needs a word — it must never be papered over with a default."""
    f = facets_for("mystery", tags=[], category=None)
    assert f.subjects == () and f.unfiled
    assert unfiled([f]) == ["mystery"]


# --- multi-valued, deliberately --------------------------------------------- #

def test_facets_are_multivalued():
    """Forcing one shelf per thing is the junk-drawer mistake, one level down."""
    f = facets_for("forcing", tags=["mathematics", "modality", "demonstration"])
    assert set(f.subjects) == {"mathematics", "modality"}


def test_forcing_conditions_sits_on_both_its_shelves(facets):
    fc = next(f for f in facets if f.uod_id == "forcing_conditions")
    assert "mathematics" in fc.subjects   # Cohen's conditions ARE mathematics
    assert "modality" in fc.subjects      # …and they demonstrate the modal lens


# --- the headline regression: the trio reunites ----------------------------- #

def test_the_three_modal_demonstrations_land_on_one_shelf(facets):
    """`broken_cut_square`, `would_be_de_inesse`, `would_be_courses` are ONE set of
    three (docs/EXEMPLARS.md §5.1). Under the producer's axis they were filed as
    theorem_proof / literature_example / domain_model — three shelves, unfindable
    together. They must now share one."""
    trio = {"broken_cut_square", "would_be_de_inesse", "would_be_courses"}
    shelved = {f.uod_id: f.subjects for f in facets if f.uod_id in trio}
    assert set(shelved) == trio, "a demonstration went missing from the corpus"
    for uid, subjects in shelved.items():
        assert "modality" in subjects, f"{uid} is not on the modality shelf"


def test_gamma_is_NOT_a_synonym_for_modality():
    """The homonym, refused. Arisbe carries modality WITHOUT Gamma
    (docs/MODALITY_WITHOUT_GAMMA.md), and "Gamma" now names the SECOND-ORDER
    frontier. Peirce's *historical* Gamma attempts at modality are tagged
    `peirce-gamma` so the two words never collide (charter P2: one word, one way)."""
    assert "second-order" in SUBJECTS
    # a bare `gamma` tag must NOT shelve anything as modality
    assert facets_for("g", tags=["gamma"]).subjects == ()
    # and the corpus no longer uses the ambiguous word
    for d in (TOMOS / "universes").iterdir():
        if d.is_dir():
            assert "gamma" not in tags_of(TOMOS, d.name), \
                f"{d.name} still carries the ambiguous 'gamma' tag"


# --- the corpus is fully and honestly shelved -------------------------------- #

def test_the_whole_corpus_is_shelved(facets):
    assert len(facets) >= 40
    assert unfiled(facets) == [], "every UoD must land somewhere, or be named"


def test_the_junk_drawer_is_gone(facets):
    """The ontologies, the boards, the dialogue episodes, the mathematics and the
    modal demonstrations were ALL `domain_model`. They are now six distinct shelves."""
    by_subject = group_by_subject(facets)
    for shelf in ("ontology", "worlds", "dialogue", "mathematics", "modality", "logic"):
        assert by_subject.get(shelf), f"nothing on the {shelf} shelf"
    assert by_subject["ontology"] == sorted(by_subject["ontology"])
    assert "zoo_world" in by_subject["worlds"]
    assert "peirce_order_1881" in by_subject["mathematics"]


def test_every_shelf_key_is_glossed():
    """P3 (recognition, never recall): a shelf must say what it holds."""
    by = group_by_subject
    for key in SUBJECTS:
        assert SUBJECTS[key].strip()
    for key in PURPOSES:
        assert PURPOSES[key].strip()


# --- the route -------------------------------------------------------------- #

def test_shelves_route_serves_the_axes_and_its_own_honesty():
    from fastapi.testclient import TestClient
    from web_api.main import app

    body = TestClient(app).get("/organon/shelves").json()
    assert body["success"]
    data = body["data"]
    subjects = {s["key"]: s["count"] for s in data["subjects"]}
    assert subjects.get("mathematics", 0) >= 3
    assert subjects.get("ontology", 0) >= 7
    assert data["unfiled"] == []
    # the layer says what it is: a convenience, not a fact about the graph
    assert "convenience" in data["note"] and "never consulted" in data["note"]


def test_browse_rows_carry_the_reader_axes():
    from fastapi.testclient import TestClient
    from web_api.main import app

    rows = TestClient(app).get("/organon/uods").json()["data"]
    fc = next(r for r in rows if r["uod_id"] == "forcing_conditions")
    assert "mathematics" in fc["subjects"] and "modality" in fc["subjects"]
    # the producer's axis is untouched — nothing migrated
    assert fc["category"] == "domain_model"
