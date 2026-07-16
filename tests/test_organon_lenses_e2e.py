"""End-to-end browser test of Organon's adaptive-scope **lenses**.

Organon is the read-only instrument; the Lens selector swaps a *navigation
projection* into the canvas without touching the asserted drawing. This drives the
real page in a headless Chromium and asserts the lens contract:

* **Drawing** (default) is the §3.3-attested SVG; switching away and back restores it.
* **Well** mounts the 2.5-D negation-well (a three.js ``<canvas>``).
* **Storyboard** is offered only for a UoD with a recorded chain, and renders one
  styled frame per state; it is hidden for a synchronic UoD.
* Switching back to Drawing on a chained UoD restores the chain player.
* No console / page errors throughout.

Requires Playwright + Chromium (``uv run playwright install chromium``); skipped
cleanly if absent. Spawns the app on its own port so it is self-contained.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright  # noqa: E402

REPO = Path(__file__).parent.parent
SYNCHRONIC = "skos_core"            # no recorded chain (structurally-wrapped
                                    # residence, 2026-07-15 — porphyry_tree now
                                    # carries a real DC+·INS residence chain)
CHAINED = "theorem_praeclarum"      # a worked 7-step proof (linear)
BRANCHING = "branching_confluence"  # a fork-and-merge episode (a DAG)
MODAL = "possible_and_necessary"    # a branching weather episode — □cold, ◇cloudy/◇calm
DIALOGUE = "dialogue_model_revision"  # M revised through dialog — verdict FALSE→TRUE→FALSE→TRUE


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def app_url():
    port = _free_port()
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "web_api.main:app",
         "--port", str(port), "--log-level", "warning"],
        cwd=str(REPO), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 40
        while time.time() < deadline:
            try:
                import urllib.request
                if urllib.request.urlopen(url + "/organon/uods", timeout=2).status == 200:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("app did not start")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


@pytest.fixture
def page(app_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = browser.new_page(viewport={"width": 1300, "height": 840})
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append("PAGEERROR: " + str(e)))
        pg._lens_errors = errors
        yield pg
        browser.close()


def _open_organon(page, app_url):
    page.goto(app_url + "/organon")
    page.wait_for_selector(".uod-item", timeout=15000)


def _load_uod(page, uod_id):
    page.eval_on_selector_all(
        ".uod-item",
        "(els, id) => { const t = els.find(e => e.dataset.uodId === id); if (t) t.click(); }",
        uod_id,
    )
    time.sleep(2.0)  # load detail + render + loadChain


def _wait_lens_offered(page, value):
    """Wait until loadChain finishes and un-hides a diachronic lens option —
    a fixed sleep is not enough on a slow (CI) runner."""
    page.wait_for_function(
        "v => { const o = document.querySelector(`#view-lens option[value='${v}']`);"
        " return o && !o.hidden; }",
        arg=value, timeout=15000,
    )


def test_well_lens_mounts_and_drawing_restores(page, app_url):
    """Well mounts a three.js canvas; switching back to Drawing restores the SVG."""
    _open_organon(page, app_url)
    _load_uod(page, SYNCHRONIC)
    # synchronic UoD: the diachronic lens option is hidden
    assert page.eval_on_selector("#view-lens option[value=storyboard]", "o => o.hidden") is True

    page.select_option("#view-lens", "well")
    page.wait_for_selector("#organon-canvas canvas", timeout=15000)  # WebGL canvas mounted

    page.select_option("#view-lens", "drawing")
    page.wait_for_selector("#organon-canvas svg", timeout=10000)     # attested SVG restored
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_storyboard_lens_for_a_chained_uod(page, app_url):
    """A chained UoD offers the Storyboard lens and renders one frame per state;
    switching back to Drawing restores the chain player."""
    _open_organon(page, app_url)
    _load_uod(page, CHAINED)
    _wait_lens_offered(page, "storyboard")

    page.select_option("#view-lens", "storyboard")
    page.wait_for_selector(".sb-frame", timeout=10000)
    frames = page.eval_on_selector_all(".sb-frame", "els => els.length")
    assert frames >= 3, f"expected several storyboard frames, got {frames}"
    # the rule + diff annotations between frames are present
    assert page.eval_on_selector_all(".sb-arrow", "els => els.length") == frames - 1

    page.select_option("#view-lens", "drawing")
    time.sleep(1.0)
    assert page.eval_on_selector("#chain-player", "el => el.style.display") == "flex"
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_liveness_facet_and_retire_toggle(page, app_url):
    """Opening a UoD records a consultation (it reads *alive*); the Retire toggle
    flips it to *retired* and back — forward-facing provenance, manifest floor #7."""
    _open_organon(page, app_url)
    _load_uod(page, SYNCHRONIC)
    page.wait_for_selector(".live-block", timeout=10000)
    # a just-opened UoD is alive (viewing revives even a previously-retired one)
    assert page.eval_on_selector(".live-block .live-status", "el => el.textContent") == "alive"

    # Retire → the facet flips and the button offers Revive
    page.click("#live-toggle")
    page.wait_for_function(
        "document.querySelector('.live-block .live-status') && "
        "document.querySelector('.live-block .live-status').textContent === 'retired'",
        timeout=8000)
    assert page.eval_on_selector("#live-toggle", "el => el.textContent") == "Revive"

    # Revive → back to alive
    page.click("#live-toggle")
    page.wait_for_function(
        "document.querySelector('.live-block .live-status') && "
        "document.querySelector('.live-block .live-status').textContent === 'alive'",
        timeout=8000)
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_derivation_dag_lens_for_a_branching_episode(page, app_url):
    """A branching episode offers the Derivation-DAG lens and hides the *linear*
    lenses (storyboard / time-stack); the DAG draws a node per state."""
    _open_organon(page, app_url)
    _load_uod(page, BRANCHING)
    # the DAG lens is offered; the linear lenses are not (this chain forks)
    _wait_lens_offered(page, "derivation-dag")
    assert page.eval_on_selector("#view-lens option[value=storyboard]", "o => o.hidden") is True

    page.select_option("#view-lens", "derivation-dag")
    page.wait_for_selector(".dd-node", timeout=10000)
    nodes = page.eval_on_selector_all(".dd-node", "els => els.length")
    assert nodes == 4, f"expected the 4-state diamond, got {nodes}"
    # the fork + merge are drawn as edges with rule pills
    assert page.eval_on_selector_all(".dd-rule", "els => els.length") == 4

    page.select_option("#view-lens", "drawing")
    page.wait_for_selector("#organon-canvas svg", timeout=10000)
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_time_stack_lens_for_a_chained_uod(page, app_url):
    """A chained UoD offers the Time-stack lens (the 2.5-D derivation film); it
    mounts a three.js canvas, and switching back to Drawing restores the player."""
    _open_organon(page, app_url)
    _load_uod(page, CHAINED)
    # offered only for a chained UoD; hidden for the synchronic majority
    _wait_lens_offered(page, "time-stack")

    page.select_option("#view-lens", "time-stack")
    page.wait_for_selector("#organon-canvas canvas", timeout=15000)   # WebGL canvas mounted
    # the lens overlay (Look-along reset + legend) is present
    assert page.eval_on_selector_all("#organon-canvas button", "els => els.length") >= 1

    page.select_option("#view-lens", "drawing")
    time.sleep(1.0)
    assert page.eval_on_selector("#chain-player", "el => el.style.display") == "flex"
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_correspondence_chord_on_linear_form(page, app_url):
    """The shared LinearFormPanel carries the picture↔proposition correspondence
    chord — naming §3.3 in words, with the 'not truth' non-claim."""
    _open_organon(page, app_url)
    _load_uod(page, SYNCHRONIC)
    # The chord lives in the panel body (a collapsed <details>), so assert it is
    # attached rather than visible.
    page.wait_for_selector("#organon-canvas .lf-panel .lf-chord", state="attached", timeout=10000)
    text = page.eval_on_selector("#organon-canvas .lf-panel .lf-chord", "el => el.textContent")
    assert "picture" in text and "proposition" in text
    assert "not truth" in text
    tip = page.eval_on_selector("#organon-canvas .lf-panel .lf-chord", "el => el.title")
    assert "SAME graph" in tip and "true" in tip
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_english_reading_gloss_with_register_toggle(page, app_url):
    """The LinearFormPanel carries a natural-language reading beside the notations —
    a gloss (not a fifth form), toggleable between the plain (idiomatic) and literal
    registers."""
    _open_organon(page, app_url)
    _load_uod(page, SYNCHRONIC)
    page.wait_for_selector("#organon-canvas .lf-panel .lf-reading-text", state="attached", timeout=10000)
    # The plain register shows by default; a wrong-vs-right reading is non-empty prose.
    plain = page.eval_on_selector("#organon-canvas .lf-panel .lf-reading-text", "el => el.textContent")
    assert plain and plain.strip(), "no idiomatic reading rendered"
    # It is framed as a reading, not a form (the header tooltip says so).
    tip = page.eval_on_selector("#organon-canvas .lf-panel .lf-reading-head", "el => el.title")
    assert "does NOT round-trip" in tip and "gloss" in tip.lower()
    # Toggling to the literal register changes the text to the structural reading.
    page.eval_on_selector("#organon-canvas .lf-panel .lf-reg button[data-reg=literal]", "el => el.click()")
    literal = page.eval_on_selector("#organon-canvas .lf-panel .lf-reading-text", "el => el.textContent")
    assert literal and "The sheet asserts" in literal
    assert literal != plain
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_propose_in_agon_carries_the_graph_as_proposal_g(page, app_url):
    """The corpus is a source of *proposals*, not only of models. 'Propose in Agon'
    carries the open graph into the arena as the proposal G (prefilling #setup-proposal,
    leaving M empty); 'as model M' carries it as the reference model M instead."""
    _open_organon(page, app_url)
    _load_uod(page, SYNCHRONIC)

    # Primary path: propose the graph as G.
    page.click("#act-agon")
    page.wait_for_selector("#setup-proposal", timeout=15000)
    assert "/agon" in page.url and "proposal_egif=" in page.url
    proposal = page.eval_on_selector("#setup-proposal", "el => el.value")
    model = page.eval_on_selector("#setup-model", "el => el.value")
    assert proposal.strip(), "the proposal G field should be prefilled from Organon"
    assert not model.strip(), "the model M field should be left empty"

    # Secondary path: the same graph used as the reference model M.
    page.goto(app_url + "/organon")
    page.wait_for_selector(".uod-item", timeout=15000)
    _load_uod(page, SYNCHRONIC)
    page.click("#act-agon-model")
    page.wait_for_selector("#setup-model", timeout=15000)
    assert "/agon" in page.url and "model_egif=" in page.url
    assert page.eval_on_selector("#setup-model", "el => el.value").strip(), \
        "the model M field should be prefilled when carried 'as model M'"


def test_style_reprojection_note_appears_on_restyle(page, app_url):
    """Choosing a non-default style reveals the 'style-only reprojection · standing
    unchanged' note — making legible that a restyle preserves standing (§3.3
    attests correspondence, not truth)."""
    _open_organon(page, app_url)
    _load_uod(page, SYNCHRONIC)
    # Hidden at the default (Dau / ELK) projection.
    assert page.eval_on_selector("#reprojection-note", "el => el.style.display") == "none"
    page.select_option("#view-style", "peirce-authentic@1.0")
    time.sleep(1.5)  # re-fetch + re-render in the chosen style
    assert page.eval_on_selector("#reprojection-note", "el => el.style.display") != "none"
    note = page.eval_on_selector("#reprojection-note", "el => el.textContent")
    assert "reprojection" in note and "standing unchanged" in note
    # Back to default hides it again.
    page.select_option("#view-style", "")
    time.sleep(1.5)
    assert page.eval_on_selector("#reprojection-note", "el => el.style.display") == "none"
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_modal_lens_reads_diamond_and_necessity(page, app_url):
    """A branching episode offers the Modal lens; it reads □ (necessary — on every
    reachable sheet) and ◇ (possible — on some) off the history. (cold) is necessary;
    (cloudy)/(calm) are possible-but-not-necessary."""
    _open_organon(page, app_url)
    _load_uod(page, MODAL)
    _wait_lens_offered(page, "modal")

    page.select_option("#view-lens", "modal")
    page.wait_for_selector(".ml-cols", timeout=10000)
    nec = page.eval_on_selector(".ml-nec", "el => el.textContent")
    pos = page.eval_on_selector(".ml-pos", "el => el.textContent")
    assert "cold" in nec, f"expected cold under □ Necessary, got: {nec}"
    assert "cloudy" in pos and "calm" in pos, f"expected cloudy/calm under ◇ Possible, got: {pos}"
    # the worlds the modality ranges over are drawn, the leaf (cold) marked
    assert page.eval_on_selector_all(".ml-world", "els => els.length") == 4
    # toggling to leaves-only re-fetches (a single endpoint world)
    page.select_option(".ml-over-sel", "leaves")
    page.wait_for_function(
        "document.querySelectorAll('.ml-world').length === 1", timeout=8000)

    page.select_option("#view-lens", "drawing")
    page.wait_for_selector("#organon-canvas svg", timeout=10000)
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_audit_lens_shows_the_verdict_flipping(page, app_url):
    """The dialogue exemplar offers the Audit lens; it peels the declared proposal
    against each successive M and draws the verdict ribbon FALSE→TRUE→FALSE→TRUE, with
    each transition labelled by the admitted fact."""
    _open_organon(page, app_url)
    _load_uod(page, DIALOGUE)
    _wait_lens_offered(page, "audit")

    page.select_option("#view-lens", "audit")
    page.wait_for_selector(".au-state", timeout=10000)
    states = page.eval_on_selector_all(".au-state", "els => els.length")
    assert states == 4, f"expected M0..M3, got {states}"
    # the declared proposal pre-fills the input
    assert page.eval_on_selector("#au-prop", "el => el.value").strip(), \
        "the audit proposal input should pre-fill from the UoD's declared proposal"
    # the verdict ribbon reads FALSE, TRUE, FALSE, TRUE in order
    verdicts = page.eval_on_selector_all(
        ".au-verdict", "els => els.map(e => e.textContent.trim())")
    assert [v.split()[-1] for v in verdicts] == ["FALSE", "TRUE", "FALSE", "TRUE"], verdicts
    # at least one transition is flagged as flipping the verdict
    assert page.eval_on_selector_all(".au-flip", "els => els.length") >= 1

    page.select_option("#view-lens", "drawing")
    time.sleep(1.0)
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_accessible_lens_aria_tree_and_keyboard_nav(page, app_url):
    """The accessible lens mounts a genuine ARIA tree (role=tree/treeitem) for any
    UoD, shows the spoken reading + linear cross-check, and is keyboard-navigable:
    ArrowDown moves focus between visible tree items, Enter collapses a group."""
    _open_organon(page, app_url)
    _load_uod(page, SYNCHRONIC)
    # Offered for the synchronic majority (no chain needed — it is a projection of
    # the graph itself, not of the history).
    assert page.eval_on_selector("#view-lens option[value=accessible]", "o => o.hidden") is False

    page.select_option("#view-lens", "accessible")
    page.wait_for_selector('#organon-canvas ul[role="tree"]', timeout=10000)
    # A real ARIA tree with at least the sheet + some contents.
    items = page.eval_on_selector_all('#organon-canvas li[role="treeitem"]', "els => els.length")
    assert items >= 2, f"expected the sheet plus contents as tree items, got {items}"
    # The root treeitem is the sheet of assertion and is the initial tab stop.
    root_label = page.eval_on_selector(
        '#organon-canvas ul.al-tree > li[role="treeitem"]', "el => el.getAttribute('aria-label')")
    assert "Sheet of assertion" == root_label
    # The spoken reading and the EGIF cross-check are present.
    reading = page.eval_on_selector("#organon-canvas .al-reading", "el => el.textContent")
    assert reading.startswith("The sheet asserts:")
    assert page.eval_on_selector_all("#organon-canvas .al-egif", "els => els.length") == 1

    # Keyboard: focus the root, ArrowDown moves focus to the next visible item.
    page.eval_on_selector('#organon-canvas ul.al-tree > li[role="treeitem"]', "el => el.focus()")
    page.keyboard.press("ArrowDown")
    moved = page.evaluate(
        "() => document.activeElement && document.activeElement.getAttribute('role') === 'treeitem'"
        " && document.activeElement !== document.querySelector('ul.al-tree > li[role=treeitem]')")
    assert moved, "ArrowDown should move focus to the next tree item"

    page.select_option("#view-lens", "drawing")
    page.wait_for_selector("#organon-canvas svg", timeout=10000)
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"


def test_branch_strip_orients_on_a_branching_episode(page, app_url):
    """Charter P1 on the diachronic axis: a reader of a branching UoD sees
    which line they are following and how many exist, from visible text alone
    — the ⑂ chip strip, the honest per-branch counter, the fork cue, and the
    convergence note. And » follows the ACTIVE line to its own leaf (the old
    flat player jumped to the other branch's — the P4 counter lie)."""
    _open_organon(page, app_url)
    _load_uod(page, MODAL)   # possible_and_necessary: the fork-and-converge diamond
    _wait_lens_offered(page, "derivation-dag")

    # The strip is visible with one chip per line; the active line is named.
    page.wait_for_selector("#cp-branches", state="visible", timeout=15000)
    chips = page.query_selector_all("#cp-branches .branch-chip")
    assert len(chips) == 2
    active = page.query_selector("#cp-branches .branch-chip.active")
    assert active and "wind-rises" in active.inner_text()

    # The counter is honest: per-line total + the branch position.
    counter = page.inner_text("#cp-counter")
    assert "branch 1 of 2" in counter and "wind-rises" in counter

    # At the fork (the base state) the cue names both continuations.
    cue = page.inner_text("#cp-fork-cue")
    assert "2 continuations" in cue
    assert "wind-rises" in cue and "clears-first" in cue

    # » lands on the ACTIVE line's leaf; the diamond's converged state says so.
    page.click("#cp-last")
    page.wait_for_function(
        "() => document.getElementById('cp-counter').textContent.includes('2 / 2')",
        timeout=10000)
    counter = page.inner_text("#cp-counter")
    assert "wind-rises" in counter
    assert "lines converge here" in counter

    # Switching lines by chip keeps the shared state and renames the counter.
    page.eval_on_selector_all(
        "#cp-branches .branch-chip",
        "els => { const t = els.find(e => e.textContent.includes('clears-first'));"
        " if (t) t.click(); }")
    page.wait_for_function(
        "() => document.getElementById('cp-counter').textContent.includes('clears-first')",
        timeout=10000)
    counter = page.inner_text("#cp-counter")
    assert "branch 2 of 2" in counter

    assert not page._lens_errors, page._lens_errors


def test_linear_chain_shows_no_branch_strip(page, app_url):
    """A linear proof reads exactly as before: no strip, the plain counter."""
    _open_organon(page, app_url)
    _load_uod(page, CHAINED)   # theorem_praeclarum, a straight line
    _wait_lens_offered(page, "storyboard")
    strip = page.query_selector("#cp-branches")
    assert strip is not None
    assert not strip.is_visible()
    counter = page.inner_text("#cp-counter")
    assert counter.strip() == "base state · 0 / 7"
    assert page.inner_text("#cp-fork-cue").strip() == ""
    assert not page._lens_errors, page._lens_errors
