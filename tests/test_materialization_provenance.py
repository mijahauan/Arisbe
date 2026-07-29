from egif_parser_dau import parse_egif
from model_materialization import materialize_egi

# A law (p1 x -> q1 x) plus one ground fact.  Two-character relation
# names: the EGIF lexer reads a single lowercase letter as a bound
# variable, never a relation name (egif_parser_dau._is_bound_variable).
EGIF = '~[ (p1 *x) ~[ (q1 x) ] ] (p1 "a")'


def test_provenance_records_the_support_of_a_derived_fact():
    egi = parse_egif(EGIF)
    prov = {}
    _facts_egi, report = materialize_egi(egi, provenance=prov)
    assert report.derived_facts == 1
    derived = ("q1", (("c", "a"),))
    assert derived in prov
    assert prov[derived] == frozenset({("p1", (("c", "a"),))})


def test_provenance_is_optional_and_backward_compatible():
    egi = parse_egif(EGIF)
    _facts_egi, report = materialize_egi(egi)
    assert report.derived_facts == 1


def test_provenance_is_deterministic_across_repeated_runs():
    seen = []
    for _ in range(5):
        prov = {}
        materialize_egi(parse_egif(EGIF), provenance=prov)
        seen.append({k: tuple(sorted(v)) for k, v in prov.items()})
    assert all(s == seen[0] for s in seen)
