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


import pytest

from vault_generator import generate_vault
from west_experiment import run_sweepb_point
from west_measure import round_robin_buckets

from west_meta_agon import MemoEvaluator, MetaEvidence, arm_cost


@pytest.fixture(scope="module")
def small_vault(tmp_path_factory):
    dest = tmp_path_factory.mktemp("e3vault")
    manifest = generate_vault(dest, seed=20260721, folders=4,
                              notes_per_folder=3,
                              cross_folder_link_prob=0.5, journal_len=3)
    return dest, manifest


class TestMemoEvaluator:
    def test_matches_run_sweepb_point_on_round_robin(self, small_vault):
        dest, manifest = small_vault
        ev = MemoEvaluator(dest, manifest, rounds=12, ttl=120)
        b = canonical(round_robin_buckets(manifest.folders, 2))
        got = ev.evaluate(b)
        ref = run_sweepb_point(dest, manifest, n=2, rounds=12, ttl=120,
                               bucketing="round_robin")
        assert (got.n, got.cost_naive, got.cost_incremental) == \
            (ref.n, ref.fed_cost_naive, ref.fed_cost_incremental)
        assert got.gap == ref.gap
        assert got.m_fed == ref.m_fed
        assert got.cut_links == ref.cut_links
        assert got.cv == ref.member_reading.cv

    def test_memo_hit_skips_rerun(self, small_vault):
        dest, manifest = small_vault
        ev = MemoEvaluator(dest, manifest, rounds=12, ttl=120)
        b = canonical(round_robin_buckets(manifest.folders, 2))
        first = ev.evaluate(b)
        assert (ev.hits, ev.misses) == (0, 1)
        second = ev.evaluate(b)
        assert (ev.hits, ev.misses) == (1, 1)
        assert second is first  # the cached object, not a re-run

    def test_key_is_canonical_not_order(self, small_vault):
        dest, manifest = small_vault
        ev = MemoEvaluator(dest, manifest, rounds=12, ttl=120)
        f = sorted(manifest.folders)
        a = canonical([[f[0], f[1]], [f[2], f[3]]])
        b = canonical([[f[3], f[2]], [f[1], f[0]]])
        ev.evaluate(a)
        ev.evaluate(b)
        assert (ev.hits, ev.misses) == (1, 1)


class TestArmCost:
    def test_selects_currency(self):
        e = MetaEvidence(n=2, cost_naive=10, cost_incremental=7, gap=0.0,
                         coverage=1.0, m_fed=5, k2=1.0, k3=0.0, cut_links=1,
                         cv=0.0, mean_member=5.0)
        assert arm_cost(e, "naive") == 10
        assert arm_cost(e, "incremental") == 7
        with pytest.raises(ValueError):
            arm_cost(e, "mono")


import json

from west_meta_agon import (WalkResult, replay_walk, run_meta_walk)


def _ev(n, naive, incr=None, gap=0.0):
    return MetaEvidence(n=n, cost_naive=naive,
                        cost_incremental=(incr if incr is not None else naive),
                        gap=gap, coverage=1.0 - gap, m_fed=0, k2=None, k3=0.0,
                        cut_links=0, cv=0.0, mean_member=0.0)


class FakeEvaluator:
    """Evidence by bucketing key; unknown keys get a default expensive read."""
    def __init__(self, table):
        self.table = table
        self.calls = []

    def evaluate(self, b):
        key = bucketing_key(b)
        self.calls.append(key)
        return self.table.get(key, _ev(len(b), 10**9))


def _walk_manifest():
    return _manifest(["a", "b", "c", "d"], [("a", "b"), ("c", "d")])


class TestWalk:
    def test_descends_and_halts_converged(self, tmp_path):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        # N=1 costs 100; its split (ab|cd) costs 80; children of that cost
        # more -> converge at N=2 after one accept.
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 80),
        })
        led = tmp_path / "w.jsonl"
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20,
                            ledger_path=led)
        assert res.halt == "converged"
        assert res.moves == ["split:0"]
        assert bucketing_key(res.final) == "a,b;c,d"
        assert res.rounds[0].disposition == "accept:split"
        assert res.rounds[1].disposition == "halt:converged"

    def test_gap_gate_refuses_regardless_of_cost(self):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        # The split is far cheaper but incoherent -> refused -> halt.
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 10, gap=0.5),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.halt == "converged"
        assert res.moves == []
        entry = res.rounds[0].slate[0]
        assert entry.refused is True

    def test_incumbent_gap_never_gated(self):
        # A standing-incoherent incumbent (the N=1 start, spec §2) can still
        # accept a coherent improving move.
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100, gap=0.58),
            "a,b;c,d": _ev(2, 90),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.moves == ["split:0"]

    def test_steepest_not_first_improvement(self):
        # Two improving splits; the CHEAPER one wins even though it is
        # tabled second.
        m = _manifest(["a", "b", "c", "d"], [])
        start = canonical([["a", "b"], ["c", "d"]])
        fake = FakeEvaluator({
            "a,b;c,d": _ev(2, 100),
            "a;b;c,d": _ev(3, 90),   # split:0
            "a,b;c;d": _ev(3, 85),   # split:1 — steepest
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.moves[0] == "split:1"

    def test_arm_currency_selects_winner(self):
        # Under naive the split improves; under incremental it worsens.
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100, incr=50),
            "a,b;c,d": _ev(2, 80, incr=60),
        })
        res_n = run_meta_walk(start, name="T", arm="naive", manifest=m,
                              evaluate=fake.evaluate, theta=0.20)
        res_i = run_meta_walk(start, name="T", arm="incremental", manifest=m,
                              evaluate=fake.evaluate, theta=0.20)
        assert res_n.moves == ["split:0"]
        assert res_i.moves == []

    def test_equal_cost_split_is_not_improving(self):
        # A split at exactly the incumbent's cost must NOT count as
        # improving (strict `<`, never `<=`) -> no admissible move -> halt.
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 100),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.halt == "converged"
        assert res.moves == []

    def test_tie_break_by_canonical_key(self):
        # Two equal-cost improving splits; the canonical-key-smaller one
        # wins the tie, not tabling order (split:0 is tabled first but
        # split:1's key "a,b;c;d" sorts before split:0's "a;b;c,d").
        m = _manifest(["a", "b", "c", "d"], [])
        start = canonical([["a", "b"], ["c", "d"]])
        fake = FakeEvaluator({
            "a,b;c,d": _ev(2, 100),
            "a;b;c,d": _ev(3, 90),   # split:0
            "a,b;c;d": _ev(3, 90),   # split:1 -- key < split:0's key
        })
        assert "a,b;c;d" < "a;b;c,d"
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.moves[0] == "split:1"
        assert res.rounds[0].chosen_key == "a,b;c;d"

    def test_gap_exactly_theta_is_not_refused(self):
        # gap == theta must be admissible (strict `>`, never `>=`).
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 90, gap=0.20),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20)
        assert res.moves == ["split:0"]
        assert res.rounds[0].slate[0].refused is False

    def test_max_rounds_reports_non_converged(self):
        # An ever-improving ladder (each split cheaper) with max_rounds=2.
        m = _manifest(["a", "b", "c", "d"], [])
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 90),
            "a;b;c,d": _ev(3, 80),
            "a,b;c;d": _ev(3, 85),
            "a;b;c;d": _ev(4, 70),
        })
        res = run_meta_walk(start, name="T", arm="naive", manifest=m,
                            evaluate=fake.evaluate, theta=0.20, max_rounds=2)
        assert res.halt == "max_rounds"
        assert len(res.moves) == 2


class TestLedger:
    def test_ledger_replays_ok(self, tmp_path):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 80),
        })
        led = tmp_path / "w.jsonl"
        run_meta_walk(start, name="T", arm="naive", manifest=m,
                      evaluate=fake.evaluate, theta=0.20, ledger_path=led)
        rep = replay_walk(led)
        assert rep["ok"] is True
        assert rep["rounds"] == 2
        assert rep["mismatches"] == []

    def test_replay_flags_doctored_disposition(self, tmp_path):
        m = _walk_manifest()
        start = canonical([["a", "b", "c", "d"]])
        fake = FakeEvaluator({
            "a,b,c,d": _ev(1, 100),
            "a,b;c,d": _ev(2, 80),
        })
        led = tmp_path / "w.jsonl"
        run_meta_walk(start, name="T", arm="naive", manifest=m,
                      evaluate=fake.evaluate, theta=0.20, ledger_path=led)
        lines = led.read_text().splitlines()
        row = json.loads(lines[1])          # line 0 is the header
        row["disposition"] = "halt:converged"
        lines[1] = json.dumps(row)
        led.write_text("\n".join(lines) + "\n")
        rep = replay_walk(led)
        assert rep["ok"] is False
        assert rep["mismatches"]

    def test_replay_recomputes_flags_not_recorded(self, tmp_path):
        # Doctor ONE slate entry's recorded refused/improving flags to
        # falsely mark it admissible, while leaving disposition/chosen (and
        # the OTHER, genuinely-winning entry) untouched. That doctored entry
        # is priced far above the real winner, so even falsely "admitting"
        # it can never change which move gets chosen -- the only way this
        # doctoring can be detected at all is by RECOMPUTING each entry's
        # flags from its recorded evidence and comparing, not by trusting
        # the recorded flags (which a "just recompute disposition" replay
        # would silently pass, since the winner/disposition never move).
        m = _manifest(["a", "b", "c", "d"], [])
        start = canonical([["a", "b"], ["c", "d"]])
        fake = FakeEvaluator({
            "a,b;c,d": _ev(2, 100),
            "a;b;c,d": _ev(3, 200, gap=0.5),  # split:0 -- truly refused,
                                               # and priced far above the
                                               # real winner regardless
            "a,b;c;d": _ev(3, 90),            # split:1 -- the real winner
        })
        led = tmp_path / "w.jsonl"
        run_meta_walk(start, name="T", arm="naive", manifest=m,
                      evaluate=fake.evaluate, theta=0.20, ledger_path=led)
        lines = led.read_text().splitlines()
        row = json.loads(lines[1])          # line 0 is the header
        assert row["disposition"] == "accept:split"
        assert row["chosen"] == "a,b;c;d"
        split0 = next(s for s in row["slate"] if s["move"] == "split:0")
        assert split0["refused"] is True
        assert split0["improving"] is False
        split0["refused"] = False
        split0["improving"] = True
        lines[1] = json.dumps(row)
        led.write_text("\n".join(lines) + "\n")
        rep = replay_walk(led)
        assert rep["ok"] is False
        assert rep["mismatches"]


from west_meta_agon import (BrokerQuality, RegimeCell, find_biting_regime,
                            run_broker_quality)


class TestRegimeFinder:
    def _fake_point(self, gaps):
        """gaps: {(n, ttl): gap}. Returns a stand-in for run_sweepb_point."""
        class P:
            def __init__(self, gap):
                self.gap = gap
        def fn(root, manifest, *, n, rounds, ttl, bucketing="round_robin"):
            return P(gaps[(n, ttl)])
        return fn

    def test_picks_largest_biting_ttl_at_n4(self):
        gaps = {(2, 60): 0.0, (2, 30): 0.1, (2, 15): 0.3,
                (4, 60): 0.1, (4, 30): 0.25, (4, 15): 0.4}
        cells, biting = find_biting_regime(
            None, None, rounds=1, theta=0.20,
            point_fn=self._fake_point(gaps))
        assert biting == 30            # largest ttl with gap>theta at n=4
        assert len(cells) == 6
        assert RegimeCell(n=4, ttl=30, gap=0.25) in cells

    def test_none_when_nothing_bites_at_n4(self):
        gaps = {(2, 60): 0.5, (2, 30): 0.5, (2, 15): 0.5,
                (4, 60): 0.0, (4, 30): 0.1, (4, 15): 0.2}  # 0.2 NOT > 0.20
        cells, biting = find_biting_regime(
            None, None, rounds=1, theta=0.20,
            point_fn=self._fake_point(gaps))
        assert biting is None          # n=2 biting does not define the regime


class TestBrokerQuality:
    def test_material_and_totals(self):
        # Fake broker keyed on CALL ORDER: run_broker_quality must call
        # round-robin FIRST, then link-aware (pinned by this test).
        class Res:
            def __init__(self, mat, peel, routes, cov):
                class C:
                    materialization_atoms = mat
                    peel_proxy = peel
                self.cost = C()
                self.routes = routes
                self.coverage = cov
        class Tax:
            cells_written = 10
            naive_member_round = 100
            incremental = 5
        calls = {"i": 0}
        def fake_broker(root, manifest, *, buckets, rounds, ttl):
            calls["i"] += 1
            if calls["i"] == 1:        # round-robin: dear
                return Res(1000, 100, 50, 0.9), Tax()
            return Res(700, 100, 20, 0.95), Tax()   # link-aware: cheaper
        m = _manifest(["a", "b", "c", "d"], [("a", "c"), ("b", "d")])
        q = run_broker_quality(None, m, n=2, rounds=1, ttl=60, tol=0.10,
                               broker_fn=fake_broker)
        assert q.rr_cost == 1000 + 100 + 10 + 100 + 50
        assert q.la_cost == 700 + 100 + 10 + 100 + 20
        assert q.material is True
        # Verify cut counts are computed (not just left as defaults).
        # For _manifest(["a","b","c","d"], [("a","c"),("b","d")]):
        # rr n=2: {a,c},{b,d} → both links intra-bucket → rr_cut=0
        # la n=2: {a,c},{b,d} → both links intra-bucket → la_cut=0
        assert q.rr_cut == 0
        assert q.la_cut == 0

    def test_boundary_exact_equality(self):
        # Kills the <= → < mutation: when la_cost == rr_cost * (1 - tol) exactly,
        # material must be True.
        class Res:
            def __init__(self, mat, peel, routes):
                class C:
                    materialization_atoms = mat
                    peel_proxy = peel
                self.cost = C()
                self.routes = routes
                self.coverage = 1.0
        class Tax:
            cells_written = 0
            naive_member_round = 0
            incremental = 0
        calls = {"i": 0}
        def fake_broker(root, manifest, *, buckets, rounds, ttl):
            calls["i"] += 1
            if calls["i"] == 1:
                # First call (round-robin): rr_cost = 1000
                return Res(1000, 0, 0), Tax()
            # Second call (link-aware): la_cost = 900 = 1000 * (1 - 0.10)
            return Res(900, 0, 0), Tax()
        m = _manifest(["a", "b", "c", "d"], [])
        q = run_broker_quality(None, m, n=2, rounds=1, ttl=60, tol=0.10,
                               broker_fn=fake_broker)
        assert q.rr_cost == 1000
        assert q.la_cost == 900
        # 900 <= 1000 * 0.9 = 900 is True (exact boundary)
        assert q.material is True

    def test_near_miss_material_false(self):
        # Kills two mutations:
        # 1. la_cost * (1 - tol) <= rr_cost (wrong operand) → would give True
        # 2. la_cost > rr_cost * (1 - tol) (inverted comparison) → would give False
        # This test ensures material is False when la_cost > rr_cost * (1 - tol).
        class Res:
            def __init__(self, mat, peel, routes):
                class C:
                    materialization_atoms = mat
                    peel_proxy = peel
                self.cost = C()
                self.routes = routes
                self.coverage = 1.0
        class Tax:
            cells_written = 0
            naive_member_round = 0
            incremental = 0
        calls = {"i": 0}
        def fake_broker(root, manifest, *, buckets, rounds, ttl):
            calls["i"] += 1
            if calls["i"] == 1:
                # First call (round-robin): rr_cost = 1000
                return Res(1000, 0, 0), Tax()
            # Second call (link-aware): la_cost = 950
            # 950 > 1000 * (1 - 0.10) = 900, so material should be False
            return Res(950, 0, 0), Tax()
        m = _manifest(["a", "b", "c", "d"], [])
        q = run_broker_quality(None, m, n=2, rounds=1, ttl=60, tol=0.10,
                               broker_fn=fake_broker)
        assert q.rr_cost == 1000
        assert q.la_cost == 950
        # 950 > 900, so material is False
        # Mutant la_cost * (1 - tol) <= rr_cost would give 855 <= 1000 = True
        assert q.material is False

    def test_cut_counts_computed(self):
        # Verify cut_link_count is actually called and results stored in rr_cut/la_cut.
        # Use a manifest with a hub to show rr vs la differ.
        # folders: [a, b, c, d]; links: a→b, a→c, a→d (star topology, a is hub)
        class Res:
            def __init__(self, mat, peel, routes):
                class C:
                    materialization_atoms = mat
                    peel_proxy = peel
                self.cost = C()
                self.routes = routes
                self.coverage = 1.0
        class Tax:
            cells_written = 0
            naive_member_round = 0
            incremental = 0
        def fake_broker(root, manifest, *, buckets, rounds, ttl):
            # Both return the same cost to isolate cut-count testing
            return Res(500, 0, 0), Tax()
        m = _manifest(["a", "b", "c", "d"],
                      [("a", "b"), ("a", "c"), ("a", "d")])
        q = run_broker_quality(None, m, n=2, rounds=1, ttl=60, tol=0.10,
                               broker_fn=fake_broker)
        # Verify rr_cut and la_cut are integers (cut_link_count called)
        assert isinstance(q.rr_cut, int)
        assert isinstance(q.la_cut, int)
        # Both should be >= 0
        assert q.rr_cut >= 0
        assert q.la_cut >= 0
        # For a star topology with 3 links to different buckets,
        # link-aware should do better (fewer cross-links) than round-robin
        assert q.la_cut <= q.rr_cut
