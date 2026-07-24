"""West-in-kytē E3b — the basin map.
Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md"""

import pytest

from vault_generator import CrossLink, VaultManifest, generate_vault

from west_meta_agon import bucketing_key, bucket_sizes, canonical
from west_basin_map import contiguous_compositions, structured_starts


def _manifest(folders, links=()):
    cross = tuple(
        CrossLink(source_note=f"{s}/n{i}.md", source_folder=s,
                  target_note=f"{t}/m{i}.md", target_folder=t)
        for i, (s, t) in enumerate(links))
    return VaultManifest(folders=tuple(folders), notes=(),
                         cross_links=cross, journal_len=0)


class TestContiguousCompositions:
    def test_three_parts_of_four_folders(self):
        m = _manifest(["a", "b", "c", "d"])
        comps = contiguous_compositions(m.folders, 3, cap=99)
        # compositions of 4 into 3 positive contiguous parts: (2,1,1),(1,2,1),(1,1,2)
        # sorted by size-tuple descending -> (2,1,1),(1,2,1),(1,1,2)
        assert [bucket_sizes(b) for b in comps] == ["2/1/1", "1/2/1", "1/1/2"]
        # (2,1,1) => contiguous blocks {a,b},{c},{d}
        assert comps[0] == (("a", "b"), ("c",), ("d",))

    def test_cap_takes_largest_first(self):
        m = _manifest(["a", "b", "c", "d", "e", "f"])
        comps = contiguous_compositions(m.folders, 2, cap=2)
        # compositions of 6 into 2 parts, size-desc: (5,1),(4,2),(3,3),(2,4),(1,5)
        # cap=2 -> (5,1),(4,2)
        assert [bucket_sizes(b) for b in comps] == ["5/1", "4/2"]

    def test_contiguous_assignment_in_sorted_order(self):
        m = _manifest(["d", "a", "c", "b"])  # unsorted input
        comps = contiguous_compositions(m.folders, 2, cap=1)  # (3,1)
        # sorted folders a,b,c,d ; (3,1) -> {a,b,c},{d}
        assert comps[0] == (("a", "b", "c"), ("d",))


class TestStructuredStarts:
    def test_includes_round_robin_endpoints_and_e3_starts(self):
        m = _manifest([f"Folder-{k}" for k in range(12)])
        starts = structured_starts(m, comp_parts=(3, 4), comp_cap=12)
        keys = {bucketing_key(b) for b in starts}
        fs = sorted(m.folders)
        n1 = bucketing_key(tuple((tuple(sorted(fs)),)))       # monolith
        n12 = bucketing_key(tuple((f,) for f in fs))          # singletons
        mid = bucketing_key(
            __import__("west_meta_agon").canonical(
                [fs[0:6], fs[6:9], fs[9:11], fs[11:12]]))     # 6/3/2/1
        assert n1 in keys and n12 in keys and mid in keys

    def test_deduped_and_deterministic(self):
        m = _manifest([f"Folder-{k}" for k in range(12)])
        a = structured_starts(m, comp_parts=(3, 4), comp_cap=12)
        b = structured_starts(m, comp_parts=(3, 4), comp_cap=12)
        keys = [bucketing_key(x) for x in a]
        assert keys == [bucketing_key(x) for x in b]          # deterministic
        assert len(keys) == len(set(keys))                    # deduped

    def test_f0_less_than_12_excludes_mid_start(self):
        # F0 < 12: the 6/3/2/1 mid-start guard should NOT fire.
        m = _manifest([f"Folder-{k}" for k in range(4)])
        starts = structured_starts(m, comp_parts=(2, 3), comp_cap=4)
        # All starts must have non-empty buckets.
        for b in starts:
            assert all(len(bucket) > 0 for bucket in b), \
                f"Bucketing {b} has empty buckets"
        # The degenerate 6/3/2/1 shape (which would have empty buckets on F0=4)
        # must NOT appear in the starts.
        fs = sorted(m.folders)
        degenerate = canonical([fs[0:6], fs[6:9], fs[9:11], fs[11:12]])
        degenerate_key = bucketing_key(degenerate)
        for b in starts:
            assert bucketing_key(b) != degenerate_key, \
                f"Degenerate 6/3/2/1 mid-start should not appear for F0={len(fs)}"


@pytest.fixture(scope="module")
def small_vault(tmp_path_factory):
    dest = tmp_path_factory.mktemp("e3b")
    manifest = generate_vault(dest, seed=20260721, folders=4,
                              notes_per_folder=3,
                              cross_folder_link_prob=0.5, journal_len=3)
    return dest, manifest


class TestMapBasins:
    def test_terminus_matches_direct_walk(self, small_vault):
        from west_meta_agon import MemoEvaluator, run_meta_walk
        from west_basin_map import BasinMap, distinct_optima, map_basins
        dest, manifest = small_vault
        starts = structured_starts(manifest, comp_parts=(2, 3), comp_cap=4)
        bm = map_basins(dest, manifest, starts, rounds=12, ttl=120, theta=0.2)
        # Every recorded terminus is a converged halt.
        for wr in bm.terminus_by_start.values():
            assert wr.halt == "converged"
        # Re-running one start's walk directly reproduces its terminus.
        s0 = starts[0]
        direct = run_meta_walk(s0, name="chk", arm="naive", manifest=manifest,
                               evaluate=MemoEvaluator(dest, manifest, rounds=12,
                                                      ttl=120).evaluate,
                               theta=0.2)
        assert (bm.terminus_by_start[bucketing_key(s0)].final_evidence.cost_naive
                == direct.final_evidence.cost_naive)

    def test_watersheds_partition_the_starts(self, small_vault):
        from west_meta_agon import MemoEvaluator, run_meta_walk
        from west_basin_map import BasinMap, distinct_optima, map_basins
        dest, manifest = small_vault
        starts = structured_starts(manifest, comp_parts=(2, 3), comp_cap=4)
        bm = map_basins(dest, manifest, starts, rounds=12, ttl=120, theta=0.2)
        # Every start appears in exactly one watershed; the union is all starts.
        flat = [s for members in bm.watersheds.values() for s in members]
        assert sorted(flat) == sorted(bucketing_key(s) for s in starts)
        assert len(flat) == len(set(flat))          # disjoint
        # Each watershed key is a terminus of each of its members.
        for term_key, members in bm.watersheds.items():
            for s_key in members:
                assert bucketing_key(bm.terminus_by_start[s_key].final) == term_key

    def test_shared_memo_saves_evals(self, small_vault):
        from west_meta_agon import MemoEvaluator, run_meta_walk
        from west_basin_map import BasinMap, distinct_optima, map_basins
        dest, manifest = small_vault
        starts = structured_starts(manifest, comp_parts=(2, 3), comp_cap=4)
        bm = map_basins(dest, manifest, starts, rounds=12, ttl=120, theta=0.2)
        assert bm.evaluator.hits > 0        # overlap across starts was reused


class FakeEval:
    """Deterministic evaluator for killer tests (rejects per-start and arm mutations)."""
    def __init__(self, table):
        self.table = table          # {bucketing_key: (cost_naive, cost_incremental, gap)}
        self.calls = []
        self.hits = 0
        self.misses = 0

    def evaluate(self, b):
        from west_meta_agon import MetaEvidence
        key = bucketing_key(b)
        self.calls.append(key)
        self.misses += 1
        cn, ci, gap = self.table.get(key, (10**9, 10**9, 0.0))
        return MetaEvidence(n=len(b), cost_naive=cn, cost_incremental=ci, gap=gap,
                            coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                            cut_links=0, cv=0.0, mean_member=0.0)


class TestShadowDiagnostic:
    def test_shortlist_hides_an_improving_merge(self):
        # 4 singletons, no links -> merge_moves(k=3) would shortlist by weight,
        # but the ONLY cheaper child is a low-weight merge the top-3 could rank
        # out. full_neighbourhood_improver must still find it.
        from west_meta_agon import MetaEvidence, canonical
        from west_basin_map import full_neighbourhood_improver

        def _ev(n, naive, gap=0.0):
            return MetaEvidence(n=n, cost_naive=naive, cost_incremental=naive, gap=gap,
                                coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                                cut_links=0, cv=0.0, mean_member=0.0)

        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a"], ["b"], ["c"], ["d"]])   # N=4
        table = {bucketing_key(incumbent): _ev(4, 100)}
        # exactly one cheaper neighbour: merging c+d (a low/zero-weight pair)
        cheaper = canonical([["a"], ["b"], ["c", "d"]])
        table[bucketing_key(cheaper)] = _ev(3, 50)

        def evaluate(b):
            return table.get(bucketing_key(b), _ev(len(b), 999))

        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is True

    def test_true_optimum_has_no_improver(self):
        from west_meta_agon import MetaEvidence, canonical
        from west_basin_map import full_neighbourhood_improver

        def _ev(n, naive, gap=0.0):
            return MetaEvidence(n=n, cost_naive=naive, cost_incremental=naive, gap=gap,
                                coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                                cut_links=0, cv=0.0, mean_member=0.0)

        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a", "b"], ["c", "d"]])
        table = {}

        def evaluate(b):
            # incumbent is 100; every neighbour is dearer.
            return _ev(len(b), 100 if bucketing_key(b) ==
                       bucketing_key(incumbent) else 200)

        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is False

    def test_incoherent_cheaper_neighbour_is_not_an_improver(self):
        # a cheaper neighbour with gap>theta is refused -> not a shadow.
        from west_meta_agon import MetaEvidence, canonical
        from west_basin_map import full_neighbourhood_improver

        def _ev(n, naive, gap=0.0):
            return MetaEvidence(n=n, cost_naive=naive, cost_incremental=naive, gap=gap,
                                coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                                cut_links=0, cv=0.0, mean_member=0.0)

        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a", "b"], ["c", "d"]])
        table = {bucketing_key(incumbent): _ev(2, 100)}

        def evaluate(b):
            if bucketing_key(b) == bucketing_key(incumbent):
                return _ev(2, 100)
            return _ev(len(b), 10, gap=0.5)     # cheaper but incoherent

        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is False

    def test_killer_equal_cost_is_not_improvement(self):
        # KILL `<` → `<=` mutation: equal cost must NOT count as strict improvement.
        from west_meta_agon import MetaEvidence, canonical
        from west_basin_map import full_neighbourhood_improver

        def _ev(n, naive, gap=0.0):
            return MetaEvidence(n=n, cost_naive=naive, cost_incremental=naive, gap=gap,
                                coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                                cut_links=0, cv=0.0, mean_member=0.0)

        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a", "b"], ["c", "d"]])
        table = {
            bucketing_key(incumbent): _ev(2, 100),
            # One neighbour at equal cost (gap 0) — should NOT count as improver.
            bucketing_key(canonical([["a"], ["b"], ["c", "d"]])): _ev(3, 100),
        }

        def evaluate(b):
            return table.get(bucketing_key(b), _ev(len(b), 999))

        # Under `<` the cost is NOT better (100 < 100 is False), returns False.
        # Under `<=` mutation (100 <= 100 is True), returns True — test fails.
        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is False

    def test_killer_split_only_improver(self):
        # KILL `split_moves(bucketing) +` deletion: must check splits, not just merges.
        from west_meta_agon import MetaEvidence, canonical
        from west_basin_map import full_neighbourhood_improver

        def _ev(n, naive, gap=0.0):
            return MetaEvidence(n=n, cost_naive=naive, cost_incremental=naive, gap=gap,
                                coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                                cut_links=0, cv=0.0, mean_member=0.0)

        m = _manifest(["a", "b", "c", "d"])
        incumbent = canonical([["a", "b"], ["c", "d"]])
        # Only split:0 child is cheaper; all merges are expensive.
        table = {
            bucketing_key(incumbent): _ev(2, 100),
            # split:0 — split first bucket -> a;b;c,d
            bucketing_key(canonical([["a"], ["b"], ["c", "d"]])): _ev(3, 50),
            # merge:0+1 — merge both buckets -> a,b,c,d
            bucketing_key(canonical([["a", "b", "c", "d"]])): _ev(1, 999),
        }

        def evaluate(b):
            return table.get(bucketing_key(b), _ev(len(b), 999))

        # Under correct code, split:0 is found and is cheaper -> True.
        # Under split_moves deletion, only merges checked -> no improver -> False (mutation fails test).
        assert full_neighbourhood_improver(
            incumbent, m, evaluate, theta=0.2) is True


class TestKillerTests:
    """Killer tests: catch mutations the real-evaluator tests can't."""

    def test_killer_shared_evaluator_identity(self):
        """KILL per-start mutation: each start must use THE SHARED evaluator, not its own."""
        from west_basin_map import map_basins
        # Create a simple manifest and starts.
        m = _manifest(["a", "b"])
        starts = [canonical([("a",), ("b",)]), canonical([("a", "b")])]
        fake = FakeEval({
            bucketing_key(canonical([("a",), ("b",)])): (100, 100, 0.0),
            bucketing_key(canonical([("a", "b")])): (50, 50, 0.0),
        })
        bm = map_basins(None, m, starts, rounds=0, ttl=0, theta=0.5, evaluator=fake)
        # The per-start mutation builds its own MemoEvaluator internally,
        # ignoring the injected one. The identity check fails.
        assert bm.evaluator is fake, "map_basins did not use the injected evaluator"
        assert len(fake.calls) > 0, "Injected evaluator was never called"

    def test_killer_arm_is_naive(self):
        """KILL arm="incremental" mutation: walk must use arm="naive", not "incremental"."""
        from west_basin_map import map_basins
        # Construct S (start) and C (split child).
        # Under "naive": S high, C low → accept split → terminus C.
        # Under "incremental": S's incremental low, C's incremental high (worse) → halt at S.
        S = canonical([("a", "b"), ("c", "d")])
        C = canonical([("a",), ("b",), ("c", "d")])  # split first bucket of S
        fake = FakeEval({
            bucketing_key(S): (1000, 100, 0.0),   # S: naive=high, incr=low
            bucketing_key(C): (10, 1000, 0.0),    # C: naive=low, incr=high
            # Other neighbors of S (for completeness, set them high).
            bucketing_key(canonical([("a", "b"), ("c",), ("d",)])): (10**9, 10**9, 0.0),
            bucketing_key(canonical([("a", "b"), ("c", "d", "e")])): (10**9, 10**9, 0.0),
        })
        bm = map_basins(None, _manifest(["a", "b", "c", "d"]),
                        [S], rounds=0, ttl=0, theta=0.2, evaluator=fake)
        # Under arm="naive", the split (S → C, 1000 → 10) is improving.
        # The terminus must be C.
        terminus = bm.terminus_by_start[bucketing_key(S)].final
        assert bucketing_key(terminus) == bucketing_key(C), \
            f"arm='incremental' mutation: expected terminus C, got {bucketing_key(terminus)}"

    def test_killer_watersheds_sorted(self, small_vault):
        """KILL unsorted-watersheds mutation: watershed members must be sorted."""
        from west_basin_map import map_basins
        dest, manifest = small_vault
        starts = structured_starts(manifest, comp_parts=(2, 3), comp_cap=4)
        bm = map_basins(dest, manifest, starts, rounds=12, ttl=120, theta=0.2)
        # Every watershed member list must equal its own sorted copy.
        # This test fails if members.sort() is removed (the mutation).
        for term_key, members in bm.watersheds.items():
            assert members == sorted(members), \
                f"Watershed {term_key} not sorted: {members} != {sorted(members)}"
