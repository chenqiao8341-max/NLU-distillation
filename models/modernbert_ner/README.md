# ModernBERT NER 使用说明

本文档说明 BERT 类模型在本项目中的定位、训练数据、推理方式和评测方式。

## 1. 模型定位

当前 BERT 路线使用 `ModernBERT-base` 做 token classification，也就是 BIO 序列标注。

它适合做这类任务：

- 从 query 原文中抽取连续片段。
- 输出字段必须严格来自 query。
- 不需要生成复杂 JSON、推理、归一化或相对时间计算。

它不适合单独做这类任务：

- 需要把“最近三年”转换为具体日期。
- 需要把研究类型映射到固定枚举。
- 需要生成主题词、关键词的语义分类。
- 需要推断 query 中没有明说的信息。

## 2. 当前模型和数据

作者/机构旧工程：

```text
/home/chenqr/work/nlu-bert
```

作者/机构推荐模型：

```text
/home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner
```

这个模型使用 `nlu-server/eval` 下的 3000 条互联网扩展数据训练：

```text
/home/chenqr/work/nlu-server/eval/作者和机构_互联网扩展3k.json
```

当前 `NLU-distillation` 中也有三类 BIO 数据和训练结果：

```text
/home/chenqr/work/NLU-distillation/data/processed/author_org/bio
/home/chenqr/work/NLU-distillation/data/processed/org_country/bio
/home/chenqr/work/NLU-distillation/data/processed/topic_keywords/bio

/home/chenqr/work/NLU-distillation/experiments/modernbert_ner/
```

注意：`data/processed/*/bio` 适合做 BIO 模型开发和对比，但业务评测应优先使用：

```text
/home/chenqr/work/nlu-server/eval/*.json
```

## 3. 作者/机构推理流程

作者/机构任务不是让 BERT 直接生成所有字段。

实际流程是：

1. ModernBERT 从 query 里抽取 `author_name` 和 `author_institution`。
2. `nlu_bert/author_variants.py` 根据抽到的作者名生成 `author_name英文变体`。
3. 输出字段对齐业务格式：

```json
{
  "query": "...",
  "author_name": "...",
  "author_name英文变体": "<variant>...</variant>",
  "author_institution": "..."
}
```

单条推理：

```bash
cd /home/chenqr/work/nlu-bert
/home/chenqr/.myenv/bin/python scripts/predict_author_org.py \
  --model-dir /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner \
  --text "南京大学生命科学学院李根喜教授课题组提出赋予多肽电活性的策略"
```

批量推理：

```bash
cd /home/chenqr/work/nlu-bert
/home/chenqr/.myenv/bin/python scripts/predict_author_org.py \
  --model-dir /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner \
  --input-json /home/chenqr/work/nlu-server/eval/作者和机构.json \
  --output-json /home/chenqr/work/NLU-distillation/reports/modernbert_ner/author_org_predictions.json
```

## 4. 训练

作者/机构旧工程训练命令：

```bash
cd /home/chenqr/work/nlu-bert
/home/chenqr/.myenv/bin/python scripts/prepare_author_org_bio.py
/home/chenqr/.myenv/bin/python scripts/train_author_org_ner.py \
  --model-path /home/chenqr/models/BERT/ModernBERT-base \
  --data-dir /home/chenqr/work/nlu-bert/data/author_org_bio \
  --output-dir /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner \
  --epochs 5 \
  --batch-size 16 \
  --learning-rate 3e-5
```

`NLU-distillation` 通用 BIO 训练命令：

```bash
cd /home/chenqr/work/NLU-distillation
CUDA_VISIBLE_DEVICES=0 /home/chenqr/.myenv/bin/python scripts/train_eval_modernbert_ner.py \
  --tasks author_org org_country topic_keywords \
  --model-path /home/chenqr/models/BERT/ModernBERT-base \
  --epochs 5 \
  --batch-size 16
```

训练可以使用全量训练数据；评测不要使用训练集，业务评测使用 `nlu-server/eval/*.json`。

## 5. 业务评测

BIO test 指标只说明 token/span 标注效果，不等于真实业务抽取效果。

作者/机构真实抽取能力需要用业务评测集：

```text
/home/chenqr/work/nlu-server/eval/作者和机构.json
```

可复跑命令：

```bash
cd /home/chenqr/work/NLU-distillation
/home/chenqr/.myenv/bin/python scripts/eval_author_org_bert_business.py \
  --model-dir /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner \
  --dataset /home/chenqr/work/nlu-server/eval/作者和机构.json \
  --output-prefix /home/chenqr/work/NLU-distillation/reports/modernbert_ner/author_org_business_eval
```

输出：

```text
reports/modernbert_ner/author_org_business_eval.json
reports/modernbert_ner/author_org_business_eval.md
reports/modernbert_ner/author_org_business_eval_details.csv
```

## 6. 哪些任务建议给 BERT

结合 `nlu-server/eval/prompt.md`：

### 建议优先给 BERT

- `作者和机构`
  - 任务核心是从 query 中抽取作者名和机构名。
  - 英文变体不由 BERT 生成，而是通过规则脚本后处理。
  - 当前 BIO 和业务评测都最接近可用路线。

### 可以尝试，但需要谨慎

- `机构和国家`
  - prompt 明确要求结果来自原文，理论上适合 span 抽取。
  - 但数据中可能存在标准答案不在 query 中的情况，BIO 会无法标注这类目标。
  - 更适合“机构名抽取 + 国家/地区规则或词典标准化”的组合方案。

- `topic和keywords`
  - prompt 要求抽医学专业术语，表面上是 span 抽取。
  - 但 topics/keywords 的区分带有语义判断，不只是找连续片段。
  - 现有 BIO 数据对 keywords 的拆分和标注有问题，当前 BERT 结果不可靠。

### 不建议直接给 token-classification BERT

- `时间和if值`
  - 需要相对时间换算、日期范围归一化和 IF 数值规则。
  - 更适合规则系统，或“规则 + 小模型分类”。

- `data_type`
  - 本质是研究类型分类/枚举映射，不是 BIO span 抽取。
  - 可用 BERT classifier，但不是当前 token-classification NER 头。

## 7. 当前已知风险

- `token_accuracy` 会被大量 `O` 标签抬高，不代表抽取效果。
- `topic_keywords` 的 `KEYWORD` BIO 标注覆盖不足，不能直接作为有效结论。
- `org_country` 中标准答案若不在原文出现，BERT 无法抽出。
- 作者英文变体依赖词典和 `pypinyin`，不是模型直接能力。

## 8. 最近一次真实业务验证

评测集使用：

```text
/home/chenqr/work/nlu-server/eval/作者和机构.json
```

真实业务评测脚本：

```bash
/home/chenqr/.myenv/bin/python scripts/eval_author_org_bert_business.py \
  --model-dir /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner \
  --dataset /home/chenqr/work/nlu-server/eval/作者和机构.json
```

结果说明：

- `author_name` 和 `author_institution` 是 BERT 抽取结果。
- `author_name英文变体` 是后处理脚本根据作者名生成。
- 这类评测才是业务真实抽取能力，不是 BIO token F1。

近期实测：

- 3k 训练版：`Average-F1 ≈ 0.510`
- fulltrain 版：`Average-F1 ≈ 0.410`

结论：

- `作者和机构` 是当前最适合 BERT 的任务。
- 但即使在这个任务上，也要用 `nlu-server/eval` 的字段级评测看真实效果。
