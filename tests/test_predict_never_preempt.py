"""Docket item ⑪, charge 3 — the predict-never-preempt invariance gate.

Modeled on the A3 conservativity gate (``test_second_order_conservativity``):
a quoted, attributed prediction banked in M — ``(asserted "author" ⌜P⌝)``,
the V2a.2 banking shape — must never *preempt* the game. Two fixture models,
identical except one carries the quoted cell, are put through the mechanical
panel's disposition of the same fixed proposals: verdict and disposition must
be identical. The quoted P is mention, not use — if it leaked into standing
ink it would (a) make the Observer abstain on a proposal it "already holds",
(b) flip a law's peel to TRUE and wake the Generalizer. Both leaks are pinned
here, on the bare fixtures and on their world-scroll residents.

The question-neutrality rider (same charge, the note-side preempt): the
V2a.1 two-option question templates used to embed the forecast as a fixed
option position — a constant tell. The option order is now seed-alternated
(rng-injected); both orders must occur across a seeded run, and ``rng=None``
keeps the historical wording (backward compatible).
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agon_evolution import (
    Agonothetes, DeliberationContext, atom_key, peel, sheet_atom_keys,
)
from egif_parser_dau import parse_egif
from model_revision import revise_with_disposition
from quotation_overlay import quote_existing_name
from world_scroll import wrap_state


HOST = '(swan "Alba") (asserted "author" "author_claim")'
QUOTED_P = '(white "Alba")'

GROUND_PROPOSAL = '(swan "Nox")'
LAW_PROPOSAL = '~[ (swan *x) ~[ (white x) ] ]'


def _pair():
    """Two hosts, identical first-order ink; one carries the quoted
    ``(asserted "author" ⌜(white "Alba")⌝)`` cell (the name vertex
    ``author_claim`` gains the sort + an oval holding P's ink)."""
    plain = parse_egif(HOST)
    host = parse_egif(HOST)
    vid = next(v.id for v in host.V if v.label == "author_claim")
    quoted, _cut = quote_existing_name(host, vid, parse_egif(QUOTED_P))
    return plain, quoted


def _dispose(model, proposal, known_laws=()):
    """The mechanical panel's reading of one proposal against one model:
    (verdict, disposition) — the pair the invariance gate compares."""
    result = peel(model, proposal)
    ctx = DeliberationContext(model, proposal, result, list(known_laws))
    panel = Agonothetes()
    winner = panel.resolve(panel.deliberate(ctx))
    return result.verdict.value, (winner.disposition if winner else None)


class TestPredictNeverPreempt:
    def test_quoted_cell_is_not_standing_ink(self):
        plain, quoted = _pair()
        assert quoted.quotation, "fixture must actually carry the quotation"
        assert atom_key("white", ["Alba"]) not in sheet_atom_keys(quoted)
        # the two fixtures' standing atoms are IDENTICAL — the quotation adds
        # only mention, never a fact.
        assert sheet_atom_keys(quoted) == sheet_atom_keys(plain)

    def test_ground_proposal_disposed_identically(self):
        plain, quoted = _pair()
        assert (_dispose(plain, GROUND_PROPOSAL)
                == _dispose(quoted, GROUND_PROPOSAL)
                == ("false", "new_fact"))

    def test_quoted_p_itself_is_not_already_held(self):
        """The Observer leak: if ⌜(white "Alba")⌝ read as standing ink, the
        proposal ``(white "Alba")`` would be redundant (Observer abstains →
        disposition None) on the quoted fixture only."""
        plain, quoted = _pair()
        assert (_dispose(plain, QUOTED_P)
                == _dispose(quoted, QUOTED_P)
                == ("false", "new_fact"))

    def test_law_over_the_quoted_p_not_preempted(self):
        """The Generalizer leak: if the quoted P leaked into the oracle's
        facts, ``∀x swan→white`` would peel TRUE on the quoted fixture and
        wake the Generalizer. Both must read (false, None)."""
        plain, quoted = _pair()
        assert (_dispose(plain, LAW_PROPOSAL)
                == _dispose(quoted, LAW_PROPOSAL)
                == ("false", None))

    def test_revision_applies_identically_and_mention_survives(self):
        """Over the RESIDENT forms — the V2a.2 banking shape (a quoted cell
        lives in the world-scroll; revision = a licensed INS of a fresh cell,
        no linear-form round trip)."""
        r_plain, _ = wrap_state(_pair()[0])
        r_quoted, _ = wrap_state(_pair()[1])
        plain2 = revise_with_disposition(r_plain, "new_fact",
                                          fact_egif=GROUND_PROPOSAL)
        quoted2 = revise_with_disposition(r_quoted, "new_fact",
                                           fact_egif=GROUND_PROPOSAL)
        assert sheet_atom_keys(plain2) == sheet_atom_keys(quoted2)
        assert atom_key("swan", ["Nox"]) in sheet_atom_keys(quoted2)
        assert quoted2.quotation           # the mention is untouched by the move
        assert atom_key("white", ["Alba"]) not in sheet_atom_keys(quoted2)

    def test_bare_sheet_revision_refuses_honestly(self):
        """PIN of a named limit (not new behavior): a BARE sheet-level M
        carrying a quotation cannot take the sheet-fallback revision path —
        ``assert_fact`` round-trips through the EGIF generator, which raises
        the named ``SecondOrderNotInLinearForm`` rather than silently
        demoting the oval to a negation (the Examination-IV A3 failure
        shape). The resident path above is the licensed route."""
        import pytest
        from second_order_limits import SecondOrderNotInLinearForm
        _plain, quoted = _pair()
        with pytest.raises(SecondOrderNotInLinearForm):
            revise_with_disposition(quoted, "new_fact",
                                     fact_egif=GROUND_PROPOSAL)

    def test_resident_fixtures_disposed_identically(self):
        """The same gate over the world-scroll residents (`wrap_state`): the
        loops play M resident, so the invariance must hold through m_view."""
        plain, quoted = _pair()
        r_plain, _ = wrap_state(plain)
        r_quoted, _ = wrap_state(quoted)
        for proposal, expected in (
            (GROUND_PROPOSAL, ("false", "new_fact")),
            (QUOTED_P, ("false", "new_fact")),
            (LAW_PROPOSAL, ("false", None)),
        ):
            assert (_dispose(r_plain, proposal)
                    == _dispose(r_quoted, proposal)
                    == expected), proposal

    def test_disposition_invariant_to_a_REALLY_banked_cell(self):
        """The fixtures above quote a hand-built cell (``_pair`` via
        ``quote_existing_name`` directly). V2a.2 opened the real channel —
        assert the same invariance on ``bank_answer``'s actual output: a
        resident model with a banked oracle answer disposes every proposal
        exactly as models without the banked quotation.

        ``bank_answer`` does two things at once: it INSs the attribution
        atom ``(asserted "author" *q)`` (``ATTRIBUTION_EGIF``) AND wraps the
        fresh name in a quotation oval holding the verbatim prose. Comparing
        a bare model against the banked model therefore varies two things
        at once. The invariance this gate actually claims is about the
        QUOTATION alone, so the sharper control already carries the
        attribution atom WITHOUT the oval (built with the same ``enlarge_m``
        primitive ``bank_answer`` itself uses) — that isolates exactly the
        quotation's contribution. The weaker bare-vs-banked comparison is
        included too, as a second, non-sharp corroboration."""
        from oracle_notes import ATTRIBUTION_EGIF, bank_answer
        from world_scroll import enlarge_m

        plain, _ = wrap_state(parse_egif('(swan "Alba")'))
        banked, _cut = bank_answer(plain, "I think all swans are white.",
                                    qid="q1", note_date="2026-07-19")
        control = enlarge_m(plain, ATTRIBUTION_EGIF)

        for proposal in (GROUND_PROPOSAL, QUOTED_P, LAW_PROPOSAL):
            # sharper form: isolates the quotation's contribution alone.
            assert _dispose(control, proposal) == _dispose(banked, proposal)
            # weaker form: bare model vs. the fully banked model.
            assert _dispose(plain, proposal) == _dispose(banked, proposal)


# --------------------------------------------------------------------------- #
# The question-neutrality rider                                               #
# --------------------------------------------------------------------------- #


class _NeutralityWorld:
    """A world double with 3 Clippings notes + 3 journal-shaped files, so a
    single candidate build yields 5 two-option questions to alternate over."""

    def __init__(self):
        self.long_labels = {}

    def notes(self):
        return [f"Clippings/n{i}.md" for i in range(3)] + ["Journal/main.md"]

    def _top_dir(self, relpath):
        return relpath.split("/")[0]

    def journal_paths(self):
        return ["Journal/main.md", "Journal/j2.md", "Journal/j3.md"]

    def note_id(self, relpath):
        return relpath


PROV_CANONICAL = "collected from elsewhere, or your own writing?"
PROV_FLIPPED = "your own writing, or collected from elsewhere?"
JOURNAL_CANONICAL = "a genuine journal, or a fragment/copy of"
JOURNAL_FLIPPED = "a fragment/copy of"   # flipped form STARTS with this option


def _two_option_texts(rng):
    from oracle_notes import candidates_from_run
    cands = candidates_from_run(_NeutralityWorld(), None, [], {}, rng=rng)
    return [c.text for c in cands
            if c.qid.startswith(("prov:", "journal:"))]


class TestQuestionNeutrality:
    def test_both_orders_occur_across_a_seeded_run(self):
        # seed chosen so the 5 flips land on both sides (deterministic).
        texts = _two_option_texts(random.Random(3))
        canonical = [t for t in texts
                     if PROV_CANONICAL in t or JOURNAL_CANONICAL in t]
        flipped = [t for t in texts if t not in canonical]
        assert canonical and flipped, texts
        # a flipped provenance question really is the same two options,
        # forecast-second.
        assert any(PROV_FLIPPED in t for t in texts) or any(
            t.split("` ", 1)[-1].startswith("a fragment/copy of")
            for t in texts if t not in canonical)

    def test_seeded_order_is_reproducible(self):
        assert _two_option_texts(random.Random(3)) == \
            _two_option_texts(random.Random(3))

    def test_rng_none_keeps_the_historical_wording(self):
        # backward-compat pin: no rng → every question in the canonical order.
        texts = _two_option_texts(None)
        assert texts and all(
            PROV_CANONICAL in t or JOURNAL_CANONICAL in t for t in texts)
