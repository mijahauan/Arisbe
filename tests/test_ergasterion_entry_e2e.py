"""End-to-end browser checks for the **Ergasterion entry doors** — the use-case
paths a newcomer must be able to see without discovering them by accident
(docs/UI_TRANSPARENCY_CHARTER.md P1 orientation · P3 recognition-never-recall ·
P5 prevent-don't-punish).

The entry screen answers two questions, in this order:

  1. *Are you making a graph, or working on one?*  → two groups of doors
     ("Make a graph": blank sheet · from a linear form · challenge;
      "Work on an existing graph": corpus · a saved draft · import)
  2. *What will you do to it?*  → the three regimes as three doors, stated as
     consequences and never as regime numbers:
       ✋ Rearrange it     — regime 3: the picture only; meaning CANNOT change
       ⊢ Reason from it   — regime 2: the six rules; checked and recorded
       ✎ Re-open as clay  — regime 1: a DIFFERENT graph, claiming nothing

Also pins what the composing panel may offer *yet*. Settle used to be hidden
until a graph was FIXED, which left the only gesture that resizes a cut invisible
exactly while a user is arranging the sheet — their drag silently did nothing.
But it must not appear on a *blank* sheet either: with nothing drawn there is
nothing to settle, and an affordance that does nothing is the same failure in the
other direction. So: Settle (and gate ①) appear as soon as there is something to
settle — and not before.

Requires Playwright + Chromium; skipped cleanly if absent.
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


def _chromium_available() -> bool:
    try:
        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _chromium_available(),
    reason="Playwright Chromium not installed (uv run playwright install chromium)",
)


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
                if urllib.request.urlopen(url + "/glossary", timeout=2).status == 200:
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
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg._errs = []
        pg.on("pageerror", lambda e: pg._errs.append(str(e)))
        yield pg
        browser.close()


# --- question 1: making, or working on? ------------------------------------- #

def test_entry_offers_both_groups_of_doors(page, app_url):
    """P1: the two questions are visible on arrival, not discovered by trying."""
    page.goto(app_url + "/ergasterion")
    heads = page.eval_on_selector_all(
        ".entry-group-head", "els => els.map(e => e.textContent.trim())")
    assert "Make a graph" in heads
    assert "Work on an existing graph" in heads
    # every door states its consequence on a second line (never a bare label)
    subs = page.eval_on_selector_all(
        "#picker-section .entry-sub", "els => els.map(e => e.textContent.trim())")
    assert len(subs) >= 3 and all(subs)
    assert not page._errs, f"page errors: {page._errs}"


def test_import_is_reachable_from_the_workshop(page, app_url):
    """A file is a way in too — the workshop links it rather than hiding it on
    another page with no path back."""
    page.goto(app_url + "/ergasterion")
    href = page.get_attribute("#picker-section a[href='/import']", "href")
    assert href == "/import"


# --- the linear-form door ---------------------------------------------------- #

def test_linear_form_door_opens_the_graph_it_denotes(page, app_url):
    """Paste EGIF → a real graph on the sheet, as clay. The `graft` op already
    did this; it was buried in a collapsed 'Fragment' disclosure *inside* the
    palette (i.e. only findable once you were already in). Now it is a door."""
    page.goto(app_url + "/ergasterion")
    page.click("#btn-start-linear")
    page.fill("#linear-egif", '(Human *x) ~[ (Mortal x) ]')
    page.click("#btn-linear-go")
    page.wait_for_selector("#palette-block", state="visible", timeout=15000)
    # the pasted form is drawn: two predicate spots (Human, Mortal) + a cut
    page.wait_for_function(
        "document.querySelectorAll('#canvas svg text').length >= 2", timeout=15000)
    assert not page._errs, f"page errors: {page._errs}"


def test_unparseable_linear_form_is_an_honest_non_result(page, app_url):
    """P5/P6: bad EGIF says what the parser objected to and leaves the sheet
    open — it never crashes, and never punishes with a raw code."""
    page.goto(app_url + "/ergasterion")
    page.click("#btn-start-linear")
    page.fill("#linear-egif", "(Human *x")          # unbalanced — will not parse
    page.click("#btn-linear-go")
    page.wait_for_function(                        # past the "Reading it…" placeholder
        "document.querySelector('#linear-feedback')"
        ".textContent.indexOf('Could not read it') >= 0", timeout=15000)
    fb = page.text_content("#linear-feedback")
    # the parser's own words reach the user — not a bare code (P6, error language)
    assert "close relation" in fb, fb
    # …and the sheet is still open to compose by hand (P5: prevent, don't punish)
    assert page.is_visible("#palette-block")
    assert not page._errs, f"page errors: {page._errs}"


# --- question 2: the three regimes as three doors ---------------------------- #

def test_picking_a_corpus_graph_asks_what_you_will_do_to_it(page, app_url):
    """The door the UI never had. Picking an existing graph does not silently
    land you in one posture — it asks, in consequences, never in regime numbers."""
    page.goto(app_url + "/ergasterion")
    page.wait_for_selector(".corpus-uod-item", timeout=15000)
    page.click(".corpus-uod-item")
    page.wait_for_selector("#intent-section", state="visible", timeout=10000)

    labels = page.eval_on_selector_all(
        "#intent-section button.action",
        "els => els.map(e => e.textContent.trim())")
    joined = " ".join(labels)
    assert "Rearrange it" in joined      # regime 3
    assert "Reason from it" in joined    # regime 2
    assert "Re-open as clay" in joined   # regime 1
    # stated as consequences, not as regime numbers
    assert "cannot" in joined.lower() and "different" in joined.lower()
    assert "regime 1" not in joined.lower() and "regime 3" not in joined.lower()
    assert not page._errs, f"page errors: {page._errs}"


def test_rearrange_opens_with_settle_armed(page, app_url):
    """'Rearrange it' = regime 3: it hands you the tool that moves marks and
    resizes cuts, already on. Nothing done here can change the meaning."""
    page.goto(app_url + "/ergasterion")
    page.wait_for_selector(".corpus-uod-item", timeout=15000)
    page.click(".corpus-uod-item")
    page.wait_for_selector("#btn-intent-rearrange", state="visible", timeout=10000)
    page.click("#btn-intent-rearrange")
    page.wait_for_function(
        "document.querySelector('#btn-settle') && "
        "document.querySelector('#btn-settle').classList.contains('primary')",
        timeout=15000)
    assert not page._errs, f"page errors: {page._errs}"


def test_intent_back_returns_to_the_doors(page, app_url):
    """P5: a chooser you can leave. Picking a graph is not a commitment."""
    page.goto(app_url + "/ergasterion")
    page.wait_for_selector(".corpus-uod-item", timeout=15000)
    page.click(".corpus-uod-item")
    page.wait_for_selector("#intent-section", state="visible", timeout=10000)
    page.click("#btn-intent-back")
    page.wait_for_selector("#picker-section", state="visible", timeout=5000)
    assert page.is_hidden("#intent-section")


# --- the composing panel offers only what applies YET ------------------------ #
# A blank sheet is not a graph: there is nothing to settle (no drawing) and
# nothing to fix (no assertion — and the blank sheet is precisely what cannot be
# posited: docs/LEVEL_ZERO_AND_THE_REGISTERS.md). Offering either is an
# affordance that does nothing — the same failure as hiding one that would.

def _blank_sheet(page, app_url):
    page.goto(app_url + "/ergasterion")
    page.click("#btn-start-empty")
    page.wait_for_selector("#palette-block", state="visible", timeout=15000)


def test_blank_sheet_offers_neither_settle_nor_fix(page, app_url):
    _blank_sheet(page, app_url)
    assert page.is_hidden("#btn-settle"), "nothing is drawn — nothing to settle"
    assert page.eval_on_selector("#btn-fix-graph", "e => e.disabled"), \
        "a blank sheet asserts nothing — gate ① must not fix it"
    # …and it says why, in plain words (P5 prevent-don't-punish, P6 error language)
    assert "blank sheet asserts nothing" in page.get_attribute("#btn-fix-graph", "title")
    assert not page._errs, f"page errors: {page._errs}"


def test_placing_a_mark_earns_settle_and_fix(page, app_url):
    """As soon as there IS a graph, both become available — this is the cut-resize
    path: place a cut, then Settle can size it by hand."""
    _blank_sheet(page, app_url)
    page.click('button[data-tool="add_cut"]')
    box = page.query_selector("#canvas").bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_function(
        "!document.querySelector('#btn-fix-graph').disabled", timeout=15000)
    assert page.is_visible("#btn-settle"), "a drawn cut can be settled (resized)"
    assert not page._errs, f"page errors: {page._errs}"


# --- the two ways to compose are named, and mutually exclusive ---------------- #

def test_compose_mode_switch_names_both_ways_and_says_the_difference(page, app_url):
    """P2 (one word, one way) + P3: 'Freeform draw' used to be a lone button among
    actions, so the difference from the palette was undiscoverable — and two 'Cut'
    buttons with different behaviour sat on screen at once. The two ways are now a
    named, exclusive mode switch that states who does what."""
    _blank_sheet(page, app_url)
    segs = page.eval_on_selector_all(
        ".cm-seg", "els => els.map(e => e.textContent.trim())")
    assert "▦ Place marks" in segs and "✎ Draw freehand" in segs
    # place is the default, and it says what it means
    assert "You name the structure" in page.text_content("#compose-mode-note")
    assert page.is_visible("#palette-block .palette-grid")

    page.click("#cm-draw")
    page.wait_for_function(
        "document.querySelector('#compose-mode-note')"
        ".textContent.indexOf('You draw the marks') >= 0", timeout=10000)
    # exclusive: the palette's marks give way to the drawing tools
    assert page.is_hidden("#palette-block .palette-grid")
    assert page.is_visible("#freeform-tools")
    # and there is no DTO to settle while the content is ink
    assert page.is_hidden("#btn-settle")

    page.click("#cm-place")
    page.wait_for_function(
        "document.querySelector('#compose-mode-note')"
        ".textContent.indexOf('You name the structure') >= 0", timeout=10000)
    assert page.is_visible("#palette-block .palette-grid")
    assert not page._errs, f"page errors: {page._errs}"
