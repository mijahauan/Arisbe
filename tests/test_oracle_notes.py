"""V2a.1 — the Obsidian oracle notes (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2). Render/seal half (Task 1) +
parse/score/ledger half (Task 2) + Conjectures section (Task 3) + driver
wiring end-to-end (Task 4) + salted seal / verified reveals (docket item
8, Task 8)."""
import hashlib
import json
import random
import re
import sys

import pytest
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from oracle_notes import (
    DEFAULT_BUDGET, OracleLedger, ParsedNote, QuestionCandidate,
    candidates_from_run, conjectures_section, note_substantially_answered,
    p2_13_report, parse_note, render_note, score, seal,
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

    def test_docket_arm_never_voices_a_consented_ref(self):
        """Whole-branch review CRITICAL 1 (2026-07-19): the P2^13 docket arm
        bypassed the item-9 consent boundary — a ``("scan", "People")`` want
        (ref = the bare folder) or a ``People/friend.md`` read want could be
        voiced as a question on the default (``--p213``) path. Both must be
        suppressed; the next-ranked eligible want takes the slot."""
        docket = _FakeDocket([
            _FakeEntry(key=("scan", "People"),
                       payload=("People", "a folder scan the attention "
                                          "economy has queued")),
            _FakeEntry(key=("read", "People/friend.md"),
                       payload=("People/friend.md", "flagged for a closer read")),
            _FakeEntry(key=("read", "Clippings/ok.md"),
                       payload=("Clippings/ok.md", "flagged for a closer read")),
        ])
        world = _FakeWorld(["a.md", "b.md"])
        cands = candidates_from_run(world, None, [], {},
                                     docket=docket, rng=random.Random(0))
        docket_cands = [c for c in cands if c.arm == "docket"]
        assert len(docket_cands) == 1
        assert "Clippings/ok.md" in docket_cands[0].qid
        for c in cands:
            assert "People" not in c.qid
            assert "People" not in c.text

    def test_random_arm_never_samples_a_consented_note(self):
        """CRITICAL 1, the other arm: ``_random_candidates`` sampled
        ``world.notes()`` unfiltered — a ``People/friend.md`` in the vault was
        in the random arm's pool. Whatever the seed, only the eligible note
        may be drawn."""
        world = _FakeWorld(["People/friend.md", "Kith_Kin/aunt.md",
                            "Household/bills.md", "a.md"])
        docket = _FakeDocket([])
        for seed in range(5):
            cands = candidates_from_run(world, None, [], {},
                                         docket=docket, rng=random.Random(seed))
            refs = [c.qid.split(":", 1)[1] for c in cands if c.arm == "random"]
            assert refs == ["a.md"], f"seed {seed} leaked a consented note"

    def test_docket_arm_excludes_arisbe_authored_notes_like_the_random_arm(self):
        """CRITICAL 1's fold-in (the deferred asymmetry): the random arm
        already excluded ``authored_by: arisbe`` notes; the docket arm must
        filter identically, or the two arms are different samples and the
        margin is biased."""
        class _W(_FakeWorld):
            def is_arisbe_note(self, relpath):
                return relpath == "Arisbe/Questions-2026-07-01.md"

        world = _W(["Arisbe/Questions-2026-07-01.md", "a.md"])
        docket = _FakeDocket([
            _FakeEntry(key=("read", "Arisbe/Questions-2026-07-01.md"),
                       payload=("Arisbe/Questions-2026-07-01.md",
                                "flagged for a closer read")),
        ])
        cands = candidates_from_run(world, None, [], {},
                                     docket=docket, rng=random.Random(0))
        assert [c for c in cands if c.arm == "docket"] == []


@dataclass
class _FakeEntry:
    """A hand-built docket entry — the shape ``wants_from_docket`` reads
    (``.key``/``.age``/``.attempts``) plus the ``(ref, reason)`` payload
    ``oracle_notes._docket_candidates`` reads. Standing in for a real
    ``run_vault_v0.EconomyDocket`` entry so this test doesn't need a live
    ``AttentionEconomy``."""
    key: Tuple
    payload: Tuple[str, str]
    age: int = 0
    attempts: int = 0


class _FakeDocket:
    def __init__(self, entries: List[_FakeEntry]):
        self._entries = entries

    @property
    def open_entries(self) -> List[_FakeEntry]:
        return self._entries


class _FakeWorld:
    """A minimal ``VaultWorld`` double: just enough surface for
    ``candidates_from_run`` (``notes``/``_top_dir``/``journal_paths``/
    ``note_id``/``long_labels``) with no Clippings/journal content of its
    own, so the P2^13 instrument's candidates are the only ones produced."""

    def __init__(self, notes: List[str]):
        self._notes = notes
        self.long_labels = {}

    def notes(self) -> List[str]:
        return list(self._notes)

    def _top_dir(self, relpath: str) -> str:
        return "(root)"

    def journal_paths(self) -> List[str]:
        return []

    def note_id(self, relpath: str) -> str:
        return relpath


class TestP213Instrument:
    """Docket item 10 — P2^13 made falsifiable: a docket arm + a
    template-random arm, blinded in the note, rated by the author, verdict
    read off the ledger by ``p2_13_report``."""

    def _docket(self):
        return _FakeDocket([
            _FakeEntry(key=("read", "Journal/foo.md"),
                       payload=("Journal/foo.md", "flagged for reading")),
            _FakeEntry(key=("scan", "Ideas"),
                       payload=("Ideas", "a folder scan the attention "
                                         "economy has queued")),
        ])

    def test_docket_present_yields_blinded_two_plus_two_in_seeded_order(self):
        world = _FakeWorld(["a.md", "b.md", "c.md", "d.md"])
        docket = self._docket()

        cands = candidates_from_run(world, None, [], {},
                                     docket=docket, rng=random.Random(42))
        p213 = [c for c in cands if c.arm in ("docket", "random")]
        assert len(p213) == 4
        assert sum(1 for c in p213 if c.arm == "docket") == 2
        assert sum(1 for c in p213 if c.arm == "random") == 2

        text = render_note(p213, note_date="2026-07-18", run_id="r",
                            segment=1, budget={"max": 4, "reflective": 0},
                            reveals=None)
        assert text.count("## Q") == 4
        # the blinding floor this docket item actually charges: no arm word
        # anywhere in the rendered markdown.
        assert "docket" not in text.lower()
        assert "random" not in text.lower()
        assert "arm" not in text.lower()

        # Review finding (2026-07-19): a per-arm parenthetical reason was a
        # real leak (an author could partition all four questions by
        # phrasing alone). Assert the stronger, template-level guarantee:
        # strip each candidate's concrete backtick-quoted subject and the
        # remaining text must be IDENTICAL across every P2^13 candidate,
        # regardless of arm.
        templated = {re.sub(r"`[^`]*`", "`REF`", c.text) for c in p213}
        assert len(templated) == 1, (
            "docket-arm and random-arm question text must be template-"
            f"identical once the concrete subject is stripped; got {templated}")

        # seeded order: a fresh call with the SAME seed reproduces the same
        # question order (the shuffle is deterministic, not the arm).
        cands2 = candidates_from_run(world, None, [], {},
                                      docket=docket, rng=random.Random(42))
        p213_2 = [c for c in cands2 if c.arm in ("docket", "random")]
        assert [c.qid for c in p213] == [c.qid for c in p213_2]

    def test_random_arm_excludes_arisbe_authored_notes(self):
        """Minor 1 (review, 2026-07-19): a self-authored note (e.g. a prior
        oracle Questions-*.md) must never enter the random arm's pool — it
        reads as trivial almost by construction, biasing the docket-vs-random
        margin toward a false PASS."""
        class _WorldWithArisbeNote(_FakeWorld):
            def is_arisbe_note(self, relpath):
                return relpath == "Arisbe/Questions-2026-07-01.md"

        world = _WorldWithArisbeNote(["Arisbe/Questions-2026-07-01.md", "a.md"])
        docket = _FakeDocket([])   # empty docket -> random arm draws from all
        cands = candidates_from_run(world, None, [], {},
                                     docket=docket, rng=random.Random(0))
        random_refs = [c.qid.split(":", 1)[1] for c in cands
                       if c.arm == "random"]
        assert random_refs == ["a.md"]
        assert "Arisbe/Questions-2026-07-01.md" not in random_refs

    def test_docket_none_is_unaffected_backward_compatible(self):
        # the existing V2a.1 default path — untouched by this docket item.
        cands = candidates_from_run(_world(), None, known_laws=[], labels={})
        assert all(c.arm is None for c in cands)

    def test_rating_recovered_from_R_line(self):
        text = _three_question_note()
        text = text.replace(
            f"*Forecast (sealed):* `sha256:{seal('collected')}`\n"
            "**A:**\n**R:** (trivial | non-trivial)",
            f"*Forecast (sealed):* `sha256:{seal('collected')}`\n"
            "**A:** yes\n**R:** non-trivial",
        )
        text = text.replace(
            f"*Forecast (sealed):* `sha256:{seal('fragment')}`\n"
            "**A:**\n**R:** (trivial | non-trivial)",
            f"*Forecast (sealed):* `sha256:{seal('fragment')}`\n"
            "**A:** no\n**R:** trivial",
        )
        # q3's **R:** line left as the unedited placeholder -> unrated

        parsed = parse_note(text)
        assert parsed.ratings == {"q1": "non-trivial", "q2": "trivial"}
        assert "q3" not in parsed.ratings
        # the answer capture must not have swallowed the rating line
        assert parsed.answers == {"q1": "yes", "q2": "no"}
        assert "declined" not in parsed.answers.get("q2", "")

    def test_rating_appended_after_placeholder_recovered(self):
        """Real-vault edit pattern (RUN 13, 2026-07-27): the author appends
        the rating AFTER the rendered placeholder instead of replacing it —
        ``**R:** (trivial | non-trivial) non-trivial`` — and the mark must
        still be recovered; an untouched placeholder stays unrated."""
        text = _three_question_note()
        text = text.replace(
            f"*Forecast (sealed):* `sha256:{seal('collected')}`\n"
            "**A:**\n**R:** (trivial | non-trivial)",
            f"*Forecast (sealed):* `sha256:{seal('collected')}`\n"
            "**A:** yes\n**R:** (trivial | non-trivial) non-trivial",
        )
        text = text.replace(
            f"*Forecast (sealed):* `sha256:{seal('fragment')}`\n"
            "**A:**\n**R:** (trivial | non-trivial)",
            f"*Forecast (sealed):* `sha256:{seal('fragment')}`\n"
            "**A:** no\n**R:** (trivial | non-trivial) trivial",
        )
        # q3's **R:** line left as the unedited placeholder -> still unrated

        parsed = parse_note(text)
        assert parsed.ratings == {"q1": "non-trivial", "q2": "trivial"}
        assert "q3" not in parsed.ratings
        assert parsed.answers == {"q1": "yes", "q2": "no"}

    def test_wants_from_docket_is_called_and_key_traceable(self):
        docket = _FakeDocket([
            _FakeEntry(key=("read", "Journal/unique-marker.md"),
                       payload=("Journal/unique-marker.md",
                                "flagged for reading")),
        ])
        world = _FakeWorld(["a.md", "b.md"])
        cands = candidates_from_run(world, None, [], {},
                                     docket=docket, rng=random.Random(1))
        docket_cands = [c for c in cands if c.arm == "docket"]
        assert len(docket_cands) == 1
        assert "read" in docket_cands[0].qid
        assert "Journal/unique-marker.md" in docket_cands[0].qid

    def test_note_qid_structure_never_distinguishes_arms(self):
        """Whole-branch review IMPORTANT 3 (2026-07-19): the note embeds
        ``<!-- qid: ... -->`` and the REAL qids are structurally
        distinguishable (``p213:scan:...`` docket vs ``p213:<relpath>``
        random) — the author answers in source mode where comments are
        visible. The note must render an OPAQUE alias; and once the alias
        hash and the backticked subject are normalized, the full rendered
        blocks (comments included) must be byte-identical across arms."""
        from oracle_notes import opaque_note_qid
        world = _FakeWorld(["a.md", "b.md", "c.md", "d.md"])
        cands = candidates_from_run(world, None, [], {},
                                     docket=self._docket(),
                                     rng=random.Random(42))
        p213 = [c for c in cands if c.arm in ("docket", "random")]
        nonces = {c.qid: f"n{i}" for i, c in enumerate(p213)}
        note_qids = {c.qid: opaque_note_qid(c.qid, nonces[c.qid])
                     for c in p213}
        text = render_note(p213, note_date="2026-07-18", run_id="r",
                            segment=1, budget={"max": 4, "reflective": 0},
                            reveals=None, nonces=nonces, note_qids=note_qids)
        shown = re.findall(r"<!-- qid: (.+?) -->", text)
        assert len(shown) == 4
        assert all(re.fullmatch(r"p213:[0-9a-f]{12}", q) for q in shown)
        for c in p213:
            assert c.qid not in text        # the real qid never reaches ink

        # the strengthened blinding assertion: whole blocks, comments included.
        qblocks = [b for b in re.split(r"\n\n(?=## Q)", text)
                   if b.startswith("## Q")]
        normalized = set()
        for i, b in enumerate(qblocks, start=1):
            b = b.rstrip("\n")          # the note's own single trailing \n
            b = b.replace(f"## Q{i}", "## QN")
            b = re.sub(r"p213:[0-9a-f]{12}", "p213:HASH", b)
            b = re.sub(r"`[^`]*`", "`X`", b)
            normalized.add(b)
        assert len(normalized) == 1, (
            "docket-arm and random-arm blocks must be byte-identical once "
            f"the opaque alias and the subject are normalized; got {normalized}")

    def test_opaque_qid_roundtrip_through_ledger(self, tmp_path):
        """IMPORTANT 3, the join: the LEDGER keeps the real qid; the note
        carries only the alias (stored as ``note_qid`` in forecasts.jsonl);
        parse -> ``resolve_note_qids`` -> outcomes/ratings/reveals all land
        under the real qid, and a later note's Reveals prints the alias."""
        from oracle_notes import opaque_note_qid, resolve_note_qids
        ledger = OracleLedger(tmp_path)
        real = "p213:scan:Ideas"
        alias = opaque_note_qid(real, "n0")
        cand = QuestionCandidate(qid=real, tier="quick",
                                 text="What is `Ideas`? One line is plenty.",
                                 why="w", settles="s", forecast="unknown",
                                 arm="docket")
        text = render_note([cand], note_date="2026-07-18", run_id="r",
                            segment=1, budget={"max": 4, "reflective": 0},
                            reveals=None, nonces={real: "n0"},
                            note_qids={real: alias})
        ledger.record_asked("2026-07-18", real, "quick", "unknown",
                             seal("unknown", "n0"), nonce="n0", arm="docket",
                             segment=1, text=cand.text, note_qid=alias)
        assert f"<!-- qid: {alias} -->" in text
        assert real not in text

        answered = text.replace("**A:**", "**A:** a folder of drafts", 1)
        answered = answered.replace("**R:** (trivial | non-trivial)",
                                     "**R:** non-trivial", 1)
        parsed = resolve_note_qids(parse_note(answered),
                                    ledger.note_qid_map())
        assert parsed.answers == {real: "a folder of drafts"}
        assert parsed.ratings == {real: "non-trivial"}

        reveals = ledger.build_reveals(parsed)
        assert [r["qid"] for r in reveals] == [real]
        nxt = render_note([], note_date="2026-07-25", run_id="r", segment=2,
                           budget=dict(DEFAULT_BUDGET), reveals=reveals)
        assert alias in nxt
        assert real not in nxt              # Reveals must not leak it later


class TestP213Report:
    """``p2_13_report`` — the pass/fail/ceiling verdict read off the
    ledger."""

    def test_pass_with_25_point_margin_over_two_segments(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        for seg in (1, 2):
            for i in range(2):     # docket arm: both non-trivial -> rate 1.0
                qid = f"d{seg}_{i}"
                ledger.record_asked("2026-07-01", qid, "quick", "unknown",
                                     seal("unknown"), arm="docket", segment=seg)
                ledger.record_rating(qid, "non-trivial", "2026-07-01")
            for i, rating in enumerate(["non-trivial", "trivial"]):
                qid = f"r{seg}_{i}"     # random arm: one hit -> rate 0.5
                ledger.record_asked("2026-07-01", qid, "quick", "unknown",
                                     seal("unknown"), arm="random", segment=seg)
                ledger.record_rating(qid, rating, "2026-07-01")

        report = p2_13_report(ledger)
        assert report["verdict"] == "pass"
        assert report["hits"] == 2
        for seg in (1, 2):
            assert report["segments"][seg]["docket_rate"] == 1.0
            assert report["segments"][seg]["random_rate"] == 0.5
            assert report["segments"][seg]["uninformative"] is False

    def test_fails_under_25_points(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        for seg in (1, 2):
            for arm, ratings in (("docket", ["non-trivial", "trivial"]),
                                 ("random", ["non-trivial", "trivial"])):
                for i, rating in enumerate(ratings):
                    qid = f"{arm}{seg}_{i}"
                    ledger.record_asked("2026-07-01", qid, "quick", "unknown",
                                         seal("unknown"), arm=arm, segment=seg)
                    ledger.record_rating(qid, rating, "2026-07-01")

        report = p2_13_report(ledger)
        assert report["verdict"] == "fail"
        assert report["hits"] == 0
        for seg in (1, 2):
            assert report["segments"][seg]["docket_rate"] == 0.5
            assert report["segments"][seg]["random_rate"] == 0.5

    def test_reask_row_never_erases_the_arm(self, tmp_path):
        """Whole-branch review IMPORTANT 2 (2026-07-19): the report's qid
        join was last-write-wins over ``forecasts.jsonl`` — a drift re-ask
        row (``arm=None``) for a formerly-armed qid erased its arm, dropping
        it from both rates while its rating still counted elsewhere. The
        join now reads each qid's EARLIEST ARMED row, so a re-ask can never
        move or erase the original arm/segment attribution."""
        ledger = OracleLedger(tmp_path)
        for seg in (1, 2):
            for i in range(2):     # docket arm: both non-trivial -> rate 1.0
                qid = f"d{seg}_{i}"
                ledger.record_asked("2026-07-01", qid, "quick", "unknown",
                                     seal("unknown"), arm="docket", segment=seg)
                ledger.record_rating(qid, "non-trivial", "2026-07-01")
            for i, rating in enumerate(["non-trivial", "trivial"]):
                qid = f"r{seg}_{i}"     # random arm: one hit -> rate 0.5
                ledger.record_asked("2026-07-01", qid, "quick", "unknown",
                                     seal("unknown"), arm="random", segment=seg)
                ledger.record_rating(qid, rating, "2026-07-01")
        before = p2_13_report(ledger)

        # the re-ask row: same qid, arm=None, a later segment — the exact
        # shape the driver writes when reask_candidate repeats d1_0 verbatim.
        ledger.record_asked("2026-07-20", "d1_0", "quick", "unknown",
                             seal("unknown"), arm=None, segment=3,
                             text="What is `X`? One line is plenty.")
        after = p2_13_report(ledger)

        assert after == before                       # neither rate moved
        assert after["segments"][1]["docket_rate"] == 1.0
        assert after["segments"][1]["docket_n"] == 2
        assert 3 not in after["segments"]            # no phantom bucket

    def test_rated_arm_none_rows_never_reach_the_ceiling(self, tmp_path):
        """IMPORTANT 2, second half: a rated ``arm=None`` question (the
        standing reflective, a re-ask) must not dilute — or trip — the
        ceiling canary, which reads the instrument's own discriminating
        power off the ARMED questions alone."""
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-01", "q_d", "quick", "unknown",
                             seal("unknown"), arm="docket", segment=1)
        ledger.record_rating("q_d", "non-trivial", "2026-07-01")
        ledger.record_asked("2026-07-01", "q_r", "quick", "unknown",
                             seal("unknown"), arm="random", segment=1)
        ledger.record_rating("q_r", "trivial", "2026-07-01")
        # eight rated arm-None rows in the same segment: under the old join
        # they push all_non_trivial/all_total to 9/10 >= 0.9 -> uninformative.
        for i in range(8):
            qid = f"refl{i}"
            ledger.record_asked("2026-07-01", qid, "reflective", "unknown",
                                 seal("unknown"), arm=None, segment=1)
            ledger.record_rating(qid, "non-trivial", "2026-07-01")

        report = p2_13_report(ledger)
        seg = report["segments"][1]
        assert seg["uninformative"] is False
        assert seg["docket_rate"] == 1.0 and seg["docket_n"] == 1
        assert seg["random_rate"] == 0.0 and seg["random_n"] == 1

    def test_ceiling_segment_flagged_uninformative(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        for i in range(4):
            arm = "docket" if i < 2 else "random"
            qid = f"c_{i}"
            ledger.record_asked("2026-07-01", qid, "quick", "unknown",
                                 seal("unknown"), arm=arm, segment=1)
            ledger.record_rating(qid, "non-trivial", "2026-07-01")

        report = p2_13_report(ledger)
        assert report["segments"][1]["uninformative"] is True
        # the only segment is uninformative -> nothing to compare
        assert report["verdict"] == "insufficient_data"
        assert report["informative_segments"] == 0


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


class TestMalformedRowResilience:
    """NEW-1 (whole-branch re-review, 2026-07-20): a live-verified crash —
    one qid-less row hand-injected into a real ``outcomes.jsonl`` raised
    ``KeyError: 'qid'`` inside ``OracleLedger.record_outcome_once`` and
    would have crashed every subsequent driver pass identically. Every
    keyed ledger read must tolerate a malformed row (unparseable line,
    non-dict row, or a valid dict missing the key that read needs),
    counting it in ``skipped_rows`` rather than raising or silently
    dropping it."""

    def test_read_all_skips_corrupt_line_and_counts_it(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        ledger.record_outcome("q1", "answered", "fine", "2026-07-18")
        with open(ledger._outcomes_path, "a", encoding="utf-8") as f:
            f.write('{"qid": "q2", "status": "answered",\n')   # torn mid-object
            f.write("not json at all\n")
            f.write("42\n")                                    # valid JSON, not a dict
        rows = ledger.outcomes()                                # must not raise
        assert [r["qid"] for r in rows] == ["q1"]
        assert ledger.skipped_rows == 3

    def test_keyed_reads_skip_rows_missing_their_key_and_count_it(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        ledger.record_outcome_once("q1", "answered", "kept", "2026-07-18")
        ledger._append(ledger._outcomes_path, {
            "status": "answered", "answer_text": "orphaned",
            "answered_note_date": "2026-07-19",
        })  # no "qid" key
        # record_outcome_once's own read must not crash on the orphan row,
        # and must still correctly recognize q1's unchanged answer as a
        # duplicate (not re-append it).
        assert ledger.record_outcome_once(
            "q1", "answered", "kept", "2026-07-18") is False
        assert ledger.skipped_rows >= 1
        # has_prior_answer must tolerate the same orphan row.
        assert ledger.has_prior_answer("q1") is True
        assert ledger.has_prior_answer("nonexistent") is False

    def test_forecasts_row_missing_forecast_plain_is_skipped_in_reveals(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        ledger._append(ledger._forecasts_path, {
            "note_date": "2026-07-18", "qid": "q1", "tier": "quick",
            # "forecast_plain" / "forecast_hash" missing entirely
        })
        parsed = ParsedNote(budget={"max": 5, "reflective": 1},
                             answers={"q1": "some answer"})
        reveals = ledger.build_reveals(parsed)                  # must not raise
        assert reveals == []
        assert ledger.skipped_rows >= 1


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
    ``runs_dir``, and the checked-in fixture tree is never mutated.

    Docket item 10, review finding (2026-07-19): ``--p213`` now defaults ON
    (the pre-registered RUN 13 launch command carries no flag at all, so an
    off-by-default instrument would never run). Every test in this class
    that exercises the ORIGINAL V2a.1 provenance/journal/horizon mix (all of
    them, below) passes ``--no-p213`` explicitly to keep testing that mix;
    ``TestP213DefaultOn`` (further down) covers the new no-flag default."""

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

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
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

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
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

        # Review finding (2026-07-19): the three early-return paths of
        # ``_run_oracle`` bank exactly as the final ("note written") path
        # does — invocation 2 above hit the "no questions this cycle" guard
        # (a genuine early return, not the note-written branch covered by
        # ``test_e2e_banks_answered_note_into_author_model`` below) yet still
        # recorded two fresh "answered" rows (qids[0], qids[2]) into the
        # ledger earlier in that same call. A regression that banks only on
        # the final return would silently defer those two answers by a
        # whole oracle pass; pin that it does not.
        from tomos_service import TomosService
        svc = TomosService(runs_dir)
        uod = svc.load_uod("vault_v0_author_model")
        assert uod is not None
        assert len(uod.current_egi.quotation) == 2

    def test_e2e_banks_answered_note_into_author_model(self, tmp_path, capsys):
        """V2a.2 item (2), Task 5: run 1 writes a questions note; the author
        answers one question genuinely (declines two, ignores two — enough
        to be "substantially answered"); run 2 reads it back AND banks the
        one genuine answer into the cumulative author-model UoD
        (``vault_v0_author_model``): exactly one quotation cell, one
        gate-shaped ``BANK_TO_M`` step, the digest surfacing only a COUNT.
        Custody: the answer's prose never reaches stdout."""
        from tomos_service import TomosService
        mod = self._main()
        runs_dir = tmp_path / "runs"
        ANSWER = "Collected it from a conference talk in 2019."

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        out1 = capsys.readouterr().out
        assert "questions_written: 5 → Arisbe/Questions-2026-07-18.md" in out1

        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        assert len(qids) == 5

        text = self._answer(text, qids[0], ANSWER)       # the one genuine answer
        text = self._answer(text, qids[1], "declined")
        text = self._answer(text, qids[2], "declined")
        # qids[3], qids[4] left blank -> ignored
        note1.write_text(text, encoding="utf-8")

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0
        out2 = capsys.readouterr().out
        assert "'banked': 1" in out2

        svc = TomosService(runs_dir)
        uod = svc.load_uod("vault_v0_author_model")
        assert uod is not None
        assert len(uod.current_egi.quotation) == 1

        chain = svc.load_chain("vault_v0_author_model")
        (step,) = [s for s in chain.steps
                   if s.parameters.get("act") == "quotation"]
        assert step.parameters["provenance"] == "oracle-answer"
        assert step.parameters["qid"] == qids[0]

        # custody: the answer's prose is banked into the side-store (chain
        # params / UoD JSON) but must never reach stdout
        assert ANSWER not in out1 and ANSWER not in out2

    def test_bank_skipped_when_world_scroll_missing(self, tmp_path, capsys, monkeypatch):
        """MINOR review finding: the defensive ``bank_skipped`` branch of
        ``_bank_author_model`` (a missing world-scroll — should never happen
        against the live loop's already-resident M, but must never crash the
        oracle pass over it) had zero test evidence. Force it by
        monkeypatching ``find_world_scroll`` as imported into
        ``tools/run_vault_v0`` so it reports "no residence" for every call,
        then drive one oracle pass that would otherwise bank a genuine
        answer — the pass must still complete (``rc == 0``) and the digest
        must report the skip as a count, never a raise."""
        mod = self._main()
        monkeypatch.setattr(mod, "find_world_scroll", lambda egi: None)
        runs_dir = tmp_path / "runs"

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        text = self._answer(text, qids[0], "an answer that would otherwise bank")
        note1.write_text(text, encoding="utf-8")

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0                      # never raises despite the missing residence
        out2 = capsys.readouterr().out
        assert "'banked': 0" in out2
        assert "'bank_skipped': 1" in out2

        from tomos_service import TomosService
        # the skip path never reaches the save call at all
        assert TomosService(runs_dir).load_uod("vault_v0_author_model") is None

    def test_long_answer_now_banks_successfully_via_content_derived_id(
            self, tmp_path, capsys):
        """Was ``test_long_answer_bank_failure_is_caught_skipped_and_counted``
        (whole-branch review, CRITICAL 1): a long, realistic answer used to
        bank as a vertex label big enough to straddle its quotation cell's
        drawn area — ``CorrespondenceViolation`` (occlusion) at the
        ``save_uod_with_chain`` §3.3 boundary inside ``_bank_author_model``
        (measured threshold ~52 chars passes / ~53 fails, scratch-script
        binary search, independent of the surrounding M's size), caught and
        counted as ``bank_failed`` rather than crashing.

        The author's ruling fixes the underlying cause instead of only
        catching it: ``oracle_notes.answer_label`` swaps a too-long answer's
        verbatim prose for a short, deterministic, content-derived id before
        it ever becomes a vertex label, so this exact input now BANKS
        SUCCESSFULLY — ``banked: 1``, no ``bank_failed`` at all — and its
        id -> original mapping lands in the gitignored ``labels.json``
        sidecar (the ``vault_world.long_labels`` precedent). The
        ``bank_failed`` safety net itself is retained (see
        ``TestBankFailedSafetyNet`` below) for whatever this bound doesn't
        anticipate; it is no longer reachable from a mere long answer."""
        mod = self._main()
        runs_dir = tmp_path / "runs"
        ANSWER = ("This one took a while to answer honestly — I mostly "
                  "journal at night about what already happened that day, "
                  "catching up rather than narrating live.")
        assert len(ANSWER) > 100          # well past the measured ~53-char cliff

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        out1 = capsys.readouterr().out

        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        text = self._answer(text, qids[0], ANSWER)   # the one genuine answer
        text = self._answer(text, qids[1], "declined")
        text = self._answer(text, qids[2], "declined")
        note1.write_text(text, encoding="utf-8")

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0
        out2 = capsys.readouterr().out
        assert "'banked': 1" in out2
        assert "bank_failed" not in out2

        from oracle_notes import answer_label
        from tomos_service import TomosService
        uod = TomosService(runs_dir).load_uod("vault_v0_author_model")
        assert uod is not None
        assert len(uod.current_egi.quotation) == 1

        expected_label, expected_sidecar = answer_label(ANSWER)
        assert expected_sidecar                       # ANSWER is over the bound
        import json
        sidecar = json.loads((runs_dir / "labels.json").read_text())
        assert sidecar[expected_label] == ANSWER

        # custody: the answer's prose never reaches stdout, whichever pass —
        # unchanged even though it now lives in labels.json and the UoD too,
        # both gitignored under runs_dir.
        assert ANSWER not in out1 and ANSWER not in out2

    def test_bank_failed_net_still_catches_a_genuine_save_exception(
            self, tmp_path, capsys, monkeypatch):
        """The ``bank_failed``/``bank_failed_kind`` safety net (whole-branch
        review, CRITICAL 1) is retained for whatever the ``answer_label``
        bound doesn't anticipate — but a long answer is no longer such a
        case (see the test above), so there is no longer an INPUT any
        author could type that reaches it. This exercises the net itself
        via a monkeypatched failure at the save boundary (an honest stand-in
        for a disk-full/permissions error) rather than fabricating a bogus
        "un-bankable answer": the net must still catch, count, and report
        the exception's class name, never crashing ``main``."""
        mod = self._main()
        runs_dir = tmp_path / "runs"

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        text = self._answer(text, qids[0], "a perfectly ordinary short answer")
        note1.write_text(text, encoding="utf-8")

        from tomos_service import TomosService
        real_save = TomosService.save_uod_with_chain

        def _boom(self, uod, chain, *a, **kw):
            # Only the author-model checkpoint save fails — the segment
            # save (which runs first, every invocation) must go through
            # untouched or this test would never reach _bank_author_model.
            if uod.uod_id == "vault_v0_author_model":
                raise IOError("simulated disk-full")
            return real_save(self, uod, chain, *a, **kw)

        monkeypatch.setattr(TomosService, "save_uod_with_chain", _boom)

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0                     # never crashes
        out2 = capsys.readouterr().out
        assert "'banked': 0" in out2
        assert "'bank_failed': 1" in out2
        assert "'bank_failed_kind': 'OSError'" in out2   # IOError is an OSError alias

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

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
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

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
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

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
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

        rc1 = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
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
        rc2 = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                        "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc2 == 0
        out2 = capsys.readouterr().out
        assert "oracle: today's note already exists - not overwriting" in out2
        assert note1.read_bytes() == answered_bytes

        # third invocation, SAME note-date again: still untouched, and the
        # ledger stayed idempotent across both re-polls (no duplicate rows)
        rc3 = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
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

    def test_qidless_outcome_row_never_crashes_the_driver(self, tmp_path, capsys):
        """NEW-1 (whole-branch re-review, 2026-07-20): the reviewer
        hand-injected one qid-less row into a real ``outcomes.jsonl`` and
        drove the driver; it crashed with ``KeyError: 'qid'`` inside
        ``OracleLedger.record_outcome_once`` and would crash every
        subsequent pass identically (the downstream ``bank_malformed``
        guard in ``_bank_author_model`` sits after this point, so it never
        fired). Now the row is skipped and counted, never fatal."""
        mod = self._main()
        runs_dir = tmp_path / "runs"

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        text = self._answer(text, qids[0], "a genuine answer")
        note1.write_text(text, encoding="utf-8")

        # Hand-inject exactly the reviewer's reproduction: a valid JSON
        # object with an "answered" status but no "qid" key at all.
        ledger_dir = runs_dir / "oracle"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        with open(ledger_dir / "outcomes.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "status": "answered", "answer_text": "orphaned",
                "answered_note_date": "2026-07-01",
            }) + "\n")

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0                          # the crash the review reproduced
        out2 = capsys.readouterr().out
        assert "bank_malformed" in out2         # counted, not silently dropped

        # a fresh ledger instance over the same dir tolerates the row too:
        # has_prior_answer must not crash on it, and must count it (a
        # qid-requiring read, unlike the bare outcomes() scan above).
        ledger = OracleLedger(runs_dir / "oracle")
        assert ledger.outcomes()                # a further read still doesn't raise
        assert ledger.has_prior_answer("nonexistent-qid") is False
        assert ledger.skipped_rows >= 1

    def test_ledger_skip_events_reach_the_digest(self, tmp_path, capsys):
        """Review finding NEW-4 (2026-07-20): `_run_oracle`'s digest folds
        in ``ledger_skip_events`` (``OracleLedger.skipped_rows`` for this
        cycle), present only once at least one row was actually skipped,
        so a malformed row shows up in the digest even when it never
        touches ``bank_malformed`` (which only catches rows malformed in
        a way that also breaks banking). It is a SKIP-EVENT count, not a
        distinct-bad-row count: a single injected bad row is re-scanned by
        several reads within this ONE cycle (outcomes()/has_prior_answer/
        bankable_outcomes each rescan the whole file), so the reported
        count is expected to exceed 1 even though exactly one row is
        damaged — pinned below rather than asserted equal to the row
        count, since it is not a "rows lost" total."""
        mod = self._main()
        runs_dir = tmp_path / "runs"

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        out0 = capsys.readouterr().out
        assert "ledger_skip_events" not in out0      # nothing malformed yet

        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        text = self._answer(text, qids[0], "a genuine answer")
        note1.write_text(text, encoding="utf-8")

        # Same hand-injected qid-less row the crash reproduction above uses:
        # exactly ONE malformed row.
        ledger_dir = runs_dir / "oracle"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        with open(ledger_dir / "outcomes.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "status": "answered", "answer_text": "orphaned",
                "answered_note_date": "2026-07-01",
            }) + "\n")

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0
        out1 = capsys.readouterr().out
        m1 = re.search(r"'ledger_skip_events': (\d+)", out1)
        assert m1 is not None, out1
        # more than the single damaged row: the recount-on-every-read
        # behaviour, not a distinct-bad-row tally.
        assert int(m1.group(1)) > 1

        # a fresh ledger instance's OWN count for a single keyed scan is
        # exactly 1 (one bad row, one skip) — confirms the digest's larger
        # number came from repeated reads THIS cycle (`record_outcome_once`
        # scans the whole file once per answered qid, `bankable_outcomes`
        # scans it again, etc.), not from somehow finding more than one bad
        # row on disk. (`outcomes()` itself is an unfiltered raw read and
        # never increments this counter — only a keyed read does.)
        ledger = OracleLedger(runs_dir / "oracle")
        ledger.has_prior_answer("nonexistent-qid")
        assert ledger.skipped_rows == 1

    def test_torn_jsonl_line_never_crashes_the_driver(self, tmp_path, capsys):
        """NEW-1: a torn/corrupt JSONL line (the failure mode a killed
        process mid-``_append`` could leave) must be skipped by
        ``_read_all``'s per-line guard, not raise ``json.JSONDecodeError``
        into the driver on every future pass."""
        mod = self._main()
        runs_dir = tmp_path / "runs"

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        note1 = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note1.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        text = self._answer(text, qids[0], "a genuine answer")
        note1.write_text(text, encoding="utf-8")

        ledger_dir = runs_dir / "oracle"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        with open(ledger_dir / "outcomes.jsonl", "a", encoding="utf-8") as f:
            f.write('{"qid": "orphan", "status": "answered", "answer_text":\n')

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0                          # never raises on the torn line

        ledger = OracleLedger(runs_dir / "oracle")
        ledger.outcomes()                       # forces a re-read; must not raise
        assert ledger.skipped_rows >= 1


class TestP213DefaultOn:
    """Review finding (2026-07-19), CRITICAL: the pre-registered RUN 13
    launch command (``--rounds 200 --segments 3``, no flag at all) must
    actually drive the P2^13 instrument — an off-by-default flag would let
    the criterion go silently unanswered again, the exact charge item ⑩
    exists to fix. These tests call ``main`` with NO ``--p213``/
    ``--no-p213`` flag at all — the real launch shape."""

    @staticmethod
    def _main():
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        import run_vault_v0
        return run_vault_v0

    def test_no_flag_drives_the_p213_instrument_by_default(self, tmp_path, capsys):
        mod = self._main()
        runs_dir = tmp_path / "runs"

        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "questions_written" in out

        note = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        assert qids   # never a zero-question note

        # the V2a.1 provenance/journal/horizon sources are NOT in play —
        # every non-reflective qid is P2^13-instrument-shaped.
        non_reflective = [q for q in qids if q != "journal-timelines"]
        assert non_reflective   # at least the random arm always has candidates
        assert all(q.startswith("p213:") for q in non_reflective)
        assert not any(q.startswith(("prov:", "journal:", "horizon:"))
                        for q in qids)

        # blinding: no arm word anywhere in the rendered note.
        assert "docket" not in text.lower()
        assert "random" not in text.lower()
        assert "arm" not in text.lower()

        # IMPORTANT 3 (whole-branch review, 2026-07-19): qid structure must
        # not distinguish arms either — every p213 comment qid is the opaque
        # alias, never a want-key (p213:scan:...) or relpath (p213:x.md)
        # shape the author could partition by in source mode.
        assert all(re.fullmatch(r"p213:[0-9a-f]{12}", q)
                   for q in non_reflective)

        # Minor 1: Arisbe's own pre-existing fixture note never becomes a
        # question subject (the random arm must exclude authored_by: arisbe).
        assert "Questions-2026-07-01.md" not in text

    def test_answers_to_opaque_qids_land_under_real_qids(self, tmp_path, capsys):
        """IMPORTANT 3, driver-wired: the author answers under the opaque
        alias; a later invocation must record outcomes/ratings under the
        REAL qid (translated through forecasts.jsonl's note_qid field), so
        the ledger and p2_13_report keep working."""
        mod = self._main()
        runs_dir = tmp_path / "runs"
        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-18"])
        assert rc == 0
        capsys.readouterr()

        note = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        text = note.read_text(encoding="utf-8")
        qids = re.findall(r"<!-- qid: (.+?) -->", text)
        # answer enough (>= half) to be substantially answered; rate one.
        to_answer = qids[: (len(qids) + 1) // 2 + 1]
        for q in to_answer:
            pattern = re.compile(
                rf"(<!-- qid: {re.escape(q)} -->.*?\*\*A:\*\*)", re.DOTALL)
            text, n = pattern.subn(lambda m: m.group(1) + " a real answer",
                                   text, count=1)
            assert n == 1
        text = text.replace("**R:** (trivial | non-trivial)",
                             "**R:** non-trivial", 1)
        note.write_text(text, encoding="utf-8")

        rc = mod.main(["--fixture", "--rounds", "30", "--segments", "1",
                       "--runs-dir", str(runs_dir), "--note-date", "2026-07-25"])
        assert rc == 0
        capsys.readouterr()

        ledger = OracleLedger(runs_dir / "oracle")
        real_qids = {f["qid"] for f in ledger.forecasts()}
        outs = ledger.outcomes()
        assert outs
        for o in outs:
            assert o["qid"] in real_qids
            assert not re.fullmatch(r"p213:[0-9a-f]{12}", o["qid"]), (
                "an outcome landed under the opaque alias, not the real qid")
        for r in ledger.ratings():
            assert r["qid"] in real_qids
            assert not re.fullmatch(r"p213:[0-9a-f]{12}", r["qid"])

    def test_no_p213_flag_still_restores_v2a1_mix(self, tmp_path, capsys):
        """The escape hatch: ``--no-p213`` must still work exactly as the
        (renamed) opt-out — this is what the four ``TestEndToEnd`` tests
        rely on."""
        mod = self._main()
        runs_dir = tmp_path / "runs"

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30",
                       "--segments", "1", "--runs-dir", str(runs_dir),
                       "--note-date", "2026-07-18"])
        assert rc == 0
        note = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        qids = re.findall(r"<!-- qid: (.+?) -->",
                           note.read_text(encoding="utf-8"))
        assert any(q.startswith("prov:") for q in qids)
        assert not any(q.startswith("p213:") for q in qids)


# --------------------------------------------------------------------------- #
# Docket item 11 (Examination IV, panel C) — the oracle hardening quartet     #
# --------------------------------------------------------------------------- #


class TestAskedEverExpiry:
    """Charge 1 (first half): ``asked_ever`` suppressed forever, contradicting
    spec thesis 3 ("wants age but persist; silence lowers priority, never
    deletes") and making drift unmeasurable BY DESIGN. The fix:
    ``asked_ever(qid, within_last_n_notes=None)`` — ``None`` keeps the
    forever-suppression; an int N means "asked within the last N distinct
    note dates" (re-eligible after)."""

    def test_default_none_keeps_forever_suppression(self, tmp_path):
        # PIN of existing behavior: the bare call and the explicit None are
        # the historical forever-suppressor, unchanged.
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-01-01", "q1", "quick", "collected",
                            seal("collected"))
        for i in range(2, 9):
            ledger.record_asked(f"2026-01-0{i}", f"d{i}", "quick", "unknown",
                                seal("unknown"))
        assert ledger.asked_ever("q1") is True
        assert ledger.asked_ever("q1", within_last_n_notes=None) is True

    def test_expires_after_n_distinct_note_dates(self, tmp_path):
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-01-01", "q1", "quick", "collected",
                            seal("collected"))
        for i in range(2, 5):   # three later distinct dates -> 4 total
            ledger.record_asked(f"2026-01-0{i}", f"d{i}", "quick", "unknown",
                                seal("unknown"))
        assert ledger.asked_ever("q1", within_last_n_notes=4) is True
        assert ledger.asked_ever("q1", within_last_n_notes=3) is False
        assert ledger.asked_ever("never-asked", within_last_n_notes=3) is False

    def test_window_reads_the_latest_asking(self, tmp_path):
        # q1 asked at date 1 AND re-asked at date 3 of 4: a window of 2
        # (covering dates 3-4) still sees it — the LATEST asking counts.
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-01-01", "q1", "quick", "collected",
                            seal("collected"))
        ledger.record_asked("2026-01-02", "d2", "quick", "unknown",
                            seal("unknown"))
        ledger.record_asked("2026-01-03", "q1", "quick", "collected",
                            seal("collected"))
        ledger.record_asked("2026-01-04", "d4", "quick", "unknown",
                            seal("unknown"))
        assert ledger.asked_ever("q1", within_last_n_notes=2) is True


class TestDriftReask:
    """Charge 1 (second half): the drift re-ask — ONE early answered question
    re-asked verbatim once >= 2 distinct note dates have passed since it was
    (last) asked. A changed answer lands as a NEW outcome row
    (``record_outcome_once`` already appends on change — pinned below, not
    re-implemented)."""

    @staticmethod
    def _seeded(tmp_path):
        from oracle_notes import reask_candidate
        ledger = OracleLedger(tmp_path)
        ledger.record_asked(
            "2026-07-01", "q1", "quick", "collected", seal("collected"),
            text="Is `X` collected from elsewhere, or your own writing?")
        ledger.record_outcome("q1", "answered", "collected from a talk",
                              "2026-07-02")
        ledger.record_asked("2026-07-02", "d2", "quick", "unknown",
                            seal("unknown"), text="What is `d2`?")
        ledger.record_asked("2026-07-03", "d3", "quick", "unknown",
                            seal("unknown"), text="What is `d3`?")
        return ledger, reask_candidate

    def test_reask_is_the_early_answered_question_verbatim(self, tmp_path):
        ledger, reask_candidate = self._seeded(tmp_path)
        c = reask_candidate(ledger)
        assert c is not None
        assert c.qid == "q1"
        assert c.text == "Is `X` collected from elsewhere, or your own writing?"
        assert c.forecast == "collected"

    def test_not_eligible_before_two_later_note_dates(self, tmp_path):
        from oracle_notes import reask_candidate
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-01", "q1", "quick", "collected",
                            seal("collected"), text="Is `X` collected?")
        ledger.record_outcome("q1", "answered", "yes", "2026-07-02")
        ledger.record_asked("2026-07-02", "d2", "quick", "unknown",
                            seal("unknown"), text="What is `d2`?")
        assert reask_candidate(ledger) is None   # only ONE later note date

    def test_unanswered_question_is_never_reasked(self, tmp_path):
        from oracle_notes import reask_candidate
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-01", "q1", "quick", "collected",
                            seal("collected"), text="Is `X` collected?")
        ledger.record_outcome("q1", "ignored", "", "2026-07-02")
        ledger.record_asked("2026-07-02", "d2", "quick", "unknown",
                            seal("unknown"), text="t2")
        ledger.record_asked("2026-07-03", "d3", "quick", "unknown",
                            seal("unknown"), text="t3")
        assert reask_candidate(ledger) is None   # drift needs a prior answer

    def test_legacy_row_without_text_is_skipped(self, tmp_path):
        # A pre-item-11 forecasts row stored no question text; there is
        # nothing to re-ask VERBATIM, so it is honestly skipped, never
        # reconstructed.
        from oracle_notes import reask_candidate
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-01", "q1", "quick", "collected",
                            seal("collected"))          # no text
        ledger.record_outcome("q1", "answered", "yes", "2026-07-02")
        ledger.record_asked("2026-07-02", "d2", "quick", "unknown",
                            seal("unknown"), text="t2")
        ledger.record_asked("2026-07-03", "d3", "quick", "unknown",
                            seal("unknown"), text="t3")
        assert reask_candidate(ledger) is None

    def test_reask_resets_its_own_clock(self, tmp_path):
        # Once re-asked (a fresh forecasts row at a later date), the same
        # question needs two MORE note dates before it is eligible again —
        # the cap that keeps one question from being re-asked every note.
        ledger, reask_candidate = self._seeded(tmp_path)
        c = reask_candidate(ledger)
        ledger.record_asked("2026-07-10", c.qid, c.tier, c.forecast,
                            seal(c.forecast), text=c.text)
        assert reask_candidate(ledger) is None

    def test_changed_answer_appends_new_row_first_intact(self, tmp_path):
        # PIN of existing behavior (record_outcome_once appends on change) —
        # verified here because the drift measurement depends on it, NOT
        # re-implemented.
        ledger = OracleLedger(tmp_path)
        assert ledger.record_outcome_once("q1", "answered", "old answer",
                                          "2026-07-02") is True
        assert ledger.record_outcome_once("q1", "answered", "old answer",
                                          "2026-07-02") is False  # idempotent
        assert ledger.record_outcome_once("q1", "answered", "new answer",
                                          "2026-07-14") is True   # change appends
        rows = [r for r in ledger.outcomes() if r["qid"] == "q1"]
        assert [r["answer_text"] for r in rows] == ["old answer", "new answer"]


class TestDeclineSynonyms:
    """Charge 2: only exactly ``"declined"`` counted as a decline;
    ``"Declined."``, ``"pass"``, ``"—"`` were banked VERBATIM as answers and
    reprinted in the next note's Reveals — the refusal's own wording became
    retained data. Fixed by a normalized synonym set matched after
    strip / rstrip(".") / casefold."""

    @staticmethod
    def _note_with_answer(answer: str) -> str:
        cand = QuestionCandidate(qid="q1", tier="quick", text="Is `X` yours?",
                                 why="w", settles="s", forecast="collected")
        text = render_note([cand], note_date="2026-07-18", run_id="r",
                           segment=1, budget=dict(DEFAULT_BUDGET), reveals=None)
        return text.replace("**A:**", f"**A:** {answer}", 1)

    @pytest.mark.parametrize("marker", [
        "declined", "Declined.", "DECLINE", "decline", "pass", "Pass.",
        "—", "-", "rather not", "Rather not.", "prefer not to say",
        "Prefer not to say.",
    ])
    def test_marker_reads_declined(self, marker):
        parsed = parse_note(self._note_with_answer(marker))
        assert parsed.declined == {"q1"}, marker
        assert not parsed.answers

    @pytest.mark.parametrize("genuine", [
        "passing thoughts on this", "I pass it around sometimes",
        "declined the invitation, but kept the notes",
        "yes - collected from a talk",
    ])
    def test_genuine_answer_is_never_swallowed(self, genuine):
        # Overmatch guard: a real answer merely CONTAINING a marker word
        # stays an answer.
        parsed = parse_note(self._note_with_answer(genuine))
        assert parsed.answers == {"q1": genuine}
        assert not parsed.declined

    def test_declined_text_never_reaches_reveals(self, tmp_path):
        # The named test: a declined answer's text NEVER appears in a
        # subsequent note's Reveals — the refusal's wording is not data.
        ledger = OracleLedger(tmp_path)
        ledger.record_asked("2026-07-18", "q1", "quick", "collected",
                            seal("collected"), text="Is `X` yours?")
        parsed = parse_note(self._note_with_answer("Pass."))
        assert parsed.declined == {"q1"}
        reveals = ledger.build_reveals(parsed)
        assert reveals == []           # a decline carries nothing to score
        next_note = render_note(
            [QuestionCandidate(qid="q2", tier="quick", text="Next?",
                               why="w", settles="s", forecast="unknown")],
            note_date="2026-07-25", run_id="r", segment=2,
            budget=dict(DEFAULT_BUDGET), reveals=reveals or None)
        assert "Pass" not in next_note


class TestDocket11Driver:
    """Charge 1 wired through the driver (``tools/run_vault_v0.py``): the
    asked_ever window (default 6) makes an old question re-eligible; the
    drift re-ask lands verbatim in a new note; a changed answer is counted
    as ``drift_data`` in the oracle digest; and charge 4's ``m_added``/
    ``m_removed`` appear in the per-segment digest."""

    PROV_QID = "prov:Clippings/saved page.md"

    @staticmethod
    def _main():
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        import run_vault_v0
        return run_vault_v0

    @staticmethod
    def _answer(text: str, qid: str, answer: str) -> str:
        pattern = re.compile(
            rf"(<!-- qid: {re.escape(qid)} -->.*?\*\*A:\*\*)", re.DOTALL)
        new_text, n = pattern.subn(
            lambda m: m.group(1) + " " + answer, text, count=1)
        assert n == 1, f"qid {qid} not found in note"
        return new_text

    def test_expired_qid_reappears_through_the_driver_window(self, tmp_path):
        # Asked 7 distinct note dates ago with a 6-note window: re-eligible,
        # so the fixture's prov question is asked AGAIN (previously: never).
        mod = self._main()
        runs_dir = tmp_path / "runs"
        ledger = OracleLedger(runs_dir / "oracle")
        ledger.record_asked("2026-06-01", self.PROV_QID, "quick", "collected",
                            seal("collected"))
        for i in range(2, 8):   # six later distinct dates
            ledger.record_asked(f"2026-06-0{i}", f"dummy:{i}", "quick",
                                "unknown", seal("unknown"))
        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30",
                       "--segments", "1", "--runs-dir", str(runs_dir),
                       "--note-date", "2026-07-18"])
        assert rc == 0
        note = runs_dir / "arisbe_notes" / "Questions-2026-07-18.md"
        qids = re.findall(r"<!-- qid: (.+?) -->",
                          note.read_text(encoding="utf-8"))
        assert self.PROV_QID in qids

    def test_drift_reask_verbatim_and_digest_counts(self, tmp_path, capsys):
        mod = self._main()
        runs_dir = tmp_path / "runs"
        marker_text = ("Is `Clippings/saved page.md` collected from "
                       "elsewhere, or your own writing? [reask-verbatim]")
        ledger = OracleLedger(runs_dir / "oracle")
        ledger.record_asked("2026-07-01", self.PROV_QID, "quick", "collected",
                            seal("collected"), text=marker_text)
        ledger.record_outcome(self.PROV_QID, "answered",
                              "collected from a talk", "2026-07-02")
        ledger.record_asked("2026-07-02", "dummy:a", "quick", "unknown",
                            seal("unknown"), text="What is `a`?")
        ledger.record_asked("2026-07-03", "dummy:b", "quick", "unknown",
                            seal("unknown"), text="What is `b`?")

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30",
                       "--segments", "1", "--runs-dir", str(runs_dir),
                       "--note-date", "2026-07-10"])
        assert rc == 0
        out1 = capsys.readouterr().out
        # charge 4's digest split, wired through the driver:
        assert "'m_added'" in out1 and "'m_removed'" in out1

        note = runs_dir / "arisbe_notes" / "Questions-2026-07-10.md"
        text = note.read_text(encoding="utf-8")
        # the re-ask is VERBATIM (the stored text, marker included — never
        # regenerated from the world), capped at one:
        assert marker_text in text
        assert text.count(f"<!-- qid: {self.PROV_QID} -->") == 1

        # the author's answer CHANGED since the first asking:
        text = self._answer(text, self.PROV_QID,
                            "actually it is my own writing")
        note.write_text(text, encoding="utf-8")

        rc = mod.main(["--fixture", "--no-p213", "--rounds", "30",
                       "--segments", "1", "--runs-dir", str(runs_dir),
                       "--note-date", "2026-07-14"])
        assert rc == 0
        out2 = capsys.readouterr().out
        assert "'drift_data': 1" in out2

        rows = [r for r in ledger.outcomes()
                if r["qid"] == self.PROV_QID and r["status"] == "answered"]
        # a changed answer lands as a NEW row; the first row is intact:
        assert [r["answer_text"] for r in rows] == [
            "collected from a talk", "actually it is my own writing"]


# --------------------------------------------------------------------------- #
# V2a.2 item (2): quotation-cell banking — the pure construction               #
# --------------------------------------------------------------------------- #

PROSE = 'A line.\nWith "q", ~[ b ], and \\.'
"""Kept at or under ``oracle_notes._MAX_ANSWER_LABEL`` (32 chars) — these
tests exercise the VERBATIM banking path (newline/quotes/brackets/backslash
survive untouched), not the long-answer digested-id path (see
``TestBankAnswerLongProse`` below for that)."""


def _resident_m():
    from egif_parser_dau import parse_egif
    from world_scroll import wrap_state
    m, _scroll = wrap_state(parse_egif('(swan "Alba")'))
    return m


class TestBankAnswer:
    def test_banked_shape_and_same_area_attachment(self):
        from oracle_notes import bank_answer
        from world_scroll import find_world_scroll
        m2, cut_id = bank_answer(_resident_m(), PROSE, qid="q1",
                                 note_date="2026-07-19")
        assert len(m2.quotation) == 1 and cut_id in m2.quotation
        name_vid = m2.quotation[cut_id]
        # oval and quoting name share an area, inside a world-scroll cell
        assert m2.get_context(cut_id) == m2.get_context(name_vid)
        scroll = find_world_scroll(m2)
        assert m2.get_context(name_vid) in scroll.cell_ids

    def test_prose_banked_verbatim_and_lifted_back(self):
        from oracle_notes import bank_answer
        from quotation_overlay import lift_quotation
        m2, cut_id = bank_answer(_resident_m(), PROSE, qid="q1",
                                 note_date="2026-07-19")
        lifted = lift_quotation(m2, cut_id)
        labels = [v.label for v in lifted.V if v.label is not None]
        assert labels == [PROSE]                       # verbatim, newline+quotes intact
        assert [lifted.rel[e.id] for e in lifted.E] == ["utterance"]

    def test_mention_not_use(self):
        from oracle_notes import bank_answer
        from agon_evolution import sheet_atom_keys, atom_key
        m = _resident_m()
        m2, _ = bank_answer(m, PROSE, qid="q1", note_date="2026-07-19")
        keys = sheet_atom_keys(m2)
        assert atom_key("asserted", ["author", None]) in keys   # the act, asserted
        assert not any("utterance" in k for k in keys)          # the content, mentioned only
        # the pre-existing standing ink is untouched
        assert atom_key("swan", ["Alba"]) in keys

    def test_structural_round_trip_preserves_banked_cell(self):
        from oracle_notes import bank_answer
        from quotation_overlay import lift_quotation
        from egi_io import to_dict, from_dict
        from eg_navigation import same_graph
        m2, cut_id = bank_answer(_resident_m(), PROSE, qid="q1",
                                 note_date="2026-07-19")
        back = from_dict(to_dict(m2))
        assert same_graph(m2, back)
        assert len(back.quotation) == 1
        (cut2,) = back.quotation
        labels = [v.label for v in lift_quotation(back, cut2).V
                  if v.label is not None]
        assert labels == [PROSE]

    def test_refuses_without_residence(self):
        from oracle_notes import bank_answer
        from egif_parser_dau import parse_egif
        import pytest as _pytest
        with _pytest.raises(ValueError):
            bank_answer(parse_egif('(swan "Alba")'), PROSE,
                        qid="q1", note_date="2026-07-19")


# --------------------------------------------------------------------------- #
# The author's ruling: long prose banks a content-derived id, not verbatim,   #
# with the original recorded in a sidecar the caller persists — the fix for  #
# the §3.3 occlusion wall (measured 52 chars passes / 53 fails) that a raw    #
# verbatim label past ~a few dozen characters could hit.                     #
# --------------------------------------------------------------------------- #

LONG_PROSE = ("This one took a while to answer honestly — I mostly journal "
              "at night about what already happened that day, catching up "
              "rather than narrating live.")


class TestAnswerLabel:
    def test_short_prose_is_verbatim_with_empty_sidecar(self):
        from oracle_notes import answer_label
        label, sidecar = answer_label(PROSE)
        assert label == PROSE
        assert sidecar == {}

    def test_prose_at_exactly_the_bound_is_verbatim(self):
        from oracle_notes import answer_label, _MAX_ANSWER_LABEL
        prose = "x" * _MAX_ANSWER_LABEL
        label, sidecar = answer_label(prose)
        assert label == prose
        assert sidecar == {}

    def test_long_prose_gets_a_short_content_derived_id(self):
        from oracle_notes import answer_label, _MAX_ANSWER_LABEL
        label, sidecar = answer_label(LONG_PROSE)
        assert label != LONG_PROSE
        assert len(label) <= _MAX_ANSWER_LABEL
        assert sidecar == {label: LONG_PROSE}

    def test_deterministic_across_calls(self):
        """The hard constraint: the id is a PURE function of the prose alone
        — no counter, nonce, uuid, or clock — because the standing polarity
        gate replays ``bank_answer`` from recorded chain params and requires
        the replayed result to match the recorded state."""
        from oracle_notes import answer_label
        label1, sidecar1 = answer_label(LONG_PROSE)
        label2, sidecar2 = answer_label(LONG_PROSE)
        assert label1 == label2
        assert sidecar1 == sidecar2

    def test_different_prose_yields_different_ids(self):
        from oracle_notes import answer_label
        label1, _ = answer_label(LONG_PROSE)
        label2, _ = answer_label(LONG_PROSE + " Slightly different this time.")
        assert label1 != label2


class TestBankAnswerLongProse:
    """``bank_answer`` on prose past ``_MAX_ANSWER_LABEL``: the vertex label
    is the content-derived id, never the verbatim prose — the mechanism
    that keeps a real long answer from ever hitting the §3.3 occlusion
    wall again (contrast the old ``bank_failed`` safety net, which caught
    the crash after the fact rather than preventing it)."""

    def test_banked_label_is_the_digest_not_verbatim(self):
        from oracle_notes import bank_answer, answer_label
        from quotation_overlay import lift_quotation
        m2, cut_id = bank_answer(_resident_m(), LONG_PROSE, qid="q1",
                                 note_date="2026-07-19")
        lifted = lift_quotation(m2, cut_id)
        labels = [v.label for v in lifted.V if v.label is not None]
        expected_label, _sidecar = answer_label(LONG_PROSE)
        assert labels == [expected_label]
        assert labels != [LONG_PROSE]

    def test_mention_not_use_still_holds(self):
        from oracle_notes import bank_answer
        from agon_evolution import sheet_atom_keys, atom_key
        m2, _ = bank_answer(_resident_m(), LONG_PROSE, qid="q1",
                            note_date="2026-07-19")
        keys = sheet_atom_keys(m2)
        assert atom_key("asserted", ["author", None]) in keys
        assert not any("utterance" in k for k in keys)
        assert atom_key("swan", ["Alba"]) in keys

    def test_structural_round_trip_preserves_the_digested_cell(self):
        from oracle_notes import bank_answer, answer_label
        from quotation_overlay import lift_quotation
        from egi_io import to_dict, from_dict
        from eg_navigation import same_graph
        m2, cut_id = bank_answer(_resident_m(), LONG_PROSE, qid="q1",
                                 note_date="2026-07-19")
        back = from_dict(to_dict(m2))
        assert same_graph(m2, back)
        (cut2,) = back.quotation
        labels = [v.label for v in lift_quotation(back, cut2).V
                  if v.label is not None]
        expected_label, _sidecar = answer_label(LONG_PROSE)
        assert labels == [expected_label]

    def test_two_bankings_of_the_same_answer_are_isomorphic(self):
        """Determinism end to end: banking the SAME long answer twice from
        the same base M produces the same graph up to isomorphism — the
        property the polarity gate's replay actually relies on."""
        from oracle_notes import bank_answer
        from eg_navigation import same_graph
        m2a, _ = bank_answer(_resident_m(), LONG_PROSE, qid="q1",
                             note_date="2026-07-19")
        m2b, _ = bank_answer(_resident_m(), LONG_PROSE, qid="q1",
                             note_date="2026-07-19")
        assert same_graph(m2a, m2b)

    def test_saves_and_attests_without_occlusion(self, tmp_path):
        """The behavior change to prove: a long answer banks successfully
        end to end, including the §3.3-attested save that used to raise
        ``CorrespondenceViolation`` on this exact shape of input."""
        from oracle_notes import bank_answer_step
        from proof_authoring import ProofChain
        from tomos_service import TomosService
        from universe_of_discourse import UoDCategory
        pc = ProofChain(_resident_m())
        pc = bank_answer_step(pc, LONG_PROSE, qid="q1", note_date="2026-07-19")
        chain, uod = pc.to_uod(
            uod_id="test_long_answer_bank", name="long answer bank test",
            description="test", category=UoDCategory.DOMAIN_MODEL)
        TomosService(tmp_path).save_uod_with_chain(uod, chain)  # must not raise
        assert TomosService(tmp_path).load_uod("test_long_answer_bank") is not None


# --------------------------------------------------------------------------- #
# V2a.2 item (2): bank_answer_step — the explicit, replayable act              #
# --------------------------------------------------------------------------- #


class TestBankAnswerStep:
    def test_one_composite_step_with_act_and_derivation(self):
        from oracle_notes import bank_answer_step, BANK_TO_M, ATTRIBUTION_EGIF
        from proof_authoring import ProofChain
        pc = ProofChain(_resident_m())
        pc = bank_answer_step(pc, PROSE, qid="q1", note_date="2026-07-19")
        chain = pc.to_chain()
        (step,) = chain.steps
        p = step.parameters
        assert step.rule_name == BANK_TO_M
        assert p["act"] == "quotation"
        assert p["derivation"] == ["INS", "with_quotation_binding"]
        assert p["provenance"] == "oracle-answer"
        assert p["attributed_to"] == "author"
        assert p["fact_egif"] == ATTRIBUTION_EGIF
        assert p["answer_text"] == PROSE
        assert p["qid"] == "q1" and p["note_date"] == "2026-07-19"
        assert p["earned"] is True

    def test_step_actually_banks(self):
        from oracle_notes import bank_answer_step
        from proof_authoring import ProofChain
        pc = ProofChain(_resident_m())
        pc = bank_answer_step(pc, PROSE, qid="q1", note_date="2026-07-19")
        chain = pc.to_chain()
        after = chain.states[chain.steps[0].to_state_id]
        assert len(after.quotation) == 1

    def test_banked_chain_reads_ampliative(self):
        from oracle_notes import bank_answer_step
        from proof_authoring import ProofChain
        from proof_character import character_of_chain
        pc = ProofChain(_resident_m())
        pc = bank_answer_step(pc, PROSE, qid="q1", note_date="2026-07-19")
        character = character_of_chain(pc.to_chain())
        assert character.character == "ampliative"


# --------------------------------------------------------------------------- #
# V2a.2 item (2), Task 5: bankable_outcomes — the latest-answered-per-qid read #
# --------------------------------------------------------------------------- #


class TestBankableOutcomes:
    def test_latest_answer_per_qid_declines_and_ignores_excluded(self, tmp_path):
        from oracle_notes import OracleLedger, bankable_outcomes
        led = OracleLedger(tmp_path / "oracle")
        led.record_outcome_once("q1", "answered", "first answer", "2026-07-01")
        led.record_outcome("q1", "answered", "revised answer", "2026-07-10")  # drift row
        led.record_outcome_once("q2", "declined", "declined", "2026-07-01")
        led.record_outcome_once("q3", "ignored", "", "2026-07-01")
        led.record_outcome_once("q4", "answered", "kept", "2026-07-05")
        rows, dropped = bankable_outcomes(led)
        by_qid = {r["qid"]: r for r in rows}
        assert set(by_qid) == {"q1", "q4"}                        # no declines, no ignores
        assert by_qid["q1"]["answer_text"] == "revised answer"    # latest per qid
        assert by_qid["q1"]["answered_note_date"] == "2026-07-10"
        assert dropped == 0

    def test_empty_ledger_yields_nothing(self, tmp_path):
        from oracle_notes import OracleLedger, bankable_outcomes
        led = OracleLedger(tmp_path / "oracle")
        assert bankable_outcomes(led) == ([], 0)

    def test_qidless_answered_row_dropped_and_counted(self, tmp_path):
        """NEW-2 (whole-branch review, 2026-07-19): a qid-less "answered"
        row used to vanish from `bankable_outcomes` with no count at all —
        now it is dropped AND counted, so the caller's `bank_malformed`
        digest entry is no longer a claim about dead code."""
        from oracle_notes import OracleLedger, bankable_outcomes
        led = OracleLedger(tmp_path / "oracle")
        led.record_outcome_once("q1", "answered", "kept", "2026-07-05")
        led._append(led._outcomes_path, {
            "status": "answered", "answer_text": "orphaned",
            "answered_note_date": "2026-07-06",
        })  # no "qid" key at all
        rows, dropped = bankable_outcomes(led)
        assert {r["qid"] for r in rows} == {"q1"}
        assert dropped == 1
