# SPR 工艺开发单 Agent（Python 本地函数调用版）

该项目是固定流程的 SPR 工艺开发单 Agent Demo：
- 不使用 FastAPI
- 不拆分多 Agent
- 工具仍是本地 mock client
- 在 **agent 层** 增加受控 LLM 建议生成（不改变工具调度与排序职责）
该项目提供一个固定流程的 SPR 工艺开发 Agent 骨架，使用 Python 3.11+、Pydantic schema 和本地 mock tool client 实现。

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

## 固定流程运行顺序（含 LLM 接入点）

1. **输入校验**：`run_agent(request)` 把字典校验成 `AgentRequest`。
2. **材料映射**：`MaterialMapper` 把 `Material_x` 映射为 `Material_x_ts`。
3. **查询历史工艺**：`ProcessHistoryClient` 返回历史命中信息。
4. **钉模候选生成**：`RivetDieSelectorClient` 给出候选 `Rivet + Die`。
5. **逐候选质量预测**：`QualityPredictorClient` 预测 `interlock / bottomthickness / rivetforce`。
6. **查询仿真历史**：`SimulationHistoryClient` 返回历史仿真记录。
7. **必要时执行仿真**：仅对未命中 `Rivet + Die` 的候选调用 `SimulationExecutorClient`。
8. **排序**：`SchemeRanker.rank_schemes()` 基于既有规则排序。
9. **LLM 建议生成（新增）**：
   - 位置：排序完成后、最终输出前。
   - 调用者：`agent/proposal_generator.py`。
   - 输入：压缩后的结构化上下文（不会把完整 trace 全量喂给模型）。
   - 输出：结构化建议字段。
10. **输出结果**：返回 `best_result / ranked_results / decision_trace` + LLM 字段。

> 关键约束：LLM 不参与工具调度，不替代排序，不改变工具职责边界。

## LLM 接入说明（在 agent 层，不在 tools 层）

- `agent/proposal_generator.py`：受控建议生成器。
- `agent/prompts.py`：system/user prompt 模板，要求严格 JSON 输出。
- `tools/` 中的工具接口和职责不变，仍用于结构化数据计算与查询。

## 所有 tool 的 temporary mock

当前每个 tool 都有 `temporary(...)` 临时函数模拟输出：
## 固定流程（详细运行顺序）

### Step 1：接收 Agent 输入
- 入口函数：`run_agent(request)`（`agent/workflow.py`）
- 行为：把传入字典校验为 `AgentRequest`。
- 记录：`decision_trace` 写入 `receive_input`。

### Step 2：材料映射（Material -> TS）
- 调用：`tools/material_mapper.py` 中 `MaterialMapper.map_joint_info()`。
- 实际 mock 执行：`MaterialMapper.temporary()`。
- 行为：将 `Material_1/2/3` 转换为 `Material_1_ts/2_ts/3_ts`。
- 记录：`decision_trace` 写入 `material_mapping`。

### Step 3：查询历史工艺数据库
- 调用：`ProcessHistoryClient.query_process_history()`。
- 实际 mock 执行：`ProcessHistoryClient.temporary()`。
- 输入：`HistoryQueryInput`。
- 输出：`HistoryQueryOutput`（`is_true`, `history_info`）。
- 记录：`decision_trace` 写入 `query_process_history`。

### Step 4：钉模选型（候选方案生成）
- 调用：`RivetDieSelectorClient.select_candidates()`。
- 实际 mock 执行：`RivetDieSelectorClient.temporary()`。
- 输入：`MaterialFeaturesInput`。
- 输出：`candidates = [{Rivet, Die}, ...]`。
- 记录：`decision_trace` 写入 `select_rivet_die`。

### Step 5：质量预测（逐候选）
- 调用：`QualityPredictorClient.predict_quality()`。
- 实际 mock 执行：`QualityPredictorClient.temporary()`。
- 输入：材料特征 + `Rivet` + `Die`。
- 输出：`interlock`, `bottomthickness`, `rivetforce`。
- 记录：每个候选都写一条 `quality_predict`。

### Step 6：查询仿真历史数据库
- 调用：`SimulationHistoryClient.query_simulation_history()`。
- 实际 mock 执行：`SimulationHistoryClient.temporary()`。
- 输入/输出：与历史工艺查询完全共用同一套 schema。
- 记录：`decision_trace` 写入 `query_simulation_history`。

### Step 7：仿真执行（仅未命中历史）
- 命中判断：只看 `Rivet + Die` 组合是否出现在仿真历史中。
- 命中时：跳过仿真，写入 `skip_simulation`。
- 未命中时：调用 `SimulationExecutorClient.run_simulation()`。
- 实际 mock 执行：`SimulationExecutorClient.temporary()`。
- 输出：`headheight`, `interlock`, `bottomthickness`，并回填候选评价值。

### Step 8：排序模块
- 调用：`SchemeRanker.rank_schemes()`（`agent/ranker.py`）。
- 排序策略：
  1. `interlock` 高优先
  2. `bottomthickness` 高优先
  3. `rivetforce` 低优先
- 输出：`ranked_results = [{Rivet, Die}, ...]`。

### Step 9：输出最优方案
- 从 `ranked_results` 取第一项作为 `best_result`。
- 返回 `AgentResponse`：
  - `request_id`
  - `best_result`
  - `ranked_results`
  - `decision_trace`

## 工具层 temporary 说明（第一版 mock）

当前每个 tool 都包含一个 `temporary(...)` 临时函数，用于模拟真实 tool 返回：
- `MaterialMapper.temporary()`
- `ProcessHistoryClient.temporary()`
- `RivetDieSelectorClient.temporary()`
- `QualityPredictorClient.temporary()`
- `SimulationHistoryClient.temporary()`
- `SimulationExecutorClient.temporary()`

## 输出字段

`AgentResponse` 主要字段：
- `request_id`
- `best_result`
- `ranked_results`
- `decision_trace`
- `proposal_summary`（新增）
- `risks`（新增）
- `human_checkpoints`（新增）
- `alternative_comparison`（新增）
- `llm_enabled`（新增）
- `llm_status`（新增：`disabled | success | fallback`）

## 环境变量配置

```bash
# 默认关闭，保证无 API Key 也可运行
export LLM_ENABLED=false

# 开启时再提供
export OPENAI_API_KEY="your_key"
export OPENAI_MODEL="gpt-4o-mini"
```

## LLM 开关行为

- `LLM_ENABLED=false`：
  - 不发起任何网络调用。
  - 直接走本地 fallback，`llm_status=disabled`。
- `LLM_ENABLED=true` 且调用成功：
  - 使用 LLM 结构化 JSON，`llm_status=success`。
- `LLM_ENABLED=true` 但调用失败/超时/JSON 非法：
  - 自动降级到本地 fallback，workflow 不中断，`llm_status=fallback`。

## fallback 规则

本地 fallback 会生成：
- `proposal_summary`：基于 `best_result` 的规则化摘要。
- `risks`：结合候选数量、历史命中情况给出基础风险。
- `human_checkpoints`：给出 2-3 条工程审核检查点。
- `alternative_comparison`：对前 2-3 名方案做简短比较。
正式接入真实服务时，可保留 `query_* / select_* / predict_* / run_*` 对外接口不变，仅替换 `temporary` 的内部实现或改为真实调用。

## 运行方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

## 统一入口

- 函数：`run_agent(request)`
- 位置：`agent/workflow.py`
- 输入：字典（符合 `AgentRequest` schema）
- 输出：字典（`AgentResponse`）

## 测试

```bash
pytest -q
```

测试覆盖点：
1. LLM 关闭时正常返回（`disabled`）。
2. LLM 异常时自动回退（`fallback`）。
3. LLM 返回合法 JSON 时正确写入新增字段（`success`）。
4. 原有 `best_result / ranked_results` 逻辑不受影响。
5. `decision_trace` 含 LLM 相关记录。
## 说明

- 所有 tool client 当前为 mock 实现，便于后续替换为真实服务。
- `query_process_history` 与 `query_simulation_history` 共用同一套输入输出 schema。
- `decision_trace` 记录每个关键步骤及关键中间结果，便于审计与调试。
