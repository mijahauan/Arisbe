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
