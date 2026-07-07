"""Tests for the MCP verifier service (R3, the consolidate/adopt track).

Two layers:

  * The **pure verifier functions** (``mcp_verifier``) are exercised directly and
    always run — they import no MCP SDK, so this is the CI-safe contract that
    holds whether or not the optional ``mcp`` extra is installed.
  * The **server wrapper** (``mcp_server``) is checked for a clean import without
    the extra (the guard fires) and, when ``mcp`` is present, for a real
    in-process tool round-trip. No live model is ever contacted — the server
    exposes Arisbe's mechanical referee; there is no LLM inside it.

Governing property: every function reduces its input to a calculus artifact and
re-checks it, and content errors come back as ``{"ok": False, "error": ...}``
rather than raising.
"""

import pytest

import mcp_verifier as v
import mcp_server


# ---------------------------------------------------------------------------
# check_egif — parse + validate
# ---------------------------------------------------------------------------

def test_check_egif_wellformed():
    r = v.check_egif('~[ (man *x) ~[ (mortal x) ] ]')
    assert r["ok"] is True
    assert r["vertices"] == 1  # one shared line of identity across the two cuts
    assert r["cuts"] == 2
    assert set(r["relations"]) == {"man", "mortal"}
    # The canonical round-trip is present and re-parses to the same structure.
    assert v.check_egif(r["egif_canonical"])["ok"] is True


def test_check_egif_reports_syntax_error_without_raising():
    r = v.check_egif("~[ (man")
    assert r["ok"] is False
    assert "error" in r and r["error"]


def test_check_egif_lists_content_addressed_elements():
    r = v.check_egif('(man *x) (mortal *y)')
    ids = {e["id"] for e in r["elements"]}
    assert "sheet" in ids
    # relations are labelled and carry their name + area
    rels = {e["relation"]: e for e in r["elements"] if "relation" in e}
    assert set(rels) == {"man", "mortal"}
    assert all(e["area"] == "sheet" for e in rels.values())


def test_canonical_ids_are_stable_across_parses():
    egif = '~[ (man *x) ~[ (mortal x) ] ]'
    a = {e["relation"]: e["id"] for e in v.check_egif(egif)["elements"] if "relation" in e}
    b = {e["relation"]: e["id"] for e in v.check_egif(egif)["elements"] if "relation" in e}
    assert a == b  # the label a relation receives is a pure function of structure


# ---------------------------------------------------------------------------
# peel — the three-valued semantic game
# ---------------------------------------------------------------------------

M = '(man "Socrates") (mortal "Socrates")'


def test_peel_true_when_model_confirms():
    r = v.peel('(mortal "Socrates")', M)
    assert r["ok"] and r["verdict"] == "true" and r["holds"] is True


def test_peel_unknown_open_world():
    r = v.peel('(mortal "Plato")', M)
    assert r["ok"] and r["verdict"] == "unknown" and r["holds"] is False


def test_peel_false_closed_world():
    r = v.peel('(mortal "Plato")', M, closed=True)
    assert r["ok"] and r["verdict"] == "false"


def test_peel_named_models_dict():
    r = v.peel('(mortal "Socrates")', {"greeks": M, "empty": '(nothing "z")'})
    assert r["ok"] and r["verdict"] == "true"


def test_peel_witness_on_existential():
    # A generic line that M can satisfy names its witness.
    r = v.peel('(man *x)', M)
    assert r["ok"] and r["verdict"] == "true"
    assert r.get("witness")  # some x=Socrates binding


def test_peel_reports_bad_g_without_raising():
    r = v.peel('~[ (man', M)
    assert r["ok"] is False and "G did not parse" in r["error"]


def test_peel_reports_bad_m_without_raising():
    r = v.peel('(man "Socrates")', '~[ (broken')
    assert r["ok"] is False and "M did not parse" in r["error"]


# ---------------------------------------------------------------------------
# apply_rule / validate_step — sound Dau-rule application
# ---------------------------------------------------------------------------

def test_apply_era_removes_a_relation():
    src = '(man *x) (mortal *y)'
    e0 = next(e["id"] for e in v.check_egif(src)["elements"] if e.get("relation") == "man")
    r = v.apply_rule(src, "ERA", selection=[e0])
    assert r["ok"] is True
    assert "man" not in r["relations"] and "mortal" in r["relations"]


def test_apply_dc_plus_inserts_empty_double_cut():
    r = v.apply_rule('(man *x)', "DC+", target="sheet")
    assert r["ok"] is True
    assert r["cuts"] == 2  # a fresh empty double cut


def test_apply_rule_rejects_unsound_move_with_engine_message():
    # ERA of a positive-context selection whose elements are not co-area, etc. —
    # here an unknown label is rejected before the engine even runs.
    r = v.apply_rule('(man *x)', "ERA", selection=["e9"])
    assert r["ok"] is False and "unknown element label" in r["error"]


def test_apply_rule_reports_engine_rejection():
    # A genuinely unsound selection (two elements not in the same area) is
    # rejected by the engine with its own message.
    src = '(man *x) ~[ (mortal *y) ]'
    els = v.check_egif(src)["elements"]
    man = next(e["id"] for e in els if e.get("relation") == "man")
    mortal = next(e["id"] for e in els if e.get("relation") == "mortal")
    r = v.apply_rule(src, "ERA", selection=[man, mortal])
    assert r["ok"] is False and r["error"]


def test_validate_step_dry_runs_without_result():
    src = '(man *x) (mortal *y)'
    e0 = next(e["id"] for e in v.check_egif(src)["elements"] if e.get("relation") == "man")
    ok = v.validate_step(src, "ERA", selection=[e0])
    assert ok == {"ok": True}  # validity only — no result graph
    bad = v.validate_step(src, "ERA", selection=["nope"])
    assert bad["ok"] is False and "error" in bad


# ---------------------------------------------------------------------------
# attest — §3.3 correspondence between graph and drawing
# ---------------------------------------------------------------------------

def test_attest_passes_on_valid_graph():
    r = v.attest('~[ (man *x) ~[ (mortal x) ] ]')
    assert r["ok"] is True and r["attested"] is True


def test_attest_reports_parse_error():
    r = v.attest('~[ (man')
    assert r["ok"] is False and r["attested"] is False


# ---------------------------------------------------------------------------
# The tool registry is the single source of truth the server wraps.
# ---------------------------------------------------------------------------

def test_tool_registry_covers_the_five_tools():
    assert set(v.TOOLS) == {"check_egif", "peel", "apply_rule", "validate_step", "attest"}
    for name, (fn, desc) in v.TOOLS.items():
        assert callable(fn) and isinstance(desc, str) and desc


# ---------------------------------------------------------------------------
# Server wrapper — guard when the extra is absent; round-trip when present.
# ---------------------------------------------------------------------------

def test_server_imports_regardless_of_extra():
    # The module imports cleanly whether or not `mcp` is installed.
    assert hasattr(mcp_server, "MCP_AVAILABLE")
    assert hasattr(mcp_server, "build_server")


def test_build_server_guarded_when_extra_absent():
    if mcp_server.MCP_AVAILABLE:
        pytest.skip("mcp extra present; guard path not exercised")
    with pytest.raises(RuntimeError, match="mcp"):
        mcp_server.build_server()


@pytest.mark.skipif(not mcp_server.MCP_AVAILABLE, reason="requires the optional 'mcp' extra")
def test_server_registers_all_tools_and_round_trips():
    import asyncio

    srv = mcp_server.build_server()

    async def _run():
        tools = await srv.list_tools()
        assert {t.name for t in tools} == set(v.TOOLS)
        # A real call through the MCP machinery returns the verifier's dict.
        _content, structured = await srv.call_tool(
            "peel", {"egif": '(mortal "Socrates")', "model": M}
        )
        assert structured["result"]["verdict"] == "true"

    asyncio.run(_run())
