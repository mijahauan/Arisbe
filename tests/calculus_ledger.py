"""The ledger of known failures and the pinned extents (spec 2026-09-10 §6).

Ledger: every failing instance must belong to an entry (else NEW), and every
evaluated instance in an entry must still fail (else SHRINK) — so the ledger
can only shrink by someone deciding it should. Instances are listed by kind in
the default mode; the exhaustive mode pins a count per (entry, kind) and lets
each entry's classifier (calculus_classifiers) decide membership, where a count
that rises fails as surely as one that falls. Extent: every count a layer
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
from typing import Dict, List, Set, Tuple

from calculus_rules import LIGATURE_RULES, expand

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "calculus_ledger.json"
EXTENT = HERE / "calculus_extent.json"


@dataclass(frozen=True)
class Failure:
    layer: str
    key: str
    detail: str
    claims: Tuple[str, ...] = ()      # the ledger entries whose classifier claims it

    @property
    def kind(self) -> str:
        from calculus_classifiers import failure_kind
        return failure_kind(self.layer, self.detail)


def _sig(g, x, sigs) -> str:
    if x == g.sheet:
        return "SHEET"
    vs, es, cs = sigs
    for table in (vs, es, cs):
        if x in table:
            return repr(table[x])
    return f"?{x}"


def _target(g, m, sigs):
    """The target signed jointly with its relation to the selection — signing
    it alone would merge IT+{c1}→c1 with IT+{c1}→c2 in ``~[ ] ~[ ]``."""
    if m.target is None:
        return None
    if m.target in m.selection:
        rel = "selected"
    elif m.target in expand(g, m.selection):
        rel = "inside-selection"
    else:
        rel = "outside"
    # Task 10: and which selected elements it encloses, at what depth — else
    # DC+{e1}→c1 (its own context) and DC+{e1}→c2 (a sibling) share a key in
    # ``~[ (p) ] ~[ (p) ]``.
    holds = sorted(("holds", chain.index(m.target), _sig(g, x, sigs))
                   for x in m.selection
                   for chain in [_enclosing(g, x) + [g.sheet]] if m.target in chain)
    return (_sig(g, m.target, sigs), rel, holds)


def _selection(g, sel, sigs, ordered=False):
    """The selection signed jointly: each element's signature together with
    its incidences to the OTHER selected elements — an edge's hooks onto them
    (position, signature), a vertex's places on them, a cut's containment of
    them (depth, signature) — so ``(P v1) (P v2)`` keeps ERA{e1,v1} (the edge
    with its own vertex) apart from ERA{e1,v2} (an edge and a stranger)."""
    S = set(sel)
    chains = {x: _enclosing(g, x) for x in S}
    out = []
    for x in (dict.fromkeys(sel) if ordered else S):
        rel = []
        for y in S - {x}:
            sy = _sig(g, y, sigs)
            rel += [("hook", i, sy) for i, w in enumerate(g.nu.get(x, ())) if w == y]
            rel += [("on", i, sy) for i, w in enumerate(g.nu.get(y, ())) if w == x]
            if y in chains[x]:
                rel.append(("in", chains[x].index(y), sy))
            if x in chains[y]:
                rel.append(("holds", chains[y].index(x), sy))
        out.append((_sig(g, x, sigs), sorted(rel)))
    return out if ordered else sorted(out)


def _enclosing(g, x) -> list:
    """The cuts enclosing ``x``, innermost first (the sheet excluded)."""
    out, a = [], x
    while a != g.sheet:
        a = g.get_context(a)
        if a != g.sheet:
            out.append(a)
    return out


def instance_key(tier: str, gname: str, g, m, sigs) -> str:
    """UUID-independent: the rule, the selection signed jointly (each element's
    signature with its incidences to the other selected elements), the target
    as (signature, relation to the selection: selected / inside-selection /
    outside), the content, and the hooks by signature. For the ligature rules
    the selection is signed IN ORDER, since the engine keeps (or moves from)
    its first element (calculus_apply.InOrder).

    It does NOT distinguish moves that agree on all of that. The signature is
    a Weisfeiler-Leman refinement, not a complete invariant, so a shared key is
    not a proof of symmetry; calculus_adjudication reports any failing key
    whose moves land in more than one refusal cell."""
    parts = (m.rule, _selection(g, m.selection, sigs, ordered=m.rule in LIGATURE_RULES),
             _target(g, m, sigs), m.content,
             sorted((_sig(g, e, sigs), i) for e, i in m.hooks))
    return f"{tier}|{gname}|{m.rule}|{hashlib.sha256(repr(parts).encode()).hexdigest()[:12]}"


# How each mode is ledgered: the default mode lists its instances (by kind);
# the exhaustive mode is too large to list, so each entry pins a count of
# distinct instance keys per kind, and its classifier decides membership.
STYLE = {"default": "instances", "exhaustive": "counts"}
_FIELDS = {"id", "layer", "rule", "classifier", "reason", "instances", "counts"}


def _entries() -> List[dict]:
    from calculus_classifiers import CLASSIFIERS
    entries = json.loads(LEDGER.read_text())["entries"]
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), "ledger entry ids must be unique"
    for e in entries:
        assert e.get("reason", "").strip(), f"ledger entry {e['id']!r} has no reason"
        assert set(e) == _FIELDS, f"{e['id']!r}: bad fields {sorted(set(e) ^ _FIELDS)}"
        assert isinstance(e["instances"], dict), f"{e['id']!r}: instances are listed by kind"
        c = e["classifier"]
        assert c is None or c in CLASSIFIERS.get(e["layer"], {}), f"{e['id']!r}: no classifier {c!r}"
        assert c is not None or not e["counts"], f"{e['id']!r}: a counted entry needs a classifier"
        assert set(e["counts"]) <= set(STYLE), f"{e['id']!r}: unknown mode in counts"
    return entries


def ledgered(layer: str) -> Set[str]:
    return {k for e in _entries() if e["layer"] == layer
            for ks in e["instances"].values() for k in ks}


def check_ledger(layer: str, evaluated_ledgered: Set[str], failures: List[Failure],
                 mode: str = "default") -> List[str]:
    entries = [e for e in _entries() if e["layer"] == layer]
    problems = []
    twice = [f for f in failures if len(f.claims) > 1]
    if twice:
        problems.append(f"{len(twice)} failure(s) claimed by two classifiers (first 5):\n"
                        + "\n".join(f"  {f.key}  {f.claims}" for f in twice[:5]))
    if STYLE[mode] == "counts":
        new, problems2 = _check_counts(layer, entries, failures, mode)
    else:
        new, problems2 = _check_instances(layer, entries, evaluated_ledgered, failures)
    if new:
        problems.append(f"{len(new)} NEW failure(s) in layer {layer!r} (first 20):\n"
                        + "\n".join(f"  {f.key}  [{f.kind}]{note} {f.detail}" for f, note in new[:20]))
        dump = os.environ.get("CALCULUS_LEDGER_DUMP")
        if dump:
            Path(f"{dump}.{layer}.json").write_text(json.dumps(
                [{**asdict(f), "kind": f.kind} for f, _ in new], indent=1))
    return problems + problems2


def _check_instances(layer, entries, evaluated, failures):
    """Default mode: every failing (kind, key) is listed; every listed one that
    was evaluated still fails with that kind; and the entry's classifier, where
    the layer has classifiers, claims each listed failure (so the classifiers
    that pin the exhaustive counts are checked against the lists)."""
    from calculus_classifiers import CLASSIFIERS
    owner = {(k, key): e["id"] for e in entries for k, ks in e["instances"].items() for key in ks}
    kinds_of = {}
    for (k, key) in owner:
        kinds_of.setdefault(key, set()).add(k)
    new, problems, drift = [], [], []
    for f in failures:
        eid = owner.get((f.kind, f.key))
        if eid is None:
            new.append((f, f" (kind flipped: ledgered as {sorted(kinds_of[f.key])})"
                        if f.key in kinds_of else ""))
        elif layer in CLASSIFIERS and eid not in f.claims:
            drift.append((f.key, eid, f.claims))
    if drift:
        problems.append(f"{len(drift)} listed failure(s) their entry's classifier does not claim "
                        f"(first 5): {drift[:5]}")
    failing = {(f.kind, f.key) for f in failures}
    for e in entries:
        stale = sorted(f"{k}|{key}" for k, ks in e["instances"].items() for key in ks
                       if key in evaluated and (k, key) not in failing)
        if stale:
            problems.append(f"entry {e['id']!r}: {len(stale)} instance(s) no longer fail — "
                            f"shrink this entry: {stale[:5]}")
    return new, problems


def _check_counts(layer, entries, failures, mode):
    """A counted mode: a failure no classifier claims, or claimed under a kind
    its entry does not pin, is NEW; per (entry, kind), the distinct failing keys
    must EQUAL the pin — fewer is SHRINK, more is a regression inside a known
    mechanism."""
    pins = {e["id"]: e["counts"].get(mode, {}) for e in entries}
    seen: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
    new = []
    for f in failures:
        if len(f.claims) != 1 or f.kind not in pins.get(f.claims[0], {}):
            new.append((f, f" (claimed by {f.claims[0]!r}, which pins no such kind)"
                        if len(f.claims) == 1 else ""))
            continue
        seen[(f.claims[0], f.kind)].add(f.key)
    problems = []
    for eid, kinds in pins.items():
        for k, n in sorted(kinds.items()):
            got = len(seen.get((eid, k), ()))
            if got < n:
                problems.append(f"entry {eid!r} [{k}]: {got} failing key(s) in mode {mode!r}, "
                                f"pinned {n} — SHRINK this entry's count")
            elif got > n:
                problems.append(f"entry {eid!r} [{k}]: {got} failing key(s) in mode {mode!r}, "
                                f"pinned {n} — the count ROSE: a regression inside a known mechanism")
    return new, problems


def refresh_reasons(owned_layers, specs: Dict[str, Tuple[str, str, str]]) -> int:
    """Rewrite only the reason field of this script's existing entries from
    ``specs`` — a text change needs no re-adjudication. Every owned entry must
    have a spec (else its reason would silently go stale)."""
    data = json.loads(LEDGER.read_text())
    missing = [e["id"] for e in data["entries"] if e["layer"] in owned_layers and e["id"] not in specs]
    if missing:
        raise SystemExit(f"owned entries with no reason: {missing}")
    n = 0
    for e in data["entries"]:
        if e["layer"] in owned_layers and e["reason"] != specs[e["id"]][2]:
            e["reason"], n = specs[e["id"]][2], n + 1
    LEDGER.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    return n


def update_ledger(owned_layers, specs: Dict[str, Tuple[str, str, str]], mode: str,
                  found: Dict[str, Dict[str, Set[str]]]) -> None:
    """Rewrite the entries of ``owned_layers`` for one mode, keeping the other
    mode's data. ``specs`` is authoritative: eid -> (layer, rule, reason);
    ``found`` is eid -> kind -> the failing keys the adjudication classified.
    An entry left with no instances and no counts is dropped."""
    from calculus_classifiers import CLASSIFIERS
    unknown = set(found) - set(specs)
    if unknown:
        raise SystemExit(f"classified into entries with no reason: {sorted(unknown)}")
    owner = defaultdict(set)
    for eid, kinds in found.items():
        for k, keys in kinds.items():
            for key in keys:
                owner[(specs[eid][0], k, key)].add(eid)
    split = {k: e for k, e in owner.items() if len(e) > 1}
    if split:
        raise SystemExit(f"{len(split)} key(s) classified into two entries: {list(split.items())[:5]}")
    old = {e["id"]: e for e in json.loads(LEDGER.read_text())["entries"]}
    kept = [e for e in old.values() if e["layer"] not in owned_layers]
    mine = []
    for eid, (layer, rule, reason) in specs.items():
        prev = old.get(eid, {"instances": {}, "counts": {}})
        kinds = {k: v for k, v in found.get(eid, {}).items() if v}
        instances, counts = dict(prev["instances"]), dict(prev["counts"])
        if STYLE[mode] == "instances":
            instances = {k: sorted(v) for k, v in sorted(kinds.items())}
        else:
            counts[mode] = {k: len(v) for k, v in sorted(kinds.items())}
            if not counts[mode]:
                del counts[mode]
        if instances or counts:
            mine.append({"id": eid, "layer": layer, "rule": rule,
                         "classifier": eid if eid in CLASSIFIERS.get(layer, {}) else None,
                         "reason": reason, "instances": instances,
                         "counts": dict(sorted(counts.items()))})
    entries = sorted(kept + mine, key=lambda e: (e["layer"], e["id"]))
    LEDGER.write_text(json.dumps({"entries": entries}, indent=1, ensure_ascii=False) + "\n")


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
    groups = defaultdict(lambda: defaultdict(list))
    for f in json.loads(Path(dump_file).read_text()):
        rule = f["key"].split("|")[2]
        groups[(f["layer"], rule, f["detail"][:48])][f["kind"]].append(f["key"])
    out = [{"id": f"{layer}-{rule}-{i}".lower(), "layer": layer, "rule": rule,
            "reason": "", "instances": {k: sorted(v) for k, v in kinds.items()},
            "_sample_detail": d}
           for i, ((layer, rule, d), kinds) in enumerate(sorted(groups.items()))]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    draft(sys.argv[1])
