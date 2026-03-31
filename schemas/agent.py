from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class RankedResult(BaseModel):
    Rivet: str
    Die: str


class CandidateEvaluation(BaseModel):
    Material_1: str
    Gauge_1: float
    Material_2: str
    Gauge_2: float
    Material_3: Optional[str] = None
    Gauge_3: Optional[float] = None
    Rivet: str
    Die: str
    interlock: float
    bottomthickness: float
    rivetforce: float


class AgentResponse(BaseModel):
    request_id: str
    best_result: Optional[RankedResult] = None
    ranked_results: list[RankedResult]
    decision_trace: list[dict[str, Any]]
    proposal_summary: str
    risks: list[str]
    human_checkpoints: list[str]
    alternative_comparison: list[str]
    llm_enabled: bool
    llm_status: str
