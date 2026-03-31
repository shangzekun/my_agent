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

    result = run_agent(sample_request)

    # 单独输出每个 step 的结果和中文解释
    for item in result["decision_trace"]:
        print(f"\n[Step {item['step']}] {item['action']}")
        print(f"说明: {item['explanation']}")
        print("结果:")
        print(json.dumps(item["result"], ensure_ascii=False, indent=2))

    # 打印完整响应
    print("\n=== Agent Response ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
