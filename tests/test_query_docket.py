"""The docket of doubts — §15 increment 2a (``src/query_docket.py``), offline and
deterministic. The wire from articulated doubt to executable reach: thin spots of M
(rare relations, lonely individuals) and noted peel-UNKNOWNs become Q1 entity
re-reaches through the existing ``inject`` seam; what Q1 cannot express waits,
counted — never silently dropped. Composes with ``WarmSetTropism`` at the same
poll boundary (decision 2, affirmed 2026-07-05)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from query_docket import DocketEntry, QueryDocket


LABELS = {"Q1": "Alba", "Q2": "Bianca", "Q3": "Ciel"}


def test_harvest_names_the_thin_spots():
    d = QueryDocket(LABELS)
    # 'colour' is grounded twice; 'ringed' once (rare); "Ciel" appears in exactly
    # one atom (lonely) while Alba/Bianca appear twice.
    d.observe('(colour "Alba") (colour "Bianca") (ringed "Alba") (seen "Bianca" "Ciel")')
    provs = {(e.provenance, e.shape) for e in d.open_entries}
    assert ("thin_spot(rare_relation)", "ringed") in provs
    assert ("thin_spot(rare_relation)", "seen") in provs
    assert ("thin_spot(lonely_individual)", "*") in provs
    lonely = [e for e in d.open_entries if e.provenance == "thin_spot(lonely_individual)"]
    assert {e.constants for e in lonely} == {("Ciel",)}
    assert d.harvested == len(d.open_entries)


def test_reaches_emits_q1_ids_and_records_the_attempt():
    d = QueryDocket(LABELS, k=4)
    d.observe('(colour "Alba") (colour "Bianca") (ringed "Ciel")')
    asks = d.reaches()
    assert asks and all(a.startswith("Q") for a in asks)
    assert "Q3" in asks                                   # Ciel — both rare-grip and lonely
    assert d.emitted == len(asks)
    assert any(e.attempts == 1 for e in d.open_entries)   # the ask recorded on the want


def test_inexpressible_entries_wait_counted_never_dropped():
    d = QueryDocket(LABELS)
    # a rare relation whose lone atom has NO constant grip (generic argument only);
    # every constant appears twice so no lonely-individual entries compete
    d.observe('(colour "Alba") (size "Alba") (colour "Bianca") (size "Bianca") (windy *x)')
    grips = [e for e in d.open_entries if e.provenance == "thin_spot(rare_relation)"
             and e.shape == "windy"]
    assert grips and grips[0].constants == ()
    assert d.inexpressible >= 1
    assert d.reaches() == []                              # nothing Q1 can express
    assert grips[0] in d.open_entries                     # still waiting, not dropped


def test_unmapped_and_ambiguous_grips_are_skipped_and_counted():
    d = QueryDocket({"Q1": "Alba", "Q2": "Twin", "Q3": "Twin"})   # 'Twin' ambiguous
    d.note_unknowns([("white", ["Nowhere"]), ("white", ["Twin"]), ("white", ["Alba"])])
    asks = d.reaches(k=5)
    assert asks == ["Q1"]                                 # only Alba reverses cleanly
    assert d.unmapped_skipped >= 1                        # 'Nowhere' not in the cache
    assert d.ambiguous_skipped >= 1                       # 'Twin' reverses two ways


def test_observe_settles_answered_wants():
    d = QueryDocket(LABELS)
    d.observe('(colour "Alba") (colour "Bianca") (ringed "Ciel")')
    open_before = len(d.open_entries)
    assert open_before >= 2                               # rare 'ringed' + lonely Ciel
    # the world answers: a second ringed atom and a second atom bearing Ciel
    d.observe('(colour "Alba") (colour "Bianca") (ringed "Ciel") (ringed "Alba") '
              '(seen "Alba" "Ciel")')
    assert d.resolved >= 2
    keys = {(e.provenance, e.shape) for e in d.open_entries}
    assert ("thin_spot(rare_relation)", "ringed") not in keys
    assert ("thin_spot(lonely_individual)", "*") not in keys or all(
        e.constants != ("Ciel",) for e in d.open_entries
        if e.provenance == "thin_spot(lonely_individual)")


def test_note_unknowns_seam_settles_when_m_comes_to_hold_the_atom():
    d = QueryDocket(LABELS)
    d.note_unknowns([("white", ["Ciel"])])
    assert [e.provenance for e in d.open_entries] == ["unknown_in_peel"]
    assert d.reaches() == ["Q3"]                          # the doubt reaches out
    d.observe('(white "Ciel")')                           # the world answers
    assert d.resolved == 1
    assert not [e for e in d.open_entries if e.provenance == "unknown_in_peel"]
    # (the answering M itself exposes fresh thin spots — new doubts are the point)


def test_ages_accumulate_and_priority_prefers_untried_then_oldest():
    d = QueryDocket(LABELS, k=1)
    d.note_unknowns([("white", ["Alba"])])
    d.observe("")                                         # tick 1: ages the entry
    d.note_unknowns([("black", ["Bianca"])])
    # both untried (attempts 0) → the older entry (white/Alba) goes first
    assert d.reaches() == ["Q1"]
    # now white/Alba has an attempt → the untried black/Bianca goes next
    assert d.reaches() == ["Q2"]


def test_max_entries_defers_counted():
    d = QueryDocket(LABELS, max_entries=1)
    d.note_unknowns([("white", ["Alba"]), ("black", ["Bianca"])])
    assert len(d.open_entries) == 1 and d.deferred == 1


def test_docket_composes_with_tropism_in_the_runner():
    """End to end at the poll boundary: warm re-reaches (tropism) and docket asks
    ride the same inject seam; the docket ticks per segment against the carried M."""
    from live_runner import LiveRunConfig, LiveRunner
    from wiki_dispute_membrane import WikiDisputeFeed
    from wikidata_source import WikidataSource, WikidataStatement as WS

    polls = [
        [WS("Q1", "colour", "white", "normal", referenced=False)],
        [WS("Q2", "colour", "white", "normal", referenced=False)],
        [WS("Q3", "ringed", "yes", "normal", referenced=False)],
    ]
    class _InjectableSource(WikidataSource):
        """The plain replay source + the inject seam the runner requires."""
        def __init__(self, polls):
            super().__init__(polls)
            self.injected_ids = []
        def inject(self, ids):
            self.injected_ids.extend(ids)

    src = _InjectableSource(polls)
    # WikidataSource resolves no labels offline; grips are the raw Q-ids — Q1-able as-is.
    docket = QueryDocket({}, k=2)

    class _Tropism:
        emitted = 0
        ambiguous_skipped = 0
        unmapped_skipped = 0
        def reaches(self, model_egif, ledger=None, k=None):
            return []

    r = LiveRunner("", src, WikiDisputeFeed,
                   LiveRunConfig(ttl=None, checkpoint=False),
                   tropism=_Tropism(), docket=docket, clock=lambda: 0.0).run()
    assert r.total_rounds == 3
    assert docket.harvested > 0                        # thin spots of the growing M
    assert docket.emitted > 0 and src.injected_ids     # asks reached the seam
    assert all(i.startswith("Q") for i in src.injected_ids)
