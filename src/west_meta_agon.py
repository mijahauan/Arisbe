"""West-in-kytē E3 — the meta-Agon over folder-bucketings (endogenous
partition): split/merge as licensed, recorded moves adjudicated on measured
cost/gap evidence, walked by full-slate steepest descent.

Spec: docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md
Unprotected, additive; E1/E2/E2b entry points untouched."""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from west_experiment import run_fed_bucketed
from west_measure import cut_link_count, read_member_costs

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


@dataclass
class MetaEvidence:
    """One evaluation of one bucketing at full R (spec §2): both arms' costs
    plus the reported-never-verdict-bearing vector (|M|, K2, K3)."""
    n: int
    cost_naive: int
    cost_incremental: int
    gap: float
    coverage: float
    m_fed: int
    k2: Optional[float]
    k3: float
    cut_links: int
    cv: float
    mean_member: float


def arm_cost(ev: MetaEvidence, arm: str) -> int:
    """The walk's adjudication currency (spec §2): Arm N for the main walks,
    Arm I for the control."""
    if arm == "naive":
        return ev.cost_naive
    if arm == "incremental":
        return ev.cost_incremental
    raise ValueError("arm must be 'naive' or 'incremental'")


class MemoEvaluator:
    """Memoized full-R evaluation, shared across every walk in one run
    (spec §2): deterministic harness => a revisited bucketing is free.
    ``hits``/``misses`` are printed by the driver (no silent caching)."""

    def __init__(self, root, manifest, *, rounds: int, ttl: int):
        self.root = root
        self.manifest = manifest
        self.rounds = rounds
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self._memo: Dict[str, MetaEvidence] = {}

    def evaluate(self, b: Bucketing) -> MetaEvidence:
        key = bucketing_key(b)
        if key in self._memo:
            self.hits += 1
            return self._memo[key]
        self.misses += 1
        buckets = [frozenset(x) for x in b]
        fed, tax = run_fed_bucketed(self.root, self.manifest, buckets=buckets,
                                    rounds=self.rounds, ttl=self.ttl)
        base = fed.cost.materialization_atoms + fed.cost.peel_proxy
        reading = read_member_costs(fed.member_costs)
        ev = MetaEvidence(
            n=len(b),
            cost_naive=base + tax.cells_written + tax.naive_member_round,
            cost_incremental=base + tax.cells_written + tax.incremental,
            gap=1.0 - (fed.coverage if fed.coverage is not None else 1.0),
            coverage=(fed.coverage if fed.coverage is not None else 1.0),
            m_fed=fed.quality.final_m_size,
            k2=fed.quality.k2_stick_rate,
            k3=fed.quality.k3_ratio,
            cut_links=cut_link_count(buckets, self.manifest),
            cv=reading.cv,
            mean_member=reading.mean,
        )
        self._memo[key] = ev
        return ev
