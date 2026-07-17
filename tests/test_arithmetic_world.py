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


class TestFeed:
    def _feed(self, **kw):
        from attention_economy import AttentionEconomy
        from arithmetic_world import ArithmeticWorld, ProbeDirectedFeed
        w = ArithmeticWorld()
        e = AttentionEconomy()
        return ProbeDirectedFeed(w, e, **kw), w, e

    def test_one_egif_per_propose_and_probes_settle(self):
        from egif_parser_dau import parse_egif
        feed, w, e = self._feed()
        m = parse_egif('(even "0")')
        out = feed.propose(m, 1)
        assert isinstance(out, str) and out.strip()
        parse_egif(out)   # every emission is legal EGIF

    def test_hunt_wants_cover_all_fermat_instances_up_front(self):
        from arithmetic_world import FERMATS
        from egif_parser_dau import parse_egif
        feed, w, e = self._feed()
        feed.propose(parse_egif('(even "0")'), 1)
        hunts = [wt for wt in e.wants() if wt.kind == "hunt"]
        covered = {wt.key[2] for wt in hunts} | {n for n in w.probed if n in FERMATS}
        assert covered >= set(FERMATS)

    def test_yield_read_from_model_delta(self):
        from egif_parser_dau import parse_egif
        feed, w, e = self._feed()
        m0 = parse_egif('(even "0")')
        feed.propose(m0, 1)
        # the model grew between calls — the feed must credit yield to last round's kinds
        m1 = parse_egif('(even "0") (odd "1") (prime "2")')
        feed.propose(m1, 2)
        assert any(v > 0 for v in e.snapshot()["kinds"].values())

    def test_journal_records_choices_and_is_deterministic(self):
        from egif_parser_dau import parse_egif
        def drive():
            feed, w, e = self._feed()
            m = parse_egif('(even "0")')
            for r in range(1, 6):
                feed.propose(m, r)
            return [j["chosen"] for j in feed.journal]
        assert drive() == drive()

    def test_fifo_and_scatter_choosers_are_deterministic_and_differ(self):
        from arithmetic_world import fifo_chooser, scatter_chooser
        from attention_economy import AttentionEconomy, Want
        e = AttentionEconomy()
        for i in range(12):
            e.register(Want(kind="k", key=(i,), created_round=i))
        f1 = [w.key for w in fifo_chooser(e, 5, 1)]
        s1 = [w.key for w in scatter_chooser(e, 5, 1)]
        assert f1 == [(0,), (1,), (2,), (3,), (4,)]
        assert s1 != f1
        # golden: pinned from the sha1 digest formula — a revert to salted hash() fails this across processes
        assert s1 == [(11,), (1,), (2,), (4,), (8,)]

    def test_extend_window_stays_bounded(self):
        from egif_parser_dau import parse_egif
        feed, w, e = self._feed()
        m = parse_egif('(even "0")')
        for r in range(1, 12):
            feed.propose(m, r)
            outstanding = sum(1 for wt in e.wants() if wt.kind == "extend")
            assert outstanding <= 3, f"extend wants unbounded: {outstanding} at round {r}"

    def test_propose_terminates_when_economy_at_cap(self):
        from egif_parser_dau import parse_egif
        from attention_economy import AttentionEconomy
        from arithmetic_world import ArithmeticWorld, ProbeDirectedFeed
        e = AttentionEconomy(max_wants=60)   # smaller than the feed's own seeds
        feed = ProbeDirectedFeed(ArithmeticWorld(), e)
        out = feed.propose(parse_egif('(even "0")'), 1)   # must return, not hang
        assert out is None or isinstance(out, str)
        assert e.dropped > 0                 # the refused registrations were counted
