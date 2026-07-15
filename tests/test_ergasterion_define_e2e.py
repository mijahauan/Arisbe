"""End-to-end browser test of the fold-to-define authoring UI (build A frontend).

Drives the real pointer interactions in a headless Chromium: draw a unary relation
freehand, fix it, then *name this subgraph* — select the body, designate the hook
line as the single port (argument order), and fold it into one defined spot — then
unfold it back. This closes the gap the route tests (``test_ergasterion_define.py``)
can't: that the canvas selection → ordered-port designation → ``/define-fold`` and
the per-spot ``/define-unfold`` affordance are actually wired in the page.

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
        pg.on("dialog", lambda d: d.accept("man"))  # the Relation-name prompt
        yield pg
        browser.close()


def _click_canvas(page, frac_x, frac_y):
    box = page.locator("#canvas").bounding_box()
    page.mouse.click(box["x"] + box["width"] * frac_x,
                     box["y"] + box["height"] * frac_y)


def _draw_and_fix_man(page):
    """Draw man(x) freehand and fix it → lands in the Argument workspace."""
    page.click("#btn-start-empty")
    page.wait_for_selector("#workspace-switch", state="visible")
    # Draw mode is entered by the compose-mode switch — the palette and the
    # drawing tools are two named, exclusive ways to make a graph.
    page.click("#cm-draw")
    page.wait_for_selector("#freeform-tools", state="visible")
    page.click('#freeform-tools [data-fftool="predicate"]')
    _click_canvas(page, 0.5, 0.3)                 # "man" (dialog accepts the name)
    page.click('#freeform-tools [data-fftool="vertex"]')
    _click_canvas(page, 0.5, 0.65)
    page.click('#freeform-tools [data-fftool="line"]')
    _click_canvas(page, 0.5, 0.3); _click_canvas(page, 0.5, 0.65)
    page.click("#btn-read-drawing")
    page.wait_for_function(
        "document.querySelector('#freeform-validity') && "
        "document.querySelector('#freeform-validity').textContent.includes('reads as')",
        timeout=8000)
    page.click("#btn-fix-graph")
    page.wait_for_function(
        "document.querySelector('#seg-argument').classList.contains('active')",
        timeout=8000)


def test_fold_to_define_then_unfold(page, app_url):
    page.goto(app_url + "/ergasterion")
    _draw_and_fix_man(page)

    # The Define panel is live in the Argument workspace (deriving phase).
    assert page.eval_on_selector(
        "#definitions-panel", "e=>getComputedStyle(e).display") != "none"

    # Select the predicate as the body of the definition.
    page.click('#canvas g[data-element-type="predicate"]')
    page.wait_for_function(
        "document.querySelector('#sel-subgraph-display').textContent.trim() !== 'none'",
        timeout=5000)

    # Designate the line (vertex) as the single port, in argument order.
    page.click("#btn-def-ports")
    assert "armed" in (page.get_attribute("#btn-def-ports", "class") or "")
    page.click('#canvas g[data-element-type="vertex"]')
    page.wait_for_function(
        "document.querySelector('#def-ports-readout').textContent.includes('1·')",
        timeout=5000)

    # Name it and fold — the subgraph becomes one defined spot.
    page.fill("#def-name", "Person")
    page.click("#btn-define-fold")
    page.wait_for_function(
        "document.querySelector('#definitions-list').textContent.includes('Person')",
        timeout=8000)
    # A live, unfoldable spot exists; the relation 'man' has been abstracted away.
    page.wait_for_selector("#definitions-list .def-unfold", state="visible", timeout=5000)
    assert not page.eval_on_selector_all(
        "#canvas text", "els=>els.some(e=>e.textContent==='man')")
    # Authoring state resets after a successful fold.
    assert "armed" not in (page.get_attribute("#btn-def-ports", "class") or "")
    assert page.input_value("#def-name") == ""

    # Unfold restores the body; the live spot disappears, the definition persists.
    page.click("#definitions-list .def-unfold")
    page.wait_for_function(
        "!document.querySelector('#definitions-list .def-unfold')", timeout=8000)
    page.wait_for_function(
        "Array.from(document.querySelectorAll('#canvas text'))"
        ".some(e=>e.textContent==='man')",
        timeout=5000)
    assert "Person" in page.text_content("#definitions-list")


def test_define_refused_without_a_name(page, app_url):
    """A definition needs a name — folding with none gives in-panel feedback,
    does not mutate the graph, and never reaches the server."""
    page.goto(app_url + "/ergasterion")
    _draw_and_fix_man(page)

    page.click('#canvas g[data-element-type="predicate"]')
    page.wait_for_function(
        "document.querySelector('#sel-subgraph-display').textContent.trim() !== 'none'",
        timeout=5000)
    page.click("#btn-define-fold")
    page.wait_for_function(
        "document.querySelector('#def-feedback').textContent.toLowerCase()"
        ".includes('name')",
        timeout=5000)
    # The relation is untouched (no spot created).
    assert page.eval_on_selector_all(
        "#canvas text", "els=>els.some(e=>e.textContent==='man')")
    assert "No definitions yet" in page.text_content("#definitions-list")
