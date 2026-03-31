from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class JointInfo(BaseModel):
    """Input joint configuration."""

    Number_of_Joints: int = Field(..., ge=2, le=3)
    Material_1: str
    Gauge_1: float = Field(..., gt=0)
    Material_2: str
    Gauge_2: float = Field(..., gt=0)
    Material_3: Optional[str] = None
    Gauge_3: Optional[float] = Field(default=None, gt=0)


class AgentRequest(BaseModel):
    """Top-level agent request schema."""

    request_id: str
    joint_info: JointInfo
