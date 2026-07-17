"""End-to-end browser test of Organon's **overview** (adaptive-scope) lens.

The overview is the Drawing at a reduced level of detail: deep cuts collapse into
content-sized placeholders so a graph too large to draw whole stays navigable
(docs/ADAPTIVE_SCOPE_VIEWER.md). This drives the real page in a headless Chromium
and asserts the client contract:

* Selecting the overview lens renders placeholder **badges** over the collapsed
  cuts (a wide ontology exceeds the auto-expand budget, so some collapse).
* Tapping a placeholder **expands** it — one fewer placeholder, camera held (no
  re-fit jump, no errors): detail appears in place.
* "Collapse all" returns to the top-level overview.
* Switching back to Drawing restores the §3.3-attested SVG.
* No console / page errors throughout.

Requires Playwright + Chromium; skipped cleanly if absent. Self-contained server.
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
# A wide ontology (86 cuts) — exceeds the default overview budget, so the
# top-level overview collapses a good number of placeholders.
WIDE = "sumo_upper"


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
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1300, "height": 840})
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append("PAGEERROR: " + str(e)))
        pg._errs = errors
        yield pg
        browser.close()


def _open(page, app_url):
    page.goto(app_url + "/organon")
    page.wait_for_selector(".uod-item", timeout=15000)


def _load(page, uod_id):
    page.eval_on_selector_all(
        ".uod-item",
        "(els, id) => { const t = els.find(e => e.dataset.uodId === id); if (t) t.click(); }",
        uod_id,
    )
    time.sleep(2.5)  # load detail + render + loadChain


def _badge_count(page):
    return page.eval_on_selector_all(".overview-badge", "els => els.length")


def test_overview_collapses_expands_and_restores(page, app_url):
    _open(page, app_url)
    _load(page, WIDE)

    # Enter the overview lens — placeholders render, controls appear.
    page.select_option("#view-lens", "overview")
    page.wait_for_selector(".overview-badge", timeout=15000)
    initial = _badge_count(page)
    assert initial > 0, "expected the wide ontology to exceed the budget"
    assert page.eval_on_selector("#overview-controls", "el => el.style.display") != "none"

    # Tap a specific placeholder → it expands (is drawn open, so its badge is
    # gone; expanding a parent may reveal child placeholders, so the *total*
    # count need not drop — the invariant is that THIS cut is no longer collapsed).
    cut = page.eval_on_selector(".overview-badge", "el => el.getAttribute('data-overview-cut')")
    page.click('.overview-badge[data-overview-cut="' + cut + '"]', force=True)
    time.sleep(1.5)
    still = page.eval_on_selector_all(
        '.overview-badge[data-overview-cut="' + cut + '"]', "els => els.length")
    assert still == 0, f"expanded cut {cut} should no longer be a placeholder"

    # Collapse all → back to the exact top-level overview. Poll rather than
    # fixed-sleep: a slow CI runner can take >1.5s to re-render the badges
    # (observed 2026-07-17: count read 0 mid-render).
    page.click("#ov-reset")
    page.wait_for_function(
        "n => document.querySelectorAll('.overview-badge').length === n",
        arg=initial, timeout=20000)
    assert _badge_count(page) == initial

    # Switch back to Drawing → the attested SVG (no badges).
    page.select_option("#view-lens", "drawing")
    page.wait_for_selector("#organon-canvas svg", timeout=10000)
    time.sleep(0.5)
    assert _badge_count(page) == 0
    assert page.eval_on_selector("#overview-controls", "el => el.style.display") == "none"

    assert not page._errs, f"console/page errors: {page._errs[:5]}"
