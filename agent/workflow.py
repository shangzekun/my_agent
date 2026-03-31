from __future__ import annotations

from schemas import (
    AgentRequest,
    AgentResponse,
    CandidateEvaluation,
    HistoryQueryInput,
    QualityPredictionInput,
    SimulationExecutionInput,
)
from tools import (
    MaterialMapper,
    ProcessHistoryClient,
    QualityPredictorClient,
    RivetDieSelectorClient,
    SimulationExecutorClient,
    SimulationHistoryClient,
)

from agent.ranker import SchemeRanker


class SPRProcessAgent:
    """Fixed-step SPR process development workflow agent."""

    def __init__(self) -> None:
        self.material_mapper = MaterialMapper()
        self.process_history_client = ProcessHistoryClient()
        self.selector_client = RivetDieSelectorClient()
        self.quality_client = QualityPredictorClient()
        self.simulation_history_client = SimulationHistoryClient()
        self.simulation_executor_client = SimulationExecutorClient()
        self.ranker = SchemeRanker()

    def run(self, request: AgentRequest) -> AgentResponse:
        trace: list[dict[str, object]] = []
        joint = request.joint_info

        trace.append({"step": 1, "action": "receive_input", "request_id": request.request_id})

        mapped_features = self.material_mapper.map_joint_info(joint)
        trace.append({"step": 2, "action": "material_mapping", "mapped_features": mapped_features.model_dump()})

        shared_query = HistoryQueryInput(
            Number_of_Joints=joint.Number_of_Joints,
            Material_1=joint.Material_1,
            Gauge_1=joint.Gauge_1,
            Material_2=joint.Material_2,
            Gauge_2=joint.Gauge_2,
            Material_3=joint.Material_3,
            Gauge_3=joint.Gauge_3,
        )
        process_history = self.process_history_client.query_process_history(shared_query)
        trace.append({"step": 3, "action": "query_process_history", "result": process_history.model_dump()})

        candidate_output = self.selector_client.select_candidates(mapped_features)
        trace.append({"step": 4, "action": "select_rivet_die", "candidates": [c.model_dump() for c in candidate_output.candidates]})

        evaluations: list[CandidateEvaluation] = []
        for candidate in candidate_output.candidates:
            quality_input = QualityPredictionInput(**mapped_features.model_dump(), Rivet=candidate.Rivet, Die=candidate.Die)
            quality = self.quality_client.predict_quality(quality_input)
            trace.append(
                {
                    "step": 5,
                    "action": "quality_predict",
                    "candidate": candidate.model_dump(),
                    "quality": quality.model_dump(),
                }
            )

            evaluations.append(
                CandidateEvaluation(
                    Material_1=joint.Material_1,
                    Gauge_1=joint.Gauge_1,
                    Material_2=joint.Material_2,
                    Gauge_2=joint.Gauge_2,
                    Material_3=joint.Material_3,
                    Gauge_3=joint.Gauge_3,
                    Rivet=candidate.Rivet,
                    Die=candidate.Die,
                    interlock=quality.interlock,
                    bottomthickness=quality.bottomthickness,
                    rivetforce=quality.rivetforce,
                )
            )

        sim_history = self.simulation_history_client.query_simulation_history(shared_query)
        trace.append({"step": 6, "action": "query_simulation_history", "result": sim_history.model_dump()})

        history_pairs = {(item.Rivet, item.Die) for item in sim_history.history_info}
        for item in evaluations:
            if (item.Rivet, item.Die) in history_pairs:
                trace.append(
                    {
                        "step": 7,
                        "action": "skip_simulation",
                        "candidate": {"Rivet": item.Rivet, "Die": item.Die},
                        "reason": "hit_simulation_history",
                    }
                )
                continue

            sim_payload = SimulationExecutionInput(
                Number_of_Joints=joint.Number_of_Joints,
                Material_1=joint.Material_1,
                Gauge_1=joint.Gauge_1,
                Material_2=joint.Material_2,
                Gauge_2=joint.Gauge_2,
                Material_3=joint.Material_3,
                Gauge_3=joint.Gauge_3,
                Rivet=item.Rivet,
                Die=item.Die,
            )
            sim_result = self.simulation_executor_client.run_simulation(sim_payload)
            item.interlock = max(item.interlock, sim_result.interlock)
            item.bottomthickness = max(item.bottomthickness, sim_result.bottomthickness)
            trace.append(
                {
                    "step": 7,
                    "action": "run_simulation",
                    "candidate": {"Rivet": item.Rivet, "Die": item.Die},
                    "simulation_result": sim_result.model_dump(),
                }
            )

        ranked_results = self.ranker.rank_schemes(evaluations)
        trace.append({"step": 8, "action": "rank_schemes", "ranked": [r.model_dump() for r in ranked_results]})

        best = ranked_results[0] if ranked_results else None
        trace.append({"step": 9, "action": "output_best", "best": best.model_dump() if best else None})

        return AgentResponse(
            request_id=request.request_id,
            best_result=best,
            ranked_results=ranked_results,
            decision_trace=trace,
        )


def run_agent(request: dict) -> dict:
    """Unified entrypoint accepting dict payload and returning dict response."""

    agent = SPRProcessAgent()
    req_model = AgentRequest.model_validate(request)
    return agent.run(req_model).model_dump()
