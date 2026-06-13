"""End-to-end browser test of the automated-Grapheus contest board (increment 3).

Unlike the route tests (which post JSON to ``/agon/contests``), this drives the real
page in a headless Chromium: type a model M + proposal G, click "Contest the Grapheus",
pick a witness at the contested frontier, and assert the board reaches a verdict and
surfaces the disposition taxonomy — closing the gap that the page actually wires the
contest endpoints to the clickable frontier options.

The flow mirrors docs/AUTOMATED_GRAPHEUS.md §9.3: propose G → contest a model M →
make a move → reach a verdict → see the disposition.

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
                if urllib.request.urlopen(url + "/agon", timeout=2).status == 200:
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
        yield pg
        browser.close()


def test_contest_graphist_witnesses_and_wins(page, app_url):
    page.goto(app_url + "/agon")
    page.wait_for_selector("#btn-contest", state="visible")

    # M: two dogs, one of them good.  G: ∃x (dog(x) ∧ good(x)).  The Graphist can win
    # by witnessing x := Rex (good), so a real choice is surfaced.
    page.fill("#setup-model", '(dog "Biscuit") (dog "Rex") (good "Rex")')
    page.fill("#setup-proposal", "(dog *x) (good x)")
    page.click("#btn-contest")

    # The contest board renders with a contested Graphist frontier (witness options).
    page.wait_for_selector("#interpret-result", state="visible")
    page.wait_for_selector(".contest-opt", state="visible")
    labels = page.locator(".contest-opt").all_inner_texts()
    assert "Rex" in labels and "Biscuit" in labels

    # Pick the winning witness.
    page.click('.contest-opt:has-text("Rex")')

    # The contest reaches a verdict and surfaces the disposition taxonomy.
    page.wait_for_selector('#interpret-result:has-text("Graphist wins")')
    body = page.inner_text("#interpret-result")
    assert "Graphist wins" in body
    assert "x = Rex" in body                       # the selective is recorded
    assert "agonothetes" in body.lower()           # the disposition taxonomy is shown
    assert "Record as conjecture" in body          # a concrete disposition label


def test_contest_concede_hands_inning_to_grapheus(page, app_url):
    page.goto(app_url + "/agon")
    page.wait_for_selector("#btn-contest", state="visible")

    page.fill("#setup-model", '(dog "Biscuit") (dog "Rex") (good "Rex")')
    page.fill("#setup-proposal", "(dog *x) (good x)")
    page.click("#btn-contest")
    page.wait_for_selector("#btn-contest-concede", state="visible")

    page.click("#btn-contest-concede")
    page.wait_for_selector('#interpret-result:has-text("Grapheus wins")')
    assert "you conceded" in page.inner_text("#interpret-result")
