"""End-to-end browser test of the **context reflex** — the shared
ContextReflex panel across Organon, Ergasterion, and Agon.

The field guide's first reflex (docs/FIELD_GUIDE_AND_DRAGONS.md, point 4): a
lone graph is an *extract* — ask after its **ground** (which universe it is
asserted in) and its **structure** (which cuts enclose a chosen element). One
shared module (`js/context-reflex.js`) renders that in every mode. This drives
the real pages in a headless Chromium and asserts:

* The panel appears in Organon when a corpus UoD is viewed, showing the ground;
  clicking an element shows the enclosing-cut breadcrumb.
* The shared module's pure logic (`enclosureChain` / `describeElement`) is
  present and correct on all three mode pages (the cross-mode contract).
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
# A derived, nested corpus proof (9 areas, a real chain) — exercises both the
# ground (a derivation: state N of M) and the enclosure breadcrumb (cuts nest).
NESTED = "theorem_praeclarum"

# A synthetic /introspect payload: sheet ⊃ C1(¬) ⊃ C2(+), an edge P(v1) in C2.
SYNTH = """{
  "areas": {
    "S":  {"is_sheet": true,  "polarity": "positive", "depth": 0, "parent": null},
    "C1": {"is_sheet": false, "polarity": "negative", "depth": 1, "parent": "S"},
    "C2": {"is_sheet": false, "polarity": "positive", "depth": 2, "parent": "C1"}
  },
  "elements": {
    "e1": {"type": "edge", "relation": "P", "arity": 1,
           "incident_vertices": ["v1"], "area": "C2", "polarity": "positive", "depth": 2},
    "v1": {"type": "vertex", "label": null, "area": "C2", "polarity": "positive", "depth": 2}
  }
}"""


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


def test_organon_context_panel_ground_and_enclosure(page, app_url):
    page.goto(app_url + "/organon")
    page.wait_for_selector(".uod-item", timeout=15000)
    page.eval_on_selector_all(
        ".uod-item",
        "(els, id) => { const t = els.find(e => e.dataset.uodId === id); if (t) t.click(); }",
        NESTED,
    )
    # The panel attaches after the drawing renders; a chained UoD then loads its
    # chain and shows a derivation position.
    page.wait_for_selector(".cx-panel", timeout=15000)
    time.sleep(2.5)

    ground = page.eval_on_selector(".cx-panel .cx-sec", "el => el.textContent")
    assert "ground" in ground.lower()
    # The chain player fills a derivation position ("… of N").
    panel_text = page.eval_on_selector(".cx-panel", "el => el.textContent")
    assert " of " in panel_text, f"expected a derivation position, got: {panel_text!r}"

    # A chained proof opens on its base (near-blank) frame — jump to the last
    # state so the full theorem (with elements to click) is on the canvas.
    if page.query_selector("#cp-last"):
        page.click("#cp-last")
        time.sleep(2.0)  # render the final frame + its introspection fetch

    # Click an element in the drawing → the enclosure breadcrumb appears.
    page.wait_for_selector("#organon-canvas svg [data-element-id]", timeout=10000)
    clicked = page.eval_on_selector_all(
        "#organon-canvas svg [data-element-id]",
        "els => { if (!els.length) return false; els[0].dispatchEvent("
        "new MouseEvent('click', {bubbles: true})); return true; }",
    )
    assert clicked, "no clickable element in the drawing"
    page.wait_for_selector(".cx-crumbs", timeout=8000)
    crumbs = page.eval_on_selector(".cx-crumbs", "el => el.textContent")
    assert "sheet" in crumbs and "here" in crumbs

    assert not page._errs, f"console/page errors: {page._errs[:5]}"


@pytest.mark.parametrize("mode", ["organon", "ergasterion", "agon"])
def test_context_reflex_module_present_and_correct(page, app_url, mode):
    """The shared module loads on every mode page and its pure enclosure logic
    is correct — the cross-mode contract, independent of per-mode UI setup."""
    page.goto(app_url + "/" + mode)
    page.wait_for_function("() => !!window.ContextReflex", timeout=15000)

    chain = page.evaluate(
        "(intro) => window.ContextReflex.enclosureChain(intro, 'e1')",
        __import__("json").loads(SYNTH),
    )
    # Innermost area first, up to the sheet: C2 (+) → C1 (¬) → S (sheet).
    assert [c["id"] for c in chain] == ["C2", "C1", "S"]
    assert chain[-1]["isSheet"] is True
    assert chain[0]["polarity"] == "positive" and chain[1]["polarity"] == "negative"

    desc = page.evaluate(
        "(intro) => window.ContextReflex.describeElement(intro, 'e1')",
        __import__("json").loads(SYNTH),
    )
    assert desc["kind"] == "edge" and desc["throughLines"] == 1

    assert not page._errs, f"console/page errors on {mode}: {page._errs[:5]}"
