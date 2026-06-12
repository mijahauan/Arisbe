"""End-to-end browser test of freeform *challenge mode* (freeform step 4).

Drives the real page in a headless Chromium: enter the freeform canvas, pick a
target from the challenge picker, and grade a drawing — both the ill-formed path
(an empty canvas → validity feedback, not a grade) and the success path (draw the
one-relation target freehand → graded a match via same_graph + the legible diff).
This closes the gap the non-browser route tests can't: that the challenge
picker→prompt→grade wiring and the freeform grade button actually work in a browser.

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


def _dispatch_dialog(dialog):
    """The freeform canvas prompts for relation / constant names; answer each by
    the prompt's own message so the one-relation target draws as (man "Socrates")."""
    msg = dialog.message
    if "Relation name" in msg:
        dialog.accept("man")
    elif "Constant name" in msg:
        dialog.accept("Socrates")
    else:
        dialog.accept()


@pytest.fixture
def page(app_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg.on("dialog", _dispatch_dialog)
        yield pg
        browser.close()


def _enter_freeform_with_challenge(page, app_url):
    """Start an empty composition, open the freeform canvas, and wait for the
    challenge picker to populate from /ergasterion/challenges."""
    page.goto(app_url + "/ergasterion")
    page.click("#btn-start-empty")
    page.wait_for_selector("#workspace-switch", state="visible")
    page.click("#btn-freeform-toggle")
    page.wait_for_selector("#freeform-tools", state="visible")
    page.wait_for_function(
        "document.querySelectorAll('#challenge-select option').length > 1",
        timeout=10000)


def _click_canvas(page, frac_x, frac_y):
    box = page.locator("#canvas").bounding_box()
    page.mouse.click(box["x"] + box["width"] * frac_x,
                     box["y"] + box["height"] * frac_y)


def test_challenge_picker_prompt_and_grade_of_empty_shows_legible_diff(page, app_url):
    """The challenge wiring, deterministically: the picker populates, choosing the
    one-relation target shows its prompt and enables grading, and grading an empty
    canvas (a well-formed but empty graph) reports the *legible diff* in EG
    vocabulary — it is missing the target's individual and relation — exercising
    the whole picker→prompt→grade-endpoint→render path without a fragile drawing."""
    _enter_freeform_with_challenge(page, app_url)

    page.select_option("#challenge-select", "one-relation")
    page.wait_for_function(
        "document.querySelector('#challenge-prompt').textContent.includes('man')",
        timeout=8000)
    assert "Socrates" in page.text_content("#challenge-prompt")
    assert not page.is_disabled("#btn-grade-challenge")

    # Grade with nothing drawn → an empty graph that differs from the target; the
    # panel shows the legible diff (the target's missing relation/individual).
    page.click("#btn-grade-challenge")
    page.wait_for_function(
        "document.querySelector('#challenge-result').textContent.trim().length > 0",
        timeout=10000)
    txt = page.text_content("#challenge-result").lower()
    assert "missing" in txt and "man" in txt


def test_challenge_correct_drawing_grades_as_match(page, app_url):
    """The success path: draw the one-relation target (man "Socrates") freehand —
    a 'man' spot wired to a 'Socrates' constant — and grading reports a match
    (same_graph, regardless of surface placement)."""
    _enter_freeform_with_challenge(page, app_url)
    page.select_option("#challenge-select", "one-relation")
    page.wait_for_function(
        "document.querySelector('#challenge-prompt').textContent.includes('man')",
        timeout=8000)

    # Place the 'man' relation spot and the 'Socrates' constant (dialogs answered
    # by _dispatch_dialog), then wire predicate→constant.
    page.click('#freeform-tools [data-fftool="predicate"]')
    _click_canvas(page, 0.5, 0.35)
    page.click('#freeform-tools [data-fftool="constant"]')
    _click_canvas(page, 0.5, 0.7)
    page.click('#freeform-tools [data-fftool="line"]')
    _click_canvas(page, 0.5, 0.35)
    _click_canvas(page, 0.5, 0.7)

    page.click("#btn-grade-challenge")
    page.wait_for_function(
        "document.querySelector('#challenge-result').textContent.trim().length > 0",
        timeout=10000)
    txt = page.text_content("#challenge-result")
    assert "Correct" in txt, f"expected a match, got: {txt}"
