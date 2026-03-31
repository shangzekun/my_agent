from __future__ import annotations

import json

from agent.workflow import run_agent


if __name__ == "__main__":
    sample_request = {
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

    result = run_agent(sample_request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
