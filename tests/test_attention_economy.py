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
