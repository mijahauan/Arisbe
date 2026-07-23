"""West-in-kytē E3 — the meta-Agon over folder-bucketings (endogenous
partition): split/merge as licensed, recorded moves adjudicated on measured
cost/gap evidence, walked by full-slate steepest descent.

Spec: docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md
Unprotected, additive; E1/E2/E2b entry points untouched."""

from typing import Iterable, List, Tuple

Bucketing = Tuple[Tuple[str, ...], ...]


def canonical(buckets: Iterable[Iterable[str]]) -> Bucketing:
    """Canonical form: each bucket lexicographically sorted, buckets ordered
    by their sorted content. The memo key and ledger id derive from this."""
    return tuple(sorted(tuple(sorted(b)) for b in buckets))


def bucketing_key(b: Bucketing) -> str:
    return ";".join(",".join(bucket) for bucket in b)


def bucket_sizes(b: Bucketing) -> str:
    """Numbers-only rendering for stdout (custody convention)."""
    return "/".join(str(len(bucket)) for bucket in b)


def split_moves(b: Bucketing) -> List[Tuple[str, Bucketing]]:
    """Every legal balanced contiguous split (spec §2): bucket i of size s>=2
    splits into its first ceil(s/2) folders vs the rest, in sorted order."""
    moves = []
    for i, bucket in enumerate(b):
        if len(bucket) < 2:
            continue
        half = (len(bucket) + 1) // 2
        child = list(b[:i]) + [bucket[:half], bucket[half:]] + list(b[i + 1:])
        moves.append((f"split:{i}", canonical(child)))
    return moves


def _pair_weight(b1: Tuple[str, ...], b2: Tuple[str, ...], manifest) -> int:
    """Cross-links between the two buckets, either direction."""
    s1, s2 = set(b1), set(b2)
    w = 0
    for cl in manifest.cross_links:
        if ((cl.source_folder in s1 and cl.target_folder in s2)
                or (cl.source_folder in s2 and cl.target_folder in s1)):
            w += 1
    return w


def merge_moves(b: Bucketing, manifest, k: int = 3) -> List[Tuple[str, Bucketing]]:
    """The top-k merge shortlist (spec §2, the slate economy): bucket-pairs
    ranked by cross-bucket link count, descending; ties by canonical pair
    index. Proposer attention, disclosed — never touches how a move is
    judged."""
    ranked = sorted(
        ((-_pair_weight(b[i], b[j], manifest), i, j)
         for i in range(len(b)) for j in range(i + 1, len(b))),
    )
    moves = []
    for _negw, i, j in ranked[:k]:
        child = [bucket for t, bucket in enumerate(b) if t not in (i, j)]
        child.append(b[i] + b[j])
        moves.append((f"merge:{i}+{j}", canonical(child)))
    return moves


def slate_moves(b: Bucketing, manifest, k: int = 3) -> List[Tuple[str, Bucketing]]:
    """The full slate the proposer tables each round: all legal splits, then
    the top-k merge shortlist (spec §2)."""
    return split_moves(b) + merge_moves(b, manifest, k=k)
