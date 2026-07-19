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


# ---------------------------------------------------------------------------
# IncrementalMaterializer — the F2⁗ semi-naive rider (2026-07-03)
# The contract is EXACTNESS: whatever the cache does internally (hit / delta
# extension / full rebuild), the returned closure always equals materialize_egi's.
# ---------------------------------------------------------------------------

def _mat_equal(inc_result, egi):
    full, _ = materialize_egi(egi)
    return _facts(inc_result) == _facts(full)


def test_incremental_equals_full_across_monotone_growth():
    from model_materialization import IncrementalMaterializer
    mat = IncrementalMaterializer()
    m1 = parse_egif('(man "Socrates") ~[ (man *x) ~[ (mortal x) ] ]')
    out1, rep1 = mat.materialize(m1)
    assert _mat_equal(out1, m1) and rep1.derived_facts == 1
    assert mat.rebuilds == 1
    # grow M by juxtaposition — the common live round; same rule, fresh parse
    m2 = parse_egif(generate_egif(m1) + ' (man "Plato")')
    out2, rep2 = mat.materialize(m2)
    assert _mat_equal(out2, m2)                       # Plato derived mortal via the delta
    assert ("mortal", "Plato") in _facts(out2)
    assert mat.extensions == 1 and mat.rebuilds == 1  # extended, not rebuilt: the rule
                                                      # survived reparse (canonicalization)
    # the same M again (an audit re-peel) is a pure cache hit
    out3, _ = mat.materialize(m2)
    assert mat.hits == 1 and _facts(out3) == _facts(out2)


def test_incremental_recursive_rule_extends_the_closure():
    from model_materialization import IncrementalMaterializer
    mat = IncrementalMaterializer()
    law = '~[ (path *x *y) (edge y *z) ~[ (path x z) ] ]'
    m1 = parse_egif(f'(path "a" "b") (edge "b" "c") {law}')
    out1, _ = mat.materialize(m1)
    assert ("path", "a", "c") in _facts(out1)
    # a new edge arrives: the transitive closure must extend through the OLD facts
    m2 = parse_egif(generate_egif(m1) + ' (edge "c" "d")')
    out2, _ = mat.materialize(m2)
    assert mat.extensions == 1
    assert {("path", "a", "c"), ("path", "a", "d")} <= _facts(out2)
    assert _mat_equal(out2, m2)


def test_incremental_falls_back_to_full_on_retraction_and_rule_change():
    from model_materialization import IncrementalMaterializer
    mat = IncrementalMaterializer()
    m1 = parse_egif('(swan "Alba") (swan "Ciel") ~[ (swan *x) ~[ (white x) ] ]')
    mat.materialize(m1)
    # an atom retracted (decay / a game move): not a superset → one full rebuild, exact
    m2 = parse_egif('(swan "Alba") ~[ (swan *x) ~[ (white x) ] ]')
    out2, _ = mat.materialize(m2)
    assert mat.rebuilds == 2 and _mat_equal(out2, m2)
    assert ("white", "Ciel") not in _facts(out2)      # no stale derivation survives
    # a rule change (the law relinquished): again a full rebuild, exact
    m3 = parse_egif('(swan "Alba")')
    out3, _ = mat.materialize(m3)
    assert mat.rebuilds == 3 and _mat_equal(out3, m3)
    assert _facts(out3) == {("swan", "Alba")}


def test_incremental_peel_verdicts_match_the_uncached_peel():
    from agon_evolution import peel
    from model_materialization import IncrementalMaterializer
    mat = IncrementalMaterializer()
    m = parse_egif('(man "Socrates") ~[ (man *x) ~[ (mortal x) ] ]')
    for proposal in ['(mortal "Socrates")', '(mortal "Plato")', '(man "Socrates")']:
        assert (peel(m, proposal, materializer=mat).verdict
                is peel(m, proposal).verdict)


# ---------------------------------------------------------------------------
# K3 — the materialization ratio (THE_MEASURE_OF_KNOWLEDGE §2, authorized
# 2026-07-17): compression = derived atoms per law, with non-Horn laws counted
# in the denominator (no compression credit without evaluable evidence).
# ---------------------------------------------------------------------------

def test_k3_syllogism_ratio():
    from model_materialization import materialization_ratio
    M = parse_egif('(man "Socrates") (man "Plato") '
                   '~[ (man *x) ~[ (mortal x) ] ]')
    k3 = materialization_ratio(M)
    assert k3.explicit == 2
    assert k3.derived == 2          # mortal(Socrates), mortal(Plato)
    assert k3.horn_laws == 1 and k3.skipped_laws == 0
    assert k3.ratio == 0.5          # derived / (explicit + derived) = 2/4, bounded in [0,1)
    assert k3.yield_per_law == 2.0  # the old derived/laws number, honestly renamed

def test_k3_no_laws_is_zero_not_error():
    from model_materialization import materialization_ratio
    k3 = materialization_ratio(parse_egif('(bird "Tweety")'))
    assert k3.derived == 0 and k3.horn_laws == 0
    assert k3.ratio == 0.0
    assert k3.yield_per_law == 0.0

def test_k3_non_horn_law_weighs_the_denominator():
    from model_materialization import materialization_ratio
    # one productive Horn law + one non-Horn shape (disjunctive head — skipped):
    # the skipped law earns no credit but still counts as a law M carries —
    # now against yield_per_law's denominator (ratio's denominator is the
    # extent-based explicit+derived count, untouched by law count).
    M = parse_egif('(man "Socrates") '
                   '~[ (man *x) ~[ (mortal x) ] ] '
                   '~[ (animal *y) ~[ ~[ (cat y) ] ~[ (dog y) ] ] ]')
    k3 = materialization_ratio(M)
    assert k3.horn_laws == 1 and k3.skipped_laws >= 1
    assert k3.yield_per_law == k3.derived / (k3.horn_laws + k3.skipped_laws)
    assert k3.yield_per_law < k3.derived / k3.horn_laws   # the skip genuinely weighs

def test_k3_ratio_is_extent_invariant():
    from model_materialization import materialization_ratio
    LAW = '~[ (man *x) ~[ (mortal x) ] ]'
    small = parse_egif(f'(man "S1") (man "S2") {LAW}')
    names = " ".join(f'(man "S{i}")' for i in range(1, 21))
    large = parse_egif(f'{names} {LAW}')
    k3_small, k3_large = materialization_ratio(small), materialization_ratio(large)
    assert k3_small.ratio == k3_large.ratio == 0.5           # extent-invariant
    assert k3_small.yield_per_law == 2.0
    assert k3_large.yield_per_law == 20.0                    # yield still scales with N
