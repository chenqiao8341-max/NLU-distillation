# Scripts

项目级脚本入口预留目录。

优先迁移顺序：

1. 从 `/home/qiao/work/nlu-bert/scripts/prepare_author_org_bio.py` 迁移作者/机构数据准备。
2. 从 `/home/qiao/work/nlu-bert/scripts/train_author_org_ner.py` 迁移 ModernBERT 训练入口。
3. 从 `/home/qiao/work/nlu-bert/scripts/eval_author_org_bert.py` 迁移评测入口。
4. 新增生产 JSONL inspect 脚本，输出字段覆盖和候选任务统计。

迁移时尽量保留旧脚本可用，不直接破坏旧工程。
