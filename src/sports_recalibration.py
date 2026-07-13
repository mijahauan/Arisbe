"""
Sports re-generalization — the run-12 calibration controller (the F1¹¹ mechanism
transplanted to a **discrete** domain).

The weather trilogy's knob-type law (``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §11.4):
a refuted theory re-generalizes into a better one only if its recalibration knob
**calibrates** (moves it toward being right), not merely selects (moves it toward
betting less). Run 12's manufactured knob is arm B's **cutpoint on win-percentage
differential** (integer thousandths, ``sports_source``): at/above the cut the arm
picks the favorite (``pick_fav`` → ``win_fav``), below it the underdog
(``pick_dog`` → ``win_dog``) — the wet/dry two-direction shape. This controller
reads the :class:`resolving_membrane.PredictionLedger` and moves the cut toward the
observed 0.5-crossing:

- **favorite bets losing more than half** → the cut is too low (the arm trusts
  small edges that don't cash) → raise it (bet the favorite only on bigger edges,
  the underdog more);
- **underdog bets losing more than half** → the cut is too high (favorites win
  even at small edges) → lower it (bet the favorite more).

Fallen arm-B laws (either direction) are re-seeded so the arm bets again — the
``reseed_laws`` runner seam, unchanged. Two register-keeping rules ride along:

- **Arm C's rivals are held** — a fallen :data:`sports_source.HELD_LAWS` law
  (home-wins / higher-win-pct-wins) is re-seeded *verbatim*, because the selection
  register's instrument is the ledger (``select_best`` over track records), not law
  standing. Holding is not calibration: nothing about the rival's claim moves.
- **Arm A is never touched** — the knob-type null (``LAW_NAIVE``) has no knob and
  no reseed; its trap/silence is the run's control reading (P1¹²).

Pure, deterministic, LLM-free, network-free — a function of the ledger + the
current cut + the standing laws, mirroring ``weather_recalibration.recalibrate``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from sports_source import HELD_LAWS, LAW_DOG, LAW_FAV


@dataclass
class RecalibrationResult:
    """The recalibrated cut + the laws to re-seed into M. ``changed`` is True iff
    the cut moved or a law is being re-seeded — the driver only mutates the source /
    runner when something actually changed, so a healthy segment is a no-op."""
    cut: int
    reseed_laws: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    changed: bool = False


def _kind_of(claim_egif: str) -> Optional[str]:
    """The arm-B direction of a *resolution* entry (``fav`` | ``dog``), or None for
    every other claim (raise-phase picks, rival/naive resolutions)."""
    s = claim_egif.lstrip()
    if s.startswith("(win_fav"):
        return "fav"
    if s.startswith("(win_dog"):
        return "dog"
    return None


def _law_standing(law: str, standing_laws: Sequence[str]) -> bool:
    """Whether ``law`` is still on M (structural, tolerant of reformatting —
    the ``weather_recalibration`` rule, self-contained per controller)."""
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
    cut: int,
    standing_laws: Sequence[str],
    window: int = 30,
    cut_step: int = 25,
    cut_cap: int = 300,
    hold_laws: Optional[Sequence[str]] = None,
) -> RecalibrationResult:
    """Move arm B's cut toward the observed 0.5-crossing and re-seed fallen laws
    (see module docstring). ``hold_laws`` (default :data:`sports_source.HELD_LAWS`)
    are arm C's rivals, re-seeded verbatim when fallen. Deterministic; a no-op when
    the cut holds and every reseedable law stands. The cut is bounded
    ``[0, cut_cap]`` — settling at 0 (*always the favorite*) is a genuine
    calibration endpoint in this domain, not a ratchet artifact; the digest's cut
    trajectory is what discriminates (F3¹¹)."""
    result = RecalibrationResult(cut=cut)
    hold = HELD_LAWS if hold_laws is None else list(hold_laws)

    cal_bets = [e for e in ledger.entries if _kind_of(e.claim_egif) is not None]
    recent = cal_bets[-window:]
    fav = [e for e in recent if _kind_of(e.claim_egif) == "fav"]
    dog = [e for e in recent if _kind_of(e.claim_egif) == "dog"]
    acc_fav, acc_dog = _acc(fav), _acc(dog)

    moved = ""
    # Favorite losses take precedence when both directions under-perform (the
    # run-11 wet-precedence rule, transplanted).
    if acc_fav is not None and acc_fav < 0.5:
        new = min(cut_cap, result.cut + cut_step)
        if new != result.cut:
            result.cut, moved = new, "cut-up"
    elif acc_dog is not None and acc_dog < 0.5:
        new = max(0, result.cut - cut_step)
        if new != result.cut:
            result.cut, moved = new, "cut-down"

    # Re-seed arm B's fallen direction(s) — the knob's reseed contract.
    reseeded = []
    for law, name in ((LAW_FAV, "fav"), (LAW_DOG, "dog")):
        if not _law_standing(law, standing_laws):
            result.reseed_laws.append(law)
            reseeded.append(name)

    if moved or reseeded:
        af = "n/a" if acc_fav is None else f"{acc_fav:.2f}"
        ad = "n/a" if acc_dog is None else f"{acc_dog:.2f}"
        note = f"cal: acc_fav={af} acc_dog={ad} cut={result.cut}"
        if moved:
            note += f" -> {moved}"
        if reseeded:
            note += f" reseed:{'+'.join(reseeded)}"
        result.notes.append(note)

    # Hold arm C's rivals: a fallen rival is re-asserted verbatim so the world
    # keeps scoring its ledger (selection needs continued betting). LAW_NAIVE is
    # deliberately not in any reseed path — arm A's trap/silence is the control.
    held = [law for law in hold if not _law_standing(law, standing_laws)]
    if held:
        result.reseed_laws.extend(held)
        result.notes.append(f"held rivals reseeded: {len(held)}")

    result.changed = bool(result.reseed_laws) or result.cut != cut
    return result


__all__ = ["RecalibrationResult", "recalibrate"]
