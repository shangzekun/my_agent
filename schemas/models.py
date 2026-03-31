from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MaterialFeaturesInput(BaseModel):
    Number_of_Joints: int
    Material_1_ts: float
    Gauge_1: float
    Material_2_ts: float
    Gauge_2: float
    Material_3_ts: Optional[float] = None
    Gauge_3: Optional[float] = None


class Candidate(BaseModel):
    Rivet: str
    Die: str


class CandidateOutput(BaseModel):
    candidates: list[Candidate]


class QualityPredictionInput(MaterialFeaturesInput):
    Rivet: str
    Die: str


class QualityPredictionOutput(BaseModel):
    interlock: float
    bottomthickness: float
    rivetforce: float


class SimulationExecutionInput(BaseModel):
    Number_of_Joints: int
    Material_1: str
    Gauge_1: float
    Material_2: str
    Gauge_2: float
    Material_3: Optional[str] = None
    Gauge_3: Optional[float] = None
    Rivet: str
    Die: str


class SimulationExecutionOutput(BaseModel):
    headheight: float
    interlock: float
    bottomthickness: float
