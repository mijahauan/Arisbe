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
