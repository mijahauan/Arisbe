"""The dry-run consequence trace (PEEL-twin housing) — V.4 fixed at the source.

Spec: docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md §3.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from alternative_trace import (
    BoundedRegister, KyteProfile, TraceResult, UnrepresentableAtomError,
    atom_and_denial_egif, trace_unknown,
)
from egif_parser_dau import parse_egif

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


def _registers():
    p = KyteProfile()
    return BoundedRegister(p.s_capacity), BoundedRegister(p.a_capacity)


class TestAtomAndDenial:
    def test_ground_atom(self):
        atom, denial = atom_and_denial_egif("white", ("Alba",))
        assert atom == '(white "Alba")'
        assert denial == '~[ (white "Alba") ]'

    def test_generic_slot_renders_defining_variable_never_None(self):
        # The V.4 kill: an unwitnessed existential is a question about a line
        # of identity, never a constant named "None".
        atom, denial = atom_and_denial_egif("loves", ("Alba", None))
        assert atom == '(loves "Alba" *x)'
        assert '"None"' not in atom and '"None"' not in denial
        g = parse_egif(atom)                     # parses as a real existential
        assert sum(1 for v in g.V if v.is_generic) == 1

    def test_two_generic_slots_get_distinct_variables(self):
        atom, _ = atom_and_denial_egif("between", (None, "B", None))
        assert atom == '(between *x "B" *x2)'

    def test_unrepresentable_label_refused_never_mangled(self):
        with pytest.raises(UnrepresentableAtomError):
            atom_and_denial_egif("said", ('he said "hi"',))

    def test_escaped_label_round_trips(self):
        # A label already in the parser's escaped form round-trips fine.
        atom, _ = atom_and_denial_egif("said", ('he said \\"hi\\"',))
        parse_egif(atom)


class TestBoundedRegister:
    def test_lru_displacement_counted(self):
        r = BoundedRegister(2)
        assert r.admit("a") is None
        assert r.admit("b") is None
        assert r.admit("c") == "a"
        assert r.displaced == 1 and r.admitted == 3
        assert r.terms == ["b", "c"]

    def test_snapshot_restore_round_trips(self):
        r = BoundedRegister(2)
        r.admit("a"); r.admit("b"); r.admit("a"); r.admit("c")
        r2 = BoundedRegister.restore(r.snapshot())
        assert r2.snapshot() == r.snapshot()
        # Order semantics survive restore: "a" (refreshed at seq 3) is older
        # than "c" (seq 4), so it is the LRU victim — a restore that mangled
        # the touch order would evict "c" instead.
        assert r2.admit("d") == "a"


class TestTraceUnknown:
    def test_material_through_the_law(self):
        # Asserting (swan "Dover") derives (white "Dover") via the law;
        # denying derives nothing: the branches diverge on "white".
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "swan", ("Dover",),
                           s_register=s, a_register=a)
        assert tr.materiality.tier == "material"
        assert "white" in tr.materiality.diverging
        assert 'white("Dover")' in tr.materiality.extra_true

    def test_bare_when_no_law_touches_it(self):
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "black", ("Dover",),
                           s_register=s, a_register=a)
        assert tr.materiality.tier == "bare"

    def test_m_is_never_mutated(self):
        import eg_navigation as nav
        m = parse_egif(M0)
        before = parse_egif(M0)
        s, a = _registers()
        trace_unknown(m, "swan", ("Dover",), s_register=s, a_register=a)
        assert nav.same_graph(m, before)

    def test_existential_traces_without_corruption(self):
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "loves", ("Ciel", None),
                           s_register=s, a_register=a)
        assert '"None"' not in tr.atom_egif
        assert tr.materiality.tier in ("material", "bare", "spurious")

    def test_s_a_refinement_recorded_in_order(self):
        s, a = _registers()
        tr = trace_unknown(parse_egif(M0), "swan", ("Dover",),
                           s_register=s, a_register=a)
        assert "derivable:white" in tr.s_admitted
        assert "distinction:swan" in tr.s_admitted
        assert "resolve:swan" in tr.a_admitted
        assert f"distinction:swan" in s.terms
