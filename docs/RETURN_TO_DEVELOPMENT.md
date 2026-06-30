# Returning to Arisbe Development

For when you've been away for weeks or months and need to recover context quickly.
This supersedes the five context-recovery documents that previously lived under
`docs/context/` (consolidated 2026-05-29).

## In 5 minutes

```bash
# 1. Re-anchor on the code
cat CLAUDE.md          # ground-truth dev guide (~150 lines)
cat README.md          # what + how to run
cat docs/VISION_AND_SCOPE.md  # why + philosophy

# 2. Confirm system health
uv run pytest tests/ -q
uv run python tools/core_protection_system.py --report

# 3. See recent work
git log --oneline -20
```

If those three steps produce a green test suite, a CLEAN protection report, and a
git log that you can follow — you have enough context to start working. The next
sections are only needed if something looks wrong. The active task handoff is
always [CURRENT_PLAN.md](../CURRENT_PLAN.md)'s `▶ NEXT SESSION` section.

## What is Arisbe

A Python 3.12 implementation of Dau's formalization of Peirce's Existential
Graphs. The core entity is not a static EGI diagram but the **Universe of
Discourse** (UoD) — the evolving diachronic process of which a single EGI is one
synchronic frame. See [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) for the longer
philosophical statement and [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md)
for how the model expresses it.

## Layout and conventions you must not forget

- **EGI is immutable.** Use `.with_vertex()`, `.with_edge()`. Never `.add_*()`.
- **Imports**: `from module_name import Foo`, not `from src.module_name`.
- **UoD state** = `(EGI, LayoutDeltas)`. Deltas persist through transformations.
- **Beta graphs** use shared vertices across cut boundaries. In EGIF, `*x` =
  defining label (new vertex), `x` = bound label (existing vertex in enclosing
  scope). `~[ (P *x) ~[ (Q x) ] ]` = ∀x(P(x) → Q(x)) with one shared vertex.
- **Protected modules** (17, listed in `tools/core_protection_system.py`) need
  `touch .core_modification_authorized` before modification.

## Where things live (post-2026-05 cleanup)

- `src/` — core modules (~32 .py files plus `web_api/` and `web_viewer/`).
- `tests/` — pytest suite (~955 passing, 35 skipped).
- `tools/` — quality tools, demos, utilities (not in import path for tests).
- `tomos/` — 87+ canonical EG examples (Peirce, Roberts, Sowa, Dau).
- `corpus/` — active working corpus.
- `docs/` — architecture and reference docs.
- `archive/qt-gui-2025/` — Qt desktop GUI and D3 layout engine, archived
  May 2026 in favor of the web viewer. See its README for context.

## Discovering the API

The auto-generated [docs/ARISBE_CORE_API_REFERENCE.md](ARISBE_CORE_API_REFERENCE.md)
covers every module in the protected-modules set. Regenerate it after
touching any protected module:

```bash
uv run python tools/extract_core_api.py

# Find a function or class by name
grep -rn "def foo\|class Foo" src/

# List exported names in a module
uv run python -c "import egi_core_dau; print([n for n in dir(egi_core_dau) if not n.startswith('_')])"
```

The top-of-file docstrings in `src/*.py` are kept current and are the best
entry point for understanding any one module.

## Known follow-ups (don't re-discover these)

- **Rule-reversibility and closure-idempotence property tests** are still
  to be written (carried forward from issue #4 into issue #8).
- **CI runs only a subset of the test suite** (see `.github/workflows/canonical.yml`).
  Full-suite-on-CI is a Phase 4 item.
- **Three-mode UI (Organon/Ergasterion/Agon) is live** as web routes
  (`/organon`, `/ergasterion`, `/agon`; Agon shipped as a thin V1 arena
  2026-06-01). The next frontier is deepening Agon — the Endoporeutic Game end
  game (see `docs/ENDOPOREUTIC_GAME_GUIDE.md`).

## If you are an AI assistant

Run the 5-minute checklist above before answering any question that depends on
project state. Trust the live `pytest` and `git log` output over anything you
remember from a previous session — both this codebase and the documentation
under it have shifted multiple times during AI-assisted development.
