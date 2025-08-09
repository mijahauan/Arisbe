#!/usr/bin/env python3
"""
EGRF (Existential Graph Rendering Format) specification.

Platform-independent rendering spec produced after layout + post-processing,
faithful to Dau/Peirce conventions and suitable for any GUI/renderer/LaTeX backend.

This is intentionally geometry-first: no layout occurs downstream of EGRF.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import time

Coordinate = Tuple[float, float]
Bounds = Tuple[float, float, float, float]


@dataclass(frozen=True)
class EGRFHeader:
    version: str = "0.1"
    producer: str = "Arisbe"
    timestamp: float = field(default_factory=lambda: time.time())


@dataclass(frozen=True)
class EGRFCut:
    id: str
    bounds: Bounds
    curve_points: Optional[List[Coordinate]] = None
    z: int = 0
    style: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EGRFPredicate:
    id: str  # edge id
    text: str
    position: Coordinate
    bounds: Bounds
    z: int = 10
    style: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EGRFLigatureHook:
    edge_id: str  # predicate edge id this hook attaches to
    at: Coordinate  # exact periphery coordinate
    arg_index: Optional[int] = None  # position in nu sequence (if known)


@dataclass(frozen=True)
class EGRFLigature:
    vertex_id: str
    degree: int
    path: List[Coordinate]  # single continuous heavy line geometry
    hooks: List[EGRFLigatureHook] = field(default_factory=list)
    labels: List[Tuple[str, Coordinate]] = field(default_factory=list)  # constants, etc.
    z: int = 5
    style: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EGRFCanvas:
    width: float
    height: float
    units: str = "pt"
    scale: float = 1.0


@dataclass(frozen=True)
class EGRFDocument:
    header: EGRFHeader
    canvas: EGRFCanvas
    cuts: List[EGRFCut]
    predicates: List[EGRFPredicate]
    ligatures: List[EGRFLigature]
    appearance_overrides: Dict[str, float] = field(default_factory=dict)
    constraints_snapshot: Dict[str, float] = field(default_factory=dict)


# Basic validator (lightweight)
def validate_egrf(doc: EGRFDocument) -> None:
    if not doc.cuts and not doc.predicates and not doc.ligatures:
        raise ValueError("EGRFDocument is empty")
    # Ensure IDs exist
    pred_ids = {p.id for p in doc.predicates}
    for lig in doc.ligatures:
        if not lig.path or len(lig.path) < 2:
            raise ValueError(f"Ligature {lig.vertex_id} has invalid path")
        for hk in lig.hooks:
            if hk.edge_id not in pred_ids:
                raise ValueError(f"Ligature hook edge_id {hk.edge_id} not in predicates")
