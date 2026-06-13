"""
DL-ReasonSuite adapter — run its DLCore tasks through Arisbe's `dl_reasoning`.

DL-ReasonSuite (Oluçoğlu et al., *Applied Sciences* 2026; github.com/okanss/DL-ReasonSuite)
ships DLCore as three JSONL task files over Turtle ontologies in two buckets — ``el``
(OWL-RL profile) and ``dl`` (fuller DL). Each task is one of:

    subsumption   query {c, d}  → "entailed" / "not_entailed"   (C ⊑ D?)
    instance_check query {a, c} → "entailed" / "not_entailed"   (a : C?)
    consistency   ask CONSISTENCY → "consistent" / "inconsistent"

This adapter is the only DL-ReasonSuite-specific layer: it imports each ontology once
(rdflib Turtle → EGI, cached), maps the query IRIs to the local names Arisbe uses, dispatches
to ``check_subsumption`` / ``check_instance`` / ``check_consistency``, and scores with the
harness's fragment-honest buckets (`dl_benchmark`). The result is a **soundness × coverage**
map per (bucket, task) — soundness must be 1.0 (Arisbe never asserts a wrong YES/NO); coverage
is how far the bounded fragment reaches. The ``dl`` bucket is expected to abstain more than
``el`` (fuller DL is outside the fragment) — that boundary, reported, *is* the result.

The dataset is NOT vendored into Arisbe (external, ~3620 tasks). Point ``--suite-dir`` at a
DL-ReasonSuite checkout's ``dl-reason-suite/`` directory.

Usage::

    uv run python tools/dl_reasonsuite.py --suite-dir /path/to/dl-reason-suite
    uv run python tools/dl_reasonsuite.py --suite-dir … --limit 40        # sample per (bucket,task)
    uv run python tools/dl_reasonsuite.py --suite-dir … --bucket el --task subsumption --full
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from domain_model_importer import from_rdf_file

from dl_benchmark import Scored, SuiteReport, _score
from dl_reasoning import check_consistency, check_instance, check_subsumption

# DL-ReasonSuite gold vocabulary → the harness's 2-valued gold.
GOLD = {"entailed": "yes", "not_entailed": "no",
        "consistent": "yes", "inconsistent": "no"}

TASK_FILES = {
    "subsumption": "tasks/dl-core/subsumption.jsonl",
    "instance_check": "tasks/dl-core/instance_check.jsonl",
    "consistency": "tasks/dl-core/consistency.jsonl",
}


def local_name(iri: str) -> str:
    """The local fragment Arisbe imports an IRI as (after '#', else last path segment)."""
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


class _OntologyCache:
    """Import each Turtle ontology once (the expensive step) and reuse the EGI."""

    def __init__(self, suite_dir: Path):
        self.suite_dir = suite_dir
        self._egis: Dict[str, object] = {}

    def egi(self, ontology_path: str):
        if ontology_path not in self._egis:
            self._egis[ontology_path] = from_rdf_file(self.suite_dir / ontology_path).egi
        return self._egis[ontology_path]


def _run_one(task: dict, cache: _OntologyCache) -> Scored:
    egi = cache.egi(task["ontology_path"])
    kind = task["task_type"]
    q = task["query"]
    if kind == "subsumption":
        r = check_subsumption(egi, local_name(q["c"]), local_name(q["d"]))
    elif kind == "instance_check":
        r = check_instance(egi, local_name(q["a"]), local_name(q["c"]))
    elif kind == "consistency":
        r = check_consistency(egi)
    else:
        raise ValueError(f"unknown DLCore task_type {kind!r}")
    expected = GOLD.get(task["expected"]["label"], "")
    return Scored(task_id=task["id"], task=kind, query=r.query or kind,
                  expected=expected, answer=r.answer.value,
                  bucket=_score(r, expected), detail=r.detail)


def run_dlcore(
    suite_dir: Path,
    *,
    task_types: Tuple[str, ...] = ("subsumption", "instance_check", "consistency"),
    buckets: Tuple[str, ...] = ("el", "dl"),
    limit: Optional[int] = None,
) -> Dict[Tuple[str, str], SuiteReport]:
    """Run DLCore, grouped by (bucket, task_type). ``limit`` caps tasks per group."""
    cache = _OntologyCache(suite_dir)
    groups: Dict[Tuple[str, str], SuiteReport] = {}
    for kind in task_types:
        path = suite_dir / TASK_FILES[kind]
        per_group_count: Dict[str, int] = {}
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            task = json.loads(line)
            bucket = "el" if "/el/" in task["ontology_path"] else "dl"
            if bucket not in buckets:
                continue
            if limit is not None and per_group_count.get(bucket, 0) >= limit:
                continue
            per_group_count[bucket] = per_group_count.get(bucket, 0) + 1
            groups.setdefault((bucket, kind), SuiteReport()).scored.append(
                _run_one(task, cache))
    return groups


def _print(groups: Dict[Tuple[str, str], SuiteReport]) -> int:
    total_wrong = 0
    print(f"{'bucket/task':28} {'n':>5} {'correct':>8} {'wrong':>6} {'abst':>6} "
          f"{'sound':>7} {'cover':>7}")
    print("-" * 72)
    overall = SuiteReport()
    for (bucket, kind), rep in sorted(groups.items()):
        total_wrong += rep.wrong
        overall.scored.extend(rep.scored)
        print(f"{bucket + '/' + kind:28} {rep.total:>5} {rep.correct:>8} {rep.wrong:>6} "
              f"{rep.abstained:>6} {rep.soundness:>6.0%} {rep.coverage:>6.0%}")
    print("-" * 72)
    print(f"{'ALL':28} {overall.total:>5} {overall.correct:>8} {overall.wrong:>6} "
          f"{overall.abstained:>6} {overall.soundness:>6.0%} {overall.coverage:>6.0%}")
    if total_wrong:
        print(f"\n⚠ {total_wrong} WRONG answer(s) — a soundness bug; investigate before trusting coverage.")
        for (b, k), rep in sorted(groups.items()):
            for s in rep.scored:
                if s.bucket == "wrong":
                    print(f"   {b}/{k} {s.query} gold={s.expected} → {s.answer}: {s.detail}")
    return 1 if total_wrong else 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Run DL-ReasonSuite DLCore through Arisbe.")
    ap.add_argument("--suite-dir", required=True,
                    help="path to a DL-ReasonSuite checkout's dl-reason-suite/ directory")
    ap.add_argument("--limit", type=int, default=40,
                    help="max tasks per (bucket, task) group (default 40; --full overrides)")
    ap.add_argument("--full", action="store_true", help="run every task (ignore --limit)")
    ap.add_argument("--bucket", choices=["el", "dl"], action="append",
                    help="restrict to bucket(s) (default both)")
    ap.add_argument("--task", choices=list(TASK_FILES), action="append",
                    help="restrict to task type(s) (default all three)")
    args = ap.parse_args(argv)

    groups = run_dlcore(
        Path(args.suite_dir),
        task_types=tuple(args.task) if args.task else tuple(TASK_FILES),
        buckets=tuple(args.bucket) if args.bucket else ("el", "dl"),
        limit=None if args.full else args.limit,
    )
    return _print(groups)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
