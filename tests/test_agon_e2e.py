"""End-to-end browser test of the /agon interpretation register (the inning
*given M, then G*).

Unlike the route tests (which post JSON to /agon/interpret directly), this drives
the *real* page in a headless Chromium: pick a reference model M from the picker,
type a proposal G, toggle the materialize/closed switches, and click the buttons —
then assert the rendered panel shows the right verdict, the deduction ("Theorem of
M?") block, and the inverse-pivot search.  This closes the gap the non-browser
tests can't: that the picker→interpret→theorem flow is actually wired end to end.

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


def _interpret_text_containing(page, needle):
    """Wait until the interpretation panel shows ``needle`` and return its text.

    Each scenario waits for content that distinguishes *its own* result (the
    model EGIF it carries), so a stale panel from a prior interpret can never be
    mistaken for this one.
    """
    page.wait_for_selector("#interpret-result", state="visible", timeout=10000)
    page.wait_for_function(
        "n => document.querySelector('#interpret-result').textContent.includes(n)",
        arg=needle, timeout=10000)
    return page.text_content("#interpret-result")


def test_interpret_teacher_is_true(page, app_url):
    """Pick the teacher's closed zoology and 'Does G hold in M?' → TRUE: every
    mammal in the closed world is warm-blooded, so the Proposer wins."""
    page.goto(app_url + "/agon")
    page.wait_for_function(
        "document.querySelectorAll('#model-picker option').length > 1", timeout=10000)
    page.select_option("#model-picker", "ex:teacher-mammals")
    assert page.input_value("#setup-proposal").strip(), "picker should fill a sample G"
    page.click("#btn-interpret")
    txt = _interpret_text_containing(page, "mammal")  # the teacher's own model
    assert "TRUE" in txt


def test_interpret_student_is_false_with_counterexample(page, app_url):
    """The student's sea-creatures: 'all sea creatures are cold-blooded' is refuted
    by Whale → FALSE, and the panel names the counterexample."""
    page.goto(app_url + "/agon")
    page.wait_for_function(
        "document.querySelectorAll('#model-picker option').length > 1", timeout=10000)
    page.select_option("#model-picker", "ex:student-sea")
    page.click("#btn-interpret")
    txt = _interpret_text_containing(page, "seacreature")  # the student's own model
    assert "FALSE" in txt
    assert "Counterexample" in txt


def test_theorem_block_appears_with_materialize(page, app_url):
    """Type a model carrying a *rule* (man ⊑ mortal) plus a fact, tick 'Use rules',
    and the deduction block renders beside the extensional peel: 'Theorem of M?'
    reads TRUE (freeze a fresh witness, materialize, the head derives) even though
    the open-world extensional peel is UNKNOWN."""
    page.goto(app_url + "/agon")
    page.fill("#setup-model", '(man "Socrates") ~[ (man *x) ~[ (mortal x) ] ]')
    page.fill("#setup-proposal", '~[ (man *x) ~[ (mortal x) ] ]')
    page.check("#model-materialize")
    page.click("#btn-interpret")
    txt = _interpret_text_containing(page, "Theorem of M? (deduction)")
    # The deduction block is present and affirmative.
    assert "TRUE" in txt
    # And it shows the freeze-a-witness body ⊢ head.
    assert "freeze a fresh witness" in txt


def test_inverse_pivot_searches_models(page, app_url):
    """Type a proposal and click 'Where does G hold?' — the inverse pivot runs the
    peel across every candidate model and paints the ranked holds/partial/
    independent/contradicts tally."""
    page.goto(app_url + "/agon")
    page.fill("#setup-proposal", '~[ (mammal *x) ~[ (warmblooded x) ] ]')
    page.click("#btn-inverse")
    page.wait_for_selector("#interpret-result", state="visible", timeout=15000)
    page.wait_for_function(
        "document.querySelector('#interpret-result').textContent"
        ".includes('In what domain does G hold')",
        timeout=15000)
    txt = page.text_content("#interpret-result")
    assert "holds" in txt and "contradicts" in txt
