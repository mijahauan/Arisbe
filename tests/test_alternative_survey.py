"""The two survey producers (spec 2026-07-26-close-the-arc §2, D-2/D-3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from world_scroll import wrap_m

from alternative_index import alt_key
from alternative_survey import (BranchSurvey, ThinSpotSurvey, survey_branches,
                                survey_thin_spots)

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
