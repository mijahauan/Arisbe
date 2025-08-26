#!/usr/bin/env python3
"""
Harvest EGIF/CGIF/CLIF examples from docs/derived/*.txt and add to corpus/corpus/.

- Detects candidate blocks via simple regex heuristics
- Validates candidates with available parsers (EGIF, CGIF)
- Writes examples to corpus/corpus/{scholars,challenging}/ with .egif/.cgif/.clif
- Generates minimal metadata JSON next to each snippet

Usage:
  python corpus_harvest_from_derived.py --input docs/derived --out corpus/corpus/scholars --limit 50 --minlen 10 --type egif,cgif

Notes:
- CLIF validation is best-effort; if clif_parser_dau exists it will be used, else only pattern detection.
- This tool is conservative: only writes snippets that parse successfully (for EGIF/CGIF). Failed ones can be exported to --rejected for manual curation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
import multiprocessing as mp

# Ensure we can import src.* when running as a script
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Optional imports; some may not exist
try:
    from src.egif_parser_dau import parse_egif  # type: ignore
except Exception:
    parse_egif = None  # type: ignore

try:
    from src.cgif_parser_dau import parse_cgif  # type: ignore
except Exception:
    parse_cgif = None  # type: ignore

try:
    from src.clif_parser_dau import parse_clif  # type: ignore
except Exception:
    parse_clif = None  # type: ignore


EGIF_PATTERNS = [
    # Cuts and relations, variables/constants
    re.compile(r"~\s*\[.*?\]", re.S),
    re.compile(r"\([A-Za-z_][A-Za-z0-9_]*\s+(?:\*?[A-Za-z_][A-Za-z0-9_]*|\".*?\")(?:\s+\*?[A-Za-z_][A-Za-z0-9_]*|\s+\".*?\")*\)", re.S),
    re.compile(r"\*\s*[A-Za-z_][A-Za-z0-9_]*", re.S),
]

CGIF_PATTERNS = [
    # Concept/Relation tokens and brackets
    re.compile(r"\[[^\]]+\]", re.S),
    re.compile(r"\([^)]+\)", re.S),
]

CLIF_PATTERNS = [
    re.compile(r"\(cl-text[\s\S]*?\)", re.S),
    re.compile(r"\(forall[\s\S]*?\)", re.S),
]


def _read_text_files(input_dir: Path, name_contains: Optional[str] = None) -> List[Tuple[Path, str]]:
    results: List[Tuple[Path, str]] = []
    for p in sorted(input_dir.glob("*.txt")):
        if name_contains and name_contains not in p.name:
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        results.append((p, txt))
    return results


def _candidate_blocks(text: str, kind: str) -> List[str]:
    pats = EGIF_PATTERNS if kind == "egif" else CLIF_PATTERNS if kind == "clif" else CGIF_PATTERNS
    found: List[str] = []
    for pat in pats:
        for m in pat.finditer(text):
            frag = m.group(0)
            # Expand to nearby context if it's very short (join adjacent matches)
            if frag and frag not in found:
                found.append(frag)
    # Also split on blank-line separated paragraphs and include those with many EGIF/CGIF tokens
    paragraphs = [para.strip() for para in re.split(r"\n\s*\n", text) if para.strip()]
    for para in paragraphs:
        token_score = 0
        if kind == "egif":
            token_score = len(re.findall(r"~\s*\[|\([A-Za-z]", para))
        elif kind == "cgif":
            token_score = len(re.findall(r"\[|\(", para))
        elif kind == "clif":
            token_score = len(re.findall(r"\(cl-text|\(forall|\(exists", para))
        if token_score >= 3 and para not in found:
            found.append(para)
    # Deduplicate, keep order
    seen = set()
    uniq = []
    for f in found:
        if f not in seen:
            seen.add(f)
            uniq.append(f.strip())
    # Prefer shorter candidates first to avoid heavy parsing of huge paragraphs
    uniq.sort(key=len)
    return uniq


def _prefilter(kind: str, snippet: str) -> bool:
    s = snippet.strip()
    if kind == "egif":
        # Skip unsupported actor/output arg '|' quickly
        if '|' in s:
            return False
        # Require at least one relation tuple like (Rel x ...) and either a cut or a star variable
        has_tuple = re.search(r"\([A-Za-z_][A-Za-z0-9_]*\s+[^)]*\)", s) is not None
        has_cut_or_star = ("~[" in s) or (re.search(r"\*[A-Za-z_][A-Za-z0-9_]*", s) is not None)
        return has_tuple and has_cut_or_star
    if kind == "cgif":
        # Require both concept and relation indicators
        has_concept = re.search(r"\[[^\]]+\]", s) is not None
        has_relation = re.search(r"\([^)]+\)", s) is not None
        # Concepts with colon (type slots) and/or star variables
        has_colon_or_star = re.search(r"\[[^\]]*:[^\]]*\]", s) is not None or re.search(r"\*[A-Za-z_][A-Za-z0-9_]*", s) is not None
        # Relation name followed by at least one argument token
        rel_tuple_like = re.search(r"\([A-Za-z_][A-Za-z0-9_]*\s+[^)]+\)", s) is not None
        # Quick balance sanity: same counts of brackets/parens
        balanced = s.count('[') == s.count(']') and s.count('(') == s.count(')')
        return has_concept and has_relation and has_colon_or_star and rel_tuple_like and balanced
    if kind == "clif":
        # Basic indicators
        return re.search(r"\((?:cl-text|forall|exists)", s) is not None
    return True


def _validate_in_subprocess(kind: str, snippet: str, timeout: float) -> bool:
    """Run validation in a short-lived process; terminate on timeout."""
    # Use spawn context for macOS/py3.8+ compatibility and top-level worker for picklability
    ctx = mp.get_context("spawn")
    q: mp.Queue = ctx.Queue(maxsize=1)
    p = ctx.Process(target=_validate_worker, args=(q, kind, snippet))
    p.daemon = True
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join(0.1)
        return False
    try:
        return bool(q.get_nowait())
    except Exception:
        return False


def _validate_worker(q: mp.Queue, k: str, s: str) -> None:
    """Top-level worker function so it can be pickled under spawn."""
    ok = _do_validate(k, s)
    try:
        q.put(bool(ok))
    except Exception:
        pass


def _validate(kind: str, snippet: str) -> bool:
    if kind == "egif" and parse_egif:
        try:
            parse_egif(snippet)
            return True
        except Exception:
            return False
    if kind == "cgif" and parse_cgif:
        try:
            parse_cgif(snippet)
            return True
        except Exception:
            return False
    if kind == "clif" and parse_clif:
        try:
            parse_clif(snippet)
            return True
        except Exception:
            return False
    # If no parser available, accept only longer snippets to avoid junk
    return len(snippet) >= 40


def _do_validate(kind: str, snippet: str) -> bool:
    """Child-process-safe validation to support timeouts."""
    try:
        if kind == "egif":
            try:
                from src.egif_parser_dau import parse_egif as _p  # type: ignore
            except Exception:
                # Fallback heuristic if parser unavailable in child
                return len(snippet) >= 40
            _p(snippet)
            return True
        if kind == "cgif":
            try:
                from src.cgif_parser_dau import parse_cgif as _p  # type: ignore
            except Exception:
                # Fallback heuristic if parser unavailable in child
                return len(snippet) >= 40
            _p(snippet)
            return True
        if kind == "clif":
            try:
                from src.clif_parser_dau import parse_clif as _p  # type: ignore
            except Exception:
                # Fallback heuristic if parser unavailable in child
                return len(snippet) >= 40
            _p(snippet)
            return True
    except Exception:
        return False
    return False


def _slugify(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_\-]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def _write_example(out_dir: Path, base_name: str, kind: str, snippet: str, source: Path, category: str):
    ext = ".egif" if kind == "egif" else ".cgif" if kind == "cgif" else ".clif"
    fname = f"{base_name}{ext}"
    target = out_dir / fname
    # Avoid overwrite by suffixing
    ctr = 1
    while target.exists():
        target = out_dir / f"{base_name}_{ctr}{ext}"
        ctr += 1
    target.write_text(snippet.strip() + "\n", encoding="utf-8")
    # Metadata JSON
    meta = {
        "title": base_name,
        "source_file": str(source.name),
        "kind": kind,
        "category": category,
        "description": "Harvested from derived docs; review for correctness.",
    }
    (out_dir / f"{target.stem}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Harvest EGIF/CGIF/CLIF examples from derived docs")
    ap.add_argument("--input", default="docs/derived", help="Input directory of normalized text")
    ap.add_argument("--out", default="corpus/corpus/scholars", help="Output directory for accepted snippets")
    ap.add_argument("--rejected", default=None, help="Optional directory for rejected snippets for curation")
    ap.add_argument("--type", default="egif,cgif", help="Comma-list of kinds to harvest: egif,cgif,clif")
    ap.add_argument("--limit", type=int, default=50, help="Max snippets per file per kind")
    ap.add_argument("--minlen", type=int, default=10, help="Minimum snippet length")
    ap.add_argument("--verbose", action="store_true", help="Print progress for each file and snippet")
    ap.add_argument("--eval-limit", type=int, default=80, help="Max candidate validations per file per kind")
    ap.add_argument("--max-snippet-len", type=int, default=600, help="Truncate candidate text to this many chars before validation")
    ap.add_argument("--per-parse-timeout", type=float, default=0.6, help="Seconds to allow each parse before timing out")
    ap.add_argument("--filename-contains", default=None, help="Only process input .txt files whose name contains this substring")
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.out)
    rej_dir = Path(args.rejected) if args.rejected else None
    kinds = [k.strip() for k in args.type.split(',') if k.strip()]

    out_dir.mkdir(parents=True, exist_ok=True)
    if rej_dir:
        rej_dir.mkdir(parents=True, exist_ok=True)

    files = _read_text_files(in_dir, args.filename_contains)
    total_written = 0

    try:
        for src_path, text in files:
            if args.verbose:
                print(f"Scanning {src_path} ...")
            for kind in kinds:
                blocks = _candidate_blocks(text, kind)
                if args.verbose:
                    print(f"  {kind}: {len(blocks)} candidates")
                written_this_file = 0
                evaluated = 0
                for blk in blocks:
                    if evaluated >= args.eval_limit:
                        if args.verbose:
                            print(f"  {kind}: eval-limit reached ({evaluated})")
                        break
                    if written_this_file >= args.limit:
                        break
                    if len(blk) < args.minlen:
                        if args.verbose:
                            print(f"    skip(short) len={len(blk)}")
                        if rej_dir:
                            (rej_dir / f"{_slugify(src_path.stem)}_{kind}_short.txt").write_text(blk, encoding="utf-8")
                        continue
                    if not _prefilter(kind, blk):
                        if args.verbose:
                            print(f"    skip(prefilter) {kind}")
                        continue
                    # Truncate overly long candidates before validation
                    blk_eval = blk[: args.max_snippet_len]
                    evaluated += 1
                    if args.verbose and evaluated % 10 == 0:
                        print(f"    progress: evaluated={evaluated}, accepted={written_this_file}")
                    ok = _validate_in_subprocess(kind, blk_eval, timeout=args.per_parse_timeout)
                    if not ok:
                        if args.verbose:
                            print("    reject(timeout)" if len(blk_eval) else "    reject(parse)")
                        if rej_dir:
                            (rej_dir / f"{_slugify(src_path.stem)}_{kind}_invalid.txt").write_text(blk_eval, encoding="utf-8")
                        continue
                    base = f"harvest_{_slugify(src_path.stem)}_{kind}"
                    category = "scholars" if "EGIF" in src_path.stem.upper() or "SOWA" in src_path.stem.upper() else "challenging"
                    _write_example(out_dir, base, kind, blk_eval, src_path, category)
                    if args.verbose:
                        print(f"    accept -> {base}.{kind}")
                    total_written += 1
                    written_this_file += 1
    except KeyboardInterrupt:
        print("Interrupted by user. Partial results saved.")

    print(f"Harvest complete. Added {total_written} examples to {out_dir}")


if __name__ == "__main__":
    main()
