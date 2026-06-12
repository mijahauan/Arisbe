"""
Theory query — is the universal G a *theorem* of the theory M? (freeze a witness)

Covers ``src/theory_query.py``: the deduction step that decides a T-box subsumption /
typing query against an ontology M, where the ordinary peel (model-checking) reads
*vacuously* over an empty or sparse A-box.  See ``docs/DOMAIN_ORACLE_AND_M.md`` §6.2.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from theory_query import entails
from tomos_service import TomosService

TOMOS = Path(__file__).parent.parent / "tomos"


def _q(theory_egif: str, query_egif: str):
    return entails(parse_egif(theory_egif), parse_egif(query_egif))


# --------------------------------------------------------------------------- #
# Applicability — only a range-restricted Horn universal is a theory query     #
# --------------------------------------------------------------------------- #


def test_universal_horn_is_applicable():
    r = _q('~[ (A *x) ~[ (B x) ] ]', '~[ (A *x) ~[ (B x) ] ]')
    assert r.applicable


@pytest.mark.parametrize("query", [
    '(A "a")',                          # a ground fact, no scroll
    '~[ (A *x) ]',                      # a bare denial (no head)
    '~[ (A *x) ~[ ~[ (B x) ] ] ]',     # negation in the head
    '~[ (A *x) ~[ (B *y) ] ]',         # fresh existential in the head (not range-restricted)
    '(A *x) ~[ (A *y) ~[ (B y) ] ]',   # extra sheet-level atom beside the scroll
])
def test_non_horn_universal_is_not_applicable(query):
    r = _q('~[ (A *x) ~[ (B x) ] ]', query)
    assert not r.applicable
    assert r.verdict == "unknown"


# --------------------------------------------------------------------------- #
# The decision — freeze a witness, materialize, check the head                 #
# --------------------------------------------------------------------------- #


def test_direct_subsumption_is_a_theorem():
    # M: A ⊑ B.  Query: A ⊑ B.  Trivially a theorem.
    r = _q('~[ (A *x) ~[ (B x) ] ]', '~[ (A *x) ~[ (B x) ] ]')
    assert r.verdict == "true"
    assert r.holds
    assert r.witnesses                       # a fresh witness was minted
    assert r.derived and not r.missing


def test_transitive_subsumption_chains():
    # M: A ⊑ B, B ⊑ C.  Query: A ⊑ C — derivable only by chaining.
    theory = '~[ (A *x) ~[ (B x) ] ] ~[ (B *y) ~[ (C y) ] ]'
    r = _q(theory, '~[ (A *x) ~[ (C x) ] ]')
    assert r.verdict == "true"


def test_underivable_against_wholly_horn_theory_is_false():
    # M: A ⊑ B (wholly Horn).  Query: A ⊑ C — not derivable, and M can say so.
    r = _q('~[ (A *x) ~[ (B x) ] ]', '~[ (A *x) ~[ (C x) ] ]')
    assert r.verdict == "false"
    assert r.missing and not r.derived


def test_underivable_with_non_horn_residue_is_unknown():
    # M carries a non-Horn disjointness ~[ (A x) (D x) ] that materialization skips.
    # A ⊑ C is underivable from the Horn fragment, but the skipped axiom might bear on
    # it → honestly UNKNOWN, not FALSE.
    theory = '~[ (A *x) ~[ (B x) ] ] ~[ (A *z) (D z) ]'
    r = _q(theory, '~[ (A *x) ~[ (C x) ] ]')
    assert r.verdict == "unknown"
    assert r.skipped_in_theory >= 1


def test_multi_variable_body_typing_rule():
    # M: a binary relation's domain typing  R(y,z) → P(y).  Query: the same rule.
    theory = '~[ (R *y *z) ~[ (P y) ] ]'
    r = _q(theory, '~[ (R *y *z) ~[ (P y) ] ]')
    assert r.verdict == "true"
    assert len(r.witnesses) == 2             # both y and z frozen


def test_conjunctive_head_all_atoms_required():
    # M: A ⊑ B, A ⊑ C.  Query head is a conjunction B ∧ C — both must derive.
    theory = '~[ (A *x) ~[ (B x) ] ] ~[ (A *w) ~[ (C w) ] ]'
    assert _q(theory, '~[ (A *x) ~[ (B x) (C x) ] ]').verdict == "true"
    # One head atom underivable → not a theorem (wholly Horn ⇒ FALSE).
    assert _q(theory, '~[ (A *x) ~[ (B x) (E x) ] ]').verdict == "false"


# --------------------------------------------------------------------------- #
# The real corpus ontologies — ontology-as-M made concrete                    #
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS)


def _corpus_q(tomos, uid: str, query: str):
    return entails(tomos.load_uod(uid).current_egi, parse_egif(query))


def test_sumo_upper_subsumption_theorems(tomos):
    # SUMO upper spine is a *pure T-box* — materialization alone derives nothing.
    # Object ⊑ Continuant ⊑ Entity is decided only by freezing a witness.
    assert _corpus_q(tomos, "sumo_upper", '~[ (Object *x) ~[ (Entity x) ] ]').verdict == "true"
    assert _corpus_q(tomos, "sumo_upper", '~[ (Object *x) ~[ (Continuant x) ] ]').verdict == "true"
    # Object is a Continuant, disjoint from the Occurrent branch — not a theorem.
    assert _corpus_q(tomos, "sumo_upper", '~[ (Object *x) ~[ (Occurrent x) ] ]').verdict == "false"
    # A relation nowhere in the ontology — definitely not a theorem.
    assert _corpus_q(tomos, "sumo_upper", '~[ (Object *x) ~[ (Nonsense x) ] ]').verdict == "false"


def test_porphyry_ladder_and_disjointness_residue(tomos):
    # The full Porphyrian ladder: Man ⊑ Animal ⊑ Living ⊑ Body ⊑ Substance.
    assert _corpus_q(tomos, "porphyry_tree", '~[ (Man *x) ~[ (Substance x) ] ]').verdict == "true"
    assert _corpus_q(tomos, "porphyry_tree", '~[ (Beast *x) ~[ (Living x) ] ]').verdict == "true"
    # Man ⊑ Beast is not derivable, but Porphyry's Man/Beast disjointness is a skipped
    # non-Horn axiom → honestly UNKNOWN (the Horn fragment can't settle it).
    man_beast = _corpus_q(tomos, "porphyry_tree", '~[ (Man *x) ~[ (Beast x) ] ]')
    assert man_beast.verdict == "unknown"
    assert man_beast.skipped_in_theory >= 1


def test_foaf_typing_chains_through_subsumption(tomos):
    # FOAF: knows(y,z) types y and z as Person; Person ⊑ Agent.  So knows(y,z) → Agent(y)
    # holds only by chaining the typing rule into the subsumption.
    assert _corpus_q(tomos, "foaf_core", '~[ (knows *y *z) ~[ (Person y) ] ]').verdict == "true"
    assert _corpus_q(tomos, "foaf_core", '~[ (knows *y *z) ~[ (Agent y) ] ]').verdict == "true"
    assert _corpus_q(tomos, "foaf_core", '~[ (Person *x) ~[ (Agent x) ] ]').verdict == "true"
