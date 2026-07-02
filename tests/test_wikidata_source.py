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
    WikidataSource, WikidataStatement as WS, collect_ids, resolve_labels,
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
