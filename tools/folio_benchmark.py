"""
FOLIO benchmark harness — score Arisbe's Z3 entailment against FOLIO's gold labels.

Runs FOLIO examples (``premises-FOL`` + ``conclusion-FOL`` → ``label``) through
``folio_fol.decide_entailment`` and reports the metrics a 3-valued NL-reasoning benchmark
deserves:

* **accuracy** — predicted verdict == gold, over all examples;
* **parse coverage** — fraction whose FOL Arisbe could read (the rest are ``Unparsed`` and
  abstained, never guessed — human-authored FOL has occasional malformations: comma-as-
  conjunction, decimal constants, unbalanced parens);
* a **gold × predicted confusion** table and a sample of disagreements.

Unlike the DLCore harness, a "wrong" here is not necessarily a soundness bug: FOLIO's gold is
human-authored and a few items are genuinely debatable, or hinge on a quantifier-scope reading
the surface FOL leaves ambiguous. Accuracy against gold (the standard FOLIO metric) is the
honest number; the disagreements are worth reading, not hiding.

The dataset is NOT vendored. Point ``--data`` at a FOLIO checkout's jsonl
(e.g. ``…/FOLIO/data/v0.0/folio-validation.jsonl``).

Usage::

    uv run python tools/folio_benchmark.py --data <FOLIO>/data/v0.0/folio-validation.jsonl
    uv run python tools/folio_benchmark.py --data … --limit 50
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from folio_fol import FolioParseError, decide_entailment, folio_fol_to_egi

_GOLD = {"True", "False", "Uncertain"}


# ---------------------------------------------------------------------------
# Fidelity: FOLIO FOL → EG (the picture), and the linear↔graphical round-trip
# ---------------------------------------------------------------------------

@dataclass
class FidelityReport:
    total: int = 0           # FOL formulas seen
    built: int = 0           # became an EGI (the drawable picture)
    roundtrip: int = 0       # egi → CLIF → egi recovered the same graph
    parse_fail: int = 0
    build_fail: int = 0

    @property
    def build_rate(self) -> float:
        return 0.0 if not self.total else self.built / self.total

    @property
    def roundtrip_rate(self) -> float:
        return 0.0 if not self.built else self.roundtrip / self.built


def run_fidelity(examples: List[dict]) -> FidelityReport:
    """Build every FOL formula's EG and test the egi→CLIF→egi round-trip (same_graph).

    The round-trip is exact for the EG-native connectives (∧ ¬ → ∀ ∃); ∨/↔/⊕ expand to
    De Morgan cuts the generator re-emits equivalently-but-not-identically, so they build
    but may not round-trip — reported, not hidden."""
    from clif_generator_dau import generate_clif
    from clif_parser_dau import parse_clif
    from eg_navigation import same_graph

    rep = FidelityReport()
    for ex in examples:
        fols = list(ex.get("premises-FOL") or [])
        if ex.get("conclusion-FOL"):
            fols.append(ex["conclusion-FOL"])
        for fol in fols:
            if not fol.strip():
                continue
            rep.total += 1
            try:
                egi = folio_fol_to_egi(fol)
            except FolioParseError:
                rep.parse_fail += 1
                continue
            except Exception:
                rep.build_fail += 1
                continue
            rep.built += 1
            try:
                if same_graph(egi, parse_clif(generate_clif(egi))):
                    rep.roundtrip += 1
            except Exception:
                pass
    return rep


def _print_fidelity(rep: FidelityReport) -> None:
    print(f"{rep.total} FOL formulas · built {rep.built} ({rep.build_rate:.1%}) · "
          f"round-trip {rep.roundtrip} ({rep.roundtrip_rate:.1%} of built)")
    print(f"  parse failures: {rep.parse_fail} · build failures: {rep.build_fail}")
    print("  (round-trip is exact for EG-native ∧¬→∀∃; ∨/↔/⊕ build but expand to "
          "De Morgan cuts that re-emit equivalently, not identically)")


@dataclass
class FolioReport:
    rows: List[dict] = field(default_factory=list)   # {gold, pred, parsed, story_id}

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def parsed(self) -> int:
        return sum(1 for r in self.rows if r["parsed"])

    @property
    def correct(self) -> int:
        return sum(1 for r in self.rows if r["pred"] == r["gold"])

    @property
    def wrong(self) -> int:
        return sum(1 for r in self.rows if r["parsed"] and r["pred"] in _GOLD and r["pred"] != r["gold"])

    @property
    def accuracy(self) -> float:
        return 0.0 if not self.total else self.correct / self.total

    @property
    def parse_coverage(self) -> float:
        return 0.0 if not self.total else self.parsed / self.total

    def confusion(self) -> Counter:
        return Counter((r["gold"], r["pred"]) for r in self.rows)


def run_folio(examples: List[dict], *, timeout_ms: int = 5000) -> FolioReport:
    report = FolioReport()
    for ex in examples:
        gold = ex.get("label", "")
        r = decide_entailment(ex.get("premises-FOL") or [], ex.get("conclusion-FOL") or "",
                              timeout_ms=timeout_ms)
        report.rows.append({"gold": gold, "pred": r.verdict, "parsed": r.parsed,
                            "story_id": ex.get("story_id", ex.get("example_id", ""))})
    return report


def run_native(examples: List[dict], *, cross_check: bool = True,
               timeout_ms: int = 5000) -> FolioReport:
    """Decide FOLIO with Arisbe's **own** bounded engine (the soundness×coverage half).

    Soundness must be measured against the **FOL semantics**, not FOLIO's (occasionally
    noisy) gold label — so every *decided* verdict is cross-checked against the authoritative
    Z3 verdict (the complete oracle).  A native verdict that disagrees with gold but *agrees*
    with Z3 is gold-noise, not an engine error."""
    from folio_native import decide_native
    from folio_fol import Z3_AVAILABLE, decide_entailment
    report = FolioReport()
    for ex in examples:
        prem, concl = ex.get("premises-FOL") or [], ex.get("conclusion-FOL") or ""
        r = decide_native(prem, concl)
        z3 = ""
        if cross_check and Z3_AVAILABLE and r.verdict in _GOLD:
            z3 = decide_entailment(prem, concl, timeout_ms=timeout_ms).verdict
        report.rows.append({"gold": ex.get("label", ""), "pred": r.verdict,
                            "parsed": r.parsed, "z3": z3,
                            "story_id": ex.get("story_id", ex.get("example_id", ""))})
    return report


def _print_native(report: FolioReport) -> None:
    """Soundness×coverage, the way a *bounded* reasoner deserves (cf. dl_benchmark):
    abstentions (``Unknown``) are coverage the fragment doesn't reach, NOT errors — and
    soundness is judged against the FOL semantics (Z3), so noisy gold is not counted as error."""
    decided_rows = [r for r in report.rows if r["pred"] in _GOLD]
    decided = len(decided_rows)
    coverage = 0.0 if not report.total else decided / report.total
    # Soundness vs the complete oracle (Z3): of the decided rows we cross-checked, how many
    # agree with Z3.  This is the real soundness — the gold label may itself be wrong.
    checked = [r for r in decided_rows if r["z3"] in _GOLD]
    sound_vs_z3 = sum(1 for r in checked if r["pred"] == r["z3"])
    # vs gold: agreement, and the disagreements split into Z3-corroborated (gold-noise) vs real.
    correct_gold = sum(1 for r in decided_rows if r["pred"] == r["gold"])
    gold_disagree = [r for r in decided_rows if r["pred"] != r["gold"]]
    gold_noise = [r for r in gold_disagree if r["z3"] == r["pred"]]   # Z3 backs native
    real_errors = [r for r in gold_disagree if r["z3"] in _GOLD and r["z3"] != r["pred"]]

    print(f"{report.total} examples · Arisbe's bounded engine (Horn materializer + "
          f"freeze-witness + denial check + case-split + model construction)")
    if checked:
        print(f"  SOUNDNESS vs Z3 {sound_vs_z3/len(checked):.1%} "
              f"({sound_vs_z3}/{len(checked)} decided agree with the complete oracle) · "
              f"COVERAGE {coverage:.1%} ({decided}/{report.total} decided)")
    else:
        print(f"  COVERAGE {coverage:.1%} ({decided}/{report.total} decided)")
    print(f"  vs gold: {correct_gold}/{decided} match; {len(gold_noise)} disagree but Z3 "
          f"corroborates native (gold-noise); {len(real_errors)} genuine error(s)")
    print(f"  (abstained on {report.total - decided} — residue beyond the engine's bound)")
    print("-" * 64)
    labels = ["True", "False", "Uncertain", "Unknown", "Unparsed"]
    conf = report.confusion()
    for g in ["True", "False", "Uncertain"]:
        gc = sum(1 for r in report.rows if r["gold"] == g)
        if not gc:
            continue
        print(f"  gold {g:>10} ({gc:>3}): " +
              " ".join(f"{p}={conf.get((g, p), 0)}" for p in labels))
    if real_errors:
        print(f"\n  ⚠ {len(real_errors)} UNSOUND verdict(s) — native disagrees with BOTH gold "
              f"and Z3:")
        for r in real_errors[:8]:
            print(f"     gold {r['gold']:>9} · z3 {r['z3']:>9} → native {r['pred']:<9} "
                  f"{r['story_id']}")
    elif gold_noise:
        print(f"\n  ✓ all {len(gold_noise)} gold-disagreement(s) corroborated by Z3 "
              f"(noisy gold labels, not engine errors):")
        for r in gold_noise[:8]:
            print(f"     gold {r['gold']:>9} · z3 {r['z3']:>9} = native {r['pred']:<9} "
                  f"{r['story_id']}")


def _print(report: FolioReport) -> None:
    print(f"{report.total} examples · accuracy {report.accuracy:.1%} "
          f"({report.correct}/{report.total}) · parse coverage {report.parse_coverage:.1%} "
          f"· {report.wrong} disagreements among decided")
    print("-" * 64)
    labels = ["True", "False", "Uncertain", "Unparsed", "Unknown"]
    conf = report.confusion()
    golds = ["True", "False", "Uncertain"]
    print(f"{'gold \\ pred':>12} " + " ".join(f"{p:>9}" for p in labels))
    for g in golds:
        print(f"{g:>12} " + " ".join(f"{conf.get((g, p), 0):>9}" for p in labels))
    # Per-label recall (correct / gold-count).
    print("-" * 64)
    for g in golds:
        gc = sum(1 for r in report.rows if r["gold"] == g)
        rc = sum(1 for r in report.rows if r["gold"] == g and r["pred"] == g)
        if gc:
            print(f"  recall[{g}] = {rc}/{gc} = {rc/gc:.0%}")
    # A few disagreements (decided but wrong) for inspection.
    bad = [r for r in report.rows if r["parsed"] and r["pred"] in _GOLD and r["pred"] != r["gold"]]
    if bad:
        print(f"\nsample disagreements (gold → pred):")
        for r in bad[:8]:
            print(f"   {r['gold']:>9} → {r['pred']:<9} {r['story_id']}")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Score FOLIO entailment via Arisbe's Z3 verdict.")
    ap.add_argument("--data", required=True, help="path to a FOLIO jsonl split")
    ap.add_argument("--limit", type=int, default=None, help="cap examples")
    ap.add_argument("--timeout-ms", type=int, default=5000)
    ap.add_argument("--fidelity", action="store_true",
                    help="instead of entailment, report FOL→EG build + round-trip fidelity")
    ap.add_argument("--native", action="store_true",
                    help="decide with Arisbe's own bounded engine (soundness×coverage) "
                         "instead of the authoritative Z3 verdict")
    args = ap.parse_args(argv)

    examples = [json.loads(l) for l in Path(args.data).read_text().splitlines() if l.strip()]
    if args.limit:
        examples = examples[: args.limit]
    if args.fidelity:
        _print_fidelity(run_fidelity(examples))
    elif args.native:
        _print_native(run_native(examples))
    else:
        _print(run_folio(examples, timeout_ms=args.timeout_ms))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
