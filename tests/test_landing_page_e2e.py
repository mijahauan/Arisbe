"""The front door: can a visitor arriving at ``/`` actually reach the modes?

Every other end-to-end suite enters a mode by direct URL, so none of them can
fail when the gateway itself is unusable. That gap let a real defect stand: the
gateway inherited ``--canvas-bg`` (white, correct for a *diagram*) as its page
ground while keeping light text, and inherited ``html,body{overflow:hidden}``
from the mode shells, which clipped the page at the fold. At 1440x896 the
Organon, Ergasterion and Agon cards sat at y=930 and could not be scrolled to.

These tests assert the two properties that failure violated: the doors are
reachable, and the text is legible against its background.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from e2e_support import require_browser

require_browser()
from playwright.sync_api import sync_playwright  # noqa: E402

REPO = Path(__file__).parent.parent
MODES = ("organon", "ergasterion", "agon")

# WCAG 2.1 body-text minimum. The gateway's own palette clears this
# comfortably; the threshold is here to catch a token regression, not to grade
# the design.
MIN_CONTRAST = 4.5


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
                if urllib.request.urlopen(url + "/", timeout=2).status == 200:
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


def _rel_luminance(rgb):
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _parse_rgb(s):
    nums = [int(n) for n in __import__("re").findall(r"\d+", s)[:3]]
    return tuple(nums)


def _contrast(fg, bg):
    l1, l2 = sorted((_rel_luminance(fg), _rel_luminance(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


@pytest.fixture
def page(app_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1440, "height": 896})
        pg.goto(app_url + "/", wait_until="networkidle")
        yield pg
        browser.close()


def test_every_mode_door_is_reachable(page):
    """Each of the three modes can be brought into view *the way a user would*.

    Deliberately not ``scroll_into_view_if_needed``: Playwright scrolls
    programmatically and succeeds even on a page pinned with
    ``overflow:hidden``, which is exactly the defect this guards. Scroll the
    window as a person would, then ask whether the door is inside the viewport.
    """
    vh = page.evaluate("() => window.innerHeight")
    for mode in MODES:
        link = page.locator(f'a[href*="{mode}"]').first
        assert link.count() > 0, f"no link to /{mode} on the gateway"

        page.evaluate("() => window.scrollTo(0, 0)")
        top_unscrolled = link.bounding_box()["y"]
        if top_unscrolled >= vh:
            # Below the fold: a user must scroll. Try, as a user would.
            page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
            page.wait_for_timeout(100)
        box = link.bounding_box()
        assert box is not None and box["height"] > 0, f"the {mode} door has no box"
        assert 0 <= box["y"] < vh, (
            f"the {mode} door sits at y={box['y']:.0f} with a {vh}px viewport and "
            f"cannot be scrolled into view — a visitor cannot reach it"
        )
        assert link.is_visible(), f"the {mode} door is not visible"


def test_page_scrolls_when_content_exceeds_the_fold(page):
    """A gateway taller than the viewport must scroll; overflow:hidden clipped it."""
    m = page.evaluate(
        "() => ({vh: window.innerHeight, ch: document.documentElement.scrollHeight})"
    )
    if m["ch"] <= m["vh"] + 1:
        pytest.skip("gateway fits the viewport; nothing to scroll")
    page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
    assert page.evaluate("() => window.scrollY") > 0, (
        "the gateway is taller than the viewport but will not scroll — "
        "content below the fold is unreachable"
    )


def test_body_text_is_legible_against_its_background(page):
    """The gateway must not paint light text on the white diagram canvas."""
    fg, bg = page.evaluate(
        "() => { const cs = getComputedStyle(document.body); return [cs.color, cs.backgroundColor]; }"
    )
    ratio = _contrast(_parse_rgb(fg), _parse_rgb(bg))
    assert ratio >= MIN_CONTRAST, (
        f"gateway body text {fg} on {bg} is {ratio:.2f}:1, below {MIN_CONTRAST}:1"
    )
