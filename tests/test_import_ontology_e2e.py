"""End-to-end browser test of the **ontology file-import** surface on /import
(web_viewer/import.html) — the ontologist's web door (docket U1/U17/U22/U25).

Before this, an ontologist could only *paste a linear form*; OWL/RDF/SUO-KIF was
CLI-only. This drives the real page in a headless Chromium and asserts the
ontology mode works end to end (read-only — the check flow, which never writes to
the corpus): switch to "Ontology file", paste the zoo OWL fixture, translate, and
see the construct-level skip-report + the drawn graph, with no console errors.

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
_ZOO_OFN = (Path(__file__).parent / "fixtures" / "zoo.ofn").read_text()


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
                if urllib.request.urlopen(url + "/import/citation-types", timeout=2).status == 200:
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
        pg = browser.new_page(viewport={"width": 1400, "height": 900})
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append("PAGEERROR: " + str(e)))
        pg._errs = errors
        yield pg
        browser.close()


def test_ontology_mode_translates_and_shows_skip_report(page, app_url):
    page.goto(app_url + "/import")
    # Switch to the ontology file import mode.
    page.wait_for_selector("#mode-ontology", timeout=10000)
    page.click("#mode-ontology")
    # The ontology block is shown; the bibliography section is hidden.
    assert page.eval_on_selector("#ontology-mode", "el => getComputedStyle(el).display") != "none"
    assert page.eval_on_selector("#bib-section", "el => getComputedStyle(el).display") == "none"

    # Paste the OWL fixture and translate.
    page.fill("#onto-input", _ZOO_OFN)
    page.select_option("#onto-format", "owl")
    page.click("#btn-check-onto")

    # The skip-report appears (partial translation, reported not dropped) …
    page.wait_for_selector("#onto-results", timeout=15000)
    deadline = time.time() + 12
    skipped = ""
    while time.time() < deadline:
        skipped = page.eval_on_selector("#onto-skipped", "el => el.textContent") or ""
        if "Not translated" in skipped or "came across" in skipped:
            break
        time.sleep(0.4)
    assert "Not translated" in skipped, f"skip-report not shown; got {skipped!r}"

    # … the translated-counts badge reads OK …
    assert page.eval_on_selector("#ob-parse", "el => el.textContent") == "OK"
    # … and the graph is drawn (the zoo fixture is small enough to render).
    page.wait_for_selector("#canvas svg", timeout=15000)

    # The Admit button becomes live (a valid, in-scale ontology).
    assert page.eval_on_selector("#btn-admit", "el => el.disabled") is False
    assert not page._errs, f"console/page errors: {page._errs}"
