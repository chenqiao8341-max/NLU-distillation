# author_org

当前最成熟任务，建议作为新项目的第一条迁移线。

已完成能力：

- BIO 数据准备：`/home/qiao/work/nlu-bert/scripts/prepare_author_org_bio.py`
- ModernBERT 训练：`/home/qiao/work/nlu-bert/scripts/train_author_org_ner.py`
- 单条/批量推理：`/home/qiao/work/nlu-bert/scripts/predict_author_org.py`
- 评测：`/home/qiao/work/nlu-bert/scripts/eval_author_org_bert.py`

下一步迁移：

1. 把数据准备输出改到 `data/processed/author_org/` 和 `data/splits/author_org/`。
2. 保持作者英文变体由规则补齐。
3. 用相同评测集比较 ModernBERT、0.8B SFT、4B SFT。
