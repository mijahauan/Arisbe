"""V2a.1 — the Obsidian oracle notes (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2). Render/seal half."""
from pathlib import Path
from oracle_notes import QuestionCandidate, candidates_from_run, render_note, seal

FIX = Path(__file__).parent / "fixtures" / "vorago_fixture"


def _world():
    from vault_world import VaultWorld
    return VaultWorld(FIX)


class TestCandidates:
    def test_sources_fire_on_the_fixture(self):
        from attention_economy import Horizon, HorizonItem
        w = _world()
        h = Horizon()
        for i in w.attachment_items(1):
            h.register(i)
        cands = candidates_from_run(w, h, known_laws=[], labels=w.labels())
        qids = [c.qid for c in cands]
        assert any(q.startswith("prov:") for q in qids)      # Clippings note
        assert any(q.startswith("journal:") for q in qids)   # two journals in fixture
        assert any(q.startswith("horizon:") for q in qids)
        assert "journal-timelines" in qids
        assert [c.qid for c in cands] == qids                # deterministic order

    def test_reflective_is_exactly_the_standing_question(self):
        cands = candidates_from_run(_world(), None, known_laws=[], labels={})
        refl = [c for c in cands if c.tier == "reflective"]
        assert [c.qid for c in refl] == ["journal-timelines"]


class TestRender:
    def test_note_shape_and_budget(self):
        cands = [QuestionCandidate(f"q{i}", "quick", f"Question {i}?", "w", "s",
                                    forecast=f"f{i}", severity=float(i))
                 for i in range(8)]
        cands.append(QuestionCandidate("r1", "reflective", "Reflect?", "w", "s",
                                        forecast="deep", severity=9.0))
        cands.append(QuestionCandidate("r2", "reflective", "Reflect more?", "w", "s",
                                        forecast="deeper", severity=8.0))
        text = render_note(cands, note_date="2026-07-18", run_id="run13",
                           segment=3, budget={"max": 5, "reflective": 1},
                           reveals=None)
        assert text.count("## Q") == 5                       # max enforced
        assert text.count("· reflective") == 1               # reflective cap
        assert "authored_by: arisbe" in text
        assert "budget: {max: 5, reflective: 1}" in text
        assert f"sha256:{seal('deep')}"[:20] in text          # sealed, not plaintext
        assert "*Forecast (sealed):*" in text
        assert "\ndeep\n" not in text                         # plaintext absent

    def test_reveals_section_renders(self):
        text = render_note([], note_date="2026-07-18", run_id="r", segment=1,
                           budget={"max": 5, "reflective": 1},
                           reveals=[{"qid": "q1", "forecast_plain": "collected",
                                      "forecast_hash": seal("collected"),
                                      "answer": "yes, clipped", "verdict": "hit"}])
        assert "## Reveals" in text and "collected" in text and "hit" in text
