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

from weather_source import LAW_PRECIP, LAW_PRECIP_DRY, LAW_TEMP


@dataclass
class RecalibrationResult:
    """The recalibrated claim knobs + the laws to re-seed into M.

    ``changed`` is True iff a knob moved or a fallen law is being re-seeded — the
    driver only mutates the source / runner when something actually changed, so a
    healthy segment is a no-op. ``pop_cut`` is the calibrated-mode precip cutpoint
    (run 11); ``pop_threshold`` the gate-mode selectivity gate (run 10).
    """
    band_width: int
    pop_threshold: int
    pop_cut: int = 50
    reseed_laws: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    changed: bool = False


def _kind_of(claim_egif: str) -> Optional[str]:
    """The claim kind of a *resolution* entry, or None for a raise-phase
    ``(forecast_…)`` item (which is never scored as a bet). Both ``(precip …)``
    (a wet bet) and ``(dry …)`` (a calibrated dry bet) are precip-arm."""
    s = claim_egif.lstrip()
    if s.startswith("(temp_band"):
        return "temp"
    if s.startswith("(precip") or s.startswith("(dry"):
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


def _acc(entries) -> Optional[float]:
    """Recent accuracy over decided (hit/miss) bets, or None if none decided."""
    hits = sum(1 for e in entries if e.result == "hit")
    misses = sum(1 for e in entries if e.result == "miss")
    graded = hits + misses
    return (hits / graded) if graded else None


def recalibrate(
    ledger,
    *,
    band_width: int,
    pop_threshold: int,
    standing_laws: Sequence[str],
    precip_mode: str = "gate",
    pop_cut: int = 50,
    target: float = 0.6,
    window: int = 20,
    band_step: int = 5,
    band_cap: int = 20,
    pop_step: int = 10,
    pop_cap: int = 90,
    cut_step: int = 10,
) -> RecalibrationResult:
    """Re-generalize under-performing / relinquished claim kinds from the ledger.

    **Temperature** (always) and **gate-mode precip** (run 10): read the kind's
    recent bets; if its law fell off ``standing_laws`` or recent accuracy is below
    ``target``, step its *selectivity* knob toward a less-falsifiable shape (band
    wider / PoP-gate higher, each capped) and re-seed a fallen law. Deterministic;
    a no-op when every kind meets target and stands.

    **Calibrated-mode precip** (run 11, ``precip_mode="calibrated"``): the precip
    arm bets *both directions* around ``pop_cut`` — the knob is a *calibration*
    knob, not a selectivity gate. Move the cut toward the observed 0.5-crossing:
    if recent **wet** bets (``(precip …)``) lose more than half (rain rarer than
    the cut assumes) raise the cut (bet wet less, dry more); if recent **dry**
    bets (``(dry …)``) lose more than half (rain commoner) lower it. Re-seed either
    precip law (wet / dry) if it fell. Because a rising cut shifts bets to the
    *majority* (dry) outcome, this arm can **recover to a positive net** — the
    recovery the selectivity gate structurally cannot reach (RUN_10_LOG F1¹⁰).
    """
    result = RecalibrationResult(
        band_width=band_width, pop_threshold=pop_threshold, pop_cut=pop_cut)

    bets = [e for e in ledger.entries if _kind_of(e.claim_egif) is not None]

    # -- temperature (unchanged) ------------------------------------------------
    temp_bets = [e for e in bets if _kind_of(e.claim_egif) == "temp"]
    if temp_bets:
        recent = temp_bets[-window:]
        acc = _acc(recent)
        standing = _law_standing(LAW_TEMP, standing_laws)
        if not (standing and (acc is None or acc >= target)):
            new = min(band_cap, result.band_width + band_step)
            stepped = new != result.band_width
            result.band_width = new
            if not standing:
                result.reseed_laws.append(LAW_TEMP)
            acc_s = "n/a" if acc is None else f"{acc:.2f}"
            result.notes.append(
                f"temp: acc={acc_s} standing={standing} "
                f"-> {'widened' if stepped else ''}"
                f"{' reseed' if not standing else ''}".strip())

    # -- precipitation ----------------------------------------------------------
    precip_bets = [e for e in bets if _kind_of(e.claim_egif) == "precip"]
    if precip_mode == "calibrated":
        _recalibrate_precip_calibrated(
            result, precip_bets, standing_laws, window, cut_step, pop_cap)
    elif precip_bets:
        recent = precip_bets[-window:]
        acc = _acc(recent)
        standing = _law_standing(LAW_PRECIP, standing_laws)
        if not (standing and (acc is None or acc >= target)):
            new = min(pop_cap, result.pop_threshold + pop_step)
            stepped = new != result.pop_threshold
            result.pop_threshold = new
            if not standing:
                result.reseed_laws.append(LAW_PRECIP)
            acc_s = "n/a" if acc is None else f"{acc:.2f}"
            result.notes.append(
                f"precip: acc={acc_s} standing={standing} "
                f"-> {'raised-pop' if stepped else ''}"
                f"{' reseed' if not standing else ''}".strip())

    result.changed = bool(result.reseed_laws) or (
        result.band_width != band_width
        or result.pop_threshold != pop_threshold
        or result.pop_cut != pop_cut)
    return result


def _recalibrate_precip_calibrated(
    result: RecalibrationResult,
    precip_bets,
    standing_laws: Sequence[str],
    window: int,
    cut_step: int,
    pop_cap: int,
) -> None:
    """The calibrated precip cutpoint controller (run 11) — mutates ``result``."""
    recent = precip_bets[-window:]
    if not recent:
        return
    wet = [e for e in recent if e.claim_egif.lstrip().startswith("(precip")]
    dry = [e for e in recent if e.claim_egif.lstrip().startswith("(dry")]
    acc_wet, acc_dry = _acc(wet), _acc(dry)

    moved = ""
    # Move the cut toward the observed 0.5-crossing (bounded [0, 100]). Wet losses
    # → cut too low (rain rarer than assumed) → raise. Dry losses → cut too high
    # (rain commoner) → lower. Wet takes precedence when both under-perform.
    if acc_wet is not None and acc_wet < 0.5:
        new = min(pop_cap, result.pop_cut + cut_step)
        if new != result.pop_cut:
            result.pop_cut, moved = new, "cut-up"
    elif acc_dry is not None and acc_dry < 0.5:
        new = max(0, result.pop_cut - cut_step)
        if new != result.pop_cut:
            result.pop_cut, moved = new, "cut-down"

    # Re-seed either precip law if the world relinquished it.
    reseeded = []
    for law, name in ((LAW_PRECIP, "wet"), (LAW_PRECIP_DRY, "dry")):
        if not _law_standing(law, standing_laws):
            result.reseed_laws.append(law)
            reseeded.append(name)

    if moved or reseeded:
        aw = "n/a" if acc_wet is None else f"{acc_wet:.2f}"
        ad = "n/a" if acc_dry is None else f"{acc_dry:.2f}"
        note = f"precip[cal]: acc_wet={aw} acc_dry={ad} cut={result.pop_cut}"
        if moved:
            note += f" -> {moved}"
        if reseeded:
            note += f" reseed:{'+'.join(reseeded)}"
        result.notes.append(note)


__all__ = ["RecalibrationResult", "recalibrate"]
