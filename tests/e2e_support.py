"""Shared browser guard for the end-to-end suites.

``pytest.importorskip("playwright")`` tests for the *package*, which this
project installs as a dev dependency; it does not test for the *browser
binary*, which it does not install. On a machine without the binary — a fresh
clone, or CI without the extra step — every end-to-end test then dies inside
``chromium.launch()`` as an ERROR rather than skipping. An errored test never
runs its teardown, so a suite that spawns uvicorn also leaks the server.

Probing the binary by path does not work either: ``chromium.executable_path``
names the full Chromium build, but ``chromium.launch()`` is satisfied by the
much smaller ``chromium-headless-shell``. A machine can have a working
launcher and a nonexistent ``executable_path``. The only honest probe is to
launch once and see.

Call :func:`require_browser` at module scope in place of the bare
``importorskip``.
"""

from __future__ import annotations

import pytest

_LAUNCHABLE: bool | None = None
_REASON = ""


def browser_available() -> tuple[bool, str]:
    """Return ``(launchable, reason)``, launching at most once per session."""
    global _LAUNCHABLE, _REASON
    if _LAUNCHABLE is not None:
        return _LAUNCHABLE, _REASON
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # package absent
        _LAUNCHABLE, _REASON = False, f"playwright package not installed ({exc})"
        return _LAUNCHABLE, _REASON
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
    except Exception as exc:
        first = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
        _LAUNCHABLE, _REASON = False, (
            f"chromium cannot launch ({first}); "
            "run: uv run playwright install chromium-headless-shell"
        )
        return _LAUNCHABLE, _REASON
    _LAUNCHABLE, _REASON = True, ""
    return _LAUNCHABLE, _REASON


def require_browser() -> None:
    """Skip the whole module — cleanly — when no browser can be launched."""
    ok, reason = browser_available()
    if not ok:
        pytest.skip(reason, allow_module_level=True)
