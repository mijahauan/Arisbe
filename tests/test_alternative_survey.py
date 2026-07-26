"""The two survey producers (spec 2026-07-26-close-the-arc §2, D-2/D-3)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from world_scroll import wrap_m

from alternative_index import alt_key
from alternative_survey import (BRANCHES_ACT, THIN_SPOTS_ACT, BranchSurvey,
                                ThinSpotSurvey, branch_survey_step,
                                records_from_survey_step, survey_branches,
                                survey_thin_spots, thin_spot_step)

# One-instance relation (swan/white grounded), a zero-grounded law body
# (dragon), its zero-grounded head (fears), and a lonely individual (Ciel
# appears twice → not lonely; Rex once → lonely).
FIXTURE_M = ('(swan "Ciel") (white "Ciel") (dog "Rex") '
             '~[ (dragon *x) ~[ (fears x) ] ]')


class TestThinSpotSurvey:
    def _survey(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        return survey_thin_spots(wrapped)

    def test_zero_grounded_relations_surface_as_unary_existentials(self):
        s = self._survey()
        assert ("dragon", (None,)) in s.unknowns
        assert ("fears", (None,)) in s.unknowns

    def test_grounded_relations_do_not_surface(self):
        # D-2: a 1-instance relation's (r *x) already HOLDS — a record would
        # be born settled. Named, recordless.
        s = self._survey()
        surfaced = {r for r, _ in s.unknowns}
        assert "swan" not in surfaced and "dog" not in surfaced
        assert "dog" in s.thin_but_grounded
        assert "swan" in s.thin_but_grounded

    def test_lonely_individuals_named_recordless(self):
        s = self._survey()
        assert "Rex" in s.lonely_individuals
        assert "Ciel" not in s.lonely_individuals

    def test_deterministic_order(self):
        a, b = self._survey(), self._survey()
        assert a == b
        assert list(a.unknowns) == sorted(a.unknowns)


class TestBranchSurvey:
    def _forked_chain(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from world_scroll import enlarge_m
        from m_steps import admit_step
        base = pc.current_state_id
        admit_step(pc, '(cloudy "sky")', disposition="new_fact", branch="wx-a")
        pc.at(base)
        admit_step(pc, '(calm "sea")', disposition="new_fact", branch="wx-b")
        return pc, base

    def test_contested_atoms_surface_with_evidence(self):
        pc, base = self._forked_chain()
        s = survey_branches(pc.to_chain(), at=base)
        assert base in s.fork_states
        assert ("cloudy", ("sky",)) in s.unknowns
        assert ("calm", ("sea",)) in s.unknowns
        ev = {k: (ins, outs) for k, ins, outs in s.evidence}
        ins, outs = ev[alt_key("cloudy", ("sky",))]
        assert len(ins) == 1 and len(outs) == 1 and ins != outs

    def test_atoms_held_at_reference_state_do_not_surface(self):
        pc, base = self._forked_chain()
        # swan Ciel holds everywhere incl. the reference state → never contested
        s = survey_branches(pc.to_chain(), at=base)
        assert ("swan", ("Ciel",)) not in s.unknowns

    def test_upto_prefix_excludes_later_steps(self):
        pc, base = self._forked_chain()
        chain = pc.to_chain()
        first_step = chain.steps[0].step_id
        s = survey_branches(chain, upto=first_step, at=base)
        assert s.fork_states == () and s.unknowns == ()

    def test_no_fork_no_unknowns(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from m_steps import admit_step
        admit_step(pc, '(white "Ciel")', disposition="new_fact")
        s = survey_branches(pc.to_chain())
        assert s.fork_states == () and s.unknowns == ()

    def test_held_at_reference_excludes_only_via_not_held_filter(self):
        # Exercise the `and atom not in held` clause in isolation: pick the
        # reference state to be branch A's own tip, where cloudy genuinely
        # holds. cloudy is still contested across leaves (present at A,
        # absent at B) — only the held-at-reference filter keeps it out.
        # calm does not hold at the reference (tip A) and is contested, so
        # it must surface.
        pc, base = self._forked_chain()
        chain = pc.to_chain()
        tip_a = chain.steps[0].to_state_id
        s = survey_branches(chain, at=tip_a)
        assert ("cloudy", ("sky",)) not in s.unknowns
        assert ("calm", ("sea",)) in s.unknowns

    def test_generic_atoms_excluded_by_ground_only_filter(self):
        # Exercise the `all(l is not None ...)` ground-only filter in
        # isolation: '(rain *x)' admitted on one branch produces a generic
        # sheet atom ('rain', (None,)) at that leaf — present at A, absent
        # at B, so it IS contested-across-leaves, but must never surface
        # (it isn't a ground atom to begin with).
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from m_steps import admit_step
        base = pc.current_state_id
        admit_step(pc, '(rain *x)', disposition="new_fact", branch="wx-a")
        pc.at(base)
        admit_step(pc, '(calm "sea")', disposition="new_fact", branch="wx-b")
        s = survey_branches(pc.to_chain(), at=base)
        surfaced_rels = {r for r, _ in s.unknowns}
        assert "rain" not in surfaced_rels
        ev_keys = {k for k, _, _ in s.evidence}
        assert alt_key("rain", (None,)) not in ev_keys
        assert ("calm", ("sea",)) in s.unknowns


class TestSurveySteps:
    def test_thin_spot_step_records_peel_shaped_params(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        pc = ProofChain(wrapped)
        thin_spot_step(pc)
        step = pc.to_chain().steps[-1]
        p = step.parameters
        assert p["act"] == THIN_SPOTS_ACT and p["earned"] is True
        assert ["dragon", ["*"]] in p["unknown_atoms"]
        assert p["budget"] == 8 and p["refused_budget"] == []
        assert "dog" in p["thin_but_grounded"]
        assert "Rex" in p["lonely_individuals"]
        # identity transform: m_view unchanged
        assert step.from_state_id != step.to_state_id

    def test_budget_refuses_and_counts(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        pc = ProofChain(wrapped)
        thin_spot_step(pc, budget=1)
        p = pc.to_chain().steps[-1].parameters
        assert len(p["unknown_atoms"]) == 1
        assert len(p["refused_budget"]) >= 1     # named, never dropped

    @pytest.mark.xfail(reason="KINDS_BUILT extended in Task 5", strict=True)
    def test_records_from_thin_spot_step_are_hypothetical(self):
        wrapped, _ = wrap_m(parse_egif(FIXTURE_M))
        pc = ProofChain(wrapped)
        thin_spot_step(pc)
        step = pc.to_chain().steps[-1]
        recs = records_from_survey_step(step, round_idx=3)
        assert recs and all(r.kind == "hypothetical" for r in recs)
        assert all(r.emerged_from == step.step_id for r in recs)
        assert all(r.emerged_round == 3 for r in recs)
        by_key = {r.key: r for r in recs}
        dragon = by_key[alt_key("dragon", (None,))]
        assert dragon.alternatives[0] == "(dragon *x)"
        assert dragon.alternatives[1] == "~[ (dragon *x) ]"

    @pytest.mark.xfail(reason="KINDS_BUILT extended in Task 5", strict=True)
    def test_branch_survey_step_records_evidence(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from m_steps import admit_step
        base = pc.current_state_id
        admit_step(pc, '(cloudy "sky")', disposition="new_fact")
        pc.at(base)
        admit_step(pc, '(calm "sea")', disposition="new_fact")
        pc.at(base)
        branch_survey_step(pc, at=base)
        step = pc.to_chain().steps[-1]
        p = step.parameters
        assert p["act"] == BRANCHES_ACT and p["at"] == base
        assert base in p["fork_states"]
        assert ["cloudy", ["sky"]] in p["unknown_atoms"]
        recs = records_from_survey_step(step)
        assert recs and all(r.kind == "modal" for r in recs)

    def test_records_from_non_survey_step_refused(self):
        wrapped, _ = wrap_m(parse_egif('(swan "Ciel")'))
        pc = ProofChain(wrapped)
        from m_steps import admit_step
        admit_step(pc, '(white "Ciel")', disposition="new_fact")
        with pytest.raises(ValueError):
            records_from_survey_step(pc.to_chain().steps[-1])
