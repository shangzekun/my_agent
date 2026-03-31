from __future__ import annotations

from schemas.models import Candidate, CandidateOutput, MaterialFeaturesInput


class RivetDieSelectorClient:
    """Mock rivet-die candidate model client."""

    def select_candidates(self, payload: MaterialFeaturesInput) -> CandidateOutput:
        """Tool entry that delegates to temporary mock implementation."""

        return self.temporary(payload)

    def temporary(self, payload: MaterialFeaturesInput) -> CandidateOutput:
        """Temporary mock function to simulate candidate model output."""

        if payload.Material_1_ts > 500:
            return CandidateOutput(
                candidates=[
                    Candidate(Rivet="RVT-5.3", Die="DIE-A"),
                    Candidate(Rivet="RVT-5.5", Die="DIE-B"),
                    Candidate(Rivet="RVT-6.0", Die="DIE-C"),
                ]
            )
        return CandidateOutput(candidates=[Candidate(Rivet="RVT-4.8", Die="DIE-S")])
