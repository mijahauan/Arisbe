#!/usr/bin/env python3
"""
Cross-platform styling manager for Arisbe.
- Loads a theme (JSON) that provides semantic style tokens per (type, role, state).
- Exposes a resolve() method to retrieve merged tokens.
- Platform adapters (Qt/TikZ) translate tokens to graphics primitives.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


DEFAULT_THEME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "styles", "default.json")


@dataclass
class StyleQuery:
    type: str
    role: Optional[str] = None
    state: Optional[str] = None


class StyleManager:
    def __init__(self, theme_path: Optional[str] = None):
        self._theme_path = theme_path or os.environ.get("ARISBE_THEME") or os.path.abspath(DEFAULT_THEME_PATH)
        self._theme: Dict[str, Any] = {}
        self._load_theme()

    def _load_theme(self) -> None:
        try:
            with open(self._theme_path, "r", encoding="utf-8") as f:
                self._theme = json.load(f)
        except Exception:
            # minimal safe defaults
            self._theme = {
                "global": {"font_family": "Arial", "font_size": 10},
                "edge.label_box": {"border_color": "#000000", "border_width": 1, "fill_color": "#FFFFFF"},
                "ligature.arm": {"line_color": "#000000", "line_width": 3, "cap": "round"},
                "vertex.dot": {"fill_color": "#000000", "border_color": "#000000", "border_width": 1, "radius": 3},
                "cut.border": {"line_color": "#000000", "line_width": 1, "radius": 10},
                "cut.fill": {"fill_color": "rgba(240,240,240,0.31)"},
            }

    @property
    def theme_path(self) -> str:
        """Return the absolute path to the currently loaded theme JSON."""
        return self._theme_path

    def set_theme_path(self, path: str) -> None:
        """Set a new theme path and load it immediately."""
        if not path:
            return
        self._theme_path = path
        self.reload()

    def resolve(self, *, type: str, role: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """Resolve style tokens using precedence: (type.role.state) > (type.role) > (role) > (type) > global."""
        result: Dict[str, Any] = {}
        # Start with global
        result.update(self._theme.get("global", {}))
        keys_to_try = []
        if role and state:
            keys_to_try.append(f"{role}.{state}")
        if type and role and state:
            keys_to_try.append(f"{type}.{role}.{state}")
        if type and role:
            keys_to_try.append(f"{type}.{role}")
        if role:
            keys_to_try.append(role)
        if type and state:
            keys_to_try.append(f"{type}.{state}")
        if type:
            keys_to_try.append(type)
        # Apply in order; later keys override earlier ones
        for key in keys_to_try:
            tokens = self._theme.get(key)
            if isinstance(tokens, dict):
                result.update(tokens)
        return result

    def reload(self) -> None:
        """Public method to reload the current theme file from disk.
        Safe to call from a file watcher callback. Falls back to defaults on error.
        """
        self._load_theme()


def create_style_manager(theme_path: Optional[str] = None) -> StyleManager:
    return StyleManager(theme_path)
