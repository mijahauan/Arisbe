"""Branching reasoning episodes — the DAG substrate + the derivation-DAG endpoint.

A chain is a DAG in general: two steps sharing a ``from_state_id`` **fork** a line
of development, two sharing a ``to_state_id`` **converge** it (the alternate-proofs
diamond, realised natively in Dau's calculus). These pin the substrate
(``ProofChain.at`` / ``converge_last_into`` / ``branch`` + round-trip persistence of
``branch_id``) and the ``/history-structure`` ``dag`` block the lens consumes.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import eg_navigation as nav  # noqa: E402
from proof_authoring import ProofChain  # noqa: E402
from tomos_service import TomosService, ChainStep  # noqa: E402
from universe_of_discourse import UoDCategory  # noqa: E402
from web_api import main as web_main  # noqa: E402

_P = lambda g: nav.child_edges(g, g.sheet, "P")[0]   # noqa: E731
_Q = lambda g: nav.child_edges(g, g.sheet, "Q")[0]   # noqa: E731


def _diamond() -> ProofChain:
    """The confluence-of-erasure diamond: (P)(Q)(R) → (R), two ways."""
    pc = ProofChain.from_egif("(P) (Q) (R)")
    pc.apply("ERA", select=_P, branch="L")
    pc.apply("ERA", select=_Q, branch="L")        # → s2 = (R)
    pc.at("s0")
    pc.apply("ERA", select=_Q, branch="R")
    pc.apply("ERA", select=_P, branch="R")        # → s4 = (R)
    pc.converge_last_into("s2")
    return pc


# ---- substrate: ProofChain branch + converge --------------------------------

def test_at_forks_a_line_of_development():
    pc = _diamond()
    chain = pc.to_chain()
    froms = [s.from_state_id for s in chain.steps]
    assert froms.count("s0") == 2, "s0 should fork into two lines"


def test_converge_merges_to_one_state():
    chain = _diamond().to_chain()
    tos = [s.to_state_id for s in chain.steps]
    assert tos.count("s2") == 2, "both lines should converge on s2"
    assert "s4" not in chain.states, "the orphaned convergent state is dropped"


def test_branch_labels_recorded():
    chain = _diamond().to_chain()
    assert {s.branch_id for s in chain.steps} == {"L", "R"}


def test_converge_refuses_a_non_matching_state():
    pc = ProofChain.from_egif("(P) (Q)")
    pc.apply("ERA", select=_P)            # → (Q)
    with pytest.raises(ValueError):
        pc.converge_last_into("s0")        # s0 = (P)(Q) ≠ (Q)


def test_branching_chain_round_trips(tmp_path):
    pc = _diamond()
    _chain, uod = pc.to_uod(uod_id="t_branch", name="t", description="d",
                            category=UoDCategory.THEOREM_PROOF)
    svc = TomosService(tmp_path)
    svc.save_uod_with_chain(uod, pc.to_chain())
    loaded = svc.load_chain("t_branch")
    assert loaded is not None
    assert sorted(loaded.states) == ["s0", "s1", "s2", "s3"]
    assert [s.from_state_id for s in loaded.steps].count("s0") == 2   # fork survives
    assert [s.to_state_id for s in loaded.steps].count("s2") == 2     # merge survives
    assert {s.branch_id for s in loaded.steps} == {"L", "R"}          # labels survive


def test_linear_chain_still_has_no_branch_ids():
    pc = ProofChain.from_egif("(P) (Q)")
    pc.apply("ERA", select=_P)
    chain = pc.to_chain()
    assert all(s.branch_id is None for s in chain.steps)


# ---- the endpoint: the dag block --------------------------------------------

@pytest.fixture(scope="module")
def client():
    return TestClient(web_main.app)


def test_history_structure_emits_a_branching_dag(client):
    """The seeded ``branching_confluence`` UoD surfaces a fork-and-merge DAG."""
    r = client.get("/organon/uods/branching_confluence/history-structure")
    assert r.status_code == 200
    dag = r.json()["data"]["dag"]
    assert dag["branching"] is True
    assert len(dag["nodes"]) == 4 and len(dag["edges"]) == 4
    # depths layer the diamond: base 0, two middles 1, convergence 2
    depths = sorted(n["depth"] for n in dag["nodes"])
    assert depths == [0, 1, 1, 2]
    froms = [e["from"] for e in dag["edges"]]
    tos = [e["to"] for e in dag["edges"]]
    assert any(froms.count(f) > 1 for f in froms)   # a fork
    assert any(tos.count(t) > 1 for t in tos)       # a convergence
    assert {e["branch_id"] for e in dag["edges"]} == {"erase-P-first", "erase-Q-first"}


def test_chain_route_flags_branching(client):
    body = client.get("/organon/uods/branching_confluence/chain").json()["data"]
    assert body["branching"] is True
    # a linear proof is not flagged
    lin = client.get("/organon/uods/barbara/chain").json()["data"]
    assert lin.get("branching") is False


# ---- branch orientation: the branches block (charter P1) ---------------------

def test_chain_route_carries_branch_orientation(client):
    """Every frame carries its DAG linkage and the top-level branches block
    enumerates the lines of development — the data the player's branch strip
    and honest counter read."""
    body = client.get("/organon/uods/branching_confluence/chain").json()["data"]
    br = body["branches"]
    assert br["branching"] is True and br["count"] == 2
    assert {b["label"] for b in br["branches"]} == {"erase-P-first", "erase-Q-first"}
    # frames carry from_state_id + branch_id (base frame: None/None)
    base = body["frames"][0]
    assert base["from_state_id"] is None and base["branch_id"] is None
    for f in body["frames"][1:]:
        assert f["from_state_id"] is not None
        assert f["branch_id"] in {"erase-P-first", "erase-Q-first"}
    # the diamond: the convergence state belongs to both branches
    conv = br["convergence_state_ids"]
    assert len(conv) == 1
    assert br["membership"][conv[0]] == [0, 1]
    # the fork's continuations name the forward labels
    fork = br["fork_state_ids"][0]
    labels = [c["label"] for c in br["continuations"][fork]]
    assert set(labels) == {"erase-P-first", "erase-Q-first"}


def test_step_diff_baseline_is_the_steps_own_parent(client):
    """On a branching chain each step's diff compares against its OWN
    from-state — never the previous authored frame (the other line's leaf)."""
    body = client.get("/organon/uods/branching_confluence/chain").json()["data"]
    # every step frame changes exactly one thing in this diamond (one ERA per
    # step); a wrong baseline (other branch's leaf) would show a compound diff
    for f in body["frames"][1:]:
        assert f["diff"]["summary"].startswith("−1"), (
            f["state_id"], f["diff"]["summary"])


def test_linear_chain_branches_block_is_degenerate_and_additive(client):
    lin = client.get("/organon/uods/barbara/chain").json()["data"]
    br = lin["branches"]
    assert br["branching"] is False and br["count"] == 1
    assert br["branches"][0]["label"] == "main"
    assert br["fork_state_ids"] == [] and br["convergence_state_ids"] == []
    # additivity: the pre-existing keys are all still present
    for key in ("uod_id", "has_chain", "step_count", "branching",
                "chain_annotations", "uod_annotations", "frames"):
        assert key in lin
    for key in ("index", "kind", "rule", "annotation", "step_id", "state_id",
                "diff", "annotations", "svg", "egi_summary", "linear_forms",
                "introspection"):
        assert key in lin["frames"][0]


def test_history_structure_carries_the_branches_block(client):
    body = client.get(
        "/organon/uods/branching_confluence/history-structure").json()["data"]
    assert body["branches"]["count"] == 2
    assert {b["label"] for b in body["branches"]["branches"]} == {
        "erase-P-first", "erase-Q-first"}


def test_modal_worlds_carry_their_branch_labels(client):
    """The modal lens's worlds are not an anonymous set: each world names the
    line(s) of development it lies on (charter P1 for the lens whose subject
    IS the branching)."""
    body = client.get(
        "/organon/uods/branching_confluence/modal?thumbs=false").json()["data"]
    assert body["branches_total"] == 2
    by_id = {w["id"]: w for w in body["worlds"]}
    # the root and the converged state lie on both lines; the middles on one
    labels = {tuple(sorted(w["branches"])) for w in body["worlds"]}
    assert ("erase-P-first", "erase-Q-first") in labels     # shared states
    assert any(len(w["branches"]) == 1 for w in body["worlds"])  # exclusive middles
