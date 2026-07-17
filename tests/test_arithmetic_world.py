"""Rung 1 world #1 — deterministic computed arithmetic (spec: docs/superpowers/specs/
2026-07-17-rung1-attention-economy-design.md). The headline: Fermat's 1640 conjecture,
refuted at F5 = 641 * 6700417 (Euler 1732)."""
from arithmetic_world import (
    ArithmeticWorld, FERMATS, FERMAT_LAW, MUSEMENT_LAW,
)


class TestWorld:
    def test_f5_is_composite_and_earlier_fermats_prime(self):
        w = ArithmeticWorld()
        assert [w.is_prime(f) for f in FERMATS] == [True, True, True, True, True, False]

    def test_atoms_for_carries_parity_prime_square_fermat(self):
        w = ArithmeticWorld()
        a4 = w.atoms_for(4)
        assert '(even "4")' in a4 and '(square "4")' in a4 and "(prime" not in a4
        a17 = w.atoms_for(17)
        assert '(odd "17")' in a17 and '(prime "17")' in a17 and '(fermat_number "17")' in a17

    def test_f5_atoms_deny_primality_under_the_standing_law(self):
        w = ArithmeticWorld()
        a = w.atoms_for(4294967297)
        assert '(fermat_number "4294967297")' in a
        assert '~[ (prime "4294967297") ]' in a   # the world's denial — the refuting instance

    def test_coin_is_deterministic_and_mixed(self):
        w = ArithmeticWorld()
        bits = [w.coin(n) for n in range(40)]
        assert bits == [w.coin(n) for n in range(40)]
        assert True in bits and False in bits

    def test_probe_cost_grows_with_n(self):
        w = ArithmeticWorld()
        assert w.probe_cost(7) < w.probe_cost(65537) < w.probe_cost(4294967297)

    def test_law_instance_verdicts(self):
        w = ArithmeticWorld()
        assert w.test_law_instance(FERMAT_LAW, 257) is True
        assert w.test_law_instance(FERMAT_LAW, 4294967297) is False
        assert w.test_law_instance(FERMAT_LAW, 10) is None          # vacuous — not a Fermat number
        assert w.test_law_instance(MUSEMENT_LAW, 65537) is True

    def test_range_cap_counts_drops(self):
        w = ArithmeticWorld(range_cap=5)
        for n in range(5):
            assert w.atoms_for(n)
        w.atoms_for(6)          # over the cap for a *new* n
        assert w.dropped == 1
        assert w.atoms_for(4294967297)   # Fermat numbers are exempt (law instances)
