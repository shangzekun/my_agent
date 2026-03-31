import json

from agent.proposal_generator import ProposalGenerator
from agent.workflow import run_agent


BASE_REQUEST = {
    "request_id": "REQ-20260331-0001",
    "joint_info": {
        "Number_of_Joints": 2,
        "Material_1": "DP590",
        "Gauge_1": 1.2,
        "Material_2": "AL6061",
        "Gauge_2": 2.0,
        "Material_3": None,
        "Gauge_3": None,
    },
}


def test_llm_disabled_workflow_ok(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ENABLED", "false")

    result = run_agent(BASE_REQUEST)

    assert result["llm_status"] == "disabled"
    assert result["llm_enabled"] is False
    assert result["best_result"] is not None
    assert len(result["ranked_results"]) >= 1
    assert any(step["action"] == "llm_generate_proposal_start" for step in result["decision_trace"])
    assert any(step["action"] == "llm_generate_proposal_disabled" for step in result["decision_trace"])


def test_llm_exception_fallback(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ENABLED", "true")

    def _raise_error(self, context):
        raise RuntimeError("mock llm failure")

    monkeypatch.setattr(ProposalGenerator, "_call_llm", _raise_error)

    result = run_agent({**BASE_REQUEST, "request_id": "REQ-20260331-0002"})

    assert result["llm_status"] == "fallback"
    assert result["llm_enabled"] is True
    assert result["proposal_summary"]
    assert any(step["action"] == "llm_generate_proposal_fallback" for step in result["decision_trace"])


def test_llm_success_json(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ENABLED", "true")

    payload = {
        "proposal_summary": "推荐使用第一名方案，满足当前质量指标。",
        "risks": ["需关注材料批次波动。"],
        "human_checkpoints": ["复核工装参数。", "确认库存。"],
        "alternative_comparison": ["方案1质量更优。", "方案2成本可能更低。"],
    }

    def _return_json(self, context):
        return json.dumps(payload, ensure_ascii=False)

    monkeypatch.setattr(ProposalGenerator, "_call_llm", _return_json)

    result = run_agent({**BASE_REQUEST, "request_id": "REQ-20260331-0003"})

    assert result["llm_status"] == "success"
    assert result["llm_enabled"] is True
    assert result["proposal_summary"] == payload["proposal_summary"]
    assert result["risks"] == payload["risks"]
    assert result["best_result"] is not None
    assert len(result["ranked_results"]) >= 1
    assert any(step["action"] == "llm_generate_proposal_success" for step in result["decision_trace"])
