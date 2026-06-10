# topic_keyword Schema

## Input

- `query`: 用户原始问题。

## Target

- `topics`
- `keyword`
- `expand_topics`
- `expand_topics_en`
- `expand_keywords`
- `expand_keywords_en`

## Existing Assets

- Production sample: `/home/qiao/work/NLU-distillation/nlu-data/100case.jsonl`
- Production full data: `/home/qiao/work/NLU-distillation/nlu-data/knows_nlu_20260101_20260603.jsonl`

## Notes

这是生产样本覆盖最多的任务，但自动评测会比作者/机构更难，建议先做人工抽样质检。
