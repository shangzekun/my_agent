# SPR 工艺开发单 Agent（Python 本地函数调用版）

该项目提供一个固定流程的 SPR 工艺开发 Agent 骨架，使用 Python 3.11+、Pydantic schema 和本地 mock tool client 实现。

## 目录结构

```text
.
├── app/
│   └── main.py
├── agent/
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

## 说明

- 所有 tool client 当前为 mock 实现，便于后续替换为真实服务。
- `query_process_history` 与 `query_simulation_history` 共用同一套输入输出 schema。
- `decision_trace` 记录每个关键步骤及关键中间结果，便于审计与调试。
