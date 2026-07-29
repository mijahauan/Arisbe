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


# Two laws deriving the SAME head from two different bodies, both of whose
# antecedents hold of "a".  `q1("a")` is therefore derivable two ways, so the
# tie-break in `_chase` is actually exercised — the single-path fixture above
# would pass against an implementation with no tie-break at all.
TWO_PATH_EGIF = (
    '~[ (p1 *x) ~[ (q1 x) ] ] ~[ (r1 *y) ~[ (q1 y) ] ] (p1 "a") (r1 "a")'
)


def test_provenance_tie_break_picks_the_smallest_support_deterministically():
    derived = ("q1", (("c", "a"),))
    via_p1 = frozenset({("p1", (("c", "a"),))})
    via_r1 = frozenset({("r1", (("c", "a"),))})

    seen = []
    for _ in range(5):
        prov = {}
        _facts_egi, report = materialize_egi(parse_egif(TWO_PATH_EGIF),
                                             provenance=prov)
        assert report.rules_applied == 2, "both derivation paths must be live"
        assert report.derived_facts == 1, "one head, reached two ways"
        assert derived in prov
        seen.append(prov[derived])

    # Deterministic across runs...
    assert all(s == seen[0] for s in seen)
    # ...and specifically the lexicographically smallest of the two candidate
    # supports: sorted([("p1", …)]) < sorted([("r1", …)]) because "p1" < "r1".
    assert sorted(via_p1) < sorted(via_r1)
    assert seen[0] == via_p1, (
        "the tie-break must keep the smallest support, not whichever the "
        f"iteration happened to reach first (got {sorted(seen[0])})"
    )
