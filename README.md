# SPR 工艺开发单 Agent（Python 本地函数调用版）

该项目是固定流程的 SPR 工艺开发单 Agent Demo：
- 不使用 FastAPI
- 不拆分多 Agent
- tools 仍是本地 mock client
- 在 **agent 层** 增加受控 LLM 建议生成（不改变工具调度与排序职责）

## 目录结构

```text
.
├── app/
│   └── main.py
├── agent/
│   ├── prompts.py
│   ├── proposal_generator.py
│   ├── ranker.py
│   └── workflow.py
├── schemas/
│   ├── agent.py
│   ├── common.py
│   ├── models.py
│   └── request.py
├── tools/
│   ├── material_mapper.py
│   ├── process_history_client.py
│   ├── quality_predictor_client.py
│   ├── rivet_die_selector_client.py
│   ├── simulation_executor_client.py
│   └── simulation_history_client.py
├── tests/
│   └── test_workflow.py
└── requirements.txt
```

## 固定流程运行顺序（含每步结果与中文解释）

1. 输入校验（step=1）
2. 材料映射（step=2）
3. 查询历史工艺（step=3）
4. 钉模候选生成（step=4）
5. 逐候选质量预测（step=5）
6. 查询仿真历史（step=6）
7. 仿真执行/跳过（step=7）
8. 排序（step=8）
9. 生成 LLM 建议（step=9）
10. 输出最终结果（step=10）

每个 step 完成后会实时打印当前结果，同时写入 `decision_trace`，并包含：
- `result`：该步骤的结构化运行结果
- `explanation`：中文解释

## LLM 接入说明（DeepSeek）

- 接入位置：`agent/proposal_generator.py`（agent 层，不在 tools 层）
- 接口实现：使用 OpenAI Python SDK 的兼容方式调用 DeepSeek
- 默认模型：`deepseek-chat`
- 默认 Base URL：`https://api.deepseek.com`
- 约束：LLM 不参与工具调度，不替代排序逻辑

## 输出字段

`AgentResponse` 主要字段：
- `request_id`
- `best_result`
- `ranked_results`
- `decision_trace`
- `proposal_summary`
- `risks`
- `human_checkpoints`
- `alternative_comparison`
- `llm_enabled`
- `llm_status`（`disabled | success | fallback`）

## 环境变量配置

```bash
# 默认关闭，保证无 API Key 也可运行
export LLM_ENABLED=false

# 开启 LLM（DeepSeek）时配置
export DEEPSEEK_API_KEY="your_deepseek_key"
export DEEPSEEK_MODEL="deepseek-chat"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"

# 可选兼容参数
export OPENAI_API_KEY=""
export OPENAI_MODEL=""
export LLM_TIMEOUT=10
```

## LLM 开关行为

- `LLM_ENABLED=false`
  - 不发起网络调用
  - 直接本地 fallback，`llm_status=disabled`
- `LLM_ENABLED=true` 且调用成功
  - 使用 DeepSeek 返回结构化 JSON，`llm_status=success`
- `LLM_ENABLED=true` 但调用失败/超时/JSON 非法
  - 自动降级本地 fallback，`llm_status=fallback`

## 运行方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

## 测试

```bash
pytest -q
```
