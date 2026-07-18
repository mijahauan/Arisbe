"""Vault V0 — the metadata membrane's reader, against the synthetic fixture
(spec: docs/superpowers/specs/2026-07-17-vault-cycle-design.md). Metadata
only: no note body text ever appears in an emission."""
from pathlib import Path
from egif_parser_dau import parse_egif
from vault_world import VaultWorld

FIX = Path(__file__).parent / "fixtures" / "vorago_fixture"


class TestReader:
    def test_notes_sorted_and_ids_egif_safe(self):
        w = VaultWorld(FIX)
        assert w.notes() == sorted(w.notes())
        for n in w.notes():
            parse_egif(f'(note "{w.note_id(n)}")')

    def test_note_facts_carry_structure_not_content(self):
        w = VaultWorld(FIX)
        egif = w.note_facts("Ideas/alpha.md")
        parse_egif(egif)
        i = w.note_id("Ideas/alpha.md")
        assert f'(in_folder "{i}" "Ideas")' in egif
        assert f'(modified "{i}" "2025-03")' in egif      # frontmatter wins
        assert '(links ' in egif and '(tagged ' in egif
        assert "peirce" in egif.lower()
        # metadata only: no body words leak (alpha.md's body must carry a
        # sentinel word the test asserts absent — put the word `SENTINELBODY`
        # in the fixture body when creating it)
        assert "SENTINELBODY" not in egif

    def test_clippings_prior_and_wikilink_resolution(self):
        w = VaultWorld(FIX)
        c = w.note_id("Clippings/saved page.md")
        assert f'(collected_prior "{c}")' in w.note_facts("Clippings/saved page.md")
        a = w.note_facts("Ideas/alpha.md")
        assert f'(links "{w.note_id("Ideas/alpha.md")}" "{w.note_id("Ideas/beta.md")}")' in a

    def test_attachments_go_to_horizon_items(self):
        w = VaultWorld(FIX)
        items = w.attachment_items(round_idx=1)
        refs = {i.ref for i in items}
        assert any(r.endswith("scan.pdf") for r in refs)
        assert any(r.endswith("sketch.canvas") for r in refs)
        assert all(i.reason == "binary" for i in items)


class TestJournal:
    def test_entries_split_on_valid_datelines_only(self):
        w = VaultWorld(FIX)
        [j] = w.journal_paths()
        entries, flagged = w.journal_entries(j)
        dates = [e[0] for e in entries]
        assert dates == ["1930-05", "1973-11", "1983-07", "2023-11"]
        assert len(flagged) == 1                     # 2115-21: month 21 invalid

    def test_journal_facts_are_event_time_claims_without_content(self):
        w = VaultWorld(FIX)
        [j] = w.journal_paths()
        egif = w.journal_facts(j)
        parse_egif(egif)
        assert '(entry_date ' in egif and '"1930-05"' in egif
        assert "SENTINELBODY" not in egif            # content never leaks
        assert "writing" not in egif                 # writing-time absent by design

    def test_malformed_datelines_reach_the_horizon_counted(self):
        w = VaultWorld(FIX)
        [j] = w.journal_paths()
        items = w.journal_horizon_items(round_idx=1)
        assert len(items) == 1 and items[0].reason == "malformed_date_line"


class TestFeed:
    def _feed(self):
        from attention_economy import AttentionEconomy, Horizon
        from vault_world import VaultWorld, VaultFeed
        w = VaultWorld(FIX)
        h = Horizon()
        return VaultFeed(w, AttentionEconomy(), horizon=h), w, h

    def test_journal_outranks_scans_and_lands_first(self):
        from egif_parser_dau import parse_egif
        feed, w, h = self._feed()
        first = feed.propose(parse_egif('(even "0")'), 1)
        assert "(journal_entry" in first        # severity 8 wins round 1

    def test_full_drive_discovers_reads_and_horizons(self):
        from egif_parser_dau import parse_egif
        from agon_evolution import run
        feed, w, h = self._feed()
        res = run('(even "0")', feed, rounds=25, uod_id="vault_fix",
                  name="vault fixture drive")
        final = res.uod.current_egi
        from agon_evolution import peel
        from semantic_game import Verdict3
        a = w.note_id("Ideas/alpha.md")
        assert peel(final, f'(note "{a}")').verdict is Verdict3.TRUE
        assert peel(final, f'(collected_prior "{w.note_id("Clippings/saved page.md")}")').verdict is Verdict3.TRUE
        assert peel(final, '(entry_date "j:L1" "1930-05")').verdict is not Verdict3.FALSE
        assert h.snapshot()["open"] >= 3        # pdf + canvas + malformed dateline
        assert feed.refused == 0

    def test_metadata_only_end_to_end(self):
        from egif_parser_dau import parse_egif
        feed, w, h = self._feed()
        m = parse_egif('(even "0")')
        emissions = [feed.propose(m, r) for r in range(1, 26)]
        assert all("SENTINELBODY" not in (e or "") for e in emissions)
