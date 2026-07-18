"""Rung 1 — the attention economy (spec: docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md)."""
from attention_economy import Want, AttentionEconomy


def _econ(**kw):
    return AttentionEconomy(**kw)


class TestScoring:
    def test_yield_per_cost_orders_kinds(self):
        e = _econ()
        a = Want(kind="rich", key=("a",))
        b = Want(kind="poor", key=("b",))
        e.register(a); e.register(b)
        # teach it: rich yielded 3 events on a probe, poor yielded 0
        e.observe(1, [(a, 3), (b, 0)])
        chosen = e.choose(1, round_idx=2)
        assert chosen[0].kind == "rich"

    def test_cost_divides_the_score(self):
        e = _econ()
        cheap = Want(kind="k", key=("cheap",), cost=1.0)
        dear = Want(kind="k", key=("dear",), cost=100.0)
        e.register(cheap); e.register(dear)
        # same kind (same Y): the cheap want must come first
        assert e.choose(2, round_idx=1)[0].key == ("cheap",)

    def test_severity_multiplies(self):
        e = _econ()
        plain = Want(kind="k", key=("plain",), cost=1.0, severity=1.0)
        severe = Want(kind="k", key=("severe",), cost=4.0, severity=8.0)
        e.register(plain); e.register(severe)
        # 8/4 = 2 > 1/1 — the law-testing want wins despite its cost
        assert e.choose(2, round_idx=1)[0].key == ("severe",)

    def test_tiebreak_fewest_attempts_then_oldest(self):
        e = _econ()
        old = Want(kind="k", key=("old",), created_round=1)
        new = Want(kind="k", key=("new",), created_round=5)
        tried = Want(kind="k", key=("tried",), created_round=0, attempts=3)
        e.register(new); e.register(tried); e.register(old)
        order = [w.key for w in e.choose(3, round_idx=6)]
        assert order.index(("old",)) < order.index(("new",))
        assert order.index(("new",)) < order.index(("tried",))

    def test_choose_increments_attempts_and_settle_removes(self):
        e = _econ()
        w = Want(kind="k", key=("w",))
        e.register(w)
        chosen = e.choose(1, round_idx=1)
        assert chosen[0].attempts == 1
        e.settle("k", ("w",))
        assert e.wants() == []

    def test_register_dedups_by_kind_key(self):
        e = _econ()
        assert e.register(Want(kind="k", key=("w",))) is True
        assert e.register(Want(kind="k", key=("w",))) is False
        assert len(e.wants()) == 1

    def test_deterministic_choice(self):
        def build():
            e = _econ()
            for i in range(20):
                e.register(Want(kind=f"k{i % 3}", key=(i,), cost=1.0 + i % 5))
            e.observe(1, [(Want(kind="k1", key=(99,)), 2)])
            return [w.key for w in e.choose(7, round_idx=2)]
        assert build() == build()


class TestGuards:
    def test_noisy_tv_kind_decays_below_productive(self):
        e = _econ()
        noise = Want(kind="coin", key=("n",))
        good = Want(kind="hunt", key=("g",))
        e.register(noise); e.register(good)
        for r in range(1, 8):
            e.observe(r, [(noise, 0), (good, 1)])
        assert e.kind_yield("coin") < e.kind_yield("hunt")
        assert e.choose(1, round_idx=9)[0].kind == "hunt"

    def test_attempt_decay_sinks_a_barren_want(self):
        e = _econ(attempt_decay=0.5)
        # barren outscores fresh on raw score (severity 2.0 vs 1.0), so absent
        # the attempt-decay term it MUST win; three barren attempts decay it
        # 2*0.05*0.5**3 = 0.0125 < fresh's 0.05 — only the decay term flips this.
        barren = Want(kind="k", key=("barren",), severity=2.0, attempts=3)
        fresh = Want(kind="k", key=("fresh",))
        e.register(barren); e.register(fresh)
        assert e.choose(1, round_idx=1)[0].key == ("fresh",)

    def test_register_cap_counts_drops(self):
        e = _econ(max_wants=2)
        assert e.register(Want(kind="k", key=(1,)))
        assert e.register(Want(kind="k", key=(2,)))
        assert e.register(Want(kind="k", key=(3,))) is False
        assert e.dropped == 1

    def test_musement_reservation_every_period_when_k_is_1(self):
        e = _econ(musement_fraction=0.1)
        e.register(Want(kind="musement", key=("m",), created_round=1))
        e.register(Want(kind="hunt", key=("h",)))
        e.observe(1, [(Want(kind="hunt", key=("h",)), 5)])  # hunt far outscores
        # round 10 is a musement round (period = 1/0.1); round 11 is not
        assert e.choose(1, round_idx=10)[0].kind == "musement"
        assert e.choose(1, round_idx=11)[0].kind == "hunt"

    def test_boredom_doubles_musement_and_yield_resets_it(self):
        e = _econ(musement_fraction=0.1, boredom_rounds=3)
        w = Want(kind="k", key=("w",))
        e.register(w)
        for r in range(3):
            e.observe(r, [(w, 0)])
        assert e.effective_musement() == 0.2
        e.observe(4, [(w, 2)])
        assert e.effective_musement() == 0.1

    def test_scoring_failure_degrades_to_mechanical_order(self):
        e = _econ()
        good = Want(kind="k", key=("good",), created_round=1)
        bad = Want(kind="k", key=("bad",), created_round=2, cost=1.0)
        e.register(good); e.register(bad)
        e._y = None  # sabotage internal state: scoring will raise
        chosen = e.choose(2, round_idx=3)
        assert [w.key for w in chosen] == [("good",), ("bad",)]  # mechanical order
        assert e.fallbacks == 1


class TestAdapters:
    def test_wants_from_docket_wraps_open_entries(self):
        from attention_economy import wants_from_docket
        from query_docket import QueryDocket
        d = QueryDocket(labels={}, k=2)
        d.note_unknowns([("orbits", ["Q1", "Q2"])])
        ws = wants_from_docket(d, round_idx=5)
        assert len(ws) == 1
        w = ws[0]
        assert w.kind == "docket"
        assert w.key == ("orbits", ("Q1", "Q2"))
        assert w.payload is d.open_entries[0]

    def test_wants_from_frontier_takes_unresolved_claims(self):
        from attention_economy import wants_from_frontier
        from agon_metalearning import DisputeEpisode
        eps = [
            DisputeEpisode(claim_egif='(hot "Sun")', mechanism="unresolved",
                           settled=None, reverts=3, disposition=None, stuck=None),
            DisputeEpisode(claim_egif='(cold "Pluto")', mechanism="reliable_source",
                           settled=True, reverts=0, disposition="new_fact", stuck=True),
        ]
        ws = wants_from_frontier(eps, round_idx=2)
        assert [w.key for w in ws] == [('(hot "Sun")',)]
        assert ws[0].kind == "frontier" and ws[0].severity == 4.0

    def test_wants_from_docket_backdates_age_and_carries_attempts(self):
        from attention_economy import wants_from_docket
        from query_docket import DocketEntry

        class FakeDocket:
            open_entries = [DocketEntry(
                shape="orbits", constants=("Q1",),
                provenance="unknown_in_peel", age=3, attempts=2)]

        ws = wants_from_docket(FakeDocket(), round_idx=5)
        assert ws[0].created_round == 2   # 5 - age 3: older doubts win ties
        assert ws[0].attempts == 2        # a barren docket want sinks here too


class TestHorizon:
    def test_register_dedups_and_counts_cap_drops(self):
        from attention_economy import Horizon, HorizonItem
        h = Horizon(max_items=2)
        assert h.register(HorizonItem("pdf", "a.pdf", 100, "binary", 1))
        assert h.register(HorizonItem("pdf", "a.pdf", 100, "binary", 1)) is False
        assert h.dropped == 0
        assert h.register(HorizonItem("img", "b.png", 5, "binary", 1))
        assert h.register(HorizonItem("img", "c.png", 5, "binary", 2)) is False
        assert h.dropped == 1

    def test_reattempt_is_oldest_first_and_counts_attempts(self):
        from attention_economy import Horizon, HorizonItem
        h = Horizon()
        h.register(HorizonItem("canvas", "new.canvas", 1, "drawn", 5))
        h.register(HorizonItem("pdf", "old.pdf", 1, "binary", 1))
        first = h.reattempt(round_idx=9, k=1)
        assert [i.ref for i in first] == ["old.pdf"]
        assert first[0].attempts == 1
        h.settle("old.pdf")
        assert [i.ref for i in h.open_items()] == ["new.canvas"]

    def test_snapshot_counts_by_kind_and_reason(self):
        from attention_economy import Horizon, HorizonItem
        h = Horizon()
        h.register(HorizonItem("date", "j:L12", 1, "malformed_date_line", 1))
        s = h.snapshot()
        assert s["by_reason"]["malformed_date_line"] == 1 and s["open"] == 1
