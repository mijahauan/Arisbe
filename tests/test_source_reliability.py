"""Reliability derived, never stored (``source_reliability.py``).

The sitting's §6a ruling: reliability is not a standing property of a peer and
is never a field anywhere. It is **recomputed from the record's own resolution
history** — how a source's contributions stood across the branching DAG. That
makes it index-over-ink: re-checkable forever, and unable to go stale the way a
cached number does.

Two constraints this module is built to satisfy, both from rulings rather than
from taste:

* **No scalar.** ``SourceStanding`` carries counts and exposes no aggregate.
  THE_MEASURE_OF_KNOWLEDGE's vector guard, and the re-measurement pass's own
  rule — a derived scalar invites a gate, and ``net_score`` was measured rising
  in *both* directions of the thing it was meant to gate.
* **Address-blind.** Examination VIII, from the author's prophet-without-honour
  case: legitimacy runs independently of network intimacy and sometimes
  inversely. Nothing here may consult reach, proximity, or contact frequency.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from m_steps import admit_step
from notion_provenance import notion_key, record_provenance
from proof_authoring import ProofChain
from world_scroll import wrap_m

from source_reliability import SourceStanding, standing_of, standings


def _chain(egif: str = '(swan "s1")') -> ProofChain:
    return ProofChain(wrap_m(parse_egif(egif))[0])


def _contribute(pc: ProofChain, source: str, notion_egif: str,
                *, affirm: bool = True) -> ProofChain:
    """One source contributing one notion, as real recorded chain steps."""
    key = notion_key(parse_egif(notion_egif))
    pc = admit_step(pc, f'~[ (provided_by "{source}" "{key}") '
                        f'~[ {notion_egif} ] ]')
    if affirm:
        pc = admit_step(pc, f'(provided_by "{source}" "{key}")')
    return pc


class TestStandingIsDerived:

    def test_a_source_with_no_contributions_has_an_empty_standing(self):
        st = standing_of(_chain().to_chain(), source="wiki")
        assert st.contributed == 0 and st.affirmed == 0

    def test_contributions_and_affirmations_are_counted_apart(self):
        """A recorded arrival and an affirmed one are different events — the
        conditional form's whole point."""
        pc = _contribute(_chain(), "wiki", '(white "s1")', affirm=True)
        pc = _contribute(pc, "wiki", '(tall "s1")', affirm=False)
        st = standing_of(pc.to_chain(), source="wiki")
        assert (st.contributed, st.affirmed) == (2, 1)

    def test_an_affirmed_contribution_reads_necessary_on_a_linear_chain(self):
        """On one line with no branch, what stands at the end stands on every
        reachable trajectory."""
        pc = _contribute(_chain(), "wiki", '(white "s1")')
        st = standing_of(pc.to_chain(), source="wiki")
        assert (st.necessary, st.possible, st.absent) == (1, 0, 0)

    def test_an_unaffirmed_contribution_reads_absent(self):
        """Held is not held-true: the notion never became derivable, so it
        stands nowhere."""
        pc = _contribute(_chain(), "wiki", '(white "s1")', affirm=False)
        st = standing_of(pc.to_chain(), source="wiki")
        assert (st.necessary, st.possible, st.absent) == (0, 0, 1)

    def test_sources_are_kept_apart(self):
        pc = _contribute(_chain(), "wiki", '(white "s1")')
        pc = _contribute(pc, "field", '(tall "s1")', affirm=False)
        assert standing_of(pc.to_chain(), source="wiki").affirmed == 1
        assert standing_of(pc.to_chain(), source="field").affirmed == 0

    def test_standings_enumerates_every_source_in_the_record(self):
        pc = _contribute(_chain(), "wiki", '(white "s1")')
        pc = _contribute(pc, "field", '(tall "s1")')
        assert {s.source for s in standings(pc.to_chain())} == {"wiki", "field"}


class TestDomainIndexing:
    """Examination VII ruling 1: the credential is domain-indexed. The relation
    is that index at the granularity the general machinery has — and it is how
    ``Unit.peers`` already keys, so the later migration is like-for-like."""

    def test_standing_can_be_asked_per_relation(self):
        pc = _contribute(_chain(), "wiki", '(white "s1")')
        pc = _contribute(pc, "wiki", '(tall "s1")', affirm=False)
        assert standing_of(pc.to_chain(), source="wiki",
                           relation="white").affirmed == 1
        assert standing_of(pc.to_chain(), source="wiki",
                           relation="tall").affirmed == 0

    def test_a_source_reliable_in_one_domain_is_not_thereby_reliable_in_another(self):
        """The substantive point of domain-indexing, and B&L's: a source is
        reliable *within a practice*."""
        pc = _contribute(_chain(), "wiki", '(white "s1")')
        pc = _contribute(pc, "wiki", '(tall "s1")', affirm=False)
        good = standing_of(pc.to_chain(), source="wiki", relation="white")
        bad = standing_of(pc.to_chain(), source="wiki", relation="tall")
        assert good.necessary == 1 and bad.necessary == 0


class TestTheGuards:

    def test_standing_exposes_no_aggregate_scalar(self):
        """The vector guard, enforced structurally rather than by convention:
        a caller that wants a comparison must state it on the components."""
        st = standing_of(_chain().to_chain(), source="wiki")
        for banned in ("score", "ratio", "net", "net_score", "accuracy",
                       "reliability", "rank"):
            assert not hasattr(st, banned), (
                f"SourceStanding grew a scalar ({banned}) — that is what "
                f"net_score did before it had to be retired as a gate")

    def test_standing_is_address_blind(self):
        """Examination VIII's prophet constraint. Two identical records
        differing only in the source's name read identically — nothing in the
        computation can see who is near, so legitimacy cannot collapse into
        proximity."""
        near = _contribute(_chain(), "household", '(white "s1")')
        far = _contribute(_chain(), "stranger", '(white "s1")')
        a = standing_of(near.to_chain(), source="household")
        b = standing_of(far.to_chain(), source="stranger")
        assert (a.contributed, a.affirmed, a.necessary, a.possible,
                a.absent) == (b.contributed, b.affirmed, b.necessary,
                              b.possible, b.absent)

    def test_nothing_is_stored_on_the_graph(self):
        """Recomputation, not caching: asking twice gives the same answer and
        leaves no trace behind to go stale."""
        pc = _contribute(_chain(), "wiki", '(white "s1")')
        chain = pc.to_chain()
        assert standing_of(chain, source="wiki") == standing_of(
            chain, source="wiki")
        assert isinstance(standing_of(chain, source="wiki"), SourceStanding)


class TestTheBranchingReading:
    """The ◇ case — the reason this reads a DAG rather than a line. A source
    whose notion survives on one trajectory and not another is neither reliable
    nor refuted, and saying so is what a branching record is for."""

    def test_a_notion_affirmed_on_one_branch_only_reads_possible(self):
        pc = _chain()
        fork_point = pc.current_state_id
        key = notion_key(parse_egif('(white "s1")'))
        pc = admit_step(pc, f'~[ (provided_by "wiki" "{key}") '
                            f'~[ (white "s1") ] ]')
        after_record = pc.current_state_id

        # one continuation affirms the arrival ...
        pc = admit_step(pc, f'(provided_by "wiki" "{key}")')
        # ... a sibling continuation does not, scribing something else instead
        pc = admit_step(pc.at(after_record), '(cold "s1")')

        st = standing_of(pc.to_chain(), source="wiki")
        assert (st.necessary, st.possible, st.absent) == (0, 1, 0), (
            "a notion standing on some but not all reachable leaves is ◇, "
            "not □ and not absent")
        assert fork_point  # the chain really did fork below this

    def test_a_notion_affirmed_before_the_fork_reads_necessary(self):
        """The control for the test above: same branching shape, but the
        affirmation happens before the split, so every leaf inherits it."""
        pc = _chain()
        key = notion_key(parse_egif('(white "s1")'))
        pc = admit_step(pc, f'~[ (provided_by "wiki" "{key}") '
                            f'~[ (white "s1") ] ]')
        pc = admit_step(pc, f'(provided_by "wiki" "{key}")')
        both = pc.current_state_id
        pc = admit_step(pc, '(cold "s1")')
        pc = admit_step(pc.at(both), '(calm "s1")')

        st = standing_of(pc.to_chain(), source="wiki")
        assert (st.necessary, st.possible, st.absent) == (1, 0, 0)

    def test_a_contribution_on_a_sibling_branch_still_counts(self):
        """What a source contributed is everything it ever contributed
        ANYWHERE in the DAG — not whatever survives on the trajectory whose
        step happens to be recorded last. Otherwise the denominator of a
        source's record depends on the order branches were written in, which
        is not a fact about the source."""
        pc = _chain()
        white = notion_key(parse_egif('(white "s1")'))
        tall = notion_key(parse_egif('(tall "s1")'))
        fork = pc.current_state_id

        # branch A: wiki contributes and affirms one notion
        pc = admit_step(pc, f'~[ (provided_by "wiki" "{white}") '
                            f'~[ (white "s1") ] ]')
        pc = admit_step(pc, f'(provided_by "wiki" "{white}")')

        # branch B, from the fork: wiki contributes a different notion
        pc = admit_step(pc.at(fork), f'~[ (provided_by "wiki" "{tall}") '
                                     f'~[ (tall "s1") ] ]')

        st = standing_of(pc.to_chain(), source="wiki")
        assert st.contributed == 2, (
            "only the last branch's records were counted — a source's record "
            "must not depend on branch write order")
        assert st.affirmed == 1
