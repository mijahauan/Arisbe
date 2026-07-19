"""V2a.1 — the Obsidian oracle notes (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2). Render/seal half (Task 1) +
parse/score/ledger half (Task 2)."""
from pathlib import Path
from oracle_notes import (
    OracleLedger, ParsedNote, QuestionCandidate, candidates_from_run,
    note_substantially_answered, parse_note, render_note, score, seal,
)

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


def _three_question_note():
    """A rendered note with three questions, none reflective — small and
    concrete enough to hand-edit in a test the way an author would in
    Obsidian."""
    cands = [
        QuestionCandidate("q1", "quick", "Is this your own writing?", "w1", "s1",
                           forecast="collected", severity=3.0),
        QuestionCandidate("q2", "quick", "Is this file a fragment?", "w2", "s2",
                           forecast="fragment", severity=2.0),
        QuestionCandidate("q3", "short", "What is this horizon item?", "w3", "s3",
                           forecast="unknown", severity=1.0),
    ]
    text = render_note(cands, note_date="2026-07-18", run_id="run13",
                        segment=1, budget={"max": 5, "reflective": 1},
                        reveals=None)
    return text


class TestParse:
    def test_round_trip_recovers_author_edits(self):
        text = _three_question_note()

        # answer q1, directly after its "**A:**"
        text = text.replace(
            f"*Forecast (sealed):* `sha256:{seal('collected')}`\n**A:**",
            f"*Forecast (sealed):* `sha256:{seal('collected')}`\n"
            "**A:** yes, I collected it from a talk I attended",
        )
        # decline q2
        text = text.replace(
            f"*Forecast (sealed):* `sha256:{seal('fragment')}`\n**A:**",
            f"*Forecast (sealed):* `sha256:{seal('fragment')}`\n**A:** declined",
        )
        # q3 left blank — untouched

        # edit the budget knob
        text = text.replace("budget: {max: 5, reflective: 1}",
                             "budget: {max: 3, reflective: 1}")

        # append stray prose at the bottom, after the (blank) last question
        text += "\nUnrelated musings the author jotted at the bottom.\n"

        parsed = parse_note(text)

        assert parsed.budget == {"max": 3, "reflective": 1}
        assert parsed.answers == {"q1": "yes, I collected it from a talk I attended"}
        assert parsed.declined == {"q2"}
        assert parsed.ignored == {"q3"}
        assert "Unrelated musings" in parsed.stray


class TestScore:
    def test_hit_miss_and_unscored(self):
        assert score("collected", "yes, I collected it from a talk") == "hit"
        assert score("fragment", "no, it's my own original writing") == "miss"
        assert score("unknown", "it's an old sketch I never finished") == "unscored"
        # case-insensitive
        assert score("Fragment", "this is a FRAGMENT of the main journal") == "hit"


class TestLedger:
    def test_record_asked_and_outcome_round_trip(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        assert ledger.asked_ever("journal-timelines") is False

        ledger.record_asked("2026-07-18", "journal-timelines", "reflective",
                             "reconstructed", seal("reconstructed"))
        assert ledger.asked_ever("journal-timelines") is True  # suppressor fires

        ledger.record_outcome("journal-timelines", "answered",
                               "usually a day or two after the fact",
                               "2026-07-25")
        outs = ledger.outcomes()
        assert len(outs) == 1
        assert outs[0]["qid"] == "journal-timelines"
        assert outs[0]["status"] == "answered"

        # a fresh ledger opened on the same directory sees everything
        ledger2 = OracleLedger(tmp_path)
        assert ledger2.asked_ever("journal-timelines") is True
        assert len(ledger2.outcomes()) == 1

    def test_build_reveals_scores_hit_miss_unscored(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-18", "q1", "quick", "collected", seal("collected"))
        ledger.record_asked("2026-07-18", "q2", "quick", "fragment", seal("fragment"))
        ledger.record_asked("2026-07-18", "q3", "short", "unknown", seal("unknown"))

        parsed = ParsedNote(
            budget={"max": 5, "reflective": 1},
            answers={
                "q1": "yes, I collected it from a talk",
                "q2": "no, it's my own original writing",
                "q3": "it's an old sketch I never finished",
            },
        )
        reveals = ledger.build_reveals(parsed)
        verdicts = {r["qid"]: r["verdict"] for r in reveals}
        assert verdicts == {"q1": "hit", "q2": "miss", "q3": "unscored"}
        assert all(r["forecast_hash"] for r in reveals)  # the seal, joined in


class TestSubstantiallyAnswered:
    def test_half_or_more_counts(self):
        parsed = ParsedNote(budget={}, answers={"q1": "x"}, declined={"q2"},
                             ignored={"q3", "q4"})
        assert note_substantially_answered(parsed) is True  # 2 of 4

    def test_below_half_fails(self):
        parsed = ParsedNote(budget={}, answers={"q1": "x"},
                             ignored={"q2", "q3", "q4"})
        assert note_substantially_answered(parsed) is False  # 1 of 4
