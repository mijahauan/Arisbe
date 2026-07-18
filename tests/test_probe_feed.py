# tests/test_probe_feed.py
"""The generic probe-feed base (vault-cycle Task 1): mechanics shared by every
world; count-or-refuse is the new contract (carried from the rung-1 review)."""
from attention_economy import AttentionEconomy, Want
from probe_feed import ProbeDirectedFeedBase
from egif_parser_dau import parse_egif


class _VoicelessFeed(ProbeDirectedFeedBase):
    """A feed whose only want cannot be voiced — must be refused and counted."""
    def _seed(self, round_idx):
        self._economy.register(Want(kind="mute", key=("m",), payload=None))
    def _refill(self, round_idx):
        pass
    def _execute(self, want):
        return None


def test_unvoiceable_want_is_refused_and_counted():
    feed = _VoicelessFeed(AttentionEconomy())
    out = feed.propose(parse_egif('(even "0")'), 1)
    assert out is None
    assert feed.refused == 1
    assert feed._economy.wants() == []   # settled, not respinning


def test_base_is_abstractless_and_deterministic():
    a = _VoicelessFeed(AttentionEconomy()); b = _VoicelessFeed(AttentionEconomy())
    m = parse_egif('(even "0")')
    assert [a.propose(m, r) for r in (1, 2)] == [b.propose(m, r) for r in (1, 2)]
