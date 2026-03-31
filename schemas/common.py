from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HistoryQueryInput(BaseModel):
    """Shared query input for process/simulation history."""

    Number_of_Joints: int = Field(..., ge=2, le=3)
    Material_1: str
    Gauge_1: float
    Material_2: str
    Gauge_2: float
    Material_3: Optional[str] = None
    Gauge_3: Optional[float] = None


class HistoryInfo(BaseModel):
    Material_1: str
    Gauge_1: float
    Material_2: str
    Gauge_2: float
    Material_3: Optional[str] = None
    Gauge_3: Optional[float] = None
    Rivet: str
    Die: str


class HistoryQueryOutput(BaseModel):
    is_true: str
    history_info: list[HistoryInfo]
