"""
A DLCore benchmark harness — score Arisbe's reasoning against gold labels.

Runs a suite of DLCore tasks (subsumption / instance / consistency) through
``dl_reasoning`` and scores each against a 2-valued gold label, with the scoring a
*fragment-bounded* reasoner deserves:

* **correct**   — Arisbe decided (YES/NO) and matches gold.
* **wrong**     — Arisbe decided and *contradicts* gold.  This is the number that must
                  stay **zero**: a sound engine never asserts a YES/NO it cannot back.
* **abstained** — Arisbe answered UNKNOWN / UNSUPPORTED / OUT_OF_SIGNATURE where gold is
                  decided.  Not an error — it is *coverage* the bounded fragment doesn't
                  reach, reported honestly rather than guessed.

So the two headline numbers are **soundness** (1 − wrong/decided; must be 1.0) and
**coverage** (decided/total).  Reporting them separately is the honest way to put a
bounded, three-valued engine beside a full-DL benchmark like DL-ReasonSuite's DLCore —
where the gold is cross-checked by HermiT + Pellet — instead of a single accuracy number
that would silently conflate "wrong" with "didn't try".

Task schema (one JSON object per task)::

    {"id": "...", "ontology_egif": "<EGIF of M>", "task": "subsumption",
     "sub": "Dog", "sup": "Animal", "expected": "yes"}            # subsumption
    {"id": "...", "ontology_egif": "...", "task": "instance",
     "individual": "Rex", "cls": "Animal", "expected": "yes"}     # instance
    {"id": "...", "ontology_egif": "...", "task": "consistency",
     "expected": "yes"}                                            # consistency (yes = consistent)

``expected`` is ``"yes"`` / ``"no"`` (2-valued gold).  ``ontology_egif`` may be replaced by
``ontology_ref`` (a corpus UoD id) to run against a stored ontology; the DL-ReasonSuite
adapter (mapping its OWL-DL task files into this schema) is a thin layer to add once the
dataset files are in hand — the harness itself is dataset-independent.

Usage::

    uv run python tools/dl_benchmark.py tasks.json          # run a suite, print the report
    uv run python tools/dl_benchmark.py --self-test          # run the built-in demo suite
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from egif_parser_dau import parse_egif

from dl_reasoning import (
    DLAnswer,
    DLResult,
    check_consistency,
    check_instance,
    check_subsumption,
)

_DECIDED = {DLAnswer.YES, DLAnswer.NO}
_GOLD = {"yes": DLAnswer.YES, "no": DLAnswer.NO}


@dataclass
class Scored:
    task_id: str
    task: str
    query: str
    expected: str
    answer: str
    bucket: str          # "correct" | "wrong" | "abstained"
    detail: str = ""


@dataclass
class SuiteReport:
    scored: List[Scored] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.scored)

    @property
    def correct(self) -> int:
        return sum(1 for s in self.scored if s.bucket == "correct")

    @property
    def wrong(self) -> int:
        return sum(1 for s in self.scored if s.bucket == "wrong")

    @property
    def abstained(self) -> int:
        return sum(1 for s in self.scored if s.bucket == "abstained")

    @property
    def decided(self) -> int:
        return self.correct + self.wrong

    @property
    def soundness(self) -> float:
        """Among the answers Arisbe decided, the fraction it got right (target: 1.0)."""
        return 1.0 if self.decided == 0 else self.correct / self.decided

    @property
    def coverage(self) -> float:
        """Fraction of tasks Arisbe decided at all (the fragment's reach)."""
        return 0.0 if self.total == 0 else self.decided / self.total

    def summary(self) -> str:
        return (f"{self.total} tasks · {self.correct} correct · {self.wrong} wrong · "
                f"{self.abstained} abstained | soundness {self.soundness:.0%} · "
                f"coverage {self.coverage:.0%}")


def _resolve_ontology(task: Dict[str, Any]):
    if task.get("ontology_egif") is not None:
        return parse_egif(task["ontology_egif"])
    ref = task.get("ontology_ref")
    if ref:
        from tomos_service import TomosService
        tomos = TomosService(Path(__file__).parent.parent / "tomos")
        from egif_generator_dau import generate_egif
        uod = tomos.load_uod(ref, attest=False)
        if uod is None or uod.current_egi is None:
            raise ValueError(f"ontology_ref '{ref}' not found / empty")
        return parse_egif(generate_egif(uod.current_egi))
    raise ValueError("task needs ontology_egif or ontology_ref")


def run_task(task: Dict[str, Any]) -> Scored:
    theory = _resolve_ontology(task)
    kind = task["task"]
    if kind == "subsumption":
        r = check_subsumption(theory, task["sub"], task["sup"])
    elif kind == "instance":
        r = check_instance(theory, task["individual"], task["cls"])
    elif kind == "consistency":
        r = check_consistency(theory)
    else:
        raise ValueError(f"unknown task type {kind!r}")

    expected = (task.get("expected") or "").lower()
    bucket = _score(r, expected)
    return Scored(task_id=str(task.get("id", "")), task=kind, query=r.query or kind,
                  expected=expected, answer=r.answer.value, bucket=bucket, detail=r.detail)


def _score(r: DLResult, expected: str) -> str:
    if r.answer not in _DECIDED:
        return "abstained"
    gold = _GOLD.get(expected)
    if gold is None:            # no/garbled gold → can't score as right/wrong
        return "abstained"
    return "correct" if r.answer is gold else "wrong"


def run_suite(tasks: List[Dict[str, Any]]) -> SuiteReport:
    report = SuiteReport()
    for task in tasks:
        try:
            report.scored.append(run_task(task))
        except Exception as exc:               # a malformed task abstains, loudly
            report.scored.append(Scored(
                task_id=str(task.get("id", "")), task=str(task.get("task", "?")),
                query="(error)", expected=str(task.get("expected", "")),
                answer="error", bucket="abstained", detail=f"{type(exc).__name__}: {exc}"))
    return report


# A built-in demo suite — sound answers across the truth table, plus an abstain.
SELF_TEST_TASKS: List[Dict[str, Any]] = [
    {"id": "sub-trans", "task": "subsumption", "sub": "Dog", "sup": "Animal",
     "expected": "yes",
     "ontology_egif": "~[ (Dog *x) ~[ (Mammal x) ] ] ~[ (Mammal *y) ~[ (Animal y) ] ]"},
    {"id": "sub-no", "task": "subsumption", "sub": "Animal", "sup": "Dog",
     "expected": "no",
     "ontology_egif": "~[ (Dog *x) ~[ (Mammal x) ] ] ~[ (Mammal *y) ~[ (Animal y) ] ]"},
    {"id": "inst-yes", "task": "instance", "individual": "Rex", "cls": "Animal",
     "expected": "yes",
     "ontology_egif": '(Dog "Rex") ~[ (Dog *x) ~[ (Mammal x) ] ] ~[ (Mammal *y) ~[ (Animal y) ] ]'},
    {"id": "con-yes", "task": "consistency", "expected": "yes",
     "ontology_egif": '(Dog "Rex") ~[ (Cat *x) (Dog x) ]'},
    {"id": "con-no", "task": "consistency", "expected": "no",
     "ontology_egif": '(Cat "Rex") (Dog "Rex") ~[ (Cat *x) (Dog x) ]'},
    {"id": "sub-abstain", "task": "subsumption", "sub": "A", "sup": "B", "expected": "yes",
     "ontology_egif": "~[ (A *x) ~[ ~[ (B x) ] ~[ (C x) ] ] ]"},   # non-Horn → UNKNOWN
]


def _print_report(report: SuiteReport) -> None:
    print(report.summary())
    print("-" * 72)
    for s in report.scored:
        mark = {"correct": "✓", "wrong": "✗", "abstained": "·"}[s.bucket]
        print(f"  {mark} [{s.task:12}] {s.query:28} gold={s.expected:4} "
              f"→ {s.answer:16} {s.detail}")
    if report.wrong:
        print(f"\n⚠ {report.wrong} WRONG answer(s) — a soundness bug, investigate.")


def main(argv: List[str]) -> int:
    if not argv or argv[0] == "--self-test":
        report = run_suite(SELF_TEST_TASKS)
        _print_report(report)
        return 1 if report.wrong else 0
    tasks = json.loads(Path(argv[0]).read_text())
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    report = run_suite(tasks)
    _print_report(report)
    return 1 if report.wrong else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
