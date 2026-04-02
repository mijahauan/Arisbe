"""
Pydantic request/response models for the Arisbe Web API.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class TransformApplyRequest(BaseModel):
    session_id: str
    rule: str  # "ERA" | "INS" | "IT+" | "IT-" | "DC+" | "DC-"
    parameters: Dict[str, Any]  # rule-specific


class TransformValidateRequest(BaseModel):
    session_id: str
    rule: str
    parameters: Dict[str, Any]


class SubgraphValidateRequest(BaseModel):
    session_id: str
    selected_elements: List[str]
    context_area: Optional[str] = None


class AreaAtPointRequest(BaseModel):
    session_id: str
    x: float
    y: float


class UndoRedoRequest(BaseModel):
    session_id: str
