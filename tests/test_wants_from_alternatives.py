"""AC4 unit — the traced materiality orders the asks (the consumer)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from alternative_index import (
    AlternativeRecord, AlternativeRegister, Materiality, Reception,
    TrackRecord, UntrackedSources, alt_key,
)
from alternative_trace import BoundedRegister
from attention_economy import AttentionEconomy, wants_from_alternatives


def _rec(rel, tier=None, **kw):
    base = dict(key=alt_key(rel, ("Dover",)), relation=rel, labels=("Dover",),
                alternatives=(f'({rel} "Dover")', f'~[ ({rel} "Dover") ]'),
                materiality=Materiality(tier=tier) if tier else None,
                traced_by="step-2" if tier else None)
    base.update(kw)
    return AlternativeRecord(**base)


def _register(*records):
    reg = AlternativeRegister()
    for i, r in enumerate(records):
        reg.note(r, round_idx=i)
    return reg


class TestWantsFromAlternatives:
    def test_severity_by_tier_and_spurious_not_emitted(self):
        reg = _register(_rec("alpha", "material"), _rec("bravo", "bare"),
                        _rec("carol", None), _rec("delta", "spurious"))
        wants = wants_from_alternatives(reg)
        by_rel = {w.payload.relation: w.severity for w in wants}
        assert by_rel == {"alpha": 8.0, "bravo": 2.0, "carol": 4.0}

    def test_novelty_damping_reads_the_s_register(self):
        s = BoundedRegister(8)
        s.admit("distinction:alpha")
        reg = _register(_rec("alpha", "material"), _rec("bravo", "material"))
        wants = wants_from_alternatives(reg, s_register=s)
        by_rel = {w.payload.relation: w.severity for w in wants}
        assert by_rel["alpha"] == 4.0        # already-standing distinction: damped
        assert by_rel["bravo"] == 8.0

    def test_untracked_agreement_earns_exactly_nothing(self):
        agreed = _rec("alpha", "bare", receptions=(Reception(
            source="stranger", stance="supports",
            classification="legible-benign",
            claim_egif='(alpha "Dover")', bears_evidence=True),))
        reg = _register(agreed)
        wants = wants_from_alternatives(reg, source_record=UntrackedSources())
        assert wants[0].severity == 2.0            # unchanged

    def test_tracked_positive_source_gives_bounded_bonus(self):
        class OneGoodSource:
            def track_record(self, source):
                return TrackRecord(bets=4, hits=3, misses=1) \
                    if source == "fieldbook" else None
        evidenced = _rec("alpha", "bare", receptions=(Reception(
            source="fieldbook", stance="supports",
            classification="legible-benign",
            claim_egif='(alpha "Dover")', bears_evidence=True),))
        reg = _register(evidenced)
        wants = wants_from_alternatives(reg, source_record=OneGoodSource())
        assert wants[0].severity == 2.5            # 2.0 * 1.25, once

    def test_economy_asks_material_first_fifo_does_not(self):
        # The AC4 shape: FIFO (creation order) would ask "bravo" (bare, older)
        # first; the economy asks "alpha" (material) first.
        reg = _register(_rec("bravo", "bare", emerged_round=0),
                        _rec("alpha", "material", emerged_round=1))
        wants = wants_from_alternatives(reg)
        econ = AttentionEconomy(musement_fraction=0.0)
        for w in wants:
            econ.register(w)
        chosen = econ.choose(1, round_idx=0)
        assert chosen[0].payload.relation == "alpha"
        fifo = sorted(wants, key=lambda w: (w.created_round, repr(w.key)))
        assert fifo[0].payload.relation == "bravo"

    def test_tracked_negative_or_tied_source_earns_nothing(self):
        class WeakSources:
            def track_record(self, source):
                from alternative_index import TrackRecord
                if source == "loser":
                    return TrackRecord(bets=4, hits=1, misses=3)
                if source == "coinflip":
                    return TrackRecord(bets=4, hits=2, misses=2)   # tie: hits > misses is False
                return None
        for src in ("loser", "coinflip"):
            rec = _rec("alpha", "bare", receptions=(Reception(
                source=src, stance="supports",
                classification="legible-benign",
                claim_egif='(alpha "Dover")', bears_evidence=True),))
            reg = _register(rec)
            wants = wants_from_alternatives(reg, source_record=WeakSources())
            assert wants[0].severity == 2.0, src        # no bonus, no penalty

    def test_bonus_is_one_shot_across_multiple_qualifying_receptions(self):
        class GoodSources:
            def track_record(self, source):
                from alternative_index import TrackRecord
                return TrackRecord(bets=4, hits=3, misses=1)
        two = tuple(Reception(source=s, stance="supports",
                              classification="legible-benign",
                              claim_egif='(alpha "Dover")', bears_evidence=True)
                    for s in ("s1", "s2"))
        rec = _rec("alpha", "bare", receptions=two)
        reg = _register(rec)
        wants = wants_from_alternatives(reg, source_record=GoodSources())
        assert wants[0].severity == 2.5                 # 2.0 * 1.25 exactly once

    def test_resolved_records_are_not_emitted(self):
        rec = _rec("alpha", "material", resolved_by="step-9",
                   selection='(alpha "Dover")')
        reg = _register(rec)
        assert wants_from_alternatives(reg) == []
