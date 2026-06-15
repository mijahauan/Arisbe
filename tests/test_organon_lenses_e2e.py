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
SYNCHRONIC = "porphyry_tree"        # no recorded chain
CHAINED = "theorem_praeclarum"      # a worked 7-step proof (linear)
BRANCHING = "branching_confluence"  # a fork-and-merge episode (a DAG)


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
    assert page.eval_on_selector("#view-lens option[value=storyboard]", "o => o.hidden") is False

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
    assert page.eval_on_selector("#view-lens option[value='derivation-dag']", "o => o.hidden") is False
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
    assert page.eval_on_selector("#view-lens option[value='time-stack']", "o => o.hidden") is False

    page.select_option("#view-lens", "time-stack")
    page.wait_for_selector("#organon-canvas canvas", timeout=15000)   # WebGL canvas mounted
    # the lens overlay (Look-along reset + legend) is present
    assert page.eval_on_selector_all("#organon-canvas button", "els => els.length") >= 1

    page.select_option("#view-lens", "drawing")
    time.sleep(1.0)
    assert page.eval_on_selector("#chain-player", "el => el.style.display") == "flex"
    assert not page._lens_errors, f"console/page errors: {page._lens_errors[:5]}"
