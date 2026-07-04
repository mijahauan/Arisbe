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

from web_api.routes import agon, diagrams, ergasterion, export, imports, introspect, organon, primer, rules, styles, transformations

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
app.include_router(introspect.router)
app.include_router(primer.router)
app.include_router(agon.router)
app.include_router(imports.router)
app.include_router(styles.router)
app.include_router(export.router)

# Serve the rendered book/help, if it has been built (quarto render docs/book).
# Mounted before the catch-all "/" so /book/ wins. Absent until rendered — that's fine.
book_path = Path(__file__).parent.parent.parent / "docs" / "_book"
if book_path.exists():
    # Registered BEFORE the mount so the exact path /book (which the mount would 404)
    # redirects to /book/ — the UI links use /book/, but a hand-typed address
    # shouldn't dead-end.
    @app.get("/book", include_in_schema=False)
    def _book_slash_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/book/")

    app.mount(
        "/book",
        StaticFiles(directory=str(book_path), html=True),
        name="book",
    )

# Serve the frontend
viewer_path = Path(__file__).parent.parent / "web_viewer"
if viewer_path.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(viewer_path), html=True),
        name="viewer",
    )
