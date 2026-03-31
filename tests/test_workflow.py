from agent.workflow import run_agent


def test_run_agent_end_to_end() -> None:
    request = {
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

    result = run_agent(request)

    assert result["request_id"] == "REQ-20260331-0001"
    assert result["best_result"] is not None
    assert len(result["ranked_results"]) >= 1
    assert any(step["action"] == "query_process_history" for step in result["decision_trace"])
    assert any(step["action"] in {"skip_simulation", "run_simulation"} for step in result["decision_trace"])


def test_simulation_history_match_uses_rivet_die_pair() -> None:
    request = {
        "request_id": "REQ-20260331-0002",
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

    result = run_agent(request)
    skipped = [
        step for step in result["decision_trace"] if step["action"] == "skip_simulation"
    ]
    assert any(item["candidate"] == {"Rivet": "RVT-5.3", "Die": "DIE-A"} for item in skipped)
