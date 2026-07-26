"""The dry-run consequence trace (PEEL-twin housing) — V.4 fixed at the source.

Spec: docs/superpowers/specs/2026-07-26-alternative-index-over-ink-design.md §3.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

import eg_navigation as nav
from alternative_index import record_from_trace_step
from alternative_trace import (
    BoundedRegister, KyteProfile, TraceResult, UnrepresentableAtomError,
    atom_and_denial_egif, trace_batch, trace_step, trace_unknown, TRACE_ALTERNATIVES,
)
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from world_scroll import m_view, wrap_m

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


def _chain_from(m_egif: str) -> ProofChain:
    wrapped, _ = wrap_m(parse_egif(m_egif))
    return ProofChain(wrapped)


class TestTraceStep:
    def test_recorded_earned_and_identity(self):
        pc = _chain_from(M0)
        before = pc.current
        s, a = _registers()
        tr = trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
        step = pc.to_chain().steps[-1]
        assert step.rule_name == TRACE_ALTERNATIVES
        p = step.parameters
        assert p["act"] == "alternatives_traced" and p["earned"] is True
        assert p["tier"] == tr.materiality.tier == "material"
        assert p["labels"] == ["Dover"]
        assert p["key"] == 'swan("Dover")'
        # Identity transform, fresh state, m_view untouched.
        assert step.from_state_id != step.to_state_id
        assert nav.same_graph(m_view(pc.current), m_view(before))

    def test_trace_is_neutral_for_proof_character(self):
        from proof_character import character_of_chain
        pc = _chain_from(M0)
        s, a = _registers()
        trace_step(pc, "swan", ("Dover",), s_register=s, a_register=a)
        assert character_of_chain(pc.to_chain()).character == "corollarial"

    def test_record_from_trace_step(self):
        pc = _chain_from(M0)
        s, a = _registers()
        trace_step(pc, "loves", ("Ciel", None), s_register=s, a_register=a)
        step = pc.to_chain().steps[-1]
        rec = record_from_trace_step(step)
        assert rec.key == 'loves("Ciel",*)'
        assert rec.labels == ("Ciel", None)
        assert rec.traced_by == step.step_id
        assert rec.status == "traced"

    def test_batch_budget_count_or_refuse(self):
        pc = _chain_from(M0)
        s, a = _registers()
        unknowns = [("swan", ("Dover",)), ("black", ("Dover",)),
                    ("swan", ("Dover",))]          # duplicate → one trace
        batch = trace_batch(pc, unknowns, s_register=s, a_register=a, budget=1)
        assert len(batch.results) == 1
        assert batch.refused_budget == ('black("Dover")',)

    def test_batch_counts_unrepresentable(self):
        pc = _chain_from(M0)
        s, a = _registers()
        batch = trace_batch(pc, [("said", ('a "quote"',))],
                            s_register=s, a_register=a)
        assert batch.results == ()
        assert len(batch.unrepresentable) == 1


class TestFollowOnCleanups:
    """Spec 2026-07-26-close-the-arc §4 / AC19."""

    def test_bounded_register_zero_capacity_admits_nothing(self):
        reg = BoundedRegister(0)
        out = reg.admit("a")
        assert out == "a"                      # refused, returned as displaced
        assert len(reg) == 0
        assert reg.displaced == 1
        assert reg.admitted == 0
        restored = BoundedRegister.restore(reg.snapshot())
        assert restored.snapshot() == reg.snapshot()

    def test_bounded_register_capacity_one_unchanged(self):
        reg = BoundedRegister(1)
        assert reg.admit("a") is None
        assert reg.admit("b") == "a"           # byte-identical to shipped LRU
        assert len(reg) == 1 and reg.displaced == 1 and reg.admitted == 2

    def test_diverging_simplification_is_equivalent(self):
        # rels_t ^ rels_f ⊆ {r for r,_ in extra_t ^ extra_f} — pin the
        # equivalence on sets exercising both original clauses.
        cases = [
            ({("p", ("a",))}, {("q", ("b",))}),               # one-side-only rels
            ({("p", ("a",)), ("r", ("c",))}, {("p", ("b",))}),  # shared rel, differing atoms
            ({("p", ("a",))}, {("p", ("a",))}),               # identical → empty
            (set(), {("q", ("b",))}),                          # empty side
        ]
        for extra_t, extra_f in cases:
            rels_t = {r for r, _ in extra_t}
            rels_f = {r for r, _ in extra_f}
            old = tuple(sorted(
                (rels_t ^ rels_f) | {r for r, _ in (extra_t ^ extra_f)}))
            new = tuple(sorted({r for r, _ in (extra_t ^ extra_f)}))
            assert old == new

    def test_k3_check_does_not_rematerialize(self, monkeypatch):
        import alternative_trace as at
        import model_materialization as mm
        calls = {"n": 0}
        real = mm.materialize_egi
        def counting(egi, **kw):
            calls["n"] += 1
            return real(egi, **kw)
        monkeypatch.setattr(at, "materialize_egi", counting)
        monkeypatch.setattr(mm, "materialize_egi", counting)
        m = parse_egif('(swan "Ciel")')
        tr = trace_unknown(m, "phoenix", ("Ciel",),
                           s_register=BoundedRegister(8),
                           a_register=BoundedRegister(8))
        # empty branch-diffs exercise the K3 branch (tier reads "bare" here:
        # the explicit counts differ, 2 vs 1); base + true + false = 3 calls,
        # no fourth/fifth from materialization_ratio.
        assert tr.materiality.k3_true is not None      # the K3 branch ran
        assert calls["n"] == 3
        # numbers identical to an independent materialization_ratio read
        from model_materialization import materialization_ratio
        base = tr.materiality
        kc = materialization_ratio(assert_fact_helper(m, tr.atom_egif))
        assert base.k3_true == (kc.explicit, kc.derived)

    def test_refused_unknown_is_counted_at_batch_level(self):
        # D-5 as revised: raw embedded quote → refused AND counted.
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        batch = trace_batch(pc, [("said", ('he said "hi"',))],
                            s_register=BoundedRegister(8),
                            a_register=BoundedRegister(8))
        assert len(batch.results) == 0
        assert len(batch.unrepresentable) == 1


def assert_fact_helper(m, atom_egif):
    from model_revision import assert_fact
    from world_scroll import m_view
    return assert_fact(m_view(m), atom_egif)
