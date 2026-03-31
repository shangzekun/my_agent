from __future__ import annotations

import json
import os
from typing import Any

from agent.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from schemas.agent import CandidateEvaluation, RankedResult
from schemas.common import HistoryQueryOutput
from schemas.request import AgentRequest


class ProposalGenerator:
    """受控建议生成器：优先调用 LLM，失败时自动回退。"""

    def __init__(self) -> None:
        self.llm_enabled = self._read_bool_env("LLM_ENABLED", default=False)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = float(os.getenv("OPENAI_TIMEOUT", "10"))

    def generate(
        self,
        request: AgentRequest,
        history_result: HistoryQueryOutput,
        evaluated_candidates: list[CandidateEvaluation],
        ranked_results: list[RankedResult],
        best_result: RankedResult | None,
    ) -> dict[str, Any]:
        """生成结构化建议，不中断主流程。"""

        if not self.llm_enabled:
            return self._fallback(
                best_result=best_result,
                history_result=history_result,
                evaluated_candidates=evaluated_candidates,
                ranked_results=ranked_results,
                llm_enabled=False,
                llm_status="disabled",
            )

        context = self._build_context(request, history_result, evaluated_candidates, ranked_results, best_result)
        try:
            raw_json = self._call_llm(context)
            parsed = self._parse_and_validate(raw_json)
            parsed["llm_enabled"] = True
            parsed["llm_status"] = "success"
            return parsed
        except Exception:
            return self._fallback(
                best_result=best_result,
                history_result=history_result,
                evaluated_candidates=evaluated_candidates,
                ranked_results=ranked_results,
                llm_enabled=True,
                llm_status="fallback",
            )

    def _build_context(
        self,
        request: AgentRequest,
        history_result: HistoryQueryOutput,
        evaluated_candidates: list[CandidateEvaluation],
        ranked_results: list[RankedResult],
        best_result: RankedResult | None,
    ) -> dict[str, Any]:
        """构造压缩后的结构化上下文，避免传入过长链路数据。"""

        top_candidates = [item.model_dump() for item in evaluated_candidates[:3]]
        top_ranked = [item.model_dump() for item in ranked_results[:3]]
        return {
            "request_id": request.request_id,
            "joint_info": request.joint_info.model_dump(),
            "history_hit": history_result.is_true,
            "history_count": len(history_result.history_info),
            "top_evaluated_candidates": top_candidates,
            "top_ranked_results": top_ranked,
            "best_result": best_result.model_dump() if best_result else None,
        }

    def _call_llm(self, context: dict[str, Any]) -> str:
        """调用 OpenAI SDK，请求严格 JSON 输出。"""

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 缺失")

        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=self.timeout)
        user_prompt = USER_PROMPT_TEMPLATE.format(context_json=json.dumps(context, ensure_ascii=False))

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("LLM 返回内容为空")
        return content

    def _parse_and_validate(self, raw_json: str) -> dict[str, Any]:
        """解析并校验 LLM JSON 输出字段。"""

        data = json.loads(raw_json)
        required_keys = {
            "proposal_summary",
            "risks",
            "human_checkpoints",
            "alternative_comparison",
        }
        if set(data.keys()) != required_keys:
            raise ValueError("LLM 输出字段不符合约束")

        if not isinstance(data["proposal_summary"], str):
            raise ValueError("proposal_summary 类型错误")
        for key in ("risks", "human_checkpoints", "alternative_comparison"):
            if not isinstance(data[key], list) or not all(isinstance(item, str) for item in data[key]):
                raise ValueError(f"{key} 类型错误")
        return data

    def _fallback(
        self,
        *,
        best_result: RankedResult | None,
        history_result: HistoryQueryOutput,
        evaluated_candidates: list[CandidateEvaluation],
        ranked_results: list[RankedResult],
        llm_enabled: bool,
        llm_status: str,
    ) -> dict[str, Any]:
        """本地规则回退，保证 workflow 可持续输出。"""

        if best_result:
            summary = f"推荐方案为 {best_result.Rivet} + {best_result.Die}，排序结果来自既有质量指标规则。"
        else:
            summary = "当前未产生可用候选方案，建议先检查输入工况与历史数据完整性。"

        risks: list[str] = []
        if len(evaluated_candidates) <= 1:
            risks.append("候选方案数量较少，工艺窗口可能不足。")
        if history_result.is_true == "No":
            risks.append("未命中历史工艺记录，建议增加人工复核。")
        history_pairs = {(item.Rivet, item.Die) for item in history_result.history_info}
        if ranked_results and (ranked_results[0].Rivet, ranked_results[0].Die) not in history_pairs:
            risks.append("最优方案未命中历史记录，建议优先进行仿真与试制验证。")
        if not risks:
            risks.append("建议关注材料批次波动对 interlock 与 bottomthickness 的影响。")

        checkpoints = [
            "核对板材牌号与厚度输入是否与现场工单一致。",
            "复核最优方案的 interlock、bottomthickness、rivetforce 是否满足内部门槛。",
            "在试制前确认 Rivet/Die 库存与设备参数窗口。",
        ]

        comparisons: list[str] = []
        top_ranked = ranked_results[:3]
        for idx, item in enumerate(top_ranked, start=1):
            comparisons.append(f"第{idx}名方案：{item.Rivet} + {item.Die}。")
        if len(comparisons) < 2:
            comparisons.append("可比备选方案不足，建议补充候选后再评估。")

        return {
            "proposal_summary": summary,
            "risks": risks,
            "human_checkpoints": checkpoints,
            "alternative_comparison": comparisons,
            "llm_enabled": llm_enabled,
            "llm_status": llm_status,
        }

    @staticmethod
    def _read_bool_env(name: str, default: bool) -> bool:
        """读取布尔环境变量。"""

        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}
