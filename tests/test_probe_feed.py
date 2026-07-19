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


class _EmptyFeed(ProbeDirectedFeedBase):
    """No wants at all — isolates the model-delta counters (docket item 11,
    charge 4) from choosing/executing."""
    def _seed(self, round_idx):
        pass
    def _refill(self, round_idx):
        pass
    def _execute(self, want):
        return None


def test_decayed_atom_counts_removed_never_added():
    """Docket item 11, charge 4: under ttl decay atoms enter AND leave each
    segment, but only standing totals were visible. The feed now splits the
    symmetric diff: an atom that left M since the last observation counts in
    ``removed`` (never ``added``), an entrant in ``added``."""
    feed = _VoicelessFeed(AttentionEconomy())
    m_both = parse_egif('(alpha "1") (beta "2")')
    m_decayed = parse_egif('(alpha "1")')            # b fell to decay
    m_entrant = parse_egif('(alpha "1") (gamma "3")')    # c entered
    feed.propose(m_both, 1)
    assert (feed.added, feed.removed) == (0, 0)  # no previous signature yet
    feed.propose(m_decayed, 2)
    assert (feed.added, feed.removed) == (0, 1)  # decayed: removed, not added
    feed.propose(m_entrant, 3)
    assert (feed.added, feed.removed) == (1, 1)


def test_counters_move_even_when_nothing_was_chosen():
    # Decay is the loop's act, not the feed's: the counters must not depend
    # on a want having been chosen that round.
    feed = _EmptyFeed(AttentionEconomy())
    feed.propose(parse_egif('(alpha "1") (beta "2")'), 1)
    feed.propose(parse_egif('(alpha "1")'), 2)
    assert (feed.added, feed.removed) == (0, 1)
