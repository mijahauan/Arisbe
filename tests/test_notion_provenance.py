"""Provenance in the ink (``notion_provenance.py``) — who provided, or whence
arrived, a notion, recorded as the author's ruled **conditional**:
``~[ (provided_by S k) ~[ notion ] ]``, read as *given that S provided this,
the notion*.

Design: ``docs/superpowers/specs/2026-08-01-provenance-in-the-ink-and-derived-
reliability-design.md``. The received world enters held as the consequent of
having been given it (the socialization sitting §5.1), so nothing contingent
stands at depth 0 and the notion never claims standing a record would have had
to license. Affirm the antecedent and the notion **derives** — through the Horn
forward-chainer that already reads ``~[ B ~[ H ] ]``.

Named apart from ``provenance.py``, which is the unrelated *bibliographic*
bundle (theorem / EG-derivation / calculus layers, sidecar-persisted).

Two tests here are **falsifiers for defects measured during design** (spec
§5.2, §5.3): a generic antecedent over-fires, and a quotation on the key
silently stops the rule firing. Both failed *silently* in the probe — nothing
raised — so both are pinned.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from model_materialization import materialize_egi
from world_scroll import m_view, wrap_m

from notion_provenance import (affirm_provenance, notion_key,
                               provenance_records, record_provenance)


def _resident(egif: str = '(swan "s1")'):
    """A minimal resident M to receive provenance records."""
    return wrap_m(parse_egif(egif))[0]


def _derives(m, relation: str, *labels: str) -> bool:
    """Does M, forward-chained, hold this ground atom? The question the whole
    conditional form turns on: a received notion is *derived* from its affirmed
    provenance, never stored."""
    facts, _report = materialize_egi(m_view(m))
    return any(
        facts.rel[eid] == relation
        and [facts.get_vertex(v).label for v in facts.nu[eid]] == list(labels)
        for eid in facts.rel)


class TestNotionKey:
    """The key is what makes the antecedent discriminate (spec §5.2)."""

    def test_key_is_stable_across_reparses_of_one_notion(self):
        """Two independent parses of one notion key identically — otherwise a
        source re-supplying the same notion mints a second record and
        corroboration counts one voice twice."""
        assert (notion_key(parse_egif('(white "s1")'))
                == notion_key(parse_egif('(white "s1")')))

    def test_key_is_stable_across_surface_form(self):
        """Keying is on the canonical form, not the source text: one graph
        written two ways is one notion."""
        assert (notion_key(parse_egif('(white "s1") (swan "s1")'))
                == notion_key(parse_egif('(swan "s1") (white "s1")')))

    def test_distinct_notions_key_distinctly(self):
        assert (notion_key(parse_egif('(white "s1")'))
                != notion_key(parse_egif('(tall "s1")')))

    def test_key_rides_safely_inside_an_egif_constant(self):
        """The key travels as an EGIF constant, so it must survive the parser
        without quoting trouble."""
        key = notion_key(parse_egif('(white "s1")'))
        assert key and '"' not in key and " " not in key
        parse_egif(f'(provided_by "wiki" "{key}")')


class TestTheRecord:
    """The conditional: held, not asserted, until its antecedent is affirmed."""

    def test_a_recorded_notion_is_not_yet_derived(self):
        """The point of the conditional form. The notion arrives *held* — the
        unit is committed to it only given that the source provided it, so
        nothing contingent gains standing merely by arriving."""
        m, _key = record_provenance(_resident(), source="wiki",
                                    notion_egif='(white "s1")')
        assert not _derives(m, "white", "s1")

    def test_affirming_the_antecedent_derives_the_notion(self):
        m, key = record_provenance(_resident(), source="wiki",
                                   notion_egif='(white "s1")')
        m = affirm_provenance(m, source="wiki", key=key)
        assert _derives(m, "white", "s1")

    def test_a_record_from_another_source_does_not_fire_this_one(self):
        """Falsifier for the measured over-firing defect (spec §5.2): with a
        generic antecedent, one affirmation derived a notion nobody affirmed."""
        m, white_key = record_provenance(_resident(), source="wiki",
                                         notion_egif='(white "s1")')
        m, _tall_key = record_provenance(m, source="wiki",
                                         notion_egif='(tall "s1")')
        m = affirm_provenance(m, source="wiki", key=white_key)
        assert _derives(m, "white", "s1")
        assert not _derives(m, "tall", "s1"), (
            "affirming one notion fired another the source merely also "
            "contributed — the antecedent is not discriminating")

    def test_two_sources_for_one_notion_each_suffice(self):
        """Plurality (sitting §5.2): a second authoritative adult is a second
        antecedent, and either alone carries the notion."""
        base, wiki_key = record_provenance(_resident(), source="wiki",
                                           notion_egif='(white "s1")')
        base, field_key = record_provenance(base, source="field",
                                            notion_egif='(white "s1")')
        assert wiki_key == field_key, (
            "one notion is one key — the SOURCE is what distinguishes the two "
            "records, which is why corroboration can recognise them as the "
            "same notion twice attested")
        assert not _derives(base, "white", "s1")
        assert _derives(affirm_provenance(base, source="wiki", key=wiki_key),
                        "white", "s1")
        assert _derives(affirm_provenance(base, source="field", key=field_key),
                        "white", "s1")

    def test_the_notion_is_derived_never_stored(self):
        """m_view holds the conditional and the affirmation — never the bare
        notion. That is what makes retraction of the affirmation sufficient."""
        m, key = record_provenance(_resident(), source="wiki",
                                   notion_egif='(white "s1")')
        m = affirm_provenance(m, source="wiki", key=key)
        assert _derives(m, "white", "s1")
        held = m_view(m)
        assert not any(
            held.rel[eid] == "white"
            and held.get_context(eid) == held.sheet
            for eid in held.rel), "the notion was stored, not derived"


class TestReadingRecordsBack:

    def test_records_read_back_with_source_key_and_affirmation(self):
        m, key = record_provenance(_resident(), source="wiki",
                                   notion_egif='(white "s1")')
        (rec,) = provenance_records(m)
        assert (rec.source, rec.key, rec.affirmed) == ("wiki", key, False)

        m = affirm_provenance(m, source="wiki", key=key)
        (rec,) = provenance_records(m)
        assert rec.affirmed is True

    def test_a_resident_with_no_records_reads_empty(self):
        assert provenance_records(_resident()) == []

    def test_records_carry_the_notion_relation_for_domain_indexing(self):
        """Examination VII ruling 1 made the credential domain-indexed; the
        relation is that index at the granularity the general machinery has,
        and it is what Unit.peers already keys by."""
        m, _key = record_provenance(_resident(), source="wiki",
                                    notion_egif='(white "s1")')
        (rec,) = provenance_records(m)
        assert rec.relations == frozenset({"white"})


class TestRetraction:

    def test_retracting_the_affirmation_withdraws_the_notion(self):
        """Because the notion was derived and never stored, dropping the
        antecedent is sufficient — no separate erasure of the notion, and no
        way for a stale copy to survive its warrant."""
        from world_scroll import retract_from_m

        m, key = record_provenance(_resident(), source="wiki",
                                   notion_egif='(white "s1")')
        m = affirm_provenance(m, source="wiki", key=key)
        assert _derives(m, "white", "s1")

        m, _erased = retract_from_m(m, relation="provided_by",
                                    labels=["wiki", key])
        assert not _derives(m, "white", "s1")
        assert provenance_records(m)[0].affirmed is False, (
            "the conditional still stands — only its antecedent was withdrawn")


class TestTheQuotationFalsifier:
    """Spec §5.3 — measured during design, and it fails SILENTLY.

    Attaching a quotation oval to the key vertex succeeds (a constant vertex
    takes ``sort=proposition`` and an oval without complaint), but the
    materializer then reads the oval as an extra cut in the body and skips the
    rule as ``complex_body``. Nothing raises; the notion simply stops deriving.

    Pinned so that a regression is a failure. If the materializer ever learns
    to skip quotation cuts when reading Horn shape — the more principled fix,
    named in the spec and deliberately not taken — this test fails and says so.
    """

    def test_a_quotation_on_the_key_silently_disables_derivation(self):
        from quotation_overlay import quote_existing_name

        m, key = record_provenance(_resident(), source="wiki",
                                   notion_egif='(white "s1")')
        eid = next(e for e in m.rel if m.rel[e] == "provided_by")
        m = quote_existing_name(m, m.nu[eid][1], parse_egif('(white "s1")'))[0]
        m = affirm_provenance(m, source="wiki", key=key)

        _facts, report = materialize_egi(m_view(m))
        assert any(s.reason == "complex_body" for s in report.skipped)
        assert not _derives(m, "white", "s1"), (
            "the materializer now reads through the oval — revisit the spec's "
            "named-but-not-taken fix, and the quotation may come back")


class TestChainRecording:
    """Both moves are one licensed INS-of-cell, so both record through the
    existing ``m_steps.admit_step`` — no new act, and the standing polarity
    gate covers them unchanged."""

    def test_both_moves_record_as_earned_enlargements(self):
        from m_steps import admit_step
        from proof_authoring import ProofChain

        pc = ProofChain(_resident())
        key = notion_key(parse_egif('(white "s1")'))
        pc = admit_step(
            pc,
            f'~[ (provided_by "wiki" "{key}") ~[ (white "s1") ] ]',
            disposition="new_fact", mode="induction",
            warrant="arrival recorded, not yet affirmed")
        pc = admit_step(pc, f'(provided_by "wiki" "{key}")',
                        disposition="new_fact", mode="induction")

        steps = pc.to_chain().steps
        assert len(steps) == 2
        for step in steps:
            assert step.parameters["act"] == "m_enlargement"
            assert step.parameters["earned"] is True
            assert step.parameters["derivation"] == ["INS"]
        assert _derives(pc.current, "white", "s1")
