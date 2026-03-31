from __future__ import annotations

import json

from agent.workflow import run_agent


if __name__ == "__main__":
    # 示例请求：直接走本地函数入口
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

    # 运行过程中会在每一步实时打印结果与中文解释
    result = run_agent(sample_request)

    # 最终打印完整响应
    print("\n=== Agent Response ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
