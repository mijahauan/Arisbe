#!/usr/bin/env python3
"""
Validate corpus metadata entries against project conventions:
- Each metadata JSON (non-.egi.json) must have an adjacent <id>.egi.json
- Metadata must contain schema_version, id, title, description (warn if missing)
- representations.egi.path must match adjacent file name and hash must match
- complexity and alphabet_summary should exist (warn if missing)
- replicas stored under representations.linear_forms (egif/cgif/clif) should exist (warn if missing)

Usage:
  python tools/validate_corpus.py --root corpus/corpus

Filter options:
  --include pattern   include only paths matching glob (can be repeated)
  --exclude pattern   exclude paths matching glob (can be repeated)
Defaults exclude tmp_* and harvested files.
"""
import argparse
import json
from pathlib import Path
from typing import List, Tuple, Iterable
import hashlib
import fnmatch


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def validate_entry(path: Path) -> List[Tuple[str, str]]:
    problems: List[Tuple[str, str]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        problems.append(("error", f"invalid-json: {e}"))
        return problems

    # Required-ish metadata
    for field in ("id", "title", "description"):
        if not data.get(field):
            problems.append(("warn", f"missing-{field}"))
    if not data.get("schema_version"):
        problems.append(("warn", "missing-schema_version"))

    # Adjacent EGI
    base = path.with_suffix("")
    egi_path = base.with_name(base.name + ".egi.json")
    if not egi_path.exists():
        problems.append(("error", f"missing-adjacent-egi: {egi_path.name}"))
        return problems

    # Representations.egi
    reps = data.get("representations", {})
    rep_egi = reps.get("egi") if isinstance(reps, dict) else None
    if not rep_egi or not isinstance(rep_egi, dict):
        problems.append(("warn", "missing-representations.egi"))
    else:
        expected_name = egi_path.name
        if rep_egi.get("path") != expected_name:
            problems.append(("warn", f"egi.path-mismatch: {rep_egi.get('path')} != {expected_name}"))
        # Verify hash
        try:
            egi_text = egi_path.read_text(encoding="utf-8")
            h = sha256_text(egi_text)
            if rep_egi.get("hash") != h:
                problems.append(("error", "egi.hash-mismatch"))
        except Exception as e:
            problems.append(("error", f"egi.read-failed: {e}"))

    # Complexity and alphabet summary
    if not data.get("complexity"):
        problems.append(("warn", "missing-complexity"))
    if not data.get("alphabet_summary"):
        problems.append(("warn", "missing-alphabet_summary"))

    # Replicas presence
    linear = (reps or {}).get("linear_forms", {})
    for k in ("egif", "cgif", "clif"):
        if k not in linear:
            problems.append(("warn", f"missing-replica-{k}"))
        else:
            rep = linear.get(k)
            if not isinstance(rep, dict) or not rep.get("text"):
                problems.append(("warn", f"replica-{k}-missing-text"))

    return problems


def main():
    ap = argparse.ArgumentParser(description="Validate corpus entries")
    ap.add_argument("--root", default="corpus/corpus", help="Root directory")
    ap.add_argument("--include", action="append", default=[], help="Glob of entries to include (relative to root)")
    ap.add_argument("--exclude", action="append", default=[], help="Glob of entries to exclude (relative to root)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    # Default excludes aim to ignore temporary and harvested entries.
    default_excludes = [
        "tmp_*/*",
        "tmp_*",
        "**/tmp_*/*",
        "**/tmp_*",
        "**/harvest_*.json",
        "**/tmp_smoke/*.json",
        "**/tmp_quality/*.json",
    ]
    excludes: list[str] = list(default_excludes) + list(args.exclude)
    includes: list[str] = list(args.include)

    def match_any(patterns: Iterable[str], rel: str) -> bool:
        return any(fnmatch.fnmatch(rel, pat) for pat in patterns)

    total = 0
    ok = 0
    issues = 0
    ignored = 0

    for p in root.rglob("*.json"):
        if p.name.endswith(".egi.json") or p.name == "corpus_index.json":
            continue
        rel = str(p.relative_to(root))
        # Inclusion filter (if provided)
        if includes and not match_any(includes, rel):
            ignored += 1
            continue
        # Exclusion filter
        if excludes and match_any(excludes, rel):
            ignored += 1
            continue
        total += 1
        probs = validate_entry(p)
        if not probs:
            ok += 1
        else:
            issues += 1
            print(f"[entry] {rel}")
            for level, msg in probs:
                print(f"  - {level}: {msg}")

    print(f"Validated {total} entries | OK: {ok} | With issues: {issues} | Ignored: {ignored}")


if __name__ == "__main__":
    main()
