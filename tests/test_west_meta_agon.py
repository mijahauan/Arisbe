"""West-in-kytē E3 — meta-Agon over folder-bucketings.
Spec: docs/superpowers/specs/2026-07-23-west-in-kyte-e3-design.md"""

from vault_generator import CrossLink, VaultManifest

from west_meta_agon import (bucketing_key, bucket_sizes, canonical,
                            merge_moves, slate_moves, split_moves)


def _manifest(folders, links):
    """A hand-built manifest: links = [(src_folder, tgt_folder), ...]."""
    cross = tuple(
        CrossLink(source_note=f"{s}/n{i}.md", source_folder=s,
                  target_note=f"{t}/m{i}.md", target_folder=t)
        for i, (s, t) in enumerate(links)
    )
    return VaultManifest(folders=tuple(folders), notes=(),
                         cross_links=cross, journal_len=0)


class TestCanonical:
    def test_canonical_sorts_within_and_across_buckets(self):
        b = canonical([["b", "a"], ["d"], ["c"]])
        assert b == (("a", "b"), ("c",), ("d",))

    def test_key_is_stable_and_order_independent(self):
        b1 = canonical([["b", "a"], ["c"]])
        b2 = canonical([["c"], ["a", "b"]])
        assert bucketing_key(b1) == bucketing_key(b2) == "a,b;c"

    def test_sizes_string(self):
        assert bucket_sizes((("a", "b", "c"), ("d",))) == "3/1"


class TestSplitMoves:
    def test_balanced_contiguous_split(self):
        b = canonical([["a", "b", "c", "d", "e"]])
        moves = split_moves(b)
        assert len(moves) == 1
        label, child = moves[0]
        assert label == "split:0"
        # ceil(5/2)=3 first, 2 rest, contiguous in sorted order.
        assert child == (("a", "b", "c"), ("d", "e"))

    def test_singletons_cannot_split(self):
        assert split_moves((("a",), ("b",))) == []

    def test_split_every_eligible_bucket(self):
        b = (("a", "b"), ("c",), ("d", "e"))
        labels = [m[0] for m in split_moves(b)]
        assert labels == ["split:0", "split:2"]


class TestMergeMoves:
    def test_shortlist_top_k_by_cross_bucket_links(self):
        # 4 singletons; links make (a,b) weight 3, (a,c) weight 2,
        # (b,c) weight 1, (c,d) weight 1 — tie broken by canonical pair.
        m = _manifest(
            ["a", "b", "c", "d"],
            [("a", "b"), ("a", "b"), ("b", "a"),
             ("a", "c"), ("c", "a"), ("b", "c"), ("c", "d")])
        b = canonical([["a"], ["b"], ["c"], ["d"]])
        moves = merge_moves(b, m, k=3)
        labels = [lab for lab, _ in moves]
        # top-3 pairs: (0,1) w=3, (0,2) w=2, then w=1 tie -> (1,2) before (2,3).
        assert labels == ["merge:0+1", "merge:0+2", "merge:1+2"]
        assert moves[0][1] == (("a", "b"), ("c",), ("d",))

    def test_all_pairs_when_fewer_than_k(self):
        m = _manifest(["a", "b"], [])
        b = canonical([["a"], ["b"]])
        assert [lab for lab, _ in merge_moves(b, m, k=3)] == ["merge:0+1"]

    def test_n1_cannot_merge(self):
        m = _manifest(["a", "b"], [])
        assert merge_moves((("a", "b"),), m) == []


class TestSlate:
    def test_splits_first_then_merges_deterministic(self):
        m = _manifest(["a", "b", "c"], [("a", "c")])
        b = (("a", "b"), ("c",))
        labels = [lab for lab, _ in slate_moves(b, m, k=3)]
        assert labels == ["split:0", "merge:0+1"]
