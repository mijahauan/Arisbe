"""End-to-end browser test of the in-app **primer** — the newcomer's "first
graph" front door (`web_viewer/js/primer.js`, the guided entry to the Field
Guide, docs/FIELD_GUIDE_AND_DRAGONS.md).

The newcomer's journey is Organon → Ergasterion → Agon, and to *author* a graph
the learner first needs the notation. The primer teaches the four marks without
throwing EGIF cold, and draws its worked first graphs with the real engine. This
drives the real pages in a headless Chromium and asserts:

* The home page "New here?" door opens the primer overlay (the four marks + the
  EGIF key + the worked first graphs drawn as SVG).
* Every mode page (Organon / Ergasterion / Agon) grows a "New here?" link in the
  shared mode-nav that opens the same overlay.
* A drawable-dragon chip deep-links into Ergasterion challenge mode with that
  dragon's challenge engaged.
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
                if urllib.request.urlopen(url + "/primer/examples", timeout=2).status == 200:
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


def test_home_door_opens_primer_with_drawn_examples(page, app_url):
    page.goto(app_url + "/")
    page.click("#primer-door")
    page.wait_for_selector("#primer-overlay.open", timeout=8000)

    # The four marks + the EGIF key are present.
    text = page.eval_on_selector("#primer-overlay", "el => el.textContent")
    assert "four marks" in text.lower()
    assert "scroll" in text.lower()  # the if-then mark
    # The worked first graphs are drawn by the real engine (SVG, not described).
    page.wait_for_selector("#primer-examples .primer-ex .draw svg", timeout=8000)
    n_drawn = page.eval_on_selector_all(
        "#primer-examples .primer-ex .draw svg", "els => els.length")
    assert n_drawn >= 3, f"expected ≥3 drawn examples, got {n_drawn}"

    # Closing the overlay works.
    page.click("#primer-overlay .primer-close")
    assert page.eval_on_selector(
        "#primer-overlay", "el => el.classList.contains('open')") is False
    assert not page._errs, f"console/page errors: {page._errs}"


@pytest.mark.parametrize("mode", ["organon", "ergasterion", "agon"])
def test_new_here_link_on_every_mode(page, app_url, mode):
    page.goto(app_url + "/" + mode)
    # mode-nav renders, then primer.js appends its "New here?" link.
    page.wait_for_selector(".primer-newhere", timeout=10000)
    page.click(".primer-newhere")
    page.wait_for_selector("#primer-overlay.open", timeout=8000)
    text = page.eval_on_selector("#primer-overlay", "el => el.textContent")
    assert "marks" in text.lower()
    assert not page._errs, f"console/page errors on {mode}: {page._errs}"


def test_dragon_chip_deeplinks_into_challenge(page, app_url):
    page.goto(app_url + "/agon")
    page.wait_for_selector(".primer-newhere", timeout=10000)
    page.click(".primer-newhere")
    page.wait_for_selector("#primer-overlay.open", timeout=8000)
    # The drawable-dragon chips link into Ergasterion challenge mode.
    href = page.eval_on_selector(
        "#primer-overlay .primer-dragons a", "el => el.getAttribute('href')")
    assert href.startswith("/ergasterion?challenge=")

    # Following dragon 1 lands in a session with that challenge's prompt engaged.
    page.goto(app_url + "/ergasterion?challenge=" + "%F0%9F%90%891")  # 🐉1
    page.wait_for_selector("#challenge-prompt", timeout=15000)
    # the change handler fills the prompt with "Draw: <egif>"
    deadline = time.time() + 12
    prompt = ""
    while time.time() < deadline:
        prompt = page.eval_on_selector("#challenge-prompt", "el => el.textContent") or ""
        if "Draw" in prompt:
            break
        time.sleep(0.5)
    assert "Draw" in prompt, f"challenge not engaged; prompt={prompt!r}"

    # U2 (regression): the deep-link must leave the freeform canvas *armed* — the
    # earlier race let openSession() disable freeform after the challenge armed it,
    # stranding the newcomer with the prompt but no draw tools. The freeform tools
    # row is revealed and the toggle carries the 'armed' class once engaged.
    deadline = time.time() + 12
    armed = False
    while time.time() < deadline:
        tools_shown = page.eval_on_selector(
            "#freeform-tools", "el => getComputedStyle(el).display !== 'none'")
        toggle_armed = page.eval_on_selector(
            "#btn-freeform-toggle", "el => el.classList.contains('armed')")
        if tools_shown and toggle_armed:
            armed = True
            break
        time.sleep(0.5)
    assert armed, "deep-link left the freeform canvas disabled (U2 race regressed)"
