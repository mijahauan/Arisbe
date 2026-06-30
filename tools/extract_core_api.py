#!/usr/bin/env python3
"""Regenerate ``docs/ARISBE_CORE_API_REFERENCE.md`` from the protected-modules set.

The protected-modules list lives in :mod:`tools.core_protection_system` so it
is reused by ``quality_gate_system`` and the protection enforcer. This script
imports it as the single source of truth, then walks each module with the
``inspect`` machinery to emit a markdown reference. The ``Last Generated``
timestamp is anchored to the most recent commit touching any protected module
so that ``python tools/extract_core_api.py`` is idempotent on a fresh checkout.
"""

from __future__ import annotations

import importlib
import inspect
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence

DUNDER_ALLOW = {"__init__", "__post_init__", "__str__", "__repr__"}

USAGE_NOTES = """## Usage Notes

### Import Patterns
```python
# Recommended import style
from module_name import function_name
from module_name import ClassName

# Not: from src.module_name import ...
```

### Immutability
The EGI model is immutable. Use `.with_*()` methods:

```python
# Correct
new_egi = egi.with_vertex(vertex)

# Incorrect
egi.add_vertex(vertex)  # No such method
```

### Error Handling
Check return values and handle ``None`` cases:

```python
result = transform_egi(egi, rule)
if result is None:
    # Handle transformation failure
    pass
```

---

*For usage examples, see [CORE_API_USAGE_GUIDE.md](CORE_API_USAGE_GUIDE.md).*
"""


def load_protected_modules(project_root: Path) -> List[str]:
    """Return the sorted list of protected module names (without ``.py``)."""
    sys.path.insert(0, str(project_root / "tools"))
    from core_protection_system import CoreProtectionSystem

    cps = CoreProtectionSystem(project_root=project_root)
    return sorted(m.removesuffix(".py") for m in cps.protected_modules)


def generation_timestamp(project_root: Path, modules: Sequence[str]) -> str:
    """Last commit ISO-8601 timestamp touching any protected module.

    Falls back to the current UTC time if git is unavailable (e.g. exported
    tarball with no ``.git`` directory).
    """
    paths = [f"src/{m}.py" for m in modules]
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--"] + paths,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        ts = result.stdout.strip()
        if ts:
            return ts
    except FileNotFoundError:
        pass
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _first_line(doc: str | None) -> str:
    if not doc:
        return ""
    return doc.split("\n", 1)[0].strip()


def _signature_str(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(...)"


def _method_emit_filter(name: str) -> bool:
    if not name.startswith("_"):
        return True
    return name in DUNDER_ALLOW


def _document_class(name: str, cls: type) -> List[str]:
    lines: List[str] = [f"#### `{name}`", ""]
    cdoc = inspect.getdoc(cls)
    if cdoc:
        lines.append(cdoc)
        lines.append("")

    methods: List[tuple[str, object]] = []
    for member_name, member in sorted(inspect.getmembers(cls)):
        if not _method_emit_filter(member_name):
            continue
        if not (inspect.isfunction(member) or inspect.ismethod(member)):
            continue
        methods.append((member_name, member))

    if methods:
        lines.append("**Methods**:")
        lines.append("")
        for member_name, member in methods:
            sig = _signature_str(member)
            lines.append(f"- `{member_name}{sig}`")
            summary = _first_line(inspect.getdoc(member))
            if summary:
                lines.append(f"  {summary}")
        lines.append("")
    return lines


def _document_module(module_name: str, src_path: Path) -> tuple[List[str], int, int]:
    """Return (markdown_lines, class_count, function_count) for one module."""
    module = importlib.import_module(module_name)

    lines: List[str] = []
    lines.append(f"## {module_name}.py")
    lines.append("")
    lines.append(f"**Path**: `src/{module_name}.py`  ")
    lines.append("**Status**: Protected Core Module")
    lines.append("")

    mod_doc = inspect.getdoc(module)
    if mod_doc:
        lines.append("### Module Description")
        lines.append("")
        lines.append(mod_doc)
        lines.append("")

    classes = sorted(
        (
            (n, o)
            for n, o in inspect.getmembers(module, inspect.isclass)
            if getattr(o, "__module__", None) == module_name
        ),
        key=lambda pair: pair[0],
    )
    if classes:
        lines.append("### Classes")
        lines.append("")
        for name, cls in classes:
            lines.extend(_document_class(name, cls))

    functions = sorted(
        (
            (n, o)
            for n, o in inspect.getmembers(module, inspect.isfunction)
            if getattr(o, "__module__", None) == module_name and not n.startswith("_")
        ),
        key=lambda pair: pair[0],
    )
    if functions:
        lines.append("### Functions")
        lines.append("")
        for name, fn in functions:
            sig = _signature_str(fn)
            lines.append(f"#### `{name}{sig}`")
            lines.append("")
            fdoc = inspect.getdoc(fn)
            if fdoc:
                lines.append(fdoc)
                lines.append("")

    lines.append("---")
    lines.append("")
    return lines, len(classes), len(functions)


def render(project_root: Path, modules: Sequence[str]) -> tuple[str, int, int]:
    """Render the full document. Returns (markdown, total_classes, total_functions)."""
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))

    timestamp = generation_timestamp(project_root, modules)

    out: List[str] = []
    out.append("# Arisbe Core API Reference")
    out.append("")
    out.append(f"**Last Generated**: {timestamp}  ")
    out.append("**Source of truth**: `tools/core_protection_system.py` (`protected_modules`)  ")
    out.append(f"**Module count**: {len(modules)}")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Overview")
    out.append("")
    out.append(
        "This document provides API documentation for Arisbe's protected core "
        "modules. These modules form the mathematical foundation validated by "
        "the core test suite. Modifying any module listed below requires "
        "explicit authorization (`touch .core_modification_authorized`)."
    )
    out.append("")
    out.append("To regenerate this file, run `python tools/extract_core_api.py`.")
    out.append("")
    out.append("---")
    out.append("")

    # The bulky symbol reference is HTML-only: it bloats the PDF/epub book and is
    # best browsed/searched online. Print/epub get a short pointer instead.
    out.append('::: {.content-hidden when-format="html"}')
    out.append(
        "*The full symbol reference is included in the web/HTML edition only. The "
        "print and epub editions omit it for length — browse and search it in the "
        "HTML book, or read `docs/ARISBE_CORE_API_REFERENCE.md` in the repository.*"
    )
    out.append(":::")
    out.append("")
    out.append('::: {.content-visible when-format="html"}')
    out.append("")

    total_classes = 0
    total_functions = 0
    for module_name in modules:
        module_lines, cc, fc = _document_module(module_name, src_path)
        out.extend(module_lines)
        total_classes += cc
        total_functions += fc

    out.append(USAGE_NOTES)
    out.append("")
    out.append(":::")  # close the HTML-only content block
    return "\n".join(out).rstrip() + "\n", total_classes, total_functions


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    modules = load_protected_modules(project_root)
    markdown, total_classes, total_functions = render(project_root, modules)

    output = project_root / "docs" / "ARISBE_CORE_API_REFERENCE.md"
    output.write_text(markdown, encoding="utf-8")

    print(f"Wrote {output.relative_to(project_root)}")
    print(f"  modules:   {len(modules)}")
    print(f"  classes:   {total_classes}")
    print(f"  functions: {total_functions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
