# Pipelines

后续目标是把任务组织成可复用流水线：

```bash
python -m nlu_distillation.pipeline --task author_org --model modernbert_ner --dataset data/splits/author_org
```

建议 stage：

1. `inspect`：统计 schema、字段覆盖、空值和数据源。
2. `prepare`：按任务转换训练样本。
3. `train`：调用对应模型路线。
4. `evaluate`：复用 nlu-evaluator 或任务自定义指标。
5. `compare`：汇总多模型实验结果。

`../configs/pipeline_template.yaml` 是后续实现的配置草稿。
