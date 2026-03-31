from __future__ import annotations

import json

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

from agent.proposal_generator import ProposalGenerator
from agent.ranker import SchemeRanker


class SPRProcessAgent:
    """固定步骤的 SPR 工艺开发工作流 Agent。"""

    def __init__(self) -> None:
        self.material_mapper = MaterialMapper()
        self.process_history_client = ProcessHistoryClient()
        self.selector_client = RivetDieSelectorClient()
        self.quality_client = QualityPredictorClient()
        self.simulation_history_client = SimulationHistoryClient()
        self.simulation_executor_client = SimulationExecutorClient()
        self.ranker = SchemeRanker()
        self.proposal_generator = ProposalGenerator()

    def _record_step(
        self,
        trace: list[dict[str, object]],
        step: int,
        action: str,
        result: dict[str, object],
        explanation: str,
    ) -> None:
        """记录每一步的结果与中文解释，并实时输出当前步骤结果。"""

        record = {
            "step": step,
            "action": action,
            "result": result,
            "explanation": explanation,
        }
        trace.append(record)

        print(f"\n[Step {step}] {action}")
        print(f"说明: {explanation}")
        print("结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    def run(self, request: AgentRequest) -> AgentResponse:
        trace: list[dict[str, object]] = []
        joint = request.joint_info

        self._record_step(
            trace,
            step=1,
            action="receive_input",
            result={"request_id": request.request_id, "joint_info": joint.model_dump()},
            explanation="已完成输入校验并接收请求参数。",
        )

        mapped_features = self.material_mapper.map_joint_info(joint)
        self._record_step(
            trace,
            step=2,
            action="material_mapping",
            result=mapped_features.model_dump(),
            explanation="已将材料牌号映射为抗拉强度特征，用于后续模型调用。",
        )

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
        self._record_step(
            trace,
            step=3,
            action="query_process_history",
            result=process_history.model_dump(),
            explanation="已查询历史工艺库，得到是否命中与历史方案信息。",
        )

        candidate_output = self.selector_client.select_candidates(mapped_features)
        self._record_step(
            trace,
            step=4,
            action="select_rivet_die",
            result={"candidates": [c.model_dump() for c in candidate_output.candidates]},
            explanation="已完成钉模候选生成。",
        )

        evaluations: list[CandidateEvaluation] = []
        for candidate in candidate_output.candidates:
            quality_input = QualityPredictionInput(**mapped_features.model_dump(), Rivet=candidate.Rivet, Die=candidate.Die)
            quality = self.quality_client.predict_quality(quality_input)
            self._record_step(
                trace,
                step=5,
                action="quality_predict",
                result={"candidate": candidate.model_dump(), "quality": quality.model_dump()},
                explanation="已完成单个候选方案的质量预测。",
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
        self._record_step(
            trace,
            step=6,
            action="query_simulation_history",
            result=sim_history.model_dump(),
            explanation="已查询仿真历史库，用于避免重复仿真。",
        )

        history_pairs = {(item.Rivet, item.Die) for item in sim_history.history_info}
        for item in evaluations:
            if (item.Rivet, item.Die) in history_pairs:
                self._record_step(
                    trace,
                    step=7,
                    action="skip_simulation",
                    result={"candidate": {"Rivet": item.Rivet, "Die": item.Die}, "reason": "hit_simulation_history"},
                    explanation="该候选已命中仿真历史，跳过重复仿真。",
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
            self._record_step(
                trace,
                step=7,
                action="run_simulation",
                result={"candidate": {"Rivet": item.Rivet, "Die": item.Die}, "simulation_result": sim_result.model_dump()},
                explanation="该候选未命中仿真历史，已执行仿真并回填关键指标。",
            )

        ranked_results = self.ranker.rank_schemes(evaluations)
        self._record_step(
            trace,
            step=8,
            action="rank_schemes",
            result={"ranked": [r.model_dump() for r in ranked_results]},
            explanation="已基于 interlock、bottomthickness、rivetforce 完成排序。",
        )

        best = ranked_results[0] if ranked_results else None

        self._record_step(
            trace,
            step=9,
            action="llm_generate_proposal_start",
            result={
                "request_id": request.request_id,
                "candidate_count": len(evaluations),
                "ranked_count": len(ranked_results),
            },
            explanation="开始生成结构化工艺建议（LLM 受控调用）。",
        )
        proposal = self.proposal_generator.generate(
            request=request,
            history_result=process_history,
            evaluated_candidates=evaluations,
            ranked_results=ranked_results,
            best_result=best,
        )
        if proposal["llm_status"] == "success":
            self._record_step(
                trace,
                step=9,
                action="llm_generate_proposal_success",
                result={"llm_status": proposal["llm_status"]},
                explanation="LLM 建议生成成功，已写入结构化输出字段。",
            )
        elif proposal["llm_status"] == "fallback":
            self._record_step(
                trace,
                step=9,
                action="llm_generate_proposal_fallback",
                result={"llm_status": proposal["llm_status"]},
                explanation="LLM 调用失败或输出非法，已自动降级到本地 fallback。",
            )
        else:
            self._record_step(
                trace,
                step=9,
                action="llm_generate_proposal_disabled",
                result={"llm_status": proposal["llm_status"]},
                explanation="LLM 开关关闭，直接使用本地 fallback 建议。",
            )

        self._record_step(
            trace,
            step=10,
            action="output_best",
            result={"best": best.model_dump() if best else None},
            explanation="已输出最优方案与完整排序结果。",
        )

        return AgentResponse(
            request_id=request.request_id,
            best_result=best,
            ranked_results=ranked_results,
            decision_trace=trace,
            proposal_summary=proposal["proposal_summary"],
            risks=proposal["risks"],
            human_checkpoints=proposal["human_checkpoints"],
            alternative_comparison=proposal["alternative_comparison"],
            llm_enabled=proposal["llm_enabled"],
            llm_status=proposal["llm_status"],
        )


def run_agent(request: dict) -> dict:
    """统一入口：输入字典，输出字典。"""

    agent = SPRProcessAgent()
    req_model = AgentRequest.model_validate(request)
    return agent.run(req_model).model_dump()
