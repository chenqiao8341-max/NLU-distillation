# Migration Plan

## Phase 1: 固定现状

- 保留 `nlu-data/` 中生产 JSONL 原始位置。
- 用 `100case.jsonl` 完成字段统计、任务拆分和 schema 草稿。
- 把旧工程路径登记到 `configs/task_registry.yaml` 和 `configs/model_registry.yaml`。

## Phase 2: 迁移 author_org

- 迁移 ModernBERT BIO 数据准备逻辑。
- 在本项目下生成 `data/processed/author_org/` 和 `data/splits/author_org/`。
- 训练输出统一放到 `experiments/runs/` 或 `models/modernbert_ner/outputs/`。
- 评测报告统一放到 `reports/author_org/`。

## Phase 3: 对比 0.8B 与 4B

- 将 LLaMA-Factory 的作者/机构 SFT 数据和配置登记到本项目。
- 用同一评测集跑：
  - ModernBERT
  - Qwen3.5-0.8B LoRA
  - Qwen3.5-4B LoRA
- 汇总速度、准确率、字段稳定性和 JSON 合法率。

## Phase 4: 扩展任务

建议顺序：

1. `data_type`
2. `time_if`
3. `topic_keyword`
4. `trial_slots`
5. `query_rewrite`

## Phase 5: 流程化与可视化

- 用 `configs/pipeline_template.yaml` 固化任务、模型和数据路径。
- 为 LLaMA-Factory 配置 `report_to: wandb` 或 `report_to: tensorboard`。
- 增加统一 comparison 表格，把训练 loss、eval 指标、吞吐和失败样本放在一起。
