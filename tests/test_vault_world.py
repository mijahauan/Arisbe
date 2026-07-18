"""Vault V0 — the metadata membrane's reader, against the synthetic fixture
(spec: docs/superpowers/specs/2026-07-17-vault-cycle-design.md). Metadata
only: no note body text ever appears in an emission."""
import re
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
        truly_binary = [i for i in items if not i.ref.endswith(".MD")]
        assert truly_binary
        assert all(i.reason == "binary" for i in truly_binary)

    def test_case_variant_md_reaches_the_horizon(self):
        # Note.MD-style case-variant markdown is invisible to notes()'s
        # case-sensitive rglob("*.md") — it must not ALSO be invisible to the
        # attachment horizon (that would be a silent double-drop).
        w = VaultWorld(FIX)
        assert not any(n.endswith("ODD.MD") for n in w.notes())
        items = w.attachment_items(round_idx=1)
        odd = [i for i in items if i.ref.endswith("ODD.MD")]
        assert len(odd) == 1
        assert odd[0].reason == "case_variant_md"

    def test_root_level_notes_have_a_real_bucket(self):
        w = VaultWorld(FIX)
        assert "rootnote.md" in w.notes()
        assert any(d == "(root)" for d in w.top_dirs())
        assert '(in_folder ' in w.note_facts("rootnote.md")


class TestJournal:
    MAIN = "Personal/Journal-x/Journal.md"
    OLD = "Personal/Journal-x/Journal-old.md"

    def test_entries_split_on_valid_datelines_only(self):
        w = VaultWorld(FIX)
        entries, flagged = w.journal_entries(self.MAIN)
        dates = [e[0] for e in entries]
        assert dates == ["1930-05", "1973-11", "1983-07", "2023-11"]
        assert len(flagged) == 1                     # 2115-21: month 21 invalid

    def test_journal_facts_are_event_time_claims_without_content(self):
        w = VaultWorld(FIX)
        egif = w.journal_facts(self.MAIN)
        parse_egif(egif)
        assert '(entry_date ' in egif and '"1930-05"' in egif
        assert "SENTINELBODY" not in egif            # content never leaks
        assert "writing" not in egif                 # writing-time absent by design

    def test_malformed_datelines_reach_the_horizon_counted(self):
        w = VaultWorld(FIX)
        items = w.journal_horizon_items(round_idx=1)
        # only Journal.md carries the malformed 2115-21 line; Journal-old.md
        # (added for the namespacing test below) contributes none.
        assert len(items) == 1 and items[0].reason == "malformed_date_line"

    def test_journal_ids_namespaced_per_file(self):
        # A second Journal-prefixed file (journal_paths() globs "Journal*.md"
        # vault-wide) must not collide eids with the main journal — each
        # entry id is namespaced by its sanitized relpath, not just "j:L<n>".
        w = VaultWorld(FIX)
        paths = w.journal_paths()
        assert self.MAIN in paths
        assert self.OLD in paths

        main_egif = w.journal_facts(self.MAIN)
        old_egif = w.journal_facts(self.OLD)
        parse_egif(main_egif)
        parse_egif(old_egif)

        main_ids = set(re.findall(r'\(journal_entry "([^"]+)"\)', main_egif))
        old_ids = set(re.findall(r'\(journal_entry "([^"]+)"\)', old_egif))
        assert main_ids and old_ids
        assert main_ids.isdisjoint(old_ids)           # no shared eid across files
        assert f"{self.MAIN}#L1" in main_ids
        assert f"{self.OLD}#L1" in old_ids


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
        assert peel(final, '(entry_date "Personal/Journal-x/Journal.md#L1" "1930-05")').verdict is not Verdict3.FALSE
        assert h.snapshot()["open"] >= 3        # pdf + canvas + malformed dateline
        assert feed.refused == 0

    def test_metadata_only_end_to_end(self):
        from egif_parser_dau import parse_egif
        feed, w, h = self._feed()
        m = parse_egif('(even "0")')
        emissions = [feed.propose(m, r) for r in range(1, 26)]
        assert all("SENTINELBODY" not in (e or "") for e in emissions)

    def test_root_level_note_is_discovered_and_read(self):
        from egif_parser_dau import parse_egif
        from agon_evolution import run, peel
        from semantic_game import Verdict3
        feed, w, h = self._feed()
        res = run('(even "0")', feed, rounds=25, uod_id="vault_root",
                  name="root discovery")
        rid = w.note_id("rootnote.md")
        assert peel(res.uod.current_egi, f'(note "{rid}")').verdict is Verdict3.TRUE
        assert feed.refused == 0


class TestDeterminism:
    def test_identical_fixture_identical_trajectories(self):
        from probe_feed import replay_choices
        from agon_evolution import run
        from attention_economy import AttentionEconomy, Horizon
        from vault_world import VaultWorld, VaultFeed
        def drive():
            feed = VaultFeed(VaultWorld(FIX), AttentionEconomy(), horizon=Horizon())
            res = run('(even "0")', feed, rounds=20, uod_id="vfx", name="vfx")
            return replay_choices(feed.journal), [o.disposition for o in res.outcomes]
        assert drive() == drive()


class TestConstantBound:
    """F1¹³ (RUN 13's first finding): at real-vault scale, constants of 60–142
    chars overflowed their residence cells — 53 §3.3 occlusion failures at the
    segment save. The invariant: no emitted constant exceeds _MAX_CONST; long
    originals live only in ``long_labels`` (and the driver's gitignored
    sidecar), never in M."""

    LONG = ("Deep/A Very Long Folder Name For Bound Testing/"
            "An Extremely Long Note Name That Certainly Exceeds "
            "The Forty Character Bound.md")

    def test_no_emitted_constant_exceeds_the_bound(self):
        import re
        from vault_world import VaultWorld, _MAX_CONST
        w = VaultWorld(FIX)
        emissions = [w.note_facts(n) for n in w.notes()]
        emissions += [w.journal_facts(j) for j in w.journal_paths()]
        emissions += [w.folder_listing_facts(d) for d in w.top_dirs()]
        for egif in emissions:
            for const in re.findall(r'"([^"]*)"', egif):
                assert len(const) <= _MAX_CONST, f"over-bound constant ({len(const)} chars)"

    def test_long_constants_digest_and_register(self):
        from egif_parser_dau import parse_egif
        from vault_world import VaultWorld
        w = VaultWorld(FIX)
        nid = w.note_id(self.LONG)
        assert nid.startswith("x") and len(nid) == 11
        assert w.long_labels[nid] == self.LONG
        egif = w.note_facts(self.LONG)
        parse_egif(egif)
        # the long wikilink target and the long tag digested too
        assert self.LONG not in egif
        assert "Truly Excessive" not in egif
        assert sum(1 for k in w.long_labels) >= 3   # note id + link target + tag

    def test_short_ids_pass_through_unchanged(self):
        from vault_world import VaultWorld
        w = VaultWorld(FIX)
        assert w.note_id("Ideas/alpha.md") == "Ideas/alpha.md"

    def test_segment_save_attests_at_fixture_scale(self, tmp_path):
        # the missing V0 end-to-end: run → save_uod_with_chain (§3.3 fires
        # before any disk write) → reload. Pins the exact path RUN 13 crashed on.
        from agon_evolution import run
        from attention_economy import AttentionEconomy, Horizon
        from tomos_service import TomosService
        from vault_world import VaultWorld, VaultFeed
        feed = VaultFeed(VaultWorld(FIX), AttentionEconomy(), horizon=Horizon())
        res = run("", feed, rounds=25, uod_id="vault_attest",
                  name="fixture attest drive")
        service = TomosService(tmp_path)
        service.save_uod_with_chain(res.uod, res.chain)
        reloaded = service.load_chain("vault_attest")
        assert reloaded is not None
        assert len(reloaded.steps) == len(res.chain.steps)
