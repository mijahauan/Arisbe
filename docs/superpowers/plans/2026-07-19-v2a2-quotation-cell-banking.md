# V2a.2 item (2) — Quotation-Cell Banking of Oracle Answers into M

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An author's answered oracle question enters M as a quoted attributed cell — `(asserted "author" ⌜…⌝)`, provenance `oracle-answer`, banked **unparsed** (mention, not use) — recorded as an explicit, replayable chain act, composed safely with carry and decay, and wired into the vault driver's oracle pass.

**Architecture:** A pure construction function `bank_answer` (enlarge_m INS of the attribution cell + `quote_existing_name` oval holding the verbatim prose as one `utterance` atom) and its chain-step recorder `bank_answer_step` (ONE composite step, the `challenge_step` precedent), both in `src/oracle_notes.py` beside the machinery they serve (the `quote_step`-in-`quotation_overlay` precedent). The polarity gate learns the new act (`"quotation"` ∈ `M_ACTS`, rule `BANK_TO_M` ∈ `M_RULES`) and how to **replay** it (docket ⑤ discipline). The vault driver's `_run_oracle` rebuilds the cumulative author-model from the ledger each oracle pass (the recomputation thesis — the ledger is the durable store, M is a rebuilt view) and saves it as a side-store checkpoint UoD.

**Tech Stack:** Python 3.12 / uv / pytest. No protected-core changes (`egi_core_dau`, rules, `world_scroll` untouched).

## Global Constraints

- **Timing rider (the author, 2026-07-19):** ONLY item (2) of V2a.2 is in scope. Items (1) multi-paragraph answers and (3) NL interpretation are held until the first real answered RUN-13 note. Do not touch `parse_note`'s paragraph heuristic or `score`.
- **Banked unparsed, mention-not-use** (vault spec §V2a ruling 1): the answer prose enters M only inside the quotation oval; no parsing, no assertion of its content. The only asserted ink is `(asserted "author" *q)` — truth about the *act of answering*.
- **Declines/ignores are NEVER banked** (spec ruling 4: "a refusal is never banked back as answer-data"). Ratings are never banked.
- **Custody:** answer prose may live in side-store artifacts (`runs/` UoD JSONs, chain params) — those are gitignored. It must never reach stdout (numbers-only digest discipline) and never a linear form (the structural `to_dict` path only; the linear generators raise `SecondOrderNotInLinearForm` on a quotation-bearing graph, which is the honored limit, not a bug).
- **Decay behavior is the REFUSAL, pinned** (verified on main 2026-07-19): `retract_from_m` atom-form on a banked exhibit raises `AssertionError: … the quotation moves only as a whole unit`; `live_runner._decay` catches it (docket ⑥ skip-and-count). Do NOT extend the ERA to take the oval — a widening erasure raises rather than silently taking more (B-min doctrine).
- **`_linear_form` stays freeze-not-projection** (YAGNI): the vault driver never carries banked cells inside the round loop this build, so the documented docket-freeze consequence is unreachable here. Do not change `_linear_form`.
- Import pattern `from module_name import Foo` (never `from src.…`). EGI immutable — `.with_*` only. Run tests via `uv run pytest`.
- Commit after each task; quality gates run on commit.

## File Structure

- `src/oracle_notes.py` — add `ATTRIBUTION_EGIF`, `_utterance_graph`, `bank_answer`, `BANK_TO_M`, `bank_answer_step`, `bankable_outcomes`.
- `tests/test_oracle_notes.py` — new `TestBankAnswer` + `TestBankAnswerStep` classes.
- `tests/test_live_runner.py` — two composition tests (carry, decay-refusal).
- `tests/test_corpus_polarity_discipline.py` — `M_ACTS`/`M_RULES` additions, `_replay_act` branch, one hand-built banked-chain gate test.
- `tests/test_predict_never_preempt.py` — one test through the real banking channel.
- `tools/run_vault_v0.py` — `_run_oracle` banks answered outcomes → author-model checkpoint UoD.
- `docs/superpowers/specs/2026-07-17-vault-cycle-design.md` — V2a.2(2) build record.
- `CLAUDE.md`, `CURRENT_PLAN.md` — one-line updates.

---

### Task 1: `bank_answer` — the pure construction

**Files:**
- Modify: `src/oracle_notes.py` (new section at the end, before any `__main__`)
- Test: `tests/test_oracle_notes.py`

**Interfaces:**
- Consumes: `world_scroll.enlarge_m(egi, egif)`, `world_scroll.find_world_scroll(egi)`, `quotation_overlay.quote_existing_name(host, name_vid, quoted)`, `egi_core_dau.create_empty_graph/Vertex/Edge`, `egi_io.to_dict/from_dict`.
- Produces: `ATTRIBUTION_EGIF = '(asserted "author" *q)'`; `bank_answer(m, answer_text, *, qid, note_date) -> tuple[graph, str]` returning the new graph and the quotation-cut id. Raises `ValueError` when `m` has no world-scroll (via `enlarge_m`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_oracle_notes.py`:

```python
# --------------------------------------------------------------------------- #
# V2a.2 item (2): quotation-cell banking — the pure construction               #
# --------------------------------------------------------------------------- #

PROSE = 'A multi-line answer.\nWith "quotes", ~[ brackets ], and a backslash \\.'


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
        from graph_isomorphism_engine import same_graph
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
```

Note for the implementer: `same_graph` lives in `graph_isomorphism_engine` — verify the exact import name with `grep -n "def same_graph" src/*.py` (it may be exported via `eg_navigation`); use whichever module the existing tests in this file / `test_world_scroll.py` import it from.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_oracle_notes.py -q -k BankAnswer`
Expected: 5 failures/errors — `ImportError: cannot import name 'bank_answer'`.

- [ ] **Step 3: Implement**

Append to `src/oracle_notes.py`:

```python
# --------------------------------------------------------------------------- #
# V2a.2 item (2): quotation-cell banking (docs/superpowers/specs/              #
# 2026-07-17-vault-cycle-design.md, "V2a.2 — AUTHORIZED", item 2).            #
# An answer enters M as ``(asserted "author" <q>)`` with <q> a proposition-    #
# sorted name whose quotation oval holds the VERBATIM prose as one            #
# ``(utterance "<prose>")`` atom — banked unparsed, mention not use. The      #
# only asserted ink is the attribution: truth about the act of answering,     #
# never about its content (spec §"person-model", Examination IV Suspect 4).   #
# --------------------------------------------------------------------------- #

ATTRIBUTION_EGIF = '(asserted "author" *q)'


def _utterance_graph(prose: str):
    """The quoted ink: one constant vertex carrying ``prose`` verbatim, named
    by one ``utterance`` atom. Built structurally — the prose never meets a
    linear parser/generator, so newlines/quotes/brackets survive untouched."""
    from uuid import uuid4
    from egi_core_dau import create_empty_graph, Vertex, Edge
    g = create_empty_graph()
    vid, eid = f"v_bank_{uuid4().hex[:8]}", f"e_bank_{uuid4().hex[:8]}"
    g = g.with_vertex_in_context(
        Vertex(id=vid, label=prose, is_generic=False), g.sheet)
    g = g.with_edge(Edge(id=eid), (vid,), "utterance", g.sheet)
    return g


def bank_answer(m, answer_text: str, *, qid: str, note_date: str):
    """Bank one answered oracle question into the resident M: one licensed
    INS-of-cell of ``ATTRIBUTION_EGIF`` (``enlarge_m``), then the fresh
    generic name gains its quotation oval holding the verbatim prose
    (``quote_existing_name`` — same-area attachment, inside the new cell).
    Returns ``(new_graph, quotation_cut_id)``. Raises ``ValueError`` when
    ``m`` carries no world-scroll (``enlarge_m``'s own refusal). ``qid`` and
    ``note_date`` are accepted here for signature stability with the step
    recorder and the gate's replayer, which re-executes from these params."""
    from world_scroll import enlarge_m, find_world_scroll
    from quotation_overlay import quote_existing_name
    scroll = find_world_scroll(m)
    before_cells = set(scroll.cell_ids) if scroll else set()
    m2 = enlarge_m(m, ATTRIBUTION_EGIF)
    scroll2 = find_world_scroll(m2)
    (new_cell,) = set(scroll2.cell_ids) - before_cells
    eid = next(e.id for e in m2.E
               if m2.get_context(e.id) == new_cell
               and m2.rel[e.id] == "asserted")
    q_vid = m2.nu[eid][1]
    m3, cut_id = quote_existing_name(m2, q_vid, _utterance_graph(answer_text))
    return m3, cut_id
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_oracle_notes.py -q -k BankAnswer`
Expected: 5 passed. If `test_mention_not_use` fails on the `atom_key` shape, print `sorted(sheet_atom_keys(m2))` and match the real key shape (verified on main: the asserted atom's key is `'["asserted",["author",null]]'`, i.e. labels `["author", None]`).

- [ ] **Step 5: Commit**

```bash
git add src/oracle_notes.py tests/test_oracle_notes.py
git commit -m "V2a.2(2) Task 1: bank_answer — the quoted attributed cell, banked unparsed"
```

---

### Task 2: `bank_answer_step` — the explicit, replayable act

**Files:**
- Modify: `src/oracle_notes.py`
- Test: `tests/test_oracle_notes.py`

**Interfaces:**
- Consumes: `bank_answer` (Task 1), `proof_authoring.ProofChain.apply_derived(rule_name, transform, *, note=None, params=None, branch=None)`.
- Produces: `BANK_TO_M = "BANK_TO_M"`; `bank_answer_step(pc, answer_text, *, qid, note_date, note=None) -> ProofChain` recording ONE composite step (the `challenge_step` precedent) with params: `act="quotation"`, `earned=True`, `derivation=["INS", "with_quotation_binding"]`, `provenance="oracle-answer"`, `attributed_to="author"`, `fact_egif=ATTRIBUTION_EGIF`, `answer_text`, `qid`, `note_date`. Later tasks (gate replay, driver) rely on exactly these param keys.

- [ ] **Step 1: Check `proof_character`'s rule registration**

Run: `grep -n "QUOTE\|NEUTRAL\|AMPLIATIVE\|ampliative" src/proof_character.py | head -20` (find the registry the CLAUDE.md line "PEEL neutral + ADMIT_TO_M/RETRACT_FROM_M/DECAY ampliative + …" refers to; `quotation_overlay` registers `QUOTE` there as neutral — find how).
Register `BANK_TO_M` as **ampliative** in the same way (the attribution atom is new content entering by INS; the quoted body is neutral mention — the step's dominant character is the insertion). If registration is a dict in `proof_character.py`, add the entry there; if modules self-register, do it at the bottom of the new `oracle_notes` section.

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_oracle_notes.py`:

```python
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
```

(`ProofChain.to_chain()` returns a `TransformationChain` with `.steps` and `.states` — verified against `src/proof_authoring.py:314` and `tests/test_m_steps.py`'s idiom.)

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_oracle_notes.py -q -k BankAnswerStep`
Expected: ImportError on `bank_answer_step`.

- [ ] **Step 4: Implement**

Append to `src/oracle_notes.py`:

```python
BANK_TO_M = "BANK_TO_M"


def bank_answer_step(pc, answer_text: str, *, qid: str, note_date: str,
                     note: str = None):
    """Record banking as ONE composite chain step (the ``challenge_step``
    precedent: one act, the executed derivation list). Act ``"quotation"`` —
    the polarity gate's ``M_ACTS`` names it and its replayer re-executes
    ``bank_answer`` from these params (docket ⑤: the record is earned,
    permanently)."""
    params = {
        "act": "quotation",
        "earned": True,
        "derivation": ["INS", "with_quotation_binding"],
        "provenance": "oracle-answer",
        "attributed_to": "author",
        "fact_egif": ATTRIBUTION_EGIF,
        "answer_text": answer_text,
        "qid": qid,
        "note_date": note_date,
    }
    return pc.apply_derived(
        BANK_TO_M,
        lambda g: bank_answer(g, answer_text, qid=qid, note_date=note_date)[0],
        note=note or f"bank oracle answer {qid} ({note_date})",
        params=params)
```

- [ ] **Step 5: Run tests, then commit**

Run: `uv run pytest tests/test_oracle_notes.py -q`
Expected: all pass (existing 18+ plus the new 7).

```bash
git add src/oracle_notes.py tests/test_oracle_notes.py src/proof_character.py
git commit -m "V2a.2(2) Task 2: bank_answer_step — one composite BANK_TO_M act, ampliative"
```

---

### Task 3: Composition with the live runner — carry and decay (Examination IV tests (a) and (b))

**Files:**
- Test: `tests/test_live_runner.py` (tests only — expected to pass against existing code; they PIN behavior)

**Interfaces:**
- Consumes: `bank_answer` (Task 1), `LiveRunner`, `LiveRunConfig`, `ReplaySource`, `DiscourseFeed`, `egi_io.to_dict/from_dict` — mirror the setup of the existing `test_carry_preserves_resident_M_structurally` (same file, ~line 448) exactly.
- Produces: nothing downstream; these are the standing composition pins.

- [ ] **Step 1: Write the two tests** (they should pass immediately — that is the point: pin it)

Append to `tests/test_live_runner.py`, mirroring the existing structural-carry test's constructor arguments verbatim (copy its `LiveRunConfig`/feed wiring; only the seed differs):

```python
def _banked_resident_m():
    from egif_parser_dau import parse_egif
    from world_scroll import wrap_state
    from oracle_notes import bank_answer
    m, _ = wrap_state(parse_egif('(swan "Alba")'))
    m2, _cut = bank_answer(
        m, 'The author\'s answer.\nSecond "line".',
        qid="q1", note_date="2026-07-19")
    return m2


def test_carry_preserves_a_banked_quotation_cell_across_segments():
    """Examination IV composition test (a): the structural segment carry
    (docket ④) keeps a banked ``(asserted "author" ⌜…⌝)`` cell intact —
    the EGIF text carry could not (SecondOrderNotInLinearForm)."""
    from egi_io import to_dict, from_dict
    m2 = _banked_resident_m()
    r = LiveRunner(to_dict(m2), ReplaySource(_fact_batches(2)), DiscourseFeed,
                   _cfg())          # copy the wiring of the existing carry test
    res = r.run()
    final = from_dict(res.final_model_json)
    assert len(final.quotation) == 1
    from quotation_overlay import lift_quotation
    (cut_id,) = final.quotation
    labels = [v.label for v in lift_quotation(final, cut_id).V
              if v.label is not None]
    assert labels == ['The author\'s answer.\nSecond "line".']


def test_decay_over_a_banked_cell_is_refused_skipped_and_counted():
    """Examination IV composition test (b): a stale banked attribution atom is
    NOT silently erased (the ERA would have to widen onto the oval — the
    whole-unit guard refuses) and does NOT crash the loop (docket ⑥ catches
    the refusal): skipped, counted, exempted; the quotation stands."""
    from egi_io import to_dict, from_dict
    m2 = _banked_resident_m()
    # ttl=1 and batches that never re-deliver the asserted atom → it goes stale
    r = LiveRunner(to_dict(m2), ReplaySource(_fact_batches(3)), DiscourseFeed,
                   _cfg(ttl=1))     # match the existing decay test's config idiom
    res = r.run()
    final = from_dict(res.final_model_json)
    assert len(final.quotation) == 1                      # never corrupted
    assert sum(d.decay_skipped for d in res.segments) >= 1
    # the ordinary atom (swan Alba) is still subject to normal decay — it is
    # NOT swept into the exemption (assert it decayed OR was re-delivered,
    # matching whatever _fact_batches delivers; see the existing ttl test)
```

Implementer note: `_fact_batches`, `_cfg` are placeholders for this file's actual fixture helpers — open the existing `test_carry_preserves_resident_M_structurally_across_two_segments` and the ttl/decay test (headline "disuse-decay bounds |M|"), and reuse their exact source/feed/config construction. Keep the assertions above as written; adapt only the wiring. Verify `SegmentDigest` has `decay_skipped` (it does — docket ⑥) with `grep -n "decay_skipped" src/live_runner.py`.

- [ ] **Step 2: Run**

Run: `uv run pytest tests/test_live_runner.py -q`
Expected: all pass including the two new. If the decay test's refusal never fires, force staleness the way the existing ttl test does (check `ttl_unit` — rounds vs polls) until `decay_skipped >= 1`; the refusal itself was verified by hand on main 2026-07-19 (`AssertionError: … the quotation moves only as a whole unit`).

- [ ] **Step 3: Commit**

```bash
git add tests/test_live_runner.py
git commit -m "V2a.2(2) Task 3: composition pins — banked cell survives structural carry; decay refusal skip-and-counts"
```

---

### Task 4: Gate (c) — the polarity gate learns the banking act

**Files:**
- Modify: `tests/test_corpus_polarity_discipline.py` (`M_ACTS` ~line 123, `M_RULES` ~line 125, `_replay_act`, plus one new test)

**Interfaces:**
- Consumes: `bank_answer`, `bank_answer_step`, `BANK_TO_M` (Tasks 1–2), the file's existing `_replay_derivations` / `_graphs_match` / tripwire helpers.
- Produces: the standing gate now admits and REPLAYS the banking act.

- [ ] **Step 1: Extend the allowlists**

```python
M_ACTS = ("m_enlargement", "m_retraction", "m_revision", "world_withdrawal",
          "m_discharge", "episode_entertained", "episode_abandoned", "m_refold",
          "quotation")
M_RULES = ("REVISE_M", "REVISE_M(sibling)", "ADMIT_TO_M", "RETRACT_FROM_M",
           "DECAY", "ENTERTAIN", "DISCHARGE_TO_M", "ABANDON_EPISODE",
           "BANK_TO_M")
```

- [ ] **Step 2: Extend `_replay_act`** — add before the final `return None`:

```python
    if act == "quotation" and p.get("provenance") == "oracle-answer":
        from oracle_notes import bank_answer
        return bank_answer(before, p["answer_text"],
                           qid=p.get("qid", ""),
                           note_date=p.get("note_date", ""))[0]
```

(A `"quotation"` act WITHOUT the oracle-answer provenance — `quote_step`/`sort_step` mentions — stays unreplayed/skipped, exactly as today.)

- [ ] **Step 3: Write the new gate test** (append near the tripwire tests):

```python
def test_banked_chain_passes_the_gate_and_replays():
    """Gate (c) of Examination IV's V2a.2 blockers: a chain that banks an
    oracle answer (act ``quotation``, rule ``BANK_TO_M``) satisfies the
    explicit-step check, the m_view tripwire (the act is acknowledged), and
    docket ⑤'s derivation replay (re-executing bank_answer from the recorded
    params reproduces to_state up to isomorphism)."""
    from egif_parser_dau import parse_egif
    from world_scroll import wrap_state
    from oracle_notes import bank_answer_step
    from proof_authoring import ProofChain
    m, _ = wrap_state(parse_egif('(swan "Alba")'))
    pc = ProofChain(m)
    pc = bank_answer_step(pc, 'An answer with a newline.\nAnd "quotes".',
                          qid="q9", note_date="2026-07-19")
    chain = pc.to_chain()
    (step,) = chain.steps
    assert step.parameters["act"] in M_ACTS
    assert step.rule_name in M_RULES
    replayed, skipped, mismatches, by_act = _replay_derivations(chain)
    assert mismatches == []
    assert by_act["quotation"] == 1
```

Implementer note: `_replay_derivations(chain)` reads `chain.states` / `chain.steps` — match how the corpus tests hydrate a chain (if the helper expects the on-disk `TransformationChain` shape, build the same object the corpus loader produces; see how the file's existing hand-built falsifier `test_the_tripwire_bites_on_a_silent_m_change` constructs its chain and mirror that).

- [ ] **Step 4: Run the whole gate + the quotation conservativity gate**

Run: `uv run pytest tests/test_corpus_polarity_discipline.py tests/test_second_order_conservativity.py tests/test_m_steps.py tests/test_world_scroll.py -q`
Expected: all pass — the corpus UoDs are untouched, so the parametrized checks see nothing new; the A3 gate is unaffected (banking is side-store, not corpus).

- [ ] **Step 5: Commit**

```bash
git add tests/test_corpus_polarity_discipline.py
git commit -m "V2a.2(2) Task 4: gate (c) — quotation act in M_ACTS, BANK_TO_M in M_RULES, replayable"
```

---

### Task 5: Driver wiring — the author-model checkpoint

**Files:**
- Modify: `src/oracle_notes.py` (one small helper), `tools/run_vault_v0.py` (`_run_oracle`)
- Test: `tests/test_oracle_notes.py` (e2e through the real driver, the V2a.1 precedent)

**Interfaces:**
- Consumes: `OracleLedger.outcomes()` (list of dicts with `qid`/`status`/`answer_text`/`note_date` — verify field names with `grep -n "def outcomes\|answer_text" src/oracle_notes.py`), `bank_answer_step`, `ProofChain`, `TomosService(runs_dir).save_uod_with_chain(uod, chain)`, `res.uod.current_egi` (the final segment's M, already resident).
- Produces: `bankable_outcomes(ledger) -> list[dict]` (latest answered row per qid, declines/ignores excluded); `_run_oracle`'s return dict gains `"banked": <int>`; a side-store UoD `vault_v0_author_model` whose chain is one `BANK_TO_M` step per banked answer.

- [ ] **Step 1: Write the failing unit test for `bankable_outcomes`**

```python
class TestBankableOutcomes:
    def test_latest_answer_per_qid_declines_excluded(self, tmp_path):
        from oracle_notes import OracleLedger, bankable_outcomes
        led = OracleLedger(tmp_path / "oracle")
        led.record_outcome_once("q1", "answered", "first answer", "2026-07-01")
        led.record_outcome("q1", "answered", "revised answer", "2026-07-10")  # drift row
        led.record_outcome_once("q2", "declined", "declined", "2026-07-01")
        led.record_outcome_once("q3", "ignored", "", "2026-07-01")
        led.record_outcome_once("q4", "answered", "kept", "2026-07-05")
        rows = bankable_outcomes(led)
        by_qid = {r["qid"]: r for r in rows}
        assert set(by_qid) == {"q1", "q4"}              # no declines, no ignores
        assert by_qid["q1"]["answer_text"] == "revised answer"   # latest per qid
```

(Verify the outcome-row field names against `record_outcome`'s implementation and adjust `answer_text`/`note_date` keys to the real ones.)

- [ ] **Step 2: Implement `bankable_outcomes`** in `src/oracle_notes.py`:

```python
def bankable_outcomes(ledger: "OracleLedger"):
    """The rows the author-model checkpoint banks: the LATEST ``answered``
    outcome per qid (drift rows supersede — the current answer is the
    author-model's content; the earlier rows remain ledger history).
    Declines and ignores are never banked (spec ruling 4: a refusal is never
    banked back as answer-data)."""
    latest = {}
    for row in ledger.outcomes():
        if row.get("status") == "answered":
            latest[row["qid"]] = row       # file order — later rows win
    return list(latest.values())
```

Run the unit test; expected pass.

- [ ] **Step 3: Wire `_run_oracle`**

In `tools/run_vault_v0.py`, at the END of `_run_oracle` (after `reveals` and the note-writing block, before the return), add — and extend the returned dict with `"banked"`:

```python
    # V2a.2 item (2): rebuild the cumulative author-model from the ledger
    # (the recomputation thesis — the ledger is the durable store; M is a
    # rebuilt view) and save it as a side-store checkpoint. Each banked
    # answer is one explicit BANK_TO_M step, gate-replayable. Numbers-only
    # stdout: the count, never a qid or answer text.
    banked = 0
    rows = bankable_outcomes(ledger)
    if rows:
        from proof_authoring import ProofChain
        from oracle_notes import bank_answer_step
        pc = ProofChain(res.uod.current_egi)
        for row in rows:
            pc = bank_answer_step(pc, row["answer_text"],
                                  qid=row["qid"],
                                  note_date=row.get("note_date", note_date))
            banked += 1
        chain, uod = pc.to_uod(
            uod_id="vault_v0_author_model",
            name="Vault author-model (V2a.2 banked answers)",
            description="The cumulative author-model: every answered oracle "
                        "question banked as a quoted attributed cell, rebuilt "
                        "from the ledger each oracle pass (recomputation "
                        "thesis). One BANK_TO_M step per answer.")
        TomosService(runs_dir).save_uod_with_chain(uod, chain)
```

(`ProofChain.to_uod(uod_id=, name=, description=, category=…)` returns `(chain, uod)` — `src/proof_authoring.py:322`; check the `UoDCategory` default suits and pass a better category if one fits — grep the enum.) Note: `res.uod.current_egi` is already resident (the loop opens residence) — assert `find_world_scroll` is not None before banking and skip-with-count (`digest key "bank_skipped"`) if somehow absent, never crash the oracle pass.

- [ ] **Step 4: E2E test through the real driver** (the V2a.1 e2e precedent — find the existing e2e test in `tests/test_oracle_notes.py` that invokes the driver's `main`/`_run_oracle` against the fixture twice, and extend a copy):

```python
    def test_e2e_banks_answered_note_into_author_model(self, tmp_path):
        """Drive the fixture twice: run 1 writes a questions note; the test
        answers one question by editing the note; run 2 reads it back AND
        banks it — the author-model UoD exists in the side-store, carries
        exactly one quotation cell, its chain's one step is gate-shaped, and
        stdout carried numbers only."""
        # copy the existing e2e's two-run scaffold (fixture root, runs_dir,
        # note_date args, the **A:** edit between runs) verbatim, then:
        from tomos_service import TomosService
        svc = TomosService(runs_dir)
        uod = svc.load_uod("vault_v0_author_model")
        assert len(uod.current_egi.quotation) == 1
        chain = svc.load_chain("vault_v0_author_model")
        (step,) = [s for s in chain.steps
                   if s.parameters.get("act") == "quotation"]
        assert step.parameters["provenance"] == "oracle-answer"
        # digest surfaced the count
        assert digest["oracle"]["banked"] == 1
```

(Adapt names to the real e2e scaffold; the assertions are the contract. Also assert the driver's captured stdout contains no answer text — the custody check, mirroring the existing digest-only test.)

- [ ] **Step 5: Run the file, then commit**

Run: `uv run pytest tests/test_oracle_notes.py tests/test_vault_world.py -q`
Expected: all pass.

```bash
git add src/oracle_notes.py tools/run_vault_v0.py tests/test_oracle_notes.py
git commit -m "V2a.2(2) Task 5: oracle pass rebuilds + saves the author-model checkpoint (recomputation thesis)"
```

---

### Task 6: The predict-never-preempt gate bites on the real channel

**Files:**
- Modify: `tests/test_predict_never_preempt.py`

**Interfaces:**
- Consumes: `bank_answer` (Task 1), the file's existing `_dispose` helper and proposal fixtures.

- [ ] **Step 1: Add the test**

```python
def test_disposition_invariant_to_a_REALLY_banked_cell():
    """The gate's fixture quoted a hand-built cell; V2a.2 opens the real
    channel — assert the invariance on bank_answer's actual output: a model
    with a banked oracle answer disposes every proposal exactly as the same
    model without it."""
    from egif_parser_dau import parse_egif
    from world_scroll import wrap_state
    from oracle_notes import bank_answer
    plain, _ = wrap_state(parse_egif('(swan "Alba")'))
    banked, _cut = bank_answer(plain, "I think all swans are white.",
                               qid="q1", note_date="2026-07-19")
    for proposal in ('(swan "Alba")', '(white "Alba")',
                     '~[ (swan "Alba") ~[ (white "Alba") ] ]'):
        assert _dispose(plain, proposal) == _dispose(banked, proposal)
```

Implementer note: `_dispose`'s real signature/name is in this file (~line 41's `_pair` region) — match it; if it takes EGIF-vs-parsed or extra args, adapt the call, not the assertion. Note the banked model carries the extra first-order atom `(asserted "author" *q)` — if `_dispose`'s verdict is sensitive to that atom for some proposal, compare against a `plain` that also carries the attribution WITHOUT the oval (build via `enlarge_m(plain, ATTRIBUTION_EGIF)`), which isolates exactly the quotation's contribution — that is the sharper form of the invariance; prefer it.

- [ ] **Step 2: Run + commit**

Run: `uv run pytest tests/test_predict_never_preempt.py -q`
Expected: all pass.

```bash
git add tests/test_predict_never_preempt.py
git commit -m "V2a.2(2) Task 6: predict-never-preempt asserted over the real banking channel"
```

---

### Task 7: Docs + full suite

**Files:**
- Modify: `docs/superpowers/specs/2026-07-17-vault-cycle-design.md` (V2a.2 block, ~line 414), `CLAUDE.md` (the `oracle_notes.py` bullet), `CURRENT_PLAN.md` (the V2a.2 line in NEXT SESSION)

- [ ] **Step 1: Spec build record** — after the V2a.2 authorization block, add a dated "V2a.2 item (2) build record" paragraph: what was built (bank_answer / bank_answer_step / bankable_outcomes / gate (c) / driver wiring / the composition pins), the pinned decay-refusal behavior with the verified error text, the recomputation-thesis persistence decision (ledger durable, author-model checkpoint rebuilt each oracle pass), and the explicitly-deferred remainder (items (1) and (3) under the timing rider; drift-history banking — only the latest answer per qid is banked; `_linear_form` freeze unchanged because banked cells never enter the round loop this build).
- [ ] **Step 2: CLAUDE.md** — extend the `oracle_notes.py` bullet with one sentence: banking (V2a.2 item 2) — `bank_answer`/`bank_answer_step` (act `quotation`, rule `BANK_TO_M`, gate-replayable), the author-model checkpoint `vault_v0_author_model` rebuilt from the ledger each oracle pass; decay refuses banked exhibits whole-unit (skip-and-count).
- [ ] **Step 3: CURRENT_PLAN** — update item -9's V2a.2 line: item (2) built (with commit range), items (1)/(3) still held on the timing rider.
- [ ] **Step 4: Full suite**

Run: `uv run pytest tests/ -q`
Expected: 0 failed (baseline 2026-07-18: 3712 passed / 137 skipped / 1 xfailed — plus this build's ~12 new tests).

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-07-17-vault-cycle-design.md CLAUDE.md CURRENT_PLAN.md
git commit -m "V2a.2(2) Task 7: build record; items (1)/(3) held on the timing rider"
```
