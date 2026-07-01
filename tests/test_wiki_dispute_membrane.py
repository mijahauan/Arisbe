"""Tests for the wiki-dispute membrane (``wiki_dispute_membrane``) + the dispute-learning layer
in ``agon_metalearning`` — §4b/§6 of the automated Endoporeutic Game. Offline, deterministic,
LLM-free. The headline: a **reliable source overturns a prior consensus**, and the meta-learning
learns which mechanism produces *durable* knowledge."""

from agon_evolution import run
from agon_metalearning import (
    edit_war_friction, mechanism_principles, unresolved_frontier,
)
from wiki_dispute_membrane import (
    Resolution, WikiDispute, WikiDisputeFeed, WikiEdit,
)

CONSENSUS_LAW = "~[ (author *x) ~[ (reliable x) ] ]"   # 'all authors reliable' — a consensus law
M0 = '(author "Xavier") (reliable "Xavier")'            # the law holds initially


def _disputes():
    return [
        WikiDispute(CONSENSUS_LAW,
                    [WikiEdit("alice", True), WikiEdit("bob", False), WikiEdit("alice", True)],
                    Resolution("consensus", True)),
        WikiDispute('(reliable "Yolanda")',
                    [WikiEdit("carol", True)],
                    Resolution("reliable_source", False),
                    world_egif='(author "Yolanda") ~[ (reliable "Yolanda") ]'),
        WikiDispute('(reliable "Zed")',
                    [WikiEdit("dan", True), WikiEdit("eve", False),
                     WikiEdit("dan", True), WikiEdit("eve", False)],
                    Resolution("unresolved", None),
                    world_egif='(reliable "Zed")'),
    ]


def _run():
    feed = WikiDisputeFeed(_disputes())
    res = run(M0, feed, rounds=3, uod_id="wiki", name="wiki disputes")
    return feed, res


# --------------------------------------------------------------------------- #
# The dispute record                                                           #
# --------------------------------------------------------------------------- #

def test_dispute_counts_reverts_and_editors():
    d = _disputes()[0]
    assert d.reverts == 1 and d.contested
    assert d.editors == ["alice", "bob"]
    assert _disputes()[2].reverts == 2                  # the fierce edit war


def test_ground_truth_by_resolution():
    settled = WikiDispute("(p)", [], Resolution("consensus", True))
    rejected = WikiDispute("(p)", [], Resolution("admin", False))
    assert settled.ground_truth() == "(p)"
    assert rejected.ground_truth() == "~[ (p) ]"


def test_feed_drives_the_loop_and_exhausts():
    feed = WikiDisputeFeed(_disputes())
    res = run(M0, feed, rounds=9, uod_id="w", name="w")  # rounds > disputes
    assert len(res.outcomes) == 3
    report = feed.dispute_report()
    assert [r.mechanism for r in report] == ["consensus", "reliable_source", "unresolved"]


# --------------------------------------------------------------------------- #
# The headline — a reliable source overturns a consensus                       #
# --------------------------------------------------------------------------- #

def test_reliable_source_overturns_consensus_generalization():
    feed, res = _run()
    dispositions = [o.disposition for o in res.outcomes]
    assert dispositions == ["generalization", "challenge_to_M", "new_fact"]
    eps = {e.mechanism: e for e in feed.episodes(res)}
    # the consensus law was admitted then relinquished; the reliable-source challenge stood
    assert eps["consensus"].stuck is False
    assert eps["reliable_source"].stuck is True


def test_mechanism_principles_learn_which_resolution_is_durable():
    feed, res = _run()
    principles = {p.mechanism: p for p in mechanism_principles(feed.episodes(res))}
    assert principles["reliable_source"].durable is True
    assert principles["reliable_source"].stick_rate == 1.0
    assert principles["consensus"].durable is False          # overturned → not durable
    assert principles["consensus"].stick_rate == 0.0
    assert principles["unresolved"].durable is False          # never durable, tentative posit


# --------------------------------------------------------------------------- #
# Friction + the honest horizon                                                #
# --------------------------------------------------------------------------- #

def test_edit_war_friction_ranks_the_fiercest_first():
    feed, res = _run()
    ranked = edit_war_friction(feed.episodes(res))
    assert ranked[0].claim_egif == '(reliable "Zed")'        # 2 reverts, unresolved
    assert ranked[0].reverts == 2


def test_unresolved_frontier_names_the_contested_claim():
    feed, res = _run()
    assert unresolved_frontier(feed.episodes(res)) == ['(reliable "Zed")']
