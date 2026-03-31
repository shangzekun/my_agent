from __future__ import annotations

from schemas.models import QualityPredictionInput, QualityPredictionOutput


class QualityPredictorClient:
    """Mock quality prediction model client."""

    def predict_quality(self, payload: QualityPredictionInput) -> QualityPredictionOutput:
        """Tool entry that delegates to temporary mock implementation."""

        return self.temporary(payload)

    def temporary(self, payload: QualityPredictionInput) -> QualityPredictionOutput:
        """Temporary mock function to simulate quality model output."""

        base = 0.3 + payload.Material_1_ts / 3000.0 + payload.Material_2_ts / 4000.0
        die_bonus = 0.05 if payload.Die in {"DIE-A", "DIE-B"} else 0.0
        interlock = round(base + die_bonus, 3)
        bottomthickness = round(0.2 + (payload.Gauge_1 + payload.Gauge_2) / 10.0, 3)
        rivetforce = round(30 + payload.Material_1_ts / 50 + (2 if payload.Rivet.endswith("5") else 0), 3)
        return QualityPredictionOutput(
            interlock=interlock,
            bottomthickness=bottomthickness,
            rivetforce=rivetforce,
        )
