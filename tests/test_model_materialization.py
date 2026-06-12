"""
Contract tests for model materialization (``src/model_materialization.py``).

Design-of-record: ``docs/DOMAIN_ORACLE_AND_M.md`` §6.1.

Author M as *facts + Horn rules*; materialize forward-chains the Horn fragment to the
least Herbrand model (a facts-only EGI the peel can model-check), and reports the
non-Horn rules it had to leave to the contest game. These pin: the syllogism now
works, recursion reaches a fixpoint, and each non-Horn shape is skipped with the
right reason.
"""

from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif

from domain_oracle import CorpusOracle
from model_materialization import materialize_egi
from semantic_game import Verdict3, evaluate


def _facts(egi):
    """The materialized model's atoms as a set of (relation, sorted-args) for
    comparison independent of individual naming where constants are involved."""
    out = set()
    vmap = {v.id: v for v in egi.V}
    for e in egi.E:
        args = tuple(vmap[v].label for v in egi.nu[e.id])
        out.add((egi.get_relation_name(e.id),) + args)
    return out


# ---------------------------------------------------------------------------
# Horn forward-chaining
# ---------------------------------------------------------------------------

def test_syllogism_materializes():
    M = parse_egif('(man "Socrates") ~[ (man *x) ~[ (mortal x) ] ]')
    facts, rep = materialize_egi(M)
    assert ("mortal", "Socrates") in _facts(facts)
    assert rep.rules_applied == 1
    assert rep.derived_facts == 1
    assert rep.skipped == []


def test_materialized_model_lets_the_peel_derive():
    M = parse_egif('(man "Socrates") ~[ (man *x) ~[ (mortal x) ] ]')
    facts, _ = materialize_egi(M)
    oracle = CorpusOracle([("M", facts)], closed=True)
    assert evaluate(parse_egif('(mortal "Socrates")'), oracle).verdict is Verdict3.TRUE


def test_chained_rules_reach_fixpoint():
    # man → mortal, mortal → perishable.  Both fire over Socrates.
    M = parse_egif('(man "Socrates") '
                   '~[ (man *x) ~[ (mortal x) ] ] '
                   '~[ (mortal *y) ~[ (perishable y) ] ]')
    facts, rep = materialize_egi(M)
    f = _facts(facts)
    assert ("mortal", "Socrates") in f and ("perishable", "Socrates") in f
    assert rep.rules_applied == 2


def test_recursive_transitive_closure():
    # reach(u,v) :- edge(u,v) ;  reach(u,z) :- reach(u,w), edge(w,z).
    M = parse_egif('(edge "a" "b") (edge "b" "c") '
                   '~[ (edge *u *v) ~[ (reach u v) ] ] '
                   '~[ (reach *u *w) (edge w *z) ~[ (reach u z) ] ]')
    facts, _ = materialize_egi(M)
    f = _facts(facts)
    assert ("reach", "a", "b") in f
    assert ("reach", "b", "c") in f
    assert ("reach", "a", "c") in f   # the transitive step


def test_binary_rule_join():
    # parent(x,y) ∧ parent(y,z) → grandparent(x,z)
    M = parse_egif('(parent "Ann" "Bob") (parent "Bob" "Cy") '
                   '~[ (parent *x *y) (parent y *z) ~[ (grandparent x z) ] ]')
    facts, _ = materialize_egi(M)
    assert ("grandparent", "Ann", "Cy") in _facts(facts)


# ---------------------------------------------------------------------------
# Non-Horn shapes are skipped, with the right reason
# ---------------------------------------------------------------------------

def test_existential_head_skipped():
    M = parse_egif('(person "Bob") ~[ (person *x) ~[ (hasParent *y) ] ]')
    _, rep = materialize_egi(M)
    assert rep.rules_applied == 0
    assert [s.reason for s in rep.skipped] == ["existential_head"]


def test_negation_in_head_skipped():
    # ~[ (bird *x) ~[ ~[ (flies x) ] ] ] — a cut inside the head.
    M = parse_egif('(bird "Tweety") ~[ (bird *x) ~[ ~[ (flies x) ] ] ]')
    _, rep = materialize_egi(M)
    assert any(s.reason == "negation_in_head" for s in rep.skipped)
    assert rep.rules_applied == 0


def test_bare_denial_skipped_not_chained():
    # ~[ (mortal "Zeus") ] is a denial (negative fact), not a forward rule.
    M = parse_egif('(god "Zeus") ~[ (mortal "Zeus") ]')
    facts, rep = materialize_egi(M)
    assert any(s.reason == "denial" for s in rep.skipped)
    assert ("mortal", "Zeus") not in _facts(facts)


# ---------------------------------------------------------------------------
# Degenerate / no-op cases
# ---------------------------------------------------------------------------

def test_facts_only_unchanged():
    M = parse_egif('(dog "Biscuit") (mammal "Biscuit")')
    facts, rep = materialize_egi(M)
    assert _facts(facts) == {("dog", "Biscuit"), ("mammal", "Biscuit")}
    assert rep.rules_applied == 0 and rep.derived_facts == 0


def test_no_premise_so_nothing_derived():
    # The rule is present but its antecedent never holds → no derivation.
    M = parse_egif('(cat "Felix") ~[ (man *x) ~[ (mortal x) ] ]')
    facts, rep = materialize_egi(M)
    assert ("mortal",) not in {(f[0],) for f in _facts(facts)}
    assert rep.derived_facts == 0
    assert rep.rules_applied == 1


def test_report_summary_reads():
    M = parse_egif('(man "Socrates") ~[ (man *x) ~[ (mortal x) ] ]')
    _, rep = materialize_egi(M)
    assert "derived" in rep.summary
