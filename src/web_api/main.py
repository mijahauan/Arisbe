"""
FastAPI application entry point for the Arisbe EGI Web Viewer.

Run with:
    uv run uvicorn src.web_api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Ensure src/ is importable (without the "src." prefix)
_src_dir = Path(__file__).parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from web_api.routes import diagrams, ergasterion, organon, rules, transformations

app = FastAPI(title="Arisbe EGI Viewer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagrams.router)
app.include_router(transformations.router)
app.include_router(organon.router)
app.include_router(ergasterion.router)
app.include_router(rules.router)

# Serve the frontend
viewer_path = Path(__file__).parent.parent / "web_viewer"
if viewer_path.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(viewer_path), html=True),
        name="viewer",
    )
