"""Tests for the first open membrane (``discourse_membrane``) — §4b of the automated
Endoporeutic Game. Offline and deterministic: a replayable, sourced, dated feed drives the
mechanical loop, and the raise-only referee reports cross-source conflict (not truth)."""

from discourse_membrane import (
    Conflict, DiscourseFeed, DiscourseItem, consistency_report, contested_contents,
)
from agon_evolution import run


def _feed():
    return DiscourseFeed([
        DiscourseItem("mon", "alice", '(hosts "Bayside" "Market")'),
        DiscourseItem("mon", "bob", '(hosts "Bayside" "Market")', deny=True),
        DiscourseItem("tue", "carol", '(ferry "Bayside" "Cove")'),
    ])


# --------------------------------------------------------------------------- #
# The feed as a Proposer                                                        #
# --------------------------------------------------------------------------- #

def test_feed_emits_content_in_order_wrapping_denials():
    feed = _feed()
    assert feed.propose(None, 1) == '(hosts "Bayside" "Market")'
    assert feed.propose(None, 2) == '~[ (hosts "Bayside" "Market") ]'   # a denial → a cut
    assert feed.propose(None, 3) == '(ferry "Bayside" "Cove")'
    assert feed.days == ["mon", "tue"]                                  # day = generation


def test_feed_exhaustion_returns_none():
    feed = DiscourseFeed([DiscourseItem("mon", "a", "(p)")])
    assert feed.propose(None, 1) == "(p)"
    assert feed.propose(None, 2) is None                               # ends the run cleanly


def test_feed_drives_the_loop_into_a_diachronic_uod():
    feed = _feed()
    res = run("", feed, rounds=5, uod_id="disc", name="discourse")   # rounds > items
    assert len(res.outcomes) == 3                                      # stops when exhausted
    assert [i.source for i in feed.emitted] == ["alice", "bob", "carol"]
    assert res.outcomes[0].disposition == "new_fact"                  # alice's fact admitted


# --------------------------------------------------------------------------- #
# The raise-only referee: cross-source consistency                             #
# --------------------------------------------------------------------------- #

def test_consistency_report_flags_cross_source_conflict():
    conflicts = consistency_report([
        DiscourseItem("mon", "alice", '(hosts "Bayside" "Market")'),
        DiscourseItem("mon", "bob", '(hosts "Bayside" "Market")', deny=True),
    ])
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.asserted_by == ["alice"] and c.denied_by == ["bob"]


def test_no_conflict_when_sources_agree():
    items = [
        DiscourseItem("mon", "alice", '(hosts "Bayside" "Market")'),
        DiscourseItem("tue", "carol", '(hosts "Bayside" "Market")'),   # both assert
    ]
    assert consistency_report(items) == []
    assert contested_contents(items) == set()


def test_contested_contents_names_the_disputed_proposition():
    items = [
        DiscourseItem("mon", "alice", '(hosts "Bayside" "Market")'),
        DiscourseItem("mon", "bob", '(hosts "Bayside" "Market")', deny=True),
        DiscourseItem("tue", "carol", '(ferry "Bayside" "Cove")'),     # uncontested
    ]
    assert contested_contents(items) == {'(hosts "Bayside" "Market")'}
