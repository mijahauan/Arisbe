"""West-in-kytē E3b — the basin map.
Spec: docs/superpowers/specs/2026-07-24-west-in-kyte-e3b-design.md"""

from vault_generator import CrossLink, VaultManifest

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
