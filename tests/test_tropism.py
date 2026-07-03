"""Tests for the tropism module (§13, affirmed 2026-07-02) — the warm-set re-poll: the first
*directed re-engagement*, mandated by runs 1–2 (neither passive membrane ever revisits, so
mechanism durability was vacuous twice). Deterministic and offline.

The two headlines mirror the priors the run-3 kit is built to test:
  * P1″ — the revisit works: a warm re-reach re-delivers a held fact and the round reads as
    non-revising (the habit holding) — the structural fraction runs 1–2 measured at zero;
  * P2″ — durability, finally populated: a deprecation arriving on a warm re-reach *meets its
    standing target* and the panel retracts it — the P2 event no passive source supplied.
"""

import pytest

from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from agon_evolution import (
    Agonothetes, ChallengerAgent, ContradictionAgent, GeneralizerAgent, ObserverAgent,
    UsageLedger,
)
from live_runner import LiveRunConfig, LiveRunner, ReplaySource
from tropism import WarmSetTropism, reverse_labels
from wiki_dispute_membrane import WikiDisputeFeed
from wikidata_source import RotatingWikidataSource, WikidataStatement as WS


def _wikidata_panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


# --------------------------------------------------------------------------- #
# Reversing the label cache                                                    #
# --------------------------------------------------------------------------- #

def test_reverse_labels_maps_unique_labels_back_to_ids():
    label_to_id, ambiguous = reverse_labels({"Q1": "Adam", "Q2": "Eve"})
    assert label_to_id == {"Adam": "Q1", "Eve": "Q2"}
    assert ambiguous == {}


def test_reverse_labels_normalizes_like_the_scribed_facts():
    # M carries labels through _const (quotes stripped, control chars → spaces) — the reversal
    # must meet the fact where it stands, not where the raw cache label was
    label_to_id, _ = reverse_labels({"Q3": 'Weird "Name"\twith\ttabs'})
    assert label_to_id == {"Weird Name with tabs": "Q3"}


def test_reverse_labels_splits_out_ambiguity_never_resolves_it():
    label_to_id, ambiguous = reverse_labels({"Q1": "Cambridge", "Q2": "Cambridge",
                                             "Q3": "London"})
    assert label_to_id == {"London": "Q3"}
    assert ambiguous == {"Cambridge": ["Q1", "Q2"]}


# --------------------------------------------------------------------------- #
# The warm set — reaches()                                                     #
# --------------------------------------------------------------------------- #

def test_reaches_emits_the_entities_backing_standing_facts():
    tropism = WarmSetTropism({"Q1": "Adam", "Q2": "Eve"}, k=4)
    m = '(place_of_birth "Adam" "Cambridge") (occupation "Eve" "gardener")'
    assert sorted(tropism.reaches(m, None)) == ["Q1", "Q2"]
    assert tropism.emitted == 2


def test_reaches_orders_decay_adjacent_first():
    # the fact whose relation was used LONGEST ago is nearest its ttl — re-check it first,
    # while the target still stands
    tropism = WarmSetTropism({"Q10": "swan1", "Q20": "adam"}, k=4)
    ledger = UsageLedger(ttl=8)
    ledger.touch({"color"}, 1)
    ledger.touch({"name"}, 5)
    m = '(name "adam" "Adam Smith") (color "swan1" "white")'
    assert tropism.reaches(m, ledger) == ["Q10", "Q20"]     # color (1) before name (5)
    ledger.touch({"color"}, 9)                              # now name is decay-adjacent
    assert tropism.reaches(m, ledger) == ["Q20", "Q10"]


def test_reaches_k_bounds_the_warm_slots():
    tropism = WarmSetTropism({"Q1": "a", "Q2": "b", "Q3": "c"}, k=2)
    m = '(holds "a" "x") (holds "b" "y") (holds "c" "z")'
    assert len(tropism.reaches(m, None)) == 2
    assert tropism.reaches("", None) == []                  # blank sheet → nothing to re-check
    assert tropism.reaches(m, None, k=0) == []


def test_reaches_an_unresolved_id_is_already_an_id():
    # legibility failed at ingestion (the item stayed "Q99") — the warm set still finds it
    tropism = WarmSetTropism({}, k=4)
    assert tropism.reaches('(instance_of "Q99" "human")', None) == ["Q99"]


def test_reaches_skips_and_counts_ambiguous_labels():
    # §13 decision 5 (affirmed): skip + count for run 3 — the ambiguity rate is itself worth
    # measuring before spending polls on it
    tropism = WarmSetTropism({"Q1": "Cambridge", "Q2": "Cambridge"}, k=4)
    assert tropism.reaches('(country "Cambridge" "England")', None) == []
    assert tropism.ambiguous_skipped == 1


def test_reaches_skips_and_counts_irreversible_labels():
    tropism = WarmSetTropism({}, k=4)
    assert tropism.reaches('(mortal "socrates" "yes")', None) == []
    assert tropism.unmapped_skipped == 1


def test_reaches_reads_standing_facts_only_not_laws():
    # a law is a habit too, but it has no entity to re-fetch — only sheet-level ground facts
    # name re-reachable entities; generic (law) vertices are skipped
    tropism = WarmSetTropism({"Q10": "swan1"}, k=4)
    m = '(color "swan1" "white") ~[ (swan *x) ~[ (white x) ] ]'
    assert tropism.reaches(m, None) == ["Q10"]


# --------------------------------------------------------------------------- #
# The source seam — inject()                                                   #
# --------------------------------------------------------------------------- #

def _world_fixture(world):
    def fetch_ids(ids):
        return [world[i] for i in ids if i in world]
    return fetch_ids


def test_inject_bypasses_seen_and_goes_front_of_queue(tmp_path):
    world = {"Q1": WS("Q1", "P19", "Cambridge"), "Q2": WS("Q2", "P19", "London")}
    labels = {"Q1": "Adam", "Q2": "Eve", "P19": "place of birth"}
    src = RotatingWikidataSource(
        ["Q1", "Q2"], chunk_size=1, crawl=False, fetch_ids=_world_fixture(world),
        label_fetch=lambda ids: {i: labels[i] for i in ids if i in labels})
    src.fetch()                                             # consumes Q1 → Q1 ∈ _seen
    src.inject(["Q1"])                                      # a deliberate re-reach, not a dupe
    batch = src.fetch()                                     # front-of-queue: Q1 again, not Q2
    assert batch[0].claim_egif == '(place_of_birth "Adam" "Cambridge")'
    assert src.injected == 1
    assert not src.exhausted()                              # Q2 still pending behind the warm id


def test_inject_skips_pending_ids_and_non_entities():
    world = {"Q1": WS("Q1", "P19", "Cambridge"), "Q2": WS("Q2", "P19", "London")}
    src = RotatingWikidataSource(["Q1", "Q2"], chunk_size=1, crawl=False,
                                 fetch_ids=_world_fixture(world), label_fetch=lambda ids: {})
    src.inject(["Q2", "Q2", "P19", "banana"])   # Q2 already pending; P19/banana not entities
    assert src.injected == 0
    src.fetch()
    assert src.injected == 0


def test_inject_counter_survives_the_state_round_trip(tmp_path):
    world = {"Q1": WS("Q1", "P19", "Cambridge")}
    kwargs = dict(chunk_size=1, crawl=False, fetch_ids=_world_fixture(world),
                  label_fetch=lambda ids: {})
    src = RotatingWikidataSource(["Q1"], **kwargs)
    src.fetch()
    src.inject(["Q1"])
    src.save_state(str(tmp_path / "frontier.json"))
    resumed = RotatingWikidataSource.load_state(str(tmp_path / "frontier.json"), **kwargs)
    assert resumed.injected == 1
    assert resumed.fetch()                                  # the injected re-reach survived too


def test_known_labels_exposes_a_copy_of_the_cache():
    labels = {"Q1": "Adam", "P19": "place of birth"}
    src = RotatingWikidataSource(["Q1"], fetch_ids=_world_fixture(
        {"Q1": WS("Q1", "P19", "Cambridge")}),
        label_fetch=lambda ids: {i: labels[i] for i in ids if i in labels})
    src.fetch()
    known = src.known_labels()
    assert known == {"Q1": "Adam", "P19": "place of birth"}
    known["Q1"] = "corrupted"                               # a copy — the cache stays private
    assert src.known_labels()["Q1"] == "Adam"


# --------------------------------------------------------------------------- #
# The runner — one consult per poll boundary                                   #
# --------------------------------------------------------------------------- #

def test_runner_refuses_a_tropism_without_the_seam():
    with pytest.raises(ValueError, match="inject"):
        LiveRunner("", ReplaySource([]), WikiDisputeFeed,
                   LiveRunConfig(ttl=None, checkpoint=False),
                   tropism=WarmSetTropism({}, k=1), clock=lambda: 0.0)


def test_runner_consults_the_tropism_before_each_fetch():
    order = []

    class StubSource:
        def __init__(self):
            self._polls = 0
        def inject(self, ids):
            order.append(("inject", list(ids)))
        def fetch(self):
            order.append(("fetch",))
            self._polls += 1
            return [WS("Q1", "P19", "Cambridge")] if self._polls == 1 else []
        def exhausted(self):
            return self._polls >= 2

    class StubTropism:
        def reaches(self, model_egif, ledger):
            order.append(("reaches", model_egif))
            return ["Q9"] if model_egif else []

    def feed(items):
        from wikidata_source import statements_to_disputes
        return WikiDisputeFeed(statements_to_disputes(items))

    runner = LiveRunner("", StubSource(), feed,
                        LiveRunConfig(ttl=None, checkpoint=False),
                        panel=_wikidata_panel(), tropism=StubTropism(), clock=lambda: 0.0)
    runner.run()
    # every poll boundary: reaches (player state read) then fetch; an empty warm set (blank M)
    # injects nothing, a populated one injects before the fetch it feeds
    assert order[0] == ("reaches", "")
    assert order[1] == ("fetch",)
    assert order[2][0] == "reaches" and "p19" in order[2][1]   # M read at the boundary
    assert order[3] == ("inject", ["Q9"])
    assert order[4] == ("fetch",)


# --------------------------------------------------------------------------- #
# Headlines — the priors, mechanically, offline                                #
# --------------------------------------------------------------------------- #

def test_warm_repoll_re_delivers_a_held_fact_as_a_non_revising_round():
    """P1″ offline: with the tropism on, a poll's chunk mixes warm + fresh — the warm
    re-delivery is a non-revising round (the habit holding), the structural fraction runs 1–2
    measured at zero."""
    world = {"Q1": WS("Q1", "P19", "Cambridge"), "Q2": WS("Q2", "P19", "Paris"),
             "Q3": WS("Q3", "P19", "Berlin")}
    labels = {"Q1": "Adam", "Q2": "Eve", "Q3": "Cain", "P19": "place of birth"}
    src = RotatingWikidataSource(
        ["Q1", "Q2", "Q3"], chunk_size=2, crawl=False, fetch_ids=_world_fixture(world),
        label_fetch=lambda ids: {i: labels[i] for i in ids if i in labels})
    tropism = WarmSetTropism(src.known_labels, k=1)   # warm_fraction 0.5 of chunk 2
    runner = LiveRunner("", src, WikiDisputeFeed,
                        LiveRunConfig(ttl=None, checkpoint=False, max_rounds=4),
                        panel=_wikidata_panel(), tropism=tropism, clock=lambda: 0.0)
    res = runner.run()
    assert res.segments[0].dispositions == {"new_fact": 2}          # Q1, Q2 — the habits form
    # poll 2's chunk = 1 warm (Q1 re-delivered → non-revising) + 1 fresh (Q3 → new_fact)
    assert res.segments[1].rounds == 2
    assert res.segments[1].dispositions == {"new_fact": 1}
    assert src.injected == 1 and tropism.emitted == 1


def test_deprecation_on_warm_repoll_meets_its_standing_target():
    """P2″ offline — THE P2 EVENT: runs 1–2 never revisited, so a deprecation never met a
    standing target. The tropism re-reaches the entity M holds; the world has since deprecated
    the bare value and referenced a replacement; the existing panel retracts and admits — no
    new referee, no disposition change."""
    calls = []

    def fetch_ids(ids):
        # the wiki-world moves BETWEEN polls: the first reach finds the bare value; by the
        # warm re-reach it has been deprecated and a referenced replacement has landed —
        # only a revisit will ever see it
        calls.append(list(ids))
        if len(calls) == 1:
            return [WS("Q1", "P19", "Cambridge", "normal", referenced=False)]
        return [WS("Q1", "P19", "Cambridge", "deprecated", referenced=False),
                WS("Q1", "P19", "London", "normal", referenced=True)]

    labels = {"Q1": "Adam", "P19": "place of birth"}
    src = RotatingWikidataSource(
        ["Q1"], chunk_size=1, crawl=False, fetch_ids=fetch_ids,
        label_fetch=lambda ids: {i: labels[i] for i in ids if i in labels})
    tropism = WarmSetTropism(src.known_labels, k=1)
    runner = LiveRunner("", src, WikiDisputeFeed,
                        LiveRunConfig(ttl=None, checkpoint=False, max_rounds=3),
                        panel=_wikidata_panel(), tropism=tropism, clock=lambda: 0.0)
    res = runner.run()
    assert calls == [["Q1"], ["Q1"]]                                # the revisit happened
    assert res.segments[0].dispositions == {"new_fact": 1}          # the habit forms
    assert res.segments[1].dispositions.get("retract_fact") == 1    # …and meets its denial
    assert res.segments[1].dispositions.get("new_fact") == 1
    assert same_graph(parse_egif(res.final_model_egif),
                      parse_egif('(place_of_birth "Adam" "London")'))
    assert src.injected == 1 and tropism.emitted == 1


# --------------------------------------------------------------------------- #
# Stream + tropism — the run-4 seam (§14): revisit × world-motion              #
# --------------------------------------------------------------------------- #

from wikidata_source import RecentChangesSource


def _rc_payload(*title_ts):
    return {"query": {"recentchanges": [
        {"title": t, "timestamp": ts} for t, ts in title_ts]}}


def test_stream_inject_rides_the_front_of_the_next_chunk():
    calls = []

    def fetch_ids(ids):
        calls.append(list(ids))
        return [WS(i, "P19", "x") for i in ids]

    src = RecentChangesSource(ids_per_poll=2,
                              fetch_changes=lambda since: _rc_payload(("Q8", "T1"), ("Q9", "T1")),
                              fetch_ids=fetch_ids, label_fetch=lambda ids: {})
    src.inject(["Q1"])
    src.fetch()
    assert calls == [["Q1", "Q8"]]        # warm first, the stream fills the remainder
    assert src.injected == 1


def test_stream_quiet_tick_still_serves_the_warm_set():
    # the F2″ composition half the stream can't do alone: while the world is idle the
    # tropism keeps its targets standing — a quiet tick is a warm re-reach, not a skip
    calls = []

    def fetch_ids(ids):
        calls.append(list(ids))
        return [WS(i, "P19", "x") for i in ids]

    src = RecentChangesSource(fetch_changes=lambda since: {"query": {}},
                              fetch_ids=fetch_ids, label_fetch=lambda ids: {})
    src.inject(["Q1"])
    assert src.fetch() != []
    assert calls == [["Q1"]]


def test_stream_warm_pending_survives_the_state_round_trip(tmp_path):
    src = RecentChangesSource(fetch_changes=lambda since: {"query": {}},
                              fetch_ids=lambda ids: [], label_fetch=lambda ids: {})
    src.inject(["Q1", "Q2"])
    src.save_state(str(tmp_path / "stream.json"))
    calls = []

    def fetch_ids(ids):
        calls.append(list(ids))
        return [WS(i, "P19", "x") for i in ids]

    resumed = RecentChangesSource.load_state(
        str(tmp_path / "stream.json"), fetch_changes=lambda since: {"query": {}},
        fetch_ids=fetch_ids, label_fetch=lambda ids: {})
    assert resumed.injected == 2
    resumed.fetch()
    assert calls == [["Q1", "Q2"]]        # a persisted warm re-reach survives the resume


def test_stream_plus_tropism_composition_delivers_the_p2_event():
    """THE RUN-4 HEADLINE, offline: the stream supplies world-motion (the value changes
    rank between visits), the tropism supplies the revisit (the stream has moved on) —
    composed, a deprecation meets its STANDING target and the panel retracts it. Neither
    half suffices alone: run 2's stream never revisited on its own once the edit scrolled
    past; run 3's crawl revisited a world that hadn't moved."""
    calls = []

    def fetch_ids(ids):
        calls.append(list(ids))
        if len(calls) == 1:
            return [WS("Q1", "P19", "Cambridge", "normal", referenced=False)]
        return [WS("Q1", "P19", "Cambridge", "deprecated", referenced=False),
                WS("Q1", "P19", "London", "normal", referenced=True)]

    # the stream mentions Q1 once (the edit scrolls past), then goes quiet — only the
    # tropism's warm re-reach revisits it after the world has moved
    ticks = []

    def fetch_changes(since):
        ticks.append(since)
        return _rc_payload(("Q1", "T1")) if len(ticks) == 1 else {"query": {}}

    labels = {"Q1": "Adam", "P19": "place of birth"}
    src = RecentChangesSource(ids_per_poll=1, fetch_changes=fetch_changes,
                              fetch_ids=fetch_ids,
                              label_fetch=lambda ids: {i: labels[i] for i in ids if i in labels})
    tropism = WarmSetTropism(src.known_labels, k=1)
    runner = LiveRunner("", src, WikiDisputeFeed,
                        LiveRunConfig(ttl=None, checkpoint=False, max_rounds=3),
                        panel=_wikidata_panel(), tropism=tropism, clock=lambda: 0.0)
    res = runner.run()
    assert calls == [["Q1"], ["Q1"]]                                # the revisit happened
    assert res.segments[0].dispositions == {"new_fact": 1}          # the habit forms
    assert res.segments[1].dispositions.get("retract_fact") == 1    # …and meets its denial
    assert res.segments[1].dispositions.get("new_fact") == 1
    assert same_graph(parse_egif(res.final_model_egif),
                      parse_egif('(place_of_birth "Adam" "London")'))
    assert src.injected == 1 and tropism.emitted == 1
