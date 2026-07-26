"""AC1 — the peel surfaces structured UNKNOWN atoms (the producer)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain_oracle import CorpusOracle
from egif_parser_dau import parse_egif
from m_steps import peel_step
from proof_authoring import ProofChain
from semantic_game import evaluate
from world_scroll import wrap_m

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M0 = f'(swan "Ciel") (white "Ciel") {LAW}'


def _oracle(m_egif=M0):
    from model_materialization import materialize_egi
    m, _ = materialize_egi(parse_egif(m_egif))
    return CorpusOracle([("M", m)])


class TestUnknownAtoms:
    def test_ground_unknown_collected(self):
        r = evaluate(parse_egif('(swan "Dover")'), _oracle())
        assert r.verdict.value == "unknown"
        assert r.unknown_atoms == (("swan", ("Dover",)),)

    def test_true_verdict_collects_nothing(self):
        r = evaluate(parse_egif('(swan "Ciel")'), _oracle())
        assert r.verdict.value == "true"
        assert r.unknown_atoms == ()

    def test_existential_unknown_has_generic_slot(self):
        r = evaluate(parse_egif('(black *x)'), _oracle())
        assert r.verdict.value == "unknown"
        assert ("black", (None,)) in r.unknown_atoms

    def test_ground_unknown_inside_negation_collected(self):
        r = evaluate(parse_egif('~[ (swan "Dover") ~[ (white "Dover") ] ]'),
                     _oracle())
        assert ("swan", ("Dover",)) in r.unknown_atoms

    def test_deterministic_order(self):
        a = evaluate(parse_egif('(swan "Dover") (black "Dover")'), _oracle())
        b = evaluate(parse_egif('(swan "Dover") (black "Dover")'), _oracle())
        assert a.unknown_atoms == b.unknown_atoms
        assert list(a.unknown_atoms) == sorted(a.unknown_atoms, key=repr)


class TestPeelStepCarriesUnknowns:
    def test_params_carry_unknown_atoms(self):
        wrapped, _ = wrap_m(parse_egif(M0))
        pc = ProofChain(wrapped)
        peel_step(pc, '(swan "Dover") (black *x)')
        p = pc.to_chain().steps[-1].parameters
        assert ["swan", ["Dover"]] in p["unknown_atoms"]
        assert ["black", ["*"]] in p["unknown_atoms"]
