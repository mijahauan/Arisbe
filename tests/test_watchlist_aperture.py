"""The journal watchlist aperture (V2b-lite) — the first content-bearing
channel onto the journal, ruled open by the author on RUN 13's F7¹³
(spec: docs/superpowers/specs/2026-07-27-journal-watchlist-aperture.md).

The widening is a lens, not a leak: entry text is read solely to test
membership of author-declared terms; nothing becomes an atom the author
did not name in advance. Every test here runs against synthetic tmp_path
journals or in-memory watchlist text — never the checked-in fixture tree
in place, never any real vault.
"""
import re
import sys
from pathlib import Path

from egif_parser_dau import parse_egif
from vault_world import (
    JOURNAL_SPINE_RELATIONS, VaultWorld, load_watchlist, parse_watchlist,
)

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"

WL = """\
## mood
- grace
- black swan

## disposition
- sign
"""

# The canary: a body token deliberately NOT on any watchlist — if it ever
# shows up in an emission or a digest, the aperture leaked prose (the
# SENTINELBODY pattern, kept distinct so a fixture-wide sweep can't confuse
# the two custody tests).
CANARY = "JOURNALCANARY"

ENTRIES = [
    ("1973-11-15", [f"an early entry with grace and {CANARY}"]),
    ("1983-07-02", ["a sign of the times"]),
    ("1984-01-01", ["nothing that matches here"]),
    ("2023-11-26", ["the Black  swan arrives at last"]),
]


def _write_journal(root: Path, entries=ENTRIES) -> str:
    d = root / "Personal"
    d.mkdir(parents=True, exist_ok=True)
    lines = []
    for dateline, body in entries:
        lines.append(dateline)
        lines.extend(body)
    (d / "Journal.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "Personal/Journal.md"


class TestWatchlistParse:
    def test_groups_and_terms_ordered(self):
        wl = parse_watchlist(WL)
        assert list(wl.groups) == ["mood", "disposition"]
        assert wl.groups["mood"] == ["grace", "black swan"]
        assert wl.groups["disposition"] == ["sign"]
        assert wl.refused == 0
        assert wl.is_open

    def test_over_40_char_term_refused_and_counted_never_truncated(self):
        long_term = "x" * 41
        wl = parse_watchlist(f"## g\n- ok\n- {long_term}\n")
        assert wl.refused == 1
        assert wl.groups["g"] == ["ok"]
        # count-or-refuse: never silently truncated into a shorter term
        assert not any(t.startswith("xxxx") for t in wl.terms)

    def test_absent_file_closes_the_aperture(self, tmp_path):
        wl = load_watchlist(tmp_path / "Arisbe" / "Watchlist.md")
        assert not wl.is_open
        assert wl.refused == 0

    def test_empty_file_closes_the_aperture(self, tmp_path):
        p = tmp_path / "Watchlist.md"
        p.write_text("", encoding="utf-8")
        assert not load_watchlist(p).is_open


class TestMatching:
    def test_whole_word_never_substring(self):
        wl = parse_watchlist("## g\n- sign\n")
        assert wl.match("the design of a signal") == []
        assert wl.match("a sign, at last") == ["sign"]

    def test_case_insensitive_term_emitted_as_written(self):
        wl = parse_watchlist("## g\n- Grace\n")
        assert wl.match("grace abounds") == ["Grace"]

    def test_multiword_phrase_with_boundaries(self):
        wl = parse_watchlist("## g\n- black swan\n")
        assert wl.match("a BLACK swan appeared") == ["black swan"]
        assert wl.match("blackish swannery") == []
        assert wl.match("the black swans") == []          # boundary at both ends
        assert wl.match("a black\nswan across lines") == ["black swan"]


class TestBatchIntegration:
    """The scan rides the existing single journal-file read (F3¹³): each
    batch's conjunction gains its entries' mentions atoms — no new want
    kind, no economy change."""

    def _world(self, tmp_path):
        rel = _write_journal(tmp_path)
        return VaultWorld(tmp_path, watchlist=parse_watchlist(WL)), rel

    def test_batches_carry_planted_mentions_each_entry_once(self, tmp_path):
        w, rel = self._world(tmp_path)
        batches = w.journal_facts_batches(rel, batch_size=2)
        assert len(batches) == 2                          # 4 entries, 2 per batch
        eids, mentions = [], set()
        for b in batches:
            parse_egif(b)                                 # still parseable
            eids += re.findall(r'\(journal_entry "([^"]+)"\)', b)
            mentions |= set(re.findall(r'\(mentions "([^"]+)" "([^"]+)"\)', b))
        assert len(eids) == 4 and len(set(eids)) == 4     # every entry exactly once
        # datelines sit at raw lines 1, 3, 5, 7 (one body line each)
        assert mentions == {
            (f"{rel}#L1", "grace"),
            (f"{rel}#L3", "sign"),
            (f"{rel}#L7", "black swan"),
        }

    def test_closed_watchlist_emits_no_mentions(self, tmp_path):
        rel = _write_journal(tmp_path)
        w = VaultWorld(tmp_path)                          # aperture shut
        assert "(mentions" not in " ".join(w.journal_facts_batches(rel))

    def test_custody_canary_never_leaks_into_a_batch(self, tmp_path):
        w, rel = self._world(tmp_path)
        for b in w.journal_facts_batches(rel):
            assert CANARY not in b


class TestPinning:
    """F4¹³'s pattern applied to the aperture: mentions is longitudinal
    spine, not working set — pinned from disuse-decay."""

    def test_mentions_joins_the_journal_spine(self):
        assert "mentions" in JOURNAL_SPINE_RELATIONS

    def _mentions_after_long_run(self, tmp_path, pinned):
        from agon_evolution import run
        from attention_economy import AttentionEconomy, Horizon
        from probe_feed import _model_signature
        from vault_world import VaultFeed
        _write_journal(tmp_path)
        # Filler notes keep the membrane proposing well past ttl — the run
        # loop breaks when the proposer exhausts, and a journal-only vault
        # would end before disuse-decay ever fires (no decay, no control).
        filler = tmp_path / "Ideas"
        filler.mkdir()
        for i in range(14):
            (filler / f"note{i:02d}.md").write_text(
                f"filler body {i}\n", encoding="utf-8")
        world = VaultWorld(tmp_path, watchlist=parse_watchlist(WL))
        feed = VaultFeed(world, AttentionEconomy(), horizon=Horizon())
        res = run('(even "0")', feed, rounds=40, ttl=5, pinned_relations=pinned,
                  uod_id="wl_pin", name="watchlist pin drive")
        atoms, _ = _model_signature(res.uod.current_egi)
        return sum(1 for r, _labels in atoms if r == "mentions")

    def test_pinned_mentions_survive_rounds_beyond_ttl(self, tmp_path):
        assert self._mentions_after_long_run(
            tmp_path, JOURNAL_SPINE_RELATIONS) > 0

    def test_unpinned_mentions_decay_the_control(self, tmp_path):
        # the same drive minus the pin: mentions fades like scan noise —
        # proof the pin (not luck of the round order) carries the spine.
        unpinned = frozenset(JOURNAL_SPINE_RELATIONS - {"mentions"})
        assert self._mentions_after_long_run(tmp_path, unpinned) == 0


class TestDriver:
    """--watchlist / the present-file default, and the digest's
    aggregate-only observables."""

    @staticmethod
    def _mod():
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        import run_vault_v0
        return run_vault_v0

    def test_default_present_file_opens_the_channel(self, tmp_path):
        (tmp_path / "Arisbe").mkdir()
        (tmp_path / "Arisbe" / "Watchlist.md").write_text(WL, encoding="utf-8")
        wl = self._mod()._load_watchlist(tmp_path, None)
        assert wl is not None and wl.is_open

    def test_default_absent_file_keeps_the_channel_shut(self, tmp_path):
        assert self._mod()._load_watchlist(tmp_path, None) is None

    def test_explicit_flag_path_wins_over_the_default(self, tmp_path):
        p = tmp_path / "elsewhere.md"
        p.write_text(WL, encoding="utf-8")
        wl = self._mod()._load_watchlist(tmp_path, str(p))
        assert wl is not None and wl.is_open

    def test_digest_observables_present_and_aggregate_only(self, tmp_path):
        _write_journal(tmp_path)
        (tmp_path / "Arisbe").mkdir()
        (tmp_path / "Arisbe" / "Watchlist.md").write_text(WL, encoding="utf-8")
        mod = self._mod()
        runs = tmp_path / "runs"
        runs.mkdir()
        wl = mod._load_watchlist(tmp_path, None)
        digest, *_rest = mod._run_segment(tmp_path, 12, 1, runs, "", 0,
                                          watchlist=wl)
        for key in ("watchlist_terms", "watchlist_refused",
                    "mentions_atoms", "entries_with_mentions"):
            assert isinstance(digest[key], int)
        assert digest["watchlist_terms"] == 3
        assert digest["watchlist_refused"] == 0
        assert digest["mentions_atoms"] >= 3       # journal wins early at sev 8
        assert digest["entries_with_mentions"] == 3
        # custody: a captured log of the digest carries no term, no entry id,
        # no prose token — numbers and kind/reason keys only.
        blob = repr(digest)
        for token in ("grace", "black swan", "sign", CANARY, "#L"):
            assert token not in blob

    def test_closed_channel_digest_has_no_watchlist_keys(self, tmp_path):
        _write_journal(tmp_path)
        mod = self._mod()
        runs = tmp_path / "runs"
        runs.mkdir()
        digest, *_rest = mod._run_segment(tmp_path, 8, 1, runs, "", 0,
                                          watchlist=None)
        assert "watchlist_terms" not in digest
        assert "mentions_atoms" not in digest


class TestReportHelper:
    """tools/report_watchlist.py — the PW1/PW2 disposal instrument: per-group
    per-decade rates + O1 coverage, group names and numbers only unless
    --terms is passed (local reading)."""

    @staticmethod
    def _mod():
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        import report_watchlist
        return report_watchlist

    def _finished_run(self, tmp_path):
        drv = TestDriver._mod()
        _write_journal(tmp_path)
        wl_path = tmp_path / "Arisbe" / "Watchlist.md"
        wl_path.parent.mkdir()
        wl_path.write_text(WL, encoding="utf-8")
        runs = tmp_path / "runs"
        runs.mkdir()
        wl = drv._load_watchlist(tmp_path, None)
        drv._run_segment(tmp_path, 12, 1, runs, "", 0, watchlist=wl)
        return runs, wl_path

    def test_report_prints_group_rates_and_coverage_terms_withheld(
            self, tmp_path, capsys):
        runs, wl_path = self._finished_run(tmp_path)
        mod = self._mod()
        rc = mod.main(["--runs-dir", str(runs), "--watchlist", str(wl_path)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "mood" in out and "disposition" in out
        for decade in ("1970s", "1980s", "2020s"):
            assert decade in out
        assert "coverage" in out
        # terms withheld by default; entry ids never printed at all
        for token in ("grace", "black swan", "sign,", " sign", "#L"):
            assert token not in out
        # ENTRIES: 1970s 1/1 mood; 1980s 1 sign over 2 entries; 2020s 1/1.
        assert "0.500" in out and "1.000" in out

    def test_terms_flag_adds_per_term_rows(self, tmp_path, capsys):
        runs, wl_path = self._finished_run(tmp_path)
        mod = self._mod()
        rc = mod.main(["--runs-dir", str(runs), "--watchlist", str(wl_path),
                       "--terms"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "grace" in out and "black swan" in out
