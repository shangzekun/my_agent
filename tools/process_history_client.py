from __future__ import annotations

from schemas.common import HistoryInfo, HistoryQueryInput, HistoryQueryOutput


class ProcessHistoryClient:
    """Mock process history DB query client."""

    def query_process_history(self, payload: HistoryQueryInput) -> HistoryQueryOutput:
        """Tool entry that delegates to temporary mock implementation."""

        return self.temporary(payload)

    def temporary(self, payload: HistoryQueryInput) -> HistoryQueryOutput:
        """Temporary mock function to simulate process history query output."""

        if payload.Material_1 == "DP590" and payload.Material_2 == "AL6061":
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
        return HistoryQueryOutput(is_true="No", history_info=[])
