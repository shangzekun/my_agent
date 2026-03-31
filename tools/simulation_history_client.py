from __future__ import annotations

from schemas.common import HistoryInfo, HistoryQueryInput, HistoryQueryOutput


class SimulationHistoryClient:
    """Mock simulation history DB query client."""

    def query_simulation_history(self, payload: HistoryQueryInput) -> HistoryQueryOutput:
        """Tool entry that delegates to temporary mock implementation."""

        return self.temporary(payload)

    def temporary(self, payload: HistoryQueryInput) -> HistoryQueryOutput:
        """Temporary mock function to simulate simulation-history query output."""

        # Mock: one historical pair exists regardless of current request.
        return HistoryQueryOutput(
            is_true="Yes",
            history_info=[
                HistoryInfo(
                    Material_1=payload.Material_1,
                    Gauge_1=payload.Gauge_1,
                    Material_2=payload.Material_2,
                    Gauge_2=payload.Gauge_2,
                    Material_3=payload.Material_3,
                    Gauge_3=payload.Gauge_3,
                    Rivet="RVT-5.3",
                    Die="DIE-A",
                )
            ],
        )
