"""End-to-end browser test of the freeform composition canvas (build step 2).

Unlike the route tests (which post hand-built drawing JSON), this drives the *real*
pointer interactions in a headless Chromium: arm a tool, click the canvas to place
marks, connect them, "Read it now", and "① Fix" — then assert the Graph↔Argument
two-mode switch flips and the lock badge reads FIXED.  This closes the one gap the
non-browser tests can't: that the SVG canvas's pointer handlers actually place and
wire marks, and that the page wires the canvas to the endpoints.

Requires Playwright + Chromium (``uv run playwright install chromium``); skipped
cleanly if absent.  Spawns the app on its own port so it is self-contained.
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
                if urllib.request.urlopen(url + "/ergasterion", timeout=2).status == 200:
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
        pg.on("dialog", lambda d: d.accept("loves"))  # the Relation-name prompt
        yield pg
        browser.close()


def _click_canvas(page, frac_x, frac_y):
    box = page.locator("#canvas").bounding_box()
    page.mouse.click(box["x"] + box["width"] * frac_x,
                     box["y"] + box["height"] * frac_y)


def test_freeform_draw_read_fix_and_two_mode_switch(page, app_url):
    page.goto(app_url + "/ergasterion")
    page.click("#btn-start-empty")
    page.wait_for_selector("#workspace-switch", state="visible")

    # Unfixed: The Argument is locked.
    assert "active" in (page.get_attribute("#seg-graph", "class") or "")
    assert "locked" in (page.get_attribute("#seg-argument", "class") or "")
    assert "unfixed" in (page.get_attribute("#ws-state", "class") or "")

    # Enter freeform; arm the Relation tool and place a labelled spot.
    page.click("#btn-freeform-toggle")
    page.wait_for_selector("#freeform-tools", state="visible")
    page.click('#freeform-tools [data-fftool="predicate"]')
    _click_canvas(page, 0.5, 0.3)              # "loves" (dialog accepts the name)

    # Two vertices.
    page.click('#freeform-tools [data-fftool="vertex"]')
    _click_canvas(page, 0.32, 0.7)
    _click_canvas(page, 0.68, 0.7)

    # Connect predicate→each vertex (argument order = connect order).
    page.click('#freeform-tools [data-fftool="line"]')
    _click_canvas(page, 0.5, 0.3); _click_canvas(page, 0.32, 0.7)
    _click_canvas(page, 0.5, 0.3); _click_canvas(page, 0.68, 0.7)

    # Read it now — composition speaks.
    page.click("#btn-read-drawing")
    page.wait_for_function(
        "document.querySelector('#freeform-validity') && "
        "document.querySelector('#freeform-validity').textContent.includes('reads as')",
        timeout=8000)
    assert "loves" in page.text_content("#freeform-validity")

    # Fix the graph → the picture becomes the fixed utterance.
    page.click("#btn-fix-graph")
    page.wait_for_function(
        "document.querySelector('#seg-argument') && "
        "document.querySelector('#seg-argument').classList.contains('active')",
        timeout=8000)
    # Now FIXED: meaning locked, the Argument workspace is active, Graph re-opens.
    assert "fixed" in (page.get_attribute("#ws-state", "class") or "")
    assert "Edit base graph" in (page.text_content("#seg-graph") or "")
    # Settle (single-graph appearance) is clustered up top and visible once fixed.
    assert page.eval_on_selector("#settle-row", "e=>getComputedStyle(e).display") != "none"

    # The Graph↔Argument round-trip: "Edit base graph" must visibly re-open the
    # editable freeform surface, seeded with the graph (the detach bug regression).
    page.click("#seg-graph")
    page.wait_for_function(
        "document.querySelector('#ws-state').classList.contains('unfixed')", timeout=8000)
    page.wait_for_selector(".freeform-wrap", state="visible", timeout=8000)
    assert page.eval_on_selector(".freeform-wrap", "e=>getComputedStyle(e).display") == "block"
    # Seeded, not blank: the 'loves' relation mark is on the re-opened canvas.
    assert page.eval_on_selector_all(
        ".freeform-wrap text", "els=>els.some(e=>e.textContent==='loves')")
