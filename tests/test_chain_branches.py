"""The branch enumerator — the orientation substrate for branching UoDs.

``chain_branches.branch_report`` answers the Transparency Charter P1 question
a reader of a branching UoD must be able to answer from visible text alone:
*which branch am I on, and how many are there?* These tests pin:

1. a linear chain reads as ONE branch named "main";
2. a fork reads as two branches with the fork state named;
3. the convergence DIAMOND is honest — the converged state belongs to BOTH
   branches (tracked by step ids, since the state id repeats);
4. labels come from ``branch_id`` (a relabeled line joins its journey,
   "prosperity → late-ruin"); an unlabeled fork falls back to
   "main"/"branch N" (Ergasterion's vocabulary, charter P2);
5. determinism (authored order; two calls identical).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import eg_navigation as nav
from chain_branches import branch_report
from proof_authoring import ProofChain

_P = lambda g: nav.child_edges(g, g.sheet, "P")[0]   # noqa: E731
_Q = lambda g: nav.child_edges(g, g.sheet, "Q")[0]   # noqa: E731
_R = lambda g: nav.child_edges(g, g.sheet, "R")[0]   # noqa: E731


def _linear() -> ProofChain:
    pc = ProofChain.from_egif("(P) (Q)")
    pc.apply("ERA", select=_P)
    pc.apply("ERA", select=_Q)
    return pc


def _fork(labels=("L", "R")) -> ProofChain:
    pc = ProofChain.from_egif("(P) (Q)")
    pc.apply("ERA", select=_P, branch=labels[0])
    pc.at("s0")
    pc.apply("ERA", select=_Q, branch=labels[1])
    return pc


def _diamond() -> ProofChain:
    """(P)(Q)(R) → (R) two ways; both lines converge on s2."""
    pc = ProofChain.from_egif("(P) (Q) (R)")
    pc.apply("ERA", select=_P, branch="L")
    pc.apply("ERA", select=_Q, branch="L")
    pc.at("s0")
    pc.apply("ERA", select=_Q, branch="R")
    pc.apply("ERA", select=_P, branch="R")
    pc.converge_last_into("s2")
    return pc


class TestLinear:
    def test_one_branch_named_main(self):
        rep = branch_report(_linear().to_chain())
        assert not rep.branching and rep.count == 1
        assert rep.branches[0].label == "main"
        assert rep.branches[0].state_ids == ["s0", "s1", "s2"]
        assert rep.branches[0].step_count == 2
        assert rep.fork_state_ids == [] and rep.convergence_state_ids == []
        assert all(v == [0] for v in rep.membership.values())

    def test_bare_initial_state_is_one_empty_line(self):
        rep = branch_report(ProofChain.from_egif("(P)").to_chain())
        assert rep.count == 1 and rep.branches[0].step_count == 0
        assert rep.branches[0].leaf_state_id == "s0"


class TestFork:
    def test_two_branches_and_the_fork_named(self):
        rep = branch_report(_fork().to_chain())
        assert rep.branching and rep.count == 2
        assert rep.fork_state_ids == ["s0"]
        assert [b.label for b in rep.branches] == ["L", "R"]
        assert rep.membership["s0"] == [0, 1]      # shared root
        assert rep.membership["s1"] == [0]
        assert rep.membership["s2"] == [1]

    def test_unlabeled_fork_falls_back_to_ergasterion_vocabulary(self):
        pc = ProofChain.from_egif("(P) (Q)")
        pc.apply("ERA", select=_P)
        pc.at("s0")
        pc.apply("ERA", select=_Q)
        rep = branch_report(pc.to_chain())
        assert [b.label for b in rep.branches] == ["main", "branch 1"]

    def test_continuations_carry_the_forward_labels(self):
        rep = branch_report(_fork(("wind-rises", "clears-first")).to_chain())
        conts = rep.continuations["s0"]
        assert [c["label"] for c in conts] == ["wind-rises", "clears-first"]
        assert [c["branch_indices"] for c in conts] == [[0], [1]]
        assert all(c["rule"] == "ERA" for c in conts)


class TestDiamond:
    def test_converged_state_belongs_to_both_branches(self):
        rep = branch_report(_diamond().to_chain())
        assert rep.count == 2
        assert rep.convergence_state_ids == ["s2"]
        assert rep.membership["s2"] == [0, 1]
        # one leaf state, two distinct step paths to it
        assert {b.leaf_state_id for b in rep.branches} == {"s2"}
        a, b = rep.branches
        assert a.step_ids != b.step_ids
        assert a.state_ids == ["s0", "s1", "s2"]
        assert b.state_ids == ["s0", "s3", "s2"]

    def test_labels(self):
        rep = branch_report(_diamond().to_chain())
        assert [b.label for b in rep.branches] == ["L", "R"]


class TestLabelJourney:
    def test_relabeled_line_joins_its_journey(self):
        pc = ProofChain.from_egif("(P) (Q) (R)")
        pc.apply("ERA", select=_P, branch="prosperity")
        pc.apply("ERA", select=_Q, branch="late-ruin")
        pc.at("s0")
        pc.apply("ERA", select=_R, branch="ruin-first")
        rep = branch_report(pc.to_chain())
        labels = {b.label for b in rep.branches}
        assert "prosperity → late-ruin" in labels
        assert "ruin-first" in labels


class TestDeterminism:
    def test_two_calls_identical_and_authored_order(self):
        chain = _diamond().to_chain()
        r1, r2 = branch_report(chain), branch_report(chain)
        assert r1.to_dict() == r2.to_dict()
        # branch 0 = the earliest-authored line
        assert r1.branches[0].step_ids[0] == chain.steps[0].step_id

    def test_json_ready(self):
        import json

        d = branch_report(_diamond().to_chain()).to_dict()
        json.dumps(d)  # raises if not JSON-serializable
        assert d["count"] == 2 and d["branching"] is True
        assert d["truncated"] is False
