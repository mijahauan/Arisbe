"""Tests for the first live source — Wikidata (``wikidata_source``) — with the atom-level
retraction and the mechanical ``ContradictionAgent`` that let a deprecated / reliably-sourced
statement overturn a bare one. Deterministic and offline (recorded statements; the real
``wbgetentities_fetch`` is never called in CI). The headline: a **reliable source overturns a
bare value, mechanically, with no LLM**."""

from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from agon_evolution import (
    Agonothetes, ChallengerAgent, ContradictionAgent, DeliberationContext,
    GeneralizerAgent, ObserverAgent, peel,
)
from live_runner import LiveRunConfig, LiveRunner
from model_revision import retract_atom
from wiki_dispute_membrane import WikiDisputeFeed
from wikidata_source import (
    LabelCache, RotatingWikidataSource, WikidataSource, WikidataStatement as WS,
    collect_ids, record_poll, replay_polls, resolve_labels,
    statement_egif, statements_to_disputes, unresolved_fraction,
)


# --------------------------------------------------------------------------- #
# Statement → EGIF / dispute mapping                                          #
# --------------------------------------------------------------------------- #

def test_statement_egif_is_egif_safe():
    s = WS("Q42", "place of birth", "Cambridge")
    assert statement_egif(s) == '(place_of_birth "Q42" "Cambridge")'
    assert parse_egif(statement_egif(s))               # parses


def test_statements_to_disputes_maps_rank_and_references():
    sts = [
        WS("Q42", "occupation", "author", "normal", referenced=True),
        WS("Q42", "occupation", "musician", "normal", referenced=False),
        WS("Q42", "height", "1.8m", "deprecated", referenced=False),
    ]
    d = {(x.claim_egif): x for x in statements_to_disputes(sts)}
    author = next(v for k, v in d.items() if "author" in k)
    musician = next(v for k, v in d.items() if "musician" in k)
    height = next(v for k, v in d.items() if "height" in k)
    assert author.resolution.mechanism == "reliable_source" and author.resolution.settled
    assert musician.resolution.mechanism == "consensus"
    assert height.resolution.settled is False           # deprecated → relinquished
    assert height.ground_truth().startswith("~[")       # scribed as a denial
    assert author.reverts == 1                           # two occupation values compete


# --------------------------------------------------------------------------- #
# P/Q id → label resolution (legibility; the pure half, offline)              #
# --------------------------------------------------------------------------- #

def test_collect_ids_finds_pq_ids_in_first_seen_order():
    sts = [
        WS("Q42", "P19", "Q350"),                 # item, property, entity value — all ids
        WS("Q42", "P569", "1952-03-11"),          # a time value is not an id
        WS("Douglas_Adams", "occupation", "author"),   # labels already — nothing to look up
    ]
    assert collect_ids(sts) == ["Q42", "P19", "Q350", "P569"]


def test_resolve_labels_substitutes_known_ids_and_keeps_unknown():
    sts = [WS("Q42", "P19", "Q350", "normal", referenced=True),
           WS("Q42", "P570", "Q84")]
    labels = {"Q42": "Douglas Adams", "P19": "place of birth", "Q350": "Cambridge",
              "Q84": "London"}                     # P570 has no label → stays an id (honest)
    out = resolve_labels(sts, labels)
    assert out[0].item == "Douglas Adams" and out[0].prop == "place of birth"
    assert out[0].value == "Cambridge" and out[0].referenced   # rank/provenance carried
    assert out[1].prop == "P570" and out[1].value == "London"
    # and the scribed fact is legible EGIF
    assert statement_egif(out[0]) == '(place_of_birth "Douglas Adams" "Cambridge")'
    assert parse_egif(statement_egif(out[1]))      # unresolved id still parses


def test_unresolved_fraction_is_the_legibility_tripwire():
    assert unresolved_fraction([WS("Douglas Adams", "place of birth", "Cambridge")]) == 0.0
    assert unresolved_fraction([WS("Q42", "place of birth", "Cambridge")]) == 1 / 3
    assert unresolved_fraction([WS("Q42", "P19", "Q350")]) == 1.0
    assert unresolved_fraction([]) == 0.0


def test_source_records_legibility_per_poll():
    src = WikidataSource([[WS("Q1", "prop", "a")], [WS("Item", "prop", "b")]])
    src.fetch()
    src.fetch()
    assert src.legibility == [1 / 3, 0.0]          # a spike = labels silently degrading


# --------------------------------------------------------------------------- #
# The live source                                                             #
# --------------------------------------------------------------------------- #

def test_source_yields_dispute_batches_then_exhausts():
    src = WikidataSource([[WS("Q1", "p", "a")], [WS("Q2", "p", "b")]])
    b1 = src.fetch()
    assert len(b1) == 1 and b1[0].claim_egif == '(p "Q1" "a")' and not src.exhausted()
    src.fetch()
    assert src.exhausted() and src.fetch() == []


def test_from_fetch_calls_the_injected_fetch_per_poll():
    calls = {"n": 0}
    def fetch():
        calls["n"] += 1
        return [WS("Q1", "p", f"v{calls['n']}")]
    src = WikidataSource.from_fetch(fetch, polls=3)
    assert calls["n"] == 3
    assert [src.fetch()[0].claim_egif for _ in range(3)] == [
        '(p "Q1" "v1")', '(p "Q1" "v2")', '(p "Q1" "v3")']


# --------------------------------------------------------------------------- #
# Atom-level retraction + the ContradictionAgent                              #
# --------------------------------------------------------------------------- #

def test_retract_atom_drops_only_the_matching_atom():
    m = parse_egif('(likes "a" "b") (likes "a" "c") (knows "a")')
    out = retract_atom(m, "likes", ["a", "b"])
    assert same_graph(out, parse_egif('(likes "a" "c") (knows "a")'))   # siblings survive


def test_contradiction_agent_retracts_a_denied_standing_fact():
    m = parse_egif('(place_of_birth "Q42" "Cambridge")')
    denial = '~[ (place_of_birth "Q42" "Cambridge") ]'
    ctx = DeliberationContext(m, denial, peel(m, denial), [])
    vote = ContradictionAgent().vote(ctx)
    assert vote is not None and vote.disposition == "retract_fact"
    assert vote.kwargs == {"relation": "place_of_birth", "labels": ["Q42", "Cambridge"]}


def test_contradiction_agent_abstains_when_nothing_stands_or_positive():
    m = parse_egif('(place_of_birth "Q42" "London")')
    # denies a fact not in M
    ctx = DeliberationContext(m, '~[ (place_of_birth "Q42" "Cambridge") ]',
                              peel(m, '~[ (place_of_birth "Q42" "Cambridge") ]'), [])
    assert ContradictionAgent().vote(ctx) is None
    # a positive proposal is not its business
    ctx2 = DeliberationContext(m, '(place_of_birth "Q42" "Cambridge")',
                               peel(m, '(place_of_birth "Q42" "Cambridge")'), [])
    assert ContradictionAgent().vote(ctx2) is None


# --------------------------------------------------------------------------- #
# End-to-end — a reliable source overturns a bare value, no LLM                #
# --------------------------------------------------------------------------- #

def _wikidata_panel():
    return Agonothetes([ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
                        ContradictionAgent()])


def test_deprecation_overturns_bare_value_end_to_end():
    polls = [
        [WS("Q42", "place of birth", "Cambridge", "normal", referenced=False)],
        [WS("Q42", "place of birth", "Cambridge", "deprecated", referenced=False),
         WS("Q42", "place of birth", "London", "normal", referenced=True)],
    ]
    runner = LiveRunner("", WikidataSource(polls), WikiDisputeFeed,
                        LiveRunConfig(ttl=None, checkpoint=False),
                        panel=_wikidata_panel(), clock=lambda: 0.0)
    res = runner.run()
    assert res.segments[0].dispositions == {"new_fact": 1}          # bare value admitted
    assert res.segments[1].dispositions.get("retract_fact") == 1    # then relinquished
    # the referenced value stands; the bare deprecated one is gone
    assert same_graph(parse_egif(res.final_model_egif),
                      parse_egif('(place_of_birth "Q42" "London")'))


# --------------------------------------------------------------------------- #
# The label cache — politeness across polls                                    #
# --------------------------------------------------------------------------- #

def test_label_cache_fetches_only_missing_and_negative_caches():
    asked = []

    def fake_fetch(ids):
        asked.append(list(ids))
        return {i: f"label:{i}" for i in ids if i != "Q404"}   # Q404 has no label

    cache = LabelCache(fake_fetch)
    got = cache.lookup(["Q42", "P19", "Q404", "not_an_id"])
    assert got == {"Q42": "label:Q42", "P19": "label:P19"}
    assert asked == [["Q42", "P19", "Q404"]]                   # non-ids never asked
    # a second lookup over the same ids (plus one new) asks ONLY for the new one —
    # including the labelless Q404 (negative-cached, not re-asked every poll)
    got2 = cache.lookup(["Q42", "Q404", "Q1"])
    assert got2 == {"Q42": "label:Q42", "Q1": "label:Q1"}
    assert asked[1] == ["Q1"]
    assert cache.fetched == 4


# --------------------------------------------------------------------------- #
# The poll record — offline replay (the determinism canary)                    #
# --------------------------------------------------------------------------- #

def test_record_and_replay_polls_round_trip(tmp_path):
    path = str(tmp_path / "polls.jsonl")
    poll1 = [WS("Douglas Adams", "place of birth", "Cambridge", "normal", True)]
    poll2 = [WS("Q1", "instance_of", "Q2", "deprecated", False)]
    record_poll(path, poll1)
    record_poll(path, poll2)
    polls = replay_polls(path)
    assert polls == [poll1, poll2]                             # fields + order intact
    # and the replayed record drives the SAME source shape the live run used
    src = WikidataSource(polls)
    assert src.fetch()[0].claim_egif == '(place_of_birth "Douglas Adams" "Cambridge")'
    assert src.fetch()[0].resolution.mechanism == "deprecated"


# --------------------------------------------------------------------------- #
# The rotating frontier — run 1's live source                                  #
# --------------------------------------------------------------------------- #

def _frontier_fixture(ids):
    """A tiny fake wiki: each entity has one statement; Q1's value names Q3 (the crawl edge)."""
    world = {
        "Q1": WS("Q1", "P19", "Q3"),                # entity-valued → crawlable
        "Q2": WS("Q2", "P569", "1952-03-11"),       # time value → not crawlable
        "Q3": WS("Q3", "P17", "somewhere"),
    }
    return [world[i] for i in ids if i in world]


def test_rotating_source_is_lazy_and_crawls_the_frontier(tmp_path):
    calls = []

    def fetch_ids(ids):
        calls.append(list(ids))
        return _frontier_fixture(ids)

    labels = {"Q1": "Adam", "Q2": "Eve", "Q3": "Cambridge", "P19": "place of birth",
              "P17": "country", "P569": "date of birth"}
    src = RotatingWikidataSource(
        ["Q1", "Q2"], chunk_size=2, fetch_ids=fetch_ids,
        record_path=str(tmp_path / "polls.jsonl"),
        label_fetch=lambda ids: {i: labels[i] for i in ids if i in labels})
    assert calls == []                                         # lazy: nothing at construction
    batch1 = src.fetch()
    assert calls == [["Q1", "Q2"]]
    # the crawl discovered Q3 (an entity-valued value) and enqueued it for the next poll
    assert not src.exhausted()
    batch2 = src.fetch()
    assert calls[1] == ["Q3"]
    assert src.exhausted()
    # labels resolved through the shared cache; the claims are legible
    assert any('(place_of_birth "Adam" "Cambridge")' == d.claim_egif for d in batch1)
    assert any('(country "Cambridge" "somewhere")' == d.claim_egif for d in batch2)
    assert src.legibility == [0.0, 0.0]
    # and every poll was recorded — the run replays offline
    polls = replay_polls(str(tmp_path / "polls.jsonl"))
    assert len(polls) == 2 and polls[0][0].item == "Adam"


def test_rotating_source_frontier_cap_counts_drops():
    src = RotatingWikidataSource(
        ["Q1"], chunk_size=1, frontier_cap=1,                  # no room to grow
        fetch_ids=_frontier_fixture, label_fetch=lambda ids: {})
    src.fetch()
    assert src.frontier_dropped == 1                           # Q3 dropped, counted not silent
    assert src.exhausted()


def test_rotating_source_state_round_trip_continues_the_crawl(tmp_path):
    calls = []

    def fetch_ids(ids):
        calls.append(list(ids))
        return _frontier_fixture(ids)

    kwargs = dict(chunk_size=1, fetch_ids=fetch_ids, label_fetch=lambda ids: {})
    src = RotatingWikidataSource(["Q1", "Q2"], **kwargs)
    src.fetch()                                                # consumes Q1, crawls Q3
    src.save_state(str(tmp_path / "frontier.json"))
    resumed = RotatingWikidataSource.load_state(str(tmp_path / "frontier.json"), **kwargs)
    # the resumed source continues: Q1 not re-polled, the crawled Q3 not lost
    assert resumed.fetch() and calls[-1] == ["Q2"]
    assert resumed.fetch() and calls[-1] == ["Q3"]
    assert resumed.exhausted()


def test_rotating_source_per_entity_cap_bounds_the_hub_and_counts_drops():
    """The hub-degree bound: one entity's M is a star graph, and the checkpoint attest's
    ligature routing is super-linear in hub degree — so statements per entity are capped,
    with drops counted, never silent."""
    big = [WS("Q1", f"prop{i}", f"v{i}") for i in range(10)]
    src = RotatingWikidataSource(["Q1"], chunk_size=1, per_entity_cap=3, crawl=False,
                                 fetch_ids=lambda ids: list(big),
                                 label_fetch=lambda ids: {})
    batch = src.fetch()
    assert len(batch) == 3                                     # hub degree bounded
    assert src.statements_dropped == 7                         # counted, not silent


# --------------------------------------------------------------------------- #
# The change stream — run 2's live source (recentchanges)                      #
# --------------------------------------------------------------------------- #

from wikidata_source import RecentChangesSource, rc_ids


def _rc_payload(*title_ts):
    return {"query": {"recentchanges": [
        {"title": t, "timestamp": ts} for t, ts in title_ts]}}


def test_rc_ids_dedups_keeps_order_and_skips_non_items():
    data = _rc_payload(("Q42", "T3"), ("Property:P31", "T2"), ("Q42", "T2"),
                       ("Q7259", "T1"), ("Talk:Q1", "T1"))
    ids, newest = rc_ids(data)
    assert ids == ["Q42", "Q7259"]                 # distinct items, newest-first order kept
    assert newest == "T3"                          # the continuation point
    assert rc_ids({}) == ([], None)


def test_recentchanges_source_continues_from_the_newest_timestamp():
    asked = []

    def fetch_changes(since):
        asked.append(since)
        return _rc_payload(("Q1", f"T{len(asked)}"))

    src = RecentChangesSource(
        fetch_changes=fetch_changes,
        fetch_ids=lambda ids: [WS(i, "propname", "value") for i in ids],
        label_fetch=lambda ids: {i: f"item {i}" for i in ids})
    src.fetch()
    src.fetch()
    assert asked == [None, "T1"]                   # each poll picks up where the last ended
    assert not src.exhausted()                     # a live stream never ends of itself
    assert src.polls == 2 and src.legibility == [0.0, 0.0]


def test_recentchanges_overturn_bites_because_the_stream_revisits():
    """THE RUN-2 HEADLINE (the F2 fix): the change stream re-delivers an edited entity, so a
    deprecation arrives while the bare value it overturns still STANDS in M — the overturn
    fires across polls, and the mechanism durability question is actually exercised
    (run 1's crawl left it vacuous)."""
    from agon_metalearning import mechanism_principles

    polls = [
        [WS("Q42", "place of birth", "Cambridge", "normal", referenced=False)],
        [WS("Q42", "place of birth", "Cambridge", "deprecated", referenced=False),
         WS("Q42", "place of birth", "London", "normal", referenced=True)],
    ]

    def fetch_changes(since):
        return _rc_payload(("Q42", f"T{len(calls) + 1}")) if calls_left() else {"query": {}}

    calls = []
    def calls_left():
        return len(calls) < len(polls)

    def fetch_ids(ids):
        calls.append(list(ids))
        return polls[len(calls) - 1]

    src = RecentChangesSource(fetch_changes=fetch_changes, fetch_ids=fetch_ids,
                              label_fetch=lambda ids: {})
    r = LiveRunner("", src, WikiDisputeFeed,
                   LiveRunConfig(ttl=None, max_rounds=3, checkpoint=False),
                   panel=_wikidata_panel(), clock=lambda: 0.0).run()
    # the bare value was admitted (poll 1), then relinquished when its deprecation arrived
    # with the value still standing (poll 2) — the referenced replacement is what stands
    assert same_graph(parse_egif(r.final_model_egif),
                      parse_egif('(place_of_birth "Q42" "London")'))
    by_mech = {p.mechanism: p for p in mechanism_principles(r.episodes)}
    assert by_mech["consensus"].stick_rate == 0.0 and not by_mech["consensus"].durable
    assert by_mech["reliable_source"].stick_rate == 1.0 and by_mech["reliable_source"].durable


def test_recentchanges_quiet_stream_paces_and_stops_on_budget():
    clk = [0.0]
    src = RecentChangesSource(fetch_changes=lambda since: {"query": {}},
                              fetch_ids=lambda ids: [], label_fetch=lambda ids: {})
    r = LiveRunner("", src, WikiDisputeFeed,
                   LiveRunConfig(ttl=None, min_interval_s=5.0, max_seconds=12.0,
                                 checkpoint=False),
                   clock=lambda: clk[0],
                   sleep=lambda s: clk.__setitem__(0, clk[0] + s)).run()
    assert r.stopped_because == "max_seconds" and r.total_rounds == 0
    assert src.polls >= 2                          # it kept politely polling, paced


def test_recentchanges_state_round_trip(tmp_path):
    src = RecentChangesSource(fetch_changes=lambda since: _rc_payload(("Q1", "T9")),
                              fetch_ids=lambda ids: [WS("Q1", "propname", "val")],
                              label_fetch=lambda ids: {"Q1": "One"})
    src.fetch()
    src.save_state(str(tmp_path / "stream.json"))
    resumed = RecentChangesSource.load_state(
        str(tmp_path / "stream.json"),
        fetch_changes=lambda since: {"query": {}} if since == "T9" else (_ for _ in ()).throw(
            AssertionError(f"continuation lost: {since}")),
        fetch_ids=lambda ids: [], label_fetch=lambda ids: {})
    assert resumed.fetch() == []                   # the injected assert proves since == "T9"
    assert resumed.polls == 2 and resumed.legibility[:1] == [0.0]


# --------------------------------------------------------------------------- #
# Dirty live strings — the run-2 crash class (found live 2026-07-02)           #
# --------------------------------------------------------------------------- #

from wikidata_source import parseable_disputes
from wiki_dispute_membrane import Resolution as _Res, WikiDispute as _WD, WikiEdit as _WE


def test_hash_in_a_constant_is_content_not_a_comment():
    """The run-2 crasher: a URL value carrying '#' amputated its own line in the EGIF
    preprocessor and read as an unterminated string. Quote-aware comment stripping fixes it;
    real comments still strip."""
    g = parse_egif('(described_at_url "Q1" "https://x.de/a#pid=1")')
    assert len(g.E) == 1
    # real comments still work — full-line and trailing
    g2 = parse_egif('# a comment line\n(rel "X" "y")  # trailing comment')
    assert len(g2.E) == 1
    # and a commented-out graph stays commented out
    assert len(parse_egif('(rel "X" "y")\n# (rel "X" "z")').E) == 1


def test_const_neutralizes_control_characters():
    """Fresh human edits carry newlines/tabs; the membrane renders them as spaces so the
    scribed fact stays single-line and well-formed."""
    s = WS("Q1", "described at URL", "line one\nline two\ttabbed")
    egif = statement_egif(s)
    assert "\n" not in egif and "\t" not in egif
    assert parse_egif(egif)


def test_parse_gate_drops_and_counts_a_poisonous_dispute():
    """Defense in depth: whatever exotic string the live world produces next, one bad dispute
    must not kill an unattended run — it is dropped and counted, never silent."""
    good = _WD('(rel "X" "ok")', [_WE("a", True)], _Res("consensus", True))
    bad = _WD('(rel "X" "broken', [_WE("a", True)], _Res("consensus", True))
    kept, dropped = parseable_disputes([good, bad])
    assert kept == [good] and dropped == 1


def test_recentchanges_source_counts_unparseable(tmp_path):
    src = RecentChangesSource(
        fetch_changes=lambda since: _rc_payload(("Q1", "T1")),
        fetch_ids=lambda ids: [WS("One", "relname", "fine")],
        label_fetch=lambda ids: {})
    src.fetch()
    assert src.unparseable_dropped == 0            # clean input → gate is invisible
    src.save_state(str(tmp_path / "s.json"))
    resumed = RecentChangesSource.load_state(
        str(tmp_path / "s.json"), fetch_changes=lambda since: {"query": {}},
        fetch_ids=lambda ids: [], label_fetch=lambda ids: {})
    assert resumed.unparseable_dropped == 0        # counter persists through resume
