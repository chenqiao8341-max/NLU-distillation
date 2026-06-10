# Models

这里按模型路线整理配置和迁移说明。

当前模型注册表在 `../configs/model_registry.yaml`。

候选路线：

- `modernbert_ner/`：encoder token classification，优先迁移作者/机构。
- `qwen3_5_0_8b_sft/`：LLaMA-Factory LoRA SFT，速度和成本 baseline。
- `qwen3_5_4b_sft/`：LLaMA-Factory LoRA SFT，复杂多任务候选。
- `baselines/`：规则、API teacher、原始 base model 等对照组。
