"""The ledger of known failures and the pinned extents (spec 2026-09-10 §6).

Ledger: every failing instance must belong to an entry (else NEW), and every
evaluated instance in an entry must still fail (else SHRINK) — so the ledger
can only shrink by someone deciding it should. Extent: every count a layer
covered is pinned with ==; CALCULUS_EXTENT_WRITE=1 rewrites the pins, and the
diff is then read and committed deliberately.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Set

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "calculus_ledger.json"
EXTENT = HERE / "calculus_extent.json"


@dataclass(frozen=True)
class Failure:
    layer: str
    key: str
    detail: str


def _sig(g, x, sigs) -> str:
    if x == g.sheet:
        return "SHEET"
    vs, es, cs = sigs
    for table in (vs, es, cs):
        if x in table:
            return repr(table[x])
    return f"?{x}"


def instance_key(tier: str, gname: str, g, m, sigs) -> str:
    """UUID-independent: the move's elements by canonical signature. Truly
    symmetric moves share a key, which is intended — they are one move."""
    parts = (m.rule, sorted(_sig(g, x, sigs) for x in m.selection),
             None if m.target is None else _sig(g, m.target, sigs), m.content,
             sorted((_sig(g, e, sigs), i) for e, i in m.hooks))
    return f"{tier}|{gname}|{m.rule}|{hashlib.sha256(repr(parts).encode()).hexdigest()[:12]}"


def _entries() -> List[dict]:
    entries = json.loads(LEDGER.read_text())["entries"]
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), "ledger entry ids must be unique"
    for e in entries:
        assert e.get("reason", "").strip(), f"ledger entry {e['id']!r} has no reason"
        assert set(e) == {"id", "layer", "rule", "reason", "instances"}, f"{e['id']!r}: bad fields"
    return entries


def ledgered(layer: str) -> Set[str]:
    return {k for e in _entries() if e["layer"] == layer for k in e["instances"]}


def check_ledger(layer: str, evaluated_ledgered: Set[str], failures: List[Failure]) -> List[str]:
    entries = [e for e in _entries() if e["layer"] == layer]
    known = {k for e in entries for k in e["instances"]}
    failing = {f.key for f in failures}
    problems = []
    new = [f for f in failures if f.key not in known]
    if new:
        problems.append(f"{len(new)} NEW failure(s) in layer {layer!r} (first 20):\n"
                        + "\n".join(f"  {f.key}  {f.detail}" for f in new[:20]))
        dump = os.environ.get("CALCULUS_LEDGER_DUMP")
        if dump:
            Path(f"{dump}.{layer}.json").write_text(json.dumps([asdict(f) for f in new], indent=1))
    for e in entries:
        stale = sorted(k for k in e["instances"] if k in evaluated_ledgered and k not in failing)
        if stale:
            problems.append(f"entry {e['id']!r}: {len(stale)} instance(s) no longer fail — "
                            f"shrink this entry: {stale[:5]}")
    return problems


def assert_extent(name: str, extent: dict) -> None:
    pins = json.loads(EXTENT.read_text())
    if os.environ.get("CALCULUS_EXTENT_WRITE") == "1":
        pins[name] = extent
        EXTENT.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n")
        return
    assert name in pins, f"no pinned extent for {name!r}: run once with CALCULUS_EXTENT_WRITE=1, read the diff"
    assert pins[name] == extent, f"the extent of {name!r} moved:\n  pinned {pins[name]}\n  now    {extent}"


def draft(dump_file: str) -> None:
    """Group a dumped NEW-failure file into draft entries (reasons left blank —
    _entries() refuses a blank reason, so each must be written, with its Dau page)."""
    groups = defaultdict(list)
    for f in json.loads(Path(dump_file).read_text()):
        rule = f["key"].split("|")[2]
        groups[(f["layer"], rule, f["detail"][:48])].append(f["key"])
    out = [{"id": f"{layer}-{rule}-{i}".lower(), "layer": layer, "rule": rule,
            "reason": "", "instances": sorted(keys), "_sample_detail": d}
           for i, ((layer, rule, d), keys) in enumerate(sorted(groups.items()))]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    draft(sys.argv[1])
