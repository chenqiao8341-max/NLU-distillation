# Tasks

这里按 NLU 任务类型沉淀 schema、样例、数据准备说明和评测口径。

当前任务注册表在 `../configs/task_registry.yaml`。

建议每个任务目录逐步补齐：

- `schema.md`：输入字段、目标字段、空值策略、输出 JSON 格式。
- `examples.jsonl`：小样例，便于人工检查。
- `prepare.md`：从生产 JSONL 或旧 eval 文件转换训练数据的方法。
- `metrics.md`：Exact Match、Partial、F1、Null accuracy 或任务专属指标。
