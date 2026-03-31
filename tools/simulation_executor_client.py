from __future__ import annotations

from schemas.models import SimulationExecutionInput, SimulationExecutionOutput


class SimulationExecutorClient:
    """Mock simulation execution client."""

    def run_simulation(self, payload: SimulationExecutionInput) -> SimulationExecutionOutput:
        """Tool entry that delegates to temporary mock implementation."""

        return self.temporary(payload)

    def temporary(self, payload: SimulationExecutionInput) -> SimulationExecutionOutput:
        """Temporary mock function to simulate simulation execution output."""

        return SimulationExecutionOutput(
            headheight=round(0.15 + payload.Gauge_1 / 20.0, 3),
            interlock=round(0.4 + payload.Gauge_2 / 20.0, 3),
            bottomthickness=round(0.25 + (payload.Gauge_1 + payload.Gauge_2) / 20.0, 3),
        )
