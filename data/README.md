# Data Layout

`nlu-data/` 是当前已有的生产抽取数据目录，暂时保留原路径，避免移动大文件。

建议后续逐步统一为：

```text
data/
  raw/             # 原始 JSONL 或到 nlu-data 的软链接
  samples/         # 抽样观察数据，如 100case.jsonl
  processed/       # 按任务清洗后的数据
  splits/          # train/valid/test
  annotations/     # 人工校对、补标和质检结果
```

当前原始数据：

- `../nlu-data/100case.jsonl`
- `../nlu-data/knows_nlu_20260101_20260603.jsonl`

生产数据中的顶层字段主要包括：

- `query`
- `data_sources`
- `nlu`
- `request_id`
- `trace_id`
- `time`
- `sls_time`

`nlu` 内部字段会按 `configs/task_registry.yaml` 拆到不同任务。
