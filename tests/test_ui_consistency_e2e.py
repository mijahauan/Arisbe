"""End-to-end browser checks for the UI Transparency Charter surfaces
(docs/UI_TRANSPARENCY_CHARTER.md), across the three modes:

* P1 — every mode shows its one-line orientation strip (plain words:
  where you are, what can't happen here).
* P3 — the six rule buttons carry their second-line plain names from
  GET /rules (never a bare acronym).
* P2 — the style dropdowns are populated from GET /styles with the same
  display names everywhere; the Agon M-picker has a working search.
* P7 — a [data-term] element shows the glossary hover card with a
  definition and a "more →" link into the book anchor.

Requires Playwright + Chromium; skipped cleanly if absent. Self-contained
server (the test_primer_e2e.py scaffold).
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
    """Whether the Playwright Chromium executable is actually installed —
    importorskip only proves the *package*; the browser download is separate
    (`uv run playwright install chromium`), and a missing executable should
    skip, not error (the docstring's promise)."""
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
        pg = browser.new_page(viewport={"width": 1300, "height": 900})
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append("PAGEERROR: " + str(e)))
        pg._errs = errors
        yield pg
        browser.close()


ORIENTATION = {
    "organon": "nothing you do here changes the corpus",
    "ergasterion": "the corpus\n          is reached only through agon",
    "agon": "nothing is\n        recorded unless you, as judge, assert",
}


@pytest.mark.parametrize("mode", ["organon", "ergasterion", "agon"])
def test_orientation_strip_present_per_mode(page, app_url, mode):
    """P1: one plain-words strip per mode, visible with no hover."""
    page.goto(app_url + "/" + mode)
    if mode == "ergasterion":
        # Ergasterion's persistent line is the regime banner.
        text = page.eval_on_selector(".regime-banner", "el => el.textContent")
        assert "corpus" in text and "Agon" in text
    else:
        page.wait_for_selector(".mode-orientation", timeout=8000)
        strips = page.eval_on_selector_all(
            ".mode-orientation", "els => els.map(e => e.textContent)")
        assert len(strips) == 1
        key = "changes the corpus" if mode == "organon" else "assert the result"
        assert key in strips[0]
    assert not page._errs, f"console/page errors: {page._errs}"


@pytest.mark.parametrize("mode", ["ergasterion", "agon"])
def test_rule_buttons_carry_plain_names(page, app_url, mode):
    """P3: the acronym never stands alone — each button grows its name."""
    page.goto(app_url + "/" + mode)
    page.wait_for_selector('button[data-rule="ERA"] .rb-name', timeout=10000)
    names = page.eval_on_selector_all(
        "button[data-rule] .rb-name", "els => els.map(e => e.textContent)")
    assert "Erase" in names and "Insert" in names and "Iterate" in names
    title = page.eval_on_selector('button[data-rule="ERA"]', "el => el.title")
    assert "recto" in title  # polarity in words, never hue
    assert not page._errs, f"console/page errors: {page._errs}"


def test_style_selects_populated_from_server(page, app_url):
    """P2: the same served style list, same display names, both modes."""
    page.goto(app_url + "/organon")
    page.wait_for_function(
        "document.querySelectorAll('#view-style option').length === 3", timeout=10000)
    organon_opts = page.eval_on_selector_all(
        "#view-style option", "els => els.map(e => e.textContent)")
    assert any("Peirce — handwritten" in o for o in organon_opts)
    assert any("(default)" in o for o in organon_opts)

    page.goto(app_url + "/ergasterion")
    page.wait_for_function(
        "document.querySelectorAll('#style-select option').length === 3", timeout=10000)
    erg_opts = page.eval_on_selector_all(
        "#style-select option", "els => els.map(e => e.textContent)")
    assert set(erg_opts) == set(organon_opts)  # one list, every mode
    assert not page._errs, f"console/page errors: {page._errs}"


def test_agon_model_search_filters_the_picker(page, app_url):
    """P2: the M-picker is searchable with Organon's semantics."""
    page.goto(app_url + "/agon")
    page.wait_for_function(
        "document.querySelectorAll('#model-picker option').length > 1", timeout=15000)
    before = page.eval_on_selector_all("#model-picker option", "els => els.length")
    page.fill("#model-filter", "zzz-no-such-model")
    page.wait_for_function(
        f"document.querySelectorAll('#model-picker option').length < {before}",
        timeout=5000)
    after = page.eval_on_selector_all("#model-picker option", "els => els.length")
    assert after < before
    # Clearing the search restores the full list.
    page.fill("#model-filter", "")
    page.wait_for_function(
        f"document.querySelectorAll('#model-picker option').length === {before}",
        timeout=5000)
    assert not page._errs, f"console/page errors: {page._errs}"


def test_term_help_hover_card_defines_and_links(page, app_url):
    """P7: a data-term shows its definition on hover with a book link."""
    page.goto(app_url + "/agon")
    page.wait_for_selector('[data-term="graphist"]', timeout=10000)
    # Give term-help.js time to fetch /glossary.
    page.wait_for_function("!!window.TermHelp && !!window.TermHelp.define('graphist')",
                           timeout=10000)
    page.hover('[data-term="graphist"]')
    page.wait_for_selector("#term-help-card", state="visible", timeout=5000)
    card = page.eval_on_selector("#term-help-card", "el => el.textContent")
    assert "propose" in card.lower() or "endoporeutic" in card.lower()
    href = page.eval_on_selector("#term-help-card .th-more", "el => el.href")
    assert "/book/GLOSSARY.html#" in href
    # Escape dismisses (keyboard path).
    page.keyboard.press("Escape")
    page.wait_for_selector("#term-help-card", state="hidden", timeout=5000)
    assert not page._errs, f"console/page errors: {page._errs}"
