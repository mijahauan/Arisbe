# Archived: Qt/PySide6 GUI (2025)

This directory archives the Qt-based desktop GUI work from 2025 (and the
`unified_d3` layout engine that powered it). It was moved here on 2026-05-29
during the May 2026 review (see `/Users/mjh/.claude/plans/arisbe-in-its-current-sprightly-stream.md`).

## Why archived

- The most recent six months of active development (Oct 2025 → Apr 2026) shifted
  to a web-based viewer (`src/web_api/`, `src/web_viewer/`, `src/elk_layout_engine.py`).
- The Qt GUI was incomplete: Organon ~40%, Ergasterion untested, Agon a placeholder.
- Maintaining two parallel render paths (D3 simulation vs ELK constraint-based)
  with duplicated styling and overlapping responsibilities created confusion
  about which was canonical.

## What's here

- `arisbe.py` — top-level Qt entry point
- `src/arisbe_home.py` — Qt home / launcher window
- `src/gui_clean/` — Qt Organon / Ergasterion / (placeholder Agon) modes,
  diagram canvases, dialogs
- `src/diagram_controller.py` — Command-pattern controller bridging core to Qt UI
- `src/unified_d3_engine.py`, `src/unified_d3_worker.js` — D3 force-simulation
  layout engine
- `src/insertion_clipboard.py` — GUI insertion-clipboard state (only used by gui_clean)
- `src/controller/constraint_engine.py` — Qt-coupled constraint engine
- `src/export/` — TikZ exporter using D3 LayoutDTO (tikz_exporter.py was broken
  on a missing `styling` package; dto_to_tikz_adapter.py had only Qt users)
- `src/agon/` — empty placeholder directory
- `tools/test_gui_organon.py`, `tools/test_diagram_controller.py`,
  `tools/test_history_timeline.py`, `tools/test_organon_metadata.py`,
  `tools/test_boundary_clearance.py`, `tools/test_position_persistence.py` —
  Qt-coupled test scripts (manual `print`-style, not pytest)

## Restoring

`git log --diff-filter=R -- src/gui_clean/` and similar reveal these moves.
To bring a file back:
```
git mv archive/qt-gui-2025/src/<file> src/<file>
```
Then update CLAUDE.md, AGENTS.md and re-add it to the core protection list if
appropriate.

## What replaced it

- Layout: `src/elk_layout_engine.py` (ELK constraint-based, cut-aware ligature
  routing) → produces `LayoutDTO`.
- Render: `src/simple_svg_renderer.py` → emits SVG from `LayoutDTO`.
- Interface: `src/web_api/` (FastAPI) + `src/web_viewer/` (static HTML/CSS/JS).
- The conceptual triad **Organon / Ergasterion / Agon** remains but is now
  best understood as *modes within the web app* rather than separate Qt
  windows. Implementation of that mapping is still ahead (see Phase 5 of the
  May 2026 plan).
