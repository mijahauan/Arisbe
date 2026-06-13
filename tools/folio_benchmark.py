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

from folio_fol import decide_entailment

_GOLD = {"True", "False", "Uncertain"}


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
    args = ap.parse_args(argv)

    examples = [json.loads(l) for l in Path(args.data).read_text().splitlines() if l.strip()]
    if args.limit:
        examples = examples[: args.limit]
    report = run_folio(examples, timeout_ms=args.timeout_ms)
    _print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
