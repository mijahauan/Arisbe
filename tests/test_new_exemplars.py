"""
Tests for the 2026-06-29 corpus exemplar batch (docs/EXEMPLARS.md):

  * four propositional (Alpha) proof chains — tools/build_propositional_exemplars.py
  * two domain-model boards — tools/build_domain_model_exemplars.py
  * the curated Agon innings wiring them into the model picker — src/agon_models.py

The proofs are checked by *building them fresh* (every step a real, attestable
Dau-rule application that must land on the stated conclusion) and by confirming the
four together exercise all six rules. The domain models are checked by materializing
and peeling their sample proposals to the verdicts the exemplars advertise.
"""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tools"))

import eg_navigation as nav  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402
from domain_oracle import CorpusOracle  # noqa: E402
from model_materialization import materialize_egi  # noqa: E402
from semantic_game import evaluate  # noqa: E402

import build_propositional_exemplars as proofs  # noqa: E402
import build_domain_model_exemplars as models  # noqa: E402
from agon_models import list_example_models  # noqa: E402


# --------------------------------------------------------------------------- #
# Proof exemplars                                                             #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("build, conclusion, _prov, _anns", proofs.EXEMPLARS,
                         ids=[b.__name__ for b, *_ in proofs.EXEMPLARS])
def test_proof_builds_to_its_conclusion(build, conclusion, _prov, _anns):
    """Each authored chain is a genuine sequence of sound rule applications that
    reaches exactly the advertised conclusion (no step silently rejected)."""
    chain, uod = build()
    assert chain.steps, "a proof must have at least one step"
    assert nav.same_graph(uod.current_egi, parse_egif(conclusion))


def test_proof_set_exercises_all_six_rules():
    """The quartet is a tour of the calculus: union of rules == the six Dau rules."""
    used = set()
    for build, *_ in proofs.EXEMPLARS:
        chain, _ = build()
        used.update(s.rule_name for s in chain.steps)
    assert used == {"ERA", "INS", "IT+", "IT-", "DC+", "DC-"}


def test_proof_provenance_is_authored_low_warrant():
    """Authored derivations of cited theorems, admitted at low warrant (never
    asserted true) — the manifest floor for the corpus."""
    for _build, _concl, prov_fn, _anns in proofs.EXEMPLARS:
        prov = prov_fn()
        assert prov["kind"] == "proof"
        assert prov["proof_source"]["kind"] == "authored"
        assert prov["warrant"]["derivation"] == "low"


# --------------------------------------------------------------------------- #
# Domain-model exemplars                                                      #
# --------------------------------------------------------------------------- #

def _peel(model_egif: str, proposal_egif: str, *, closed: bool):
    facts, _report = materialize_egi(parse_egif(model_egif))
    oracle = CorpusOracle([("M", facts)], closed=closed)
    return evaluate(parse_egif(proposal_egif), oracle, closed=closed)


def test_zoo_world_materializes_the_taxonomy():
    """The six Horn rules forward-chain: dog/cat/whale→mammal→warm-blooded and
    sparrow→bird→warm-blooded add the derived kinds/traits."""
    _facts, report = materialize_egi(parse_egif(models.ZOO_EGIF))
    assert report.rules_applied >= 1
    assert report.derived_facts > 0


def test_zoo_world_holds_via_chain():
    """'Every dog is warm-blooded' is decided through the materialized chain."""
    r = _peel(models.ZOO_EGIF, "~[ (dog *x) ~[ (warmblooded x) ] ]", closed=True)
    assert r.verdict.value == "true"


def test_zoo_world_refutes_overbroad_universal_naming_pip():
    """'Every warm-blooded thing is a mammal' fails, and the peel names Pip."""
    r = _peel(models.ZOO_EGIF, "~[ (warmblooded *x) ~[ (mammal x) ] ]", closed=True)
    assert r.verdict.value == "false"
    assert r.counterexample and "Pip" in r.counterexample.values()


def test_harbor_town_is_open_independent():
    """An unrecorded claim is UNKNOWN (a candidate new fact), not FALSE."""
    r = _peel(models.HARBOR_EGIF, '(harbor "Bayside") (hosts_market "Bayside")', closed=False)
    assert r.verdict.value == "unknown"


def test_harbor_town_confirms_a_present_fact():
    r = _peel(models.HARBOR_EGIF, '(ferry "Bayside" "Greyrock")', closed=False)
    assert r.verdict.value == "true"


def test_domain_models_are_domain_model_kind():
    for build in models.BUILDERS:
        _uod, prov, _anns = build()
        assert prov["kind"] == "domain_model"


# --------------------------------------------------------------------------- #
# Agon picker wiring — the curated innings                                    #
# --------------------------------------------------------------------------- #

_NEW_INNINGS = {
    "zoo-chain": "true",
    "zoo-refuted": "false",
    "harbor-open": "unknown",
}


def test_new_innings_present_in_picker():
    ids = {e.id for e in list_example_models()}
    assert _NEW_INNINGS.keys() <= ids


@pytest.mark.parametrize("inning_id, expected", _NEW_INNINGS.items())
def test_inning_sample_proposal_peels_as_advertised(inning_id, expected):
    """Each curated inning's sample proposal, peeled against its own model, gives
    exactly the verdict its note promises — the picker never lies about an outcome."""
    e = next(m for m in list_example_models() if m.id == inning_id)
    r = _peel(e.model_egif, e.sample_proposal, closed=e.closed)
    assert r.verdict.value == expected
