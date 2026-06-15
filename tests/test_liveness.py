"""Liveness / desuetude tracking — manifest floor #7 (*two deaths, so track liveness*).

The forward-facing-provenance contract: consulting a UoD keeps it alive; an
unconsulted telling slides toward desuetude (the second death, "though it was never
wrong"); retiring is deliberate and *reversible*. Nothing here is a sign or a
verdict — it is local usage *form*, outside §3.3.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from liveness import (  # noqa: E402
    LivenessLog, DORMANT_AFTER_DAYS, KIND_VIEWED, KIND_MODEL, get_log,
)


class _Clock:
    """An injectable clock so the desuetude window is deterministic in tests."""
    def __init__(self, now): self.now = now
    def __call__(self): return self.now


def _log(tmp_path, now=None):
    now = now or datetime(2026, 6, 15, tzinfo=timezone.utc)
    return LivenessLog(tmp_path / ".liveness.json", clock=_Clock(now)), _Clock(now)


def test_unconsulted_is_the_default(tmp_path):
    log, _ = _log(tmp_path)
    s = log.summary("never_opened")
    assert s.status == "unconsulted"
    assert s.count == 0 and s.last is None


def test_recording_a_view_makes_it_alive(tmp_path):
    log, clk = _log(tmp_path)
    s = log.record("porphyry_tree", KIND_VIEWED)
    assert s.status == "alive"
    assert s.count == 1 and s.kinds[KIND_VIEWED] == 1
    assert s.first == s.last and s.days_since_last == 0


def test_consultations_accumulate_and_persist(tmp_path):
    log, _ = _log(tmp_path)
    log.record("u", KIND_VIEWED)
    log.record("u", KIND_MODEL)
    log.record("u", KIND_VIEWED)
    # a fresh log over the SAME file sees the persisted tally
    reopened = LivenessLog(tmp_path / ".liveness.json", clock=_Clock(datetime(2026, 6, 15, tzinfo=timezone.utc)))
    s = reopened.summary("u")
    assert s.count == 3
    assert s.kinds[KIND_VIEWED] == 2 and s.kinds[KIND_MODEL] == 1


def test_desuetude_window_dormant_then_revived(tmp_path):
    # consult long ago, then read "now" past the window → dormant
    then = datetime(2026, 1, 1, tzinfo=timezone.utc)
    log = LivenessLog(tmp_path / ".liveness.json", clock=_Clock(then))
    log.record("old", KIND_VIEWED)
    now = then + timedelta(days=DORMANT_AFTER_DAYS + 5)
    log._clock = _Clock(now)
    s = log.summary("old")
    assert s.status == "dormant"
    assert s.days_since_last == DORMANT_AFTER_DAYS + 5
    # consulting it again brings it back to alive
    s2 = log.record("old", KIND_VIEWED)
    assert s2.status == "alive" and s2.days_since_last == 0


def test_retire_and_revive_are_reversible(tmp_path):
    log, _ = _log(tmp_path)
    log.record("settled", KIND_VIEWED)
    s = log.set_retired("settled", True)
    assert s.status == "retired" and s.retired is True
    # retirement is a stance, not a deletion: counts survive
    assert s.count == 1
    s2 = log.set_retired("settled", False)
    assert s2.retired is False and s2.status == "alive"


def test_consulting_a_retired_model_revives_it(tmp_path):
    log, _ = _log(tmp_path)
    log.record("m", KIND_VIEWED)
    log.set_retired("m", True)
    assert log.summary("m").status == "retired"
    s = log.record("m", KIND_MODEL)   # re-consulting a retired telling brings it back
    assert s.retired is False and s.status == "alive"


def test_all_returns_only_recorded_uods(tmp_path):
    log, _ = _log(tmp_path)
    log.record("a", KIND_VIEWED)
    log.record("b", KIND_MODEL)
    everything = log.all()
    assert set(everything) == {"a", "b"}
    assert everything["b"].kinds[KIND_MODEL] == 1


def test_get_log_is_cached_per_root(tmp_path):
    a = get_log(tmp_path)
    b = get_log(tmp_path)
    assert a is b
    assert a.path == tmp_path / ".liveness.json"
