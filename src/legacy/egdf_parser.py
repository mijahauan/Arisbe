from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import yaml


# ----- Typed schemas -----

class AlphabetDAUSchema(TypedDict, total=False):
    C: List[str]
    F: List[str]
    R: List[str]
    ar: Dict[str, int]


class EGIInlineSchema(TypedDict):
    sheet: str
    V: List[str]
    E: List[str]
    Cut: List[str]
    nu: Dict[str, List[str]]
    rel: Dict[str, str]
    area: Dict[str, List[str]]
    rho: Dict[str, Optional[str]]
    alphabet: AlphabetDAUSchema


class EGIRefSchema(TypedDict, total=False):
    hash: str
    inline: EGIInlineSchema
    uri: str  # optional external reference


class EGDFHeader(TypedDict):
    version: str
    generator: str
    created: str


class CutLayout(TypedDict):
    x: float
    y: float
    w: float
    h: float


class VertexLayout(TypedDict, total=False):
    x: float
    y: float
    label_anchor: Tuple[float, float]


class PredicateLayout(TypedDict):
    text: str
    x: float
    y: float
    w: float
    h: float


class LigaturePath(TypedDict):
    kind: str  # "spline" | "polyline"
    points: List[Tuple[float, float]]


class LigatureLayout(TypedDict, total=False):
    area: str
    path: LigaturePath


class LayoutSection(TypedDict, total=False):
    units: str
    cuts: Dict[str, CutLayout]
    vertices: Dict[str, VertexLayout]
    predicates: Dict[str, PredicateLayout]
    ligatures: Dict[str, LigatureLayout]


class StyleRule(TypedDict, total=False):
    select: str
    stroke: Dict[str, Any]
    fill: Dict[str, Any]
    text: Dict[str, Any]


class StylesSection(TypedDict, total=False):
    imports: List[str]
    variables: Dict[str, Any]
    rules: List[StyleRule]


class DeltaTranslate(TypedDict):
    op: str
    id: str
    dx: float
    dy: float
    by: str
    at: str


class DeltaRoute(TypedDict):
    op: str
    edge_id: str
    waypoints: List[Tuple[float, float]]


Delta = Dict[str, Any]


class EGDFSchema(TypedDict, total=False):
    egdf: EGDFHeader
    egi_ref: EGIRefSchema
    layout: LayoutSection
    styles: StylesSection
    deltas: List[Delta]


# ----- Dataclass wrapper -----

@dataclass
class EGDFDocument:
    header: EGDFHeader
    egi_ref: EGIRefSchema
    layout: LayoutSection = field(default_factory=dict)
    styles: StylesSection = field(default_factory=dict)
    deltas: List[Delta] = field(default_factory=list)

    @staticmethod
    def compute_egi_hash(egi_inline: EGIInlineSchema) -> str:
        # Stable canonical JSON for hashing
        blob = json.dumps(egi_inline, sort_keys=True, separators=(",", ":")).encode("utf-8")
        h = hashlib.sha256(blob).hexdigest()
        return f"sha256:{h}"

    def validate(self) -> None:
        # Header
        if "version" not in self.header:
            raise ValueError("EGDF header.version required")
        # EGI reference
        if "inline" not in self.egi_ref and "uri" not in self.egi_ref:
            raise ValueError("egi_ref requires either inline or uri")
        if "inline" in self.egi_ref:
            inline = self.egi_ref["inline"]
            # Basic EGI keys
            for key in ("sheet", "V", "E", "Cut", "nu", "rel", "area", "rho", "alphabet"):
                if key not in inline:
                    raise ValueError(f"egi_ref.inline.{key} is required")
            # Compute/verify hash
            expected = EGDFDocument.compute_egi_hash(inline)
            if self.egi_ref.get("hash") and self.egi_ref["hash"] != expected:
                raise ValueError("egi_ref.hash does not match inline content")
            self.egi_ref["hash"] = expected
        # Layout sanity
        units = self.layout.get("units", "pt")
        if units not in ("pt", "px", "mm", "cm", "in"):
            raise ValueError("layout.units must be one of pt|px|mm|cm|in")

    def to_dict(self) -> EGDFSchema:
        self.validate()
        return {
            "egdf": self.header,
            "egi_ref": self.egi_ref,
            "layout": self.layout,
            "styles": self.styles,
            "deltas": self.deltas,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False)

    @staticmethod
    def from_dict(data: EGDFSchema) -> "EGDFDocument":
        header = data.get("egdf", {"version": "0.1", "generator": "arisbe", "created": ""})
        egi_ref = data.get("egi_ref", {})  # type: ignore[assignment]
        layout = data.get("layout", {})  # type: ignore[assignment]
        styles = data.get("styles", {})  # type: ignore[assignment]
        deltas = data.get("deltas", [])  # type: ignore[assignment]
        doc = EGDFDocument(header=header, egi_ref=egi_ref, layout=layout, styles=styles, deltas=deltas)
        doc.validate()
        return doc

    @staticmethod
    def from_json(text: str) -> "EGDFDocument":
        return EGDFDocument.from_dict(json.loads(text))

    @staticmethod
    def from_yaml(text: str) -> "EGDFDocument":
        return EGDFDocument.from_dict(yaml.safe_load(text))
