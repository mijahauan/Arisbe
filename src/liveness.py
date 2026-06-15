"""liveness.py — forward-facing provenance: is a telling still alive in the conversation?

Manifest floor #7 (``docs/MANIFEST_AND_MEANING.md``): *"Two deaths, so track
liveness."* A telling can be relinquished by **falsification** (drawn back under a
cut and refuted) or by **desuetude** (falling out of use). Warrant already records
how a telling was tested (Agon, §3.3); this module records the *other* axis — every
time a UoD/model is **consulted** (viewed in Organon, used as a model M in Agon,
re-opened) — so the corpus can say whether each telling *remains alive* or is
sliding into the second death "though it was never wrong."

What this is **not**: it is not part of the graph and not §3.3 — consulting a sign
is not itself a sign, so the correspondence chord does not answer for it (nothing
here attests). It is local, mutable *usage* state (a single JSON store beside the
corpus, churning on every view — keep it out of the committed corpus). And, like all
warrant here, it is **reversible**: a settled model can be explicitly *retired* (the
second death made deliberate) and *revived* — "no irreversible commitment anywhere;
the only bedrock is the blank sheet." Recording a consultation never mutates the UoD
or its drawing.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Optional

# A consultation older than this is *dormant* (sliding toward desuetude). A window,
# not a verdict — the telling is not wrong, only unconsulted.
DORMANT_AFTER_DAYS = 90

# The kinds of consultation we record. Open set in spirit; these are the wired ones.
KIND_VIEWED = "viewed"      # opened/read in Organon
KIND_MODEL = "model"        # used as the model M in an Agon inning
KIND_TESTED = "tested"      # a proposal was tested against it (interpret / contest)
KIND_REOPENED = "reopened"  # re-opened for editing (Ergasterion edit-base)
CONSULT_KINDS = {KIND_VIEWED, KIND_MODEL, KIND_TESTED, KIND_REOPENED}

# Lifecycle acts (not consultations — they don't refresh the "last consulted" clock).
KIND_RETIRED = "retired"
KIND_REVIVED = "revived"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


@dataclass
class LivenessSummary:
    """The forward-facing record for one UoD — *form* of its use, never a verdict."""
    uod_id: str
    count: int = 0                       # total consultations (any kind)
    first: Optional[str] = None          # iso of the first consultation
    last: Optional[str] = None           # iso of the most recent consultation
    kinds: Dict[str, int] = field(default_factory=dict)
    retired: bool = False
    status: str = "unconsulted"          # alive | dormant | unconsulted | retired
    days_since_last: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "uod_id": self.uod_id, "count": self.count,
            "first": self.first, "last": self.last, "kinds": dict(self.kinds),
            "retired": self.retired, "status": self.status,
            "days_since_last": self.days_since_last,
        }


def status_of(rec: dict, now: datetime) -> tuple:
    """(status, days_since_last) for a stored record under the desuetude policy.

    retired ⇒ "retired"; never consulted ⇒ "unconsulted" (dying the second death,
    though never wrong); consulted within the window ⇒ "alive"; else ⇒ "dormant".
    """
    if rec.get("retired"):
        last = rec.get("last")
        days = _days_since(last, now) if last else None
        return "retired", days
    last = rec.get("last")
    if not rec.get("count") or not last:
        return "unconsulted", None
    days = _days_since(last, now)
    return ("alive" if days is not None and days <= DORMANT_AFTER_DAYS else "dormant"), days


def _days_since(iso: str, now: datetime) -> Optional[int]:
    try:
        dt = datetime.fromisoformat(iso)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


class LivenessLog:
    """A small read-modify-write JSON store of per-UoD consultation summaries.

    Compact by design: one summary per UoD (first / last / count / per-kind tally /
    retired), not a full event log — enough to answer "still alive?" without
    unbounded growth. Thread-guarded for the single-process dev server.
    """

    def __init__(self, path: Path, clock: Callable[[], datetime] = _utcnow):
        self.path = Path(path)
        self._clock = clock
        self._lock = threading.Lock()

    # ---- persistence ----
    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        tmp.replace(self.path)

    # ---- recording ----
    def record(self, uod_id: str, kind: str = KIND_VIEWED) -> LivenessSummary:
        """Record one consultation of ``uod_id``; returns the refreshed summary.

        A consultation refreshes the "last consulted" clock and the per-kind tally.
        A consultation also implicitly *revives* a retired model (re-consulting a
        retired telling is exactly the reversible act the manifest insists on).
        """
        now = self._clock()
        iso = _iso(now)
        with self._lock:
            data = self._read()
            rec = data.get(uod_id) or {"first": iso, "last": iso, "count": 0,
                                       "kinds": {}, "retired": False}
            rec["count"] = int(rec.get("count", 0)) + 1
            rec["last"] = iso
            rec.setdefault("first", iso)
            rec["kinds"] = dict(rec.get("kinds", {}))
            rec["kinds"][kind] = int(rec["kinds"].get(kind, 0)) + 1
            if rec.get("retired") and kind in CONSULT_KINDS:
                rec["retired"] = False  # consulting it again brings it back to life
                rec["kinds"][KIND_REVIVED] = int(rec["kinds"].get(KIND_REVIVED, 0)) + 1
            data[uod_id] = rec
            self._write(data)
            return self._summary(uod_id, rec, now)

    def set_retired(self, uod_id: str, retired: bool = True) -> LivenessSummary:
        """Explicitly retire (the deliberate second death) or revive a model.

        Reversible by construction — the inverse call revives it. Does *not* touch
        the "last consulted" clock; retirement is a stance about use, not a use.
        """
        now = self._clock()
        with self._lock:
            data = self._read()
            rec = data.get(uod_id) or {"first": None, "last": None, "count": 0,
                                       "kinds": {}, "retired": False}
            rec["retired"] = bool(retired)
            rec["kinds"] = dict(rec.get("kinds", {}))
            key = KIND_RETIRED if retired else KIND_REVIVED
            rec["kinds"][key] = int(rec["kinds"].get(key, 0)) + 1
            data[uod_id] = rec
            self._write(data)
            return self._summary(uod_id, rec, now)

    # ---- reading ----
    def _summary(self, uod_id: str, rec: dict, now: datetime) -> LivenessSummary:
        st, days = status_of(rec, now)
        return LivenessSummary(
            uod_id=uod_id, count=int(rec.get("count", 0)),
            first=rec.get("first"), last=rec.get("last"),
            kinds=dict(rec.get("kinds", {})), retired=bool(rec.get("retired")),
            status=st, days_since_last=days,
        )

    def summary(self, uod_id: str) -> LivenessSummary:
        """The summary for one UoD (``unconsulted`` if it has no record)."""
        now = self._clock()
        rec = self._read().get(uod_id)
        if rec is None:
            return LivenessSummary(uod_id=uod_id)
        return self._summary(uod_id, rec, now)

    def all(self) -> Dict[str, LivenessSummary]:
        """Summaries for every UoD that carries a record (keyed by id)."""
        now = self._clock()
        data = self._read()
        return {uid: self._summary(uid, rec, now) for uid, rec in data.items()}


# A cached default log per tomos root, so the route modules share one store without
# threading an instance through. Keyed by resolved path.
_LOGS: Dict[str, LivenessLog] = {}
_LOGS_LOCK = threading.Lock()


def get_log(tomos_root, clock: Callable[[], datetime] = _utcnow) -> LivenessLog:
    """The shared ``LivenessLog`` for a corpus root (store: ``<root>/.liveness.json``)."""
    key = str(Path(tomos_root).resolve())
    with _LOGS_LOCK:
        log = _LOGS.get(key)
        if log is None:
            log = LivenessLog(Path(tomos_root) / ".liveness.json", clock=clock)
            _LOGS[key] = log
        return log
