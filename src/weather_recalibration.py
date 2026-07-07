"""
Weather re-generalization — the controller that turns predict→refute→**silence**
into predict→refute→**re-generalize**.

Run 7 (``runs/RUN_7_LOG.md`` F2⁷) seeded a naive weather theory ("what is
forecast, happens"); the world falsified it and both laws were relinquished via
``challenge_to_M`` — then the game fell silent, because nothing induced a
*better-calibrated* replacement.  This module reads the resolving membrane's
:class:`resolving_membrane.PredictionLedger` track record and, for each claim
kind that has fallen (or is under-performing), **steps its discretization toward
a less-falsifiable, better-calibrated shape** and re-seeds its (structurally
identical) law:

- **temperature** — widen the band (``self._width``): an observation a few degrees
  off the forecast then lands in the *same* band, so the same law
  ``~[ (forecast_temp_band …) ~[ (temp_band …) ] ]`` becomes reliable;
- **precipitation** — raise the PoP threshold (``self._pop``): only high-confidence
  forecasts are claimed, so the precip law holds.

The controller is an **adaptive step-to-reliability-target**, not an exact fit:
the ledger records only hit/miss (not the numeric delta), and a one-step-per-
segment controller needs only those counts, is robust, and converges within the
caps.  ``recalibrate`` is a pure, deterministic function of the ledger + current
knobs + the standing laws — LLM-free, geometry-free, network-free.  The driver
applies the result between segments (mutate ``source._width``/``_pop``; re-add
``reseed_laws`` to ``runner._laws``); with re-generalization off, run 7 is
reproduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from weather_source import LAW_PRECIP, LAW_TEMP


@dataclass
class RecalibrationResult:
    """The recalibrated claim knobs + the laws to re-seed into M.

    ``changed`` is True iff a knob moved or a fallen law is being re-seeded — the
    driver only mutates the source / runner when something actually changed, so a
    healthy segment is a no-op.
    """
    band_width: int
    pop_threshold: int
    reseed_laws: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    changed: bool = False


def _kind_of(claim_egif: str) -> Optional[str]:
    """The claim kind of a *resolution* entry, or None for a raise-phase
    ``(forecast_…)`` item (which is never scored as a bet)."""
    s = claim_egif.lstrip()
    if s.startswith("(temp_band"):
        return "temp"
    if s.startswith("(precip"):
        return "precip"
    return None


def _law_standing(law: str, standing_laws: Sequence[str]) -> bool:
    """Whether ``law`` is still on M (structural, tolerant of reformatting)."""
    try:
        from egif_parser_dau import parse_egif
        from eg_navigation import same_graph
        target = parse_egif(law)
        for s in standing_laws:
            try:
                if same_graph(parse_egif(s), target):
                    return True
            except Exception:
                if s.strip() == law.strip():
                    return True
        return False
    except Exception:
        return any(s.strip() == law.strip() for s in standing_laws)


def recalibrate(
    ledger,
    *,
    band_width: int,
    pop_threshold: int,
    standing_laws: Sequence[str],
    target: float = 0.6,
    window: int = 20,
    band_step: int = 5,
    band_cap: int = 20,
    pop_step: int = 10,
    pop_cap: int = 90,
) -> RecalibrationResult:
    """Re-generalize under-performing / relinquished claim kinds from the ledger.

    For each kind (temperature, precipitation): read its recent resolution bets
    (the last ``window``, ignoring raise-phase ``(forecast_…)`` items); if its
    law has fallen off ``standing_laws`` **or** its recent accuracy is below
    ``target``, step its knob toward a less-falsifiable shape (band wider / PoP
    higher, each capped) and — if the law has fallen — mark it for re-seeding so
    the game bets again under the new calibration.  Deterministic; a no-op
    (``changed=False``) when every tried kind meets target and stands.
    """
    result = RecalibrationResult(band_width=band_width, pop_threshold=pop_threshold)

    bets = [e for e in ledger.entries if _kind_of(e.claim_egif) is not None]
    for kind, law in (("temp", LAW_TEMP), ("precip", LAW_PRECIP)):
        kind_bets = [e for e in bets if _kind_of(e.claim_egif) == kind]
        if not kind_bets:
            continue                       # never tried — nothing to calibrate
        recent = kind_bets[-window:]
        hits = sum(1 for e in recent if e.result == "hit")
        misses = sum(1 for e in recent if e.result == "miss")
        graded = hits + misses
        acc = (hits / graded) if graded else None
        standing = _law_standing(law, standing_laws)
        underperforming = acc is not None and acc < target
        if standing and not underperforming:
            continue                       # this kind is calibrated and betting

        # Step the discretization toward a less-falsifiable shape (if room).
        if kind == "temp":
            new = min(band_cap, result.band_width + band_step)
            stepped = new != result.band_width
            result.band_width = new
        else:
            new = min(pop_cap, result.pop_threshold + pop_step)
            stepped = new != result.pop_threshold
            result.pop_threshold = new

        # Bring a fallen law back so the second act is prediction, not silence.
        if not standing:
            result.reseed_laws.append(law)

        acc_s = "n/a" if acc is None else f"{acc:.2f}"
        result.notes.append(
            f"{kind}: acc={acc_s} standing={standing} "
            f"-> {'widened' if (stepped and kind == 'temp') else ''}"
            f"{'raised-pop' if (stepped and kind == 'precip') else ''}"
            f"{' reseed' if not standing else ''}".strip())

    result.changed = bool(result.reseed_laws) or (
        result.band_width != band_width or result.pop_threshold != pop_threshold)
    return result


__all__ = ["RecalibrationResult", "recalibrate"]
