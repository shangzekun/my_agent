from __future__ import annotations

from schemas.agent import CandidateEvaluation, RankedResult


class SchemeRanker:
    """Sort candidate schemes by quality indicators."""

    def rank_schemes(self, schemes: list[CandidateEvaluation]) -> list[RankedResult]:
        ranked = sorted(
            schemes,
            key=lambda item: (
                -item.interlock,
                -item.bottomthickness,
                item.rivetforce,
            ),
        )
        return [RankedResult(Rivet=item.Rivet, Die=item.Die) for item in ranked]
