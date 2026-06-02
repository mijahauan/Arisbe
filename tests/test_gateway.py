"""
Tests for the Arisbe gateway (the root landing page).

The root ``/`` is the environment's front door: an introduction to Arisbe
(Peirce's home; the moving-pictures-of-thought aim) and the triad of modes
— Organon / Ergasterion / Agon — plus the Import doorway.  The former root
viewer is preserved at ``/legacy-viewer.html``.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from web_api import main as web_main


@pytest.fixture
def client():
    return TestClient(web_main.app)


def test_root_serves_gateway(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "Arisbe" in html
    # The triad + the doorway are all linked.
    for href in ("/organon", "/ergasterion", "/agon", "/import"):
        assert f'href="{href}"' in html
    # The house image and the triad framing are present.
    assert "arisbe_house.jpg" in html
    assert "Organon" in html and "Ergasterion" in html and "Agon" in html


def test_house_image_served(client):
    r = client.get("/assets/arisbe_house.jpg")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content[:3] == b"\xff\xd8\xff"  # JPEG magic


def test_legacy_viewer_preserved(client):
    r = client.get("/legacy-viewer.html")
    assert r.status_code == 200
    assert "Existential Graph Viewer" in r.text


def test_mode_routes_have_home_link(client):
    for route in ("/organon", "/ergasterion", "/agon", "/import"):
        r = client.get(route)
        assert r.status_code == 200
        assert "⌂ Arisbe" in r.text
        assert 'href="/"' in r.text
