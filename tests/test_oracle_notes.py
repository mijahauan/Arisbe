"""V2a.1 — the Obsidian oracle notes (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2). Render/seal half (Task 1) +
parse/score/ledger half (Task 2) + Conjectures section (Task 3) + driver
wiring end-to-end (Task 4) + salted seal / verified reveals (docket item
8, Task 8)."""
import hashlib
import json
import re
import sys
from pathlib import Path
from oracle_notes import (
    DEFAULT_BUDGET, OracleLedger, ParsedNote, QuestionCandidate,
    candidates_from_run, conjectures_section, note_substantially_answered,
    parse_note, render_note, score, seal,
)

FIX = Path(__file__).parent / "fixtures" / "vorago_fixture"
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"


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


class TestConsentBoundary:
    """Docket item 9 — the People/Kith_Kin/Household consent boundary
    (vault_world.py's docstring only, until now) must bind the question
    generator: a horizon item under one of those folders is registered and
    counted like any other, but never promoted to question text."""

    def test_people_folder_never_yields_a_question_candidate(self):
        from attention_economy import Horizon, HorizonItem
        from oracle_notes import _horizon_candidates
        h = Horizon()
        # People/x.pdf is the larger item, so an unfiltered top-2 cut would
        # pick it first — the filter must exclude it regardless of size.
        h.register(HorizonItem(kind="extension", ref="People/x.pdf", size=9000,
                                reason="binary", registered_round=1))
        h.register(HorizonItem(kind="extension", ref="Clippings/y.pdf", size=100,
                                reason="binary", registered_round=1))
        cands = _horizon_candidates(h, {})
        assert [c.qid for c in cands] == ["horizon:Clippings/y.pdf"]
        # never dropped: still registered, still counted on the horizon.
        assert {i.ref for i in h.open_items()} == {"People/x.pdf", "Clippings/y.pdf"}
        assert h.snapshot()["open"] == 2

    def test_root_level_ref_is_not_filtered_and_does_not_crash(self):
        from attention_economy import Horizon, HorizonItem
        from oracle_notes import _horizon_candidates
        h = Horizon()
        h.register(HorizonItem(kind="extension", ref="root.pdf", size=500,
                                reason="binary", registered_round=1))
        cands = _horizon_candidates(h, {})
        assert [c.qid for c in cands] == ["horizon:root.pdf"]


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
        assert parsed.budget_parsed is True

    def test_budget_parsed_false_when_knob_missing(self):
        text = _three_question_note()
        text = text.replace("budget: {max: 5, reflective: 1}", "budget: (mangled)")
        parsed = parse_note(text)
        assert parsed.budget_parsed is False
        assert parsed.budget == {"max": 5, "reflective": 1}  # the honest default
        # one source of truth: parse_note's fallback IS oracle_notes.DEFAULT_BUDGET
        assert parsed.budget == DEFAULT_BUDGET

    def test_qid_containing_a_space_is_recovered(self):
        # A real vault path can carry a space ("Clippings/saved page.md") —
        # the qid built from it ("prov:Clippings/saved page.md") must not
        # break the parser (discovered via the fixture in Task 4's e2e test).
        cand = QuestionCandidate("prov:Clippings/saved page.md", "quick",
                                  "Is this yours?", "w", "s", forecast="collected")
        text = render_note([cand], note_date="2026-07-18", run_id="r", segment=1,
                            budget={"max": 5, "reflective": 1}, reveals=None)
        text = text.replace("**A:**", "**A:** yes, collected from a talk")
        parsed = parse_note(text)
        assert parsed.answers == {
            "prov:Clippings/saved page.md": "yes, collected from a talk"}
        assert parsed.stray == ""


class TestScore:
    def test_hit_miss_and_unscored(self):
        assert score("collected", "yes, I collected it from a talk") == "hit"
        assert score("fragment", "no, it's my own original writing") == "miss"
        assert score("unknown", "it's an old sketch I never finished") == "unscored"
        # case-insensitive
        assert score("Fragment", "this is a FRAGMENT of the main journal") == "hit"


class TestSeal:
    def test_salted_seal_differs_from_dictionary_hash(self):
        assert seal("collected", "ab12") != seal("collected")
        assert seal("collected", "ab12") == hashlib.sha256(
            b"ab12collected").hexdigest()

    def test_reveals_recompute_and_flag_a_doctored_row(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-18", "q1", "quick", "collected",
                             seal("collected", "nonce1"), nonce="nonce1")

        # doctor the stored row: swap the plaintext without updating the
        # hash (exactly what a tampered forecasts.jsonl would look like).
        path = tmp_path / "forecasts.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["forecast_plain"] = "fragment"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

        parsed = ParsedNote(
            budget={"max": 5, "reflective": 1},
            answers={"q1": "yes, I collected it from a talk"},
        )
        reveals = ledger.build_reveals(parsed)
        assert reveals[0]["verdict"] == "seal-broken"

    def test_intact_row_reveals_hit_or_miss_as_before(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-18", "q1", "quick", "collected",
                             seal("collected", "nonce1"), nonce="nonce1")
        ledger.record_asked("2026-07-18", "q2", "quick", "fragment",
                             seal("fragment", "nonce2"), nonce="nonce2")

        parsed = ParsedNote(
            budget={"max": 5, "reflective": 1},
            answers={
                "q1": "yes, I collected it from a talk",
                "q2": "no, it's my own original writing",
            },
        )
        reveals = ledger.build_reveals(parsed)
        verdicts = {r["qid"]: r["verdict"] for r in reveals}
        assert verdicts == {"q1": "hit", "q2": "miss"}

        # a legacy row (no nonce field at all — the pre-Task-8 shape) still
        # verifies: seal(plain, "") recovers the unsalted legacy value.
        legacy = OracleLedger(tmp_path.parent / "legacy")
        legacy.record_asked("2026-07-18", "q3", "quick", "collected",
                             seal("collected"))  # no nonce arg -> legacy shape
        legacy_parsed = ParsedNote(
            budget={"max": 5, "reflective": 1},
            answers={"q3": "yes, I collected it from a talk"},
        )
        legacy_reveals = legacy.build_reveals(legacy_parsed)
        assert legacy_reveals[0]["verdict"] == "hit"

    def test_note_never_contains_nonce_or_plaintext(self):
        cand = QuestionCandidate("q1", "quick", "Is this yours?", "w", "s",
                                  forecast="collected")
        text = render_note([cand], note_date="2026-07-18", run_id="r",
                            segment=1, budget={"max": 5, "reflective": 1},
                            reveals=None, nonces={"q1": "deadbeef12345678"})
        assert "deadbeef12345678" not in text
        assert "\ncollected\n" not in text
        assert f"sha256:{seal('collected', 'deadbeef12345678')}" in text


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

    def test_record_outcome_once_is_idempotent_under_repolling(self, tmp_path):
        """Driver-style double-recording: a note that sits partially answered
        gets re-polled on every invocation. Recording the SAME outcome twice
        must not append a duplicate row (repeated polling would otherwise
        pollute the ledger); a CHANGED answer for the same qid must still
        append (progress is kept, only exact duplicates are not)."""
        ledger = OracleLedger(tmp_path)

        # first poll: records the outcome, appends
        assert ledger.record_outcome_once(
            "q1", "answered", "yes, collected from a talk", "2026-07-18") is True
        # second poll (re-run while the note is still sitting there,
        # identical answer): must be skipped
        assert ledger.record_outcome_once(
            "q1", "answered", "yes, collected from a talk", "2026-07-18") is False
        outs = ledger.outcomes()
        assert len(outs) == 1

        # third poll: the author CHANGED their answer for the same qid —
        # this must append a new row, not be swallowed as a duplicate
        assert ledger.record_outcome_once(
            "q1", "answered", "actually, it's my own writing", "2026-07-19") is True
        outs = ledger.outcomes()
        assert len(outs) == 2
        assert outs[-1]["answer_text"] == "actually, it's my own writing"


class TestConjectures:
    def test_admitted_law_renders_gloss_and_egif(self):
        law = "~[ (Bird *x) ~[ (Flies x) ] ]"
        text = conjectures_section([law], [])
        assert "## Conjectures" in text
        assert f"`{law}`" in text
        assert "Bird" in text and "Flies" in text  # the gloss, not just the ink

    def test_empty_when_no_laws(self):
        assert conjectures_section([], []) == ""

    def test_wired_into_render_note(self):
        law = "~[ (Bird *x) ~[ (Flies x) ] ]"
        conj = conjectures_section([law], [])
        text = render_note([], note_date="2026-07-18", run_id="r", segment=1,
                            budget={"max": 5, "reflective": 1}, reveals=None,
                            conjectures=conj)
        assert "## Conjectures" in text and law in text
        # default (no conjectures passed) omits the section entirely
        bare = render_note([], note_date="2026-07-18", run_id="r", segment=1,
                            budget={"max": 5, "reflective": 1}, reveals=None)
        assert "## Conjectures" not in bare


class TestSubstantiallyAnswered:
    def test_half_or_more_counts(self):
        parsed = ParsedNote(budget={}, answers={"q1": "x"}, declined={"q2"},
                             ignored={"q3", "q4"})
        assert note_substantially_answered(parsed) is True  # 2 of 4

    def test_below_half_fails(self):
        parsed = ParsedNote(budget={}, answers={"q1": "x"},
                             ignored={"q2", "q3", "q4"})
        assert note_substantially_answered(parsed) is False  # 1 of 4


class TestEndToEnd:
    """Task 4 — the driver wiring (``tools/run_vault_v0.py``), exercised
    through ``main`` exactly as a real invocation would call it. Always
    ``--fixture`` (the read-only synthetic vault under
    ``tests/fixtures/vorago_fixture``) with ``--runs-dir`` pointed at a tmp
    dir — the custody boundary under test: nothing lands anywhere but
    ``runs_dir``, and the checked-in fixture tree is never mutated."""

    @staticmethod
    def _main():
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        import run_vault_v0
        return run_vault_v0

    @staticmethod
    def _answer(text: str, qid: str, answer: str) -> str:
        """Insert ``answer`` right after the given qid's ``**A:**`` marker —
        qid-anchored (via the invisible ``<!-- qid: ... -->`` comment), so it
        doesn't depend on exact question wording."""
        pattern = re.compile(
            rf"(<!-- qid: {re.escape(qid)} -->.*?\*\*A:\*\*)", re.DOTALL)
        new_text, n = pattern.subn(lambda m: m.group(1) + " " + answer, text, count=1)
        assert n == 1, f"qid {qid} not found in note"
        return new_text

    def test_two_invocations_answer_cycle_then_exhaustion(self, tmp_path, capsys):
        """Invocation 1 writes the note — the fixture's whole V2a.1 candidate
        pool is exactly 5 (prov + journal + 2 horizon + the standing
        reflective), which is also the default budget cap, so all 5 are
        asked at once. We simulate the author answering/declining/ignoring a
        mix, then invocation 2 must: record every outcome, compute reveals
        for the genuine answers (hit + unscored), and — because every one of
        those 5 qids is now ``asked_ever`` (the suppressor) and this closed
        fixture offers no others — hit the review-mandated zero-questions
        guard rather than write an empty note."""
        mod = self._main()
        runs_dir = tmp_path / "runs"
        orig_fixture_note = (
            FIX / "Arisbe" / "Questions-2026-07-01.md").read_text(encoding="utf-8")

        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        out1 = capsys.readouterr().out
        assert "questions_written: 5 → Arisbe/Questions-2026-07-18.md" in out1

        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        assert note1.exists()
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        assert len(qids) == 5

        # qids[0] = prov (forecast "collected") -> a genuine hit
        text = self._answer(text, qids[0], "yes, I collected it from a talk")
        # qids[1] = journal (forecast "fragment") -> declined, no reveal
        text = self._answer(text, qids[1], "declined")
        # qids[2] = the first horizon item (forecast "unknown") -> unscored
        text = self._answer(text, qids[2], "it's an old conference scan")
        # qids[3], qids[4] left blank -> ignored (silence)
        note1.write_text(text, encoding="utf-8")

        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0
        out2 = capsys.readouterr().out
        assert "oracle: no questions this cycle" in out2
        assert "questions_written" not in out2.split("oracle:")[0]  # no stray write

        # exactly one note on disk — no second file materialized
        assert sorted((runs_dir / "arisbe_notes").glob("Questions-*.md")) == [note1]

        ledger = OracleLedger(runs_dir / "oracle")
        outs = ledger.outcomes()
        assert len(outs) == 5
        by_qid = {o["qid"]: o["status"] for o in outs}
        assert by_qid[qids[0]] == "answered"
        assert by_qid[qids[1]] == "declined"
        assert by_qid[qids[2]] == "answered"
        assert by_qid[qids[3]] == "ignored"
        assert by_qid[qids[4]] == "ignored"

        parsed = parse_note(text)
        reveals = ledger.build_reveals(parsed)
        verdicts = {r["qid"]: r["verdict"] for r in reveals}
        assert verdicts == {qids[0]: "hit", qids[2]: "unscored"}

        # custody: nothing touched outside runs_dir — the checked-in fixture
        # (including its own pre-existing synthetic Arisbe/ note, used by
        # test_vault_world.py's reader-exclusion tests) is byte-identical.
        assert not (FIX / "Arisbe" / "Questions-2026-07-18.md").exists()
        assert not (FIX / "Arisbe" / "Questions-2026-07-25.md").exists()
        assert (FIX / "Arisbe" / "Questions-2026-07-01.md").read_text(
            encoding="utf-8") == orig_fixture_note

    def test_seeded_low_budget_leaves_a_remainder_for_a_genuine_second_note(
            self, tmp_path, capsys):
        """The zero-questions guard above is the *exhaustion* edge; this test
        exercises the ordinary, expected path where the previous note's
        (author-editable) budget knob really does leave candidates
        unasked, so a second real invocation both reveals the first note's
        answers AND writes a genuine new note. We seed a seed note with a
        low budget (max 2) and zero questions of its own (vacuously
        "substantially answered", so it never blocks) — the standard
        ``render_note`` shape, not hand-rolled markup."""
        from oracle_notes import render_note as _render_note
        mod = self._main()
        runs_dir = tmp_path / "runs"
        oracle_dir = runs_dir / "arisbe_notes"
        oracle_dir.mkdir(parents=True)
        seed = _render_note([], note_date="2026-07-01", run_id="seed", segment=0,
                             budget={"max": 2, "reflective": 1}, reveals=None)
        (oracle_dir / "Questions-2026-07-01.md").write_text(seed, encoding="utf-8")

        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-10"])
        assert rc == 0
        out1 = capsys.readouterr().out
        assert "questions_written: 2 → Arisbe/Questions-2026-07-10.md" in out1

        note1 = oracle_dir / "Questions-2026-07-10.md"
        text1 = note1.read_text(encoding="utf-8")
        qids1 = re.findall(r"<!-- qid: (.+?) -->", text1)
        assert qids1 == ["prov:Clippings/saved page.md",
                          "journal:Personal/Journal-x/Journal.md"]  # top-severity two

        text1 = self._answer(text1, qids1[0], "yes, collected from a talk")
        text1 = self._answer(text1, qids1[1], "declined")
        note1.write_text(text1, encoding="utf-8")

        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-14"])
        assert rc == 0
        out2 = capsys.readouterr().out
        assert "questions_written: 2 → Arisbe/Questions-2026-07-14.md" in out2

        note2 = oracle_dir / "Questions-2026-07-14.md"
        assert note2.exists()
        text2 = note2.read_text(encoding="utf-8")
        assert "## Reveals" in text2 and "collected" in text2  # the hit, revealed
        qids2 = re.findall(r"<!-- qid: (.+?) -->", text2)
        assert set(qids2).isdisjoint(qids1)   # genuinely new questions
        assert all(q.startswith("horizon:") for q in qids2)  # the leftover source

    def test_budget_knob_unparsed_prints_warning_and_falls_back(
            self, tmp_path, capsys):
        """Guard 2: a previous note whose budget line was mangled by hand
        (or an older format) must not fail silently — the driver prints the
        warning and proceeds on the honest default, never a fabricated
        guess."""
        mod = self._main()
        runs_dir = tmp_path / "runs"
        oracle_dir = runs_dir / "arisbe_notes"
        oracle_dir.mkdir(parents=True)
        (oracle_dir / "Questions-2026-07-10.md").write_text(
            "---\nauthored_by: arisbe\nrun: r\nsegment: 1\ndate: 2026-07-10\n"
            "budget: (mangled)\n---\n",
            encoding="utf-8",
        )

        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-17"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "oracle: budget knob unparsed - using defaults" in out
        assert "questions_written: 5 → Arisbe/Questions-2026-07-17.md" in out

    def test_same_day_repoll_never_clobbers_the_note(self, tmp_path, capsys):
        """Guard 3: once a note for a given date is substantially answered, a
        re-poll on THAT SAME date (the driver invoked again before the day
        rolls over) must never overwrite it — only a later date's poll
        produces a new note. Three invocations at the same ``--note-date``:
        the first writes, the second (after the note is answered) and the
        third both hit the clobber guard and leave the file byte-unchanged."""
        mod = self._main()
        runs_dir = tmp_path / "runs"

        rc1 = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                        "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc1 == 0
        out1 = capsys.readouterr().out
        assert "questions_written: 5 → Arisbe/Questions-2026-07-18.md" in out1

        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        assert len(qids) == 5

        # answer/decline enough (3 of 5) to be "substantially answered", so a
        # same-date re-poll would otherwise fall through to a write
        text = self._answer(text, qids[0], "yes, I collected it from a talk")
        text = self._answer(text, qids[1], "declined")
        text = self._answer(text, qids[2], "it's an old conference scan")
        note1.write_text(text, encoding="utf-8")
        answered_bytes = note1.read_bytes()

        # second invocation, SAME note-date: must not overwrite
        rc2 = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                        "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc2 == 0
        out2 = capsys.readouterr().out
        assert "oracle: today's note already exists - not overwriting" in out2
        assert note1.read_bytes() == answered_bytes

        # third invocation, SAME note-date again: still untouched, and the
        # ledger stayed idempotent across both re-polls (no duplicate rows)
        rc3 = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                        "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc3 == 0
        out3 = capsys.readouterr().out
        assert "oracle: today's note already exists - not overwriting" in out3
        assert note1.read_bytes() == answered_bytes

        # both re-polls parse the SAME answered note as "prior" and record
        # its 5 outcomes (3 answered/declined + 2 ignored); the second
        # re-poll's rows are identical to the first's, so record_outcome_once
        # skips them all — one row per qid, never duplicated across polls
        ledger = OracleLedger(runs_dir / "oracle")
        outs = ledger.outcomes()
        assert len(outs) == 5
        assert len({(o["qid"], o["status"], o["answer_text"]) for o in outs}) == 5

        # exactly one note on disk for this date
        assert sorted((runs_dir / "arisbe_notes").glob("Questions-*.md")) == [note1]
